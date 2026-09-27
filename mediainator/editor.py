"""Single-book draft editor with explicit, verified save and conflict review."""
import base64
from copy import deepcopy
from pathlib import Path
from PyQt6.QtCore import QEventLoop, Qt
from PyQt6.QtGui import QPixmap, QTextCharFormat, QFont, QTextListFormat
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QPushButton, QListWidget, QInputDialog, QMessageBox, QFileDialog,
    QTextEdit, QDialogButtonBox, QTableWidget, QTableWidgetItem, QComboBox)
from .metadata import MetadataWorker
from .metadata_rules import changes, validate


class Entries(QListWidget):
    def __init__(self, ordered, parent=None):
        super().__init__(parent)
        self.ordered = ordered
        self.setMaximumHeight(90)

    def values(self):
        return [self.item(i).text() for i in range(self.count())]

    def buttons(self):
        bar = QHBoxLayout()
        for text, slot in [('Add author' if self.ordered else 'Add tag', self.add), ('Remove author' if self.ordered else 'Remove tag', self.remove)]+([('Move author up',lambda:self.move(-1)),('Move author down',lambda:self.move(1))] if self.ordered else []):
            b=QPushButton(text); b.clicked.connect(slot); bar.addWidget(b)
        return bar

    def add(self):
        value, ok = QInputDialog.getText(self,'Add author' if self.ordered else 'Add tag','Name')
        value=value.strip()
        if ok and value:
            if not self.ordered and ',' in value:
                QMessageBox.warning(self,'Invalid tag','Tag names cannot contain commas because Calibre treats commas as separators.')
            elif value not in self.values():
                self.addItem(value)

    def remove(self):
        self.takeItem(self.currentRow())

    def move(self, step):
        row=self.currentRow(); target=row+step
        if row>=0 and 0<=target<self.count():
            self.insertItem(target,self.takeItem(row)); self.setCurrentRow(target)


class MetadataEditor(QDialog):
    def __init__(self, root, book, recovery_dir, parent=None):
        super().__init__(parent)
        self.root,self.book,self.recovery_dir=root,book,recovery_dir
        self.review_store=None
        self.activity=None; self.recovery_store=None; self.library_uuid=None
        self.recovery_context=None
        self.failed_saves=0; self.failed_draft=None; self.preservation_failed=False
        self.preserved_payload=None; self.preserved_signature=None
        self.on_preserved=lambda message:None
        self.approved_close_signature=None
        self.activity_operation=None; self.recovery_id=None; self.draft_revision=0; self._revision_signature=None
        self.baseline=None; self.cover=None; self.busy=False; self.filling=False
        self.on_saved=lambda:None
        self.setWindowTitle('Book metadata')
        self.resize(650,780)
        layout=QVBoxLayout(self); self.status=QLabel(); self.status.setWordWrap(True); layout.addWidget(self.status)
        self.review_status=QLabel();layout.addWidget(self.review_status)
        mark_reviewed=QPushButton('Mark Reviewed');mark_reviewed.clicked.connect(self.mark_reviewed);layout.addWidget(mark_reviewed)
        form=QFormLayout(); layout.addLayout(form)
        self.title=QLineEdit(); form.addRow('Title',self.title)
        self.authors=Entries(True); form.addRow('Authors (ordered)',self.authors); form.addRow(self.authors.buttons())
        self.tags=Entries(False); form.addRow('Tags',self.tags); form.addRow(self.tags.buttons())
        self.series=QLineEdit(); self.number=QLineEdit(); self.number_label=QLabel('Series number')
        form.addRow('Series',self.series); form.addRow(self.number_label,self.number)
        self.description=QTextEdit(); self.description.setAcceptRichText(False); self.description.setMaximumHeight(170)
        toolbar=QHBoxLayout()
        for label, action in [('Bold',lambda:self.format_text('bold')),('Italic',lambda:self.format_text('italic')),('Bullets',lambda:self.list_text(False)),('Numbered list',lambda:self.list_text(True)),('Paragraph',self.paragraph)]:
            button=QPushButton(label); button.clicked.connect(action); toolbar.addWidget(button)
        layout.addLayout(toolbar); layout.addWidget(self.description)
        coverbar=QHBoxLayout(); self.preview=QLabel(); self.preview.setFixedSize(80,100); coverbar.addWidget(self.preview)
        choose=QPushButton('Choose cover image'); choose.clicked.connect(self.choose_cover); coverbar.addWidget(choose)
        remove=QPushButton('Remove cover'); remove.clicked.connect(lambda:self.set_cover(None)); coverbar.addWidget(remove)
        layout.addLayout(coverbar)
        buttons=QHBoxLayout()
        self.save_button=QPushButton('Save metadata'); self.save_button.clicked.connect(self.save_changes)
        discard=QPushButton('Discard local edits'); discard.clicked.connect(self.discard)
        discard.setToolTip('Discard only local unsaved edits. Previously saved changes and separately preserved recovery remain available.')
        close=QPushButton('Close editor'); close.clicked.connect(self.close)
        keep=QPushButton('Keep Editing');keep.clicked.connect(self.title.setFocus)
        for b in (self.save_button,keep,discard,close):buttons.addWidget(b)
        self.preserve_elsewhere_button=QPushButton('Preserve Elsewhere…')
        self.preserve_elsewhere_button.setVisible(False)
        self.preserve_elsewhere_button.clicked.connect(self.preserve_elsewhere)
        buttons.addWidget(self.preserve_elsewhere_button)
        layout.addLayout(buttons)
        self.series.textChanged.connect(self.series_changed)
        for widget in (self.title,self.series,self.number):widget.textChanged.connect(self.mark)
        self.description.textChanged.connect(self.mark)
        for entries in (self.authors,self.tags):
            entries.model().rowsInserted.connect(self.mark); entries.model().rowsRemoved.connect(self.mark)

    def set_phase(self,phase):
        self.phase=phase
        name=self.baseline['title'] if self.baseline else self.book.title
        self.setWindowTitle(f'Book metadata — {name} — {phase}')

    def request(self, action, **values):
        if self.busy:return None
        self.busy=True
        self.set_phase('Saving' if action=='save' else 'Loading')
        request=dict(action=action,book=self.book.id.rsplit(':',1)[1],uuid=self.book.uuid,**values)
        self.worker=MetadataWorker(self.root,request,self.recovery_dir,self)
        result={}; loop=QEventLoop(self)
        self.worker.result.connect(lambda value:result.update(value))
        self.worker.failure.connect(lambda error:result.update(error=error))
        self.worker.finished.connect(loop.quit)
        self.setEnabled(False)
        self.worker.start(); loop.exec(); self.worker.wait()
        self.setEnabled(True); self.busy=False; self.worker.deleteLater()
        if 'error' in result:
            self.set_phase('Verification required' if action=='save' else 'Load failed');self.status.setText(result['error']); return None
        return result

    def load(self):
        result=self.request('read')
        if result:
            self.library_uuid=result.get('library_uuid',self.library_uuid)
            self.fill(result['current']); return True
        return False

    def fill(self, record):
        self.filling=True; self.baseline=deepcopy(record)
        self.title.setText(record['title'])
        for widget,field in ((self.authors,'authors'),(self.tags,'tags')):
            widget.clear(); widget.addItems(record[field])
        self.series.setText(record['series']); self.number.setText(str(record['series_index']) if record['series'] else '')
        self.number.setVisible(bool(record['series'])); self.number_label.setVisible(bool(record['series']))
        self.description.setHtml(record['comments']); self.description.document().setModified(False)
        self.set_cover(record['cover']); self.filling=False; self.mark(); self.update_review_status()

    def mark_reviewed(self):
        if self.busy or not self.review_store:return
        if self.dirty():
            self.status.setText('Save or discard metadata before marking the saved record reviewed.');return
        try:
            self.review_store.mark_reviewed(self.book.uuid);self.update_review_status();self.on_saved()
            if self.activity:self.activity.record('Metadata review',str(self.root)+'\0'+self.book.uuid,outcome='success',
                source=dict(kind='metadata_review',library=str(self.root),book_uuid=self.book.uuid),details=dict(reviewed=True))
        except (OSError,ValueError) as exc:
            self.status.setText('Review status not saved: '+str(exc))
            if self.activity:self.activity.record('Metadata review',str(self.root)+'\0'+self.book.uuid,outcome='failure',pending=True,
                source=dict(kind='metadata_review',library=str(self.root),book_uuid=self.book.uuid),details=dict(error=str(exc)),deduplicate=True)

    def update_review_status(self):
        if not self.review_store or not self.baseline:return
        try:
            related=[i for i in self.review_store.review_records() if i['destination_uuid']==self.book.uuid and i.get('missing')]
            complete=bool(self.baseline['title'].strip() and self.baseline['authors'] and all(a.strip() and a.casefold()!='unknown' for a in self.baseline['authors']))
            if any('title' in i['missing'] and self.baseline['title']==i.get('title') for i in related):complete=False
            needed=self.book.uuid in self.review_store.review_needed()
            if hasattr(self.review_store,'reasons'):
                from dataclasses import replace
                current=replace(self.book,title=self.baseline['title'],author=' & '.join(self.baseline['authors']),series=self.baseline['series'],cover=self.baseline['cover'] or '',missing_fields=())
                reasons=self.review_store.reasons(current)
                self.review_status.setText('Review: '+('; '.join(reasons) if reasons else 'No outstanding reasons'))
                return
            self.review_status.setText('Metadata Completeness: '+('Complete' if complete else 'Incomplete')+' · Review Status: '+('Needs Metadata Review' if needed else 'Reviewed' if related else 'Not flagged'))
        except (OSError,ValueError) as exc:self.review_status.setText('Review status unavailable: '+str(exc))

    def draft(self):
        if self.baseline is None:return None
        record=deepcopy(self.baseline)
        record.update(title=self.title.text(),authors=self.authors.values(),tags=self.tags.values(),series=self.series.text().strip(),cover=self.cover)
        value=self.number.text()
        try:value=float(value)
        except ValueError:pass
        record['series_index']=value if record['series'] else None
        if self.description.document().isModified():record['comments']=self.description.toHtml()
        return record

    def dirty(self):
        return bool(self.baseline and changes(self.baseline,self.draft()))

    def mark(self,*_):
        if not self.filling:
            import json
            signature=json.dumps(self.draft(),sort_keys=True)
            if signature!=self._revision_signature:
                self.draft_revision+=1;self._revision_signature=signature
            self.set_phase('Unsaved changes' if self.dirty() else 'Ready')

    def series_changed(self,value):
        if self.filling:return
        self.number.setVisible(bool(value.strip())); self.number_label.setVisible(bool(value.strip()))
        self.number.setText('1' if value.strip() else '')

    def set_cover(self,value):
        self.cover=value; pix=QPixmap()
        if value:pix.loadFromData(base64.b64decode(value))
        self.preview.setPixmap(pix.scaled(80,100,Qt.AspectRatioMode.KeepAspectRatio) if not pix.isNull() else pix)
        self.mark()

    def choose_cover(self):
        path,_=QFileDialog.getOpenFileName(self,'Choose cover','','Images (*.jpg *.jpeg *.png *.webp *.bmp)')
        if not path:return
        try:
            data=Path(path).read_bytes(); pix=QPixmap()
            if not pix.loadFromData(data):raise ValueError('Select a valid image.')
            self.set_cover(base64.b64encode(data).decode())
        except (OSError,ValueError) as exc:QMessageBox.warning(self,'Cannot use cover',str(exc))

    def format_text(self,kind):
        fmt=QTextCharFormat()
        if kind=='bold':fmt.setFontWeight(QFont.Weight.Normal if self.description.fontWeight()==QFont.Weight.Bold else QFont.Weight.Bold)
        else:fmt.setFontItalic(not self.description.fontItalic())
        self.description.mergeCurrentCharFormat(fmt)

    def list_text(self,numbered):
        fmt=QTextListFormat(); fmt.setStyle(QTextListFormat.Style.ListDecimal if numbered else QTextListFormat.Style.ListDisc)
        self.description.textCursor().createList(fmt)

    def paragraph(self):
        cursor=self.description.textCursor(); block=cursor.blockFormat(); block.setObjectIndex(-1); cursor.setBlockFormat(block)

    def resolve(self,result,draft):
        dialog=QDialog(self); dialog.setWindowTitle('Resolve metadata conflicts'); layout=QVBoxLayout(dialog)
        layout.addWidget(QLabel('Calibre changed externally. Choose a value for each conflicting field.'))
        table=QTableWidget(len(result['conflicts']),4); table.setHorizontalHeaderLabels(['Field','My value','Calibre value','Use'])
        choices={}
        for row,f in enumerate(result['conflicts']):
            table.setItem(row,0,QTableWidgetItem(f))
            for col,record in ((1,draft),(2,result['current'])):
                item=QTableWidgetItem(str(record[f]) if f!='cover' else ('Image present' if record[f] else 'No cover'))
                if f=='cover' and record[f]:
                    from PyQt6.QtGui import QIcon
                    pix=QPixmap();pix.loadFromData(base64.b64decode(record[f]));item.setIcon(QIcon(pix))
                table.setItem(row,col,item)
            combo=QComboBox();combo.addItems(['Keep My Value','Use Calibre Value']);table.setCellWidget(row,3,combo);choices[f]=combo
        table.resizeColumnsToContents();layout.addWidget(table)
        bar=QHBoxLayout()
        for label,index in [('Keep All Mine',0),('Use All Calibre Values',1)]:
            b=QPushButton(label);b.clicked.connect(lambda _,i=index:[c.setCurrentIndex(i) for c in choices.values()]);bar.addWidget(b)
        layout.addLayout(bar)
        buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject);layout.addWidget(buttons)
        dialog.resize(800,350)
        if dialog.exec()!=QDialog.DialogCode.Accepted:return None
        pending=changes(self.baseline,draft)
        selected=deepcopy(result['current'])
        for field,value in pending.items():selected[field]=value
        for field,combo in choices.items():selected[field]=draft[field] if combo.currentIndex()==0 else result['current'][field]
        if not selected['series']:selected['series_index']=None
        self.fill(result['current']); self.apply_pending(selected)
        return selected

    def apply_pending(self, draft):
        baseline=deepcopy(self.baseline); self.fill(draft); self.baseline=baseline
        # Draft HTML must remain byte-identical until the user actually edits it.
        if draft['comments']!=baseline['comments']:
            self.description.document().setModified(True)
        self.mark()

    def validate_draft(self, draft):
        validate(draft)
        if draft.get('cover') and draft['cover']!=self.baseline.get('cover'):
            try:
                image=QPixmap();valid=image.loadFromData(base64.b64decode(draft['cover'],validate=True))
            except (ValueError,TypeError):valid=False
            if not valid:raise ValueError('Selected cover is not a valid image. Choose another image.')

    def draft_signature(self):
        import json
        return json.dumps(self.draft(),sort_keys=True)

    def clear_preservation_failure(self):
        if self.activity and self.activity_operation:
            self.activity.invoke('resolve_notice','Emergency preservation',self.activity_operation)

    def reset_failures(self):
        self.failed_saves=0;self.failed_draft=None;self.preservation_failed=False
        self.preserve_elsewhere_button.hide()

    def save_failed(self):
        self.failed_saves+=1;self.failed_draft=self.draft_signature()
        if self.failed_saves>=2 and self.dirty():self.emergency_preserve()
        return False

    def emergency_preserve(self, destination=None):
        try:
            self.validate_draft(self.draft())
            path=self.preserve_recovery(destination)
            self.preserved_payload=self.recovery_store.read(path)
            self.preserved_signature=(self.draft_revision,self.draft_signature())
            self.preservation_failed=False;self.preserve_elsewhere_button.hide()
            message='Unsaved edits preserved in an emergency copy. They have not been saved to the library. Review Recovery is available in Activity.'
            self.set_phase('Preserved for recovery');self.status.setText(message);self.on_preserved(message)
            return True
        except (OSError,ValueError,TypeError) as exc:
            self.preservation_failed=True;self.preserve_elsewhere_button.show()
            self.status.setText('Emergency preservation failed; your edits remain open. '+str(exc)+' Choose Preserve Elsewhere… or retry. A file alone is not proof of successful registration.')
            if self.activity:
                self.activity.record('Emergency preservation',self.activity_operation or str(self.book.uuid),
                    outcome='failure',pending=True,source=dict(kind='metadata',library=str(self.root),
                    library_uuid=self.library_uuid,book_uuid=self.book.uuid),details=dict(error=str(exc)),deduplicate=True)
            return False

    def preserve_elsewhere(self):
        if self.busy:return False
        destination=QFileDialog.getExistingDirectory(self,'Preserve unsaved edits elsewhere')
        return self.emergency_preserve(destination) if destination else False

    def protected_current_draft(self):
        if self.preservation_failed or not self.preserved_payload or self.preserved_signature!=(self.draft_revision,self.draft_signature()):return False
        try:
            return any(r['registered'] and r['state']=='unresolved' and r['payload']==self.preserved_payload
                for r in self.recovery_store.discover()['records'])
        except (OSError,ValueError):return False

    def close_failure_choice(self):
        dialog=QMessageBox(self);dialog.setWindowTitle('Unsaved edits are still open')
        dialog.setText(self.status.text())
        retry=dialog.addButton('Retry Save',QMessageBox.ButtonRole.AcceptRole)
        alternate=dialog.addButton('Preserve Elsewhere…',QMessageBox.ButtonRole.ActionRole) if self.preservation_failed else None
        keep=dialog.addButton('Keep Editing',QMessageBox.ButtonRole.RejectRole)
        cancel=dialog.addButton(QMessageBox.StandardButton.Cancel);dialog.setDefaultButton(cancel)
        dialog.exec()
        if dialog.clickedButton() is retry:return 'retry'
        if alternate is not None and dialog.clickedButton() is alternate:return 'elsewhere'
        return 'cancel'

    def save_for_close(self):
        # Close intent is stack-scoped. Cancel/Keep Editing cannot leave a latent close.
        while True:
            if self.save_changes():return True
            if self.protected_current_draft():return True
            if not self.failed_saves:return False  # Invalid input or cancelled conflicts.
            choice=self.close_failure_choice()
            if choice=='elsewhere':
                if self.preserve_elsewhere() and self.protected_current_draft():return True
                return False
            if choice!='retry':return False

    def save_changes(self):
        if self.busy:return False
        if not self.baseline:return self.load()
        draft=self.draft()
        try:self.validate_draft(draft)
        except ValueError as exc:self.reset_failures();self.status.setText(str(exc));return False
        if self.failed_draft is not None and self.failed_draft!=self.draft_signature():self.reset_failures()
        pending=changes(self.baseline,draft)
        if not pending:
            if self.recovery_context:
                # Even a no-op recovery needs a fresh read before resolution.
                result=self.request('read')
                if not result:return False
                if result.get('library_uuid')!=self.library_uuid or result['current'].get('uuid')!=self.book.uuid:
                    self.status.setText('Recovery identity changed; preserved copy retained.');return False
                if changes(result['current'],draft):
                    self.status.setText('Metadata changed since review. Reopen Recovery before resolving this copy.');return False
                self.fill(result['current'])
                if not self.finish_recovery():return False
            if self.activity and self.activity_operation:
                self.activity.record('Single-book metadata saves',self.activity_operation,outcome='success',pending=False,
                    details=dict(message='No outstanding draft changes.'))
            from .feedback import save_feedback
            self.status.setText(save_feedback(self.baseline["title"]));self.set_phase('No changes to save')
            self.clear_preservation_failure()
            self.activity_operation=None;self.reset_failures()
            self.on_saved();return True
        from uuid import uuid4
        if self.activity_operation is None:self.activity_operation=str(uuid4())
        attempt_id=str(uuid4())
        if self.activity:
            self.activity.record('Single-book metadata saves',self.activity_operation,outcome='running',pending=True,
                source=dict(kind='metadata',library=str(self.root),library_uuid=self.library_uuid,book_uuid=self.book.uuid,book=self.book.id),
                details=dict(fields=sorted(pending),draft_revision=self.draft_revision),attempt_id=attempt_id)
        result=self.request('save',baseline=self.baseline,changes=pending)
        if self.activity:
            source=dict(kind='metadata',library=str(self.root),library_uuid=self.library_uuid,book_uuid=self.book.uuid,book=self.book.id)
            self.activity.record('Single-book metadata saves',self.activity_operation,
                outcome='failure' if result is None or result.get('errors') else 'conflict' if result.get('conflicts') else 'success',
                pending=result is None or bool(result.get('errors') or result.get('conflicts')),source=source,attempt_id=attempt_id,
                details=dict(fields=sorted(pending),saved=result.get('saved',[]) if result else [],
                             errors=result.get('errors',{}) if result else {'operation':self.status.text()},
                             conflicts=result.get('conflicts',[]) if result else [],draft_revision=self.draft_revision))
        if result is None:
            self.status.setText(f"Save result could not be verified for {self.baseline['title']}. "+self.status.text())
            self.save_button.setText('Retry unsaved changes');return self.save_failed()
        if result.get('conflicts'):
            self.reset_failures()
            if self.resolve(result,draft) is None:return False
            return self.save_changes()
        current=result['current'];remaining={f:v for f,v in pending.items() if f not in result.get('saved',[])}
        self.fill(current)
        if remaining:self.apply_pending(dict(current,**remaining))
        errors=result.get('errors',{})
        from .feedback import save_feedback
        self.status.setText(save_feedback(current['title'],result.get('saved',[]),remaining,errors)+((' '+str(result['recovery'])) if result.get('recovery') else ''))
        self.save_button.setText('Retry unsaved changes' if remaining else 'Save metadata')
        self.set_phase('Save incomplete' if remaining or errors else 'Saved')
        self.on_saved()
        if self.recovery_context and not self.finish_recovery():return False
        if not remaining and not errors:
            self.clear_preservation_failure()
            self.activity_operation=None;self.recovery_id=None;self.reset_failures();return True
        return self.save_failed()

    def finish_recovery(self):
        """Persist remaining recovery intent only after a verified Save response."""
        if not self.recovery_context:return True
        try:
            old=self.recovery_context
            # Refuse to replace a newer preserved revision from another review.
            found=next((r for r in self.recovery_store.discover()['records'] if r['payload']['id']==old['id']),None)
            if not found or found['payload']!=old or found['state']!='unresolved':
                raise ValueError('Recovery changed since review. Existing recovery was retained.')
            if self.dirty():
                payload=self.recovery_store.capture(self.library_uuid,self.book.uuid,self.baseline,self.draft(),
                    max(self.draft_revision,old['revision']+1),old['operation_id'],old['id'])
                self.recovery_store.preserve(payload,Path(found['path']).parent)
                self.recovery_context=payload;self.draft_revision=max(self.draft_revision,payload['revision'])
            else:
                self.recovery_store.resolve(old,'recovered');self.recovery_context=None
            return True
        except (OSError,ValueError) as exc:
            self.status.setText('Library results retained, but recovery registration could not be updated: '+str(exc))
            return False

    def preserve_recovery(self, destination=None):
        if self.busy or not self.dirty() or not self.recovery_store or not self.library_uuid:
            raise ValueError('A stable unsaved draft and verified library identity are required.')
        from uuid import uuid4
        if self.activity_operation is None:self.activity_operation=str(uuid4())
        payload=self.recovery_store.capture(self.library_uuid,self.book.uuid,self.baseline,self.draft(),
                                           self.draft_revision,self.activity_operation,self.recovery_id)
        self.recovery_id=payload['id']  # Stable intent identity, not proof of preservation.
        path=self.recovery_store.preserve(payload,destination)
        self.recovery_context=payload
        if self.activity:self.activity.invoke('resolve_notice','Emergency preservation',self.activity_operation)
        return path

    def record_discard(self):
        self.clear_preservation_failure()
        self.reset_failures()
        if self.recovery_context:
            # Local editor discard does not abandon the durable emergency copy.
            self.recovery_context=None;self.activity_operation=None;self.recovery_id=None
            return
        if self.activity and self.activity_operation:
            self.activity.record('Single-book metadata saves',self.activity_operation,outcome='discarded',pending=False,
                                 source=dict(kind='metadata',library=str(self.root),library_uuid=self.library_uuid,book_uuid=self.book.uuid),
                                 details=dict(message='Remaining local edits discarded; committed values retained.'))
        self.activity_operation=None;self.recovery_id=None

    def discard(self):
        if self.busy:return False
        if self.dirty() and self.activity_operation is None:
            from uuid import uuid4
            self.activity_operation=str(uuid4())
        preserved = bool(self.recovery_context or self.preserved_payload)
        recovery_note = ' The preserved recovery draft remains available in Activity; discarding it is a separate action.' if preserved else ''
        if self.load():
            self.record_discard()
            self.save_button.setText('Save metadata')
            self.status.setText('Local edits discarded; saved values reloaded.' + recovery_note)
            # This read changed no saved metadata. Avoid a redundant catalog/editor reload.
            return True
        if self.baseline:
            self.record_discard()
            self.fill(self.baseline)
            self.status.setText('Local edits discarded. Waiting for library access to reload current values.' + recovery_note)
            return True
        return False

    def approve_parent_close(self):
        self.approved_close_signature=(self.draft_revision,self.draft_signature())

    def review(self, closing=False):
        if self.busy:
            self.status.setText('Wait for metadata verification to finish.');return False
        if not self.dirty():return True
        if closing and self.approved_close_signature==(self.draft_revision,self.draft_signature()) and self.protected_current_draft():return True
        answer=QMessageBox.question(self,'Unsaved metadata','Save changes before continuing?',QMessageBox.StandardButton.Save|QMessageBox.StandardButton.Discard|QMessageBox.StandardButton.Cancel,QMessageBox.StandardButton.Cancel)
        if answer==QMessageBox.StandardButton.Save:return self.save_for_close() if closing else self.save_changes()
        if answer==QMessageBox.StandardButton.Discard:return self.discard()
        return False

    def closeEvent(self,event):
        if self.review(closing=True):event.accept()
        else:event.ignore()

    def reject(self):
        if self.review(closing=True):super().reject()
