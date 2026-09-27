"""Disposable evidence for review findings; run from repository root."""
import json,tempfile
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch
from PyQt6.QtWidgets import QApplication,QMessageBox
from mediainator.paper_store import PaperStore,PaperStoreError
from mediainator.paper_ui import Paperinator
from mediainator.settings import defaults
app=QApplication.instance() or QApplication([])
results={}
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp);state=defaults();store=PaperStore(root/'library',state['profile_id']);store.initialize()
 # Recovery must not change another profile's files before checking ownership.
 part=store.files_dir/'.staging/active.part';part.parent.mkdir(parents=True);part.write_bytes(b'in-progress')
 other=PaperStore(store.root,str(uuid4()))
 try: other.recover()
 except PaperStoreError: pass
 results['foreign_profile_recovery_removed_staging_file']=not part.exists()
 # Cancelling the second draft review must not discard the first draft.
 panel=Paperinator(state,lambda:True,store)
 first=panel.add_item();first.title.setText('First unsaved item')
 second=panel.new_note();second.title.setText('Second unsaved note')
 with patch.object(QMessageBox,'question',side_effect=[QMessageBox.StandardButton.Discard,QMessageBox.StandardButton.Cancel]):
  accepted=panel.review_close()
 results['cancelled_close_already_discarded_first_draft']=not accepted and not first.dirty()
 for editor in panel.editors:editor.approve_close()
 panel.shutdown();panel.deleteLater()
print(json.dumps(results,indent=2))
Path('test_data/m18_m19_review/findings_reproduced.json').write_text(json.dumps(results,indent=2)+'\n')
