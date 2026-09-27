"""Open the verified disposable M4 library for human acceptance; no original-library writes."""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication
from mediainator.library import check_library
from mediainator.settings import SettingsStore
from mediainator.window import Hub

report = json.loads(Path('test_data/m4_acceptance/application_report.json').read_text())
if not report['source_unchanged'] or not all(c['passed'] for c in report['checks']):
    raise SystemExit('Complete the disposable application checks before desktop acceptance.')
library = check_library(Path(report['library']))
app = QApplication(sys.argv)
store = SettingsStore(library.parent/'desktop-settings.json')
state = store.load(); state['library'] = str(library); state['view'] = 'List'; state['bookinator_open'] = True
hub = Hub(store, state, live=True)
hub.setWindowTitle('M4-G ACCEPTANCE — DISPOSABLE LIBRARY')
prepared = [False]
def prepare(_):
    if prepared[0]: return
    prepared[0] = True
    books = hub.bookinator
    books.bulk_selection = {b.uuid for b in books.books if int(b.id.rsplit(':',1)[1]) <= 4}
    books.sync_bulk_checks()
    books.note.setText('M4 desktop acceptance: four books selected. Open Bulk edit / history to preview a tag change and revert it. This is a disposable library.')
hub.bookinator.loader.loaded.connect(prepare)
hub.show()
app.exec()
