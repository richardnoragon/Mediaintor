"""Installed, disposable-user diagnostics verification; no library or uploads."""
import hashlib,json,os,subprocess,tempfile
from pathlib import Path

project=Path(__file__).resolve().parent.parent
root=Path(tempfile.mkdtemp(prefix='mediainator-m6-diagnostics-'));home=root/'user';home.mkdir()
archive=next((project/'dist').glob('*.tar.gz'))
env=dict(os.environ,HOME=str(home),XDG_CONFIG_HOME=str(home/'config'),XDG_DATA_HOME=str(home/'data'),XDG_CACHE_HOME=str(home/'cache'),QT_QPA_PLATFORM='offscreen')
r=subprocess.run(['/usr/bin/python3','-I','-B',str(project/'tools/package_install.py'),'install',str(archive)],env=env,capture_output=True,text=True,timeout=60)
assert r.returncode==0,r.stderr
release=(home/'.local/share/mediainator-install/current').resolve()
code=r'''
import json,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,sys.argv[1])
from PyQt6.QtWidgets import QApplication
from mediainator.window import Hub
from mediainator.settings import SettingsStore
from mediainator.diagnostics import record_error
app=QApplication([]);store=SettingsStore(Path.home()/'config/check.json');hub=Hub(store,store.load());hub.show()
secret='PRIVATE_雪_/home/private/library/book_author_ISBN_recovery\nnotes'
try:raise RuntimeError(secret)
except RuntimeError as exc:record_error('metadata-failure',exc)
checks=[]
with patch('socket.socket',side_effect=AssertionError('network attempt')),patch('mediainator.compatibility.service.check',side_effect=AssertionError('Calibre probe')):
 hub.show_diagnostics();app.processEvents();dialog=hub.diagnostics_dialog
 payload=dialog.snapshot.payload
 assert dialog.preview.toPlainText().encode()==payload;checks.append('preview_is_exact_export_bytes')
 assert b'PRIVATE' not in payload and b'/home' not in payload;checks.append('private_exception_content_omitted')
 parsed=json.loads(payload);assert parsed['versions']['application']=='0.1.0a1' and 'metadata-failure' in payload.decode();checks.append('installed_versions_and_fixed_error_summary')
 target=Path.home()/'export.json'
 with patch('mediainator.diagnostics_ui.QFileDialog.getSaveFileName',return_value=('','')):dialog.export()
 assert not target.exists();checks.append('cancel_writes_no_export')
 record_error('reader-failure',ValueError(secret))
 with patch('mediainator.diagnostics_ui.QFileDialog.getSaveFileName',return_value=(str(target),'')):dialog.export()
 assert target.read_bytes()==payload;checks.append('export_uses_frozen_preview')
 assert target.stat().st_mode & 0o777==0o600;checks.append('owner_only_permissions')
 dialog.grab().save(sys.argv[2]);hub.close();assert not dialog.isVisible();checks.append('hub_close_closes_diagnostics')
print(json.dumps(checks))
'''
folder=project/'test_data/m6_05_diagnostics'
r=subprocess.run(['/usr/bin/python3','-I','-B','-c',code,str(release),str(folder/'preview.png')],env=env,cwd='/tmp',capture_output=True,text=True,timeout=30)
assert r.returncode==0,r.stderr
report={'artifact_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'root':str(root),'checks':[dict(test=x,passed=True) for x in json.loads(r.stdout)],'library_access':False,'uploads':False,'desktop_acceptance':'M6-07 pending; automated offscreen verification'}
(folder/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
