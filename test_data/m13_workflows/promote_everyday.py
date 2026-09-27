"""Owner-authorized reversible M13 promotion; preserve both installations."""
import hashlib,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
assert not subprocess.check_output(['docker','ps','-q'],text=True).strip(), 'Close applications normally first'
assert json.loads((ROOT/'test_data/m13_workflows/desktop_acceptance.json').read_text())['gate'].startswith('M13-G CLOSED')
apps=Path.home()/'.local/share/applications'
items=[('M13',ROOT.parent/'Mediaintor-M13-Development','mediainator-m13-development.desktop','M13 Development','M13 Everyday','Media-inator Everyday (M13)'),('M12',ROOT.parent/'Mediaintor-M12-Test','mediainator-m12-test.desktop','M12 Everyday','M12 Rollback','Media-inator M12 Rollback')]
backups=[]
for name,target,desktop,old,new,label in items:
 compose=target/'deployment/docker-compose.yml';entry=apps/desktop
 assert '"'+old+'"' in compose.read_text()
 backup=target/'backups/pre-m13-everyday-promotion'
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
report=dict(status='M13 promoted for everyday use; M12 retained as stopped rollback',build='0.1.0a1-db6a7fb8885f9bd9',installations=results,changes=['deployment display labels','existing desktop display names'],publication=False,data_migration=False,m11_unchanged=True)
(ROOT/'test_data/m13_workflows/promotion.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
