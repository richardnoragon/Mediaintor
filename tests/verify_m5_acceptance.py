"""M5 application/scale regression and desktop-fixture preparation on a fresh 101-book copy."""
import base64
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
MODULE_ROOT=Path(os.environ.get("MEDIAINATOR_ACCEPTANCE_RELEASE",Path(__file__).resolve().parent.parent)).resolve()
sys.path.insert(0,str(MODULE_ROOT))
import mediainator
assert Path(mediainator.__file__).resolve().parent.parent == MODULE_ROOT
from PyQt6.QtCore import QEventLoop, QTimer, QBuffer, QIODevice
from PyQt6.QtGui import QImage
from PyQt6.QtWidgets import QApplication
from mediainator.activity import ActivityStore, ActivityBridge
from mediainator.activity_panel import ActivityPanel
from mediainator.bulk import BulkStore, plan
from mediainator.bulk_dialog import BulkDialog
from mediainator.editor import MetadataEditor
from mediainator.import_dialog import ImportDialog
from mediainator.import_store import fingerprint, atomic_json
from mediainator.metadata import run_request
from mediainator.reader import external_readers
from mediainator.settings import SettingsStore
from mediainator.window import Hub

app=QApplication([]);project=Path(__file__).resolve().parent.parent
out=Path(os.environ.get('MEDIAINATOR_ACCEPTANCE_OUTPUT',project/'test_data/m5_acceptance'));out.mkdir(parents=True,exist_ok=True)
seed=Path(json.loads((project/'test_data/m4_acceptance/application_report.json').read_text())['library'])
if not (seed/'.mediainator-disposable.json').exists():raise SystemExit('M4 disposable fixture unavailable; original library will not be substituted.')
if external_readers(include_calibre=True):raise SystemExit('Close Calibre/readers before verification; none were closed automatically.')
def hashes(folder):return {str(p.relative_to(folder)):fingerprint(p) for p in folder.rglob('*') if p.is_file()}
before=hashes(seed);root=Path(tempfile.mkdtemp(prefix='mediainator-application-acceptance-'));library=root/'library';shutil.copytree(seed,library)
(library/'.mediainator-disposable.json').write_text(json.dumps(dict(purpose='mediainator-disposable-test',root=str(library))))
settings=SettingsStore(root/'settings.json');hub=Hub(settings,settings.load(),library=library);books=hub.bookinator;checks=[]
def check(name,ok,**details):
    checks.append(dict(test=name,passed=bool(ok),**details));print(name,bool(ok),flush=True);assert ok,name

def wait_load():
    loop=QEventLoop();books.loader.loaded.connect(loop.quit);books.loader.failed.connect(loop.quit)
    timer=QTimer();timer.setSingleShot(True);timer.timeout.connect(loop.quit);timer.start(30000)
    loop.exec();timer.stop()
    assert not books.loader.active and books.books,books.note.text()

try:
    wait_load();initial=books.books
    # Keep the sequential driver from overlapping timer-driven refresh with the next check.
    books.refresh_timer.stop();books.auto_refresh=lambda *args,**kwargs:None
    check('all_101_books_load',len(initial)==101,count=len(initial))
    check('metadata_and_all_format_paths',all(b.uuid and b.title and b.author and b.paths and all(Path(p).is_file() for _,p in b.paths) for b in initial))
    check('all_covers_resolve',all(b.cover and Path(b.cover).is_file() for b in initial))
    multi=next(b for b in initial if len(b.formats)==3)
    check('epub_mobi_pdf_grouped_on_one_book',set(multi.formats)=={'EPUB','MOBI','PDF'})
    books.search.setText(multi.title);check('title_search_includes_multiformat_book',multi in books.visible)
    books.search.setText(multi.author);check('author_search_includes_book',multi in books.visible)
    books.search.clear();books.view.setCurrentText('List');check('list_count_matches_grid',books.table.rowCount()==101 and books.grid.count()==101)
    check('unknown_reading_status',all(b.reading_status=='Unknown' for b in initial))
    book=initial[0];books.state['selected_book']=book.id;books.edit_metadata();editor=books.editor;editor.on_saved=lambda:None
    saved_title=editor.baseline['title'];editor.title.setText('M5 application regression title')
    check('single_metadata_save',editor.save_changes())
    editor.title.setText(saved_title);check('single_metadata_restore',editor.save_changes());editor.done(0)
    bulk=BulkDialog(library,root/'bulk',list(initial[:4]));bulk.activity=hub.activity;bulk.tags.addItem('M5 Regression Tag')
    bulk.preview();print('Bulk preview status:',bulk.status.text(),flush=True);check('bulk_preview_is_explicit',bulk.batch is not None and all('M5 Regression Tag' not in i['baseline']['tags'] for i in bulk.batch['items']))
    bulk.execute();check('bulk_four_book_save',all(i['state']=='complete' for i in bulk.batch['items']))
    bulk.revert();bulk.execute();check('bulk_revert_verified',bulk.batch['kind']=='revert' and all(i['state']=='complete' for i in bulk.batch['items']))
    # Real import; distinct bytes avoid duplicate fixture history.
    fixture=root/'M5 Desktop Review.epub'
    with zipfile.ZipFile(fixture,'w') as archive:
        archive.writestr('mimetype','application/epub+zip',compress_type=zipfile.ZIP_STORED)
        archive.writestr('META-INF/container.xml','<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0"><rootfiles><rootfile full-path="content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>')
        archive.writestr('content.opf','<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="id"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="id">m5-acceptance</dc:identifier><dc:language>en</dc:language></metadata><manifest><item id="page" href="page.xhtml" media-type="application/xhtml+xml"/></manifest><spine><itemref idref="page"/></spine></package>')
        archive.writestr('page.xhtml','<html xmlns="http://www.w3.org/1999/xhtml"><head><title>M5</title></head><body><p>M5 acceptance fixture.</p></body></html>')
    imports=ImportDialog(library,root/'imports');imports.activity=hub.activity;imports.preview([str(fixture)])
    check('import_preview_missing_metadata_warning',bool(imports.plan['items'][0]['missing']))
    imports.execute_batch();check('copy_only_import_and_review_flag',imports.batch['items'][0]['state']=='complete' and fixture.exists() and imports.batch['items'][0]['destination_uuid'] in imports.store.review_needed())
    identity=hub.activity_controller.batch_record(imports.batch,imports.journal,'import')['id']
    hub.activity_controller.actions.delete(identity)
    check('review_state_survives_history_cleanup',imports.batch['items'][0]['destination_uuid'] in imports.store.review_needed())
    # Seed a real single-book recovery for human review without applying it.
    book_id=int(book.id.rsplit(':',1)[1]);current=run_request(library,dict(action='read',book=book_id,uuid=book.uuid),root/'covers')
    payload=hub.recovery_store.capture(current['library_uuid'],book.uuid,current['current'],dict(current['current'],tags=current['current']['tags']+['M5 Desktop Recovery']),1,'desktop-recovery')
    hub.recovery_store.preserve(payload)
    check('recovery_seed_does_not_write', 'M5 Desktop Recovery' not in run_request(library,dict(action='read',book=book_id,uuid=book.uuid),root/'covers')['current']['tags'])
    # Fresh process discovers only; no Qt windows or Calibre writes are needed.
    code='import sys;sys.path.insert(0,sys.argv.pop(1));from mediainator.recovery import RecoveryStore;import sys,json;r=RecoveryStore(*sys.argv[1:]);print(json.dumps(r.discover()))'
    discovered=json.loads(subprocess.check_output([sys.executable,'-I','-B','-c',code,str(MODULE_ROOT),str(root/'data'),hub.state['profile_id'],hub.state['device_id']],cwd=root,text=True))
    check('fresh_process_recovery_discovery',len(discovered['records'])==1 and discovered['records'][0]['state']=='unresolved')
    # A pending bulk batch makes review/confirm/discard available in the desktop fixture.
    store=BulkStore(root/'bulk',library);identities=[dict(book=int(b.id.rsplit(':',1)[1]),uuid=b.uuid) for b in initial[:3]]
    response=run_request(library,dict(action='bulk_read',books=identities),root/'covers')
    pending=plan(store,identities,response,'Add Tags',dict(tags=['M5 Desktop Batch']));store.save(pending)
    hub.activity.batch(pending,store.folder/(pending['id']+'.json'),'bulk')
    hub.activity_panel.refresh();check('startup_attention_counts_no_double_total',hub.activity.store.summary()['total']==2)
    # Scale fixture: 1000 owned operations / 4000 attempts, not user history.
    scale=ActivityStore(root/'scale','scale-profile','scale-device');scale.record('Bulk edits','template',outcome='failure',pending=True)
    data=scale._read();template=next(iter(data['operations'].values()));data['operations']={}
    for i in range(1000):
        item=deepcopy(template);item['id']=str(i);item['key']=str(i);item['operation']=('Bulk edits','Ebook imports','Single-book metadata saves','Batch reverts')[i%4]
        item['attempts']=[dict(deepcopy(template['attempts'][0]),id=f'{i}-{j}',outcome=('failure','success','failure','interrupted')[j]) for j in range(4)]
        item['recovery']=i%3==0;item['dismissed']=i%5==0;data['operations'][str(i)]=item
    atomic_json(scale.path,data)
    start=time.monotonic();panel=ActivityPanel(ActivityBridge(scale,lambda _:None));panel.show_history();elapsed=time.monotonic()-start
    check('scale_full_history_1000_operations',sum(panel.history.tree.topLevelItem(i).childCount() for i in range(panel.history.tree.topLevelItemCount()))==1000,seconds=round(elapsed,3))
    check('scale_distinct_attention_and_latest_actual_failure',scale.summary()['total']==800 and all(g['failure']['attempt']['outcome']=='failure' for g in scale.latest().values()))
    panel.history.close();panel.close()
    # A valid cover for the separate emergency desktop scenario.
    image=QImage(40,60,QImage.Format.Format_RGB32);image.fill(0xff375a7f);image.save(str(root/'replacement.png'))
    hub.persist();hub.activity_panel.grab().save(str(out/'activity.png'))
finally:
    unchanged=hashes(seed)==before
    (out/'application_report.json').write_text(json.dumps(dict(module_root=str(MODULE_ROOT),root=str(root),library=str(library),seed_unchanged=unchanged,checks=checks,desktop_confirmation='pending'),indent=2))
    assert unchanged,'Disposable seed changed'
    hub.hide()
