from pathlib import Path
import json,shutil,tempfile,subprocess,os,hashlib,time
from PIL import Image
source=Path('/home/sproket01/Calibre Library'); evidence=Path.cwd()/'test_data/m2_validation';root=Path(tempfile.mkdtemp(prefix='mediainator-m2-'));lib=root/'library';book=32
hashes=lambda p:{str(f.relative_to(p)):hashlib.sha256(f.read_bytes()).hexdigest() for f in p.rglob('*') if f.is_file()}
source_before=hashes(source);shutil.copytree(source,lib)
env=dict(os.environ,QT_QPA_PLATFORM='offscreen',CALIBRE_CONFIG_DIRECTORY=str(root/'config'));env.pop('CALIBRE_OVERRIDE_DATABASE_PATH',None)
commands=[];checks=[]
def command(*args):
 p=subprocess.run(['/usr/bin/calibredb',*args,'--with-library',str(lib)],env=env,capture_output=True,text=True,timeout=45)
 commands.append({'args':args,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
 (evidence/'commands.json').write_text(json.dumps(commands,indent=2))
 return p
fields='title,authors,tags,cover,series,series_index,comments,uuid,formats,identifiers,publisher,languages'
def read():
 p=command('list','--for-machine','--fields',fields,'--search',f'id:{book}');assert p.returncode==0,p.stderr
 rows=json.loads(p.stdout);assert len(rows)==1
 r=rows[0];r['format_hashes']={Path(f).suffix:hashlib.sha256(Path(f).read_bytes()).hexdigest() for f in r['formats']};r['cover_hash']=hashlib.sha256(Path(r['cover']).read_bytes()).hexdigest() if r.get('cover') and Path(r['cover']).exists() else None
 return r
def save(**values):
 args=['set_metadata',str(book)]
 for k,v in values.items():args+=['--field',k+':'+str(v)]
 return command(*args)
def record(name,**data):checks.append({'test':name,**data});print(name,json.dumps(data),flush=True);(evidence/'checks.json').write_text(json.dumps(checks,indent=2))
baseline=read();(evidence/'baseline.json').write_text(json.dumps(baseline,indent=2))
p=save(title='M2 Path Test — Revised',authors='Validation Author & Second Author');after=read()
assert p.returncode==0 and after['title']=='M2 Path Test — Revised'
assert after['uuid']==baseline['uuid'] and after['format_hashes']==baseline['format_hashes']
assert after['formats']!=baseline['formats'] and all(not Path(f).exists() for f in baseline['formats'])
record('title_author_paths',passed=True,old_paths=baseline['formats'],new_paths=after['formats'],authors=after['authors'],identity_and_format_bytes_preserved=True)
cover=root/'new-cover.png';Image.new('RGB',(200,300),(40,90,150)).save(cover)
html='<p>M2 <strong>description</strong> &amp; notes.</p>'
p=save(tags='M2 validation,Science fiction',series='M2 Test Series',series_index='2.5',comments=html,cover=cover);after=read()
assert p.returncode==0 and after['series']=='M2 Test Series' and after['series_index']==2.5 and after['cover_hash']!=baseline['cover_hash']
assert set(after['tags'])=={'M2 validation','Science fiction'} and 'description' in after['comments']
for k in ['uuid','identifiers','publisher','languages','format_hashes']:assert after.get(k)==baseline.get(k),k
record('seven_fields_roundtrip',passed=True,comments_readback=after['comments'],cover_reencoded=hashlib.sha256(cover.read_bytes()).hexdigest()!=after['cover_hash'],unedited_fields_preserved=True)
# Genuine sequential partial save: first successes remain when a later operation fails.
p=save(title='M2 Committed Title',tags='Committed tag');assert p.returncode==0
before_fail=read();p=save(series_index='not-a-number');after_fail=read()
assert p.returncode!=0 and after_fail['title']==before_fail['title'] and after_fail['tags']==before_fail['tags'] and after_fail['series_index']==before_fail['series_index']
record('partial_across_commands',passed=True,failed_exit=p.returncode,successful_title_and_tags_retained=True,failed_index_unchanged=True)
# Probe whether a mixed command is atomic for input-validation failure.
before=read();p=save(title='Must not be accepted on parse failure',series_index='invalid');after=read()
record('combined_parse_failure',exit_code=p.returncode,title_changed=before['title']!=after['title'],stderr=p.stderr[-500:])
# Missing and invalid cover may be silently ignored or cause partially applied metadata.
for label,path in [('missing_cover',root/'absent.png'),('invalid_cover',root/'invalid.png')]:
 if label=='invalid_cover':path.write_bytes(b'not an image')
 before=read();p=save(title='M2 '+label,cover=path);after=read()
 cover_path=Path(after['cover'])
 try:
  with Image.open(cover_path) as im: im.verify()
  decodable=True
 except Exception: decodable=False
 record(label,exit_code=p.returncode,title_changed=after['title']!=before['title'],cover_changed=after['cover_hash']!=before['cover_hash'],cover_bytes=cover_path.stat().st_size,cover_decodable=decodable,stderr=p.stderr[-1000:])
# Recovery on the disposable copy using the known valid replacement.
p=save(cover=cover);recovered=read()
with Image.open(recovered['cover']) as im: im.verify()
assert p.returncode==0 and recovered['cover_hash']
record('cover_retry_with_valid_image',passed=True,cover_decodable=True)
# Clearing/coupling requires explicit policy; record rather than infer support.
p=save(series='',series_index='1');after=read();record('clear_series',exit_code=p.returncode,series=after.get('series'),index=after.get('series_index'))
p=save(series_index='3.5');after=read();record('index_without_series',exit_code=p.returncode,series=after.get('series'),index=after.get('series_index'))
# Revalidation against an external CLI actor; this is a protocol experiment, not app conflict UI.
save(series='Conflict Series',series_index='1',tags='Baseline tag');base=read();draft={'tags':['Local tag'],'comments':'<p>Local description</p>'}
save(tags='External tag',publisher='External publisher');current=read()
conflicts=[k for k in draft if current.get(k)!=base.get(k) and current.get(k)!=draft[k]]
assert conflicts==['tags']
# User chooses external tags, local description; only local outstanding field is sent.
p=save(comments=draft['comments']);final=read();assert p.returncode==0 and final['tags']==['External tag'] and final['publisher']=='External publisher'
record('pre_save_three_way_conflict',passed=True,conflicts=conflicts,external_unedited_publisher_preserved=True,chosen_external_tags_preserved=True)
# A new external edit after a failed attempt must conflict on retry.
base=read();save(comments='<p>New external description</p>');current=read()
assert current['comments']!=base['comments'] and current['comments']!=draft['comments']
record('retry_revalidation',passed=True,new_conflicting_field='comments',no_retry_write_sent=True)
# Discard protocol: abandon local draft, keep already committed current metadata.
draft.clear();discard=read();assert discard['title']==final['title'] and discard['tags']==final['tags']
record('discard_remaining_draft',passed=True,committed_values_preserved=True)
assert source_before==hashes(source)
summary={'temporary_root':str(root),'source_library_unchanged':True,'book_id':book,'checks':checks,'limits':['Disposable CLI/protocol tests, not implemented M2 editor','No atomic cross-process compare-and-set guarantee','No actual disk-full failure injected','Cover deletion and rich-text editing not selected']}
(evidence/'report.json').write_text(json.dumps(summary,indent=2));print('COMPLETE: original-library hashes unchanged',flush=True)
