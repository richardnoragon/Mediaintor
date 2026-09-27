import subprocess,json
from pathlib import Path
root=Path(__file__).resolve().parents[2];r=root/'test_data/m14_discovery';verification=json.loads((r/'duplicate_refresh_package_verification.json').read_text())
release=(Path(verification['fixture'])/'.local/share/mediainator-install/current').resolve()
assert (release/'mediainator').is_dir()
args=['docker','run','--rm','--network','none','--read-only','--user','1000:1000','--tmpfs','/tmp:rw,mode=1777','--tmpfs','/tmp/runtime:rw,mode=700,uid=1000,gid=1000','-v','/run/user/1000/wayland-0:/tmp/runtime/wayland-0:ro','-e','XDG_RUNTIME_DIR=/tmp/runtime','-e','XDG_SESSION_TYPE=wayland','-e','WAYLAND_DISPLAY=wayland-0','-e','HOME=/tmp','-e','QT_QPA_PLATFORM=offscreen','-e','CALIBRE_CONFIG_DIRECTORY=/tmp/calibre','-v',str(root)+':/scripts:ro','-v',str(r/'scale')+':/fixture:ro','-v',str(r)+':/reports:rw','-v',str(release)+':/release:ro','--entrypoint','/usr/bin/python3','sha256:da0d06cee1517cbbc0b0b8910c3303b6ad3b47377445a76e47994e977f885783','-B','/scripts/test_data/m14_discovery/check_duplicate_refresh_scale.py']
with (r/'duplicate_refresh_scale_output.log').open('w') as log:subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=300)
