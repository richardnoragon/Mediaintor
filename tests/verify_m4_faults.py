"""Calibre API fault injection on a fresh disposable copy, with the real DB lock held."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import json, tempfile, shutil
from unittest.mock import patch
from calibre.db.legacy import LibraryDatabase
from calibre.db.cache import Cache
from calibre.utils.lock import singleinstance
from mediainator.calibre_metadata_helper import execute
from mediainator.bulk import BulkStore, plan, remaining, reconcile, revert_plan
from mediainator.import_store import fingerprint

out=Path('test_data/m4_acceptance');root=Path(tempfile.mkdtemp(prefix='mediainator-m4-faults-'));lib=root/'library'
source=Path('/home/sproket01/Calibre Library')
def hashes(folder):return {str(p.relative_to(folder)):fingerprint(p) for p in folder.rglob('*') if p.is_file()}
before=hashes(source);shutil.copytree(source,lib)
assert singleinstance('db'),'Close Calibre before validation'
store=BulkStore(root/'history',lib);checks=[]
def check(name,value):
 checks.append(dict(test=name,passed=bool(value)));print(name,value,flush=True)
 (out/'fault_checks.json').write_text(json.dumps(checks,indent=2));assert value,name

def call(**kw):
 with patch('calibre.utils.lock.singleinstance',return_value=True):
  return execute(dict(library=str(lib),recovery_dir=str(root/'recovery'),**kw))
db=LibraryDatabase(str(lib));ident=dict(book=1,uuid=db.new_api.field_for('uuid',1));db.close()
def read():return call(action='bulk_read',books=[ident])
def write(batch):
 item=batch['items'][0];item['state']='inflight';item['attempt_before']={f:item['baseline'][f] for f in remaining(item)};store.save(batch)
 response=call(action='save',**ident,library_uuid=batch['library_uuid'],baseline=item['baseline'],changes=remaining(item),bulk_journal=str(store.folder/(batch['id']+'.json')))
 return json.loads((store.folder/(batch['id']+'.json')).read_text()),response
try:
 baseline=call(action='read',**ident)['current'];call(action='save',**ident,baseline=baseline,changes={'series':'Old','series_index':3})
 batch=plan(store,[ident],read(),'Set Series',dict(series='New',mode='Fixed',fixed=5))
 original_set=Cache.set_field
 def fail_number(self,name,mapping,**kwargs):
  if name=='series_index':
   original_set(self,name,{1:2},**kwargs)
   raise OSError('Injected failure after an intermediate number write')
  return original_set(self,name,mapping,**kwargs)
 with patch.object(Cache,'set_field',fail_number):batch,response=write(batch)
 item=batch['items'][0]
 check('partial_series_commit_and_failed_number_observed',item['state']=='failed' and item['applied']['series']['before']=='Old' and item['applied']['series_index']=={'before':3,'after':2})
 batch=reconcile(batch,read());check('own_partial_value_not_external_conflict',batch['items'][0]['state']=='pending')
 batch,response=write(batch)
 check('retry_preserves_original_before',batch['items'][0]['state']=='complete' and batch['items'][0]['applied']['series_index']=={'before':3,'after':5})
 reverted=revert_plan(store,batch,read());reverted,response=write(reverted)
 check('revert_restores_original_coupled_values',response['current']['series']=='Old' and response['current']['series_index']==3)
 # Fail the final journal acknowledgement after the DB commit, keeping the in-flight intent.
 batch=plan(store,[ident],read(),'Add Tags',dict(tags=['M4 crash']))
 from mediainator.import_store import atomic_json
 count=[0]
 def fail_ack(path,value):
  count[0]+=1
  if count[0]==2:raise OSError('Injected outcome journal failure')
  return atomic_json(path,value)
 try:
  with patch('mediainator.import_store.atomic_json',side_effect=fail_ack):write(batch)
  raise AssertionError('fault was not injected')
 except OSError:pass
 batch=store.batches()[0]
 # Identify the exact journal, independent of ordering.
 batch=next(b for b in store.batches() if b['operation']=='Add Tags')
 check('unacknowledged_commit_keeps_intent',batch['items'][0]['state']=='inflight')
 batch=reconcile(batch,read());check('unacknowledged_commit_recovered',batch['items'][0]['state']=='complete' and 'tags' in batch['items'][0]['applied'])
 # A changed identity must stop all writes.
 item=batch['items'][0]
 try:call(action='save',**ident,library_uuid='wrong-library',baseline=item['baseline'],changes={'tags':['unsafe']});raise AssertionError('identity check absent')
 except ValueError:check('library_identity_rejected',True)
 with patch('calibre.utils.lock.singleinstance',return_value=False):
  try:execute(dict(action='bulk_read',library=str(lib),books=[ident]));raise AssertionError('lock ignored')
  except RuntimeError:check('library_lock_rejected',True)
finally:
 unchanged=hashes(source)==before
 (out/'fault_report.json').write_text(json.dumps(dict(library=str(lib),source_unchanged=unchanged,checks=checks),indent=2))
 assert unchanged,'Source changed during fault checks'
