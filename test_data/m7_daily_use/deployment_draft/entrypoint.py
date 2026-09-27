"""Explicit install/check/run; never upgrades the candidate automatically."""
import os
from pathlib import Path
import sys
import subprocess
runtime=Path('/tmp/runtime');runtime.mkdir(mode=0o700,exist_ok=True)
mode=sys.argv[1] if len(sys.argv)>1 else 'run'
if mode=='install':
    sys.exit(subprocess.call(['/usr/bin/python3','-I','-B','/opt/mediainator/installer/package_install.py','install','/opt/mediainator/candidate.tar.gz']))
if mode=='verify':
    os.execv('/usr/bin/python3',['python3','-I','-B','/opt/mediainator/verify.py'])
if mode!='run':raise SystemExit('Expected install, verify or run')
launcher=Path.home()/'.local/bin/mediainator'
if not launcher.is_file():raise SystemExit('Install the candidate explicitly before launching.')
os.execv(str(launcher),[str(launcher)])
