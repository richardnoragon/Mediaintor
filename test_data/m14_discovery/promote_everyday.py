"""Owner-authorized reversible M14 promotion; preserve both installations."""
import hashlib,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
for project in ('mediainator-m14','mediainator-m13'):
 assert not subprocess.check_output(['docker','ps','-q','--filter','label=com.docker.compose.project='+project],text=True).strip(), 'Close '+project+' normally first'
assert json.loads((ROOT/'test_data/m14_discovery/desktop_acceptance.json').read_text())['gate']=='PASSED'
apps=Path.home()/'.local/share/applications'
items=[('M14',ROOT.parent/'Mediaintor-M14-Development','mediainator-m14-development.desktop','M14 Development','M14 Everyday','Media-inator Everyday (M14)'),('M13',ROOT.parent/'Mediaintor-M13-Development','mediainator-m13-development.desktop','M13 Everyday','M13 Rollback','Media-inator M13 Rollback')]
backups=[]
for name,target,desktop,old,new,label in items:
 compose=target/'deployment/docker-compose.yml';entry=apps/desktop
 assert '"'+old+'"' in compose.read_text()
 backup=target/'backups/pre-m14-everyday-promotion'
 subprocess.run([sys.executable,str(ROOT.parent/'Mediaintor-M7-Testing/releases/mediainator-rc1/manage.py'),'backup',str(target/'active'),str(backup)],check=True)
 shutil.copytree(target/'deployment',backup/'deployment')
 shutil.copy2(entry,backup/desktop)
 backups.append((name,target,entry,compose,old,new,label,backup))
results=[]
for name,target,entry,compose,old,new,label,backup in backups:
 compose.write_text(compose.read_text().replace('"'+old+'"','"'+new+'"'))
 entry.write_text('\n'.join('Name='+label if line.startswith('Name=') else line for line in entry.read_text().splitlines())+'\n')
 subprocess.run(['desktop-file-validate',str(entry)],check=True)
 subprocess.run(['docker','compose','config','--quiet'],cwd=target/'deployment',check=True)
 inventory=json.loads((backup/'manifest.json').read_text())['inventory'];checked=0
 for rel,item in inventory.items():
  if 'sha256' in item:
   p=target/'active'/rel
   assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'],rel
   checked+=1
 results.append(dict(installation=name,label=new,launcher=label,desktop_file=str(entry),backup=str(backup),active_files_unchanged=checked))
report=dict(status='M14 promoted for everyday use; M13 retained as stopped rollback',build='0.1.0a1-9cf2b6503ae20a40',installations=results,changes=['deployment display labels','existing desktop display names'],publication=False,data_migration=False,m12_and_m11_unchanged=True)
(ROOT/'test_data/m14_discovery/promotion.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
