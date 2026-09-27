"""Validate copied state with the installed package; never write catalog metadata."""
import sys,json,sqlite3,hashlib
from pathlib import Path
base=Path.home()/'.local/share/mediainator-install';release=(base/'current').resolve()
assert release.name=='0.1.0a1-a3a4679f39f4c255'
sys.path.insert(0,str(release))
from mediainator.settings import SettingsStore
from mediainator.workspaces import WorkspaceStore
from mediainator.import_store import ImportStore
from mediainator.bulk import BulkStore
from mediainator.activity import ActivityStore
from mediainator.recovery import RecoveryStore
from mediainator.progress import read_progress
config=Path.home()/'.config/Media-inator/Media-inator';data=Path.home()/'.local/share/Media-inator/Media-inator';library=Path('/data/library')
s=SettingsStore(config/'settings.json').load();assert s['library']==str(library)
raw=json.loads((config/'workspaces.json').read_text())
w=WorkspaceStore(config/'workspaces.json',s['profile_id'],s['device_id'],raw['last_session']['snapshot']).load()
with sqlite3.connect((library/'metadata.db').as_uri()+'?mode=ro',uri=True) as db:
 assert db.execute('pragma integrity_check').fetchone()[0]=='ok'
 libid=db.execute('select uuid from library_id').fetchone()[0]
 books=db.execute('select id,uuid,title from books').fetchall();ids={uid for _,uid,_ in books}
 formats=db.execute('select b.path,d.name,d.format from books b join data d on b.id=d.book').fetchall()
 covers=db.execute('select path from books where has_cover=1').fetchall()
 cleanup_books=[{'id':bid,'title':title} for bid,uid,title in books if any(x in title.lower() for x in ['m10','m9','acceptance','test','externally changed'])]
 tags=[v for v, in db.execute('select name from tags') if any(x in v.lower() for x in ['m10','m9','acceptance','test'])]
assert all((library/p/(n+'.'+f.lower())).is_file() for p,n,f in formats)
assert all((library/p/'cover.jpg').is_file() for p, in covers)
for entry in [w['last_session'],*w['named'].values()]:
 selection=entry['snapshot']['selection']
 if selection:assert selection['library_uuid']==libid and selection['book_uuid'] in ids
imports=ImportStore(config/'imports',library).batches();bulk=BulkStore(config/'bulk',library).batches()
assert all(b['library_uuid']==libid for _,b in imports)
assert all(b['library_uuid']==libid for b in bulk)
activity=ActivityStore(data/'Activity',s['profile_id'],s['device_id']).records()
recoveries=RecoveryStore(data,s['profile_id'],s['device_id']).discover();assert not recoveries['errors']
for r in recoveries['records']:
 assert r['payload']['identity']['library_uuid']==libid
 if r['state']=='unresolved':assert r['payload']['identity']['book_uuid'] in ids
progress=[read_progress(Path.home()/'.config/calibre/viewer/annots',library/p/(n+'.'+f.lower())) for p,n,f in formats]
print(json.dumps(dict(build=release.name,library_uuid=libid,profile_id=s['profile_id'],device_id=s['device_id'],books=len(books),formats=len(formats),covers=len(covers),named_workspaces=len(w['named']),startup=w['startup'],valid_resume_records=sum(bool(p.position) for p in progress),import_batches=len(imports),bulk_batches=len(bulk),activity_records=len(activity),recovery_records=len(recoveries['records']),unresolved_recovery=sum(r['state']=='unresolved' for r in recoveries['records']),identity_references_valid=True,sqlite_integrity='ok',cleanup_review=dict(books=cleanup_books,tags=tags,workspaces=[e['name'] for e in w['named'].values()],policy='Candidates only; retain every item until specifically approved.'))))
