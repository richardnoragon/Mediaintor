"""Install once; fail closed on a different/modified release. No automatic upgrade."""
import hashlib,json,subprocess,sys
from pathlib import Path
base=Path.home()/'.local/share/mediainator-install'
expected='0.1.0a1-c08faf149723f3c0'
if (base/'transaction.json').exists():raise SystemExit('Pending installation repair: resolve before starting RC1.')
if not (base/'installation.json').exists():
    if (base/'current').exists():raise SystemExit('Unregistered existing installation; inspect it manually.')
    subprocess.run(['/usr/bin/python3','-I','-B','/opt/mediainator/installer/package_install.py','install','/opt/mediainator/candidate.tar.gz'],check=True)
state=json.loads((base/'installation.json').read_text())
assert state['current']==expected,'Different build installed; RC1 will not silently replace it'
folder=base/'releases'/expected
assert (base/'current').resolve()==folder.resolve()
for rel,hashes in state['releases'].items():
    directory=base/'releases'/rel
    assert directory.resolve().parent==(base/'releases').resolve()
    assert not any(p.is_symlink() for p in directory.rglob('*'))
    actual={str(p.relative_to(directory)):hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.rglob('*') if p.is_file()}
    assert actual==hashes,'Program inventory differs; inspect before running RC1'
print('RC1 installed build verified:',expected)
