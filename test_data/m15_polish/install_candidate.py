"""Explicit M14-only upgrade; retain baseline and verify user data unchanged."""
import hashlib,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
target=ROOT.parent/'Mediaintor-M15-Development'
deployment=target/'deployment'
archive=ROOT/'dist/m15-polish/mediainator-0.1.0a1-ubuntu26.04-x86_64.tar.gz'
report=json.loads((ROOT/'test_data/m15_polish/polish_package_verification.json').read_text())
assert hashlib.sha256(archive.read_bytes()).hexdigest()==report['sha256']
assert not subprocess.check_output(['docker','ps','-q','--filter','label=com.docker.compose.project=mediainator-m15'],text=True).strip(),'Close M14 development containers first'
import tarfile
with tarfile.open(archive) as bundle:
 manifest=json.load(bundle.extractfile(next(n for n in bundle.getnames() if n.endswith('manifest.json'))))
build=manifest['version']+'-'+manifest['build_id']
assert '0.1.0a1-9cf2b6503ae20a40' in (deployment/'runtime.py').read_text(), 'Unexpected current build'
backup=target/('backups/pre-'+build)
subprocess.run([sys.executable,str(ROOT.parent/'Mediaintor-M7-Testing/releases/mediainator-rc1/manage.py'),'backup',str(target/'active'),str(backup)],check=True)
saved=backup/'deployment';shutil.copytree(deployment,saved)
shutil.copytree(target/'artifacts',backup/'artifacts')
shutil.copy2(archive,target/'artifacts/candidate.tar.gz')
def compose(*args):
 p=subprocess.run(['docker','compose',*args],cwd=deployment,capture_output=True,text=True,timeout=120)
 if p.returncode:raise RuntimeError(p.stdout+p.stderr)
 return p.stdout
install=compose('run','--rm','--no-deps','--entrypoint','/usr/bin/python3','init','-I','-B','/opt/m9/package_install.py','install','/opt/m9/candidate.tar.gz')
p=deployment/'runtime.py'
s=p.read_text().replace('0.1.0a1-9cf2b6503ae20a40',build).replace('M14 baseline candidate verified:','M14 discovery candidate verified:').replace('explicit M12 candidate','explicit M14 candidate').replace('M10 baseline installation','M10 candidate installation').replace('M10 baseline accepted M8 build verified:','M10 workspace candidate verified:')
p.write_text(s)
verified=compose('run','--rm','--no-deps','init')
smoke=compose('run','--rm','--no-deps','--entrypoint','/home/mediainator/.local/bin/mediainator','init','--package-smoke')
inventory=json.loads((backup/'manifest.json').read_text())['inventory']
checked=0
for name,item in inventory.items():
 if name.startswith(('home/.local/share/mediainator-install/','home/.local/bin/','home/.local/share/applications/')):continue
 path=target/'active'/name
 if 'sha256' in item:
  assert path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256'],name
  checked+=1
result=dict(status='installed; personal KDE acceptance pending',build=build,sha256=report['sha256'],backup=str(backup),retained_files_verified=checked,inventory_check=verified,package_smoke=json.loads(smoke),installer_output=install,scope='M15 only; accepted M14 Everyday and M13 Rollback not mounted or modified')
(ROOT/'test_data/m15_polish/installed_polish.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
