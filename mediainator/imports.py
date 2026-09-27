"""Background import planning/execution; every execution follows a confirmed preview."""
import json, os, subprocess, tempfile
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal
from .reader import external_readers
from .snapshot import Snapshot
from .import_store import discover


def call_helper(request):
    from .compatibility import require_compatible
    require_compatible()
    if external_readers(include_calibre=True):raise RuntimeError('Waiting for library access: close Calibre and readers.')
    with tempfile.TemporaryDirectory(prefix='mediainator-import-request-') as temp:
        temp=Path(temp);inp=temp/'input.json';out=temp/'output.json';inp.write_text(json.dumps(request))
        env=dict(os.environ,QT_QPA_PLATFORM='offscreen',CALIBRE_CONFIG_DIRECTORY=str(temp/'config'))
        env.pop('CALIBRE_OVERRIDE_DATABASE_PATH',None)
        result=subprocess.run(['/usr/bin/calibre-debug','-e',str(Path(__file__).with_name('calibre_import_helper.py')),'--',str(inp),str(out)],env=env,capture_output=True)
        if result.returncode or not out.exists():raise RuntimeError('Import result unverified; use Review/Retry to reconcile. '+result.stderr.decode(errors='replace')[-500:])
        response=json.loads(out.read_text())
        if response.get('error'):raise RuntimeError(response['error'])
        return response


class ImportWorker(QThread):
    result=pyqtSignal(object)
    failure=pyqtSignal(str)
    progress=pyqtSignal(str)

    def __init__(self,root,request,parent=None):
        super().__init__(parent);self.root=Path(root);self.request=request

    def run(self):
        snapshot=None
        try:
            request=dict(self.request)
            if request['action']=='preview':
                if external_readers(include_calibre=True):raise RuntimeError('Waiting for library access: close Calibre and readers.')
                self.progress.emit('Finding files in the selected paths… No files are being imported.')
                request['sources']=discover(request['sources'])
                self.progress.emit(f'Found {len(request["sources"])} files. Preparing a private library copy…')
                snapshot=Snapshot(self.root).create(self.isInterruptionRequested)
                request['library']=str(snapshot.root)
            else:request['library']=str(self.root)
            if request['action']=='preview':self.progress.emit(f'Validating {len(request["sources"])} files and checking duplicates… No files are being imported.')
            self.result.emit(call_helper(request))
        except Exception as exc:
            from .diagnostics import record_error
            record_error('import-failure',exc)
            from .compatibility import CompatibilityError
            if isinstance(exc,CompatibilityError):self.result.emit(dict(error=str(exc),compatibility_blocked=True))
            else:self.failure.emit(str(exc))
        finally:
            if snapshot:snapshot.close()
