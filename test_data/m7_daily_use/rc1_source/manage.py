"""Explicit local setup/copy/restore. Never stops containers or overwrites data."""
import argparse,hashlib,json,os,shutil,stat,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
IMAGE='sha256:da0d06cee1517cbbc0b0b8910c3303b6ad3b47377445a76e47994e977f885783'
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for data in iter(lambda:f.read(1024*1024),b''):h.update(data)
    return h.hexdigest()
def inventory(root):
    result={}
    for base,dirs,files in os.walk(root,followlinks=False):
        for name in dirs+files:
            p=Path(base)/name;key=str(p.relative_to(root));s=p.lstat()
            if stat.S_ISLNK(s.st_mode):result[key]={'link':os.readlink(p)}
            elif stat.S_ISREG(s.st_mode):result[key]={'sha256':digest(p),'mode':stat.S_IMODE(s.st_mode)}
            elif stat.S_ISDIR(s.st_mode):result[key]={'directory':True,'mode':stat.S_IMODE(s.st_mode)}
            else:raise RuntimeError('Special file cannot be backed up: '+str(p))
    return result
def overlap(a,b):return a==b or a.is_relative_to(b) or b.is_relative_to(a)
def quiet(root):
    ids=subprocess.check_output(['docker','ps','-q'],text=True).split()
    if ids:
        for container in json.loads(subprocess.check_output(['docker','inspect',*ids])):
            for mount in container['Mounts']:
                source=mount.get('Source')
                if source and overlap(root,Path(source).resolve()):
                    raise RuntimeError('Close the Hub/readers first; a running container mounts this environment.')
def check_payload(root):
    assert all((root/n).is_dir() and not (root/n).is_symlink() for n in ('home','library','import-sources')),'Expected home/library/import-sources directories'
    assert (root/'library/metadata.db').is_file(),'Expected a dedicated Calibre test library'
def independent(a,b):
    assert not overlap(a,b),'Source and destination must be separate, non-overlapping paths'
def verify_bundle():
    manifest=json.loads((ROOT/'FILES.json').read_text())
    for name,expected in manifest.items():
        p=ROOT/name
        assert p.is_file() and not p.is_symlink() and digest(p)==expected,'Bundle integrity failure: '+name
    return manifest
parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='action',required=True)
c=sub.add_parser('configure');c.add_argument('--state-root',type=Path,required=True)
sub.add_parser('load-image');sub.add_parser('verify-bundle')
b=sub.add_parser('backup');b.add_argument('state',type=Path);b.add_argument('destination',type=Path)
r=sub.add_parser('restore');r.add_argument('backup',type=Path);r.add_argument('destination',type=Path)
a=parser.parse_args()
if a.action=='verify-bundle':verify_bundle();print('Bundle checksums verified')
elif a.action=='load-image':
    verify_bundle();subprocess.run(['docker','load','-i',str(ROOT/'image.tar')],check=True)
    actual=subprocess.check_output(['docker','image','inspect','--format','{{.Id}}',IMAGE],text=True).strip()
    assert actual==IMAGE;print('Pinned image available')
elif a.action=='configure':
    verify_bundle()
    state=a.state_root.expanduser().resolve();assert not state.is_relative_to(ROOT),'Store data outside the frozen bundle'
    socket=Path(os.environ['XDG_RUNTIME_DIR'])/os.environ.get('WAYLAND_DISPLAY','wayland-0');assert socket.is_socket(),'Native KDE Wayland session required'
    for value in (str(state),str(socket)):
        assert not any(c in value for c in "\n\r'$"),'Unsupported env-file path characters'
    assert not (ROOT/'.env').exists(),'Existing .env retained; edit it explicitly or use another extracted bundle'
    for folder in ('home','library','import-sources'):(state/folder).mkdir(parents=True,exist_ok=True)
    (ROOT/'.env').write_text(f"APP_UID={os.getuid()}\nAPP_GID={os.getgid()}\nSTATE_ROOT='{state}'\nWAYLAND_SOCKET='{socket}'\nCOMPOSE_PROJECT_NAME=mediainator-rc1\n")
    (ROOT/'.env').chmod(0o600);print('Configured. Copy your dedicated library into '+str(state/'library')+' before first use.')
elif a.action=='backup':
    source=a.state.expanduser().resolve();target=a.destination.expanduser().resolve();independent(source,target)
    check_payload(source);quiet(source);assert not target.exists(),'Backup destination already exists'
    before=inventory(source);target.mkdir(parents=True)
    shutil.copytree(source,target/'data',symlinks=True)
    quiet(source);assert inventory(source)==before and inventory(target/'data')==before,'Source changed or copy differs; incomplete backup retained'
    (target/'manifest.json').write_text(json.dumps({'schema':1,'inventory':before,'image':IMAGE},indent=2)+'\n');print('Backup verified:',target)
elif a.action=='restore':
    backup=a.backup.expanduser().resolve();target=a.destination.expanduser().resolve();independent(backup,target)
    assert not target.exists(),'Restore destination already exists; original environments are never overwritten'
    manifest=json.loads((backup/'manifest.json').read_text());assert manifest['schema']==1
    source=backup/'data';check_payload(source);quiet(source)
    assert inventory(source)==manifest['inventory'],'Backup integrity mismatch'
    shutil.copytree(source,target,symlinks=True)
    assert inventory(source)==manifest['inventory'] and inventory(target)==manifest['inventory'],'Restore verification failed'
    print('Restore verified:',target,'— use a separate Compose configuration with the same internal paths; do not overwrite active state.')
