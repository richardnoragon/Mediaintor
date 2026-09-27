"""Deterministic M12-01 characterization: real UI handoff, controlled loader/I/O."""
import sys,json,tempfile,hashlib
from pathlib import Path
from dataclasses import replace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from PyQt6.QtWidgets import QApplication
from mediainator.window import Hub
from mediainator.settings import SettingsStore
from mediainator.editor import MetadataEditor
app=QApplication([])
class Loader:
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
  try:hub.activity_controller.review(record)
  except ValueError as exc:error=str(exc)
  else:raise AssertionError('Expected existing-editor handoff failure did not occur')
  assert error=='Current metadata could not be read; recovery was retained.'
  assert loader.active and loader.calls==1 and books.editor is None
  assert len(loads)==1,'Recovery metadata read should have been blocked before starting'
  assert path.read_bytes()==saved
  # Model loader completion, then repeat the identical owner action.
  loader.active=False;hub.activity_controller.review(record)
  assert books.editor and books.editor.dirty()
  assert books.editor.tags.values()==['Preserved M12 draft']
  assert books.editor.recovery_context['id']==payload['id']
  assert path.read_bytes()==saved
  found=hub.recovery_store.discover();assert next(r for r in found['records'] if r['payload']['id']==payload['id'])['state']=='unresolved'
  report=dict(reproduced=True,error=error,refresh_started_by_editor_finished=True,initial_metadata_loads=1,total_loads_after_retry=len(loads),retry_after_refresh_opens_preserved_draft=True,payload_unchanged=True,recovery_remains_unresolved_until_explicit_save=True,scope='Real Hub/Bookinator/MetadataEditor/ActivityController and recovery store; fake catalog loader and metadata-read boundary. Temporary sample data only; no Calibre, Docker or accepted installation accessed.',limitation='Reproduces a sufficient cause consistent with M11 symptoms; does not retrospectively prove the exact timing of the original desktop failure.')
  # Avoid close prompts; no catalog work or source/user writes during teardown.
  books.editor.fill(baseline);books.editor.on_saved=lambda:None;books.loader=None;hub.library=None;books.library=None;hub.state['selected_book']=None
  hub.close();app.processEvents()
 print(json.dumps(report,indent=2))
 (ROOT/'test_data/m12_usability/recovery_reproduction.json').write_text(json.dumps(report,indent=2)+'\n')
