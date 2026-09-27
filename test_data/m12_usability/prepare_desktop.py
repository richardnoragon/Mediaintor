"""Run using the installed M12 candidate with the Hub closed."""
import sys,json,sqlite3,hashlib,zipfile
from pathlib import Path
from uuid import uuid4
base=Path.home()/'.local/share/mediainator-install'
release=(base/'current').resolve()
assert release.name=='0.1.0a1-16e57f586750466b'
sys.path.insert(0,str(release))
from mediainator.settings import SettingsStore
from mediainator.recovery import RecoveryStore
from mediainator.metadata import run_request
from mediainator.snapshot import Snapshot
config=Path.home()/'.config/Media-inator/Media-inator'
data=Path.home()/'.local/share/Media-inator/Media-inator'
settings=SettingsStore(config/'settings.json').load()
library=Path('/data/library')
assert settings['library']==str(library)
before=hashlib.sha256((library/'metadata.db').read_bytes()).hexdigest()
with sqlite3.connect((library/'metadata.db').as_uri()+'?mode=ro',uri=True) as db:
 book,uid,title=db.execute('select id,uuid,title from books order by id limit 1').fetchone()
snapshot=Snapshot(library).create()
try:
 current=run_request(snapshot.root,dict(action='read',book=book,uuid=uid),config/'metadata-recovery')
finally:snapshot.close()
baseline=current['current'];tag='M12 Recovery Acceptance'
assert tag not in baseline['tags']
store=RecoveryStore(data,settings['profile_id'],settings['device_id'])
assert not any(r['payload']['operation_id']=='m12-final-acceptance' for r in store.discover()['records']),'Fixture already exists; do not duplicate'
payload=store.capture(current['library_uuid'],uid,baseline,dict(baseline,tags=baseline['tags']+[tag]),1,'m12-final-acceptance')
store.preserve(payload)
source=Path('/data/import-sources/M12 Final Acceptance.epub');assert not source.exists()
with zipfile.ZipFile(source,'w') as z:
 z.writestr('mimetype','application/epub+zip')
 z.writestr('META-INF/container.xml','<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>')
 z.writestr('content.opf',f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="id"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="id">urn:uuid:{uuid4()}</dc:identifier><dc:title>M12 Final Acceptance</dc:title><dc:creator>Media-inator Test Fixture</dc:creator><dc:language>en</dc:language></metadata><manifest><item id="text" href="text.xhtml" media-type="application/xhtml+xml"/><item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/></manifest><spine toc="ncx"><itemref idref="text"/></spine></package>''')
 z.writestr('text.xhtml','<html xmlns="http://www.w3.org/1999/xhtml"><head><title>M12 Final Acceptance</title></head><body><h1>M12 Final Acceptance</h1><p>This original test document verifies copy-only import and reading in the isolated M12 installation.</p></body></html>')
 z.writestr('toc.ncx','<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1"><head/><docTitle><text>M12 Final Acceptance</text></docTitle><navMap><navPoint id="start" playOrder="1"><navLabel><text>Acceptance</text></navLabel><content src="text.xhtml"/></navPoint></navMap></ncx>')
assert hashlib.sha256((library/'metadata.db').read_bytes()).hexdigest()==before
print(json.dumps(dict(build=release.name,import_source=str(source),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),recovery_book=title,recovery_book_uuid=uid,recovery_id=payload['id'],recovery_tag=tag,library_database_unchanged=True,recovery='Synthetic unsaved tag only; not applied to library',desktop_acceptance='pending')))
