"""Create M12 only from a quiet M11 source; never stop or mutate M11."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[2];source=ROOT.parent/'Mediaintor-M11-Everyday';target=ROOT.parent/'Mediaintor-M12-Test'
launcher=Path.home()/'.local/share/applications/mediainator-m12-test.desktop'
manage=ROOT.parent/'Mediaintor-M7-Testing/releases/mediainator-rc1/manage.py'
assert not target.exists() and not launcher.exists(),'Existing destination retained; inspect before proceeding'
def run(args,cwd=None):
 p=subprocess.run(list(map(str,args)),cwd=cwd,capture_output=True,text=True,timeout=180)
 if p.returncode:raise RuntimeError(p.stdout+p.stderr)
 return p.stdout
def hashes(folder):
 return {str(p.relative_to(folder)):('link:'+os.readlink(p) if p.is_symlink() else hashlib.sha256(p.read_bytes()).hexdigest()) for p in folder.rglob('*') if p.is_file() or p.is_symlink()}
# The backup utility independently refuses overlapping running-container mounts.
ids=run(['docker','ps','-q']).split()
if ids:
 for container in json.loads(run(['docker','inspect',*ids])):
  for mount in container['Mounts']:
   path=Path(mount.get('Source','/')).resolve()
   assert not path.is_relative_to(source/'active'), 'Close M11 Hub/readers before setup'
assert shutil.disk_usage(ROOT).free>1024**3
before=hashes(source/'active');deployment_before=hashes(source/'deployment')
target.mkdir();backup=target/'backups/m11-source'
print(run([sys.executable,manage,'backup',source/'active',backup]),flush=True)
print(run([sys.executable,manage,'restore',backup,target/'active']),flush=True)
shutil.copytree(source/'deployment',target/'deployment');shutil.copytree(source/'artifacts',target/'artifacts')
for name in ('.env','docker-compose.yml','launch.py','runtime.py'):
 p=target/'deployment'/name;p.write_text(p.read_text().replace(str(source),str(target)).replace('mediainator-m11','mediainator-m12').replace('M11','M12'))
launcher.write_text('[Desktop Entry]\nType=Application\nName=Media-inator M12 Test\nExec=/usr/bin/python3 "'+str(target/'deployment/launch.py')+'"\nTerminal=false\nCategories=Office;\n')
run(['desktop-file-validate',launcher])
verified=run(['docker','compose','run','--rm','--no-deps','init'],target/'deployment')
smoke=json.loads(run(['docker','compose','run','--rm','--no-deps','--entrypoint','/home/mediainator/.local/bin/mediainator','init','--package-smoke'],target/'deployment'))
assert hashes(source/'active')==before and hashes(source/'deployment')==deployment_before
assert hashes(target/'active')==before,'Baseline copy changed unexpectedly'
report=dict(status='isolated baseline copied and smoke verified; M12 implementation not installed',root=str(target),source=str(source),backup=str(backup),launcher=str(launcher),compose_project='mediainator-m12',baseline_build='0.1.0a1-a3a4679f39f4c255',source_unchanged=True,copy_matches_source=True,installed_inventory=verified,smoke=smoke)
(ROOT/'test_data/m12_usability/setup.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
