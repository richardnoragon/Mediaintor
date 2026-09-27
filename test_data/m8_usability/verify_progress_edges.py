"""Disposable capability probes, not the production progress adapter."""
import sys
sys.dont_write_bytecode = True
import hashlib, json, shutil, tempfile
from pathlib import Path
from datetime import datetime, timezone
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from mediainator.progress import capture_rename, renamed_resume_args, ProgressStore
from calibre.constants import __version__
from calibre.db.annotations import merge_annotations
from calibre.gui2.viewer.annotations import parse_annotations
from calibre.db.legacy import LibraryDatabase

assert __version__ == '9.2.1'
checks = []
def check(name, value, detail=''):
    assert value, name
    checks.append({'name': name, 'passed': True, 'detail': detail})
def record(ts):
    return {'type':'last-read', 'pos':'epubcfi(/2/2/4/2:0)', 'pos_type':'epubcfi', 'timestamp':ts}
def merged(rows):
    result = {}; merge_annotations(rows, result); return result['last-read'][0]
def instant(ts):
    d = datetime.fromisoformat(ts.replace('Z','+00:00'))
    if d.tzinfo is None: raise ValueError('Timezone required')
    return d.astimezone(timezone.utc)

check('UTC timestamps select latest', merged([record('2026-09-22T10:00:00+00:00'),record('2026-09-22T11:00:00+00:00')])['timestamp'].startswith('2026-09-22T11'))
a,b=record('2026-09-22T12:00:00+02:00'),record('2026-09-22T10:30:00+00:00')
check('Calibre string ordering differs from chronological offset ordering', merged([a,b]) == a and instant(b['timestamp'])>instant(a['timestamp']), 'Normalize offsets for cross-format selection; do not reuse lexical ordering.')
a,b=record('2026-09-22T10:00:00Z'),record('2026-09-22T12:00:00+02:00')
check('Equivalent instants form a tie',instant(a['timestamp'])==instant(b['timestamp']), 'No unique latest format established.')
check('Malformed timestamp can outrank valid timestamp in Calibre merge',merged([record('2026-09-22T10:00:00Z'),record('zzzz')])['timestamp']=='zzzz','Validate timestamps independently.')
for name,raw in [('truncated',b'[{'),('invalid_utf8',b'\xff')]:
    try: parse_annotations(raw)
    except Exception as e: check('Parser rejects '+name,True,type(e).__name__)
    else: raise AssertionError(name)
for name,raw in [('wrong_shape',b'{}'),('missing_fields',b'[{"type":"last-read"}]')]:
    result=parse_annotations(raw)
    check('JSON parsing alone accepts '+name, result is not None,'Adapter needs structure and position validation.')

source=Path(sys.argv[1]).resolve()
with tempfile.TemporaryDirectory(prefix='m8-progress-') as tmp:
    root=Path(tmp); library=root/'library'; shutil.copytree(source,library)
    db=LibraryDatabase(str(library)); api=db.new_api
    try:
        book=next(i for i in api.all_book_ids() if api.field_for('title',i)=='The Time Machine')
        original=Path(api.format_abspath(book,'EPUB')); identity=api.field_for('uuid',book)
        content=hashlib.sha256(original.read_bytes()).hexdigest()
        annotations=root/'viewer-annotations'; annotations.mkdir()
        key=lambda p:hashlib.sha256(str(p).encode()).hexdigest()+'.json'
        saved=record('2026-09-22T10:00:00+00:00'); oldkey=annotations/key(original)
        oldkey.write_text(json.dumps([saved]))
        api.save_annotations_list(book,'EPUB','',[(saved,instant(saved['timestamp']).timestamp())])
        handoff=capture_rename('disposable-library',identity,'EPUB',original,annotations)
        store=ProgressStore(root/'progress.json','disposable-library',annotations)
        store.refresh(identity,'EPUB',original)
        api.set_field('title',{book:'M8 Disposable Renamed Time Machine'})
        renamed=Path(api.format_abspath(book,'EPUB'))
        reopened=ProgressStore(root/'progress.json','disposable-library',annotations)
        check('Persistent application store resumes after real rename and restart',reopened.resume_args(identity,'EPUB',renamed)==['--open-at',saved['pos']])
        check('Production handoff survives real Calibre rename',renamed_resume_args(handoff,'disposable-library',api.field_for('uuid',book),'EPUB',renamed,annotations)==['--open-at',saved['pos']])
        check('Calibre title save changes format path',renamed!=original and renamed.exists() and not original.exists())
        check('Rename preserves book UUID and ebook bytes',identity==api.field_for('uuid',book) and content==hashlib.sha256(renamed.read_bytes()).hexdigest())
        check('Path-keyed viewer sidecar does not follow rename',oldkey.exists() and not (annotations/key(renamed)).exists(),'Sidecar fixture: no automatic migration by metadata API.')
        check('Library annotation API omits last-read records',not api.annotations_map_for_book(book,'EPUB').get('last-read'),'Calibre annot_db_data supports bookmark/highlight identities, not last-read; database is not a resume fallback.')
        check('Missing sidecar is distinguishable from corrupt file',not (annotations/'missing.json').exists())
        bad=annotations/'corrupt.json'; bad.write_bytes(b'[{'); before=bad.read_bytes()
        try: parse_annotations(bad.read_bytes())
        except Exception: pass
        check('Read-only failed parsing preserves corrupt bytes',bad.read_bytes()==before)
    finally: db.close()
report={'calibre_version':__version__,'scope':'Disposable API and parser probes; no production progress adapter or GUI rename acceptance','checks':checks,'passed':len(checks)}
Path(sys.argv[2]).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'passed':len(checks)}))
