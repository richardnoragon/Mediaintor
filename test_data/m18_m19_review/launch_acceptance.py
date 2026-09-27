"""Launch a frozen review build with a separate M18 or M19 acceptance profile."""
import os,sys,json,subprocess
from pathlib import Path
base=Path(__file__).resolve().parent
milestone=sys.argv[1] if len(sys.argv)>1 else '19'
if milestone not in ('18','19'):raise SystemExit('Choose 18 or 19')
release=base/'final_package/installation/releases/0.1.0a1-b016b423b7099943'
profile=base/('desktop_m'+milestone)
profile.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,XDG_CONFIG_HOME=str(profile/'config'),XDG_DATA_HOME=str(profile/'data'),XDG_CACHE_HOME=str(profile/'cache'),MEDIAINATOR_INSTALLATION_LABEL='M'+milestone+' Acceptance Testing')
sys.path.insert(0,str(release))
from mediainator.settings import defaults
config=profile/'config/Media-inator/Media-inator/settings.json'
if not config.exists():
 state=defaults();state.update(profile_name='M'+milestone+' acceptance',bookinator_open=False,musicinator_open=milestone=='18',paperinator_open=milestone=='19')
 config.parent.mkdir(parents=True,exist_ok=True);config.write_text(json.dumps(state,indent=2)+'\n')
 from mediainator.music_store import MusicStore
 from mediainator.music_scan import plan
 from mediainator.paper_store import PaperStore
 from mediainator.paper_import import plan as papers
 fixtures=base/'real_media'
 if milestone=='18':
  store=MusicStore(profile/'music.sqlite',state['profile_id'])
  for group in plan([fixtures/'audio'],[],set()).groups:
   store.apply_group('create',group.editions(),title=group.title,artists=[group.artist],year=group.year,genres=group.genres)
 else:
  store=PaperStore(profile/'paper/profiles'/state['profile_id'],state['profile_id']);store.initialize()
  for proposal in papers([fixtures/'Research.pdf'],store.load(),{},set()).proposals:
   store.import_document(proposal.path,'managed',item_fields=proposal.fields,text=proposal.text,expected=(proposal.size,proposal.sha256))
with (profile/'desktop.log').open('a') as log:
 process=subprocess.Popen(['/usr/bin/python3','-B','-m','mediainator','--sample','--music-catalog',str(profile/'music.sqlite'),'--paper-library',str(profile/'paper')],cwd=release,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
(profile/'session.json').write_text(json.dumps({'pid':process.pid,'release':str(release)},indent=2)+'\n')
print('Started M'+milestone+' isolated acceptance build')
