"""Restore M16 from the verified, closed M15 pre-promotion backup."""
import json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
source=ROOT.parent/'Mediaintor-M15-Development'
backup=source/'backups/pre-m15-everyday-promotion'
target=ROOT.parent/'Mediaintor-M16-Development'
assert not target.exists(),'Existing destination retained'
manage=ROOT.parent/'Mediaintor-M7-Testing/releases/mediainator-rc1/manage.py'
target.mkdir()
subprocess.run([sys.executable,str(manage),'restore',str(backup),str(target/'active')],check=True)
shutil.copytree(backup/'deployment',target/'deployment')
shutil.copytree(source/'artifacts',target/'artifacts')
for name in ('.env','docker-compose.yml','launch.py','runtime.py'):
 p=target/'deployment'/name
 p.write_text(p.read_text().replace(str(source),str(target)).replace('mediainator-m15','mediainator-m16').replace('M15 Development','M16 Development').replace('M15 Everyday','M16 Development'))
config=json.loads(subprocess.check_output(['docker','compose','config','--format','json'],cwd=target/'deployment',text=True))
for service in config['services'].values():
 assert service['environment']['MEDIAINATOR_INSTALLATION_LABEL']=='M16 Development'
 for mount in service.get('volumes',[]):
  if not mount.get('read_only'):assert Path(mount['source']).resolve().is_relative_to(target.resolve()),mount
launcher=Path.home()/'.local/share/applications/mediainator-m16-development.desktop'
assert not launcher.exists()
launcher.write_text('[Desktop Entry]\nType=Application\nName=Media-inator M16 Development\nExec=/usr/bin/python3 "'+str(target/'deployment/launch.py')+'"\nTerminal=false\nCategories=Office;\n')
subprocess.run(['desktop-file-validate',str(launcher)],check=True)
result=dict(root=str(target),source_backup=str(backup),baseline_build='0.1.0a1-47d071de892ca535',writable_mounts_independent=True,m15_untouched=True,started=False)
(ROOT/'test_data/m16_hub/setup.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
