"""Open only the verified disposable M5 acceptance library, with isolated saved state."""
import argparse
import base64
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from PyQt6.QtCore import QTimer, QLockFile
from PyQt6.QtWidgets import QApplication
from mediainator.library import check_library
from mediainator.settings import SettingsStore
from mediainator.window import Hub

parser=argparse.ArgumentParser();parser.add_argument('--emergency',action='store_true');args=parser.parse_args()
project=Path(__file__).resolve().parent.parent
report=json.loads((project/'test_data/m5_acceptance/application_report.json').read_text())
if not report['seed_unchanged'] or not all(c['passed'] for c in report['checks']):raise SystemExit('Complete automated application verification first.')
library=check_library(Path(report['library']));root=library.parent
app=QApplication(sys.argv);app.setApplicationName('M5 Disposable Acceptance')
lock=QLockFile(str(root/'desktop.lock'))
if not lock.tryLock(0):raise SystemExit('An M5 acceptance window is already open. Close it before starting another scenario.')
store=SettingsStore(root/'settings.json');state=store.load();state['library']=str(library);state['view']='List';state['bookinator_open']=True
hub=Hub(store,state,live=True);hub.setWindowTitle('M5 ACCEPTANCE — DISPOSABLE LIBRARY')
app.commitDataRequest.connect(hub.commit_shutdown)
prepared=[False]
def ready(_):
    if prepared[0]:return
    prepared[0]=True
    if args.emergency:
        books=hub.bookinator;book=books.books[0];books.state['selected_book']=book.id;books.edit_metadata()
        editor=books.editor
        if not editor or not editor.baseline:return
        blocked=root/'desktop-blocked-cover-backup'
        if not blocked.exists():blocked.write_text('Disposable fault fixture: cover backup cannot create a directory here.')
        editor.recovery_dir=blocked
        editor.title.setText('M5 Desktop Emergency Review')
        editor.set_cover(base64.b64encode((root/'replacement.png').read_bytes()).decode())
        editor.status.setText('DISPOSABLE TEST: click Save, then Retry. The cover backup destination is deliberately blocked. Only the cover should remain unsaved and be preserved. Then close the Hub.')
    else:
        hub.tabs.setCurrentIndex(0)
        hub.show_preservation_notice('M5 desktop acceptance: inspect Activity; review the prepared single-book recovery and pending bulk batch. All changes stay in this disposable library.')
hub.bookinator.loader.loaded.connect(ready)
hub.show();app.exec()
