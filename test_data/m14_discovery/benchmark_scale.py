"""Installed baseline measurements; Qt offscreen timings are not KDE acceptance."""
import sys,json,time,statistics,platform,subprocess,resource,os
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,'/release')
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer,QT_VERSION_STR
from mediainator.snapshot import Snapshot
from mediainator.library import parse_catalog
from mediainator.catalog import find_books
from mediainator.settings import SettingsStore
from mediainator.window import Hub
app=QApplication([]);root=Path('/fixture');lib=root/'library';out=Path('/reports')
report=dict(build='0.1.0a1-db6a7fb8885f9bd9',machine=dict(platform=platform.platform(),python=sys.version,qt=QT_VERSION_STR,cpu=Path('/proc/cpuinfo').read_text().split('model name')[1].split('\n')[0] if 'model name' in Path('/proc/cpuinfo').read_text() else platform.machine(),memory=Path('/proc/meminfo').read_text().splitlines()[0]),mode='Qt offscreen; actual installed application catalog/render paths, not compositor/keyboard-to-screen KDE acceptance',limitations=['M14 features not implemented; no M14 saved-search/review/advanced-filter/duplicate-scan performance claimed','No saved reader annotations in generated fixture','Page cache not forcibly cleared; first run is process-cold, not guaranteed storage-cold'])
def save():
 (out/'baseline_performance.json').write_text(json.dumps(report,indent=2)+'\n')
def stats(values):
 ordered=sorted(values)
 return dict(samples_seconds=values,median_seconds=statistics.median(values),p95_seconds=ordered[max(0,__import__('math').ceil(len(values)*.95)-1)],max_seconds=max(values))
t=time.perf_counter();snap=Snapshot(lib).create();report['snapshot_seconds']=time.perf_counter()-t;print('snapshot',report['snapshot_seconds'],flush=True)
t=time.perf_counter();output=subprocess.check_output(['/usr/bin/calibredb','list','--with-library',str(snap.root),'--for-machine','--fields','title,authors,tags,formats,cover,uuid,series']);report['calibre_list_seconds']=time.perf_counter()-t
t=time.perf_counter();books=parse_catalog(snap.root,output);report['parse_seconds']=time.perf_counter()-t;assert len(books)==10000
(out/'catalog.json').write_bytes(output)
store=SettingsStore(Path('/tmp/m14-bench/settings.json'));hub=Hub(store,store.load(),app_data=Path('/tmp/m14-bench/data'));hub.workspaces.timer.stop();module=hub.bookinator;module.refresh_timer.stop();module.reader_timer.stop();module.library=snap.root;module.compatibility_allowed=True
hub.resize(1280,900);hub.tabs.setCurrentWidget(module);hub.show();app.processEvents()
t=time.perf_counter();module.loaded(books);app.processEvents();module.repaint();report['loaded_to_paint_seconds']=time.perf_counter()-t;save();print('loaded/render',report['loaded_to_paint_seconds'],flush=True)
oracle=json.loads((root/'oracle.json').read_text())
cases=[('all','',(),()),('generated','M14 Fixture',(),()),('specific','M14 Fixture 09999',(),()),('tag','',('Tag 03',),()),('tag_any','',('Tag 03','Tag 04'),()),('unknown','',(),('Unknown',))]
report['cases']={}
for name,text,tags,statuses in cases:
 expected={r['uuid'] for r in oracle if text.casefold() in r['title'].casefold() and (not tags or set(tags)&set(r['tags']))}
 backend=[];ui=[]
 for run in range(23):
  t=time.perf_counter();found=find_books(books,text,tags=tags,statuses=statuses);elapsed=time.perf_counter()-t
  assert {b.uuid for b in found}==expected,(name,len(found),len(expected))
  if run>=3:backend.append(elapsed)
  module.search.blockSignals(True);module.search.setText(text);module.search.blockSignals(False)
  module.filter_values.update(tags=set(tags),statuses=set(statuses),formats=set())
  t=time.perf_counter();module.search_changed();app.processEvents();module.repaint();elapsed=time.perf_counter()-t
  if run>=3:ui.append(elapsed)
 report['cases'][name]=dict(results=len(expected),backend=stats(backend),search_handler_to_paint=stats(ui));save();print(name,len(expected),'UI median',statistics.median(ui),flush=True)
report['peak_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
report['correctness']='All six baseline result sets match independent fixture oracle across 23 runs each'
save();module.library=None;hub.close();snap.close();print('benchmark complete',flush=True)
