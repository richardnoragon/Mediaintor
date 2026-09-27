"""Read-only compatibility checks on a fresh disposable copy; never the live library."""
import hashlib,json,shutil,sys,tempfile,os,subprocess
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from mediainator.compatibility import service,CompatibilityError
from mediainator.metadata import run_request
from mediainator.imports import call_helper
from mediainator.snapshot import Snapshot
from mediainator.reader import Reader,ReaderError
from mediainator.settings import defaults

project=Path(__file__).resolve().parent.parent
seed=Path(json.loads((project/'test_data/m5_acceptance/application_report.json').read_text())['library'])
from mediainator.library import check_library
check_library(seed)
def hashes(root):return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
before=hashes(seed)
root=Path(tempfile.mkdtemp(prefix='mediainator-m6-03-'));library=root/'library';shutil.copytree(seed,library)
(library/'.mediainator-disposable.json').write_text(json.dumps({'purpose':'mediainator-disposable-test','root':str(library)}))
checks=[]
def passed(name):checks.append(dict(test=name,passed=True))
result=service.check(force=True)
if not result.verified:raise RuntimeError(result.message)
passed('actual_four_tool_version_and_runtime_verified')
with patch('mediainator.compatibility.probe_version',return_value='10.0.0'):
    blocked=service.check(force=True)
    assert not blocked.verified;passed('unverified_version_denied')
    # Freeze this verified probe result as the injected dependency state.
    with patch.object(service,'check',return_value=blocked):
        for name,operation in [('metadata',lambda:run_request(library,{'action':'read','book':1},root/'recovery')),
                               ('import',lambda:call_helper({'action':'preview','library':str(library),'sources':[]})),
                               ('snapshot',lambda:Snapshot(library))]:
            try:operation()
            except CompatibilityError:passed(name+'_blocked_before_access')
            else:raise AssertionError(name+' did not block')
        book=next(library.rglob('*.epub'))
        with patch('mediainator.reader.subprocess.Popen') as launch:
            try:Reader(defaults(),lambda:True,live=True).launch(library,book)
            except ReaderError:pass
            else:raise AssertionError('Viewer was not blocked')
            launch.assert_not_called();passed('viewer_launch_blocked')
assert service.check(force=True).verified;passed('explicit_recheck_recovers_compatibility')
snapshot=Snapshot(library).create()
try:
    import sqlite3
    with sqlite3.connect(snapshot.root/'metadata.db') as db:book_id,book_uuid=db.execute('select id,uuid from books limit 1').fetchone()
    response=run_request(snapshot.root,{'action':'read','book':book_id,'uuid':book_uuid},root/'recovery')
    assert response.get('current') or response.get('values') or response.get('title') or response.get('book') or response.get('library_uuid'),response
    passed('verified_real_helper_read_on_private_copy')
finally:snapshot.close()
assert hashes(seed)==before;passed('disposable_seed_unchanged')
# Install into a disposable user prefix and exercise first-run guidance from those files.
home=root/'installed-user';home.mkdir()
env=dict(os.environ,HOME=str(home),XDG_CONFIG_HOME=str(home/'config'),XDG_DATA_HOME=str(home/'data'),XDG_CACHE_HOME=str(home/'cache'),QT_QPA_PLATFORM='offscreen')
archive=next((project/'dist').glob('*.tar.gz'))
installed=subprocess.run(['/usr/bin/python3','-I','-B',str(project/'tools/package_install.py'),'install',str(archive)],env=env,capture_output=True,text=True,timeout=60)
assert installed.returncode==0,installed.stderr
release=(home/'.local/share/mediainator-install/current').resolve()
code=r"""
import sys,json
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from mediainator.window import Hub
from mediainator.settings import SettingsStore
app=QApplication([]);store=SettingsStore(Path.home()/'config/check.json');hub=Hub(store,store.load(),live=True)
hub.show();done=[]
def poll():
 if hub.prerequisites.result:
  r=hub.prerequisites.result
  done.append({'verified':r.verified,'choose_enabled':hub.prerequisites.choose.isEnabled(),'no_library':hub.library is None,'no_loader':hub.bookinator.loader is None,'guide':hub.prerequisites.guide.text()})
  hub.close()
timer=QTimer();timer.timeout.connect(poll);timer.start(100)
QTimer.singleShot(45000,hub.close)
app.exec()
assert done and done[0]['verified'] and done[0]['choose_enabled'] and done[0]['no_library'] and done[0]['no_loader'],done
print(json.dumps(done[0]))
"""
ui=subprocess.run(['/usr/bin/python3','-I','-B','-c',code,str(release)],env=env,cwd='/tmp',capture_output=True,text=True,timeout=60)
assert ui.returncode==0,ui.stderr
passed('installed_first_run_guidance_without_library_access')
report={'root':str(root),'checks':checks,'detected':result.detected,'original_library_used':False,'artifact_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'installed_guidance':json.loads(ui.stdout)}
(project/'test_data/m6_03_compatibility/report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
