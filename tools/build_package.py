"""Build a deterministic personal-use bundle without pip or network access."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile
import tomllib

ROOT = Path(__file__).resolve().parent.parent

def build(destination):
    version = tomllib.loads((ROOT/'pyproject.toml').read_text())['project']['version']
    files = {str(p.relative_to(ROOT)): p.read_bytes() for p in sorted((ROOT/'mediainator').glob('*.py'))}
    for name in ('runtime.json', 'mediainator.desktop.in', 'mediainator.svg', 'NOTICES.txt', 'INSTALL.md', 'USER_GUIDE.md', 'TROUBLESHOOTING.md', 'run.py'):
        files[name] = (ROOT/'packaging'/name).read_bytes()
    files['package_install.py'] = (ROOT/'tools/package_install.py').read_bytes()
    files['README.md'] = b'Media-inator personal preview. Read INSTALL.md and USER_GUIDE.md.\n'
    hashes = {name: hashlib.sha256(data).hexdigest() for name, data in sorted(files.items())}
    build_id = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()[:16]
    manifest = {'schema': 1, 'version': version, 'build_id': build_id, 'files': hashes}
    files['manifest.json'] = (json.dumps(manifest, indent=2, sort_keys=True)+'\n').encode()
    destination.mkdir(parents=True, exist_ok=True)
    target = destination/f'mediainator-{version}-ubuntu26.04-x86_64.tar.gz'
    with target.open('wb') as raw, gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as zipped:
        with tarfile.open(fileobj=zipped, mode='w') as archive:
            for name, data in sorted(files.items()):
                item = tarfile.TarInfo(name); item.size=len(data); item.mode=0o644
                archive.addfile(item, io.BytesIO(data))
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    target.with_suffix(target.suffix+'.sha256').write_text(f'{digest}  {target.name}\n')
    return target, digest

if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'dist')
    args=parser.parse_args();target,digest=build(args.output);print(f'{digest}  {target}')
