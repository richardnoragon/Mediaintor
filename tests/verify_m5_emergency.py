"""M5-06 real Calibre partial-save failure and automatic preservation on a disposable copy."""
import base64
import json
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from PyQt6.QtWidgets import QApplication, QMessageBox
from mediainator.settings import SettingsStore
from mediainator.window import Hub
from mediainator.catalog import Book
from mediainator.metadata import run_request
from mediainator.reader import external_readers
from mediainator.import_store import fingerprint

app=QApplication([]);project=Path(__file__).resolve().parent.parent
out=project/'test_data/m5_06_emergency';out.mkdir(exist_ok=True)
seed=Path(json.loads((project/'test_data/m5_05_actions/report.json').read_text())['library'])
if not (seed/'.mediainator-disposable.json').exists():raise SystemExit('Disposable seed unavailable; original library will not be substituted.')
if external_readers(include_calibre=True):raise SystemExit('Close Calibre/readers before this verification. No windows were closed.')
def hashes(folder):return {str(p.relative_to(folder)):fingerprint(p) for p in folder.rglob('*') if p.is_file()}
before=hashes(seed);root=Path(tempfile.mkdtemp(prefix='mediainator-m5-06-'));library=root/'library';shutil.copytree(seed,library)
(library/'.mediainator-disposable.json').write_text(json.dumps(dict(purpose='mediainator-disposable-test',root=str(library))))
with sqlite3.connect(f'file:{library}/metadata.db?mode=ro',uri=True) as db:
    book_id,book_uuid=db.execute('select id,uuid from books order by id limit 1').fetchone()
settings=SettingsStore(root/'settings.json');hub=Hub(settings,settings.load());hub.library=library;books=hub.bookinator;books.library=library
book=Book(str(library)+':'+str(book_id),'Disposable','Author',(),(),uuid=book_uuid)
books.books=(book,);books.state['selected_book']=book.id;checks=[]
def check(name,ok):
    checks.append(dict(test=name,passed=bool(ok)));print(name,bool(ok),flush=True);assert ok,name

def read():return run_request(library,dict(action='read',book=book_id,uuid=book_uuid),root/'covers')['current']
try:
    books.edit_metadata();editor=books.editor;original=read()
    check('real_editor_reads_current_library_identity',bool(editor.baseline and editor.library_uuid))
    editor.title.setText('M5-06 verified partial title')
    # Valid image, but a file occupies the cover-backup directory: real storage failure.
    from PyQt6.QtCore import QBuffer, QIODevice
    from PyQt6.QtGui import QImage
    image=QImage(3,3,QImage.Format.Format_RGB32);image.fill(0xff112233)
    buffer=QBuffer();buffer.open(QIODevice.OpenModeFlag.WriteOnly);image.save(buffer,'PNG')
    replacement=base64.b64encode(bytes(buffer.data())).decode();editor.set_cover(replacement)
    blocked=root/'blocked-cover-backups';blocked.write_text('This file prevents directory creation.')
    editor.recovery_dir=blocked
    check('first_real_save_reports_partial_failure',not editor.save_changes() and editor.dirty())
    current=read();check('successful_title_remains_committed',current['title']=='M5-06 verified partial title')
    check('failed_cover_restores_original',current['cover']==original['cover'])
    check('first_failure_does_not_preserve_automatically',not hub.recovery_store.discover()['records'])
    check('second_real_save_fails_but_protects_draft',not editor.save_changes() and editor.protected_current_draft())
    found=hub.recovery_store.discover()['records'][0]
    check('emergency_copy_contains_only_failed_cover',found['payload']['pending']=={'cover':replacement})
    check('ordinary_editor_stays_open_and_dirty',editor.isVisible() and editor.dirty())
    check('hub_displays_truthful_preservation_notice','not been saved to the library' in hub.preservation_notice.text())
    with patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.Save):
        check('requested_hub_close_completes_automatically',hub.close())
    check('hub_shutdown_keeps_saved_module_selection',settings.load()['bookinator_open'])
    restart=Hub(settings,settings.load());app.processEvents()
    check('restart_discovers_preserved_cover',len(restart.recovery_store.discover()['records'])==1)
    check('restart_summary_without_auto_recovery_dialog',not restart.activity_panel.startup.isHidden() and restart.bookinator.editor is None)
    check('restart_does_not_apply_failed_cover',read()['cover']==original['cover'])
    restart.close()
finally:
    unchanged=hashes(seed)==before
    (out/'report.json').write_text(json.dumps(dict(kind='M5-06 automatic preservation/close verification; not M5-G acceptance',root=str(root),library=str(library),seed_unchanged=unchanged,checks=checks),indent=2))
    assert unchanged,'Disposable seed changed'
