"""Explicit integration/fault test: calibre-debug -e tests/verify_m2_calibre.py.
Creates a new full disposable copy. Never writes the source library.
"""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
import json, tempfile, shutil, hashlib, base64
from unittest.mock import patch
from calibre.db.legacy import LibraryDatabase
from calibre.db.cache import Cache
from calibre.utils.lock import singleinstance
from mediainator.calibre_metadata_helper import execute

source=Path('/home/sproket01/Calibre Library');root=Path(tempfile.mkdtemp(prefix='mediainator-m2-integration-'));lib=root/'library'
out=Path('test_data/m2_acceptance');out.mkdir(exist_ok=True)
def hashes(folder):return {str(p.relative_to(folder)):hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*') if p.is_file()}
before=hashes(source);shutil.copytree(source,lib)
assert singleinstance('db'), 'Close Calibre before validation'
(lib/'.mediainator-disposable.json').write_text(json.dumps({'purpose':'mediainator-disposable-test','root':str(lib)}))
db=LibraryDatabase(str(lib));uuid=db.new_api.field_for('uuid',32);ids=db.new_api.all_book_ids();formats={i:{f:hashlib.sha256(db.new_api.format(i,f)).hexdigest() for f in db.new_api.formats(i)} for i in ids};db.close()
checks=[]
def check(name,condition,**data):
    checks.append(dict(test=name,passed=bool(condition),**data));print(name,condition,flush=True)
    (out/'adapter_checks.json').write_text(json.dumps(checks,indent=2));assert condition,name

def call(action='read',**kw):
    with patch('calibre.utils.lock.singleinstance',return_value=True):
        return execute(dict(action=action,library=str(lib),book=32,uuid=uuid,recovery_dir=str(root/'recovery'),**kw))

def save(current,**pending):return call('save',baseline=current,changes=pending)
try:
    baseline=call()['current'];cover=baseline['cover'];html='<p class="exact">Exact <b>HTML</b> &amp; link <a href="https://example.org">here</a>.</p>'
    r=save(baseline,title='M2 integration title',authors=['Asimov, Isaac','Silverberg, Robert'],tags=['M2 validation','Classic'],series='Test series',series_index=2.5,comments=html,cover=None)
    check('seven_fields_and_cover_removal',not r['errors'] and len(r['saved'])==7 and r['current']['cover'] is None)
    current=r['current'];r=save(current,cover=cover);check('cover_replacement',not r['errors'] and bool(r['current']['cover']))
    current=r['current'];r=save(current,series='',series_index=None)
    check('series_clear_accepts_internal_index',not r['errors'] and r['current']['series_index'] is None and r['current']['series']=='')
    r=save(r['current'],series='New series',series_index=1)
    check('new_series_default',not r['errors'] and r['current']['series_index']==1)
    base=r['current'];external=save(base,tags=['External tag'])['current']
    conflict=save(base,tags=['My tag'],comments='<p>My description</p>')
    check('conflict_no_write',conflict.get('conflicts')==['tags'] and call()['current']['comments']==html)
    r=save(conflict['current'],comments='<p>My description</p>')
    check('choose_external_preserves_other_changes',not r['errors'] and r['current']['tags']==['External tag'])
    original_set=Cache.set_field
    def fail_tags(self,name,mapping,**kwargs):
        if name=='tags':raise OSError('Injected tag-write failure')
        return original_set(self,name,mapping,**kwargs)
    with patch.object(Cache,'set_field',fail_tags):r=save(r['current'],title='Committed before failure',tags=['Pending tag'])
    check('real_adapter_partial_save',r['saved']==['title'] and 'tags' in r['errors'] and r['current']['title']=='Committed before failure')
    base=r['current'];save(base,tags=['Second external change']);r=save(base,tags=['Pending tag'])
    check('retry_rechecks_conflict',r.get('conflicts')==['tags'])
    current=call()['current'];original_cover=Cache.set_cover;attempt=[0]
    def damage_once(self,mapping):
        attempt[0]+=1
        return original_cover(self,{32:b'injected invalid image'} if attempt[0]==1 else mapping)
    # Different valid PNG: ensures cover write is attempted, not an unchanged-field shortcut.
    from qt.core import QImage,QColor,QBuffer,QIODevice
    image=QImage(30,40,QImage.Format.Format_RGB32);image.fill(QColor('red'));buffer=QBuffer();buffer.open(QIODevice.OpenModeFlag.WriteOnly);image.save(buffer,'PNG');newcover=base64.b64encode(bytes(buffer.data())).decode()
    with patch.object(Cache,'set_cover',damage_once):r=save(current,comments='<p>Saved before cover failure</p>',cover=newcover)
    check('damaged_cover_restored',bool(r['errors'].get('cover')) and r['current']['cover']==current['cover'] and 'restored successfully' in r['recovery'] and r['current']['comments']=='<p>Saved before cover failure</p>')
    def fail_cover(self,mapping):raise OSError('Injected recovery failure')
    with patch.object(Cache,'set_cover',fail_cover):r=save(r['current'],cover=newcover)
    check('failed_recovery_keeps_backup',bool(r['errors']) and 'recovery failed' in r['recovery'] and any((root/'recovery').glob('*.json')))
    r=save(r['current'],cover=newcover);check('retry_valid_cover',not r['errors'])
    current=r['current']
    for bad in ['Bad, tag']:
        try:save(current,title='Must not save',tags=[bad]);raise AssertionError('validation missing')
        except ValueError:pass
    check('invalid_tag_no_mutation',call()['current']['title']==current['title'])
    try:save(current,cover=base64.b64encode(b'bad').decode(),title='Must not save');raise AssertionError('validation missing')
    except ValueError:pass
    check('invalid_cover_prevalidated',call()['current']['title']==current['title'])
    with patch('calibre.utils.lock.singleinstance',return_value=False):
        try:execute(dict(action='read',library=str(lib),book=32,uuid=uuid));raise AssertionError('lock bypass')
        except RuntimeError as exc:check('lock_denial', 'Waiting for library access' in str(exc))
    db=LibraryDatabase(str(lib));api=db.new_api
    check('catalog_101_and_formats_unchanged',len(api.all_book_ids())==101 and all({f:hashlib.sha256(api.format(i,f)).hexdigest() for f in api.formats(i)}==formats[i] for i in ids))
    check('uuid_preserved',api.field_for('uuid',32)==uuid);db.close()
finally:
    unchanged=hashes(source)==before
    (out/'adapter_report.json').write_text(json.dumps(dict(library=str(lib),uuid=uuid,source_unchanged=unchanged,checks=checks),indent=2))
    assert unchanged,'Source changed during tests'
