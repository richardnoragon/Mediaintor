"""Versioned, owner-scoped workspace snapshots; no restoration side effects."""
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4
import fcntl
import json
import os
import stat
from PyQt6.QtCore import QSaveFile, QIODevice

LIMIT = 1024 * 1024
# Hub first, then open modules in registry order.
WORKSPACE_MODULES = ('bookinator', 'musicinator', 'movieinator', 'paperinator')
MODULE_SETS = tuple(['hub'] + [m for i, m in enumerate(WORKSPACE_MODULES) if mask >> i & 1]
                    for mask in range(2 ** len(WORKSPACE_MODULES)))
# Optional per-module selections: key → (module, identity fields). Absent keys keep
# snapshots written before that module existed valid.
MODULE_SELECTIONS = {'movie_selection': ('movieinator', {'catalog_uuid', 'movie_id'}),
                     'music_selection': ('musicinator', {'catalog_uuid', 'album_id'}),
                     'paper_selection': ('paperinator', {'library_uuid', 'item_id'})}
class WorkspaceError(ValueError):
    pass


def uuid(value):
    if not isinstance(value, str): raise WorkspaceError('Invalid workspace identity')
    try: UUID(value)
    except ValueError as exc: raise WorkspaceError('Invalid workspace identity') from exc


def snapshot(value):
    try:
        # Module selections are optional so snapshots written before those modules stay valid.
        if not {'modules','active','selection','geometry'} <= set(value) <= {'modules','active','selection','geometry',*MODULE_SELECTIONS}: raise ValueError()
        if value['modules'] not in MODULE_SETS: raise ValueError()
        if value['active'] not in value['modules']: raise ValueError()
        for key,(module,fields) in MODULE_SELECTIONS.items():
            chosen=value.get(key)
            if chosen is not None:
                if set(chosen) != fields or module not in value['modules']: raise ValueError()
                for field in fields: uuid(chosen[field])
        selection=value['selection']
        if selection is not None:
            if set(selection) != {'library_uuid','book_uuid'}: raise ValueError()
            uuid(selection['library_uuid']); uuid(selection['book_uuid'])
            if 'bookinator' not in value['modules']: raise ValueError()
        g=value['geometry']
        if set(g) != {'qt','normal','maximized','screen','available'}: raise ValueError()
        if not isinstance(g['qt'],str) or len(g['qt'])>32768: raise ValueError()
        bytes.fromhex(g['qt'])
        if type(g['maximized']) is not bool or not isinstance(g['screen'],str) or len(g['screen'])>1024: raise ValueError()
        for key in ('normal','available'):
            rect=g[key]
            if not isinstance(rect,list) or len(rect)!=4 or any(type(n) is not int or abs(n)>1000000 for n in rect) or min(rect[2:])<=0: raise ValueError()
    except (TypeError,KeyError,ValueError) as exc: raise WorkspaceError('Invalid workspace snapshot; original file preserved') from exc
    return deepcopy(value)


def name(value):
    if not isinstance(value,str) or not value.strip() or len(value.strip())>80 or any(ord(c)<32 for c in value):
        raise WorkspaceError('Use a workspace name of 1–80 printable characters')
    return value.strip()


def now(): return datetime.now(timezone.utc).isoformat()

class WorkspaceStore:
    def __init__(self,path,profile_id,device_id,initial):
        uuid(profile_id); uuid(device_id)
        self.path=Path(path); self.owner=dict(profile_id=profile_id,device_id=device_id)
        self.initial=snapshot(initial)

    def validate(self,data):
        try:
            if set(data)!={'schema','owner','revision','last_session','startup','named'}: raise ValueError()
            if type(data['schema']) is not int or data['schema']!=1 or data['owner']!=self.owner: raise ValueError()
            if type(data['revision']) is not int or data['revision']<0: raise ValueError()
            named=data['named']
            if not isinstance(named,dict) or len(named)>5: raise ValueError()
            if data['startup']!='last_session' and data['startup'] not in named: raise ValueError()
            entries=[data['last_session']]
            names=set()
            for key,entry in named.items():
                uuid(key)
                if set(entry)!={'name','snapshot','saved_at'}: raise ValueError()
                normalized=name(entry['name'])
                if normalized!=entry['name'] or normalized.casefold() in names: raise ValueError()
                names.add(normalized.casefold());entries.append(entry)
            if set(data['last_session'])!={'snapshot','saved_at'}: raise ValueError()
            for entry in entries:
                snapshot(entry['snapshot'])
                stamp=datetime.fromisoformat(entry['saved_at'])
                if stamp.tzinfo is None: raise ValueError()
        except (TypeError,KeyError,ValueError,AttributeError) as exc:
            raise WorkspaceError('Unsupported, damaged or differently owned workspace file; original preserved') from exc
        return deepcopy(data)

    def load(self):
        try:
            fd=os.open(self.path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
            with os.fdopen(fd,'rb') as stream:
                if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode): raise WorkspaceError('Workspace file is not a regular file')
                raw=stream.read(LIMIT+1)
            if len(raw)>LIMIT: raise WorkspaceError('Workspace file exceeds size limit')
            return self.validate(json.loads(raw))
        except FileNotFoundError:
            return dict(schema=1,owner=self.owner,revision=0,last_session=dict(snapshot=deepcopy(self.initial),saved_at=now()),startup='last_session',named={})
        except (OSError,ValueError,RecursionError) as exc:
            raise WorkspaceError('Cannot read workspace file; original preserved: '+str(exc)) from exc

    def change(self,revision,operation):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.path.with_suffix('.lock').open('a') as lock:
            try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError as exc: raise WorkspaceError('Workspace file busy; retry') from exc
            current=self.load()
            if current['revision']!=revision: raise WorkspaceError('Workspaces changed; reload before retrying')
            updated=deepcopy(current); result=operation(updated)
            updated['revision']+=1; self.validate(updated)
            raw=json.dumps(updated,ensure_ascii=False,indent=2).encode()
            if len(raw)>LIMIT: raise WorkspaceError('Workspace file exceeds size limit')
            target=QSaveFile(str(self.path));target.setDirectWriteFallback(False)
            if not target.open(QIODevice.OpenModeFlag.WriteOnly): raise WorkspaceError('Cannot open workspace save')
            if target.write(raw)!=len(raw): target.cancelWriting();raise WorkspaceError('Workspace write failed; previous file retained')
            if not target.commit(): raise WorkspaceError('Workspace commit failed; previous file retained')
            return result

    def save_named(self,revision,label,value,replace=None,overwrite=None):
        label=name(label);value=snapshot(value)
        if replace and overwrite: raise WorkspaceError('Choose replacement or overwrite')
        def apply(data):
            named=data['named']; target=overwrite or replace
            if target and target not in named: raise WorkspaceError('Workspace no longer exists')
            if any(k!=target and v['name'].casefold()==label.casefold() for k,v in named.items()): raise WorkspaceError('Name already exists; explicitly overwrite it')
            if len(named)==5 and not target: raise WorkspaceError('Choose a workspace to replace or Cancel')
            if replace:
                del named[replace]
                if data['startup']==replace:data['startup']='last_session'
            key=overwrite or str(uuid4());named[key]=dict(name=label,snapshot=value,saved_at=now());return key
        return self.change(revision,apply)

    def rename(self,revision,key,label):
        label=name(label)
        def apply(data):
            if key not in data['named']: raise WorkspaceError('Workspace no longer exists')
            if any(k!=key and e['name'].casefold()==label.casefold() for k,e in data['named'].items()):raise WorkspaceError('Name already exists')
            data['named'][key]['name']=label
        self.change(revision,apply)

    def delete(self,revision,key):
        def apply(data):
            if key not in data['named']:raise WorkspaceError('Workspace no longer exists')
            del data['named'][key]
            if data['startup']==key:data['startup']='last_session'
        self.change(revision,apply)

    def set_startup(self,revision,key):
        def apply(data):
            if key!='last_session' and key not in data['named']:raise WorkspaceError('Workspace no longer exists')
            data['startup']=key
        self.change(revision,apply)

    def save_last_session(self,revision,value):
        value=snapshot(value)
        self.change(revision,lambda data:data.update(last_session=dict(snapshot=value,saved_at=now())))
