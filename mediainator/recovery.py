"""Durable single-book recovery payloads. No automatic catalog writes or close actions."""
from copy import deepcopy
import base64
import hashlib
import json
from pathlib import Path
from uuid import UUID, uuid4
from .activity import locked
from .import_store import atomic_json
from .metadata_rules import FIELDS, changes, conflicts, equal


def checksum(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def validate_payload(payload, owner):
    try:
        if payload['schema'] != 1 or str(UUID(payload['id'])) != payload['id']: raise ValueError()
        identity = payload['identity']
        if any(identity[k] != owner[k] for k in owner): raise ValueError()
        if any(not isinstance(identity[k], str) or not identity[k] for k in ('profile_id','device_id','library_uuid','book_uuid')): raise ValueError()
        if type(payload['revision']) is not int or payload['revision'] < 0: raise ValueError()
        if not isinstance(payload['operation_id'], str) or not payload['operation_id']: raise ValueError()
        pending, baseline = payload['pending'], payload['baseline']
        if not isinstance(pending, dict) or not pending or not set(pending) <= set(FIELDS): raise ValueError()
        required = set(pending)
        if required & {'series','series_index'}: required.update(('series','series_index'))
        if set(baseline) != required: raise ValueError()
        for record in (pending, baseline):
            for field, value in record.items():
                if field in ('authors','tags'):
                    if not isinstance(value,list) or not all(isinstance(v,str) for v in value): raise ValueError()
                elif field == 'cover':
                    if value is not None: base64.b64decode(value, validate=True)
                elif field == 'series_index':
                    if value is not None and type(value) not in (int,float,str): raise ValueError()
                elif not isinstance(value,str): raise ValueError()
        checksum(payload)
    except (KeyError, TypeError, AttributeError, ValueError) as exc:
        raise ValueError('Unsupported, damaged or differently owned recovery payload; file preserved.') from exc
    return payload


class RecoveryStore:
    def __init__(self, app_data, profile_id, device_id, activity=None):
        self.owner = dict(profile_id=profile_id, device_id=device_id)
        key = hashlib.sha256(json.dumps(self.owner,sort_keys=True).encode()).hexdigest()
        self.folder = Path(app_data)/'Recovery'/'Single Book Edits'/key
        self.index = self.folder/'index.json'
        self.activity = activity

    def capture(self, library_uuid, book_uuid, baseline, draft, revision, operation_id, recovery_id=None):
        pending = changes(baseline, draft)
        keys = set(pending)
        if keys & {'series','series_index'}: keys.update(('series','series_index'))
        payload = dict(schema=1,id=recovery_id or str(uuid4()),identity=dict(self.owner,library_uuid=library_uuid,book_uuid=book_uuid),
                       operation_id=operation_id,revision=revision,pending=deepcopy(pending),
                       baseline={k:deepcopy(baseline[k]) for k in keys})
        return validate_payload(payload,self.owner)

    def _index(self):
        try: data=json.loads(self.index.read_text())
        except FileNotFoundError: return dict(schema=1,owner=self.owner,records={})
        if not isinstance(data,dict) or data.get('schema')!=1 or data.get('owner')!=self.owner or not isinstance(data.get('records'),dict):
            raise ValueError('Recovery discovery index is damaged or unsupported; existing files preserved.')
        for identity, record in data['records'].items():
            if (not isinstance(record,dict) or record.get('state') not in {'unresolved','recovered','discarded'}
                    or not isinstance(record.get('path'),str) or type(record.get('revision')) is not int):
                raise ValueError('Recovery discovery index contains an invalid record.')
            if not isinstance(record.get('generations', []), list) or any(not isinstance(p,str) for p in record.get('generations', [])):
                raise ValueError('Recovery generation registry is invalid; files retained.')
        return data

    def read(self, path, *, library_uuid=None, book_uuid=None):
        path=Path(path)
        if path.is_symlink(): raise ValueError('Recovery symlinks are not supported.')
        try:
            envelope=json.loads(path.read_text());payload=validate_payload(envelope['payload'],self.owner)
            if checksum(payload)!=envelope['sha256']: raise ValueError('Recovery integrity check failed; file preserved.')
        except (KeyError,TypeError) as exc: raise ValueError('Recovery envelope is incomplete; file preserved.') from exc
        if library_uuid is not None and payload['identity']['library_uuid']!=library_uuid: raise ValueError('Recovery library identity differs.')
        if book_uuid is not None and payload['identity']['book_uuid']!=book_uuid: raise ValueError('Recovery book identity differs.')
        return payload

    def preserve(self, payload, destination=None):
        validate_payload(payload,self.owner)
        with locked(self.folder):
            index=self._index();existing=index['records'].get(payload['id'])
            if existing and existing['revision']>=payload['revision']:
                old=self.read(existing['path'])
                if existing['state']=='unresolved' and old==payload: return Path(existing['path'])
                raise ValueError('Recovery revision already exists or is older; preserve a new revision.')
            destination=Path(destination) if destination else self.folder
            destination.mkdir(parents=True,exist_ok=True)
            path=destination/(payload['id']+'.'+str(payload['revision'])+'.json')
            if path.exists() and self.read(path)!=payload: raise ValueError('Recovery destination contains different data; preserved.')
            atomic_json(path,dict(payload=payload,sha256=checksum(payload)))
            if self.read(path)!=payload: raise ValueError('Recovery read-back differs.')
            generations=list(existing.get('generations', [])) if existing else []
            if existing and existing['path'] not in generations:generations.append(existing['path'])
            if str(path.resolve()) not in generations:generations.append(str(path.resolve()))
            index['records'][payload['id']]=dict(path=str(path.resolve()),revision=payload['revision'],state='unresolved',generations=generations)
            atomic_json(self.index,index)
            if self._index()!=index: raise ValueError('Recovery registration read-back differs.')
        if self.activity:
            self.activity.record('Single-book recovery',payload['id'],outcome='success',pending=True,recovery=True,
                source=dict(kind='recovery',path=str(path.resolve()),recovery_id=payload['id'],save_operation_id=payload['operation_id'],**payload['identity']),
                details=dict(revision=payload['revision'],fields=sorted(payload['pending']),message='Unsaved edits preserved in an emergency copy; review and Save are required.'))
        return path

    def discover(self):
        """Inspect only local registrations/default storage; never execute a retry."""
        records=[];errors=[]
        with locked(self.folder):
            try:index=self._index()
            except (OSError,ValueError) as exc:index=dict(records={});errors.append(str(exc))
            registered={Path(r['path']).resolve() for r in index['records'].values()}
            for identity,entry in index['records'].items():
                try:
                    payload=self.read(entry['path'])
                    if payload['id']!=identity or payload['revision']!=entry['revision']:raise ValueError('Registered recovery identity/revision differs.')
                    records.append(dict(entry,payload=payload,registered=True))
                except (OSError,ValueError) as exc:errors.append(str(entry['path'])+': '+str(exc))
            candidates={}
            for path in self.folder.glob('*.json'):
                if path==self.index or path.resolve() in registered:continue
                try:
                    payload=self.read(path)
                    # Older generations of a registered ID must not resurrect resolved work.
                    if payload['id'] in index['records']:continue
                    prior=candidates.get(payload['id'])
                    if prior is None or payload['revision']>prior['payload']['revision']:
                        candidates[payload['id']]=dict(path=str(path),payload=payload,registered=False,state='unresolved',revision=payload['revision'])
                except (OSError,ValueError) as exc:errors.append(str(path)+': '+str(exc))
            records.extend(candidates.values())
        return dict(records=records,errors=errors)

    def draft(self, payload, current, *, library_uuid, book_uuid, choices=None):
        validate_payload(payload,self.owner)
        if payload['identity']['library_uuid']!=library_uuid or payload['identity']['book_uuid']!=book_uuid or current.get('uuid')!=book_uuid:
            raise ValueError('Recovery identity differs; refresh before review.')
        pending=payload['pending'];blocked=conflicts(payload['baseline'],current,pending)
        if set(pending)&{'series','series_index'}:
            for field in ('series','series_index'):
                expected=pending.get(field,payload['baseline'][field])
                if not equal(field,current[field],payload['baseline'][field]) and not equal(field,current[field],expected) and field not in blocked:blocked.append(field)
        if blocked and (choices is None or not set(blocked)<=set(choices)): return dict(conflicts=blocked,current=deepcopy(current),draft=None)
        if choices and any(v not in {'current','recovered'} for v in choices.values()): raise ValueError('Invalid recovery conflict choice.')
        draft=deepcopy(current)
        for field,value in pending.items():
            if not choices or choices.get(field,'recovered')=='recovered':draft[field]=deepcopy(value)
        for field in blocked:
            if choices[field]=='recovered':draft[field]=deepcopy(pending.get(field,payload['baseline'][field]))
        if not draft['series']:draft['series_index']=None
        return dict(conflicts=[],current=deepcopy(current),draft=draft)

    def resolve(self, payload, state):
        if state not in {'recovered', 'discarded'}:
            raise ValueError('Invalid recovery resolution.')
        validate_payload(payload, self.owner)
        with locked(self.folder):
            index = self._index(); entry = index['records'].get(payload['id'])
            if entry is None:
                path = self.folder/(payload['id']+'.'+str(payload['revision'])+'.json')
                entry = dict(path=str(path), revision=payload['revision'], state='unresolved')
            if entry['revision'] != payload['revision'] or self.read(entry['path']) != payload:
                raise ValueError('Recovery changed since review; existing copy retained.')
            entry['state'] = state; index['records'][payload['id']] = entry
            atomic_json(self.index, index)
        if self.activity:
            self.activity.record('Single-book recovery', payload['id'], outcome='discarded' if state=='discarded' else 'success',
                pending=False, recovery=False, details=dict(message='Recovery '+state, revision=payload['revision']))
            self.activity.invoke('resolve_notice', 'Single-book metadata saves', payload['operation_id'])

    def owned_paths(self, payload):
        with locked(self.folder):
            entry = self._index()['records'].get(payload['id'])
            if not entry or entry['state']=='unresolved': raise ValueError('Resolve recovery before deleting history.')
            paths = {Path(entry['path'])}
            paths.update(Path(p) for p in entry.get('generations', []))
            paths.update(self.folder.glob(payload['id']+'.*.json'))
            for path in paths:
                if self.read(path)['id'] != payload['id']: raise ValueError('Recovery file belongs to another operation.')
            return sorted(paths)

    def forget(self, identity):
        with locked(self.folder):
            index = self._index(); entry = index['records'].get(identity)
            if entry and entry['state']=='unresolved': raise ValueError('Cannot delete unresolved recovery registration.')
            index['records'].pop(identity, None); atomic_json(self.index, index)

    def sync_activity(self):
        result=self.discover()
        if self.activity:
            for record in result['records']:
                payload=record['payload']
                self.activity.record('Single-book recovery',payload['id'],
                    outcome='discarded' if record['state']=='discarded' else 'success' if record['registered'] else 'interrupted',
                    pending=record['state']=='unresolved',recovery=record['state']=='unresolved',
                    source=dict(kind='recovery',path=record['path'],recovery_id=payload['id'],save_operation_id=payload['operation_id'],**payload['identity']),
                    details=dict(revision=payload['revision'],fields=sorted(payload['pending'])),deduplicate=True,legacy=True)
            if result['errors']:self.activity.notify('Recovery discovery needs attention: '+'; '.join(result['errors']))
        return result
