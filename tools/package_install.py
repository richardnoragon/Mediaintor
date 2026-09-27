"""Offline current-user installer. It never reads or writes a Calibre library."""
import base64
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def safe_directory(path):
    for component in (path, *path.parents):
        if component.is_symlink():
            raise ValueError(f'Refusing symlink directory: {component}')
    path.mkdir(parents=True, exist_ok=True)


def read_bundle(path):
    files = {}
    total = 0
    with tarfile.open(path, 'r:gz') as archive:
        for member in archive:
            parts = PurePosixPath(member.name)
            if (not member.isfile() or parts.is_absolute() or '..' in parts.parts
                    or str(parts) != member.name or member.name in files):
                raise ValueError('Unsafe or duplicate archive entry.')
            total += member.size
            if member.size > 16*1024*1024 or total > 64*1024*1024:
                raise ValueError('Package exceeds size limits.')
            files[member.name] = archive.extractfile(member).read()
    manifest = json.loads(files['manifest.json'])
    if manifest['schema'] != 1 or not re.fullmatch(r'[A-Za-z0-9.]+', manifest['version']):
        raise ValueError('Unsupported package manifest.')
    hashes = {name: digest(data) for name, data in sorted(files.items()) if name != 'manifest.json'}
    if hashes != manifest['files']:
        raise ValueError('Package checksum mismatch.')
    build_id = digest(json.dumps(hashes, sort_keys=True).encode())[:16]
    if manifest['build_id'] != build_id:
        raise ValueError('Invalid build identity.')
    required = {'run.py','runtime.json','mediainator.desktop.in','mediainator.svg','mediainator/__main__.py'}
    if not required <= files.keys():
        raise ValueError('Incomplete package.')
    return files, manifest


def clean_env():
    env = {k:v for k,v in os.environ.items() if not k.startswith(('PYTHON','QT_'))
           and k not in ('QML_IMPORT_PATH','QML2_IMPORT_PATH')}
    env['QT_QPA_PLATFORM'] = 'offscreen'
    return env


def check_runtime(required):
    os_info = platform.freedesktop_os_release()
    if os_info['ID'] != required['os_id'] or os_info['VERSION_ID'] != required['os_version'] or platform.machine() != required['architecture']:
        raise ValueError('This package requires Ubuntu 26.04 x86_64; existing installation unchanged.')
    code = "import json,platform,importlib.metadata as m; from PyQt6.QtCore import qVersion; from PyQt6.QtWidgets import QApplication; a=QApplication([]); print(json.dumps({'python':platform.python_version(),'PyQt6':m.version('PyQt6'),'PyQt6-sip':m.version('PyQt6-sip'),'Qt':qVersion()}))"
    result = subprocess.run(['/usr/bin/python3','-I','-B','-c',code], env=clean_env(),capture_output=True,text=True,timeout=30)
    if result.returncode:
        raise ValueError('System Python/PyQt6 runtime unavailable. See INSTALL.md; no dependencies were installed.')
    actual=json.loads(result.stdout)
    if any(actual[k] != required[k] for k in actual):
        raise ValueError(f'Unverified runtime: {actual}; required: '+str({k:required[k] for k in actual}))
    return actual


def desktop_quote(value):
    # Exec has its own quoting layer, followed by desktop-entry string escaping.
    value=value.replace('%','%%')
    value='"'+''.join('\\'+c if c in '\\"`$' else c for c in value)+'"'
    return value.replace('\\','\\\\')


def atomic(path, data, mode=0o644):
    fd, temporary=tempfile.mkstemp(prefix='.mediainator-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as output:
            output.write(data);output.flush();os.fsync(output.fileno())
        os.chmod(temporary,mode);os.replace(temporary,path)
        sync_dir(path.parent)
    finally:
        if os.path.exists(temporary):os.unlink(temporary)


def sync_dir(path):
    fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)


def release_files(folder):
    if folder.is_symlink():raise ValueError('Unsafe release symlink.')
    result={}
    for path in folder.rglob('*'):
        if path.is_symlink():raise ValueError('Unexpected release symlink.')
        if path.is_file():result[str(path.relative_to(folder))]=digest(path.read_bytes())
    return result


def finish_transaction(base,launcher,desktop):
    """Explicit, repeatable completion of a previously recorded install/uninstall."""
    journal=base/'transaction.json'
    if journal.is_symlink():raise ValueError('Unsafe transaction journal.')
    tx=json.loads(journal.read_text())
    if tx.get('schema')!=1 or tx.get('action') not in ('install','uninstall'):
        raise ValueError('Unsupported installation transaction; files retained.')
    state=tx['state'];expected_paths={str(launcher),str(desktop)}
    safe_directory(base/'releases')
    if state['current'] not in state['releases']:raise ValueError('Invalid transaction current release.')
    if set(state['integration'])!=expected_paths or set(tx['previous'])!=expected_paths|{str(base/'installation.json')}:
        raise ValueError('Transaction paths do not match current user installation.')
    for rel,expected in state['releases'].items():
        if not re.fullmatch(r'[A-Za-z0-9.]+-[a-f0-9]{16}',rel):raise ValueError('Invalid release identity.')
        actual=release_files(base/'releases'/rel)
        if tx['action']=='install' and actual!=expected:raise ValueError('Release files changed; cannot complete installation.')
        if tx['action']=='uninstall' and any(expected.get(k)!=v for k,v in actual.items()):
            raise ValueError('Release files changed; cannot complete uninstall.')
    current=base/'current'
    allowed={tx.get('old_current'),'releases/'+state['current']}
    if current.is_symlink():
        if os.readlink(current) not in allowed:raise ValueError('Current pointer changed; transaction stopped.')
    elif current.exists():raise ValueError('Current pointer is not a symlink.')
    elif tx['action']=='install' and tx.get('old_current') is not None:
        raise ValueError('Previous current pointer was removed; files retained.')
    state_path=base/'installation.json'
    target_state=(json.dumps(state,indent=2)+'\n').encode()
    # Preflight all integration files before making any further changes.
    for name,old in tx['previous'].items():
        path=Path(name)
        if path.is_symlink():raise ValueError('Unexpected integration symlink.')
        now=digest(path.read_bytes()) if path.exists() else None
        target=digest(target_state) if path==state_path else state['integration'][name]
        permitted={old,target}
        if tx['action']=='uninstall':permitted.add(None)
        if now not in permitted:raise ValueError('Integration file changed; transaction stopped without overwrite.')
    if tx['action']=='install':
        if set(tx['payloads'])!=expected_paths:raise ValueError('Invalid integration payloads.')
        payloads={name:base64.b64decode(data,validate=True) for name,data in tx['payloads'].items()}
        if any(digest(data)!=state['integration'][name] for name,data in payloads.items()):raise ValueError('Damaged integration payload.')
        atomic(launcher,payloads[str(launcher)],0o755);atomic(desktop,payloads[str(desktop)])
        atomic(state_path,target_state,0o600)
        pointer=base/'.current-new'
        if pointer.is_symlink():
            if os.readlink(pointer)!='releases/'+state['current']:raise ValueError('Unexpected staged pointer.')
            pointer.unlink()
        elif pointer.exists():raise ValueError('Unexpected staged pointer.')
        pointer.symlink_to('releases/'+state['current']);os.replace(pointer,current);sync_dir(base)
    else:
        for path in (launcher,desktop,current):
            if path.exists() or path.is_symlink():path.unlink();sync_dir(path.parent)
        for rel in state['releases']:
            folder=base/'releases'/rel
            # Only preflighted, unchanged manifest files are removed; retained app data is elsewhere.
            if folder.exists():shutil.rmtree(folder)
        sync_dir(base/'releases')
        if state_path.exists():state_path.unlink();sync_dir(base)
    journal.unlink();sync_dir(base)


def start_transaction(base,action,state,launcher,desktop,payloads=None):
    previous={str(p):digest(p.read_bytes()) if p.exists() else None for p in (launcher,desktop,base/'installation.json')}
    tx={'schema':1,'action':action,'state':state,'previous':previous,
        'old_current':os.readlink(base/'current') if (base/'current').is_symlink() else None,
        'payloads':{name:base64.b64encode(data).decode() for name,data in (payloads or {}).items()}}
    atomic(base/'transaction.json',(json.dumps(tx,indent=2)+'\n').encode(),0o600)
    finish_transaction(base,launcher,desktop)


def integration_paths():
    home=Path.home()
    data=Path(os.environ.get('XDG_DATA_HOME',str(home/'.local/share')))
    if not data.is_absolute():raise ValueError('XDG_DATA_HOME must be absolute.')
    if any(c in str(home)+str(data) for c in '\n\r\t'):
        raise ValueError('Installation paths cannot contain control characters.')
    return home/'.local/share/mediainator-install',home/'.local/bin/mediainator',data/'applications/mediainator.desktop'


def verify_owned(state, base, launcher, desktop):
    allowed={str(launcher),str(desktop)}
    if set(state['integration']) != allowed:
        raise ValueError('Installation locations changed; restore the original XDG settings before updating.')
    for name, expected in state['integration'].items():
        p=Path(name)
        if p.is_symlink() or not p.is_file() or digest(p.read_bytes()) != expected:
            raise ValueError('Managed launcher/menu entry was changed; review it before proceeding.')
    for rel, hashes in state['releases'].items():
        if not re.fullmatch(r'[A-Za-z0-9.]+-[a-f0-9]{16}',rel):raise ValueError('Invalid installed release identity.')
        folder=base/'releases'/rel
        if folder.is_symlink():raise ValueError('Release directory was replaced by a symlink.')
        actual={}
        for p in folder.rglob('*'):
            if p.is_symlink():raise ValueError('Unexpected installed symlink.')
            if p.is_file():actual[str(p.relative_to(folder))]=digest(p.read_bytes())
        if actual != hashes:raise ValueError('Installed program files changed; refusing destructive cleanup.')
    current=base/'current'
    if not current.is_symlink() or os.readlink(current) != 'releases/'+state['current']:
        raise ValueError('Current release pointer changed unexpectedly.')


def run(action, archive=None, yes=False):
    if os.geteuid()==0:raise ValueError('Per-user installation must not run as root.')
    files=manifest=None
    if action=='install':
        files,manifest=read_bundle(archive)
        check_runtime(json.loads(files['runtime.json']))
    base,launcher,desktop=integration_paths()
    for p in (base,launcher.parent,desktop.parent):safe_directory(p)
    lock_path=base/'install.lock'
    if lock_path.is_symlink():raise ValueError('Unsafe installation lock.')
    with lock_path.open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise ValueError('Media-inator or another installer is running.')
        # Also guard a development launch using the existing application identity.
        from PyQt6.QtCore import QCoreApplication,QStandardPaths,QLockFile
        app=QCoreApplication.instance() or QCoreApplication([])
        app.setApplicationName('Media-inator');app.setOrganizationName('Media-inator')
        config=Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation))
        safe_directory(config)
        app_lock=QLockFile(str(config/'instance.lock'))
        if not app_lock.tryLock(0):raise ValueError('Close Media-inator before modifying its installation.')
        try:
            pending=base/'transaction.json'
            if pending.exists() or pending.is_symlink():
                if action!='repair':raise ValueError('An interrupted installation action is pending. Run this installer with repair to complete it; user data is retained.')
                finish_transaction(base,launcher,desktop)
                print('Interrupted installation action completed; application data retained.');return
            if action=='repair':print('No interrupted installation action.');return
            safe_directory(base/'releases')
            state_path=base/'installation.json'
            if state_path.is_symlink():raise ValueError('Unsafe installation state.')
            state=json.loads(state_path.read_text()) if state_path.exists() else None
            if state:verify_owned(state,base,launcher,desktop)
            elif any(p.exists() or p.is_symlink() for p in (launcher,desktop,base/'current')):
                raise ValueError('Unmanaged installation entry exists; refusing overwrite.')
            if action=='uninstall':
                if not state:raise ValueError('No managed installation found.')
                if not yes and input('Remove program files only; retain all libraries and application data? [y/N] ').lower()!='y':
                    print('Cancelled.');return
                start_transaction(base,'uninstall',state,launcher,desktop)
                print('Uninstalled program files; all application data retained.');return
            release=manifest['version']+'-'+manifest['build_id']
            folder=base/'releases'/release
            safe_directory(folder.parent)
            new=not folder.exists()
            if not new and (not state or release not in state['releases']):
                if release_files(folder)!={k:digest(v) for k,v in files.items()}:raise ValueError('Unmanaged release directory exists.')
            old={p:(p.read_bytes(),p.stat().st_mode & 0o777) if p.exists() else None for p in (launcher,desktop,state_path)}
            try:
                if new:
                    staging=Path(tempfile.mkdtemp(prefix='.staging-',dir=folder.parent))
                    for name,data in files.items():
                        p=staging/name;p.parent.mkdir(parents=True,exist_ok=True);atomic(p,data)
                    for directory in sorted((p for p in staging.rglob('*') if p.is_dir()),key=lambda p:len(p.parts),reverse=True):sync_dir(directory)
                    sync_dir(staging);os.replace(staging,folder);sync_dir(folder.parent)
                check=subprocess.run(['/usr/bin/python3','-I','-B',str(folder/'run.py'),'--package-check'],env=clean_env(),capture_output=True,text=True,timeout=30)
                if check.returncode:raise ValueError('Installed application import check failed; prior release retained.')
                launcher_data=('#!/bin/sh\nif [ -e '+shlex.quote(str(base/'transaction.json'))+' ]; then\n  echo "Installation action interrupted. Run the trusted installer with repair; application data is retained." >&2\n  exit 1\nfi\nexec /usr/bin/python3 -I -B '+shlex.quote(str(base/'current/run.py'))+' "$@"\n').encode()
                template=files['mediainator.desktop.in'].decode()
                # Icon is a desktop string, not an Exec argument.
                icon=str(base/'current/mediainator.svg').replace('\\','\\\\')
                desktop_data=template.replace('@EXEC@',desktop_quote(str(launcher))).replace('@ICON@',icon).encode()
                releases=dict(state['releases']) if state else {}
                releases[release]={k:digest(v) for k,v in files.items()}
                new_state={'current':release,'releases':releases,'integration':{str(launcher):digest(launcher_data),str(desktop):digest(desktop_data)}}
                start_transaction(base,'install',new_state,launcher,desktop,{str(launcher):launcher_data,str(desktop):desktop_data})
            except Exception:
                if (base/'transaction.json').exists():
                    raise ValueError('Installation action interrupted. Run this installer with repair; prior release files and user data are retained.')
                for p,previous in old.items():
                    if previous:atomic(p,*previous)
                    elif p.exists():p.unlink()
                # current is replaced only as the final activation step.
                if new and folder.exists():shutil.rmtree(folder)
                raise
            print('Installed '+release+' for the current user. Calibre remains separately managed.')
        finally:app_lock.unlock()

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='action',required=True)
    install=sub.add_parser('install');install.add_argument('archive',type=Path)
    uninstall=sub.add_parser('uninstall');uninstall.add_argument('--yes',action='store_true')
    sub.add_parser('repair',help='Complete a previously journaled installation/uninstall; retain user data')
    args=parser.parse_args()
    try:run(args.action,getattr(args,'archive',None),getattr(args,'yes',False))
    except (ValueError,OSError,KeyError,TypeError,subprocess.SubprocessError) as exc:
        print('Installation action stopped: '+str(exc),file=sys.stderr);sys.exit(1)
