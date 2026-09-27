"""Launch the frozen M17 acceptance build with independent disposable state."""
import os,sys,json,tarfile,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
base=Path(__file__).resolve().parent
archive=ROOT/'dist/m17-movieinator/mediainator-0.1.0a1-ubuntu26.04-x86_64.tar.gz'
with tarfile.open(archive) as bundle:
    manifest=json.load(bundle.extractfile('manifest.json'))
    build=manifest['version']+'-'+manifest['build_id']
    release=base/'releases'/build
    if not release.exists():
        release.mkdir(parents=True)
        bundle.extractall(release,filter='data')
env=dict(os.environ, XDG_CONFIG_HOME=str(base/'profile/config'), XDG_DATA_HOME=str(base/'profile/data'), XDG_CACHE_HOME=str(base/'profile/cache'), MEDIAINATOR_INSTALLATION_LABEL='M17 Movie-inator Testing')
config=base/'profile/config/Media-inator/Media-inator/settings.json'
if not config.exists():
    sys.path.insert(0,str(release))
    from mediainator.settings import defaults
    state=defaults();state['profile_name']='M17 acceptance';state['bookinator_open']=False
    config.parent.mkdir(parents=True,exist_ok=True)
    config.write_text(json.dumps(state,indent=2)+'\n')
catalog=base/'profile/data/Movies/catalog.sqlite'
log=(base/'desktop.log').open('a')
process=subprocess.Popen(['/usr/bin/python3','-B','-m','mediainator','--sample','--movie-catalog',str(catalog)],cwd=release,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
(base/'session.json').write_text(json.dumps(dict(build=build,pid=process.pid,catalog=str(catalog),scope='Frozen M17 test build; independent profile and movie catalog; sample books only; no Everyday data mounted or configured'),indent=2)+'\n')
print('Started M17 test build '+build)
