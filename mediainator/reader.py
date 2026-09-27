"""One detached owned reader with version-bound handled close and restart identity."""
import os
import signal
import re
from pathlib import Path
import subprocess
from .library import check_library, local_path


class ReaderError(Exception):
    pass


def identity(pid):
    """Linux process start time protects against PID reuse."""
    try:
        text = Path(f'/proc/{pid}/stat').read_text()
        tail = text[text.rfind(')') + 2:].split()
        if tail[0] == 'Z':
            return None
        return tail[19]
    except (OSError, IndexError):
        return None


def external_readers(include_calibre=False):
    names = {'ebook-viewer'} | ({'calibre', 'calibre-server', 'calibredb'} if include_calibre else set())
    found = []
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():
            continue
        try:
            if proc.stat().st_uid == os.getuid() and (proc / 'comm').read_text().strip() in names and identity(int(proc.name)):
                found.append(int(proc.name))
        except OSError:
            continue
    return found


class Reader:
    def __init__(self, state, save, live=False, log_dir=None):
        self.state, self.save = state, save
        self.child = None
        self.live = live
        self.log_dir = log_dir

    def active(self):
        if self.child is not None:
            self.child.poll()  # Reap a completed child without waiting.
        record = self.state.get('reader')
        return bool(record and identity(record['pid']) == record['start_time'])

    def launch(self, root, path, resume=None):
        if self.active():
            raise ReaderError('A reader is already open. Close it before opening another book.')
        if self.live and external_readers(include_calibre=True):
            raise ReaderError('Calibre or an external reader is open. It remains externally owned; close it before launching a hub reader in M1.')
        root = Path(root).resolve(strict=True) if self.live else check_library(root)
        path = local_path(root, str(path))
        if not path.is_file():
            raise ReaderError('This format file is missing. Reconnect its drive or restore the file through Calibre, then reload the catalog and retry.')
        from .compatibility import require_compatible, CompatibilityError
        try:require_compatible()
        except CompatibilityError as exc:raise ReaderError(str(exc)) from exc
        if not self.save():
            raise ReaderError('Save the hub settings successfully before opening a reader.')
        env = dict(os.environ)
        env.pop('CALIBRE_OVERRIDE_DATABASE_PATH', None)
        if not self.live:
            env['CALIBRE_CONFIG_DIRECTORY'] = str(root.parent / 'viewer-config')
        else:
            env.pop('CALIBRE_CONFIG_DIRECTORY', None)
        log_path = Path(self.log_dir) / 'viewer.log' if self.log_dir else root.parent / 'viewer.log'
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open('ab') as log:
            extra = resume() if resume else []
            if extra and (len(extra) != 2 or extra[0] != '--open-at'):
                raise ReaderError('Invalid resume request')
            child = subprocess.Popen(['/usr/bin/ebook-viewer', '--new-instance', *extra, str(path)], env=env,
                                     stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)
        self.child = child
        start = identity(child.pid)
        if start is None:
            raise ReaderError(f'Reader exited during launch. See {log_path}')
        self.state['reader'] = {'pid': child.pid, 'start_time': start, 'file': str(path),
                                'profile_id': self.state['profile_id'], 'module': 'bookinator'}
        if not self.save():
            raise ReaderError('Reader started, but its ownership could not be saved. Close the reader before restarting the hub.')

    def request_close(self):
        """Request the installed version's handled close; caller polls asynchronously."""
        if not self.active():
            return
        try:
            version = subprocess.run(['/usr/bin/ebook-viewer', '--version'], capture_output=True,
                                     text=True, timeout=5)
        except subprocess.TimeoutExpired as exc:
            raise ReaderError('Calibre version check timed out. Close the reader manually or retry.') from exc
        if version.returncode or not re.search(r'(?<![0-9.])9\.2\.1(?![0-9.])', version.stdout):
            raise ReaderError('Automatic close is unverified for this Calibre version. Close the reader manually, Retry, or leave it open.')
        record = self.state['reader']
        fd = os.pidfd_open(record['pid'])
        try:
            args = Path(f"/proc/{record['pid']}/cmdline").read_bytes().split(b'\0')
            if identity(record['pid']) != record['start_time'] or record['file'].encode() not in args or not any(b'ebook-viewer' in a for a in args):
                raise ReaderError('Reader identity could not be verified. Close it manually.')
            signal.pidfd_send_signal(fd, signal.SIGTERM)
        finally:
            os.close(fd)
