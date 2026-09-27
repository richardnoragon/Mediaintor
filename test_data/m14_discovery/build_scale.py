"""Calibre 9.2.1 fixture builder; run only in the disposable /fixture mount."""
import io,json,hashlib,sqlite3,time,uuid,zipfile
from pathlib import Path
from xml.sax.saxutils import escape
from calibre.library import db as Database
from calibre.ebooks.metadata.book.base import Metadata
root=Path('/fixture');library=root/'library'
assert not (library/'metadata.db').exists(), 'Existing fixture retained'
library.mkdir(exist_ok=True)
start=time.monotonic();db=Database(str(library));api=db.new_api
manifest=json.loads(Path('/scripts/test_data/free_ebooks_100/manifest.json').read_text())
source=sqlite3.connect('file:/seed/metadata.db?mode=ro',uri=True)
records=[];payloads={}
def digest(b):return hashlib.sha256(b).hexdigest()
def epub(number,title,author):
 out=io.BytesIO()
 with zipfile.ZipFile(out,'w') as z:
  z.writestr('mimetype','application/epub+zip')
  z.writestr('META-INF/container.xml','<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>')
  z.writestr('content.opf',f'<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="id"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="id">m14-{number}</dc:identifier><dc:title>{escape(title)}</dc:title><dc:creator>{escape(author)}</dc:creator><dc:language>en</dc:language></metadata><manifest><item id="text" href="text.xhtml" media-type="application/xhtml+xml"/><item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/></manifest><spine toc="ncx"><itemref idref="text"/></spine></package>')
  z.writestr('toc.ncx',f'<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1"><head/><docTitle><text>{escape(title)}</text></docTitle><navMap><navPoint id="start" playOrder="1"><navLabel><text>Start</text></navLabel><content src="text.xhtml"/></navPoint></navMap></ncx>')
  z.writestr('text.xhtml','<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Disposable fixture</title></head><body><h1>'+escape(title)+'</h1>'+''.join(f'<p>Original generated test text for fixture {number}, paragraph {j}. No real publication is represented.</p>' for j in range(160))+'</body></html>')
 return out.getvalue()
from qt.core import QImage,QColor,QBuffer,QByteArray,QIODevice
im=QImage(120,180,QImage.Format.Format_RGB32);im.fill(QColor('#466b88'));arr=QByteArray();buf=QBuffer(arr);buf.open(QIODevice.OpenModeFlag.WriteOnly);im.save(buf,'JPEG');cover=bytes(arr)
for n in range(1,10001):
 if n<=100:
  item=manifest[n-1];mi=Metadata(item['title'],item['authors']);mi.tags=[item['genre'],'m14-free-sample'];mi.set_identifier('gutenberg',item['gutenberg_id'])
  row=source.execute('select b.id,b.path from books b join identifiers i on i.book=b.id where i.type=? and i.val=?',('gutenberg',item['gutenberg_id'])).fetchone();assert row,item['title']
  fm={}
  for fmt,name in source.execute('select format,name from data where book=?',(row[0],)):
   path=Path('/seed')/row[1]/(name+'.'+fmt.lower());content=path.read_bytes()
   assert any(f['sha256']==digest(content) for f in item['files']), str(path)
   fm[fmt]=io.BytesIO(content)
  origin=item['source']
 else:
  # 100 exact pairs, 100 metadata-only similar pairs; other titles unique.
  base=n-1 if 102<=n<=500 and n%2==0 else n
  title=f'M14 Fixture {base:05d}';author=f'Generated Author {base%200:03d}'
  if n%37==0:title='Unknown'
  if n%41==0:author='Unknown'
  mi=Metadata(title,[author]);mi.tags=[f'Tag {n%40:02d}',f'Group {n%7}', 'm14-generated']
  mi.series=f'Series {n%80:02d}' if n%5 else None;mi.series_index=float(n%12+1)
  content=payloads[n-1] if 102<=n<=300 and n%2==0 else epub(n,title,author)
  if n<=300:payloads[n]=content
  fm={'EPUB':io.BytesIO(content)};origin='original generated fixture'
 mi.uuid=str(uuid.uuid5(uuid.NAMESPACE_URL,f'mediainator:m14:scale:v1:{n}'))
 ids,duplicates=api.add_books([(mi,fm)],add_duplicates=True,preserve_uuid=True,run_hooks=False);assert len(ids)==1
 bid=ids[0]
 if n%4:api.set_cover({bid:cover})
 records.append(dict(n=n,id=bid,uuid=mi.uuid,title=mi.title,authors=mi.authors,tags=mi.tags,series=mi.series or '',cover=bool(n%4),formats=list(fm),origin=origin,reading_status=['Unknown','Unread','Reading','Finished'][(n//3)%4],manual_review=n%53==0,import_warning=n%59==0,warning_acknowledged=n%118==0,missing_title_provenance=n>100 and n%37==0,missing_author=not mi.authors or any(a.strip().casefold() in ('unknown','unknown author','') for a in mi.authors)))
 if n%500==0:print(f'{n}/10000 created; {time.monotonic()-start:.1f}s',flush=True)
source.close();db.close()
(library/'.mediainator-disposable.json').write_text(json.dumps({'purpose':'mediainator-disposable-test','root':str(library)}))
(root/'oracle.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
files=[p for p in library.rglob('*') if p.is_file()]
report=dict(books=len(records),free_samples=100,generated=9900,creation_seconds=time.monotonic()-start,file_count=len(files),bytes=sum(p.stat().st_size for p in files),oracle_sha256=digest((root/'oracle.json').read_bytes()),limitations='Synthetic reading/review flags live in oracle only; baseline application reports Unknown. Generated files are small text-heavy EPUBs, not 10,000 distinct publications. API may normalize missing metadata; oracle retains intended provenance.')
(root/'fixture.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
