"""Installed API checks used only on the separately restored M7 environment."""
import json,sys,sqlite3,hashlib
from pathlib import Path
release=(Path.home()/'.local/share/mediainator-install/current').resolve(strict=True)
sys.path.insert(0,str(release))
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QStandardPaths
from mediainator.settings import SettingsStore
from mediainator.window import Hub
from mediainator.catalog import Book
from mediainator.metadata import run_request
from mediainator.import_dialog import ImportDialog
from mediainator.bulk import BulkStore,plan
app=QApplication([]);app.setApplicationName('Media-inator');app.setOrganizationName('Media-inator')
config=Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation))
data=Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation))
store=SettingsStore(config/'settings.json');state=store.load();library=Path('/data/library')
expected=json.loads(Path('/qualification/expected_settings.json').read_text())
assert state['library']==str(library)
assert all(state[k]==expected[k] for k in ('view','profile_id','device_id','geometry','profile_name'))
# Sample Hub avoids loading/writing anything automatically; attach explicit restored identities.
hub=Hub(store,state,app_data=data);hub.library=library;hub.bookinator.library=library
with sqlite3.connect((library/'metadata.db').as_uri()+'?mode=ro',uri=True) as db:
    assert db.execute('pragma integrity_check').fetchone()[0]=='ok'
    assert db.execute('select count(*) from books').fetchone()[0]==101
    book_id,book_uuid=db.execute('select id,uuid from books order by id limit 1').fetchone()
book=Book(str(library)+':'+str(book_id),'Restored validation book','Author',(),(),uuid=book_uuid)
hub.bookinator.books=(book,)
def read():return run_request(library,dict(action='read',book=book_id,uuid=book_uuid),config/'covers')
mode=sys.argv[1];current=read();baseline=current['current'];marker='M7 Restored Recovery'
if mode=='seed':
    assert marker not in baseline['tags']
    payload=hub.recovery_store.capture(current['library_uuid'],book_uuid,baseline,dict(baseline,tags=baseline['tags']+[marker]),1,'m7-restored-recovery')
    hub.recovery_store.preserve(payload)
    import shutil
    source=Path('/data/import-sources/M7 pending import.epub')
    shutil.copy2(next(library.rglob('*.epub')),source)
    with source.open('ab') as stream:stream.write(b'\nM7 independent pending-import fixture\n')
    imports=ImportDialog(library,config/'imports');imports.preview([str(source)])
    assert imports.plan
    journal,batch=imports.store.create(imports.plan)
    hub.activity_controller.batch_record(batch,journal,'import')
    bulk=BulkStore(config/'bulk',library)
    identities=[dict(book=book_id,uuid=book_uuid)]
    records=run_request(library,dict(action='bulk_read',books=identities),config/'covers')
    pending=plan(bulk,identities,records,'Add Tags',dict(tags=['M7 Pending Bulk']))
    bulk.save(pending);hub.activity_controller.batch_record(pending,bulk.folder/(pending['id']+'.json'),'bulk')
    assert marker not in read()['current']['tags']
elif mode in ('check','recover'):
    from mediainator.import_store import ImportStore
    records=hub.recovery_store.discover();assert not records['errors']
    target=next(r for r in records['records'] if r['payload']['operation_id']=='m7-restored-recovery')
    assert target['state']=='unresolved'
    assert marker not in baseline['tags']
    assert ImportStore(config/'imports',library).pending()
    assert BulkStore(config/'bulk',library).pending()
    if mode=='recover':
        record=next(r for r in hub.activity.store.records() if r['source'].get('recovery_id')==target['payload']['id'])
        hub.activity_controller.review(record)
        editor=hub.bookinator.editor
        assert editor and editor.dirty() and marker not in read()['current']['tags']
        assert editor.save_changes()
        assert marker in read()['current']['tags']
        assert next(r for r in hub.recovery_store.discover()['records'] if r['payload']['id']==target['payload']['id'])['state']=='recovered'
        editor.done(0)
        updated=read()['current']
        run_request(library,dict(action='save',book=book_id,uuid=book_uuid,baseline=updated,changes={'tags':baseline['tags']}),config/'covers')
        assert read()['current']['tags']==baseline['tags']
elif mode!='catalog':raise SystemExit('Unknown verification action')
print(json.dumps({'mode':mode,'passed':True,'books':101,'view':state['view'],'profile_id':state['profile_id'],'device_id':state['device_id']}))
hub.hide()
