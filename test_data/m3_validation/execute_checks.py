"""Explicit Calibre 9.2.1 capability/protocol tests; disposable targets only."""
from pathlib import Path
import sys, os, json, hashlib, tempfile, shutil, uuid, subprocess
from calibre.db.legacy import LibraryDatabase
from calibre.ebooks.metadata.meta import get_metadata
from calibre.ebooks.metadata.book.base import Metadata
from calibre.utils.lock import singleinstance
from calibre.constants import __version__

# Child is covered by the orchestrator's held Calibre lock; only it opens this DB.
if len(sys.argv)>1 and sys.argv[1]=='--commit-without-ack':
    request=json.loads(Path(sys.argv[2]).read_text())
    lib=Path(request['library']);assert lib.name=='recovery' and lib.parent.name.startswith('run-') and lib.parent.parent.name.startswith('mediainator-m3-validation-')
    db=LibraryDatabase(str(lib));mi=Metadata('Crash recovery case',['Validation']);mi.uuid=request['uuid']
    db.new_api.add_books([(mi,{'EPUB':request['source']})],preserve_uuid=True,run_hooks=False,apply_import_tags=False)
    db.close()
    os._exit(23)  # Deliberate process exit after commit, before journal acknowledgement.

out=Path(__file__).resolve().parent
workspace=json.loads((out/'workspace.json').read_text());root=Path(workspace['root']).resolve();baseline=Path(workspace['baseline']).resolve();fixtures=Path(workspace['fixtures']).resolve();source=Path(workspace['source_library']).resolve()
assert root.name.startswith('mediainator-m3-validation-') and root.parent==Path('/tmp')
assert baseline.parent==root and fixtures.parent==root
assert __version__=='9.2.1'
def manifest(folder):
    return {str(p.relative_to(folder)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(folder.rglob('*')) if p.is_file()}
for folder,name in [(baseline,'baseline_manifest.json'),(fixtures,'fixture_manifest.json')]:
    assert manifest(folder)==json.loads((out/name).read_text()),'Prepared fixture/baseline changed'
source_before=manifest(source)
assert singleinstance('db'),'Close Calibre before validation'
run=Path(tempfile.mkdtemp(prefix='run-',dir=root));checks=[];events=[];dbs=[]
def journal(path, data):
    tmp=path.with_suffix('.new')
    with tmp.open('w') as f:
        json.dump(data,f,indent=2);f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)
    fd=os.open(path.parent,os.O_RDONLY);os.fsync(fd);os.close(fd)
def record(case,passed,**data):
    checks.append(dict(case=case,passed=bool(passed),**data));journal(out/'checks.json',checks);print(case,passed,flush=True)
    assert passed,case

def open_db(name,full=False):
    target=run/name
    assert target.parent==run
    if full:shutil.copytree(baseline,target)
    db=LibraryDatabase(str(target));dbs.append(db);return db

def inventory(api):
    return {str(i):dict(uuid=api.field_for('uuid',i),title=api.field_for('title',i),authors=list(api.field_for('authors',i)),tags=list(api.field_for('tags',i)),series=api.field_for('series',i),series_index=api.field_for('series_index',i),comments=api.field_for('comments',i),cover=hashlib.sha256(api.cover(i) or b'').hexdigest(),formats={fmt:hashlib.sha256(api.format(i,fmt)).hexdigest() for fmt in api.formats(i)}) for i in api.all_book_ids()}
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def metadata(path):
    if path.suffix.lower()=='.epub':
        import zipfile, xml.etree.ElementTree as ET
        with zipfile.ZipFile(path) as z:
            if z.read('mimetype').strip()!=b'application/epub+zip':raise ValueError('Invalid EPUB mimetype')
            tree=ET.fromstring(z.read('META-INF/container.xml'))
            opf=next(e.attrib['full-path'] for e in tree.iter() if e.tag.endswith('rootfile'))
            ET.fromstring(z.read(opf))
            if z.testzip() is not None:raise ValueError('Corrupt EPUB archive member')
    with path.open('rb') as f:mi=get_metadata(f,path.suffix[1:])
    return mi

def add(api,path,title=None):
    mi=metadata(path)
    if title:mi.title=title
    ids,dups=api.add_books([(mi,{path.suffix[1:].upper():str(path)})],add_duplicates=True,run_hooks=False,apply_import_tags=False)
    assert len(ids)==1 and not dups
    i=ids[0];assert hashlib.sha256(api.format(i,path.suffix[1:].upper())).hexdigest()==digest(path)
    events.append(dict(action='add_books',source=str(path),title=mi.title,id=i,uuid=api.field_for('uuid',i)))
    return i
try:
    parsed={}
    for path in sorted(fixtures.rglob('*')):
        if not path.is_file():continue
        try:
            if path.suffix.lower() not in {'.epub','.mobi','.pdf'}:raise ValueError('Unsupported format')
            mi=metadata(path);parsed[str(path.relative_to(fixtures))]={'title':mi.title,'authors':mi.authors}
        except Exception as exc:parsed[str(path.relative_to(fixtures))]={'error':f'{type(exc).__name__}: {exc}'}
    full=open_db('imports',True);before_existing=inventory(full.new_api)
    record('V01',len(before_existing)==101 and 'error' in parsed['invalid.epub'] and 'error' in parsed['unsupported.txt'],parsed=parsed)
    clean=open_db('clean');api=clean.new_api
    imported={fmt:add(api,fixtures/('time-machine.'+fmt)) for fmt in ['epub','mobi','pdf']}
    clean.close();dbs.remove(clean);clean=LibraryDatabase(str(run/'clean'));dbs.append(clean);api=clean.new_api
    record('V02',len(api.all_book_ids())==3 and all(api.format(i,f.upper()) for f,i in imported.items()),ids=imported,scope='Calibre API copy with import hooks disabled')
    known={h for r in before_existing.values() for h in r['formats'].values()};seen=set();decisions=[]
    for path in [fixtures/'time-machine.epub',fixtures/'nested/deeper/renamed-identical.epub',fixtures/'different-content-same-metadata.epub',fixtures/'different-content-same-metadata.epub']:
        h=digest(path);duplicate=h in known or h in seen;seen.add(h);decisions.append({'source':str(path),'skip_duplicate':duplicate})
    record('V03',[x['skip_duplicate'] for x in decisions]==[True,True,False,True] and inventory(full.new_api)==before_existing,decisions=decisions,scope='hash-policy harness, not application duplicate UI')
    variant=fixtures/'different-content-same-metadata.epub';mi=metadata(variant)
    identical=digest(variant) in known
    candidates=[i for i,r in before_existing.items() if r['title']==mi.title]
    i=add(full.new_api,variant)
    record('V04',not identical and bool(candidates) and len(full.new_api.all_book_ids())==102,similar_title_candidates=candidates,explicit_harness_action='create distinct record, no merge',new_id=i)
    missing_results=[];markers=[]
    # Calibre extraction synthesizes defaults; raw OPF provenance determines missing fields.
    import zipfile,xml.etree.ElementTree as ET
    for name in ['missing-title','missing-author','missing-both']:
        path=fixtures/(name+'.epub')
        with zipfile.ZipFile(path) as z:
            container=ET.fromstring(z.read('META-INF/container.xml'));opf=next(e.attrib['full-path'] for e in container.iter() if e.tag.endswith('rootfile'));tree=ET.fromstring(z.read(opf))
        missing=[field for field,tag in [('title','title'),('authors','creator')] if not any((e.text or '').strip() for e in tree.iter('{http://purl.org/dc/elements/1.1/}'+tag))]
        mi=metadata(path)
        if 'title' in missing:mi.title=path.stem
        if 'authors' in missing:mi.authors=['Unknown']
        ids,_=api.add_books([(mi,{'EPUB':str(path)})],add_duplicates=True,run_hooks=False,apply_import_tags=False);bid=ids[0]
        markers.append({'uuid':api.field_for('uuid',bid),'missing':missing,'needs_metadata_review':True})
        missing_results.append({'fixture':name,'parsed':parsed[path.name],'effective_title':api.field_for('title',bid),'effective_authors':list(api.field_for('authors',bid)),'missing':missing})
        assert ('title' not in missing or api.field_for('title',bid)==path.stem) and ('authors' not in missing or list(api.field_for('authors',bid))==['Unknown'])
    journal(run/'review_markers.json',markers)
    record('V05',len(json.loads((run/'review_markers.json').read_text()))==3,results=missing_results,scope='provenance/sidecar protocol only; marker UI not implemented',filename_convention='stem without extension in this experiment')
    attach=open_db('attachments',True);aa=attach.new_api;existing_attach=inventory(aa);bid=add(aa,fixtures/'time-machine.epub','Explicit attachment target');initial=inventory(aa)[str(bid)]
    results=[aa.add_format(bid,fmt,str(fixtures/('time-machine.'+fmt.lower())),replace=False,run_hooks=False) for fmt in ['MOBI','PDF']]
    after=inventory(aa)[str(bid)]
    record('V06',all(results) and {k:v for k,v in initial.items() if k!='formats'}=={k:v for k,v in after.items() if k!='formats'} and all(after['formats'][f]==digest(fixtures/('time-machine.'+f.lower())) for f in ['EPUB','MOBI','PDF']),book=bid,uuid=after['uuid'])
    old=after['formats']['EPUB'];refused=aa.add_format(bid,'EPUB',str(variant),replace=False,run_hooks=False)
    race=add(aa,fixtures/'time-machine.epub','Race target');assert 'MOBI' not in aa.formats(race)
    aa.add_format(race,'MOBI',str(fixtures/'time-machine.mobi'),replace=False,run_hooks=False)
    raced=aa.add_format(race,'MOBI',str(fixtures/'time-machine.mobi'),replace=False,run_hooks=False)
    record('V07',not refused and not raced and inventory(aa)[str(bid)]['formats']['EPUB']==old,collision_return=refused,post_preview_collision_return=raced)
    staged=run/'staged.epub';shutil.copy2(variant,staged);preview_hash=digest(staged);before_cancel=inventory(api)
    # Cancel sends no mutation; changing a scratch source invalidates its preview fingerprint.
    staged.write_bytes(staged.read_bytes()+b'changed after preview');stale=digest(staged)!=preview_hash
    vanished=run/'vanished.epub';shutil.copy2(fixtures/'missing-title.epub',vanished);vanished.unlink()
    record('V08',stale and not vanished.exists() and inventory(api)==before_cancel,scope='cancel/stale-plan protocol; UI pending',invalid_inputs=parsed['invalid.epub'])
    recovery=open_db('recovery',True);rr=recovery.new_api;existing_recovery=inventory(rr)
    first=add(rr,variant,'Recovery completed item')
    # Real Calibre partial failure: metadata row can commit before missing format fails.
    missing_mi=Metadata('Injected missing file',['Validation'])
    failure=None
    try:rr.add_books([(missing_mi,{'EPUB':str(vanished)})],run_hooks=False)
    except Exception as exc:failure=f'{type(exc).__name__}: {exc}'
    orphan_ids=[i for i in rr.all_book_ids() if rr.field_for('title',i)=='Injected missing file']
    lock=subprocess.run(['/usr/bin/calibre-debug','-c','from calibre.utils.lock import singleinstance; print(singleinstance("db"))'],capture_output=True,text=True)
    record('V09',bool(failure) and rr.has_id(first) and lock.stdout.strip()=='False',failure=failure,partial_record_ids=orphan_ids,partial_record_formats={str(i):rr.formats(i) for i in orphan_ids},lock_result=lock.stdout.strip())
    batch={'library':str(run/'recovery'),'completed':[{'id':first,'uuid':rr.field_for('uuid',first)}],'pending':[{'source':str(fixtures/'time-machine.mobi'),'state':'pending'},{'source':str(fixtures/'time-machine.pdf'),'state':'pending'}],'failed':[{'id':i,'state':'unverified-format-failure'} for i in orphan_ids],'resume_automatically':False}
    journal(run/'batch.json',batch);record('V10',rr.format(first,'EPUB') is not None and len(batch['pending'])==2,scope='stop-after-current-item harness; durable journal, no next item started')
    crash_uuid=str(uuid.uuid4());intent={'library':str(run/'recovery'),'source':str(variant),'sha256':digest(variant),'uuid':crash_uuid,'state':'in-flight'};journal(run/'intent.json',intent)
    recovery.close();dbs.remove(recovery)
    child=subprocess.run(['/usr/bin/calibre-debug','-e',str(Path(__file__).resolve()),'--','--commit-without-ack',str(run/'intent.json')],capture_output=True,text=True,timeout=45)
    recovery=LibraryDatabase(str(run/'recovery'));dbs.append(recovery);rr=recovery.new_api
    matches=[i for i in rr.all_book_ids() if rr.field_for('uuid',i)==crash_uuid and hashlib.sha256(rr.format(i,'EPUB') or b'').hexdigest()==intent['sha256']]
    record('V11',child.returncode==23 and len(matches)==1 and json.loads((run/'intent.json').read_text())['state']=='in-flight',exit_code=child.returncode,reconciled_ids=matches,scope='real child process exit after commit before acknowledgement',stderr=child.stderr[-500:])
    intent['state']='verified-success';intent['id']=matches[0];journal(run/'intent.json',intent)
    restored=json.loads((run/'batch.json').read_text());before_retry=inventory(rr)
    retry_plan=[dict(item,sha256=digest(item['source']),confirmation_required=True) for item in restored['pending']]
    journal(run/'retry_preview.json',retry_plan)
    # Confirmed harness retry repairs the known partial record rather than adding another.
    assert len(orphan_ids)==1
    repair_id=orphan_ids[0];repair_uuid=rr.field_for('uuid',repair_id);count_before_repair=len(rr.all_book_ids())
    repair_source=fixtures/'missing-title.epub'
    repair_plan={'action':'attach to tracked partial record','id':repair_id,'uuid':repair_uuid,'source':str(repair_source),'sha256':digest(repair_source),'replace':False,'confirmation':'explicit validation scenario'}
    journal(run/'repair_preview.json',repair_plan)
    repaired=rr.add_format(repair_id,'EPUB',str(repair_source),replace=False,run_hooks=False)
    assert repaired and len(rr.all_book_ids())==count_before_repair and rr.field_for('uuid',repair_id)==repair_uuid and hashlib.sha256(rr.format(repair_id,'EPUB')).hexdigest()==repair_plan['sha256']
    before_discard=inventory(rr)
    # Discard only work entries, without sending any database removal command.
    for item in restored['pending']:item['state']='discarded-pending'
    journal(run/'batch.json',restored)
    record('V12',all(i['confirmation_required'] for i in retry_plan) and inventory(rr)==before_discard and rr.has_id(first) and len(matches)==1,scope='persisted Review/Retry/Discard protocol plus explicit partial-record repair; no automatic resumption',repaired_id=repair_id,repair_preserved_id_uuid_and_count=True)
    for db,base in [(full,before_existing),(attach,existing_attach),(recovery,existing_recovery)]:
        now=inventory(db.new_api);assert all(now[k]==v for k,v in base.items())
    for db in list(dbs):db.close();dbs.remove(db)
    # Reopen all targets and verify they remain readable after mutation/recovery.
    counts={}
    for name in ['imports','clean','attachments','recovery']:
        db=LibraryDatabase(str(run/name));counts[name]=len(db.new_api.all_book_ids());journal(run/(name+'-final.json'),inventory(db.new_api));db.close()
    record('V13',manifest(source)==source_before and manifest(baseline)==json.loads((out/'baseline_manifest.json').read_text()) and manifest(fixtures)==json.loads((out/'fixture_manifest.json').read_text()),counts=counts,original_records_preserved=True)
finally:
    for db in dbs:db.close()
    journal(out/'events.json',events)
    unchanged=manifest(source)==source_before
    journal(out/'results.json',{'version':__version__,'run_root':str(run),'source_unchanged':unchanged,'checks':checks,'gate':'M3-G OPEN; application acceptance not run','scope':'Calibre capability and recovery-protocol validation, not production M3 implementation'})
    assert unchanged,'Original library changed during validation'
