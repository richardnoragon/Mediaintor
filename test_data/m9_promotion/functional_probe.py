"""Installed M9 data/read/recovery checks inside a disposable container copy."""
import sys,os,json,sqlite3,hashlib
from pathlib import Path
base=Path.home()/'.local/share/mediainator-install';release=(base/'current').resolve();sys.path.insert(0,str(release))
from mediainator.settings import SettingsStore
from mediainator.import_store import ImportStore
from mediainator.bulk import BulkStore
from mediainator.activity import ActivityStore
from mediainator.recovery import RecoveryStore
from mediainator.progress import read_progress
library=Path('/data/library');config=Path.home()/'.config/Media-inator/Media-inator';data=Path.home()/'.local/share/Media-inator/Media-inator'
s=SettingsStore(config/'settings.json').load();assert s.get('library')==str(library)
c=sqlite3.connect((library/'metadata.db').as_uri()+'?mode=ro',uri=True)
libid=c.execute('select uuid from library_id').fetchone()[0];books={u for u, in c.execute('select uuid from books')}
formats=c.execute('select b.uuid,b.path,d.name,d.format from books b join data d on b.id=d.book').fetchall();assert len(books)==101
missing=[str(library/p/(n+'.'+f.lower())) for _,p,n,f in formats if not (library/p/(n+'.'+f.lower())).is_file()];assert not missing
imports=ImportStore(config/'imports',library).batches();bulk=BulkStore(config/'bulk',library).batches()
for path,batch in imports+bulk:
 assert batch.get('library_uuid')==libid
activity=ActivityStore(data/'Activity',s['profile_id'],s['device_id']);records=activity.records()
recovery=RecoveryStore(data,s['profile_id'],s['device_id']);recoveries=recovery.discover();assert not recoveries['errors']
for r in recoveries['records']:
 assert r['payload']['identity']['library_uuid']==libid
 assert r['payload']['identity']['book_uuid'] in books
ann=Path.home()/'.config/calibre/viewer/annots';progress=[]
for uuid,p,n,f in formats:
 result=read_progress(ann,library/p/(n+'.'+f.lower()))
 if result.position:progress.append({'uuid':uuid,'format':f,'has_position':True})
assert len(progress)>=3
for rec in records:
 source=rec.get('source',{})
 if source.get('library'):assert source['library']==str(library)
 if source.get('library_uuid'):assert source['library_uuid']==libid
 if source.get('book_uuid'):assert source['book_uuid'] in books
c.close()
# Synthetic recovery exists only in this disposable validation clone.
from mediainator.metadata_rules import FIELDS
uuid=next(iter(books));baseline=dict(title='Recovery fixture',authors=['Unknown'],tags=[],series='',series_index=None,comments='',cover=None,uuid=uuid)
draft=dict(baseline,tags=['M9 recovery fixture'])
before=hashlib.sha256((library/'metadata.db').read_bytes()).hexdigest()
payload=recovery.capture(libid,uuid,baseline,draft,1,'m9-validation')
recovery.preserve(payload)
again=RecoveryStore(data,s['profile_id'],s['device_id']);found=again.discover();assert not found['errors']
assert any(r['payload']['id']==payload['id'] for r in found['records'])
review=again.draft(payload,baseline,library_uuid=libid,book_uuid=uuid)
assert review['draft']['tags']==['M9 recovery fixture']
assert hashlib.sha256((library/'metadata.db').read_bytes()).hexdigest()==before

print(json.dumps({'build':release.name,'books':len(books),'formats':len(formats),'library_uuid':libid,'settings_valid':True,'format_paths_valid':True,'import_batches':len(imports),'bulk_batches':len(bulk),'activity_records':len(records),'recovery_records':len(recoveries['records']),'valid_resume_records':len(progress),'library_references_valid':True,'synthetic_recovery_restart_review_without_auto_write':True}))
