"""Run with installed M13 interpreter; create preview/recovery fixtures, never book writes."""
import sys,json,sqlite3,hashlib,zipfile
from pathlib import Path
base=Path.home()/'.local/share/mediainator-install';release=(base/'current').resolve()
assert release.name=='0.1.0a1-ffbaa166eaebf2fe'
sys.path.insert(0,str(release))
from mediainator.recovery import RecoveryStore
from mediainator.metadata_rules import FIELDS
cfg=Path.home()/'.config/Media-inator/Media-inator';settings=json.loads((cfg/'settings.json').read_text())
library=Path('/data/library');assert settings['library']==str(library)
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=digest(library/'metadata.db')
with sqlite3.connect((library/'metadata.db').as_uri()+'?mode=ro',uri=True) as db:
 db.execute('BEGIN')
 bid,uid,title=db.execute('select id,uuid,title from books where uuid=?',('d145f3a1-2382-4fe7-bc40-26208145311c',)).fetchone()
 tags=[r[0] for r in db.execute('select t.name from tags t join books_tags_link l on l.tag=t.id where l.book=?',(bid,))]
 libid=db.execute('select uuid from library_id').fetchone()[0]
store=RecoveryStore(Path.home()/'.local/share/Media-inator/Media-inator',settings['profile_id'],settings['device_id'])
operation='m13-local-discard-check';tag='M13 Local Discard Check'
existing=[r for r in store.discover()['records'] if r['payload']['operation_id']==operation]
assert tag not in tags
if existing:
 assert len(existing)==1 and existing[0]['state']=='unresolved'
 payload=existing[0]['payload']
else:
 baseline=dict.fromkeys(FIELDS);baseline['tags']=tags
 payload=store.capture(libid,uid,baseline,dict(baseline,tags=tags+[tag]),1,operation)
 store.preserve(payload)
source=Path('/data/import-sources/M13 Final Acceptance.epub');target=source.with_name('M13 Action Feedback.epub');sourcehash=digest(source)
if not target.exists():
 with zipfile.ZipFile(source) as src,zipfile.ZipFile(target,'x') as dst:
  for entry in src.infolist():
   content=src.read(entry.filename)
   if entry.filename=='text.xhtml':content=content.replace(b'</body>',b'<p>M13 action feedback preview fixture; do not import.</p></body>')
   dst.writestr(entry,content)
assert digest(source)==sourcehash and digest(target)!=sourcehash
assert digest(library/'metadata.db')==before
print(json.dumps(dict(build=release.name,source=str(target),source_sha256=digest(target),original_source_sha256=sourcehash,recovery_id=payload['id'],recovery_book=title,recovery_tag=tag,recovery_operation=operation,library_database_unchanged=True,usage='Preview action feedback without import; discard local recovered edits then separately discard preserved test draft after review.'),indent=2))
