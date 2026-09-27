"""Create an independent M13 copy of quiet accepted M12; no source mutation."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[2]
source=ROOT.parent/'Mediaintor-M12-Test';target=ROOT.parent/'Mediaintor-M13-Development'
launcher=Path.home()/'.local/share/applications/mediainator-m13-development.desktop'
manage=ROOT.parent/'Mediaintor-M7-Testing/releases/mediainator-rc1/manage.py'
assert not target.exists() and not launcher.exists(),'Existing destination retained; inspect first'
def run(args,cwd=None):
 p=subprocess.run(list(map(str,args)),cwd=cwd,capture_output=True,text=True,timeout=180)
 if p.returncode:raise RuntimeError(p.stdout+p.stderr)
 return p.stdout
def hashes(folder):
 return {str(p.relative_to(folder)):('link:'+os.readlink(p) if p.is_symlink() else hashlib.sha256(p.read_bytes()).hexdigest()) for p in folder.rglob('*') if p.is_file() or p.is_symlink()}
ids=run(['docker','ps','-q']).split()
for container in json.loads(run(['docker','inspect',*ids])) if ids else []:
 for mount in container['Mounts']:
  path=Path(mount.get('Source','/')).resolve();active=(source/'active').resolve()
  assert not(path.is_relative_to(active) or active.is_relative_to(path)), 'Close M12 normally before copying'
assert shutil.disk_usage(ROOT).free>1024**3
before=hashes(source/'active');deployment_before=hashes(source/'deployment')
target.mkdir();backup=target/'backups/m12-source'
print(run([sys.executable,manage,'backup',source/'active',backup]),flush=True)
print(run([sys.executable,manage,'restore',backup,target/'active']),flush=True)
shutil.copytree(source/'deployment',target/'deployment');shutil.copytree(source/'artifacts',target/'artifacts')
for name in ('.env','docker-compose.yml','launch.py','runtime.py'):
 p=target/'deployment'/name
 p.write_text(p.read_text().replace(str(source),str(target)).replace('mediainator-m12','mediainator-m13').replace('M12 Everyday','M13 Development').replace('M12 baseline','M13 baseline').replace('M12 workspace','M13 baseline'))
launcher.write_text('[Desktop Entry]\nType=Application\nName=Media-inator M13 Development\nExec=/usr/bin/python3 "'+str(target/'deployment/launch.py')+'"\nTerminal=false\nCategories=Office;\n')
run(['desktop-file-validate',launcher])
config=json.loads(run(['docker','compose','config','--format','json'],target/'deployment'))
for service in config['services'].values():
 for mount in service.get('volumes',[]):
  if mount.get('read_only'):continue
  assert Path(mount['source']).resolve().is_relative_to(target.resolve()),mount
 assert service['environment']['MEDIAINATOR_INSTALLATION_LABEL']=='M13 Development'
verified=run(['docker','compose','run','--rm','--no-deps','init'],target/'deployment')
smoke=json.loads(run(['docker','compose','run','--rm','--no-deps','--entrypoint','/home/mediainator/.local/bin/mediainator','init','--package-smoke'],target/'deployment'))
assert hashes(source/'active')==before and hashes(source/'deployment')==deployment_before
assert hashes(target/'active')==before,'Baseline copy unexpectedly changed'
report=dict(status='isolated baseline copied and verified; M13 application changes not installed',root=str(target),source=str(source),backup=str(backup),launcher=str(launcher),compose_project='mediainator-m13',baseline_build='0.1.0a1-f59e8af9b043f304',source_unchanged=True,copy_matches_source=True,writable_mounts_independent=True,files_verified=len(before),installed_inventory=verified,smoke=smoke)
(ROOT/'test_data/m13_workflows/setup.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
