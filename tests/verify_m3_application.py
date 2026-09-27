"""Explicit M3 integration checks on new disposable libraries; never source writes."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import json,tempfile,subprocess,os,shutil,hashlib
from PyQt6.QtWidgets import QApplication,QMessageBox
from unittest.mock import patch
from mediainator.import_dialog import ImportDialog
from mediainator.imports import call_helper
from mediainator.import_store import atomic_json,ImportStore
app=QApplication([])
root=Path(tempfile.mkdtemp(prefix='mediainator-m3-acceptance-'));lib=root/'library'
setup=root/'setup.py';setup.write_text('from calibre.db.legacy import LibraryDatabase\nimport sys\ndb=LibraryDatabase(sys.argv[1]);db.close()\n')
env=dict(os.environ,QT_QPA_PLATFORM='offscreen',CALIBRE_CONFIG_DIRECTORY=str(root/'config'))
subprocess.run(['/usr/bin/calibre-debug','-e',str(setup),'--',str(lib)],env=env,check=True,capture_output=True)
w=json.loads(Path('test_data/m3_validation/workspace.json').read_text());fixtures=Path(w['fixtures']);source=Path(w['source_library'])
def hashes(folder):return {str(p.relative_to(folder)):hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*') if p.is_file()}
source_before=hashes(source);fixture_before=hashes(fixtures)
out=Path('test_data/m3_acceptance');out.mkdir(exist_ok=True);checks=[]
def check(name,condition):
 checks.append(dict(test=name,passed=bool(condition)));print(name,condition,flush=True);assert condition,name
 atomic_json(out/'application_checks.json',checks)
def choose_new(dialog):
 for action,dest in dialog.choices:
  if action.isEnabled():action.setCurrentText('Create new book')
def ready(dialog):return all(i['state'] in {'complete','duplicate','discarded','invalid'} for i in dialog.batch['items'])
d=ImportDialog(lib,root/'state');d.show()
d.preview([str(fixtures/'time-machine.epub')]);check('preview_no_write',not d.store.batches())
d.execute_batch();check('epub_import',ready(d) and d.batch['items'][0]['state']=='complete')
book=d.batch['items'][0]['destination_uuid']
for fmt in ['mobi','pdf']:
 d.preview([str(fixtures/('time-machine.'+fmt))]);check(fmt+'_explicit_similar_choice',d.choices[0][0].currentText()=='Choose action…')
 d.choices[0][0].setCurrentText('Attach to existing book');d.choices[0][1].setCurrentIndex(1);d.execute_batch()
 check(fmt+'_attachment',d.batch['items'][0]['state']=='complete' and d.batch['items'][0]['destination_uuid']==book)
d.preview([str(fixtures/'time-machine.epub'),str(fixtures/'nested/deeper/renamed-identical.epub')]);check('duplicates_skipped',all(i['state']=='duplicate' for i in d.plan['items']))
d.preview([str(fixtures/'missing-both.epub'),str(fixtures/'invalid.epub')]);check('invalid_isolated',d.plan['items'][1]['state']=='invalid');d.execute_batch()
check('fallback_flag',d.batch['items'][0]['state']=='complete' and d.batch['items'][0]['destination_uuid'] in d.store.review_needed())
# Stale source detected after preview; failed item remains journaled.
staged=root/'changing.epub';shutil.copy2(fixtures/'different-content-same-metadata.epub',staged)
d.preview([str(staged)]);choose_new(d);staged.write_bytes(staged.read_bytes()+b'changed');d.execute_batch();check('stale_source_refused',d.batch['items'][0]['state']=='failed')
# Retry rebuilds preview, remains uncommitted until confirmation, and uses same journal.
oldpath=d.journal;d.retry();check('retry_requires_confirmation',d.plan is not None and d.journal==oldpath)
choose_new(d);d.execute_batch();check('retry_reuses_journal',d.journal==oldpath and d.batch['items'][0]['state']=='complete')
# Controlled stop after one verified item with a real persisted remainder.
d.preview([str(fixtures/'missing-title.epub'),str(fixtures/'missing-author.epub')]);choose_new(d)
original=d.request
count=[0]
def stop_after_one(request):
 result=original(request)
 if request['action']=='execute':count[0]+=1;d.stop()
 return result
with patch.object(d,'request',side_effect=stop_after_one):d.execute_batch()
check('stop_after_current',count[0]==1 and d.batch['items'][0]['state']=='complete' and d.batch['items'][1]['state']=='pending')
stopped_path=d.journal;d.close()
restarted=ImportDialog(lib,root/'state');check('restart_no_automatic_resume',bool(restarted.store.pending()) and json.loads(stopped_path.read_text())['items'][1]['state']=='pending')
restarted.journal=stopped_path;restarted.batch=json.loads(stopped_path.read_text());restarted.retry();choose_new(restarted);restarted.execute_batch();check('restart_retry',ready(restarted) and restarted.batch['items'][-1]['state']=='complete')
# Simulate a lost acknowledgement by reverting only journal state, then reconcile real committed bytes.
journal=restarted.journal;batch=json.loads(journal.read_text());idx=len(batch['items'])-1;batch['items'][idx]['state']='in-flight';atomic_json(journal,batch)
response=call_helper(dict(action='reconcile',library=str(lib),journal=str(journal),index=idx,library_uuid=batch['library_uuid']))
check('commit_without_ack_reconciled',response['item']['state']=='complete')
# Independent library mutation after preview invalidates the pending plan.
restarted.preview([str(fixtures/'missing-author.epub')])
# Already imported input is duplicate and never added again.
check('post_retry_duplicate',restarted.plan['items'][0]['state']=='duplicate')
# Preserve completed items when pending invalid work is discarded.
restarted.journal=stopped_path;restarted.batch=json.loads(stopped_path.read_text());restarted.plan=None
with patch('mediainator.import_dialog.QMessageBox.question',return_value=QMessageBox.StandardButton.Yes):restarted.discard_pending()
check('discard_keeps_completed',all(i['state']=='complete' for i in json.loads(stopped_path.read_text())['items']))
# A source not yet in the library, followed by a real metadata change after preview.
stale=root/'new-stale.epub';stale.write_bytes((fixtures/'different-content-same-metadata.epub').read_bytes()+b'new-case')
restarted.preview([str(stale)]);choose_new(restarted)
from mediainator.metadata import run_request
current=run_request(lib,dict(action='read',book='1',uuid=book),root/'backup')['current']
run_request(lib,dict(action='save',book='1',uuid=book,baseline=current,changes={'title':'Externally changed after preview'}),root/'backup')
restarted.execute_batch();check('library_changed_requires_review',restarted.batch['items'][0]['state']=='failed' and 'Library changed' in restarted.batch['items'][0]['warning'])
restarted.retry();choose_new(restarted);restarted.execute_batch();check('fresh_preview_after_external_change',restarted.batch['items'][0]['state']=='complete')
# Metadata-only partial record created under the pre-journaled operation UUID.
partial=root/'partial.epub';partial.write_bytes((fixtures/'missing-title.epub').read_bytes()+b'partial-case')
restarted.preview([str(partial)]);intent=restarted.plan['items'][0]
partial_uuid=intent['operation_uuid']
seed=root/'partial.py';seed.write_text("from calibre.db.legacy import LibraryDatabase\nfrom calibre.ebooks.metadata.book.base import Metadata\nimport sys\ndb=LibraryDatabase(sys.argv[1]);mi=Metadata('Partial',['Validation']);mi.uuid=sys.argv[2];db.new_api.create_book_entry(mi,add_duplicates=True,preserve_uuid=True);db.close()\n")
subprocess.run(['/usr/bin/calibre-debug','-e',str(seed),'--',str(lib),partial_uuid],env=env,check=True,capture_output=True)
# First attempt detects stale preview; Retry keeps the same operation identity.
choose_new(restarted);restarted.execute_batch();check('partial_record_requires_repreview',restarted.batch['items'][0]['state']=='failed')
restarted.retry();choose_new(restarted);restarted.execute_batch();check('partial_record_repaired_same_uuid',restarted.batch['items'][0]['state']=='complete' and restarted.batch['items'][0]['destination_uuid']==partial_uuid)
check('source_and_fixtures_unchanged',hashes(source)==source_before and hashes(fixtures)==fixture_before)
restarted.grab().save(str(out/'imports.png'));restarted.close()
atomic_json(out/'application_report.json',dict(root=str(root),library=str(lib),checks=checks,source_unchanged=True))
