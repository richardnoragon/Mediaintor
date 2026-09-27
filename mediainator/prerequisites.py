"""Non-modal first-run guidance and asynchronous compatibility checks."""
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QWidget,QVBoxLayout,QLabel,QPushButton
from .compatibility import service

class CheckWorker(QThread):
    checked=pyqtSignal(object)
    def run(self):self.checked.emit(service.check(force=True))

class Prerequisites(QWidget):
    def __init__(self,hub):
        super().__init__(hub);self.hub=hub;self.worker=None;self.result=None
        layout=QVBoxLayout(self)
        self.guide=QLabel('First run: install Calibre 9.2.1 separately, close Calibre and readers, then select the existing library folder containing metadata.db. Browsing uses a private copy; books open from their original locations. No library is created or imported by setup.')
        self.guide.setWordWrap(True);layout.addWidget(self.guide)
        self.status=QLabel('Checking prerequisites…');self.status.setWordWrap(True);layout.addWidget(self.status)
        self.choose=QPushButton('Choose existing Calibre library');self.choose.setEnabled(False)
        self.choose.clicked.connect(hub.choose_library);layout.addWidget(self.choose)
        self.recheck=QPushButton('Recheck prerequisites');self.recheck.clicked.connect(self.check);layout.addWidget(self.recheck)
        help=QLabel('Calibre is managed separately. Installation guidance: <a href="https://calibre-ebook.com/download_linux">official Calibre Linux instructions</a>. Do not replace your installed version without checking the supported version above. Local Activity and emergency preservation remain available when library operations are blocked.')
        help.setWordWrap(True);help.setOpenExternalLinks(True);layout.addWidget(help)
    def check(self):
        if self.hub.closing or (self.worker and self.worker.isRunning()):return
        self.recheck.setEnabled(False);self.status.setText('Checking prerequisites…')
        self.worker=CheckWorker(self);self.worker.checked.connect(self.checked)
        self.worker.finished.connect(lambda:self.recheck.setEnabled(True));self.worker.start()
    def checked(self,result):
        if self.hub.closing:return
        self.result=result;self.status.setText(result.message);self.choose.setEnabled(result.verified)
        if self.hub.bookinator:self.hub.bookinator.set_compatibility(result)
        # Do not replay a blocked request or resume pending work on Recheck.
        if self.hub.initial_books_pending:
            self.hub.initial_books_pending=False
            if result.verified and self.hub.bookinator and self.hub.bookinator.loader:
                self.hub.bookinator.loader.load()
        if not result.verified and self.hub.bookinator:
            self.hub.bookinator.note.setText('Catalog may be stale. '+result.message)
    def shutdown(self):
        if self.worker and self.worker.isRunning():self.worker.wait()
