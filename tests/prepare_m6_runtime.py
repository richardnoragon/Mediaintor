"""Download/extract an Ubuntu dependency closure into /tmp; never install system packages."""
import hashlib,json,re,subprocess,tempfile
from pathlib import Path
project=Path(__file__).resolve().parent.parent
root=Path(tempfile.mkdtemp(prefix='mediainator-m6-clean-'));(root/'status').touch();(root/'downloaded').mkdir()
requested=json.loads((project/'packaging/runtime.json').read_text())['system_packages']+['bash','coreutils','dpkg','base-files']
solver=subprocess.run(['apt-get','-s','-o','Dir::State::status='+str(root/'status'),'--no-install-recommends','install',*requested],capture_output=True,text=True,check=True)
(root/'solver.txt').write_text(solver.stdout)
packages=[]
for line in solver.stdout.splitlines():
    match=re.match(r'Inst (\S+) \((\S+)',line)
    if match:packages.append(match[1]+'='+match[2])
with (root/'download.log').open('w') as log:
    subprocess.run(['apt-get','-o','Acquire::Retries=0','-o','Acquire::http::Timeout=20','download',*packages],cwd=root/'downloaded',stdout=log,stderr=subprocess.STDOUT,check=True,timeout=240)
fs=root/'rootfs';fs.mkdir()
archives=sorted((root/'downloaded').glob('*.deb'),key=lambda p:0 if p.name.startswith('base-files_') else 1)
for archive in archives:subprocess.run(['dpkg-deb','-x',str(archive),str(fs)],check=True)
for name in ['home/m6-test','dev','proc','tmp']:(fs/name).mkdir(parents=True,exist_ok=True)
# Debian maintainer scripts normally configure /bin/sh. Use installed bash in POSIX mode.
sh=fs/'usr/bin/sh'
if not sh.exists():sh.symlink_to('bash')
report={'root':str(root),'rootfs':str(fs),'requested':requested,'packages':packages,'extracted_packages':len(archives),
        'shell_setup':'usr/bin/sh -> bash (POSIX invocation); no maintainer scripts executed',
        'archives':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in archives}}
(project/'test_data/m6_06_installation/clean_root.json').write_text(json.dumps(report,indent=2)+'\n')
print(fs)
