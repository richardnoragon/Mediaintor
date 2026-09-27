"""Deterministic bulk plans and durable field-scoped recovery/revert history."""
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import uuid
from .import_store import atomic_json
from .metadata_rules import equal

OPERATIONS = ('Add Tags', 'Remove Tags', 'Set Series', 'Clear Series', 'Replace Author')
FINAL = {'complete', 'discarded', 'excluded'}
FIELDS = {'authors', 'tags', 'series', 'series_index'}


def number(value, positive=False):
    try:
        result = Decimal(str(value))
        if not result.is_finite() or result < 0 or (positive and result == 0):
            raise ValueError()
        import math
        if not math.isfinite(float(result)) or (result != 0 and float(result) == 0):
            raise ValueError()
        return result
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError('Use a finite number greater than zero for increments, or zero or greater for other numbers.') from None


def propose(record, operation, options, index):
    if operation not in OPERATIONS:
        raise ValueError('Choose one supported operation per batch.')
    result = {}
    if operation in ('Add Tags', 'Remove Tags'):
        tags = options.get('tags', [])
        if not tags or any(not t.strip() or ',' in t for t in tags):
            raise ValueError('Add at least one tag. Commas are not allowed: Calibre treats them as separators.')
        tags = list(dict.fromkeys(t.strip() for t in tags))
        result['tags'] = list(dict.fromkeys(record['tags'] + tags)) if operation == 'Add Tags' else [t for t in record['tags'] if t not in tags]
    elif operation == 'Replace Author':
        old, new = options.get('old', ''), options.get('new', '').strip()
        if not old or not new:
            raise ValueError('Enter both the exact author to replace and its replacement.')
        if old in record['authors'] and old != new:
            # Preserve list order, deduplicating only the replacement author.
            authors = []; found = False
            for author in record['authors']:
                author = new if author == old else author
                if author == new:
                    if found: continue
                    found = True
                authors.append(author)
            result['authors'] = authors
    elif operation == 'Clear Series':
        result = {'series': '', 'series_index': None}
    else:
        series = options.get('series', '').strip()
        if not series: raise ValueError('Enter a series name.')
        mode = options.get('mode', 'Keep existing')
        if mode == 'Keep existing':
            value = record['series_index'] if record['series'] and record['series_index'] is not None else 1
            value = number(value)
        elif mode == 'Fixed': value = number(options.get('fixed', 1))
        elif mode == 'Sequential': value = number(options.get('start', 1)) + number(options.get('increment', 1), True) * index
        else: raise ValueError('Choose a series-number mode.')
        result = {'series': series, 'series_index': float(number(value))}
    changed = {f: v for f, v in result.items() if not equal(f, record[f], v)}
    # Series and index form one coupled intent, even if one value is unchanged.
    if changed and operation in ('Set Series', 'Clear Series'): return result
    return changed


class BulkStore:
    def __init__(self, folder, library):
        self.library = str(Path(library).resolve())
        self.folder = Path(folder) / hashlib.sha256(self.library.encode()).hexdigest()[:20]
        self.folder.mkdir(parents=True, exist_ok=True)

    def save(self, batch):
        if batch['library'] != self.library: raise ValueError('Wrong library for this batch.')
        identity = str(uuid.UUID(batch['id']))
        atomic_json(self.folder / (identity + '.json'), batch)

    def batches(self):
        result = []
        for path in sorted(self.folder.glob('*.json')):
            try:
                batch = json.loads(path.read_text())
                if (batch.get('schema') != 1 or batch.get('library') != self.library
                        or path.stem != str(uuid.UUID(batch['id'])) or not isinstance(batch.get('items'), list)
                        or not isinstance(batch['created'], str) or not isinstance(batch['library_uuid'], str)):
                    raise ValueError()
                for item in batch['items']:
                    if (not {'book','uuid','baseline','desired','state','applied'} <= item.keys()
                            or not isinstance(item['book'], int) or not set(item['desired']) <= FIELDS
                            or item['state'] not in FINAL | {'pending','failed','conflict','inflight'}
                            or not isinstance(item['applied'], dict)):
                        raise ValueError()
                result.append(batch)
            except (KeyError, TypeError, AttributeError, ValueError):
                raise ValueError('Unsupported or damaged bulk history. The file has been preserved: '+str(path)) from None
        return sorted(result, key=lambda b: b['created'], reverse=True)

    def pending(self):
        return [b for b in self.batches() if any(i['state'] not in FINAL for i in b['items'])]

    def delete(self, batch):
        # Pending journals are recovery data, not disposable history.
        if any(i['state'] not in FINAL for i in batch['items']):
            raise ValueError('Review or discard pending work before deleting its history.')
        (self.folder / (str(uuid.UUID(batch['id'])) + '.json')).unlink()


def plan(store, identities, response, operation, options):
    items = []
    for index, identity in enumerate(identities):
        record = response['records'].get(identity['uuid'])
        if record is None: raise ValueError(response['errors'].get(identity['uuid'], 'Selected book is unavailable. Refresh the catalog.'))
        desired = propose(record, operation, options, index)
        items.append(dict(identity, title=record['title'], baseline=deepcopy(record), desired=desired,
                          state='pending' if desired else 'complete', applied={}, errors={}))
    return dict(schema=1, id=str(uuid.uuid4()), library=store.library, library_uuid=response['library_uuid'],
                created=datetime.now(timezone.utc).isoformat(), operation=operation, options=options,
                items=items, kind='edit')


def remaining(item):
    return {f: v for f, v in item['desired'].items() if f in item.get('force_fields', []) or f not in item['applied'] or not equal(f, item['applied'][f]['after'], v)}


def reconcile(batch, response):
    if response['library_uuid'] != batch['library_uuid']: raise ValueError('Library identity changed. Pending work has been preserved.')
    for item in batch['items']:
        if item['state'] in FINAL: continue
        current = response['records'].get(item['uuid'])
        if current is None:
            item['state'] = 'failed'; item['errors'] = {'book': response['errors'].get(item['uuid'], 'Book unavailable')}; continue
        item['current'] = current
        # A lost acknowledgement is reconciled only for an intent durably marked in-flight.
        if item['state'] == 'inflight':
            for f, v in remaining(item).items():
                if equal(f, current[f], v):
                    before = item['attempt_before'][f]
                    if not equal(f, before, v): item['applied'][f] = {'before': item['applied'].get(f, {}).get('before', before), 'after': v}
                    else: item['desired'].pop(f, None)
                    item['force_fields'] = [key for key in item.get('force_fields', []) if key != f]
            item['baseline'] = dict(item['baseline'], **{f: a['after'] for f, a in item['applied'].items()})
        pending = remaining(item)
        blocked = [f for f, v in pending.items() if not equal(f, current[f], item['baseline'][f]) and not equal(f, current[f], v)]
        if pending and ('series' in pending or 'series_index' in pending):
            for f in ('series', 'series_index'):
                if not equal(f, current[f], item['baseline'][f]) and not equal(f, current[f], item['desired'].get(f, item['baseline'][f])):
                    if f not in blocked: blocked.append(f)
        item['conflicts'] = blocked
        item['state'] = 'conflict' if blocked else 'pending' if pending else 'complete'
    return batch


def record_result(item, result):
    item['current'] = {f: v for f, v in result['current'].items() if f in FIELDS | {'title', 'uuid'}}
    if result.get('conflicts'):
        item['state'] = 'conflict'; item['conflicts'] = result['conflicts']; return
    for f, before in item['attempt_before'].items():
        after = result['current'][f]
        if not equal(f, before, after):
            original = item['applied'].get(f, {}).get('before', before)
            item['applied'][f] = {'before': original, 'after': after}
        elif f in result.get('saved', []) and f not in item['applied']:
            item['desired'].pop(f, None)
    item['force_fields'] = [f for f in item.get('force_fields', []) if f not in result.get('saved', [])]
    # Known partial outcomes become the new retry baseline; history keeps the original values.
    item['baseline'] = deepcopy(item['current'])
    item['errors'] = result.get('errors', {})
    item['state'] = 'failed' if remaining(item) else 'complete'


def revert_plan(store, original, response):
    if response['library_uuid'] != original['library_uuid']: raise ValueError('Library identity changed.')
    if any(i['state'] == 'inflight' for i in original['items']): raise ValueError('Review uncertain writes before reverting.')
    items = []
    for old in original['items']:
        if not old['applied']: continue
        current = response['records'].get(old['uuid'])
        if current is None: current = dict(old['baseline'], title=old['title'])
        baseline = dict(current, **{f: a['after'] for f, a in old['applied'].items()})
        desired = {f: a['before'] for f, a in old['applied'].items()}
        # Restore coupled series/index when a series field was actually changed.
        if 'series' in desired and 'series_index' not in desired:
            desired['series_index'] = old['baseline']['series_index'] if desired['series'] else None
            baseline['series_index'] = old['baseline']['series_index']
        items.append(dict(book=old['book'], uuid=old['uuid'], title=current['title'], baseline=baseline,
                          desired=desired, applied={}, errors={}, state='pending'))
    if not items: raise ValueError('This batch has no verified changes to revert.')
    batch = dict(schema=1, id=str(uuid.uuid4()), library=store.library, library_uuid=original['library_uuid'],
                 created=datetime.now(timezone.utc).isoformat(), operation='Revert '+original['operation'],
                 kind='revert', original=original['id'], items=items)
    return reconcile(batch, response)
