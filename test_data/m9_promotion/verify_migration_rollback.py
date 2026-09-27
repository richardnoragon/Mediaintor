"""Host orchestrator: all mutations restricted to new M9 validation copies."""
from pathlib import Path
import subprocess,json,hashlib
root=Path.cwd(); reportdir=root/'test_data/m9_promotion';r=json.loads((reportdir/'preparation.json').read_text());base=Path(r['root'])
manage=root.parent/'Mediaintor-M7-Testing/releases/mediainator-rc1/manage.py'
def run(args):
 p=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=180)
 if p.returncode:raise RuntimeError(p.stdout+p.stderr)
 return p.stdout
assert not run(['docker','ps','-q']).strip(),'Close running containers before consistent backup'
post=base/'backups/post-upgrade-184039712b870efd'
run(['python3',manage,'backup',base/'active',post])
for backup,name in [(post,'functional-check'),(Path(r['backup']),'rollback-check')]:run(['python3',manage,'restore',backup,base/name])
image='sha256:da0d06cee1517cbbc0b0b8910c3303b6ad3b47377445a76e47994e977f885783'
def container(folder,args,extra=()):
 cmd=['docker','run','--rm','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--user','1000:1000','--tmpfs','/tmp:rw,mode=1777','-e','QT_QPA_PLATFORM=offscreen']
 for child,target in [('home','/home/mediainator'),('library','/data/library'),('import-sources','/data/import-sources')]:cmd+=['-v',f'{folder/child}:{target}']
 cmd+=list(extra)+['--entrypoint',args[0],image]+args[1:]
 return run(cmd)
functional=json.loads(container(base/'functional-check',['/usr/bin/python3','-I','-B','/probe.py'],['-v',f'{reportdir/"functional_probe.py"}:/probe.py:ro']))
old=json.loads(container(base/'rollback-check',['/home/mediainator/.local/bin/mediainator','--package-smoke']))
oldstate=json.loads((base/'rollback-check/home/.local/share/mediainator-install/installation.json').read_text());assert oldstate['current']=='0.1.0a1-c08faf149723f3c0'
upgrade=container(base/'rollback-check',['/usr/bin/python3','-I','-B','/installer.py','install','/candidate.tar.gz'],['-v',f'{base/"deployment/package_install.py"}:/installer.py:ro','-v',f'{base/"artifacts/candidate.tar.gz"}:/candidate.tar.gz:ro'])
returned=json.loads(container(base/'rollback-check',['/home/mediainator/.local/bin/mediainator','--package-smoke']))
newstate=json.loads((base/'rollback-check/home/.local/share/mediainator-install/installation.json').read_text());assert newstate['current']==r['target_build']
def hashes(folder):return {str(p.relative_to(folder)):hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*') if p.is_file() and not p.is_symlink()}
assert hashes(base/'active')==hashes(post/'data'),'Newer M9 data changed during rollback validation'
assert hashes(Path(r['source']))==hashes(Path(r['backup'])/'data'),'M8 source changed'
assert hashes(base/'rollback-check/library')==hashes(Path(r['backup'])/'data/library')
result=dict(functional=functional,rollback_old_build=oldstate['current'],rollback_old_smoke=old,return_build=newstate['current'],return_smoke=returned,post_upgrade_snapshot=str(post),m9_active_unchanged=True,m8_source_unchanged=True,rollback_library_retained=True,scope='Snapshot rollback and return on separate clones; not in-place downgrade; personal KDE checks pending')
(reportdir/'migration_rollback_results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
