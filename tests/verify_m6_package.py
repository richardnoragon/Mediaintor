"""Verify a bundle in a private mount namespace, with no project or user data."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parent.parent
report_dir=ROOT/'test_data/m6_package'
report_dir.mkdir(exist_ok=True)
fixture=Path(tempfile.mkdtemp(prefix='mediainator-m6-package-'))
archive=next((ROOT/'dist').glob('*.tar.gz'))
shutil.copy2(archive,fixture/'bundle.tar.gz')
shutil.copy2(ROOT/'tools/package_install.py',fixture/'package_install.py')
scenario=r'''
import json,os,subprocess
from pathlib import Path
home=Path.home();results=[]
def run(args):
 p=subprocess.run(args,capture_output=True,text=True,timeout=60)
 if p.returncode:raise RuntimeError(p.stdout+p.stderr)
 return p.stdout
installer=['/usr/bin/python3','-I','-B',str(home/'package_install.py')]
run(installer+['install',str(home/'bundle.tar.gz')]);results.append('clean_user_install')
launcher=home/'.local/bin/mediainator'
result=json.loads(run([str(launcher),'--package-smoke']))
assert result['application_imported'];results.append('installed_hub_offscreen_smoke_without_checkout')
desktop=home/'.local/share/applications/mediainator.desktop'
run(['desktop-file-validate',str(desktop)]);results.append('desktop_entry_valid')
data=home/'.local/share/Media-inator/Media-inator/Recovery/sentinel'
data.parent.mkdir(parents=True,exist_ok=True);data.write_text('retain me')
run(installer+['install',str(home/'bundle.tar.gz')]);results.append('same_artifact_reinstall')
run(installer+['uninstall','--yes']);assert data.read_text()=='retain me';results.append('uninstall_retains_data')
run(installer+['install',str(home/'bundle.tar.gz')]);assert data.read_text()=='retain me';results.append('reinstall_retains_data')
assert not Path('/run/media').exists();results.append('checkout_and_original_library_not_mounted')
print(json.dumps({'checks':[{'test':x,'passed':True} for x in results],'runtime':result}))
'''
(fixture/'scenario.py').write_text(scenario)
cmd=['bwrap','--unshare-all','--die-with-parent','--ro-bind','/usr','/usr','--ro-bind','/etc','/etc',
     '--symlink','usr/bin','/bin','--symlink','usr/sbin','/sbin','--symlink','usr/lib','/lib',
     '--symlink','usr/lib64','/lib64','--proc','/proc','--dev','/dev','--tmpfs','/tmp',
     '--dir','/home','--bind',str(fixture),'/home/m6-test','--chdir','/tmp',
     '--clearenv','--setenv','HOME','/home/m6-test','--setenv','PATH','/usr/bin:/bin',
     '--setenv','LANG','C.UTF-8','--setenv','QT_QPA_PLATFORM','offscreen',
     '/usr/bin/python3','-I','-B','/home/m6-test/scenario.py']
p=subprocess.run(cmd,capture_output=True,text=True,timeout=180)
(report_dir/'namespace_output.txt').write_text(p.stdout+p.stderr)
if p.returncode:
 print(p.stderr);sys.exit(p.returncode)
report=json.loads(p.stdout)
report.update({'artifact':archive.name,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
 'fixture':str(fixture),'isolation':'private mount/user/network namespace; host /usr and /etc read-only; clean user; no project or original home mounted',
 'limitations':'Not a freshly installed OS; uses host system packages. KDE menu interaction and populated-state upgrade remain M6-06/07.'})
(report_dir/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
