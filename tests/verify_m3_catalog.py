"""101-book hub integration for import, review filtering and metadata correction."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import tempfile,json,shutil,time
from PyQt6.QtWidgets import QApplication
from mediainator.window import Hub
from mediainator.settings import SettingsStore
app=QApplication([]);root=Path(tempfile.mkdtemp(prefix='mediainator-m3-catalog-'))
w=json.loads(Path('test_data/m3_validation/workspace.json').read_text());lib=root/'library';shutil.copytree(w['baseline'],lib)
store=SettingsStore(root/'settings.json');state=store.load();state['library']=str(lib)
hub=Hub(store,state,live=True);hub.show();module=hub.bookinator
checks=[]
def until(predicate):
 end=time.monotonic()+60
 while not predicate():
  app.processEvents();time.sleep(.01)
  if time.monotonic()>end:raise AssertionError(module.note.text())
def check(name,passed):
 checks.append(dict(test=name,passed=bool(passed)));print(name,passed,flush=True);assert passed,name
until(lambda:len(module.books)==101 and not module.loader.active)
module.open_imports();d=module.import_dialog;d.preview([str(Path(w['fixtures'])/'missing-both.epub')]);d.execute_batch()
until(lambda:len(module.books)==102 and not module.loader.active)
check('101_to_102_catalog_refresh',len(module.books)==102)
d.close();module.needs_review.setChecked(True);check('needs_review_list',len(module.visible)==1)
module.select(0);module.edit_metadata();e=module.editor
check('independent_initial_status','Incomplete' in e.review_status.text() and 'Needs Metadata Review' in e.review_status.text())
e.title.setText('Corrected metadata');e.authors.clear();e.authors.addItem('Verified Author');assert e.save_changes()
until(lambda:not module.loader.active);app.processEvents()
check('save_does_not_clear_review','Completeness: Complete' in e.review_status.text() and 'Needs Metadata Review' in e.review_status.text())
e.mark_reviewed();until(lambda:not module.loader.active);app.processEvents()
check('explicit_mark_reviewed',not module.import_store().review_needed())
module.needs_review.setChecked(False);hub.grab().save('test_data/m3_acceptance/catalog.png')
if module.editor:module.editor.done(0)
until(lambda:not module.loader.active);hub.close()
Path('test_data/m3_acceptance/catalog_report.json').write_text(json.dumps(dict(root=str(root),checks=checks),indent=2))
