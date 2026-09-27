"""Read-only closure checks; never closes the running desktop or changes user data."""
from pathlib import Path
import json,hashlib,sqlite3,os
root=Path(__file__).resolve().parents[2];folder=root/'test_data/m11_promotion'
r=json.loads((folder/'promotion_results.json').read_text());active=Path(r['root'])/'active';config=active/'home/.config/Media-inator/Media-inator';data=active/'home/.local/share/Media-inator/Media-inator';lib=active/'library'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
archive=root/'dist/m10/mediainator-0.1.0a1-ubuntu26.04-x86_64.tar.gz';assert sha(archive)==r['sha256']
base=active/'home/.local/share/mediainator-install';installed=json.loads((base/'installation.json').read_text());assert installed['current']==r['build'];release=(base/'current').resolve();assert release.name==r['build'];assert {str(p.relative_to(release)):sha(p) for p in release.rglob('*') if p.is_file()}==installed['releases'][r['build']]
w=json.loads((config/'workspaces.json').read_text());assert any(e['name']=='M11 Everyday' for e in w['named'].values())
batches=[json.loads(p.read_text()) for p in (config/'bulk').rglob('*.json')];original=next(b for b in batches if b['id']=='f6c4e359-326d-4332-854d-04cc03c23717');revert=next(b for b in batches if b.get('kind')=='revert' and b.get('original')==original['id']);assert all(i['state']=='complete' for i in original['items']+revert['items'])
with sqlite3.connect((lib/'metadata.db').resolve().as_uri()+'?mode=ro',uri=True) as db:
 assert db.execute('pragma quick_check').fetchone()[0]=='ok'
 def tags(book):return sorted(v for v, in db.execute('select t.name from tags t join books_tags_link l on l.tag=t.id where l.book=?',(book,)))
 for item in original['items']:assert tags(item['book'])==sorted(item['applied']['tags']['before'])
 assert 'M11 Verified' in tags(32)
 book=db.execute('select id,path from books where title=?',('M11 Acceptance',)).fetchone();assert book
 name=db.execute("select name from data where book=? and format='EPUB'",(book[0],)).fetchone()[0];assert (lib/book[1]/(name+'.epub')).is_file()
 recovery_book=db.execute('select id from books where uuid=?',('d145f3a1-2382-4fe7-bc40-26208145311c',)).fetchone()[0];assert 'M10 Recovery Acceptance' in tags(recovery_book)
 count=db.execute('select count(*) from books').fetchone()[0]
recoveries=[]
for p in (data/'Recovery').rglob('index.json'):recoveries.extend(json.loads(p.read_text()).get('records',{}).items())
assert dict(recoveries)['fd35c048-4292-42de-9269-4d316c6868e6']['state']=='recovered'
fixtures=json.loads((folder/'desktop_fixtures.json').read_text());assert sha(active/'import-sources/M11 Acceptance.epub')==fixtures['sha256']
# Compare accepted M10 against the verified source snapshot; no writes.
backup=json.loads((Path(r['source_backup'])/'manifest.json').read_text())['inventory'];source=Path(r['source'])/'active';mismatch=[]
for name,item in backup.items():
 p=source/name
 if 'sha256' in item and (not p.is_file() or sha(p)!=item['sha256']):mismatch.append(name)
 if 'link' in item and (not p.is_symlink() or os.readlink(p)!=item['link']):mismatch.append(name)
assert not mismatch,mismatch
result=dict(build=r['build'],archive_sha256=r['sha256'],package_inventory_valid=True,books=count,named_workspace_persisted=True,import_epub_persisted=True,import_source_unchanged=True,metadata_tag_verified_on='The Time Machine',bulk_batch=original['id'],revert_batch=revert['id'],bulk_revert_complete=True,original_tags_restored=True,recovery_state='recovered',recovery_tag_persisted=True,unresolved_recovery=sum(v['state']=='unresolved' for _,v in recoveries),m10_source_files_match_promotion_backup=True,scope='Read-only final checks while Hub may remain open; backup/restore evidence comes from earlier closed snapshots')
(folder/'final_integrity.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
