"""Real Calibre snapshots plus installed-candidate duplicate GUI lifecycle."""
import sys,json,subprocess,time
from pathlib import Path
from dataclasses import replace
from types import SimpleNamespace
sys.path.insert(0,'/release')
from PyQt6.QtWidgets import QApplication,QWidget
from PyQt6.QtTest import QTest
from mediainator.snapshot import Snapshot
from mediainator.library import parse_catalog
from mediainator.discovery_store import DiscoveryStore
from mediainator.duplicate_ui import DuplicateDialog
app=QApplication([]);lib=Path('/fixture/library');host=QWidget();host.library=lib
store=DiscoveryStore('/tmp/probe-state',lib,'probe',{'profile_id':'test','device_id':'test'});host.discovery_context=lambda:(store,store.load(),[])
snapshots=[]
def load():
 snap=Snapshot(lib).create();snapshots.append(snap)
 output=subprocess.check_output(['/usr/bin/calibredb','list','--with-library',str(snap.root),'--for-machine','--fields','title,authors,tags,formats,cover,uuid,series'])
 def original(value):return str(lib/Path(value).relative_to(snap.root))
 host.books=tuple(replace(b,id=b.id.replace(str(snap.root),str(lib),1),paths=tuple((f,original(p)) for f,p in b.paths),cover=original(b.cover) if b.cover else '') for b in parse_catalog(snap.root,output))
 host.loader=SimpleNamespace(active=False,snapshot=snap)
load();dialog=DuplicateDialog(host);dialog.show();dialog.scan();deadline=time.monotonic()+120
while dialog.worker:
 if time.monotonic()>deadline:raise TimeoutError('scan')
 QTest.qWait(10)
message=dialog.status.text();rows=list(dialog.model.rows)
assert message.startswith('Scan complete.') and '0 errors' in message,message
assert '100 identical-content groups' in message,message
assert rows
checks=[]
for n in range(2):
 load();dialog.catalog_refreshed();app.processEvents()
 assert not dialog.stale and dialog.status.text()==message and dialog.model.rows==rows
 checks.append('coherent unchanged 10000-book snapshot refresh '+str(n+1)+' preserves scan result')
report=dict(status='passed',completion=message,visible_rows=len(rows),checks=checks,scope='Installed candidate; pinned Calibre, immutable real fixture; no synthetic reading/review overlays')
Path('/reports/duplicate_refresh_scale.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2),flush=True)
dialog.close();host.close()
for snapshot in snapshots:snapshot.close()
