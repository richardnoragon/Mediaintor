"""Explicit M13-only upgrade; retain baseline and verify user data unchanged."""
import hashlib,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
target=ROOT.parent/'Mediaintor-M13-Development'
deployment=target/'deployment'
archive=ROOT/'dist/m13-acceptance-fixes/mediainator-0.1.0a1-ubuntu26.04-x86_64.tar.gz'
report=json.loads((ROOT/'test_data/m13_workflows/acceptance_fixes_package_verification.json').read_text())
assert hashlib.sha256(archive.read_bytes()).hexdigest()==report['sha256']
assert not subprocess.check_output(['docker','ps','-q'],text=True).strip(),'Close test containers first'
import tarfile
with tarfile.open(archive) as bundle:
 manifest=json.load(bundle.extractfile(next(n for n in bundle.getnames() if n.endswith('manifest.json'))))
build=manifest['version']+'-'+manifest['build_id']
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
s=p.read_text().replace('0.1.0a1-911ac9451958810d',build).replace('M10 baseline installation','M10 candidate installation').replace('M10 baseline accepted M8 build verified:','M10 workspace candidate verified:')
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
result=dict(status='installed; personal KDE acceptance pending',build=build,sha256=report['sha256'],backup=str(backup),retained_files_verified=checked,inventory_check=verified,package_smoke=json.loads(smoke),installer_output=install,scope='M13 only; accepted M12/M11/RC1/M9/M10 not mounted or modified')
(ROOT/'test_data/m13_workflows/installed_acceptance_fixes_candidate.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
