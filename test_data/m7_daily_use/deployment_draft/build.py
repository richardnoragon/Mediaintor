"""Build from the fixed local artifact, then pin the image ID for all launches."""
import hashlib,json,os,shutil,subprocess,tempfile
from pathlib import Path
folder=Path(__file__).resolve().parent;root=folder.parent
candidate=json.loads((root/'candidate.json').read_text())
archive=root/candidate['artifact']
assert hashlib.sha256(archive.read_bytes()).hexdigest()==candidate['artifact_sha256']
with tempfile.TemporaryDirectory(prefix='image-context-',dir=folder) as temporary:
    context=Path(temporary)
    for name in ('Dockerfile','entrypoint.py','verify.py'):shutil.copy2(folder/name,context/name)
    shutil.copy2(archive,context/'candidate.tar.gz')
    subprocess.run(['docker','build','--build-arg',f'PACKAGE_SHA256={candidate["artifact_sha256"]}','--build-arg',f'APP_UID={os.getuid()}','--build-arg',f'APP_GID={os.getgid()}','--iidfile',str(context/'image.id'),'-t','mediainator-m7:candidate',str(context)],check=True)
    image=(context/'image.id').read_text().strip()
    assert image.startswith('sha256:')
    candidate.update(container_image_digest=image,deployment='Docker image built; install/runtime/display acceptance pending')
    (root/'candidate.json').write_text(json.dumps(candidate,indent=2)+'\n')
    inspect=subprocess.check_output(['docker','image','inspect',image])
    (root/'evidence/docker_image.json').write_bytes(inspect)
print('Image pinned:',image)
