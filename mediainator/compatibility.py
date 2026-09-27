"""Fail-closed Calibre compatibility at operation boundaries; no library probes."""
from dataclasses import dataclass
import importlib.metadata
import os
from pathlib import Path
import platform
import re
import subprocess
import tempfile
import threading

SUPPORTED = '9.2.1'
TOOLS = ('calibre', 'calibredb', 'calibre-debug', 'ebook-viewer')

class CompatibilityError(RuntimeError):
    pass

@dataclass(frozen=True)
class Result:
    state: str
    detected: str
    reason: str
    @property
    def verified(self):return self.state == 'verified'
    @property
    def message(self):
        return (f'Detected: {self.detected}. Supported Calibre: {SUPPORTED}. {self.reason} '
                + ('Existing library-access rules still apply.' if self.verified else
                   'Protected library operations are disabled. Install the verified prerequisites separately, then choose Recheck. Help, local history and preservation remain available. No override is available.'))

def signature():
    paths=[Path('/usr/bin')/name for name in TOOLS]
    # Ubuntu's CLI wrappers can stay unchanged while the Calibre Python package changes.
    paths += [Path('/usr/lib/calibre/calibre/constants.py'), Path('/usr/lib/calibre/calibre/__init__.py')]
    return tuple((str(p.resolve()),p.stat().st_dev,p.stat().st_ino,p.stat().st_size,p.stat().st_mtime_ns,p.stat().st_ctime_ns) for p in paths)

def runtime_problem():
    from PyQt6.QtCore import qVersion
    actual=(platform.python_version(),importlib.metadata.version('PyQt6'),
            importlib.metadata.version('PyQt6-sip'),qVersion())
    expected=('3.14.4','6.10.2','13.11.0','6.10.2')
    if actual!=expected:return 'Unverified Python/PyQt6/SIP/Qt runtime: '+', '.join(actual)+'. Verified: '+', '.join(expected)+'.'
    os_info=platform.freedesktop_os_release()
    if os_info.get('ID')!='ubuntu' or os_info.get('VERSION_ID')!='26.04' or platform.machine()!='x86_64':
        return 'The verified platform is Ubuntu 26.04 x86_64 with KDE.'
    return ''

def probe_version(tool):
    with tempfile.TemporaryDirectory(prefix='mediainator-version-') as folder:
        env={k:v for k,v in os.environ.items() if not k.startswith(('PYTHON','QT_'))}
        env.pop('CALIBRE_OVERRIDE_DATABASE_PATH',None)
        env['CALIBRE_CONFIG_DIRECTORY']=folder
        # Preserve the desktop platform for ebook-viewer's version-only initialization.
        output=subprocess.run(['/usr/bin/'+tool,'--version'],env=env,capture_output=True,timeout=8)
        if output.returncode:raise ValueError('Version command failed for '+tool)
        if len(output.stdout)>4096:raise ValueError('Oversized version response for '+tool)
        match=re.fullmatch(re.escape(tool)+r' \(calibre ([0-9]+\.[0-9]+\.[0-9]+)\)\s*',output.stdout.decode('utf-8').strip())
        if not match:raise ValueError('Unrecognized version response for '+tool)
        return match[1]

class Service:
    def __init__(self):self.lock=threading.Lock();self.cached=None;self.identity=None
    def check(self,force=False):
        with self.lock:
            try:
                problem=runtime_problem()
                if problem:return Result('unverified','runtime',problem)
                before=signature()
                if not force and self.cached and self.cached.verified and self.identity==before:return self.cached
                versions={tool:probe_version(tool) for tool in TOOLS}
                if signature()!=before:return Result('probe-failed','changed during check','Toolchain changed; recheck after updates finish.')
                detected=', '.join(f'{k} {v}' for k,v in versions.items())
                if len(set(versions.values()))!=1:result=Result('inconsistent-toolchain',detected,'Calibre tools report different versions.')
                elif next(iter(versions.values()))!=SUPPORTED:result=Result('unverified',detected,'This version has not passed compatibility verification.')
                else:result=Result('verified',detected,'Compatibility verified.')
                self.identity=before;self.cached=result
                return result
            except FileNotFoundError:return Result('missing','missing prerequisite','Required system Calibre tools or runtime files were not found.')
            except (OSError,ValueError,subprocess.SubprocessError,importlib.metadata.PackageNotFoundError) as exc:
                return Result('probe-failed','unavailable','Compatibility check failed ('+type(exc).__name__+'). Recheck the installation.')

service=Service()
def require_compatible():
    result=service.check()
    if not result.verified:raise CompatibilityError(result.message)
    return result

def require_helper_version():
    from calibre.constants import __version__
    if __version__!=SUPPORTED:
        raise CompatibilityError(f'Detected Calibre {__version__}; supported {SUPPORTED}. Protected operation blocked; no library was opened.')
