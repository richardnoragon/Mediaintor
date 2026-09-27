"""Explicit asynchronous scans; immutable results, no modification actions."""
from PyQt6.QtCore import QThread,pyqtSignal,QAbstractTableModel,QModelIndex,Qt
from PyQt6.QtWidgets import QDialog,QVBoxLayout,QHBoxLayout,QPushButton,QLabel,QProgressBar,QTableView
from .duplicate_scan import scan_library

class DuplicateWorker(QThread):
    result=pyqtSignal(object);progress=pyqtSignal(str);failure=pyqtSignal(str)
    def __init__(self,root,books,missing_titles):
        super().__init__();self.root=root;self.books=tuple(books);self.missing_titles=missing_titles
    def run(self):
        try:self.result.emit(scan_library(self.root,self.books,self.isInterruptionRequested,self.progress.emit,self.missing_titles))
        except (OSError,ValueError) as exc:self.failure.emit(str(exc))

class DuplicateModel(QAbstractTableModel):
    def __init__(self,parent):super().__init__(parent);self.rows=[]
    def replace(self,rows):self.beginResetModel();self.rows=rows;self.endResetModel()
    def rowCount(self,parent=QModelIndex()):return 0 if parent.isValid() else len(self.rows)
    def columnCount(self,parent=QModelIndex()):return 5
    def headerData(self,n,orientation,role=Qt.ItemDataRole.DisplayRole):
        if orientation==Qt.Orientation.Horizontal and role==Qt.ItemDataRole.DisplayRole:return ['Category / group','Title','Author','Book UUID','Evidence / path'][n]
    def data(self,i,role=Qt.ItemDataRole.DisplayRole):
        if i.isValid() and role in (Qt.ItemDataRole.DisplayRole,Qt.ItemDataRole.ToolTipRole):return self.rows[i.row()][i.column()]

class DuplicateDialog(QDialog):
    def __init__(self,host):
        super().__init__(host);self.host=host;self.worker=None;self.stale=False;self.closing=False;self.scan_catalog=None;self.scan_inventory=None
        self.setWindowTitle('Library duplicate review — read only');self.resize(1100,700)
        layout=QVBoxLayout(self);self.status=QLabel('Start a scan of books already in this library. Similar means matching normalized title and author; review each match.');self.status.setWordWrap(True);layout.addWidget(self.status)
        self.load_notice=QLabel('Library loading — no new scan has started. When loading finishes, click Scan library.');self.load_notice.setWordWrap(True);self.load_notice.hide();layout.addWidget(self.load_notice)
        self.progress=QProgressBar();self.progress.setRange(0,0);self.progress.hide();layout.addWidget(self.progress)
        self.table=QTableView();self.model=DuplicateModel(self);self.table.setModel(self.model)
        for i,width in enumerate((155,220,180,270,440)):self.table.setColumnWidth(i,width)
        layout.addWidget(self.table);bar=QHBoxLayout();layout.addLayout(bar)
        self.start=QPushButton('Scan library');self.start.clicked.connect(self.scan);bar.addWidget(self.start)
        self.cancel=QPushButton('Cancel scan');self.cancel.clicked.connect(self.cancel_scan);self.cancel.setEnabled(False);bar.addWidget(self.cancel)
        close=QPushButton('Close duplicate review');close.clicked.connect(self.close);bar.addWidget(close)
        for b in self.findChildren(QPushButton):b.setAutoDefault(False)
        self.library_loading(bool(self.host.loader and self.host.loader.active))
    def scan(self):
        if self.worker:return
        if self.host.loader and self.host.loader.active:self.library_loading(True);return
        try:
            from .discovery import DiscoveryIndex
            _,state,warnings=self.host.discovery_context();index=DiscoveryIndex(self.host.books,state,warnings)
        except (OSError,ValueError) as exc:self.status.setText('Scan unavailable: '+str(exc));return
        self.scan_catalog=tuple(self.host.books)
        inventory=getattr(getattr(self.host.loader,'snapshot',None),'source_inventory',None)
        self.scan_inventory=dict(inventory) if inventory is not None else None
        self.stale=False;self.closing=False;self.model.replace([]);self.start.setEnabled(False);self.cancel.setEnabled(True);self.progress.show()
        missing={b.uuid for b in self.host.books if 'Missing title' in index.reasons.get(b.uuid,())}
        worker=DuplicateWorker(self.host.library,self.host.books,missing);self.worker=worker
        worker.progress.connect(self.show_progress);worker.result.connect(self.result);worker.failure.connect(lambda message:self.status.setText('Scan incomplete: '+message));worker.finished.connect(self.finished);worker.start()
    def library_loading(self,active):
        # Keep loading feedback separate from the evidence status, including cancellation/staleness.
        self.load_notice.setVisible(active)
        self.start.setEnabled(not active and self.worker is None)
    def show_progress(self,message):
        if not self.stale and not self.closing:self.status.setText(message)
    def catalog_refreshed(self):
        if self.scan_catalog is None:return
        inventory=getattr(getattr(self.host.loader,'snapshot',None),'source_inventory',None)
        if self.scan_inventory is not None and inventory==self.scan_inventory and tuple(self.host.books)==self.scan_catalog:return
        self.invalidate()
    def cancel_scan(self):
        if self.worker:self.worker.requestInterruption();self.status.setText('Cancelling scan…')
    def result(self,result):
        if self.closing:return
        rows=[]
        for category in ('exact','similar'):
            for n,group in enumerate(result[category],1):
                for book in group['books']:
                    evidence=(group['format']+' SHA-256 '+group['sha256']+' · '+book['path']) if category=='exact' else 'Normalized title and author match; potential duplicate only'
                    rows.append((category.title()+f' {n}',book['title'],book['author'],book['uuid'],evidence))
        for row in result['errors']:rows.append(('Uncertain','','','',row['path']+': '+row['error']))
        self.model.replace(rows)
        status='Cancelled — incomplete' if result['cancelled'] else 'Finished with errors — incomplete' if result['errors'] else 'Scan complete'
        if self.stale:status='Stale catalog — rescan required'
        self.status.setText(f"{status}. {len(result['exact'])} identical-content groups; {len(result['similar'])} potential title/author groups; {len(result['errors'])} errors. No books changed.")
    def invalidate(self):
        self.stale=True;self.cancel_scan();self.status.setText('Library changed or could not be verified unchanged — displayed results are stale; start another scan.')
    def finished(self):
        worker=self.worker;self.worker=None
        if worker:worker.deleteLater()
        self.library_loading(bool(self.host.loader and self.host.loader.active));self.cancel.setEnabled(False);self.progress.hide()
    def shutdown(self):
        self.closing=True
        if self.worker:self.worker.requestInterruption();self.worker.wait()
    def closeEvent(self,event):self.shutdown();event.accept()
