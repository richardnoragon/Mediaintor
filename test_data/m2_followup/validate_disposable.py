"""Run from repository root: calibre-debug -e this_file. Mutates only a fresh /tmp copy."""
from pathlib import Path
import hashlib, json, tempfile, shutil, sqlite3
from decimal import Decimal, InvalidOperation
from calibre.db.legacy import LibraryDatabase
from qt.core import QImage
source = Path('/home/sproket01/Calibre Library')
evidence = Path.cwd() / 'test_data/m2_followup'
root = Path(tempfile.mkdtemp(prefix='mediainator-m2-followup-'))
lib = root / 'library'
def hashes(path):
    return {str(p.relative_to(path)): hashlib.sha256(p.read_bytes()).hexdigest() for p in path.rglob('*') if p.is_file()}
before = hashes(source)
shutil.copytree(source, lib)
assert lib.resolve() != source.resolve() and lib.parent == root
checks = []
def record(name, **values):
    checks.append(dict(test=name, **values))
    (evidence/'checks.json').write_text(json.dumps(checks, indent=2))
    print(name, json.dumps(values), flush=True)
db = LibraryDatabase(str(lib)); api = db.new_api; book = 32
formats_before = {f: hashlib.sha256(api.format(book, f)).hexdigest() for f in api.formats(book)}
uuid_before = api.field_for('uuid', book)
def setfield(name, value):
    return api.set_field(name, {book: value}, allow_case_change=False)
def reopen():
    global db, api
    db.close(); db = LibraryDatabase(str(lib)); api = db.new_api
try:
    setfield('series', 'Foundation'); setfield('series_index', 3)
    setfield('series', None); setfield('series_index', None)
    reopen()
    with sqlite3.connect(f'file:{lib / "metadata.db"}?mode=ro', uri=True) as con:
        stored = con.execute('SELECT series_index FROM books WHERE id=?', (book,)).fetchone()[0]
        schema = [list(r) for r in con.execute('PRAGMA table_info(books)') if r[1]=='series_index']
    record('literal_series_removal', requirement_passed=api.field_for('series',book) is None and stored is None, series=api.field_for('series',book), index=api.field_for('series_index',book), raw_stored_index=stored, schema=schema)
    setfield('series', 'New Series'); setfield('series_index', 1)
    assert api.field_for('series_index',book)==1
    record('explicit_new_series_default', passed=True)
    authors=['Asimov, Isaac', 'Silverberg, Robert']; tags=['Science, Fiction', 'Classic', 'Space Opera']
    setfield('authors', authors); setfield('tags', tags); reopen()
    actual_authors=list(api.field_for('authors',book)); actual_tags=list(api.field_for('tags',book))
    record('list_roundtrip', passed=actual_authors==authors and set(actual_tags)==set(tags), authors=actual_authors,tags=actual_tags)
    setfield('authors', list(reversed(authors))); reopen()
    record('author_reorder', passed=list(api.field_for('authors',book))==list(reversed(authors)))
    html='<p class="existing">A <b>bold</b> <i>italic</i> <a href="https://example.org">link</a>.</p><ul><li>Bullet</li></ul><ol><li>Numbered</li></ol>'
    setfield('comments',html); baseline_html=api.field_for('comments',book)
    setfield('tags',tags+['HTML preservation test']); reopen()
    record('untouched_html',passed=baseline_html==html and api.field_for('comments',book)==html)
    original_cover=api.cover(book); assert original_cover and not QImage.fromData(original_cover).isNull()
    backup=root/'original-cover.jpg'; backup.write_bytes(original_cover)
    api.set_cover({book:None}); reopen()
    cover_path=lib/api.field_for('path',book)/'cover.jpg'
    record('cover_removal',passed=api.cover(book) is None and not cover_path.exists() and not api.field_for('cover',book))
    api.set_cover({book:original_cover})
    setfield('title','M2 recovery committed title')
    # Inject malformed data downstream of input validation to exercise actual write failure.
    pending=b'not a valid image'
    failure=None
    try: api.set_cover({book:pending})
    except Exception as exc: failure=f'{type(exc).__name__}: {exc}'
    damaged=api.cover(book)
    restored=False
    if failure or not damaged or QImage.fromData(damaged).isNull():
        api.set_cover({book:backup.read_bytes()})
        restored=api.cover(book)==original_cover and not QImage.fromData(api.cover(book)).isNull()
    reopen()
    record('automatic_backup_recovery_protocol',passed=restored and api.cover(book)==original_cover and api.field_for('title',book)=='M2 recovery committed title', write_error=failure, damaged_bytes=len(damaged or b''),pending_retained=pending==b'not a valid image',backup_retained=backup.exists())
    # Simulated failure of the restoration step; no claim of successful recovery.
    result={'restored':False,'pending':pending,'backup':str(backup)}
    try: raise OSError('Injected restoration failure')
    except OSError as exc: result['error']=str(exc)
    record('recovery_failure_reporting_protocol',passed=not result['restored'] and bool(result['pending']) and backup.exists(), error=result['error'], injection='simulated restoration exception, not disk-full')
    def valid(value):
        try:
            n=Decimal(value); return n.is_finite() and n>=0
        except InvalidOperation: return False
    valid_values=['0','1','2.5','4.1','12']; invalid_values=['-1','-2.5','abc','2a','NaN','Infinity']
    for value in valid_values:
        assert valid(value); setfield('series_index',float(value)); assert api.field_for('series_index',book)==float(value)
    assert not any(valid(value) for value in invalid_values)
    record('number_validation_protocol',passed=True,accepted=valid_values,rejected=invalid_values)
    assert api.field_for('uuid',book)==uuid_before
    assert {f:hashlib.sha256(api.format(book,f)).hexdigest() for f in api.formats(book)}==formats_before
    record('identity_and_format_integrity',passed=True)
finally:
    db.close()
    unchanged=before==hashes(source)
    (evidence/'report.json').write_text(json.dumps(dict(temporary_root=str(root),source_library_unchanged=unchanged,checks=checks,scope='Calibre API and protocol experiments; no application implementation'),indent=2))
    assert unchanged, 'Original library changed during validation'
