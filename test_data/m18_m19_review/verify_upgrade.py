import os,sys,json,hashlib
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4
root=Path.cwd();sys.path.insert(0,str(root))
from tools import package_install
from mediainator.paper_store import PaperStore
from mediainator.music_store import MusicStore
base=root/'test_data/m18_m19_review/upgrade';base.mkdir(parents=True,exist_ok=True)
for key,folder in [('XDG_CONFIG_HOME','config'),('XDG_DATA_HOME','data'),('XDG_CACHE_HOME','cache')]:os.environ[key]=str(base/folder)
profile=str(uuid4());p=PaperStore(base/'data/paper'/profile,profile);p.initialize()
paper=p.add_item({'title':'Retained research'});p.add_note({'title':'Retained note','body':'# Knowledge survives upgrade','item_id':paper})
m=MusicStore(base/'data/music.sqlite',profile);m.add_album({'title':'Retained album','artists':['Review artist']})
def hashes():return {str(path.relative_to(base/'data')):hashlib.sha256(path.read_bytes()).hexdigest() for path in (base/'data').rglob('*') if path.is_file()}
before=hashes();old=root/'test_data/m18_m19_review/package/artifact/mediainator-0.1.0a1-ubuntu26.04-x86_64.tar.gz';new=root/'test_data/m18_m19_review/final_package/artifact/mediainator-0.1.0a1-ubuntu26.04-x86_64.tar.gz'
checks=[]
with patch.object(package_install,'integration_paths',lambda:(base/'installation',base/'bin/mediainator',base/'applications/mediainator.desktop')):
 for label,archive in [('install prior',old),('upgrade candidate',new),('rollback prior',old),('upgrade again',new)]:
  package_install.run('install',archive);assert hashes()==before;checks.append(label+' preserves populated data bytes')
 package_install.run('uninstall',yes=True);assert hashes()==before;checks.append('uninstall preserves populated data')
 package_install.run('install',new);assert hashes()==before;checks.append('reinstall preserves populated data')
assert p.load().items[0].title=='Retained research';assert m.load()[0].title=='Retained album'
(base/'report.json').write_text(json.dumps({'checks':checks,'profile':profile,'paper_note_retained':True},indent=2)+'\n')
print(checks)
