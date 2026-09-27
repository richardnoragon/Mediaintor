"""Verify the completed fixture and measure the accepted installed baseline."""
import json,hashlib,subprocess,time
from pathlib import Path
root=Path(__file__).resolve().parents[2];reports=root/'test_data/m14_discovery';fixture=reports/'scale'
deadline=time.monotonic()+900
while not (fixture/'fixture.json').exists():
 if time.monotonic()>deadline:raise TimeoutError('Fixture creation has not completed')
 time.sleep(1)
# Make status independent of cover distribution; these are oracle-only values.
p=fixture/'oracle.json';records=json.loads(p.read_text())
for row in records:row['reading_status']=['Unknown','Unread','Reading','Finished'][(row['n']//3)%4]
p.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
p=fixture/'fixture.json';info=json.loads(p.read_text());info['oracle_sha256']=hashlib.sha256((fixture/'oracle.json').read_bytes()).hexdigest();p.write_text(json.dumps(info,indent=2)+'\n')
subprocess.run(['python3','-B',str(reports/'verify_scale.py')],check=True)
release=(root.parent/'Mediaintor-M14-Development/active/home/.local/share/mediainator-install/current').resolve()
assert release.name=='0.1.0a1-db6a7fb8885f9bd9'
args=['docker','run','--rm','--network','none','--read-only','--user','1000:1000','--tmpfs','/tmp:rw,mode=1777','--tmpfs','/tmp/runtime:rw,mode=700,uid=1000,gid=1000','-v','/run/user/1000/wayland-0:/tmp/runtime/wayland-0:ro','-e','XDG_RUNTIME_DIR=/tmp/runtime','-e','XDG_SESSION_TYPE=wayland','-e','WAYLAND_DISPLAY=wayland-0','-e','HOME=/tmp','-e','QT_QPA_PLATFORM=offscreen','-e','CALIBRE_CONFIG_DIRECTORY=/tmp/calibre','-v',str(root)+':/scripts:ro','-v',str(fixture)+':/fixture:ro','-v',str(reports)+':/reports:rw','-v',str(release)+':/release:ro','--entrypoint','/usr/bin/python3','sha256:da0d06cee1517cbbc0b0b8910c3303b6ad3b47377445a76e47994e977f885783','-B','/scripts/test_data/m14_discovery/benchmark_scale.py']
with (reports/'baseline_output.log').open('w') as log:subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=1800)
print('Verification and baseline benchmark completed',flush=True)
