"""Explicit disposable-copy M4 integration run; never writes the source library."""
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time
from copy import deepcopy
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from PyQt6.QtWidgets import QApplication
from mediainator.snapshot import Snapshot
from mediainator.import_store import fingerprint
from mediainator.bulk import BulkStore, plan, reconcile, revert_plan
from mediainator.bulk_worker import BulkWorker
from mediainator.metadata import run_request

app=QApplication.instance() or QApplication([])
out=Path('test_data/m4_acceptance');out.mkdir(exist_ok=True)
source=Path('/home/sproket01/Calibre Library')
def hashes(root):return {str(p.relative_to(root)):fingerprint(p) for p in root.rglob('*') if p.is_file()}
before=hashes(source)
root=Path(tempfile.mkdtemp(prefix='mediainator-m4-acceptance-'));library=root/'library'
snapshot=Snapshot(source).create()
shutil.copytree(snapshot.root,library);snapshot.close()
(library/'.mediainator-disposable.json').write_text(json.dumps(dict(purpose='mediainator-disposable-test',root=str(library))))
store=BulkStore(root/'bulk',library)
# Read identities via a read-only SQLite connection on the disposable database.
import sqlite3
with sqlite3.connect(f'file:{library}/metadata.db?mode=ro',uri=True) as db:
    identities=[dict(book=row[0],uuid=row[1]) for row in db.execute('select id,uuid from books order by id')]
selected=identities[:4];checks=[]
def check(name,passed):
    checks.append(dict(test=name,passed=bool(passed)));(out/'application_checks.json').write_text(json.dumps(checks,indent=2))
    print(name,passed,flush=True);assert passed,name

def read(ids=selected):
    for attempt in range(10):
        try:return run_request(library,dict(action='bulk_read',books=ids),root/'recovery')
        except RuntimeError as exc:
            if 'Waiting for library access' not in str(exc) or attempt==9:raise
            time.sleep(1)
def build(operation,**options):return plan(store,selected,read(),operation,options)
def execute(batch,stop_after=None,attempt=0):
    worker=BulkWorker(store,batch=batch);results=[];errors=[]
    worker.result.connect(results.append);worker.failure.connect(errors.append)
    if stop_after is not None:
        counter=[0]
        def stop(_):
            counter[0]+=1
            if counter[0]==stop_after:worker.requestInterruption()
        # QThread interruption is effective while running, not direct run().
        worker.progress.connect(stop)
    from PyQt6.QtCore import QEventLoop
    loop=QEventLoop();worker.finished.connect(loop.quit);worker.start();loop.exec();worker.wait()
    assert not errors,errors
    result=results[0]
    # Test-driver retries are explicit fresh reviews; the application never auto-resumes.
    if stop_after is None and attempt<5 and any('Waiting for library access' in str(i.get('errors',{})) for i in result['items']):
        print('Contention safely retained; test driver reviews and confirms a retry',flush=True)
        time.sleep(1)
        result=reconcile(result,read([dict(book=i['book'],uuid=i['uuid']) for i in result['items']]))
        return execute(result,attempt=attempt+1)
    return result

def save(identity,baseline,**changes):
    for attempt in range(10):
        try:return run_request(library,dict(action='save',**identity,baseline=baseline,changes=changes),root/'recovery')
        except RuntimeError as exc:
            if 'Waiting for library access' not in str(exc) or attempt==9:raise
            time.sleep(1)

try:
    check('101_records_read',len(read(identities)['records'])==101)
    formats_before={str(p.relative_to(library)):fingerprint(p) for p in library.rglob('*') if p.suffix.lower() in ('.epub','.mobi','.pdf')}
    batch=build('Add Tags',tags=['M4 verified']);batch=execute(batch)
    check('four_book_add_verified',all(i['state']=='complete' and 'tags' in i['applied'] for i in batch['items']))
    original=deepcopy(batch)
    batch=execute(revert_plan(store,batch,read()))
    check('revert_tag_only',all(i['state']=='complete' for i in batch['items']) and all('M4 verified' not in r['tags'] for r in read()['records'].values()))
    batch=build('Set Series',series='M4 sequence',mode='Sequential',start=0,increment=0.5)
    batch['items'][1]['state']='excluded';batch=execute(batch)
    response=read()
    check('sequence_preserves_exclusion_gap',[response['records'][selected[i]['uuid']]['series_index'] for i in (0,2,3)]==[0,1,1.5])
    batch=execute(build('Clear Series'))
    check('clear_hides_orphan_index',all(not r['series'] and r['series_index'] is None for r in read()['records'].values()))
    batch=execute(build('Set Series',series='M4 keep default',mode='Keep existing'))
    check('keep_without_series_defaults_one',all(r['series_index']==1 for r in read()['records'].values()))
    batch=build('Add Tags',tags=['M4 conflict']);base=read()['records'][selected[1]['uuid']]
    save(selected[1],base,tags=['External edit'])
    batch=execute(batch)
    check('one_conflict_others_continue',[i['state'] for i in batch['items']]==['complete','conflict','complete','complete'])
    response=read();batch=reconcile(batch,response);item=batch['items'][1]
    item['baseline']=deepcopy(item['current']);item['state']='pending';item['conflicts']=[]
    batch=execute(batch)
    check('reviewed_conflict_retry',all(i['state']=='complete' for i in batch['items']))
    base=read()['records'][selected[0]['uuid']];save(selected[0],base,tags=['Changed after batch'])
    reverted=revert_plan(store,batch,read())
    check('revert_detects_later_edit',reverted['items'][0]['state']=='conflict')
    reverted=execute(reverted)
    check('revert_unaffected_continue',reverted['items'][0]['state']=='conflict' and all(i['state']=='complete' for i in reverted['items'][1:]))
    batch=build('Add Tags',tags=['M4 stop']);batch=execute(batch,stop_after=1)
    check('stop_preserves_pending',any(i['state']=='pending' for i in batch['items']) and any(i['state']=='complete' for i in batch['items']))
    restarted=BulkStore(root/'bulk',library)
    check('restart_no_auto_resume',any(b['id']==batch['id'] for b in restarted.pending()))
    batch=reconcile(batch,read());batch=execute(batch)
    check('pending_retry_verified',all(i['state']=='complete' for i in batch['items']))
    interrupted_revert=execute(revert_plan(store,batch,read()),stop_after=1)
    check('revert_stop_retains_pending',any(i['state']=='pending' for i in interrupted_revert['items']))
    interrupted_revert=reconcile(interrupted_revert,read());interrupted_revert=execute(interrupted_revert)
    check('revert_restart_retry',all(i['state']=='complete' for i in interrupted_revert['items']))
    # Simulate loss of acknowledgement after an actual committed save.
    batch=build('Add Tags',tags=['M4 lost ack']);item=batch['items'][0]
    item['state']='inflight';item['attempt_before']={f:item['baseline'][f] for f in item['desired']};store.save(batch)
    save(selected[0],item['baseline'],**item['desired'])
    batch=reconcile(batch,read());store.save(batch)
    check('lost_ack_reconciled',batch['items'][0]['state']=='complete' and bool(batch['items'][0]['applied']))
    batch=execute(batch)
    # Exact author replacement and internal file path changes.
    base=read()['records'][selected[0]['uuid']];save(selected[0],base,authors=['M4 Target','M4 Coauthor','M4 Replacement'])
    base=read()['records'][selected[1]['uuid']];save(selected[1],base,authors=['M4 Targets','Other'])
    batch=execute(build('Replace Author',old='M4 Target',new='M4 Replacement'))
    records=read()['records']
    check('exact_author_order_dedup',records[selected[0]['uuid']]['authors']==['M4 Replacement','M4 Coauthor'] and records[selected[1]['uuid']]['authors']==['M4 Targets','Other'])
    # Paths may change but content multiset must remain identical.
    formats_after=[fingerprint(p) for p in library.rglob('*') if p.suffix.lower() in ('.epub','.mobi','.pdf')]
    check('all_format_contents_preserved',sorted(formats_before.values())==sorted(formats_after))
    check('all_book_identities_preserved',set(read(identities)['records'])=={i['uuid'] for i in identities})
    batch=build('Remove Tags',tags=['M4 stop']);batch=execute(batch)
    check('remove_tags_verified',all('M4 stop' not in r['tags'] for r in read()['records'].values()))
    store.delete(batch);check('explicit_history_deletion',all(b['id']!=batch['id'] for b in store.batches()))
    # Scale uses the same approved operation and normal worker, on the disposable copy.
    scale=plan(store,identities,read(identities),'Add Tags',dict(tags=['M4 scale']))
    scale=execute(scale)
    check('101_book_batch',all(i['state']=='complete' for i in scale['items']) and len(scale['items'])==101)
    scale=execute(revert_plan(store,scale,read(identities)))
    check('101_book_revert',all(i['state']=='complete' for i in scale['items']))
    # Exercise the actual preview UI without writing via a live original library.
    from mediainator.catalog import Book
    from mediainator.bulk_dialog import BulkDialog
    records=read()['records']
    books=[Book('calibre:'+str(i['book']),records[i['uuid']]['title'],', '.join(records[i['uuid']]['authors']),(),(),uuid=i['uuid']) for i in selected]
    dialog=BulkDialog(library,root/'ui-bulk',books)
    dialog.operation.setCurrentText('Add Tags');dialog.tags.addItem('M4 UI');dialog.preview()
    check('ui_preview_without_write',dialog.batch is not None and not dialog.store.batches() and all('M4 UI' not in r['tags'] for r in read()['records'].values()))
    dialog.table.item(1,0).setCheckState(__import__('PyQt6.QtCore',fromlist=['Qt']).Qt.CheckState.Unchecked)
    dialog.execute()
    check('ui_confirmation_and_exclusion',dialog.batch['items'][1]['state']=='excluded' and all(i['state']=='complete' for n,i in enumerate(dialog.batch['items']) if n!=1))
    dialog.show();app.processEvents();dialog.grab().save(str(out/'bulk_preview.png'));dialog.close()

finally:
    unchanged=hashes(source)==before
    (out/'application_report.json').write_text(json.dumps(dict(library=str(library),root=str(root),source_unchanged=unchanged,checks=checks),indent=2))
    assert unchanged,'Original library changed during validation'
