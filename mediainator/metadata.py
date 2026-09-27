"""Asynchronous isolated metadata reads and explicit Calibre writes."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
from PyQt6.QtCore import QThread, pyqtSignal
from .reader import external_readers
from .snapshot import Snapshot


def run_request(root, request, recovery_dir):
    from .compatibility import require_compatible
    require_compatible()
    if external_readers(include_calibre=True):
        raise RuntimeError('Waiting for library access: close Calibre and all readers, then Retry.')
    request = dict(request, library=str(root), recovery_dir=str(recovery_dir))
    with tempfile.TemporaryDirectory(prefix='mediainator-metadata-') as folder:
        folder = Path(folder)
        inp, out = folder/'request.json', folder/'response.json'
        inp.write_text(json.dumps(request))
        env = dict(os.environ, QT_QPA_PLATFORM='offscreen', CALIBRE_CONFIG_DIRECTORY=str(folder/'config'))
        env.pop('CALIBRE_OVERRIDE_DATABASE_PATH', None)
        command = ['/usr/bin/calibre-debug', '-e', str(Path(__file__).with_name('calibre_metadata_helper.py')), '--', str(inp), str(out)]
        # Do not kill a writer mid-commit. A slow write keeps its worker and draft alive.
        result = subprocess.run(command, env=env, capture_output=True, timeout=60 if request['action'] in ('read', 'bulk_read') else None)
        if result.returncode or not out.exists():
            raise RuntimeError('Metadata result unverified. Keep the draft and Retry to re-read current values. ' + result.stderr.decode(errors='replace')[-500:])
        response = json.loads(out.read_text())
        if response.get('error'):
            raise RuntimeError(response['error'])
        return response


class MetadataWorker(QThread):
    result = pyqtSignal(object)
    failure = pyqtSignal(str)

    def __init__(self, root, request, recovery_dir, parent=None):
        super().__init__(parent)
        self.root, self.request, self.recovery_dir = Path(root), request, recovery_dir

    def run(self):
        snapshot = None
        try:
            root = self.root
            if self.request['action'] in ('read', 'bulk_read'):
                if external_readers(include_calibre=True):
                    raise RuntimeError('Waiting for library access: close Calibre and all readers.')
                snapshot = Snapshot(root).create(self.isInterruptionRequested)
                root = snapshot.root
            self.result.emit(run_request(root, self.request, self.recovery_dir))
        except Exception as exc:
            from .diagnostics import record_error
            record_error('metadata-failure',exc)
            self.failure.emit(str(exc))
        finally:
            if snapshot:
                snapshot.close()
