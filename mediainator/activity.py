"""Persistent, owner-scoped operation history; never executes recovery work."""
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
import fcntl
import hashlib
import json
from pathlib import Path
from uuid import uuid4
from .import_store import atomic_json


def now():
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def locked(folder):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / '.lock').open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


class ActivityStore:
    def __init__(self, folder, profile_id, device_id):
        self.owner = dict(profile_id=profile_id, device_id=device_id)
        key = hashlib.sha256(json.dumps(self.owner, sort_keys=True).encode()).hexdigest()
        self.folder = Path(folder) / key
        self.path = self.folder / 'operations.json'

    def _read(self):
        try:
            data = json.loads(self.path.read_text())
        except FileNotFoundError:
            return dict(schema=1, owner=self.owner, operations={})
        if (not isinstance(data, dict) or data.get('schema') != 1 or data.get('owner') != self.owner
                or not isinstance(data.get('operations'), dict)):
            raise ValueError('Activity history is unsupported or damaged; existing data was preserved.')
        if not isinstance(data.get('deleted', {}), dict):
            raise ValueError('Activity cleanup index is damaged; existing data was preserved.')
        for key, value in data['operations'].items():
            if (not isinstance(value, dict) or value.get('id') != key or not isinstance(value.get('attempts'), list)
                    or not {'operation', 'module', 'pending', 'recovery', 'dismissed', 'source'} <= value.keys()):
                raise ValueError('Activity history is incomplete; existing data was preserved.')
            if not isinstance(value['source'],dict) or any(type(value[f]) is not bool for f in ('pending','recovery','dismissed')):
                raise ValueError('Activity history state is invalid; existing data was preserved.')
            for attempt in value['attempts']:
                if (not isinstance(attempt,dict) or not {'id','time','outcome','details','legacy'}<=attempt.keys()
                        or not isinstance(attempt['details'],dict)
                        or attempt['outcome'] not in {'running','success','failure','partial','interrupted','conflict','discarded'}):
                    raise ValueError('Activity attempt history is invalid; existing data was preserved.')
        return data

    def records(self):
        with locked(self.folder):
            return deepcopy(list(self._read()['operations'].values()))

    def record(self, operation, key, *, module='bookinator', outcome, pending=False,
               recovery=False, details=None, source=None, legacy=False, original=None,
               deduplicate=False, attempt_id=None):
        identity = hashlib.sha256((module+'\0'+operation+'\0'+key).encode()).hexdigest()
        with locked(self.folder):
            data = self._read()
            if identity in data.get('deleted', {}): return identity
            item = data['operations'].setdefault(identity, dict(id=identity, key=key, operation=operation, module=module,
                source=source or {}, attempts=[], pending=False, recovery=False, dismissed=False))
            if item.get('deletion') and not (details or {}).get('cleanup_incomplete'): return identity
            details = deepcopy(details or {})
            attempt = dict(id=attempt_id or str(uuid4()), time=None if legacy else now(), outcome=outcome,
                           details=details, legacy=legacy)
            previous = item['attempts'][-1] if item['attempts'] else None
            existing = next((i for i,a in enumerate(item['attempts']) if attempt_id and a['id']==attempt_id),None)
            if existing is not None:
                attempt['started'] = item['attempts'][existing].get('started',item['attempts'][existing]['time'])
                item['attempts'][existing] = attempt
            elif not (deduplicate and previous and previous['outcome'] == outcome and previous['details'] == details
                    and item['pending'] == pending and item['recovery'] == recovery):
                item['attempts'].append(attempt)
            elif not legacy and outcome == 'failure':
                previous['started'] = previous.get('started',previous['time'])
                previous['time'] = attempt['time']
                previous['occurrences'] = previous.get('occurrences',1) + 1
            item.update(pending=bool(pending), recovery=bool(recovery))
            if source is not None: item['source'] = deepcopy(source)
            if original is not None: item['original'] = original
            atomic_json(self.path, data)
        return identity

    def resolve_notice(self, operation, key, module='bookinator'):
        """Clear an actionable condition without logging successful housekeeping."""
        identity = hashlib.sha256((module+'\0'+operation+'\0'+key).encode()).hexdigest()
        with locked(self.folder):
            data = self._read(); item = data['operations'].get(identity)
            if item and item['pending']:
                item['pending'] = False
                atomic_json(self.path, data)

    def project_batch(self, batch, path, kind, *, legacy=False, interrupted=False, running=False, attempt_id=None):
        terminal = {'complete', 'duplicate', 'discarded', 'excluded'}
        items = batch['items']
        pending = sum(i['state'] not in terminal for i in items)
        failed = [i for i in items if i['state'] in {'failed', 'invalid'} or (i['state'] not in terminal and i.get('errors'))]
        uncertain = any(i['state'] in {'inflight', 'in-flight', 'unverified'} for i in items)
        outcome = 'running' if running else 'failure' if failed else 'conflict' if any(i['state']=='conflict' for i in items) else 'interrupted' if interrupted or uncertain or pending else 'success'
        if not pending and (batch.get('pending_discarded') or (items and all(i['state'] in {'discarded', 'excluded'} for i in items))): outcome = 'discarded'
        operation = 'Ebook imports' if kind == 'import' else 'Batch reverts' if batch.get('kind') == 'revert' else 'Bulk edits'
        source = dict(kind=kind, journal=str(Path(path).resolve()), library=batch['library'],
                      library_uuid=batch.get('library_uuid'), batch_id=batch['id'])
        details = dict(completed=sum(i['state']=='complete' for i in items), pending=pending,
                       failed=len(failed), items=[dict(book=i.get('uuid') or i.get('destination_uuid'),
                        title=i.get('title'), state=i['state'], error=i.get('errors') or i.get('warning')) for i in items])
        return self.record(operation, batch['library']+'\0'+batch['id'], outcome=outcome, pending=bool(pending),
                           source=source, details=details, legacy=legacy, original=batch.get('original'), deduplicate=True, attempt_id=attempt_id)

    def recover_interrupted(self):
        """Mark previous process attempts interrupted; no work is reconstructed or run."""
        with locked(self.folder):
            data=self._read();changed=False
            for record in data['operations'].values():
                if record['attempts'] and record['attempts'][-1]['outcome']=='running':
                    record['attempts'][-1]['outcome']='interrupted'
                    record['attempts'][-1]['details']['interruption']='Previous process ended without a verified activity outcome; review authoritative journal/recovery state.'
                    changed=True
            if changed:atomic_json(self.path,data)

    def summary(self):
        records = self.records()
        active = [r for r in records if not r['dismissed'] and (r['pending'] or r['recovery'] or r.get('deletion'))]
        return dict(total=len(active), pending=sum(bool(r['pending'] or r.get('deletion')) for r in active),
                    failed=sum(bool(r['attempts'] and r['attempts'][-1]['outcome']=='failure') for r in active),
                    recovery=sum(r['recovery'] for r in active))

    def latest(self):
        grouped = {}
        for record in self.records():
            group = grouped.setdefault((record['module'], record['operation']), {})
            for attempt in record['attempts']:
                if attempt['outcome'] not in {'success', 'failure'}: continue
                old = group.get(attempt['outcome'])
                if old is None or (attempt['time'] or '') > (old['attempt']['time'] or ''):
                    group[attempt['outcome']] = dict(operation_id=record['id'], attempt=deepcopy(attempt))
        return grouped


class ActivityBridge:
    """UI-facing best-effort recording; storage failure never recurses or drops drafts."""
    def __init__(self, store, notify):
        self.store, self.notify = store, notify
        self.last_error = None
        self.listeners = []

    def invoke(self, method, *args, **kwargs):
        try:
            result = getattr(self.store, method)(*args, **kwargs)
            self.last_error = None
            return result
        except (OSError, ValueError, TypeError, KeyError) as exc:
            from .diagnostics import record_error
            record_error('activity-storage-failure',exc)
            self.last_error = 'Activity history could not be saved/read: '+str(exc)
            self.notify(self.last_error)
            return None
        finally:
            if method not in ('records', 'summary', 'latest'):
                for listener in self.listeners:
                    listener()

    def record(self, *args, **kwargs):
        from .diagnostics import record_operation
        record_operation(args[0] if args else kwargs.get('operation'),kwargs.get('outcome'))
        return self.invoke('record', *args, **kwargs)
    def batch(self, *args, **kwargs):
        result=self.invoke('project_batch', *args, **kwargs)
        # Inspect only state enums from this operation, never item metadata/errors.
        batch=args[0] if args else kwargs.get('batch')
        if type(batch) is dict and not kwargs.get('legacy') and not kwargs.get('running'):
            items=batch.get('items')
            if type(items) is list and any(type(i) is dict and type(i.get('state')) is str and i['state'] in ('failed','inflight','in-flight','unverified') for i in items):
                from .diagnostics import record_error
                record_error('operation-failure')
        return result
