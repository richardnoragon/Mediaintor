"""Run with calibre-debug -e test_data/m5_validation/verify.py.
Validates a candidate protocol on a new disposable copy, not an M5 implementation.
"""
import sys
from pathlib import Path
PROJECT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(PROJECT));sys.path.insert(0,str(Path(__file__).parent))
import json, tempfile, shutil, base64
from copy import deepcopy
from unittest.mock import patch
from calibre.db.legacy import LibraryDatabase
from calibre.db.cache import Cache
from calibre.utils.lock import singleinstance
from mediainator.calibre_metadata_helper import execute
from mediainator.import_store import fingerprint, ImportStore, atomic_json
from mediainator.bulk import BulkStore, plan
from mediainator.snapshot import Snapshot
from mediainator.reader import external_readers
import protocol

out=PROJECT/'test_data/m5_validation';checks=[]
root=Path(tempfile.mkdtemp(prefix='mediainator-m5-validation-',dir='/tmp'));library=root/'library'
source=Path('/home/sproket01/Calibre Library')
def hashes(folder):return {str(p.relative_to(folder)):fingerprint(p) for p in folder.rglob('*') if p.is_file()}
def check(name,passed):
 checks.append(dict(test=name,passed=bool(passed)));(out/'checks.json').write_text(json.dumps(checks,indent=2));print(name,passed,flush=True);assert passed,name

if external_readers(include_calibre=True):raise SystemExit('Close Calibre/readers before running disposable validation. No windows were closed.')
assert singleinstance('db'),'Calibre database lock is unavailable; no writes attempted'
before=hashes(source)
snapshot=Snapshot(source).create();shutil.copytree(snapshot.root,library);snapshot.close()
(library/'.mediainator-disposable.json').write_text(json.dumps(dict(purpose='mediainator-disposable-test',root=str(library))))
db=LibraryDatabase(str(library));api=db.new_api;book=min(api.all_book_ids());book_uuid=api.field_for('uuid',book);library_uuid=api.library_id;count=len(api.all_book_ids());db.close()
identity=dict(profile='validation-profile',device='validation-device',library=library_uuid,book=book_uuid)
def call(action='read',**kw):
 # The outer real db lock is held for this whole experiment; execute otherwise
 # attempts to acquire the same process-global non-reentrant lock a second time.
 with patch('calibre.utils.lock.singleinstance',return_value=True):
  return execute(dict(action=action,library=str(library),book=book,uuid=book_uuid,library_uuid=library_uuid,recovery_dir=str(root/'cover-backups'),**kw))
try:
 check('fresh_101_book_copy',count==101)
 format_before=sorted(fingerprint(p) for p in library.rglob('*') if p.suffix.lower() in ('.epub','.mobi','.pdf'))
 baseline=call()['current'];draft=dict(baseline,title='M5 committed title',tags=['M5 pending'])
 original=Cache.set_field
 def fail_tags(self,field,mapping,**kw):
  if field=='tags':raise OSError('Injected tag write failure')
  return original(self,field,mapping,**kw)
 with patch.object(Cache,'set_field',fail_tags):
  first=call('save',baseline=baseline,changes={'title':draft['title'],'tags':draft['tags']})
  retry=call('save',baseline=first['current'],changes={'tags':draft['tags']})
 check('save_retry_failure_keeps_committed_title',first['saved']==['title'] and 'tags' in retry['errors'] and retry['current']['title']==draft['title'])
 payload=protocol.capture(identity,retry['current'],dict(retry['current'],tags=draft['tags']))
 check('only_unsaved_fields_captured',set(payload['pending'])=={'tags'} and set(payload['baseline'])=={'tags'})
 path=protocol.preserve(root/'Recovery'/'Single Book Edits',root/'activity-index.json',payload)
 check('durable_readback_and_discovery',protocol.read(path,identity)==payload and json.loads((root/'activity-index.json').read_text())['records'][payload['id']]==str(path))
 check('close_continuation_requires_requested_close_and_same_revision',protocol.close_allowed(True,True,2,2) and not protocol.close_allowed(False,True,2,2) and not protocol.close_allowed(True,False,2,2) and not protocol.close_allowed(True,True,3,2))
 before_restart=hashes(library);restored=protocol.read(path,identity)
 check('restart_discovery_does_not_write',hashes(library)==before_restart and restored['state']=='unresolved')
 current=call()['current'];call('save',baseline=current,changes={'tags':['External tags'],'comments':'<p>Unrelated external description</p>'})
 current=call()['current'];recovered,blocked=protocol.reviewed_draft(restored,current)
 check('external_change_requires_review',recovered is None and blocked==['tags'])
 recovered,_=protocol.reviewed_draft(restored,current,{'tags':'current'})
 check('keep_current_choice',recovered['tags']==['External tags'])
 recovered,_=protocol.reviewed_draft(restored,current,{'tags':'recovered'})
 pre_review=hashes(library)
 check('reconstructed_draft_preserves_unrelated_values',recovered['comments']==current['comments'] and recovered['title']==draft['title'] and hashes(library)==pre_review)
 saved=call('save',baseline=current,changes={'tags':recovered['tags']})
 check('explicit_recovery_save_verified',not saved['errors'] and saved['current']['tags']==draft['tags'] and saved['current']['comments']==current['comments'])
 # Pending image survives removal of the chosen source file; exact unedited HTML survives.
 from qt.core import QImage,QColor,QBuffer,QIODevice
 image=QImage(20,30,QImage.Format.Format_RGB32);image.fill(QColor('blue'));buffer=QBuffer();buffer.open(QIODevice.OpenModeFlag.WriteOnly);image.save(buffer,'PNG')
 selected=root/'selected.png';selected.write_bytes(bytes(buffer.data()))
 image_bytes=selected.read_bytes();cover=base64.b64encode(image_bytes).decode();html='<p class="original">Recovery <b>HTML</b> &amp; text</p>'
 current=saved['current'];rich=protocol.capture(identity,current,dict(current,cover=cover,comments=html))
 rich_path=protocol.preserve(root/'Recovery'/'Single Book Edits',root/'image-index.json',rich);selected.unlink()
 recovered=protocol.read(rich_path,identity)
 check('cover_bytes_and_html_roundtrip',base64.b64decode(recovered['pending']['cover'])==image_bytes and recovered['pending']['comments']==html)
 protocol.preserve(root/'Recovery'/'Single Book Edits',root/'activity-index.json',rich)
 check('multiple_copies_remain_discoverable',set(json.loads((root/'activity-index.json').read_text())['records'])=={payload['id'],rich['id']})
 # A later change after review is rejected by the real locked adapter.
 current=call()['current'];recovery_draft=dict(current,tags=['Recovered after review'])
 call('save',baseline=current,changes={'tags':['Changed during review']})
 raced=call('save',baseline=current,changes={'tags':recovery_draft['tags']})
 check('save_revalidates_changes_after_recovery_review',raced.get('conflicts')==['tags'] and raced['current']['tags']==['Changed during review'])
 # An uncertain acknowledgement can preserve all intended fields, then exclude
 # values that are already committed from the explicit recovered Save.
 uncertain=protocol.capture(identity,current,recovery_draft)
 current=call()['current'];call('save',baseline=current,changes={'tags':recovery_draft['tags']})
 current=call()['current'];uncertain_draft,blocked=protocol.reviewed_draft(uncertain,current)
 from mediainator.metadata_rules import changes
 check('already_committed_recovery_is_noop',not blocked and not changes(current,uncertain_draft))
 # Fault before replace: existing good copy survives. Failures do not authorize close.
 with patch('mediainator.import_store.os.replace',side_effect=OSError('Injected full disk')):
  try:protocol.preserve(root/'Recovery'/'Single Book Edits',root/'activity-index.json',payload);raise AssertionError('missing fault')
  except OSError:check('failed_replace_preserves_existing_copy',protocol.read(path,identity)==payload)
 with patch('protocol.atomic_json',side_effect=PermissionError('Injected destination denied')):
  try:protocol.preserve(root/'denied',root/'denied-index.json',payload);raise AssertionError('missing fault')
  except PermissionError:check('failed_destination_blocks_close',not protocol.close_allowed(True,False,2,2))
 alternate=protocol.preserve(root/'alternate-location',root/'alternate-index.json',payload)
 check('alternate_location_registered_and_verified',protocol.read(alternate,identity)==payload)
 def fail_registry(path,value):
  if Path(path).name=='failed-index.json':raise OSError('Injected registry write failure')
  atomic_json(path,value)
 with patch('protocol.atomic_json',side_effect=fail_registry):
  try:protocol.preserve(root/'unindexed',root/'failed-index.json',payload);raise AssertionError('missing fault')
  except OSError:check('registration_failure_not_success',not (root/'failed-index.json').exists() and (root/'unindexed'/(payload['id']+'.json')).exists())
 corrupt=root/'corrupt.json';envelope=json.loads(path.read_text());envelope['payload']['pending']['tags']=['tampered'];corrupt.write_text(json.dumps(envelope));old=corrupt.read_bytes()
 try:protocol.read(corrupt,identity);raise AssertionError('corruption accepted')
 except ValueError:check('corrupt_copy_preserved_and_rejected',corrupt.read_bytes()==old)
 for dimension in ('profile','device','library','book'):
  try:protocol.read(path,dict(identity,**{dimension:'different'}));raise AssertionError('identity accepted')
  except ValueError:check('reject_wrong_'+dimension,True)
 new_schema=deepcopy(payload);new_schema['schema']=99;unknown=root/'future.json';unknown.write_text(json.dumps(dict(payload=new_schema,sha256=protocol.digest(new_schema))))
 try:protocol.read(unknown,identity);raise AssertionError('schema accepted')
 except ValueError:check('unknown_schema_preserved',unknown.exists())
 hidden=deepcopy(payload);protocol.dismiss(hidden)
 check('dismiss_preserves_pending_payload',hidden['pending']==payload['pending'] and hidden['state']=='unresolved')
 try:protocol.delete_allowed(hidden);raise AssertionError('unresolved deletion allowed')
 except ValueError:check('unresolved_delete_blocked',True)
 try:protocol.discard(hidden,True);raise AssertionError('unreviewed discard allowed')
 except ValueError:check('review_required_before_discard',True)
 hidden['reviewed']=True;protocol.discard(hidden,True)
 check('separate_discard_then_delete',not hidden['pending'] and protocol.delete_allowed(hidden))
 # M3 review status must survive activity deletion: record the existing coupling,
 # and verify copying the status to independent state before deleting the journal.
 imports=ImportStore(root/'imports',library)
 ipath,ibatch=imports.create(dict(library_uuid=library_uuid,items=[dict(source='fixture.epub',operation_uuid='fixture-operation',state='complete',missing=['title'],destination_uuid=book_uuid)]))
 attention=imports.review_needed();atomic_json(root/'book-review-state.json',dict(schema=1,needs_review=sorted(attention)));ipath.unlink()
 check('review_status_can_be_detached_before_history_deletion',book_uuid in json.loads((root/'book-review-state.json').read_text())['needs_review'] and not imports.review_needed())
 # Existing bulk history blocks deleting unresolved work and survives restarts.
 bulk=BulkStore(root/'bulk',library);current=call()['current']
 bplan=plan(bulk,[dict(book=book,uuid=book_uuid)],dict(library_uuid=library_uuid,records={book_uuid:current},errors={}),'Add Tags',dict(tags=['M5 bulk pending']))
 bulk.save(bplan)
 try:bulk.delete(bplan);raise AssertionError('pending bulk delete allowed')
 except ValueError:check('existing_bulk_delete_guard',len(BulkStore(root/'bulk',library).pending())==1)
 check('all_ebook_contents_preserved',format_before==sorted(fingerprint(p) for p in library.rglob('*') if p.suffix.lower() in ('.epub','.mobi','.pdf')))
finally:
 unchanged=hashes(source)==before
 report=dict(kind='candidate protocol/capability validation, not M5 application acceptance',library=str(library),root=str(root),source_unchanged=unchanged,checks=checks)
 (out/'results.json').write_text(json.dumps(report,indent=2));assert unchanged,'Original library changed during validation'
