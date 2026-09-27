"""Prepare an independent M11 everyday copy and isolated restore checks."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[2];evidence=ROOT/'test_data/m11_promotion'
source=ROOT.parent/'Mediaintor-M10-Development';target=ROOT.parent/'Mediaintor-M11-Everyday'
archive=ROOT/'dist/m10/mediainator-0.1.0a1-ubuntu26.04-x86_64.tar.gz'
sha='edc96793ca09a37db7a15bbd1036db96f2c771cff43b16563796590a8805b1f4'
expected='0.1.0a1-a3a4679f39f4c255';image='sha256:da0d06cee1517cbbc0b0b8910c3303b6ad3b47377445a76e47994e977f885783'
launcher=Path.home()/'.local/share/applications/mediainator-m11-everyday.desktop'
manage=ROOT.parent/'Mediaintor-M7-Testing/releases/mediainator-rc1/manage.py'
def run(args,cwd=None):
 p=subprocess.run(list(map(str,args)),cwd=cwd,capture_output=True,text=True,timeout=180)
 if p.returncode:raise RuntimeError(p.stdout+p.stderr)
 return p.stdout
assert not target.exists() and not launcher.exists(),'Destination exists; inspect rather than overwrite'
assert not run(['docker','ps','-q']).strip(),'Close running test containers'
assert not set(run(['ps','-eo','comm=']).splitlines()) & {'calibre','ebook-viewer','calibre-paralle'},'Close Calibre/readers'
assert hashlib.sha256(archive.read_bytes()).hexdigest()==sha
assert shutil.disk_usage(ROOT).free>1024**3
assert Path('/run/user/1000/wayland-0').is_socket()
def hashes(folder):
 return {str(p.relative_to(folder)):('link:'+os.readlink(p) if p.is_symlink() else hashlib.sha256(p.read_bytes()).hexdigest()) for p in folder.rglob('*') if p.is_file() or p.is_symlink()}
before=hashes(source/'active');deployment_before=hashes(source/'deployment')
base=source/'active/home/.local/share/mediainator-install';state=json.loads((base/'installation.json').read_text());assert state['current']==expected
assert hashes(base/'releases'/expected)==state['releases'][expected]
target.mkdir();backup=target/'backups/m10-promotion-source'
print(run([sys.executable,manage,'backup',source/'active',backup]),flush=True)
print(run([sys.executable,manage,'restore',backup,target/'active']),flush=True)
shutil.copytree(source/'deployment',target/'deployment');shutil.copytree(source/'artifacts',target/'artifacts')
shutil.copy2(archive,target/'artifacts/candidate.tar.gz')
deploy=target/'deployment'
for name in ('.env','docker-compose.yml','launch.py','runtime.py'):
 p=deploy/name;s=p.read_text().replace(str(source),str(target)).replace('mediainator-m10','mediainator-m11').replace('M10','M11');p.write_text(s)
def container(folder,args,extra=()):
 cmd=['docker','run','--rm','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--user','1000:1000','--tmpfs','/tmp:rw,mode=1777','-e','QT_QPA_PLATFORM=offscreen']
 for child,mount in [('home','/home/mediainator'),('library','/data/library'),('import-sources','/data/import-sources')]:cmd+=['-v',f'{folder/child}:{mount}']
 return run(cmd+list(extra)+['--entrypoint',args[0],image]+args[1:])
install=container(target/'active',['/usr/bin/python3','-I','-B','/installer.py','install','/candidate.tar.gz'],['-v',f'{deploy/"package_install.py"}:/installer.py:ro','-v',f'{target/"artifacts/candidate.tar.gz"}:/candidate.tar.gz:ro'])
verified=container(target/'active',['/usr/bin/python3','-I','-B','/runtime.py'],['-v',f'{deploy/"runtime.py"}:/runtime.py:ro'])
smoke=json.loads(container(target/'active',['/home/mediainator/.local/bin/mediainator','--package-smoke']))
probe=lambda folder:json.loads(container(folder,['/usr/bin/python3','-I','-B','/probe.py'],['-v',f'{evidence/"probe.py"}:/probe.py:ro']))
functional=probe(target/'active')
# All copied user data must be byte-identical; installer integration is separately verified.
after=hashes(target/'active')
exclude=('home/.local/share/mediainator-install/','home/.local/bin/','home/.local/share/applications/')
assert {k:v for k,v in before.items() if not k.startswith(exclude)}=={k:v for k,v in after.items() if not k.startswith(exclude)},'User data changed during promotion'
post=target/'backups/m11-installed'
print(run([sys.executable,manage,'backup',target/'active',post]),flush=True)
print(run([sys.executable,manage,'restore',post,target/'restore-validation']),flush=True)
restored=probe(target/'restore-validation');assert restored==functional
restored_smoke=json.loads(container(target/'restore-validation',['/home/mediainator/.local/bin/mediainator','--package-smoke']))
# Snapshot fallback to the preserved source, then return to a new current-state restore.
print(run([sys.executable,manage,'restore',backup,target/'fallback-validation']),flush=True)
fallback=probe(target/'fallback-validation');assert fallback==functional
fallback_smoke=json.loads(container(target/'fallback-validation',['/home/mediainator/.local/bin/mediainator','--package-smoke']))
assert hashes(source/'active')==before and hashes(source/'deployment')==deployment_before
assert hashes(target/'active')==after,'Everyday state changed during isolated fallback tests'
launcher.write_text('[Desktop Entry]\nType=Application\nName=Media-inator Everyday (M11)\nExec=/usr/bin/python3 "'+str(deploy/'launch.py')+'"\nTerminal=false\nCategories=Office;\n')
run(['desktop-file-validate',launcher])
result=dict(status='automated promotion and isolated restore/fallback verified; personal KDE acceptance pending',root=str(target),source=str(source),build=expected,sha256=sha,source_backup=str(backup),installed_backup=str(post),launcher=str(launcher),compose_project='mediainator-m11',installation=install,inventory=verified,smoke=smoke,functional=functional,restored=restored,fallback=fallback,restored_smoke=restored_smoke,fallback_smoke=fallback_smoke,source_unchanged=True,everyday_data_unchanged_during_rollback=True,user_state_byte_identical=True,cleanup='No deletion; all candidates retained',rollback_scope='Snapshot fallback to identical accepted package, isolated restored current-state return; no in-place downgrade')
(evidence/'promotion_results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
