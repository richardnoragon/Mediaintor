"""Exercise offline help from the installed bundle using a disposable user prefix."""
import hashlib,json,os,subprocess,tempfile
from pathlib import Path

project=Path(__file__).resolve().parent.parent
root=Path(tempfile.mkdtemp(prefix='mediainator-m6-help-'));home=root/'user';home.mkdir()
archive=next((project/'dist').glob('*.tar.gz'))
env=dict(os.environ,HOME=str(home),XDG_CONFIG_HOME=str(home/'config'),XDG_DATA_HOME=str(home/'data'),XDG_CACHE_HOME=str(home/'cache'),QT_QPA_PLATFORM='offscreen')
command=['/usr/bin/python3','-I','-B',str(project/'tools/package_install.py'),'install',str(archive)]
result=subprocess.run(command,env=env,capture_output=True,text=True,timeout=60)
assert result.returncode==0,result.stderr
release=(home/'.local/share/mediainator-install/current').resolve()
code=r'''
import json,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,sys.argv[1])
from PyQt6.QtWidgets import QApplication
from mediainator.window import Hub
from mediainator.settings import SettingsStore
from mediainator.help_ui import TOPICS,documentation_root,about_text
app=QApplication([]);store=SettingsStore(Path.home()/'config/help-test.json');hub=Hub(store,store.load());hub.show()
checks=[]
assert documentation_root()==Path(sys.argv[1]);checks.append('installed_docs_resolve_without_checkout')
with patch('mediainator.compatibility.service.check',side_effect=AssertionError('Help probed Calibre')),patch('subprocess.Popen',side_effect=AssertionError('Help launched a subprocess')):
 for topic in TOPICS:
  hub.show_help(topic);app.processEvents()
  assert len(hub.help_dialog.browser.toPlainText())>500
  checks.append('offline_topic_'+topic)
 assert '0.1.0a1' in about_text() and 'Qt' in about_text();checks.append('installed_about_version')
 hub.help_dialog.search.setText('settings');hub.help_dialog.find_next()
 assert hub.help_dialog.notice.text()=='Match selected.';checks.append('installed_help_search')
 hub.help_dialog.grab().save(sys.argv[2])
 hub.close();assert not hub.help_dialog.isVisible();checks.append('help_closes_with_hub')
print(json.dumps(checks))
'''
folder=project/'test_data/m6_04_help'
r=subprocess.run(['/usr/bin/python3','-I','-B','-c',code,str(release),str(folder/'help.png')],env=env,cwd='/tmp',capture_output=True,text=True,timeout=30)
assert r.returncode==0,r.stderr
checks=json.loads(r.stdout)
report={'artifact_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'root':str(root),'checks':[dict(test=x,passed=True) for x in checks], 'library_access':False,'desktop_acceptance':'pending M6-07; automated offscreen rendering only'}
(folder/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
