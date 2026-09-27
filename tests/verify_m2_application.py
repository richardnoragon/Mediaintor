"""Explicit real Qt/Calibre application acceptance on a fresh disposable copy."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import json,tempfile,shutil,time,hashlib
from unittest.mock import patch
from PyQt6.QtWidgets import QApplication,QMessageBox
from mediainator.settings import SettingsStore
from mediainator.window import Hub
from mediainator.metadata import run_request

app=QApplication([]);root=Path(tempfile.mkdtemp(prefix='mediainator-m2-desktop-'));lib=root/'library'
source=Path('/home/sproket01/Calibre Library')
def hashes(folder):return {str(p.relative_to(folder)):hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*') if p.is_file()}
before=hashes(source);shutil.copytree(source,lib)
(lib/'.mediainator-disposable.json').write_text(json.dumps({'purpose':'mediainator-disposable-test','root':str(lib)}))
store=SettingsStore(root/'settings.json');state=store.load();state['library']=str(lib)
hub=Hub(store,state,live=True);hub.show();module=hub.bookinator
out=Path('test_data/m2_acceptance');checks=[]
def until(predicate):
    deadline=time.monotonic()+45
    while not predicate():
        app.processEvents();time.sleep(.01)
        if time.monotonic()>deadline:raise AssertionError('Timed out: '+module.note.text())
def check(name,value):
    checks.append(dict(test=name,passed=bool(value)));print(name,value,flush=True);assert value,name
until(lambda:len(module.books)==101 and not module.loader.active)
check('101_catalog',len(module.books)==101)
module.search.setText('The Time Machine');check('title_search',len(module.visible)==1)
module.select(0);book=module.visible[0];check('multi_format_group',set(book.formats)=={'EPUB','MOBI','PDF'})
module.edit_metadata();editor=module.editor;check('editor_read',editor.baseline is not None)
original=editor.baseline.copy();editor.title.setText('M2 Desktop Review');editor.series.setText('Acceptance series');editor.number.setText('2.5');editor.tags.addItem('M2 acceptance')
check('draft_dirty',editor.dirty())
with patch('mediainator.editor.QMessageBox.question',return_value=QMessageBox.StandardButton.Cancel):check('cancel_hub_close',not hub.review_close() and editor.dirty())
check('save_actual_editor',editor.save_changes())
until(lambda:not module.loader.active)
app.processEvents()
check('path_refresh',any(b.title=='M2 Desktop Review' and all(Path(p).exists() for _,p in b.paths) for b in module.books))
# Search now filters out the renamed record; close any old editor and select current title.
module.search.setText('M2 Desktop Review');module.select(0)
if module.editor is None:module.edit_metadata()
editor=module.editor
editor.series.clear();check('clear_editor_save',editor.save_changes())
until(lambda:not module.loader.active);app.processEvents()
check('hidden_index',editor.baseline['series_index'] is None and editor.number.isHidden())
# Fresh external mutation between editor load and Save; leave local draft intact.
editor.title.setText('Local draft')
current=run_request(lib,dict(action='read',book='32',uuid=book.uuid),root/'recovery')['current']
run_request(lib,dict(action='save',book='32',uuid=book.uuid,baseline=current,changes={'title':'External edit'}),root/'recovery')
module.auto_refresh();check('dirty_external_refresh_deferred','Refresh pending' in module.note.text() and editor.title.text()=='Local draft')
with patch.object(editor,'resolve',return_value=None) as resolve:
    check('conflict_cancel_keeps_draft',not editor.save_changes() and editor.title.text()=='Local draft' and resolve.called)
check('discard_reads_external',editor.discard() and editor.title.text()=='External edit')
until(lambda:not module.loader.active);app.processEvents()
module.search.setText('External edit');module.select(0)
if module.editor is None:module.edit_metadata()
editor=module.editor
editor.set_cover(None);check('editor_cover_removal',editor.save_changes())
until(lambda:not module.loader.active);app.processEvents()
editor.set_cover(original['cover']);check('editor_cover_replacement',editor.save_changes())
until(lambda:not module.loader.active);app.processEvents()
check('untouched_html',editor.baseline['comments']==original['comments'])
hub.grab().save(str(out/'hub.png'));editor.grab().save(str(out/'editor.png'))
check('original_library_unchanged',before==hashes(source))
module.refresh_timer.stop();editor.done(0);until(lambda:not module.loader.active);hub.close();app.processEvents()
(out/'application_report.json').write_text(json.dumps(dict(root=str(root),library=str(lib),checks=checks),indent=2))
# Keep this isolated copy and settings for user desktop acceptance.
