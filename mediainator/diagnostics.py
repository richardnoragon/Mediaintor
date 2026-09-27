"""Allowlisted, local diagnostics. Never serialize arbitrary application objects."""
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import tempfile
import threading
from . import __version__

MESSAGES = {
    'metadata-failure':'A metadata operation failed.',
    'import-failure':'An import operation failed.',
    'activity-storage-failure':'Activity storage could not be read or written.',
    'settings-failure':'Settings could not be saved.',
    'refresh-failure':'Catalog refresh failed or was interrupted.',
    'reader-failure':'A reader launch failed.',
    'recovery-failure':'Recovery or preservation needs attention.',
    'operation-failure':'An operation needs attention.',
}
OPERATIONS = {'Settings save':'settings-failure','Catalog refresh':'refresh-failure',
              'Reader launch':'reader-failure','Emergency preservation':'recovery-failure',
              'Single-book recovery':'recovery-failure','Recovery discovery':'recovery-failure',
              'Single-book metadata saves':'metadata-failure'}
MODULES = frozenset('mediainator.'+name for name in ('metadata','imports','activity','settings','snapshot','library','reader','recovery','recovery_actions','editor','window','bulk_worker','compatibility'))
FUNCTIONS = frozenset(('run','run_request','call_helper','execute','save','load','create','record','invoke','check','require_compatible','probe_version','preserve','emergency_preserve','launch','persist','_read'))
CATEGORIES = {OSError:'OSError',RuntimeError:'RuntimeError',ValueError:'ValueError',TypeError:'TypeError',KeyError:'KeyError',PermissionError:'PermissionError',FileNotFoundError:'FileNotFoundError',TimeoutError:'TimeoutError'}
VALIDATION = frozenset(('verified','missing','unverified','inconsistent-toolchain','probe-failed','not-checked'))
FEATURES = ('bookinator_open','library_configured','activity_visible','recovery_enabled')
_events=deque(maxlen=50)
_lock=threading.Lock()
_dropped=0


def record_error(code, exc=None):
    """Retain only sanitized primitives, never exception instances or raw messages."""
    global _dropped
    code=code if type(code) is str and code in MESSAGES else 'operation-failure'
    event={'code':code,'message':MESSAGES[code], 'time':datetime.now(timezone.utc).isoformat(),
           'category':CATEGORIES.get(type(exc),'OtherError') if exc is not None else 'Unspecified',
           'frames':[], 'omitted_frames':0, 'exception_text_omitted':exc is not None}
    tb=exc.__traceback__ if isinstance(exc,BaseException) else None
    count=0
    while tb is not None and count<128:
        module=tb.tb_frame.f_globals.get('__name__');function=tb.tb_frame.f_code.co_name
        if type(module) is str and module in MODULES and function in FUNCTIONS and len(event['frames'])<12:
            event['frames'].append({'module':module,'function':function,'line':min(max(tb.tb_lineno,0),1000000)})
        else:event['omitted_frames']+=1
        tb=tb.tb_next;count+=1
    if tb is not None:event['omitted_frames']+=1
    with _lock:
        if len(_events)==_events.maxlen:_dropped+=1
        _events.append(event)


def record_operation(operation,outcome):
    if type(outcome) is str and outcome in ('failure','partial','interrupted'):
        code=OPERATIONS.get(operation,'operation-failure') if type(operation) is str else 'operation-failure'
        record_error(code)


def safe_version(value):
    if type(value) is str and len(value)<=48 and re.fullmatch(r'[0-9]+(?:\.[0-9]+){1,3}(?:(?:a|b|rc)[0-9]+)?',value):return value
    return 'unavailable'


def dependency_version(name):
    try:return safe_version(importlib.metadata.version(name))
    except (importlib.metadata.PackageNotFoundError,OSError,ValueError):return 'unavailable'


def kde_version():
    # Fixed package query; never inventory unrelated software or export command output.
    try:
        result=subprocess.run(['/usr/bin/dpkg-query','-W','-f=${Version}','plasma-workspace'],capture_output=True,timeout=2)
        if result.returncode or len(result.stdout)>128:return 'unavailable'
        match=re.fullmatch(rb'(?:[0-9]+:)?([0-9]+\.[0-9]+\.[0-9]+)(?:-[0-9A-Za-z.+~]+)?',result.stdout.strip())
        return safe_version(match[1].decode()) if match else 'unavailable'
    except (OSError,subprocess.SubprocessError):return 'unavailable'


@dataclass(frozen=True)
class Snapshot:
    payload: bytes


def collect_snapshot(features=None,validation=None,detected=None):
    from PyQt6.QtCore import qVersion
    # Caller passes typed flags and status only, never a settings or Activity dump.
    flags=features if type(features) is dict else {}
    status=validation if type(validation) is str and validation in VALIDATION else 'not-checked'
    try:os_info=platform.freedesktop_os_release()
    except OSError:os_info={}
    with _lock:
        events=json.loads(json.dumps(list(_events)))
        dropped=_dropped
    tools={}
    if type(detected) is str and len(detected)<256:
        names=('calibre','calibredb','calibre-debug','ebook-viewer')
        pattern=', '.join(re.escape(name)+r' ([0-9]+\.[0-9]+\.[0-9]+)' for name in names)
        match=re.fullmatch(pattern,detected)
        if match:tools={name:safe_version(value) for name,value in zip(names,match.groups())}
    report={'schema':1,'scope':'current session; raw logs and recovery data are not read',
            'versions':{'application':safe_version(__version__),'python':safe_version(platform.python_version()),
                        'PyQt6':dependency_version('PyQt6'),'PyQt6-sip':dependency_version('PyQt6-sip'),
                        'Qt':safe_version(qVersion()),'KDE':kde_version(),
                        'OS':'ubuntu' if os_info.get('ID')=='ubuntu' else 'unavailable',
                        'OS_version':safe_version(os_info.get('VERSION_ID')),'Calibre_tools_at_last_check':tools},
            'environment_validation':{'last_ui_check':status,'calibre_supported':'9.2.1',
                'note':'This export does not run compatibility checks. Use Recheck prerequisites for a fresh result.'},
            'features':{key:flags[key] for key in FEATURES if type(flags.get(key)) is bool},
            'events':events,'omissions':{'older_session_events':dropped,
                'stack_frames':sum(e['omitted_frames'] for e in events),
                'exception_texts':sum(e['exception_text_omitted'] for e in events),
                'raw_sources_excluded':['logs','settings','environment','book metadata','library paths and names','recovery contents','backup locations','user notes']}}
    return Snapshot((json.dumps(report,ensure_ascii=True,indent=2,sort_keys=True)+'\n').encode('utf-8'))


def write_snapshot(path,snapshot):
    """Atomic local write of the already-previewed bytes; original survives failure."""
    path=Path(path)
    if path.is_symlink():raise ValueError('Symlink export destination is not supported.')
    fd,temp=tempfile.mkstemp(prefix='.mediainator-diagnostics-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream:
            os.fchmod(stream.fileno(),0o600)
            stream.write(snapshot.payload);stream.flush();os.fsync(stream.fileno())
        os.replace(temp,path)
    finally:
        if os.path.exists(temp):os.unlink(temp)
