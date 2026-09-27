"""M5 design-validation prototype. Not imported by the application."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from uuid import uuid4
from mediainator.import_store import atomic_json
from mediainator.metadata_rules import changes, conflicts, equal


def digest(payload):
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def capture(identity, baseline, draft):
    pending=changes(baseline,draft)
    fields=set(pending)
    if fields & {'series','series_index'}:fields.update(('series','series_index'))
    return dict(schema=1,id=str(uuid4()),identity=deepcopy(identity),state='unresolved',reviewed=False,
                pending=deepcopy(pending),baseline={f:deepcopy(baseline[f]) for f in fields})


def read(path, identity):
    envelope=json.loads(Path(path).read_text());payload=envelope['payload']
    if payload['schema']!=1 or digest(payload)!=envelope['sha256']:raise ValueError('Unsupported or damaged recovery copy; preserve for inspection.')
    if payload['identity']!=identity:raise ValueError('Recovery ownership or library/book identity differs.')
    return payload


def preserve(folder, registry, payload):
    folder=Path(folder);registry=Path(registry)
    path=folder/(payload['id']+'.json')
    atomic_json(path,dict(payload=payload,sha256=digest(payload)))
    if read(path,payload['identity'])!=payload:raise ValueError('Recovery read-back differs.')
    # A close is safe only after the alternate/default destination is discoverable.
    try:
        index=json.loads(registry.read_text())
        if index['schema']!=1 or not isinstance(index['records'],dict):raise ValueError('Unsupported recovery index.')
    except FileNotFoundError:
        index=dict(schema=1,records={})
    index['records'][payload['id']]=str(path)
    atomic_json(registry,index)
    if json.loads(registry.read_text())['records'][payload['id']]!=str(path):raise ValueError('Recovery registration failed.')
    return path


def reviewed_draft(payload, current, choices=None):
    pending=payload['pending'];blocked=conflicts(payload['baseline'],current,pending)
    if set(pending)&{'series','series_index'}:
        for field in ('series','series_index'):
            expected=pending.get(field,payload['baseline'][field])
            if not equal(field,current[field],payload['baseline'][field]) and not equal(field,current[field],expected) and field not in blocked:blocked.append(field)
    if blocked and (choices is None or not set(blocked)<=set(choices)):
        return None,blocked
    draft=deepcopy(current)
    for field,value in pending.items():
        if not choices or choices.get(field,'recovered')=='recovered':draft[field]=deepcopy(value)
    if choices:
        for field in blocked:
            if choices[field]=='recovered':draft[field]=pending.get(field,payload['baseline'][field])
    if not draft['series']:draft['series_index']=None
    return draft,[]


def dismiss(payload):
    payload['dismissed']=True


def discard(payload, confirmed):
    if not payload['reviewed'] or not confirmed:raise ValueError('Review and explicitly confirm Discard Pending first.')
    payload['state']='discarded';payload['pending']={}


def delete_allowed(payload):
    if payload['state']=='unresolved':raise ValueError('Unresolved recovery cannot be deleted.')
    return True


def close_allowed(close_requested, preserved, dirty_revision, preserved_revision):
    return close_requested and preserved and dirty_revision==preserved_revision
