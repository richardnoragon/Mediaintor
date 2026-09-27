"""Installed baseline measurements; Qt offscreen timings are not KDE acceptance."""
import sys,json,time,statistics,platform,subprocess,resource,os
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,os.environ.get('M14_CODE_ROOT','/scripts'))
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer,QT_VERSION_STR
from mediainator.snapshot import Snapshot
from mediainator.library import parse_catalog
from mediainator.catalog import find_books
from mediainator.settings import SettingsStore
from mediainator.window import Hub
app=QApplication([]);root=Path('/fixture');lib=root/'library';out=Path('/reports')
report=dict(build=os.environ.get('M14_BUILD','M14 source candidate'),machine=dict(platform=platform.platform(),python=sys.version,qt=QT_VERSION_STR,cpu=Path('/proc/cpuinfo').read_text().split('model name')[1].split('\n')[0] if 'model name' in Path('/proc/cpuinfo').read_text() else platform.machine(),memory=Path('/proc/meminfo').read_text().splitlines()[0]),mode='Qt offscreen; actual installed application catalog/render paths, not compositor/keyboard-to-screen KDE acceptance',limitations=['Advanced discovery measured separately below with documented synthetic reading and review overlay','No saved reader annotations in generated fixture','Page cache not forcibly cleared; first run is process-cold, not guaranteed storage-cold'])
def save():
 (out/os.environ.get('M14_REPORT','candidate_performance.json')).write_text(json.dumps(report,indent=2)+'\n')
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

from dataclasses import replace
from mediainator.discovery import DiscoveryIndex,empty_query,warning_id
from mediainator.discovery_ui import DiscoveryDialog
from mediainator.discovery_store import DiscoveryStore
from mediainator.duplicate_ui import DuplicateWorker
mapping={r['uuid']:r for r in oracle}
overlay=tuple(replace(b,reading_status=mapping[b.uuid]['reading_status'],missing_fields=tuple(f for f,k in [('title','missing_title_provenance'),('author','missing_author')] if mapping[b.uuid][k])) for b in books)
state_store=DiscoveryStore(Path('/tmp/scale-discovery'),lib,'fixture',{'profile_id':'test','device_id':'test'})
state=state_store.load();state['manual_review']={r['uuid']:True for r in oracle if r['manual_review']};warnings=[]
for r in oracle:
 if r['import_warning']:
  w=dict(destination_uuid=r['uuid'],source_batch='fixture',operation_uuid=r['uuid'],missing=['fixture warning'],reviewed=r['warning_acknowledged']);warnings.append(w)
# Exercise real Calibre library identity/provenance integration before the synthetic overlay.
real_store,real_state,real_warnings=module.discovery_context();assert real_store.identity['uuid'];report['real_library_identity_verified']=True
module.books=overlay;module.discovery_context=lambda:(state_store,state,warnings)
t=time.perf_counter();dialog=DiscoveryDialog(module);dialog.outer={};report['workbench_open_seconds']=time.perf_counter()-t;dialog.show();app.processEvents()
queries=[('unread_series_cover','all',[('reading_status','Unread'),('series','Series 04'),('missing_metadata','cover')],lambda r:r['reading_status']=='Unread' and r['series']=='Series 04' and not r['cover']),('missing_author_or_title','any',[('missing_metadata','author'),('missing_metadata','title')],lambda r:r['missing_author'] or r['missing_title_provenance']),('tags_all','all',[('tag','Tag 03'),('tag','Group 3')],lambda r:'Tag 03' in r['tags'] and 'Group 3' in r['tags']),('tags_any','any',[('tag','Tag 03'),('tag','Group 3')],lambda r:'Tag 03' in r['tags'] or 'Group 3' in r['tags']),('review','all',[],lambda r:r['missing_author'] or r['missing_title_provenance'] or not r['cover'] or r['manual_review'] or (r['import_warning'] and not r['warning_acknowledged']))]
report['advanced']={}
for name,mode,conditions,predicate in queries:
 expected={r['uuid'] for r in oracle if predicate(r)};elapsed=[]
 for run in range(23):
  dialog.filling=True;dialog.mode.setCurrentIndex(0 if mode=='all' else 1);dialog.text.setText('');dialog.review.setChecked(name=='review');dialog.conditions=[dict(field=f,value=v) for f,v in conditions];dialog.filling=False
  t=time.perf_counter();dialog.refresh();app.processEvents();dialog.repaint();dt=time.perf_counter()-t
  assert {b.uuid for b in dialog.model.books}==expected,(name,len(dialog.model.books),len(expected))
  if run>=3:elapsed.append(dt)
 report['advanced'][name]=dict(results=len(expected),handler_to_paint=stats(elapsed));save();print('advanced',name,len(expected),statistics.median(elapsed),flush=True)
# Include the actual text-change debounce and event processing in input latency.
from PyQt6.QtTest import QTest
text_times=[];saved_times=[]
dialog.filling=True;dialog.review.setChecked(False);dialog.conditions=[];dialog.outer={};dialog.text.setText('');dialog.filling=False;dialog.refresh()
for run in range(23):
 target='M14 Fixture 09999' if run%2 else 'M14 Fixture 09998'
 expected={r['uuid'] for r in oracle if target.casefold() in r['title'].casefold()}
 t=time.perf_counter();dialog.text.setText(target)
 while dialog.timer.isActive():QTest.qWait(1)
 app.processEvents();dialog.repaint();dt=time.perf_counter()-t
 assert {b.uuid for b in dialog.model.books}==expected
 if run>=3:text_times.append(dt)
q=dialog.query();state_store.update(0,lambda d:d['saved_searches'].update(test=dict(name='Saved scale query',query=q)))
dialog.state=state_store.load();dialog.reload_names('test')
for run in range(23):
 t=time.perf_counter();dialog.apply_saved();app.processEvents();dialog.repaint()
 if run>=3:saved_times.append(time.perf_counter()-t)
report['advanced']['text_input_including_debounce']=stats(text_times);report['advanced']['saved_search_apply']=stats(saved_times)
# Run scan on the real immutable snapshot, alongside painted discovery.
worker=DuplicateWorker(snap.root,overlay,{r['uuid'] for r in oracle if r['missing_title_provenance']});results=[];worker.result.connect(results.append);worker.start();concurrent=[]
while worker.isRunning():
 t=time.perf_counter();dialog.refresh();app.processEvents();dialog.repaint();concurrent.append(time.perf_counter()-t)
worker.wait();app.processEvents();assert results and not results[0]['errors'];assert len(results[0]['exact'])==100;assert len(results[0]['similar'])==180
report['duplicate_scan']=dict(exact_groups=len(results[0]['exact']),similar_groups=len(results[0]['similar']),files_hashed=results[0]['files_hashed'],search_during_scan=stats(concurrent));print('duplicates',100,180,'search median',statistics.median(concurrent),flush=True)
dialog.close();save()
report['peak_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
report['correctness']='Six catalog and five advanced result sets match independent fixture oracle across 23 runs each; duplicate groups match oracle' 
save();module.library=None;hub.close();snap.close();print('benchmark complete',flush=True)
