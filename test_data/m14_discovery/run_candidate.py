"""Read-only fixture/source mounts; candidate reports are the only retained writes."""
import subprocess,sys,json
from pathlib import Path
root=Path(__file__).resolve().parents[2];reports=root/'test_data/m14_discovery';fixture=reports/'scale'
args=['docker','run','--rm','--network','none','--read-only','--user','1000:1000','--tmpfs','/tmp:rw,mode=1777','--tmpfs','/tmp/runtime:rw,mode=700,uid=1000,gid=1000','-v','/run/user/1000/wayland-0:/tmp/runtime/wayland-0:ro','-e','XDG_RUNTIME_DIR=/tmp/runtime','-e','XDG_SESSION_TYPE=wayland','-e','WAYLAND_DISPLAY=wayland-0','-e','HOME=/tmp','-e','QT_QPA_PLATFORM=offscreen','-e','CALIBRE_CONFIG_DIRECTORY=/tmp/calibre','-v',str(root)+':/scripts:ro','-v',str(fixture)+':/fixture:ro','-v',str(reports)+':/reports:rw','--entrypoint','/usr/bin/python3','sha256:da0d06cee1517cbbc0b0b8910c3303b6ad3b47377445a76e47994e977f885783','-B','/scripts/test_data/m14_discovery/benchmark_candidate.py']
installed='--installed' in sys.argv
if installed:
 release=(root.parent/'Mediaintor-M14-Development/active/home/.local/share/mediainator-install/current').resolve()
 verified=json.loads((reports/'installed_candidate.json').read_text());assert release.name==verified['build']
 args[args.index('--entrypoint'):args.index('--entrypoint')]=['-v',str(release)+':/release:ro','-e','M14_CODE_ROOT=/release','-e','M14_BUILD='+release.name,'-e','M14_REPORT=installed_performance.json']
with (reports/('installed_scale_output.log' if installed else 'candidate_output.log')).open('w') as log:subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=1800)
print('Candidate benchmark completed')
