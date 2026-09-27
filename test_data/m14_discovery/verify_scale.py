"""Read-only independent fixture audit, no application query implementation."""
import json,sqlite3,hashlib,collections,unicodedata
from pathlib import Path
root=Path(__file__).resolve().parent;fixture=root/'scale';lib=fixture/'library'
records=json.loads((fixture/'oracle.json').read_text());assert len(records)==10000
byid={r['id']:r for r in records};groups=collections.defaultdict(list)
with sqlite3.connect((lib/'metadata.db').as_uri()+'?mode=ro',uri=True) as db:
 assert db.execute('pragma quick_check').fetchone()[0]=='ok'
 assert db.execute('select count(*) from books').fetchone()[0]==10000
 rows=db.execute('select b.id,b.uuid,b.title,b.path,d.format,d.name from books b join data d on d.book=b.id').fetchall()
 for bid,uid,title,path,fmt,name in rows:
  assert uid==byid[bid]['uuid'] and title==byid[bid]['title']
  f=lib/path/(name+'.'+fmt.lower());digest=hashlib.sha256(f.read_bytes()).hexdigest()
  groups[(fmt,digest)].append(uid)
 duplicates=[dict(format=fmt,sha256=digest,uuids=sorted(ids)) for (fmt,digest),ids in groups.items() if len(set(ids))>1]
 cover_count=sum((lib/p/'cover.jpg').is_file() for p, in db.execute('select path from books'))
 assert cover_count==7500
normalize=lambda s:' '.join(unicodedata.normalize('NFKC',s).casefold().split())
similar=collections.defaultdict(list)
for r in records:
 if r['missing_title_provenance'] or r['missing_author']:continue
 similar[(normalize(r['title']),tuple(normalize(a) for a in r['authors']))].append(r['uuid'])
# Approved future M14 cases; statuses/review flags are supplied by the test oracle,
# not asserted to exist in the installed M13 baseline.
expected={
 'unread_series_missing_cover':[r['uuid'] for r in records if r['reading_status']=='Unread' and r['series']=='Series 04' and not r['cover']],
 'missing_author_or_title':[r['uuid'] for r in records if r['missing_author'] or r['missing_title_provenance']],
 'tags_all':[r['uuid'] for r in records if {'Tag 03','Group 3'}<=set(r['tags'])],
 'tags_any':[r['uuid'] for r in records if {'Tag 03','Group 3'}&set(r['tags'])],
 'review_default':[r['uuid'] for r in records if r['missing_author'] or r['missing_title_provenance'] or not r['cover'] or r['manual_review'] or (r['import_warning'] and not r['warning_acknowledged'])],
}
report=dict(books=10000,formats=len(rows),covers=cover_count,missing_covers=10000-cover_count,exact_duplicate_groups=duplicates,similar_metadata_groups=[v for v in similar.values() if len(v)>1],expected=expected,generated_epub_note='Logical metadata/distributions are reproducible; ZIP creation timestamps and Calibre timestamps make byte-identical regeneration unsupported. This artifact has recorded hashes.',status_note='Known reading states and workflow flags are oracle overlays for future M14 tests; current installed loader reports Unknown.')
(root/'scale_verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(books=10000,formats=len(rows),covers=cover_count,exact_groups=len(duplicates),similar_groups=len(report['similar_metadata_groups']),expected_counts={k:len(v) for k,v in expected.items()}),indent=2))
