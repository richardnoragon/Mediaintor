"""First-click recovery, Cancel, and failed-read regression using temporary data."""
import sys,json,tempfile,hashlib
from pathlib import Path
from dataclasses import replace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from PyQt6.QtWidgets import QApplication
from mediainator.window import Hub
from mediainator.settings import SettingsStore
from mediainator.editor import MetadataEditor
app=QApplication([])
from PyQt6.QtCore import QObject, pyqtSignal
class Loader(QObject):
    loaded=pyqtSignal(object)
    failed=pyqtSignal(str)
    active=False
    calls=0
    def load(self):self.active=True;self.calls+=1
    def shutdown(self):self.active=False
with tempfile.TemporaryDirectory(prefix='m12-recovery-repro-') as tmp:
 root=Path(tmp);settings=SettingsStore(root/'config/settings.json');hub=Hub(settings,settings.load(),app_data=root/'data');hub.workspaces.timer.stop()
 books=hub.bookinator;library=root/'library';library.mkdir();hub.library=library;books.library=library
 book=replace(books.books[0],id=str(library)+':1',uuid='m12-repro-book');books.books=(book,);books.state['selected_book']=book.id
 baseline=dict(title=book.title,authors=['Test Author'],tags=[],series='',series_index=None,comments='',cover=None,uuid=book.uuid)
 payload=hub.recovery_store.capture('m12-library',book.uuid,baseline,dict(baseline,tags=['Preserved M12 draft']),1,'m12-reproduction')
 path=hub.recovery_store.preserve(payload);hub.recovery_store.sync_activity()
 record=next(r for r in hub.activity.store.records() if r['source'].get('recovery_id')==payload['id'])
 saved=path.read_bytes();loads=[]
 def load(editor):loads.append(editor.book.uuid);editor.library_uuid='m12-library';editor.fill(baseline);return True
 loader=Loader();books.loader=loader;books.compatibility_allowed=True
 with patch.object(MetadataEditor,'load',load),patch('mediainator.reader.external_readers',return_value=[]):
  books.edit_metadata();assert books.editor and books.editor.baseline
  hub.activity_panel.show_history(True)
  hub.activity_panel.show_details(record["id"])
  hub.activity_controller.review(record)
  assert not hub.activity_panel.history.isVisible()
  assert all(not dialog.isVisible() for dialog in hub.activity_panel.details if dialog.record_id==record["id"])
  assert books.editor.isVisible()
  assert not loader.active and loader.calls==0
  assert len(loads)==2,'Recovery must read current metadata on the first attempt'
  assert books.editor and books.editor.dirty()
  assert books.editor.tags.values()==['Preserved M12 draft']
  assert books.editor.recovery_context['id']==payload['id']
  assert path.read_bytes()==saved
  found=hub.recovery_store.discover();assert next(r for r in found['records'] if r['payload']['id']==payload['id'])['state']=='unresolved'
  report=dict(first_review_opens_preserved_draft=True,metadata_loads=len(loads),refresh_during_handoff=loader.calls,payload_unchanged=True)
  # Duplicate review of the ready dirty draft still follows explicit Cancel.
  from PyQt6.QtWidgets import QMessageBox
  ready=books.editor
  with patch.object(QMessageBox,'question',return_value=QMessageBox.StandardButton.Cancel):
   hub.activity_controller.review(record)
  assert books.editor is ready and ready.dirty() and path.read_bytes()==saved
  # Existing asynchronous refresh is awaited; duplicate clicks cannot duplicate the draft.
  ready.fill(baseline);loader.active=True
  hub.activity_controller.review(record)
  assert hub.activity_controller.pending_review is not None
  try:hub.activity_controller.review(record)
  except ValueError as exc:assert 'already waiting' in str(exc)
  else:raise AssertionError('Duplicate waiting review accepted')
  loader.active=False;loader.loaded.emit(books.books)
  assert hub.activity_controller.pending_review is None
  assert books.editor.dirty() and books.editor.tags.values()==['Preserved M12 draft']
  ready=books.editor;ready.fill(baseline);loader.active=True
  hub.activity_controller.review(record)
  hub.activity_controller.pending_review['cancel']()
  loader.active=False;loader.loaded.emit(books.books)
  assert not ready.dirty() and path.read_bytes()==saved
  # Simulate a metadata access failure: do not expose an empty editor or consume recovery.
  ready.fill(baseline)
  def denied(editor):editor.status.setText('Permission denied reading metadata');return False
  with patch.object(MetadataEditor,'load',denied):
   try:hub.activity_controller.review(record)
   except ValueError as exc:assert 'Permission denied' in str(exc)
   else:raise AssertionError('Expected explicit access failure')
  assert books.editor is None and path.read_bytes()==saved
  books.edit_metadata()
  # Avoid close prompts; no catalog work or source/user writes during teardown.
  books.editor.fill(baseline);books.editor.on_saved=lambda:None;books.loader=None;hub.library=None;books.library=None;hub.state['selected_book']=None
  hub.close();app.processEvents()
 print(json.dumps(report,indent=2))

