"""Host launcher using only the sibling candidate/data and Wayland socket."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parent.parent
candidate=json.loads((root/'candidate.json').read_text())
archive=root/candidate['artifact']
if hashlib.sha256(archive.read_bytes()).hexdigest()!=candidate['artifact_sha256']:raise SystemExit('Candidate archive hash mismatch')
action=sys.argv[1] if len(sys.argv)>1 else 'run'
if action not in ('install','verify','run'):raise SystemExit('Expected install, verify or run')
image=candidate.get('container_image_digest')
if not image or not image.startswith('sha256:'):raise SystemExit('Build and record a verified local Docker image ID first.')
sock=Path(os.environ.get('XDG_RUNTIME_DIR',''))/os.environ.get('WAYLAND_DISPLAY','wayland-0')
if not sock.is_socket():raise SystemExit('Run from your active KDE Wayland session; display socket unavailable.')
args=['docker','run','--rm','--init','--name','mediainator-m7','--network','none','--read-only',
      '--cap-drop','ALL','--security-opt','no-new-privileges','--user',f'{os.getuid()}:{os.getgid()}',
      '--tmpfs','/tmp:rw,nosuid,nodev,mode=1777',
      '--tmpfs',f'/tmp/runtime:rw,nosuid,nodev,mode=700,uid={os.getuid()},gid={os.getgid()}',
      '--mount',f'type=bind,src={root/"active/home"},dst=/home/mediainator',
      '--mount',f'type=bind,src={root/"active/library"},dst=/data/library',
      '--mount',f'type=bind,src={root/"active/import-sources"},dst=/data/import-sources',
      '--mount',f'type=bind,src={sock},dst=/tmp/runtime/wayland-0,readonly',image,action]
# No host home, source tree, Docker socket or session bus is mounted.
sys.exit(subprocess.call(args))
