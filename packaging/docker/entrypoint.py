"""Explicit installation and launch of the bundled, verified application."""
import os
from pathlib import Path
import subprocess
import sys

mode = sys.argv[1] if len(sys.argv) > 1 else 'run'
if mode == 'install':
    raise SystemExit(subprocess.call(['/usr/bin/python3', '-I', '-B',
        '/opt/mediainator/installer/package_install.py', 'install',
        '/opt/mediainator/candidate.tar.gz']))
launcher = Path.home() / '.local/bin/mediainator'
if not launcher.is_file():
    raise SystemExit('Run the explicit install command before launching.')
if mode not in ('run', 'verify'):
    raise SystemExit('Expected install, verify or run')
args = [str(launcher)] + (['--package-smoke'] if mode == 'verify' else sys.argv[2:])
os.execv(str(launcher), args)
