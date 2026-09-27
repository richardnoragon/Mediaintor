"""M5-03 production integration on a fresh disposable library (not M5-G acceptance)."""
import json,sys,tempfile,shutil,zipfile
from pathlib import Path
from copy import deepcopy
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QEventLoop
from mediainator.activity import ActivityStore,ActivityBridge
from mediainator.recovery import RecoveryStore
from mediainator.snapshot import Snapshot
from mediainator.metadata import run_request
from mediainator.import_store import fingerprint
from mediainator.import_dialog import ImportDialog
from mediainator.bulk_dialog import BulkDialog
from mediainator.editor import MetadataEditor
from mediainator.catalog import Book
from mediainator.reader import external_readers

app=QApplication.instance() or QApplication([])
out=Path('test_data/m5_03_integration');out.mkdir(exist_ok=True)
source=Path('/home/sproket01/Calibre Library');root=Path(tempfile.mkdtemp(prefix='mediainator-m5-03-'));library=root/'library'
def hashes(folder):return {str(p.relative_to(folder)):fingerprint(p) for p in folder.rglob('*') if p.is_file()}
if external_readers(include_calibre=True):raise SystemExit('Calibre/readers must be closed before verification. No windows were closed.')
before=hashes(source);snapshot=Snapshot(source).create();shutil.copytree(snapshot.root,library);snapshot.close()
(library/'.mediainator-disposable.json').write_text(json.dumps(dict(purpose='mediainator-disposable-test',root=str(library))))
import sqlite3
with sqlite3.connect(f'file:{library}/metadata.db?mode=ro',uri=True) as db:
    book_id,book_uuid=db.execute('select id,uuid from books order by id limit 1').fetchone()
activity=ActivityStore(root/'data'/'Activity','profile','device');notices=[];bridge=ActivityBridge(activity,notices.append)
recovery=RecoveryStore(root/'data','profile','device',bridge);checks=[]
def check(name,passed):
    checks.append(dict(test=name,passed=bool(passed)));(out/'checks.json').write_text(json.dumps(checks,indent=2));print(name,passed,flush=True);assert passed,name
book=Book(str(library)+':'+str(book_id),'Title','Author',(),(),uuid=book_uuid)
try:
    editor=MetadataEditor(library,book,root/'cover-recovery');editor.activity=bridge;editor.recovery_store=recovery
    check('real_editor_loads_library_identity',editor.load() and bool(editor.library_uuid))
    editor.title.setText('M5-03 verified metadata title')
    check('real_metadata_save',editor.save_changes())
    records=activity.records();metadata=next(r for r in records if r['operation']=='Single-book metadata saves')
    check('save_attempt_owned_and_verified',len(metadata['attempts'])==1 and metadata['attempts'][0]['outcome']=='success' and metadata['source']['library_uuid']==editor.library_uuid)
    editor.tags.addItem('M5-03 pending recovery');path=editor.preserve_recovery()
    payload=recovery.read(path,library_uuid=editor.library_uuid,book_uuid=book_uuid)
    check('production_recovery_contains_only_pending_tags',set(payload['pending'])=={'tags'} and editor.dirty())
    restarted=RecoveryStore(root/'data','profile','device',bridge);found=restarted.sync_activity()
    check('recovery_restart_discovers_without_write',len(found['records'])==1 and found['records'][0]['registered'])
    current=run_request(library,dict(action='read',book=book_id,uuid=book_uuid),root/'cover-recovery')['current']
    run_request(library,dict(action='save',book=book_id,uuid=book_uuid,baseline=current,changes={'tags':['M5 external tags']}),root/'cover-recovery')
    current=run_request(library,dict(action='read',book=book_id,uuid=book_uuid),root/'cover-recovery')['current']
    reviewed=restarted.draft(payload,current,library_uuid=editor.library_uuid,book_uuid=book_uuid)
    check('production_recovery_requires_conflict_choice',reviewed['conflicts']==['tags'] and reviewed['draft'] is None)
    reviewed=restarted.draft(payload,current,library_uuid=editor.library_uuid,book_uuid=book_uuid,choices={'tags':'recovered'})
    check('review_does_not_write',run_request(library,dict(action='read',book=book_id,uuid=book_uuid),root/'cover-recovery')['current']['tags']==['M5 external tags'])
    # Normal Save is the only catalog mutation; close/recovery orchestration remains M5-06.
    editor.fill(current);editor.apply_pending(reviewed['draft']);check('explicit_reviewed_save',editor.save_changes())
    bulk=BulkDialog(library,root/'bulk',[book]);bulk.activity=bridge;bulk.tags.addItem('M5-03 bulk');bulk.preview();bulk.execute()
    check('real_bulk_activity',any(r['operation']=='Bulk edits' and r['attempts'][-1]['outcome']=='success' for r in activity.records()))
    bulk.revert();bulk.execute()
    check('real_revert_activity_with_lineage',any(r['operation']=='Batch reverts' and r.get('original') and r['attempts'][-1]['outcome']=='success' for r in activity.records()))
    # Unique, valid EPUB with no title/creator for actual fallback review-state migration.
    fixture=root/'M5-03 Fallback.epub'
    with zipfile.ZipFile(fixture,'w') as archive:
        archive.writestr('mimetype','application/epub+zip',compress_type=zipfile.ZIP_STORED)
        archive.writestr('META-INF/container.xml','<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0"><rootfiles><rootfile full-path="content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>')
        archive.writestr('content.opf','<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="id"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="id">m5-03-validation</dc:identifier><dc:language>en</dc:language></metadata><manifest><item id="page" href="page.xhtml" media-type="application/xhtml+xml"/></manifest><spine><itemref idref="page"/></spine></package>')
        archive.writestr('page.xhtml','<html xmlns="http://www.w3.org/1999/xhtml"><head><title>M5</title></head><body><p>M5 production activity verification.</p></body></html>')
    imports=ImportDialog(library,root/'imports');imports.activity=bridge;imports.preview([str(fixture)]);imports.execute_batch()
    check('real_import_activity',imports.batch is not None and imports.batch['items'][0]['state']=='complete' and any(r['operation']=='Ebook imports' and r['attempts'][-1]['outcome']=='success' for r in activity.records()))
    imported_uuid=imports.batch['items'][0]['destination_uuid'];needed=imports.store.review_needed()
    imports.store.delete_history(imports.journal)
    check('real_import_review_status_survives_history_deletion',imported_uuid in needed and imported_uuid in imports.store.review_needed())
    imports.store.mark_reviewed(imported_uuid)
    check('mark_reviewed_persists_without_import_journal',imported_uuid not in imports.store.review_needed())
    check('activity_backend_no_storage_errors',not notices)
finally:
    unchanged=hashes(source)==before
    (out/'report.json').write_text(json.dumps(dict(kind='M5-03 production integration, not M5-G acceptance',root=str(root),library=str(library),source_unchanged=unchanged,checks=checks),indent=2))
    assert unchanged,'Original library changed during verification'
