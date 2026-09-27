"""Explicit, revision-checked activity actions and restart-safe history cleanup."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
from uuid import UUID
from .activity import locked
from .import_store import ImportStore, atomic_json
from .bulk import BulkStore

FINAL = {'complete', 'duplicate', 'discarded', 'excluded'}


def revision(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


class RecoveryActions:
    def __init__(self, bridge, recovery, config):
        self.bridge, self.store, self.recovery = bridge, bridge.store, recovery
        self.config = Path(config)
        self.reviewed = {}

    def record(self, identity):
        record = next((r for r in self.store.records() if r['id'] == identity), None)
        if record is None: raise ValueError('Activity record no longer exists. Refresh history.')
        return record

    def source(self, record):
        source = record['source']; kind = source.get('kind')
        if kind in ('import', 'bulk'):
            cls, folder = (ImportStore, 'imports') if kind == 'import' else (BulkStore, 'bulk')
            store = cls(self.config/folder, source['library'])
            identity = str(UUID(source['batch_id']))
            path = store.folder/(identity+'.json')
            if path.is_symlink() or path.resolve() != Path(source['journal']).resolve():
                raise ValueError('Journal is not owned by this operation.')
            batches = store.batches()
            batch = next((b for b in ([b for _, b in batches] if kind == 'import' else batches) if b['id'] == identity), None)
            if batch is None: raise ValueError('Operation journal is unavailable; existing history was retained.')
            if batch.get('library_uuid') != source.get('library_uuid'):
                raise ValueError('Journal library identity changed.')
            return path, batch
        if kind == 'recovery':
            found = self.recovery.discover()
            entry = next((r for r in found['records'] if r['payload']['id'] == source['recovery_id']), None)
            if not entry: raise ValueError('Recovery copy is unavailable; it has not been discarded.')
            payload = entry['payload']
            if any(payload['identity'][key] != source[key] for key in payload['identity']):
                raise ValueError('Recovery ownership or library/book identity changed.')
            return Path(entry['path']), entry
        return None, record

    def acknowledge_review(self, identity):
        record = self.record(identity); _, value = self.source(record)
        if record['source'].get('kind') in ('import', 'bulk'):
            if any(i['state'] in {'inflight', 'in-flight', 'unverified'} for i in value['items']):
                raise ValueError('Reconcile uncertain writes before discarding pending work.')
        self.reviewed[identity] = revision(value)

    def dismiss(self, identity):
        with locked(self.store.folder):
            data = self.store._read(); data['operations'][identity]['dismissed'] = True
            atomic_json(self.store.path, data)
        self.changed()

    def changed(self):
        for listener in self.bridge.listeners: listener()

    def discard(self, identity):
        record = self.record(identity); path, value = self.source(record)
        if self.reviewed.get(identity) != revision(value):
            raise ValueError('Review Recovery first. The pending record may have changed since your review.')
        kind = record['source'].get('kind')
        if kind in ('import', 'bulk'):
            # All writers in this application are excluded by the UI coordinator.
            if any(i['state'] in {'inflight', 'in-flight', 'unverified'} for i in value['items']):
                raise ValueError('Uncertain writes must be reconciled before discard.')
            for item in value['items']:
                if item['state'] not in FINAL: item['state'] = 'discarded'
            value['pending_discarded'] = True
            atomic_json(path, value)
            self.bridge.batch(value, path, kind)
        elif kind == 'recovery':
            self.recovery.resolve(value['payload'], 'discarded')
        elif kind == 'metadata':
            if any(r['state']=='unresolved' and r['payload']['operation_id']==record['key'] for r in self.recovery.discover()['records']):
                raise ValueError('Review and discard the associated preserved recovery copy first.')
            self.bridge.record(record['operation'],record['key'],outcome='discarded',pending=False,
                details=dict(message='Unpreserved pending save abandoned after review; committed values retained.'))
        else:
            raise ValueError('This operation has no durable pending work to discard. Use its editor or Dismiss.')
        self.reviewed.pop(identity, None)
        self.changed()

    def delete(self, identity):
        """Called only after separate confirmation. A durable intent precedes unlink."""
        record = self.record(identity)
        intent = record.get('deletion')
        if intent is None:
            path, value = self.source(record)
            if record['pending'] or record['recovery']:
                raise ValueError('Review and explicitly discard unresolved work before deleting history.')
            kind = record['source'].get('kind'); paths = []
            if kind in ('import', 'bulk'):
                if any(i['state'] not in FINAL for i in value['items']):
                    raise ValueError('The journal still contains pending work.')
                if kind == 'import': ImportStore(self.config/'imports', record['source']['library']).review_records()
                paths = [path]
            elif kind == 'recovery':
                if value['state'] == 'unresolved': raise ValueError('Recovery is still unresolved.')
                paths = self.recovery.owned_paths(value['payload'])
            intent = {'files': [{'path': str(p), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]}
            with locked(self.store.folder):
                data = self.store._read()
                if data['operations'].get(identity) != record: raise ValueError('Activity changed; review again.')
                data['operations'][identity]['deletion'] = intent
                atomic_json(self.store.path, data)
        # An interrupted cleanup retains its intent. Retry removes only unchanged files.
        for item in intent['files']:
            path = Path(item['path'])
            if path.is_symlink(): raise ValueError('Cleanup target became a symlink; file retained.')
            if path.exists():
                if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
                    raise ValueError('Cleanup target changed; file retained. Review is required.')
                path.unlink()
                descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
                try: os.fsync(descriptor)
                finally: os.close(descriptor)
        if record['source'].get('kind') == 'recovery':
            self.recovery.forget(record['source']['recovery_id'])
        with locked(self.store.folder):
            data = self.store._read()
            data['operations'].pop(identity, None)
            data.setdefault('deleted', {})[identity] = {'source': record['source']}
            for other in data['operations'].values():
                if other.get('original') == record['source'].get('batch_id') and record['source'].get('batch_id'):
                    other['original_history_deleted'] = True
            atomic_json(self.store.path, data)
        self.reviewed.pop(identity, None); self.changed()


class ActivityController:
    """GUI routing: review first; existing explicit confirmations perform writes."""
    def __init__(self, hub):
        self.hub = hub
        self.pending_review = None
        self.review_token = 0
        self.actions = RecoveryActions(hub.activity, hub.recovery_store, hub.store.path.parent)

    def idle(self, allow_catalog=False):
        books = self.hub.bookinator
        if books and (books.bulk_active() or books.import_active() or
                      (books.loader and books.loader.active and not allow_catalog) or (books.editor and books.editor.busy)):
            raise ValueError('Wait for the current library operation to finish before changing recovery state.')

    def batch_record(self, batch, path, kind):
        self.hub.activity.batch(batch, path, kind, legacy=True)
        record = next((r for r in self.actions.store.records() if r['source'].get('batch_id')==batch['id']
                    and r['source'].get('library')==batch['library']), None)
        if record is None:raise ValueError('This history was deleted. Reopen the operation list.')
        return record

    def reviewed_batch(self, batch, path, kind):
        record = self.batch_record(batch, path, kind)
        self.actions.acknowledge_review(record['id'])

    def perform(self, action, identity):
        from PyQt6.QtWidgets import QMessageBox
        record = None
        try:
            self.idle(allow_catalog=action=='review'); record = self.actions.record(identity)
            if record.get('deletion') and action != 'delete':
                raise ValueError('History cleanup was interrupted. Use Delete this history record to finish cleanup.')
            if action == 'dismiss': self.actions.dismiss(identity)
            elif action == 'review': self.review(record)
            elif action == 'discard':
                # Validate the review revision before asking for an irreversible choice.
                _, value = self.actions.source(record)
                if self.actions.reviewed.get(identity) != revision(value):
                    raise ValueError('Open the recovery draft or review the pending operation first. Review changed or uncertain work before discarding it.')
                books = self.hub.bookinator
                if books and books.editor and record['source'].get('kind')=='metadata' and books.editor.activity_operation==record['key']:
                    raise ValueError('Use Save / Discard in the open metadata editor before cleaning up this save attempt.')
                if books and books.editor and books.editor.recovery_context and record['source'].get('recovery_id') == books.editor.recovery_context['id']:
                    raise ValueError('Close the recovered editor first. Discarding local edits there keeps the preserved copy until this separate action.')
                if QMessageBox.warning(self.hub, 'Discard Pending?',
                    'Pending work cannot be resumed after discard. Committed results remain saved.',
                    QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
                    self.actions.discard(identity)
                    self.invalidate_dialogs(record)
            elif action == 'delete':
                if record['pending'] or record['recovery']:
                    raise ValueError('Review the unresolved work, then explicitly discard it before deleting this history record.')
                if QMessageBox.warning(self.hub, 'Delete History?',
                    'Deleting this history permanently removes its details and the ability to revert this operation. Other batches and library files remain unchanged.',
                    QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
                    self.actions.delete(identity); self.invalidate_dialogs(record)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            current = next((r for r in (self.hub.activity.invoke('records') or []) if r['id']==identity), None)
            if action=='delete' and current and current.get('deletion'):
                self.hub.activity.record(current['operation'], current['key'], module=current['module'],
                    outcome='failure', pending=False, details=dict(error=str(exc), cleanup_incomplete=True))
            QMessageBox.warning(self.hub, 'Activity action incomplete', str(exc))
        finally:
            if action in ('dismiss', 'discard', 'delete') and record is not None:
                current = next((r for r in (self.hub.activity.invoke('records') or []) if r['id']==identity), None)
                if current != record:
                    for dialog in list(self.hub.activity_panel.details):
                        if dialog.record_id==identity:dialog.close()
            self.hub.activity_panel.schedule_refresh()

    def invalidate_dialogs(self, record):
        books = self.hub.bookinator
        if not books: return
        for name in ('import_dialog', 'bulk_dialog'):
            dialog = getattr(books, name)
            if dialog and dialog.batch and dialog.batch['id'] == record['source'].get('batch_id'):
                dialog.close(); dialog.deleteLater(); setattr(books, name, None)
            elif dialog and name=='bulk_dialog':
                dialog.refresh_history()

    def bookinator(self, record):
        source = record['source']; library = source.get('library')
        if library and (not self.hub.library or Path(library).resolve()!=Path(self.hub.library).resolve()):
            raise ValueError('Choose the library shown in this activity record before reviewing it.')
        self.hub.open_books(); self.idle()
        return self.hub.bookinator

    def wait_for_catalog(self, record, books, value):
        from PyQt6.QtCore import QTimer
        if self.pending_review is not None:
            raise ValueError('Recovery review is already waiting for the catalog. Wait or close the module to cancel.')
        self.review_token += 1
        token = self.review_token
        loader = books.loader
        library = self.hub.library
        expected = revision(value)
        def finish(error=None):
            if not self.pending_review or self.pending_review['token'] != token:return
            self.pending_review = None
            timer.stop()
            for signal,slot in ((loader.loaded,loaded),(loader.failed,failed)):
                try:signal.disconnect(slot)
                except (TypeError,RuntimeError):pass
            timer.deleteLater()
            if self.hub.closing or self.hub.bookinator is not books or self.hub.library != library:return
            if error:
                self.hub.statusBar().showMessage('Recovery retained: '+str(error));return
            try:
                fresh = self.actions.record(record['id'])
                _, latest = self.actions.source(fresh)
                if revision(latest) != expected:raise ValueError('Preserved draft changed while waiting. Review / Retry again.')
                self.review(fresh)
            except (ValueError,OSError,RuntimeError) as exc:
                self.hub.statusBar().showMessage('Recovery retained: '+str(exc))
        loaded=lambda *_:finish()
        failed=lambda message:finish('Catalog read failed: '+str(message))
        timer=QTimer(self.hub);timer.setSingleShot(True)
        timer.timeout.connect(lambda:finish('Catalog wait timed out. Review / Retry when Library loaded.'))
        self.pending_review=dict(token=token,cancel=lambda:finish('Review cancelled; preserved draft unchanged.'))
        loader.loaded.connect(loaded);loader.failed.connect(failed);timer.start(35000)
        self.hub.statusBar().showMessage('Waiting for catalog refresh before reviewing recovery. Close the module to cancel.')

    def present_editor(self, editor, record):
        """Hand focus from read-only Activity windows to the ready draft."""
        panel=self.hub.activity_panel
        for dialog in list(panel.details):
            if dialog.record_id==record['id']:dialog.hide()
        if panel.history and panel.history.isVisible():panel.history.hide()
        editor.show()
        editor.raise_()
        editor.activateWindow()
        editor.title.setFocus()

    def review(self, record):
        from PyQt6.QtWidgets import QMessageBox
        source = record['source']; kind = source.get('kind')
        path, value = self.actions.source(record)
        books = self.hub.bookinator
        if kind in ('metadata','recovery','metadata_review') and books and books.loader and books.loader.active:
            self.idle(allow_catalog=True)
            self.wait_for_catalog(record,books,value)
            return
        if kind in ('import', 'bulk'):
            books = self.bookinator(record)
            if kind == 'import':
                dialog = books.open_imports()
                if dialog: dialog.review_batch(path)
            else:
                dialog = books.open_bulk()
                if dialog:
                    index = dialog.history.findData(source['batch_id'])
                    if index < 0: raise ValueError('Batch is unavailable in this library.')
                    dialog.history.setCurrentIndex(index); dialog.review()
            return
        if kind in ('metadata', 'recovery', 'metadata_review'):
            books = self.bookinator(record)
            if kind == 'metadata' and books.editor and books.editor.activity_operation == record['key']:
                books.editor.show(); books.editor.raise_(); return
            if kind=='metadata':
                linked=next((r for r in self.actions.store.records() if r['source'].get('save_operation_id')==record['key'] and r['recovery']),None)
                if linked:return self.review(linked)
            book_uuid = source.get('book_uuid')
            book = next((b for b in books.books if b.uuid == book_uuid), None)
            if not book: raise ValueError('Book is unavailable. Load the correct library and refresh before review.')
            # Closing/reviewing the old editor can trigger auto-refresh synchronously.
            # Keep that refresh deferred until the new draft is ready, not between editors.
            if getattr(books, 'recovery_handoff', False):
                raise ValueError('Recovery review is already in progress. Wait for it to finish.')
            books.recovery_handoff = True
            try:
                if books.editor:
                    if not books.editor.review(): return
                    books.editor.done(0)
                books.state['selected_book'] = book.id
                books.edit_metadata(present=False)
                editor = books.editor
                if not editor or not editor.baseline:
                    reason = editor.status.text() if editor else 'Catalog is loading. Wait for Library loaded, then Review / Retry.'
                    if editor:
                        books.editor = None
                        editor.deleteLater()
                    raise ValueError('Draft review could not read current metadata. '+reason+' Preserved recovery was retained.')
            finally:
                books.recovery_handoff = False
                if getattr(books, 'refresh_deferred', False):
                    from PyQt6.QtCore import QTimer
                    books.refresh_deferred = False
                    QTimer.singleShot(0, books.auto_refresh)
            if source.get('library_uuid') and editor.library_uuid != source['library_uuid']:
                raise ValueError('Current library identity differs; recovery was not applied.')
            if kind == 'recovery':
                _, latest = self.actions.source(record)
                if revision(latest) != revision(value):
                    raise ValueError('Preserved draft changed during metadata reading. Review / Retry again; recovery retained.')
                payload = value['payload']
                if value['state'] != 'unresolved': raise ValueError('This recovery has already been resolved.')
                result = self.hub.recovery_store.draft(payload, editor.baseline,
                    library_uuid=editor.library_uuid, book_uuid=book.uuid)
                if result['conflicts']:
                    proposed = dict(editor.baseline, **payload['pending'])
                    for field in result['conflicts']:
                        proposed[field] = payload['pending'].get(field, payload['baseline'][field])
                    if editor.resolve(result, proposed) is None: return
                else: editor.apply_pending(result['draft'])
                editor.recovery_context = deepcopy(payload)
                editor.recovery_id = payload['id']; editor.activity_operation = payload['operation_id']
                editor.draft_revision = max(editor.draft_revision, payload['revision'])
                editor.status.setText('Recovered draft reviewed. Choose Save to commit; opening recovery has not written to Calibre.')
                self.actions.acknowledge_review(record['id'])
                self.present_editor(editor, record)
            else:
                editor.status.setText('Review current metadata. Only drafts still open or explicitly preserved can be recovered; history does not contain unsaved values.')
                self.actions.acknowledge_review(record['id'])
                self.present_editor(editor, record)
            return
        if kind in ('settings', 'refresh', 'reader_launch', 'discovery', 'recovery_discovery'):
            # A separate deliberate confirmation is required even for refresh/launch.
            if QMessageBox.question(self.hub, 'Review retry',
                'Retry '+record['operation']+'?\n'+str(source.get('file') or source.get('path') or source.get('library') or ''),
                QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes: return
            if kind == 'settings': self.hub.persist()
            elif kind == 'refresh': self.bookinator(record).manual_refresh()
            elif kind == 'reader_launch': self.bookinator(record).open_format(source['path'])
            else:
                self.hub.sync_local_activity(); self.hub.recovery_store.sync_activity()
            return
        if kind == 'movie_catalog':
            movies = self.hub.movieinator
            if movies is None:
                self.hub.open_movies(); movies = self.hub.movieinator
            movies.reload(explicit=True)
            return
        if kind == 'music_catalog':
            music = self.hub.musicinator
            if music is None:
                self.hub.open_music(); music = self.hub.musicinator
            music.reload(explicit=True)
            return
        if kind in ('paper_library', 'paper_purge'):
            papers = self.hub.paperinator
            if papers is None:
                self.hub.open_papers(); papers = self.hub.paperinator
            papers.reload(explicit=True)
            return
        raise ValueError('No executable recovery data is available. Inspect details or dismiss the notice.')
