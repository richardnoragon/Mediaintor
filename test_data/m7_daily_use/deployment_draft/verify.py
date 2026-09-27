"""Container checks; writes only a scratch database, never library metadata."""
import json,sys,sqlite3,tempfile
from pathlib import Path
release=(Path.home()/'.local/share/mediainator-install/current').resolve(strict=True)
sys.path.insert(0,str(release))
from mediainator.compatibility import service
result=service.check(force=True)
assert result.verified,result.message
from PyQt6.QtWidgets import QApplication
app=QApplication([])
assert app.platformName()=='wayland',app.platformName()
with tempfile.TemporaryDirectory(prefix='m7-lock-',dir=Path.home()) as folder:
    path=Path(folder)/'check.db';a=sqlite3.connect(path,timeout=.1);b=sqlite3.connect(path,timeout=.1)
    a.execute('create table probe(value text)');a.commit();a.execute('begin immediate');a.execute("insert into probe values ('saved')")
    try:b.execute("insert into probe values ('blocked')")
    except sqlite3.OperationalError as exc:assert 'locked' in str(exc)
    else:raise AssertionError('Concurrent writer was not blocked')
    a.commit();assert b.execute('select value from probe').fetchall()==[('saved',)];b.close();a.close()
with sqlite3.connect('file:/data/library/metadata.db?mode=ro',uri=True) as db:
    count=db.execute('select count(*) from books').fetchone()[0]
    assert db.execute('pragma integrity_check').fetchone()[0]=='ok'
assert count==101,count
# Exercise actual Calibre adapter writes on a throwaway copy of the test library.
from mediainator.snapshot import Snapshot
from mediainator.metadata import run_request
with tempfile.TemporaryDirectory(prefix='m7-adapter-') as folder:
    import shutil
    copy=Path(folder)/'library';shutil.copytree('/data/library',copy)
    with sqlite3.connect(copy/'metadata.db') as db:
        book,uuid=db.execute('select id,uuid from books order by id limit 1').fetchone()
    args={'action':'read','book':book,'uuid':uuid}
    original=run_request(copy,args,Path(folder)/'covers')
    baseline=original['current'];tags=baseline['tags']+['M7 container probe']
    saved=run_request(copy,dict(action='save',book=book,uuid=uuid,baseline=baseline,changes={'tags':tags}),Path(folder)/'covers')
    readback=run_request(copy,args,Path(folder)/'covers')['current']
    assert set(readback['tags'])==set(tags),saved
    run_request(copy,dict(action='save',book=book,uuid=uuid,baseline=readback,changes={'tags':baseline['tags']}),Path(folder)/'covers')
    assert set(run_request(copy,args,Path(folder)/'covers')['current']['tags'])==set(baseline['tags'])
snapshot=Snapshot(Path('/data/library')).create()
try:
    with sqlite3.connect(snapshot.root/'metadata.db') as db:
        assert db.execute('select count(*) from books').fetchone()[0]==101
finally:snapshot.close()
print(json.dumps({'compatibility':result.detected,'qt_platform':app.platformName(),'sqlite_write_lock':'passed','books':count,'library_integrity':'ok','snapshot':'passed','calibre_adapter_write_readback_restore':'passed on throwaway copy','reader_visual_acceptance':'pending'},indent=2))
