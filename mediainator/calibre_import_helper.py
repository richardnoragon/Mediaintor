"""Calibre-bound import capabilities. Invoked only by the explicit import workflow."""
import sys
# Calibre starts a fresh interpreter; keep the installed release manifest unchanged.
sys.dont_write_bytecode = True
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import json, hashlib, uuid, zipfile, struct, tempfile, shutil
import xml.etree.ElementTree as ET
from mediainator.import_store import fingerprint, atomic_json, FINAL


def parse(path):
    from calibre.ebooks.metadata.meta import get_metadata
    path=Path(path)
    if path.is_symlink() or not path.is_file():raise ValueError('Source must be a readable local file, not a symbolic link.')
    fmt=path.suffix[1:].upper()
    if fmt not in {'EPUB','MOBI','PDF'}:raise ValueError('Unsupported format; select EPUB, MOBI or PDF.')
    before_hash=fingerprint(path)
    missing=[]
    if fmt=='EPUB':
        with zipfile.ZipFile(path) as archive:
            if archive.read('mimetype').strip()!=b'application/epub+zip':raise ValueError('Invalid EPUB mimetype.')
            container=ET.fromstring(archive.read('META-INF/container.xml'))
            opf=next(e.attrib['full-path'] for e in container.iter() if e.tag.endswith('rootfile'))
            tree=ET.fromstring(archive.read(opf))
            if archive.testzip():raise ValueError('Corrupt EPUB archive.')
            for field,tag in [('title','title'),('authors','creator')]:
                if not any((e.text or '').strip() for e in tree.iter('{http://purl.org/dc/elements/1.1/}'+tag)):missing.append(field)
    elif fmt=='PDF':
        from calibre.utils.podofo import get_podofo
        doc=get_podofo().PDFDoc();doc.open(str(path))
        if not doc.page_count():raise ValueError('PDF has no readable pages.')
    else:
        from calibre.ebooks.mobi.reader.headers import MetadataHeader
        with path.open('rb') as stream:MetadataHeader(stream,log=None)
    with path.open('rb') as stream:mi=get_metadata(stream,fmt.lower())
    title=mi.title or ''
    authors=list(mi.authors or [])
    if not title.strip() or title in {path.stem,'Unknown'}:
        if 'title' not in missing:missing.append('title')
    if not authors or all(a.strip().casefold()=='unknown' for a in authors):
        if 'authors' not in missing:missing.append('authors')
    if 'title' in missing:title=path.stem
    if 'authors' in missing:authors=['Unknown']
    if fingerprint(path)!=before_hash:raise ValueError('Source changed during metadata extraction; preview again.')
    return dict(source=str(path),hash=before_hash,format=fmt,title=title,authors=authors,missing=missing)


def execute(request):
    from mediainator.compatibility import require_helper_version
    require_helper_version()
    from calibre.constants import __version__
    from calibre.utils.lock import singleinstance
    from calibre.db.legacy import LibraryDatabase
    from calibre.ebooks.metadata.book.base import Metadata
    if __version__!='9.2.1':raise ValueError('Import adapter requires validated Calibre 9.2.1.')
    if not singleinstance('db'):raise RuntimeError('Waiting for library access. Close Calibre and readers, then Retry.')
    root=Path(request['library']).resolve(strict=True)
    if not (root/'metadata.db').is_file() or any(p.is_symlink() for p in root.rglob('*')):raise ValueError('A local library without symlinks is required.')
    db=LibraryDatabase(str(root));api=db.new_api
    try:
        library_uuid=api.library_id
        if request.get('library_uuid') and library_uuid!=request['library_uuid']:raise ValueError('Library identity changed; build a new preview.')
        records=[dict(id=i,uuid=api.field_for('uuid',i),title=api.field_for('title',i),authors=list(api.field_for('authors',i)),formats=list(api.formats(i))) for i in api.all_book_ids()]
        hashes={}
        for book in records:
            for fmt in book['formats']:
                path=api.format_abspath(book['id'],fmt)
                if not path:raise ValueError('Existing library format is missing; repair it before importing.')
                hashes.setdefault(fingerprint(path),[]).append((book['id'],fmt))
        def token():
            return hashlib.sha256(json.dumps({'records':sorted(records,key=lambda r:r['id']),'hashes':sorted(hashes)},sort_keys=True).encode()).hexdigest()
        catalog_token=token()
        if request['action']=='preview':
            items=[];seen=set()
            for source in request['sources']:
                item=dict(source=source,state='pending',operation_uuid=str(uuid.uuid4()),action='new',destination=None,warning='')
                try:
                    item.update(parse(source))
                    if item['hash'] in hashes or item['hash'] in seen:
                        item.update(state='duplicate',warning='Identical file contents: skipped.')
                    else:
                        from difflib import SequenceMatcher
                        normalize=lambda title: ''.join(c for c in title.casefold() if c.isalnum())
                        similar=[r['id'] for r in records if SequenceMatcher(None,normalize(r['title']),normalize(item['title'])).ratio()>=0.85]
                        item['similar']=similar
                        item['warning']='; '.join(filter(None,['Similar existing title: choose an action.' if similar else '', 'Missing metadata: '+', '.join(item['missing']) if item['missing'] else '']))
                    seen.add(item['hash'])
                except Exception as exc:item.update(state='invalid',warning=str(exc))
                items.append(item)
            return dict(library_uuid=library_uuid,catalog_token=catalog_token,items=items,records=records)
        path=Path(request['journal']);batch=json.loads(path.read_text())
        if batch['library_uuid']!=library_uuid or Path(batch['library']).resolve()!=root:raise ValueError('Recovery journal belongs to another library.')
        item=batch['items'][request['index']]
        if item['state'] in FINAL:return {'item':item}
        # Reconcile commit-before-ack and a partial metadata-only record by stable operation identity.
        wanted=item.get('destination_uuid') or item['operation_uuid']
        matches=[r for r in records if r['uuid']==wanted]
        target=matches[0]['id'] if len(matches)==1 else None
        if len(matches)>1:raise ValueError('Ambiguous record identity; manual review required.')
        if target is not None and item.get('format') in api.formats(target):
            if fingerprint(api.format_abspath(target,item['format']))==item.get('hash'):
                item.update(state='complete',destination_uuid=wanted,destination=target,warning='Verified existing completed import.')
                atomic_json(path,batch);return {'item':item}
            item.update(state='failed',warning='Destination format is occupied by different contents. No overwrite.');atomic_json(path,batch);return {'item':item}
        if request['action']=='reconcile':return {'item':item}
        if batch.get('catalog_token') != catalog_token:raise ValueError('Library changed after preview. Retry to review a fresh plan before importing.')
        if item['state']=='invalid':raise ValueError('Invalid input must be removed from the batch or selected again.')
        if fingerprint(item['source'])!=item['hash']:raise ValueError('Source changed after preview. Build a new preview before importing.')
        if item['action']=='attach':
            if target is None:raise ValueError('Selected destination no longer exists.')
        elif item['hash'] in hashes:
            item.update(state='duplicate',warning='Identical contents now exist in the library; skipped.');atomic_json(path,batch);return {'item':item}
        if target is not None:item.update(destination=target,destination_uuid=wanted)
        item['state']='in-flight';atomic_json(path,batch)
        # Stage bytes before mutation so later source changes cannot alter the committed payload.
        with tempfile.TemporaryDirectory(prefix='mediainator-import-stage-') as stage:
            staged=Path(stage)/Path(item['source']).name;shutil.copyfile(item['source'],staged)
            if fingerprint(staged)!=item['hash']:raise ValueError('Source changed while staging; no format written.')
            parse(staged)
            if target is None:
                from calibre.ebooks.metadata.meta import get_metadata
                with staged.open('rb') as stream:mi=get_metadata(stream,item['format'].lower())
                mi.title=item['title'];mi.authors=item['authors'];mi.uuid=item['operation_uuid']
                target=api.create_book_entry(mi,add_duplicates=True,apply_import_tags=False,preserve_uuid=True)
                item.update(destination=target,destination_uuid=api.field_for('uuid',target));atomic_json(path,batch)
            added=api.add_format(target,item['format'],str(staged),replace=False,run_hooks=False)
            if not added:raise ValueError('Destination format became occupied. No overwrite.')
            if fingerprint(api.format_abspath(target,item['format']))!=item['hash']:raise ValueError('Imported file contents could not be verified.')
        # Refresh the batch fingerprint for our own verified mutation, preserving detection of later external changes.
        records=[dict(id=i,uuid=api.field_for('uuid',i),title=api.field_for('title',i),authors=list(api.field_for('authors',i)),formats=list(api.formats(i))) for i in api.all_book_ids()]
        hashes={}
        for record in records:
            for fmt in record['formats']:hashes[fingerprint(api.format_abspath(record['id'],fmt))]=True
        batch['catalog_token']=token()
        item.update(state='complete',warning='Imported and verified.');atomic_json(path,batch)
        return {'item':item}
    finally:db.close()


if __name__=='__main__':
    inp,out=map(Path,sys.argv[1:3])
    try:result=execute(json.loads(inp.read_text()))
    except Exception as exc:result={'error':str(exc)}
    atomic_json(out,result)
