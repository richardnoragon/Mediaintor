"""Preview, explicit confirmation and restart review for copy-only imports."""
from pathlib import Path
import json
from PyQt6.QtCore import QEventLoop, QTimer, Qt
from PyQt6.QtGui import QStandardItemModel,QStandardItem
from PyQt6.QtWidgets import (QDialog,QVBoxLayout,QHBoxLayout,QPushButton,QLabel,
    QProgressBar,QLineEdit,QFileDialog,QTableWidget,QTableWidgetItem,QComboBox,QMessageBox)
from .imports import ImportWorker
from .import_store import ImportStore, atomic_json, FINAL


class ImportDialog(QDialog):
    def __init__(self,library,folder,parent=None):
        super().__init__(parent)
        self.activity=None
        self.activity_controller=None
        self.library=Path(library);self.store=ImportStore(folder,library)
        self.plan=None;self.batch=None;self.journal=None;self.busy=False;self.running=False;self.stop_requested=False
        self.on_changed=lambda:None
        self.setWindowTitle('Ebook imports — Ready (copy only)');self.resize(1100,650);self.setAcceptDrops(True)
        layout=QVBoxLayout(self);self.status=QLabel('Choose ebook files or a folder, or drop files here. Browse with the picker, or type/paste a full file or folder path below. Originals remain untouched.');self.status.setWordWrap(True);layout.addWidget(self.status)
        self.progress=QProgressBar();self.progress.setRange(0,0);self.progress.setAccessibleName('Import preparation progress');self.progress.hide();layout.addWidget(self.progress)
        bar=QHBoxLayout();layout.addLayout(bar)
        for text,slot in [('Choose ebook files',self.files),('Choose folder and subfolders',self.folder),('Review interrupted imports',self.recovery)]:
            button=QPushButton(text);button.clicked.connect(slot);bar.addWidget(button)
        path_bar=QHBoxLayout();layout.addLayout(path_bar)
        path_label=QLabel('File or folder path:');path_bar.addWidget(path_label)
        self.path_input=QLineEdit();self.path_input.setAccessibleName('File or folder path');path_label.setBuddy(self.path_input);path_bar.addWidget(self.path_input)
        self.path_preview=QPushButton('Preview path');self.path_preview.clicked.connect(self.preview_path);path_bar.addWidget(self.path_preview)
        self.path_input.returnPressed.connect(self.preview_path)
        self.table=QTableWidget(0,5);self.table.setHorizontalHeaderLabels(['Source','Title / Author','Status / Warning','Action','Destination']);layout.addWidget(self.table)
        bar=QHBoxLayout();layout.addLayout(bar)
        self.confirm=QPushButton('Confirm and import copies');self.confirm.setEnabled(False);self.confirm.clicked.connect(self.execute_batch);bar.addWidget(self.confirm)
        for text,slot in [('Stop after current file',self.stop),('Rebuild import preview',self.retry),('Discard pending imports',self.discard_pending),('Close imports',self.close)]:
            button=QPushButton(text);button.clicked.connect(slot);bar.addWidget(button)
        for button in self.findChildren(QPushButton):button.setAutoDefault(False)
        self.choices=[]
        pending=self.store.pending()
        if pending:
            self.journal,self.batch=pending[0];self.render();self.summary()
            self.status.setText('Previous import interrupted. '+self.status.text()+' Nothing resumes automatically.')

    def set_phase(self,phase):
        self.phase=phase;self.setWindowTitle('Ebook imports — '+phase+' (copy only)')

    def request(self,request):
        self.compatibility_blocked=False
        self.busy=True;self.set_phase('Running' if request.get('action')=='execute' else 'Preparing preview');result={};loop=QEventLoop(self)
        worker=ImportWorker(self.library,request,self);self.worker=worker
        self.progress.show();self.progress.repaint()
        worker.progress.connect(self.status.setText)
        worker.result.connect(result.update);worker.failure.connect(lambda msg:result.update(error=msg));worker.finished.connect(loop.quit)
        worker.start();loop.exec();worker.wait();worker.deleteLater();self.busy=False;self.progress.hide()
        self.compatibility_blocked=result.get('compatibility_blocked',False)
        if result.get('error'):self.set_phase('Failed — review required');self.status.setText(result['error']);return None
        return result

    def preview_path(self):
        if self.busy or self.running:return
        text=self.path_input.text().strip()
        path=Path(text).expanduser()
        if not text or not path.is_absolute() or not path.exists():
            self.status.setText('Enter an existing absolute file or folder path, then choose Preview path.');return
        self.preview([str(path)])

    def files(self):
        if self.busy or self.running:return
        paths,_=QFileDialog.getOpenFileNames(self,'Choose ebooks','','Ebooks (*.epub *.mobi *.pdf);;All files (*)')
        if paths:self.preview(paths)

    def folder(self):
        if self.busy or self.running:return
        path=QFileDialog.getExistingDirectory(self,'Choose folder (including subfolders)')
        if path:self.preview([path])

    def dragEnterEvent(self,event):
        if not self.busy and not self.running and event.mimeData().hasUrls():event.acceptProposedAction()

    def dropEvent(self,event):
        if self.busy or self.running:return
        self.preview([u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]);event.acceptProposedAction()

    def preview(self,paths):
        self.status.setText('Validating files and building preview…');self.confirm.setEnabled(False)
        plan=self.request(dict(action='preview',sources=paths))
        if not plan:return
        self.plan=plan;self.batch=None;self.journal=None;self.retry_origin=None;self.render()
        self.preview_status()

    def actionable(self):
        return bool(self.plan) and any(i['state'] not in FINAL|{'invalid'} for i in self.plan['items'])

    def preview_status(self):
        if self.actionable():
            self.set_phase('Preview — confirmation required');self.status.setText('Preview ready. Review warnings and choose destinations explicitly. No files have been imported.')
        else:
            self.set_phase('Preview — nothing to import');self.status.setText('No importable changes: all files are duplicates, skipped, or invalid. No files have been imported.')

    def render(self):
        plan=self.plan or self.batch
        if not plan:return
        self.progress.show();self.progress.repaint()
        old_model=getattr(self,'destination_model',None)
        self.destination_model=QStandardItemModel(self)
        empty=QStandardItem('Choose destination…');self.destination_model.appendRow(empty)
        for record in (self.plan or {}).get('records',[]):
            entry=QStandardItem(record['title']+' — '+', '.join(record['authors'])+' ['+', '.join(record['formats'])+']')
            entry.setData(record,Qt.ItemDataRole.UserRole);self.destination_model.appendRow(entry)
        self.table.setUpdatesEnabled(False)
        self.table.setRowCount(0);self.table.setRowCount(len(plan['items']));self.choices=[]
        for row,item in enumerate(plan['items']):
            for col,text in enumerate([item['source'],item.get('title','')+' / '+', '.join(item.get('authors',[])),item['state']+': '+item.get('warning','')]):
                cell=QTableWidgetItem(text);cell.setFlags(cell.flags() & ~Qt.ItemFlag.ItemIsEditable);self.table.setItem(row,col,cell)
            action=QComboBox();action.addItems(['Create new book','Attach to existing book','Skip'])
            if item.get('similar'):
                action.insertItem(0,'Choose action…');action.setCurrentIndex(0)
            destination=QComboBox();destination.setModel(self.destination_model)
            editable=bool(self.plan) and item['state'] not in FINAL|{'invalid'}
            if item.get('action')=='attach':
                action.setCurrentText('Attach to existing book')
                for idx in range(1,destination.count()):
                    if destination.itemData(idx)['uuid']==item.get('destination_uuid'):destination.setCurrentIndex(idx)
            if item.get('action')=='new' and (not self.plan or not item.get('similar')):action.setCurrentText('Create new book')
            if item['state'] in {'duplicate','discarded','invalid'}:
                action.clear();action.addItem({'duplicate':'Skipped — identical file','discarded':'Skipped','invalid':'Not importable'}[item['state']])
            action.setEnabled(editable);destination.setEnabled(editable and action.currentText()=='Attach to existing book')
            def update_choice(_=None,row=row,item=item,action=action,destination=destination,editable=editable):
                choice=action.currentText()
                destination.setEnabled(editable and choice=='Attach to existing book')
                warning=item.get('warning','')
                if choice!='Choose action…':
                    warning=warning.replace('Similar existing title: choose an action.', 'Similar existing title; selected action: '+choice+'.')
                self.table.item(row,2).setText(item['state']+': '+warning)
            action.currentTextChanged.connect(update_choice)
            update_choice()
            self.table.setCellWidget(row,3,action);self.table.setCellWidget(row,4,destination);self.choices.append((action,destination))
        for col,width in enumerate((300,240,340,210,260)):self.table.setColumnWidth(col,width)
        self.table.setUpdatesEnabled(True)
        if old_model:old_model.deleteLater()
        self.progress.hide();self.confirm.setEnabled(self.actionable() and not self.running)

    def execute_batch(self):
        if self.busy or self.running or not self.actionable():return
        for item,(action,destination) in zip(self.plan['items'],self.choices):
            if item['state'] in FINAL or item['state']=='invalid':continue
            choice=action.currentText()
            if choice=='Choose action…':self.status.setText('Choose an action for every similar-title item.');return
            if choice=='Skip':item['state']='discarded';continue
            if choice=='Attach to existing book':
                record=destination.currentData()
                if not record:self.status.setText('Choose an explicit destination for each attachment.');return
                if item['format'] in record['formats']:self.status.setText('Destination already has this format. Choose a different action; no overwrite is allowed.');return
                item.update(action='attach',destination=record['id'],destination_uuid=record['uuid'],missing=[])
            else:item.update(action='new',destination=None);item.pop('destination_uuid',None)
        if getattr(self,'retry_origin',None):
            self.journal=self.retry_origin
            self.batch=json.loads(self.journal.read_text())
            self.batch['items']=[i for i in self.batch['items'] if i['state'] in FINAL]+self.plan['items']
            self.batch['catalog_token']=self.plan['catalog_token']
            atomic_json(self.journal,self.batch);self.retry_origin=None
        else:self.journal,self.batch=self.store.create(self.plan)
        self.plan=None
        self.running=True;self.stop_requested=False;self.confirm.setEnabled(False)
        from uuid import uuid4
        activity_attempt=str(uuid4())
        if self.activity:self.activity.batch(self.batch,self.journal,'import',running=True,attempt_id=activity_attempt)
        for index,item in enumerate(self.batch['items']):
            if self.stop_requested:break
            if item['state'] in FINAL or item['state']=='invalid':continue
            self.status.setText(f'Importing {index+1}/{len(self.batch["items"])}; Stop finishes this item before pausing.')
            response=self.request(dict(action='execute',journal=str(self.journal),index=index,library_uuid=self.batch['library_uuid']))
            self.batch=json.loads(self.journal.read_text())
            if response is None and self.compatibility_blocked:
                self.stop_requested=True
                break
            if response is None:
                failed=self.batch['items'][index]
                failed['state']='unverified' if failed['state']=='in-flight' else 'failed'
                failed['warning']=self.status.text();atomic_json(self.journal,self.batch)
            self.render()
        self.running=False;self.render();self.summary()
        if self.activity:self.activity.batch(self.batch,self.journal,'import',interrupted=self.stop_requested,attempt_id=activity_attempt)
        self.on_changed()

    def summary(self):
        if self.batch:
            completed=sum(i['state']=='complete' for i in self.batch['items']);pending=sum(i['state'] not in FINAL for i in self.batch['items'])
            self.set_phase('Completed' if not pending else 'Interrupted' if self.stop_requested else 'Incomplete — review required')
            self.status.setText(f'Completed: {completed}; Pending/failed: {pending}. Review results; Rebuild import preview requires a new confirmation. Original files retained.')

    def stop(self):
        self.stop_requested=True
        if self.running:self.set_phase('Stopping after current file');self.status.setText('Stop requested. Verifying the current item; remaining items will be retained.')

    def recovery(self):
        if self.busy or self.running:return
        batches=self.store.pending()
        if not batches:self.status.setText('No unfinished imports.');return
        from PyQt6.QtWidgets import QInputDialog
        labels=[p.stem for p,b in batches]
        selected,ok=QInputDialog.getItem(self,'Review interrupted imports','Batch',labels,0,False)
        if not ok:return
        self.review_batch(batches[labels.index(selected)][0])

    def review_batch(self, path):
        if self.busy or self.running:return False
        matches=[(p,b) for p,b in self.store.batches() if p.resolve()==Path(path).resolve()]
        if not matches:raise ValueError('Selected import journal is unavailable.')
        self.journal,self.batch=matches[0];self.plan=None;self.retry_origin=None
        for index,item in enumerate(self.batch['items']):
            if item['state'] not in FINAL:
                if self.request(dict(action='reconcile',journal=str(self.journal),index=index,library_uuid=self.batch['library_uuid'])) is None:
                    return False
        self.batch=json.loads(self.journal.read_text());self.render();self.summary()
        if self.activity_controller:self.activity_controller.reviewed_batch(self.batch,self.journal,'import')
        return True

    def retry(self):
        if self.busy or self.running:return
        if not self.batch:
            if self.plan:self.preview([i['source'] for i in self.plan['items']]);return
            self.recovery();return
        # Reconcile first. Preserve operation UUIDs so metadata-only records are repaired.
        oldpath=self.journal
        if not self.review_batch(oldpath):return
        for index,item in enumerate(self.batch['items']):
            if item['state'] not in FINAL:self.request(dict(action='reconcile',journal=str(oldpath),index=index,library_uuid=self.batch['library_uuid']))
        old=json.loads(oldpath.read_text());pending=[i for i in old['items'] if i['state'] not in FINAL]
        response=self.request(dict(action='preview',sources=[i['source'] for i in pending]))
        if not response:return
        prior={i['source']:i for i in pending}
        for item in response['items']:
            earlier=prior[item['source']]
            for key in ['operation_uuid','destination','destination_uuid','action']: 
                if key in earlier:item[key]=earlier[key]
        # Keep old work pending until the user explicitly confirms the refreshed plan.
        self.plan=response;self.batch=old;self.journal=oldpath;self.retry_origin=oldpath;self.render()
        self.set_phase('Preview — confirmation required');self.status.setText('Retry preview rebuilt. Review changed inputs/destinations and confirm before continuing.')

    def discard_pending(self):
        if self.busy or self.running or not self.batch:return
        if self.activity_controller:
            record=self.activity_controller.batch_record(self.batch,self.journal,'import')
            self.activity_controller.perform('discard',record['id']);return
        if QMessageBox.question(self,'Discard pending imports?','Completed imports and original files will be retained. Discard only pending work?',QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)!=QMessageBox.StandardButton.Yes:return
        for item in self.batch['items']:
            if item['state'] not in FINAL:item['state']='discarded'
        atomic_json(self.journal,self.batch);self.plan=None;self.render();self.summary()
        if self.activity:self.activity.batch(self.batch,self.journal,'import')

    def closeEvent(self,event):
        if self.busy or self.running:
            self.stop();event.ignore()
        else:event.accept()

    def reject(self):
        if self.busy or self.running:self.stop()
        else:super().reject()
