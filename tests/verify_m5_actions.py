"""Explicit M5-05 production recovery actions on a fresh copy of a disposable library."""
import json
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PyQt6.QtWidgets import QApplication, QMessageBox
from mediainator.settings import SettingsStore
from mediainator.window import Hub
from mediainator.catalog import Book
from mediainator.metadata import run_request
from mediainator.reader import external_readers
from mediainator.import_store import fingerprint, atomic_json
from mediainator.bulk_dialog import BulkDialog

app = QApplication([])
project = Path(__file__).resolve().parent.parent
out = project/'test_data'/'m5_05_actions'; out.mkdir(exist_ok=True)
seed = Path(json.loads((project/'test_data/m5_03_integration/report.json').read_text())['library'])
if not (seed/'.mediainator-disposable.json').exists(): raise SystemExit('Disposable seed is unavailable; no user library selected.')
if external_readers(include_calibre=True): raise SystemExit('Close Calibre/readers before validation. No windows were closed.')
def hashes(root): return {str(p.relative_to(root)):fingerprint(p) for p in root.rglob('*') if p.is_file()}
before = hashes(seed)
root = Path(tempfile.mkdtemp(prefix='mediainator-m5-05-')); library=root/'library'
shutil.copytree(seed, library)
(library/'.mediainator-disposable.json').write_text(json.dumps(dict(purpose='mediainator-disposable-test',root=str(library))))
with sqlite3.connect(f'file:{library}/metadata.db?mode=ro', uri=True) as db:
    book_id, book_uuid = db.execute('select id,uuid from books order by id limit 1').fetchone()
settings = SettingsStore(root/'settings.json'); hub=Hub(settings, settings.load())
hub.library=library; books=hub.bookinator; books.library=library
book=Book(str(library)+':'+str(book_id), 'Disposable book', 'Author', (), (), uuid=book_uuid)
books.books=(book,)
checks=[]
def check(name, passed):
    checks.append(dict(test=name, passed=bool(passed))); print(name, bool(passed), flush=True)
    assert passed, name

def read(): return run_request(library, dict(action='read',book=book_id,uuid=book_uuid),root/'covers')
try:
    initial=read(); current=initial['current']; proposed=dict(current,tags=['M5-05 recovered'])
    payload=hub.recovery_store.capture(initial['library_uuid'],book_uuid,current,proposed,1,'m5-05-save')
    path=hub.recovery_store.preserve(payload)
    record=next(r for r in hub.activity.store.records() if r['source'].get('recovery_id')==payload['id'])
    # An external edit requires a conflict choice before draft application.
    run_request(library, dict(action='save',book=book_id,uuid=book_uuid,baseline=current,changes={'tags':['M5-05 external']}),root/'covers')
    from mediainator.editor import MetadataEditor
    def choose_recovered(editor, result, draft):
        check('real_current_values_detect_recovery_conflict', result['conflicts']==['tags'])
        editor.fill(result['current']); editor.apply_pending(draft); return draft
    with patch.object(MetadataEditor,'resolve',choose_recovered):
        hub.activity_controller.review(record)
    editor=books.editor
    check('review_opens_draft_without_catalog_write',editor.dirty() and read()['current']['tags']==['M5-05 external'])
    check('explicit_recovered_save_verified', editor.save_changes() and read()['current']['tags']==['M5-05 recovered'])
    check('successful_save_resolves_durable_recovery',hub.recovery_store.discover()['records'][0]['state']=='recovered')
    editor.done(0)
    hub.activity_controller.actions.delete(record['id'])
    check('resolved_recovery_cleanup_removes_owned_payload',not path.exists() and not hub.recovery_store.discover()['records'])
    bulk=BulkDialog(library,root/'bulk',[book]);bulk.activity=hub.activity;bulk.activity_controller=hub.activity_controller
    bulk.tags.addItem('M5-05 batch'); bulk.preview()
    bulk.store.save(bulk.batch); bulk.refresh_history()
    rec=hub.activity_controller.batch_record(bulk.batch,bulk.store.folder/(bulk.batch['id']+'.json'),'bulk')
    bulk.review()
    check('real_bulk_review_does_not_write', 'M5-05 batch' not in read()['current']['tags'])
    hub.activity_controller.actions.discard(rec['id'])
    check('reviewed_bulk_discard_keeps_catalog', 'M5-05 batch' not in read()['current']['tags'])
    hub.activity_controller.actions.delete(rec['id'])
    check('bulk_cleanup_retains_library_book',read()['current']['uuid']==book_uuid)
    # Pending import using a real source format: review/retry rebuilds preview only.
    source=next(library.rglob('*.epub'))
    from mediainator.import_dialog import ImportDialog
    imports=ImportDialog(library,root/'imports');imports.activity=hub.activity;imports.activity_controller=hub.activity_controller
    imports.preview([str(source)])
    check('real_import_preview_available',bool(imports.plan))
    imports.journal,imports.batch=imports.store.create(imports.plan);imports.plan=None
    rec=hub.activity_controller.batch_record(imports.batch,imports.journal,'import')
    check('specific_import_journal_review',imports.review_batch(imports.journal))
    imports.retry()
    check('retry_builds_preview_without_running',bool(imports.plan) and not imports.running)
    # This source already exists; no pending copy may remain after reconciliation.
    imports.batch=json.loads(imports.journal.read_text())
    hub.activity.batch(imports.batch,imports.journal,'import')
    hub.activity_controller.actions.acknowledge_review(rec['id'])
    hub.activity_controller.actions.discard(rec['id'])
    source_hash=fingerprint(source)
    hub.activity_controller.actions.delete(rec['id'])
    check('import_cleanup_preserves_source_ebook',source.exists() and fingerprint(source)==source_hash)
    check('cleanup_tombstones_survive_projection',all(r['id']!=rec['id'] for r in hub.activity.store.records()))
finally:
    unchanged=hashes(seed)==before
    (out/'report.json').write_text(json.dumps(dict(kind='M5-05 production actions, not M5-G acceptance',root=str(root),library=str(library),seed_unchanged=unchanged,checks=checks),indent=2))
    assert unchanged,'Disposable seed changed'
    hub.close()
