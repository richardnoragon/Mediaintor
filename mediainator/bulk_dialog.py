"""Mandatory review, conflict choices, durable recovery and batch revert UI."""
from copy import deepcopy
from PyQt6.QtCore import Qt, QEventLoop, QTimer
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QPushButton,
    QComboBox, QLineEdit, QListWidget, QAbstractItemView, QTableWidget, QTableWidgetItem,
    QMessageBox, QDialogButtonBox, QWidget, QTabWidget)
from .bulk import BulkStore, OPERATIONS, FINAL, plan, reconcile, revert_plan, remaining
from .bulk_worker import BulkWorker
from .editor import Entries


class BulkDialog(QDialog):
    def __init__(self, library, folder, books, parent=None):
        super().__init__(parent)
        self.activity=None
        self.activity_controller=None
        self.store = BulkStore(folder, library)
        self.books = {b.uuid: b for b in books}
        self.batch = None; self.busy = False; self.worker = None
        self.on_changed = lambda: None
        self.setWindowTitle('Bulk metadata — Ready'); self.resize(1050, 780)
        self.phase='Ready'; self.view_index=0; self.views=[]
        layout = QVBoxLayout(self)
        self.tabs=QTabWidget();layout.addWidget(self.tabs)
        self.pages=[]
        for name in ('New Bulk Edit','Batch History'):
            page=QWidget();box=QVBoxLayout(page);self.tabs.addTab(page,name);self.pages.append(box)
        self.settings = settings = QWidget(self); form = QFormLayout(settings); self.form=form;self.pages[0].addWidget(settings)
        selection=QLabel(f'{len(books)} selected books, including any hidden by catalog filters.');selection.setWordWrap(True);form.addRow(selection)
        self.operation = QComboBox(); self.operation.addItems(OPERATIONS); form.addRow('Operation', self.operation)
        self.tags = Entries(False); form.addRow('Tags', self.tags); self.tag_buttons=self.tags.buttons();form.addRow(self.tag_buttons)
        self.old_author = QLineEdit(); self.new_author = QLineEdit()
        form.addRow('Exact author to replace', self.old_author); form.addRow('Replacement author', self.new_author)
        self.series = QLineEdit(); form.addRow('Series', self.series)
        self.mode = QComboBox(); self.mode.addItems(['Keep existing', 'Fixed', 'Sequential']); form.addRow('Number mode', self.mode)
        self.fixed = QLineEdit('1'); self.start = QLineEdit('1'); self.increment = QLineEdit('1')
        form.addRow('Fixed number', self.fixed); form.addRow('Starting number', self.start); form.addRow('Increment', self.increment)
        self.order = QListWidget(); self.order.setMaximumHeight(110)
        self.order.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        for book in books:
            from PyQt6.QtWidgets import QListWidgetItem
            item = QListWidgetItem(book.title+' — '+book.author); item.setData(Qt.ItemDataRole.UserRole, book.uuid); self.order.addItem(item)
        form.addRow('Sequence order (drag to arrange)', self.order)
        orderbar = QHBoxLayout()
        for title, direction in [('Move up', -1), ('Move down', 1)]:
            button = QPushButton(title); button.clicked.connect(lambda _, d=direction: self.move(d)); orderbar.addWidget(button)
        form.addRow(orderbar)
        self.preview_button = QPushButton('Build preview'); self.preview_button.clicked.connect(self.preview); form.addRow(self.preview_button)
        self.history = QComboBox();self.history.setAccessibleName('Selected batch history record')
        self.pages[1].addWidget(self.history)
        self.history_summary=QLabel('Select a batch to inspect its recorded outcome.');self.history_summary.setWordWrap(True)
        self.pages[1].addWidget(self.history_summary)
        self.links=QComboBox();self.links.setAccessibleName('Related batch records')
        linkbar=QHBoxLayout();linkbar.addWidget(self.links)
        self.view_related=QPushButton('View related batch');self.view_related.clicked.connect(self.navigate_related);linkbar.addWidget(self.view_related)
        self.pages[1].addLayout(linkbar)
        self.history_actions=[]
        for label,slot in [('Review pending changes',self.review),('Preview revert of selected batch',self.revert),('Discard selected batch pending work',self.discard),('Delete selected batch history',self.delete_history)]:
            button=QPushButton(label);button.clicked.connect(slot);self.pages[1].addWidget(button);self.history_actions.append(button)
        for box in self.pages:
            status=QLabel('Choose settings and build a preview.' if box is self.pages[0] else 'Select a batch. No work resumes automatically.');status.setWordWrap(True);box.addWidget(status)
            table=QTableWidget(0,5);table.setHorizontalHeaderLabels(['Include','Book','Current values','Proposed values','Status']);table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers);box.addWidget(table,1)
            bar=QHBoxLayout();box.addLayout(bar)
            confirm=QPushButton('Confirm bulk changes');confirm.clicked.connect(self.execute);confirm.setEnabled(False);bar.addWidget(confirm)
            back=QPushButton('Edit bulk settings');back.clicked.connect(self.back);bar.addWidget(back)
            stop=QPushButton('Stop after current book');stop.clicked.connect(self.stop);stop.setEnabled(False);bar.addWidget(stop)
            resolve=QPushButton('Review selected conflict');resolve.clicked.connect(self.resolve);bar.addWidget(resolve)
            self.views.append(dict(status=status,table=table,confirm=confirm,back_button=back,stop_button=stop,resolve_button=resolve,batch=None,phase='Ready'))
        self.bind_view(0)
        close=QPushButton('Close bulk editor');close.clicked.connect(self.close);layout.addWidget(close)
        self.tabs.currentChanged.connect(self.change_view)
        self.history.currentIndexChanged.connect(self.history_selected)
        self.operation.currentTextChanged.connect(self.update_controls)
        self.mode.currentTextChanged.connect(self.update_controls)
        self.update_controls()
        self.refresh_history()

    def bind_view(self,index):
        for name in ('status','table','confirm','back_button','stop_button','resolve_button','batch','phase'):
            setattr(self,name,self.views[index][name])
        self.view_index=index

    def change_view(self,index):
        if self.busy or self.phase=='Preview — confirmation required':
            self.tabs.blockSignals(True);self.tabs.setCurrentIndex(self.view_index);self.tabs.blockSignals(False);return
        self.views[self.view_index].update(batch=self.batch,phase=self.phase)
        self.bind_view(index);self.set_phase(self.phase)
        if index==1:self.history_selected()

    def set_phase(self,phase):
        self.phase=phase
        name='Revert' if self.batch and self.batch.get('kind')=='revert' else 'Bulk metadata'
        self.setWindowTitle(f'{name} — {phase}')
        locked=self.busy or phase=='Preview — confirmation required'
        for i in range(2):self.tabs.setTabEnabled(i,not locked or i==self.view_index)
        self.history.setEnabled(not locked);self.links.setEnabled(not locked)
        self.view_related.setEnabled(not locked and self.links.count()>0)
        selected=self.selected_history()
        pending=bool(selected and any(i['state'] not in FINAL for i in selected['items']))
        applied=bool(selected and any(i.get('applied') for i in selected['items']))
        for button,eligible in zip(self.history_actions,(pending,applied,pending,bool(selected) and not pending)):
            button.setEnabled(not locked and eligible)
        self.stop_button.setEnabled(self.busy and phase in ('Running','Stopping after current book'))
        self.resolve_button.setEnabled(not self.busy and phase=='Preview — confirmation required')
        self.back_button.setEnabled(not self.busy)
        self.back_button.setText('Cancel revert preview' if self.batch and self.batch.get('kind')=='revert' and phase=='Preview — confirmation required' else 'Edit bulk settings' if self.view_index==0 else 'Return to batch history')
        if self.view_index==0:self.settings.setEnabled(not self.busy and phase in ('Ready','Preview cancelled'))

    def history_ready(self):
        if self.busy or self.phase=='Preview — confirmation required':return False
        self.tabs.setCurrentIndex(1)
        return self.view_index==1

    def describe_history(self):
        self.links.clear()
        batch=self.selected_history()
        if not batch:
            self.history_summary.setText('No batch selected. Select a record before taking an action.');return
        from .feedback import batch_counts
        c=batch_counts(batch)
        self.history_summary.setText(f"Selected batch: {batch['operation']} · {batch['id'][:8]} · {batch['created']}\n"
            +f"{c['completed']} completed · {c['failed']} failed · {c['pending']} pending\n"
            +'Books: '+', '.join(i['title'] for i in batch['items'][:5])+(' …' if len(batch['items'])>5 else ''))
        batches=self.store.batches();ids={b['id'] for b in batches}
        if batch.get('original'):
            original=batch['original']
            self.history_summary.setText(self.history_summary.text()+f"\nRevert of: {original[:8]}"+(' (history unavailable)' if original not in ids else ''))
            if original in ids:self.links.addItem('View original batch '+original[:8],original)
        for child in batches:
            if child.get('original')==batch['id']:
                counts=batch_counts(child);outcome='completed' if not any(counts[k] for k in ('pending','failed','excluded','discarded')) else 'incomplete or partly excluded'
                self.links.addItem(f"View revert {child['id'][:8]} ({outcome})",child['id'])
        self.history_summary.setText(self.history_summary.text()+'\nLinked results describe recorded operations; later metadata changes are not undone automatically.')

    def history_selected(self,*_):
        if self.busy or self.phase=='Preview — confirmation required':return
        self.describe_history()
        if self.view_index==1:
            self.batch=self.selected_history()
            if self.batch:self.render('history')
            else:self.table.setRowCount(0);self.confirm.setEnabled(False);self.set_phase('Ready')

    def navigate_related(self):
        if not self.history_ready():return
        index=self.history.findData(self.links.currentData())
        if index>=0:self.history.setCurrentIndex(index)

    def update_controls(self):
        operation = self.operation.currentText()
        tags=operation in ('Add Tags','Remove Tags')
        self.form.setRowVisible(self.tags,tags);self.form.setRowVisible(self.tag_buttons,tags)
        for widget in (self.old_author,self.new_author):self.form.setRowVisible(widget,operation=='Replace Author')
        for widget in (self.series,self.mode):self.form.setRowVisible(widget,operation=='Set Series')
        self.form.setRowVisible(self.fixed,operation=='Set Series' and self.mode.currentText()=='Fixed')
        for widget in (self.start,self.increment):self.form.setRowVisible(widget,operation=='Set Series' and self.mode.currentText()=='Sequential')
        self.tags.setEnabled(tags)
        for widget in (self.old_author, self.new_author): widget.setEnabled(operation == 'Replace Author')
        for widget in (self.series, self.mode): widget.setEnabled(operation == 'Set Series')
        self.fixed.setEnabled(operation == 'Set Series' and self.mode.currentText() == 'Fixed')
        for widget in (self.start, self.increment): widget.setEnabled(operation == 'Set Series' and self.mode.currentText() == 'Sequential')

    def move(self, direction):
        row = self.order.currentRow(); target = row + direction
        if row >= 0 and 0 <= target < self.order.count():
            self.order.insertItem(target, self.order.takeItem(row)); self.order.setCurrentRow(target)

    def options(self):
        return dict(tags=self.tags.values(), old=self.old_author.text(), new=self.new_author.text(), series=self.series.text(),
                    mode=self.mode.currentText(), fixed=self.fixed.text(), start=self.start.text(), increment=self.increment.text())

    def request(self, identities=None, batch=None):
        if self.busy: return None
        self.busy = True; self.confirm.setEnabled(False)
        self.set_phase('Running' if batch else 'Preparing preview')
        result = {}; loop = QEventLoop(self)
        self.worker = BulkWorker(self.store, identities, batch, self)
        self.worker.result.connect(lambda value: result.update(value))
        self.worker.failure.connect(lambda error: result.update(error=error))
        self.worker.progress.connect(self.status.setText)
        self.worker.finished.connect(loop.quit)
        self.worker.start(); loop.exec(); self.worker.wait(); self.worker.deleteLater(); self.worker = None
        self.busy = False
        if 'error' in result:
            self.status.setText(result['error']);self.set_phase('Failed — review required'); return None
        return result

    def identities(self, batch=None):
        if batch: return [dict(book=i['book'], uuid=i['uuid']) for i in batch['items']]
        return [dict(book=int(self.books[self.order.item(i).data(Qt.ItemDataRole.UserRole)].id.rsplit(':', 1)[1]),
                     uuid=self.order.item(i).data(Qt.ItemDataRole.UserRole)) for i in range(self.order.count())]

    def preview(self):
        if self.busy: return
        try:
            identities = self.identities()
            if not identities: raise ValueError('Select books in the catalog before creating a batch.')
            response = self.request(identities)
            if response:
                self.batch = plan(self.store, identities, response, self.operation.currentText(), self.options())
                self.render()
        except (ValueError, OSError) as exc: self.status.setText(str(exc))

    def render(self, phase='preview'):
        self.settings.setEnabled(False)
        self.table.setHorizontalHeaderLabels(['Include','Book','Current values' if phase=='preview' else 'Recorded values','Proposed values','Status'])
        self.table.setRowCount(len(self.batch['items']))
        for row, item in enumerate(self.batch['items']):
            check = QTableWidgetItem(); check.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
            check.setCheckState(Qt.CheckState.Checked if item['state'] not in FINAL else Qt.CheckState.Unchecked)
            self.table.setItem(row, 0, check)
            fields = item['desired']
            current = item.get('current', item['baseline'])
            values = [item['title'], '\n'.join(f'{f}: {current.get(f)}' for f in fields),
                      '\n'.join(f'{f}: {v}' for f, v in fields.items()),
                      item['state'] + (' · '+str(item['errors']) if item.get('errors') else '')]
            for col, value in enumerate(values, 1): self.table.setItem(row, col, QTableWidgetItem(value))
        self.table.resizeColumnsToContents(); self.table.resizeRowsToContents()
        self.confirm.setEnabled(any(i['state'] in ('pending', 'failed') for i in self.batch['items']))
        from .feedback import batch_feedback
        self.confirm.setText('Confirm revert' if self.batch.get('kind')=='revert' else 'Confirm bulk changes')
        self.status.setText(batch_feedback(self.batch, 'preview' if phase=='preview' else 'result'))
        from .feedback import batch_counts
        counts=batch_counts(self.batch)
        if phase=='preview':state='Preview — confirmation required' if counts['pending']+counts['failed'] else 'No changes to apply'
        else:state='Incomplete — review required' if counts['pending']+counts['failed'] else 'Completed'
        if phase!='preview':self.confirm.setEnabled(False)
        self.set_phase(state)

    def back(self):
        if self.busy: return
        from .feedback import batch_feedback
        completed=self.phase=='Completed'
        message=('Results dismissed. Completed changes remain saved in Batch History.' if completed else batch_feedback(self.batch,'cancel') if self.batch else 'No preview open. Choose settings or a history record.')
        self.batch = None; self.table.setRowCount(0); self.confirm.setEnabled(False); self.settings.setEnabled(True)
        self.status.setText(message);self.set_phase('Ready' if completed or self.phase!='Preview — confirmation required' else 'Preview cancelled')

    def execute(self):
        if self.busy or not self.batch or self.phase!='Preview — confirmation required': return
        for row, item in enumerate(self.batch['items']):
            if item['state'] not in FINAL and self.table.item(row, 0).checkState() != Qt.CheckState.Checked:
                item['state'] = 'excluded'
        path=self.store.folder/(self.batch['id']+'.json')
        from uuid import uuid4
        activity_attempt=str(uuid4())
        if self.activity:self.activity.batch(self.batch,path,'bulk',running=True,attempt_id=activity_attempt)
        self.stop_requested=False
        result = self.request(batch=self.batch)
        if result:
            self.batch = result; self.render('result')
            self.confirm.setEnabled(False)
            from .feedback import batch_feedback
            self.status.setText(batch_feedback(self.batch,'interrupted' if self.stop_requested else 'result'))
            if self.stop_requested and any(i['state'] not in FINAL for i in self.batch['items']):self.set_phase('Interrupted')
        else:
            self.confirm.setEnabled(False)
            from .feedback import batch_feedback
            error=self.status.text()
            try:
                import json
                if path.exists():self.batch=json.loads(path.read_text())
                self.status.setText(batch_feedback(self.batch,'failed')+'\n'+error);self.set_phase('Failed — review required')
            except (OSError,ValueError,KeyError,TypeError):
                self.status.setText('Operation result requires verification. History and pending work retained. '+error);self.set_phase('Verification required')
        if self.activity:
            try:
                import json
                if path.exists():self.activity.batch(json.loads(path.read_text()),path,'bulk',attempt_id=activity_attempt)
                else:
                    operation='Batch reverts' if self.batch.get('kind')=='revert' else 'Bulk edits'
                    self.activity.record(operation,self.batch['library']+'\0'+self.batch['id'],outcome='failure',pending=True,
                        details=dict(error=self.status.text(),journal_available=False),attempt_id=activity_attempt)
            except (OSError,ValueError) as exc:self.status.setText('Bulk activity unavailable: '+str(exc))
        self.refresh_history(preferred=self.batch['id']); self.on_changed()

    def stop(self):
        if not self.busy or not self.worker:return
        self.stop_requested=True
        self.set_phase('Stopping after current book')
        if self.worker: self.worker.requestInterruption(); self.status.setText('Stopping after verification of the current book. Pending work will remain available.')

    def refresh_history(self, preferred=None):
        old = preferred or self.history.currentData(); self.history.blockSignals(True);self.history.clear()
        try:
            for batch in self.store.batches():
                pending = sum(i['state'] not in FINAL for i in batch['items'])
                self.history.addItem(f"{batch['created'][:19]} · {batch['operation']} · {pending} pending · {batch['id'][:8]}", batch['id'])
            if old:self.history.setCurrentIndex(self.history.findData(old))
        except (ValueError, OSError) as exc: self.status.setText('History unavailable: '+str(exc))
        finally:self.history.blockSignals(False)
        self.describe_history();self.set_phase(self.phase)

    def selected_history(self):
        return next((b for b in self.store.batches() if b['id'] == self.history.currentData()), None)

    def review(self):
        if not self.history_ready(): return
        try:
            batch = self.selected_history()
            if not batch: return
            response = self.request(self.identities(batch))
            if response:
                self.batch = reconcile(batch, response); self.store.save(self.batch); self.render(); self.refresh_history()
                if self.activity_controller:self.activity_controller.reviewed_batch(self.batch,self.store.folder/(self.batch['id']+'.json'),'bulk')
        except (ValueError, OSError) as exc: self.status.setText(str(exc))

    def resolve(self):
        if self.busy or not self.batch: return
        row = self.table.currentRow()
        if row < 0: return
        item = self.batch['items'][row]
        if item['state'] != 'conflict': return
        dialog = QDialog(self); dialog.setWindowTitle('Review conflicting fields'); layout = QVBoxLayout(dialog)
        choices = {}
        proposed = dict(item['baseline'], **item['desired'])
        for field in item['conflicts']:
            layout.addWidget(QLabel(f"{field}\nCalibre: {item['current'][field]}\nProposed: {proposed[field]}"))
            choice = QComboBox(); choice.addItems(['Use Calibre value', 'Use proposed value']); layout.addWidget(choice); choices[field] = choice
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(buttons); buttons.accepted.connect(dialog.accept); buttons.rejected.connect(dialog.reject)
        if dialog.exec() != QDialog.DialogCode.Accepted: return
        for field, choice in choices.items():
            if choice.currentIndex() == 0: item['desired'].pop(field, None)
            else:
                item['desired'][field] = proposed[field]
                if field not in item.setdefault('force_fields', []): item['force_fields'].append(field)
        # A series/name decision must not leave an orphaned number intent.
        if 'series_index' in item['desired'] and 'series' not in item['desired'] and not item['current']['series']:
            item['desired'].pop('series_index')
        item['baseline'] = deepcopy(item['current']); item['conflicts'] = []; item['errors'] = {}
        item['state'] = 'pending' if remaining(item) else 'complete'
        self.render()  # Still requires explicit confirmation; adapter rechecks after this review.

    def discard(self):
        if not self.history_ready(): return
        try:
            batch = self.selected_history()
            if not batch: return
            if self.activity_controller:
                record=self.activity_controller.batch_record(batch,self.store.folder/(batch['id']+'.json'),'bulk')
                self.activity_controller.perform('discard',record['id']);return
            if any(i['state']=='inflight' for i in batch['items']):
                self.status.setText('Review pending work first to reconcile uncertain writes.'); return
            if QMessageBox.question(self, 'Discard pending work?', 'Keep committed changes and abandon remaining work?',
                    QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes: return
            for item in batch['items']:
                if item['state'] not in FINAL: item['state'] = 'discarded'
            self.store.save(batch); self.batch = batch; self.render('result'); self.refresh_history()
            if self.activity:self.activity.batch(batch,self.store.folder/(batch['id']+'.json'),'bulk')
        except (ValueError, OSError) as exc: self.status.setText(str(exc))

    def revert(self):
        if not self.history_ready(): return
        try:
            original = self.selected_history()
            if not original: return
            response = self.request(self.identities(original))
            if response: self.batch = revert_plan(self.store, original, response); self.render()
        except (ValueError, OSError) as exc: self.status.setText(str(exc))

    def delete_history(self):
        if not self.history_ready(): return
        try:
            batch = self.selected_history()
            if not batch: return
            if self.activity_controller:
                record=self.activity_controller.batch_record(batch,self.store.folder/(batch['id']+'.json'),'bulk')
                self.activity_controller.perform('delete',record['id']);return
            if QMessageBox.warning(self, 'Delete batch history?', 'Deleting this batch history permanently removes the ability to revert this batch.',
                    QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes: return
            self.store.delete(batch); self.back(); self.refresh_history()
        except (ValueError, OSError) as exc: self.status.setText(str(exc))

    def closeEvent(self, event):
        if self.busy:
            if QMessageBox.question(self, 'Bulk operation running', 'Stop after the current book? Close again when verification finishes.',
                    QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes: self.stop()
            event.ignore()
        else:
            event.accept()
            QTimer.singleShot(0, self.on_changed)

    def reject(self):
        self.close()
