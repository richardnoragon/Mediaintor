"""Frozen diagnostic preview with explicit local export; no upload control."""
from PyQt6.QtWidgets import QDialog,QVBoxLayout,QLabel,QPlainTextEdit,QPushButton,QHBoxLayout,QFileDialog
from .diagnostics import collect_snapshot,write_snapshot

class DiagnosticsDialog(QDialog):
    def __init__(self,hub):
        super().__init__(hub);self.setWindowTitle('Preview redacted diagnostics');self.resize(800,620)
        checked=hub.prerequisites.result if hub.prerequisites else None
        self.snapshot=collect_snapshot({'bookinator_open':hub.bookinator is not None,
            'library_configured':hub.library is not None,'activity_visible':hub.activity_panel.isVisible(),
            'recovery_enabled':True},checked.state if checked else None,checked.detected if checked else None)
        layout=QVBoxLayout(self)
        notice=QLabel('Review the exact JSON that will be exported. Only sanitized current-session events are included. Book data, paths, library names, raw logs and recovery contents are always excluded. Nothing is uploaded. Close and reopen to capture a new snapshot.')
        notice.setWordWrap(True);layout.addWidget(notice)
        self.preview=QPlainTextEdit();self.preview.setReadOnly(True);self.preview.setAccessibleName('Exact diagnostic export preview')
        self.preview.setPlainText(self.snapshot.payload.decode('utf-8'));layout.addWidget(self.preview)
        self.status=QLabel('No export has been written.');self.status.setWordWrap(True);layout.addWidget(self.status)
        bar=QHBoxLayout();export=QPushButton('Export JSON…');export.clicked.connect(self.export);bar.addWidget(export)
        cancel=QPushButton('Close');cancel.clicked.connect(self.close);bar.addWidget(cancel);layout.addLayout(bar)
    def export(self):
        name,_=QFileDialog.getSaveFileName(self,'Export redacted diagnostics','mediainator-diagnostics.json','JSON (*.json)')
        if not name:
            self.status.setText('Export cancelled. No file was written.');return
        try:write_snapshot(name,self.snapshot)
        except (OSError,ValueError):
            self.status.setText('Export failed. Check destination permissions and free space, or choose another regular file location. The preview is unchanged; you can retry.');return
        self.status.setText('The previewed diagnostics were exported locally. Nothing was uploaded.')
