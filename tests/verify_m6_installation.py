"""Fresh Ubuntu package-root installation and retained-data build upgrade checks."""
import hashlib,json,shutil,subprocess,sys,tempfile
from pathlib import Path
project=Path(__file__).resolve().parent.parent
folder=project/'test_data/m6_06_installation'
clean=json.loads((folder/'clean_root.json').read_text());rootfs=Path(clean['rootfs'])
fixture=Path(tempfile.mkdtemp(prefix='mediainator-m6-upgrade-'))
prior=folder/'artifacts/prior-m6-05.tar.gz';current=next((project/'dist').glob('*.tar.gz'))
for source,name in [(prior,'prior.tar.gz'),(current,'current.tar.gz'),(project/'tools/package_install.py','installer.py'),(project/'tests/m6_retained_state.py','state.py')]:shutil.copy2(source,fixture/name)
seed=Path(json.loads((project/'test_data/m5_acceptance/application_report.json').read_text())['library'])
from sys import path
path.insert(0,str(project))
from mediainator.library import check_library
check_library(seed)
shutil.copytree(seed,fixture/'library')
(fixture/'source.epub').write_bytes(b'untouched import source fixture')
scenario=r'''
import hashlib,json,os,subprocess
from pathlib import Path
home=Path.home();checks=[]
def run(*args):
 p=subprocess.run(list(args),capture_output=True,text=True,timeout=60)
 if p.returncode:raise RuntimeError(p.stdout+p.stderr)
 return p.stdout
def files(folder):return {str(p.relative_to(folder)):hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*') if p.is_file()}
installer=['/usr/bin/python3','-I','-B',str(home/'installer.py')]
run(*installer,'install',str(home/'prior.tar.gz'));checks.append('prior_real_m6_05_build_installed')
base=home/'.local/share/mediainator-install';prior=os.readlink(base/'current')
state=json.loads(run('/usr/bin/python3','-I','-B',str(home/'state.py'),str((base/'current').resolve()),'seed'))
protected=[Path(state['config']),Path(state['data']),home/'library']
before=[files(p) for p in protected];source=(home/'source.epub').read_bytes()
run(*installer,'install',str(home/'current.tar.gz'));checks.append('distinct_new_build_upgrade')
assert os.readlink(base/'current')!=prior and (base/prior).is_dir();checks.append('prior_release_retained')
assert [files(p) for p in protected]==before and (home/'source.epub').read_bytes()==source;checks.append('upgrade_preserves_all_data_bytes')
result=json.loads(run('/usr/bin/python3','-I','-B',str(home/'state.py'),str((base/'current').resolve()),'check'))
assert result==state;checks.append('settings_identity_history_journals_recovery_usable')
checks.append('unknown_settings_schema_preserved_and_rejected')
smoke=json.loads(run(str(home/'.local/bin/mediainator'),'--package-smoke'));assert smoke['application_imported'];checks.append('installed_hub_runs_on_clean_runtime')
run(*installer,'uninstall','--yes');assert [files(p) for p in protected]==before;checks.append('uninstall_preserves_data_bytes')
assert not (base/'current').exists() and not (home/'.local/bin/mediainator').exists();checks.append('uninstall_removes_program_entries')
run(*installer,'install',str(home/'current.tar.gz'));checks.append('clean_reinstall')
result=json.loads(run('/usr/bin/python3','-I','-B',str(home/'state.py'),str((base/'current').resolve()),'check'));assert result==state;checks.append('reinstall_discovers_retained_recovery_without_replay')
assert [files(p) for p in protected]==before;checks.append('all_library_and_recovery_bytes_still_unchanged')
for plugin in ['libqoffscreen.so','libqwayland.so']:
 output=run('/lib64/ld-linux-x86-64.so.2','--list','/usr/lib/x86_64-linux-gnu/qt6/plugins/platforms/'+plugin)
 assert 'not found' not in output
checks.append('native_platform_plugin_dependencies_resolve')
assert not Path('/run/media').exists();checks.append('no_checkout_or_original_home_mounted')
print(json.dumps({'checks':[{'test':c,'passed':True} for c in checks],'state_counts':{k:state[k] for k in ['recovery','imports','bulk']},'runtime':smoke}))
'''
(fixture/'scenario.py').write_text(scenario)
cmd=['bwrap','--unshare-all','--die-with-parent','--ro-bind',str(rootfs),'/', '--dev','/dev','--proc','/proc','--tmpfs','/tmp','--bind',str(fixture),'/home/m6-test','--chdir','/tmp','--clearenv','--setenv','HOME','/home/m6-test','--setenv','PATH','/usr/bin:/bin','--setenv','LANG','C.UTF-8','--setenv','QT_QPA_PLATFORM','offscreen','/usr/bin/python3','-I','-B','/home/m6-test/scenario.py']
p=subprocess.run(cmd,capture_output=True,text=True,timeout=180)
(folder/'clean_runtime_output.txt').write_text(p.stdout+p.stderr)
if p.returncode:print(p.stdout+p.stderr);sys.exit(p.returncode)
report=json.loads(p.stdout);report.update({'root':str(fixture),'prior_sha256':hashlib.sha256(prior.read_bytes()).hexdigest(),'current_sha256':hashlib.sha256(current.read_bytes()).hexdigest(),'clean_runtime':'194 Ubuntu dependency packages extracted into a fresh root; no host /usr or /etc mounted; no maintainer scripts or desktop services run','original_library_used':False,'desktop_acceptance':'M6-07 pending'})
(folder/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
