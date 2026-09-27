"""Run against installed modules, with paths supplied only by the disposable verifier."""
import json,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from PyQt6.QtCore import QCoreApplication,QStandardPaths
from mediainator.settings import SettingsStore,SettingsError
from mediainator.activity import ActivityStore,ActivityBridge
from mediainator.recovery import RecoveryStore
from mediainator.import_store import ImportStore
from mediainator.bulk import BulkStore,plan
app=QCoreApplication([]);app.setApplicationName('Media-inator');app.setOrganizationName('Media-inator')
config=Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation))
data=Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation))
store=SettingsStore(config/'settings.json');state=store.load();library=Path.home()/'library'
if sys.argv[2]=='seed':
    state.update(library=str(library),view='List',profile_name='Retained personal profile');store.save(state)
activity=ActivityStore(data/'Activity',state['profile_id'],state['device_id'])
recovery=RecoveryStore(data,state['profile_id'],state['device_id'],ActivityBridge(activity,lambda msg:None))
imports=ImportStore(config/'imports',library);bulk=BulkStore(config/'bulk',library)
record=dict(title='Retained book',authors=['Author'],tags=['Old'],series='',series_index=None,comments='<p>Exact text</p>',cover=None,uuid='book')
if sys.argv[2]=='seed':
    payload=recovery.capture('library-identity','book',record,dict(record,tags=['Pending']),1,'pending-save')
    recovery.preserve(payload)
    imports.create(dict(library_uuid='library-identity',items=[dict(source=str(Path.home()/'source.epub'),state='pending',operation_uuid='pending-import')]))
    batch=plan(bulk,[dict(book=1,uuid='book')],dict(library_uuid='library-identity',records={'book':record},errors={}), 'Add Tags',dict(tags=['Queued']))
    bulk.save(batch)
else:
    assert state['view']=='List' and state['profile_name']=='Retained personal profile'
    found=recovery.discover();assert not found['errors'] and len(found['records'])==1
    assert found['records'][0]['payload']['pending']=={'tags':['Pending']}
    assert found['records'][0]['state']=='unresolved'
    assert len(imports.pending())==1 and len(bulk.pending())==1
    assert activity.records() and activity.records()[0]['recovery']
    draft=recovery.draft(found['records'][0]['payload'],record,library_uuid='library-identity',book_uuid='book')
    assert draft
    old=store.path.read_bytes();invalid=dict(state,schema_version=999)
    store.path.write_text(json.dumps(invalid))
    try:
        try:store.load()
        except SettingsError:pass
        else:raise AssertionError('Unknown schema was accepted')
        assert json.loads(store.path.read_text())['schema_version']==999
    finally:store.path.write_bytes(old)
print(json.dumps({'config':str(config),'data':str(data),'profile_id':state['profile_id'],'device_id':state['device_id'],'recovery':len(recovery.discover()['records']),'imports':len(imports.pending()),'bulk':len(bulk.pending())}))
