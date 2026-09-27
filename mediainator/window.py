"""Hub lifecycle, catalog views and single-book metadata editor integration."""
from PyQt6.QtCore import QByteArray, Qt, QTimer, QEvent
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap, QAction, QKeySequence
from PyQt6.QtWidgets import (
    QAbstractItemView, QComboBox, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QPushButton,
    QStackedWidget, QTabWidget, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget, QFileDialog, QCheckBox, QMenu, QProgressBar, QGridLayout, QScrollArea, QStyle,
)
from .catalog import SAMPLE_BOOKS, find_books
from .settings import SettingsError
from .library import LibraryLoader, SnapshotLoader
from .reader import Reader, ReaderError
from pathlib import Path


def placeholder(title: str) -> QIcon:
    image = QPixmap(110, 145)
    image.fill(QColor("#34465a"))
    painter = QPainter(image)
    painter.setPen(QColor("#ffffff"))
    font = painter.font()
    font.setPointSize(22)
    painter.setFont(font)
    painter.drawText(image.rect(), Qt.AlignmentFlag.AlignCenter, title[0])
    painter.end()
    return QIcon(image)


class Bookinator(QWidget):
    def __init__(self, state, save, library=None, reader=None, live=False, choose_library=None):
        super().__init__()
        self.state, self.save = state, save
        self.library, self.reader = library, reader
        self.books = () if library or live else SAMPLE_BOOKS
        self.closing = False
        self.recovery_checked = False
        self.import_dialog = None
        self.bulk_dialog = None
        self.bulk_selection = set()
        self.review_cache = None
        self.discovery_dialog = None
        self.duplicate_dialog = None
        self.editor = None
        self.live = live
        self.compatibility_allowed = not live
        self.refresh_signature = None
        self.progress_store = None
        self.book_progress = {}
        self.reader_was_active = False
        self.visible = []
        self.rendering = False
        layout = QVBoxLayout(self)
        self.note = note = QLabel("Calibre library" if live and library else "Disposable test library" if library else "Choose a Calibre library to begin." if live else "Sample catalog · Connect a disposable test library to launch readers.")
        note.setWordWrap(True)
        layout.addWidget(note)
        if choose_library:
            choose = QPushButton("Choose library…")
            choose.clicked.connect(choose_library)
            layout.addWidget(choose)
        self.retry = QPushButton("Reload library")
        self.retry.setVisible(library is not None)
        layout.addWidget(self.retry)
        self.loader = (SnapshotLoader(library, self) if live else LibraryLoader(library, self)) if library else None
        self.load_progress=QProgressBar();self.load_progress.setRange(0,0);self.load_progress.hide();layout.addWidget(self.load_progress)
        self.cancel_load=QPushButton('Cancel library load');self.cancel_load.hide();layout.addWidget(self.cancel_load)
        if self.loader:
            self.cancel_load.clicked.connect(self.loader.cancel)
            self.loader.progress.connect(self.note.setText)
            self.loader.loaded.connect(self.loaded)
            self.loader.failed.connect(self.load_failed)
            self.loader.busy_changed.connect(self.loading)
            self.retry.clicked.connect(self.manual_refresh)
            if not live:
                QTimer.singleShot(0, self.loader.load)
        bar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Find by title, author or series")
        self.search.setAccessibleName("Find books by title, author or series")
        self.search.setClearButtonEnabled(True)
        saved_search = state.get('catalog_search', {})
        self.search.setText(saved_search.get('text', ''))
        self.filter_values = {key: set(saved_search.get(key, [])) for key in ('tags','formats','statuses')}
        bar.addWidget(self.search, 1)
        self.clear_search = QPushButton('Clear All')
        self.clear_search.clicked.connect(self.clear_search_filters)
        bar.addWidget(self.clear_search)
        self.filter_toggle = QCheckBox('Filters')
        self.filter_toggle.setChecked(saved_search.get('expanded', True))
        bar.addWidget(self.filter_toggle)
        self.view = QComboBox()
        self.view.addItems(["Grid", "List"])
        self.view.setCurrentText(state["view"])
        self.view.setAccessibleName("Catalog view")
        bar.addWidget(self.view)
        layout.addLayout(bar)
        self.filter_panel = QWidget()
        filter_layout = QHBoxLayout(self.filter_panel)
        self.filter_buttons = {}
        for key, label in [('tags','Tags'),('formats','Formats'),('statuses','Reading status')]:
            button = QPushButton(label); menu = QMenu(button); button.setMenu(menu)
            self.filter_buttons[key] = (button, menu, label)
            filter_layout.addWidget(button)
        self.filter_panel.setVisible(self.filter_toggle.isChecked())
        layout.addWidget(self.filter_panel)
        bulkbar = QHBoxLayout()
        self.bulk_count = QLabel('0 selected'); bulkbar.addWidget(self.bulk_count)
        for title, slot in [('Select all search results', self.select_all_bulk), ('Clear selection', self.clear_bulk), ('Bulk edit / history…', self.open_bulk)]:
            button = QPushButton(title); button.clicked.connect(slot); bulkbar.addWidget(button)
        self.sort = QComboBox(); self.sort.addItems(['Title A–Z', 'Title Z–A', 'Author A–Z'])
        self.sort.currentIndexChanged.connect(self.render); bulkbar.addWidget(self.sort)
        self.bulk_recovery = QLabel(); self.bulk_recovery.setWordWrap(True); layout.addLayout(bulkbar); layout.addWidget(self.bulk_recovery)
        discoverybar=QHBoxLayout()
        for label,slot in [('Find / review…',self.open_discovery),('Duplicates…',self.open_duplicates)]:
            button=QPushButton(label);button.clicked.connect(slot);discoverybar.addWidget(button)
        layout.addLayout(discoverybar)
        self.count = QLabel()
        layout.addWidget(self.count)
        self.pages = QStackedWidget()
        from .catalog_views import CatalogGrid, CatalogTable
        self.grid = CatalogGrid(self)
        self.grid.setViewMode(QListWidget.ViewMode.IconMode)
        self.grid.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.grid.setMovement(QListWidget.Movement.Static)
        self.grid.setWordWrap(True)
        self.grid.setSpacing(12)
        from PyQt6.QtCore import QSize
        self.grid.setIconSize(QSize(110, 145))
        self.grid.setGridSize(QSize(245, 310))
        self.table = CatalogTable(self)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.pages.addWidget(self.grid)
        self.pages.addWidget(self.table)
        layout.addWidget(self.pages, 1)
        self.detail = QLabel("Select a book to see its formats.")
        self.detail.setWordWrap(True)
        layout.addWidget(self.detail)
        self.formats = QHBoxLayout()
        layout.addLayout(self.formats)
        self.edit_button = QPushButton("Edit metadata…")
        self.edit_button.setEnabled(False)
        self.edit_button.clicked.connect(self.edit_metadata)
        layout.addWidget(self.edit_button)
        self.import_button=imports=QPushButton('Import ebooks…');imports.setEnabled(bool(library) and self.compatibility_allowed);imports.clicked.connect(self.open_imports);layout.addWidget(imports)
        self.needs_review=QCheckBox('Show Needs Metadata Review only');self.needs_review.setChecked(saved_search.get('needs_review', False));self.needs_review.toggled.connect(self.search_changed);layout.addWidget(self.needs_review)
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(30000)
        self.refresh_timer.timeout.connect(self.auto_refresh)
        self.reader_timer = QTimer(self)
        self.reader_timer.setInterval(1000)
        self.reader_timer.timeout.connect(self.reader_progress_poll)
        self.reader_timer.start()
        if self.loader:
            self.refresh_timer.start()
        self.search.textChanged.connect(self.search_changed)
        self.filter_toggle.toggled.connect(self.search_changed)
        self.rebuild_filters()
        self.view.currentTextChanged.connect(self.change_view)
        self.grid.currentRowChanged.connect(self.select)
        self.table.currentCellChanged.connect(lambda row, *_: self.select(row))
        self.grid.model().checked.connect(self.sync_bulk_checks)
        self.table.model().checked.connect(self.sync_bulk_checks)
        self.render()

    def rebuild_filters(self):
        for key, (button, menu, label) in self.filter_buttons.items():
            choices = set(self.filter_values[key])
            for book in self.books:
                choices.update(book.tags if key == 'tags' else book.formats if key == 'formats' else [book.reading_status])
            menu.clear()
            for value in sorted(choices, key=str.casefold):
                action = menu.addAction(value); action.setCheckable(True)
                action.setChecked(value in self.filter_values[key])
                action.toggled.connect(lambda checked, k=key, v=value: self.filter_changed(k,v,checked))
            selected = sorted(self.filter_values[key])
            button.setText(label+(': '+', '.join(selected) if selected else ': All'))

    def filter_changed(self, key, value, checked):
        if checked:self.filter_values[key].add(value)
        else:self.filter_values[key].discard(value)
        self.search_changed()

    def search_changed(self, *_):
        self.filter_panel.setVisible(self.filter_toggle.isChecked())
        self.state['catalog_search'] = dict(text=self.search.text(),
            **{k:sorted(v) for k,v in self.filter_values.items()},
            expanded=self.filter_toggle.isChecked(), needs_review=self.needs_review.isChecked())
        self.save()
        # Change labels without rebuilding an open menu.
        for key,(button,menu,label) in self.filter_buttons.items():
            values=sorted(self.filter_values[key]); button.setText(label+(': '+', '.join(values) if values else ': All'))
        self.render()

    def clear_search_filters(self):
        self.search.blockSignals(True); self.search.clear(); self.search.blockSignals(False)
        self.needs_review.blockSignals(True); self.needs_review.setChecked(False); self.needs_review.blockSignals(False)
        for values in self.filter_values.values():values.clear()
        self.rebuild_filters(); self.search_changed()

    def bulk_item_changed(self, item):
        if self.rendering: return
        identity = item.data(Qt.ItemDataRole.UserRole)
        if not identity: return
        if item.checkState() == Qt.CheckState.Checked: self.bulk_selection.add(identity)
        else: self.bulk_selection.discard(identity)
        self.sync_bulk_checks()

    def sync_bulk_checks(self):
        self.rendering = True
        self.grid.model().refresh_checks(); self.table.model().refresh_checks()
        self.bulk_count.setText(f'{len(self.bulk_selection)} selected')
        self.rendering = False

    def select_all_bulk(self):
        self.bulk_selection.update(b.uuid for b in self.visible if b.uuid)
        self.sync_bulk_checks()

    def clear_bulk(self):
        self.bulk_selection.clear(); self.sync_bulk_checks()

    def bulk_active(self):
        return bool(self.bulk_dialog and self.bulk_dialog.busy)

    def open_bulk(self):
        if not self.library or self.import_active() or self.bulk_active() or (self.loader and self.loader.active) or not self.editor_review(): return
        if self.editor: self.editor.done(0)
        from .bulk_dialog import BulkDialog
        if self.bulk_dialog: self.bulk_dialog.close(); self.bulk_dialog.deleteLater()
        self.bulk_dialog = BulkDialog(self.library, self.window().store.path.parent/'bulk',
            [b for b in self.visible if b.uuid in self.bulk_selection] +
            [b for b in self.books if b.uuid in self.bulk_selection and b not in self.visible], self)
        self.bulk_dialog.activity=self.window().activity
        self.bulk_dialog.activity_controller=self.window().activity_controller
        self.bulk_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.bulk_dialog.on_changed = self.auto_refresh
        self.bulk_dialog.show()
        return self.bulk_dialog

    def sync_activity(self):
        if not self.library:return
        self.window().sync_local_activity(self.library)

    def discovery_context(self):
        import sqlite3
        from .discovery_store import DiscoveryStore
        if not self.library:raise ValueError('Choose and load a library first.')
        try:
            with sqlite3.connect((Path(self.library)/'metadata.db').resolve().as_uri()+'?mode=ro',uri=True) as db:
                row=db.execute('SELECT uuid FROM library_id LIMIT 1').fetchone()
                if not row or not row[0]:raise ValueError('Library identity unavailable.')
                uid=row[0]
        except sqlite3.Error as exc:raise ValueError('Cannot read library identity: '+str(exc)) from exc
        store=DiscoveryStore(self.window().store.path.parent/'discovery',self.library,uid,
            {k:self.state[k] for k in ('profile_id','device_id')})
        return store,store.load(),self.import_store().review_records()

    def review_index(self):
        if self.review_cache is None:
            from .discovery import DiscoveryIndex
            _,state,warnings=self.discovery_context()
            self.review_cache=DiscoveryIndex(self.books,state,warnings)
        return self.review_cache

    def open_discovery(self):
        if self.loader and self.loader.active:return
        try:
            from .discovery_ui import DiscoveryDialog
            if self.discovery_dialog:self.discovery_dialog.reload()
            else:self.discovery_dialog=DiscoveryDialog(self)
            self.discovery_dialog.show();self.discovery_dialog.raise_()
        except (OSError,ValueError) as exc:QMessageBox.warning(self,'Discovery unavailable',str(exc))

    def open_duplicates(self):
        if not self.library:return
        from .duplicate_ui import DuplicateDialog
        if not self.duplicate_dialog:self.duplicate_dialog=DuplicateDialog(self)
        self.duplicate_dialog.show();self.duplicate_dialog.raise_()

    def import_store(self):
        from .import_store import ImportStore
        return ImportStore(self.window().store.path.parent/'imports',self.library) if self.library else None

    def open_imports(self):
        from .import_dialog import ImportDialog
        if self.bulk_active() or not self.library or (self.loader and self.loader.active) or not self.editor_review():return
        if self.editor:self.editor.done(0)
        if not self.import_dialog:
            try:self.import_dialog=ImportDialog(self.library,self.window().store.path.parent/'imports',self)
            except (OSError,ValueError) as exc:
                QMessageBox.warning(self,'Import recovery unavailable',str(exc));return
            self.import_dialog.activity=self.window().activity
            self.import_dialog.activity_controller=self.window().activity_controller
            self.import_dialog.on_changed=self.auto_refresh
        self.import_dialog.show();self.import_dialog.raise_()
        return self.import_dialog

    def import_active(self):
        return bool(self.import_dialog and (self.import_dialog.busy or self.import_dialog.running))

    def signature(self):
        if not self.library:return None
        try:
            return tuple((p.name,p.stat().st_size,p.stat().st_mtime_ns) for p in (Path(self.library)/'metadata.db',Path(self.library)/'metadata.db-wal') if p.exists())
        except OSError:return None

    def editor_review(self):
        return self.editor is None or self.editor.review()

    def manual_refresh(self):
        if self.editor_review():
            self.auto_refresh(explicit=True)

    def set_compatibility(self, result):
        self.compatibility_allowed=result.verified
        self.import_button.setEnabled(bool(self.library) and result.verified)
        self.retry.setEnabled(result.verified and not (self.loader and self.loader.active))
        if not result.verified:self.note.setText('Catalog may be stale. '+result.message)
        self.render()

    def auto_refresh(self, explicit=False):
        if getattr(self, "recovery_handoff", False):
            self.refresh_deferred = True
            return
        if self.closing or getattr(self.window(),'closing',False) or not self.compatibility_allowed:return
        if (self.bulk_dialog and self.bulk_dialog.isVisible()) or self.bulk_active() or self.import_active() or not self.loader or self.loader.active or (self.editor and self.editor.busy):return
        if self.editor and self.editor.dirty():
            if self.signature()!=self.refresh_signature:
                self.note.setText('Library changed externally. Refresh pending until edits are saved or discarded.')
            return
        from .reader import external_readers
        if external_readers(include_calibre=True):
            self.note.setText('Waiting for library access... Close Calibre and readers; refresh retries automatically.')
            return
        self.loader.load()

    def edit_metadata(self, *, present=True):
        if self.bulk_active() or self.import_active():return
        from .editor import MetadataEditor
        book=next((b for b in self.books if b.id==self.state['selected_book']),None)
        if not book or not book.uuid or (self.loader and self.loader.active):return
        if self.editor:
            self.editor.show();self.editor.raise_();return
        root=self.window().store.path.parent/'metadata-recovery'
        self.editor=MetadataEditor(self.library,book,root,self)
        from .review_service import ReviewService
        self.editor.review_store=ReviewService(self)
        self.editor.activity=self.window().activity
        self.editor.recovery_store=self.window().recovery_store
        self.editor.on_saved=self.after_metadata
        self.editor.on_preserved=self.window().show_preservation_notice
        self.editor.finished.connect(self.editor_finished)
        if present:self.editor.show()
        self.editor.load()

    def editor_finished(self,*_):
        if self.editor:
            self.editor.deleteLater();self.editor=None
        self.auto_refresh()

    def reader_progress_poll(self):
        active = bool(self.reader and self.reader.active())
        if self.reader_was_active and not active:
            self.auto_refresh()
        self.reader_was_active = active

    def refresh_progress(self):
        if not self.library:
            return
        from .progress import ProgressStore, Progress
        import os, sqlite3
        from contextlib import closing
        try:
            with closing(sqlite3.connect((Path(self.library)/'metadata.db').resolve().as_uri()+'?mode=ro', uri=True)) as db:
                library_uuid = db.execute('SELECT uuid FROM library_id LIMIT 1').fetchone()[0]
            config = (Path(os.environ.get('CALIBRE_CONFIG_DIRECTORY', str(Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home()/'.config')))/'calibre')))
                      if self.live else Path(self.library).parent/'viewer-config')
            if self.progress_store is None:
                self.progress_store = ProgressStore(self.window().store.path.parent/'reading-progress.json',
                    str(Path(self.library).resolve())+'\0'+str(library_uuid), config/'viewer/annots')
            for book in self.books:
                values = {}
                for fmt, path in book.paths:
                    try: values[fmt] = self.progress_store.refresh(book.uuid, fmt, path)
                    except (OSError, ValueError): values[fmt] = Progress(issue='unavailable')
                self.book_progress[book.uuid] = values
        except (OSError, ValueError, sqlite3.Error, TypeError, KeyError, AttributeError):
            self.progress_store = None
            self.book_progress = {}

    def progress_summary(self, book):
        from .progress import latest_formats, progress_label
        values = self.book_progress.get(book.uuid, {})
        latest = latest_formats(values)
        if len(latest) == 1:
            return latest[0]+'\n'+progress_label(values[latest[0]])
        if len(latest) > 1:
            return 'Latest reading time shared by '+', '.join(latest)+'\nProgress: Unknown\nStatus: Unknown'
        return 'Progress: Unknown\nStatus: Unknown'

    def after_metadata(self):
        self.auto_refresh()

    def loading(self, active):
        if self.duplicate_dialog:self.duplicate_dialog.library_loading(active)
        self.load_progress.setVisible(active);self.cancel_load.setVisible(active)
        self.retry.setEnabled(not active and self.compatibility_allowed)
        if active:
            self.note.setText("Loading library…")

    def loaded(self, books):
        self.review_cache=None
        self.books = books
        self.rebuild_filters()
        self.refresh_progress()
        if hasattr(self.window(),'activity'):self.window().activity.invoke('resolve_notice','Catalog refresh',str(self.library))
        self.bulk_selection.intersection_update(b.uuid for b in books)
        if self.library and not self.recovery_checked:
            self.recovery_checked=True
            try:
                self.sync_activity()
            except (OSError,ValueError) as exc:
                self.window().activity.record('Recovery discovery',str(self.library),outcome='failure',pending=True,
                    source=dict(kind='recovery_discovery',library=str(self.library)),details=dict(error=str(exc)),deduplicate=True)
                self.window().statusBar().showMessage('Import recovery data unavailable: '+str(exc))
        from .bulk import BulkStore
        try:
            pending = BulkStore(self.window().store.path.parent/'bulk', self.library).pending() if self.library else []
            self.bulk_recovery.setText(f'{len(pending)} bulk batches await Review / Retry Pending / Discard Pending in Bulk edit / history.' if pending else '')
            self.bulk_count.setToolTip(f'{len(pending)} bulk batches have pending work. Open Bulk edit / history to Review / Retry Pending or Discard Pending.')
        except (OSError, ValueError) as exc:
            self.bulk_count.setToolTip('Bulk history unavailable: '+str(exc))
        self.refresh_signature = self.signature()
        if self.editor and not self.editor.busy and not self.editor.dirty():
            self.editor.load()
        self.note.setText("Library loaded · One hub-launched reader at a time.")
        self.render(preserve_editor=True)
        if self.discovery_dialog:self.discovery_dialog.reload()
        if self.duplicate_dialog:self.duplicate_dialog.catalog_refreshed()

    def load_failed(self, message):
        self.note.setText("Load failed. Previous results may be out of date. " + message)
        if hasattr(self.window(),'activity'):
            self.window().activity.record('Catalog refresh',str(self.library),outcome='interrupted' if 'cancelled' in message.lower() else 'failure',pending=True,
                source=dict(kind='refresh',library=str(self.library)),details=dict(error=message),deduplicate=True)

    def open_format(self, path):
        if self.bulk_active() or self.import_active():return
        if self.editor and (self.editor.busy or self.editor.dirty()):
            self.note.setText('Save or discard metadata before launching a reader, then wait for catalog refresh.')
            return
        if self.loader and self.loader.active:return
        try:
            resume = None
            if self.progress_store:
                match = next(((b.uuid, f) for b in self.books for f, p in b.paths if p == str(path)), None)
                if match:
                    resume = lambda: self.progress_store.resume_args(*match, Path(path))
            if resume:
                self.reader.launch(self.library, Path(path), resume=resume)
            else:
                self.reader.launch(self.library, Path(path))
            self.reader_was_active = True
            self.window().activity.invoke('resolve_notice','Reader launch',str(self.library)+'\0'+str(path))
            self.note.setText("Reader launched. Close it before opening another book. Rendering and annotation saving are controlled by Calibre.")
        except (ReaderError, OSError, ValueError) as exc:
            self.window().activity.record('Reader launch',str(self.library)+'\0'+str(path),outcome='failure',pending=True,
                source=dict(kind='reader_launch',library=str(self.library),path=str(path)),details=dict(error=str(exc)),deduplicate=True)
            QMessageBox.warning(self, "Cannot open reader", str(exc))

    def change_view(self, value):
        self.state["view"] = value
        self.pages.setCurrentIndex(0 if value == "Grid" else 1)
        self.save()

    def render(self, *, preserve_editor=False):
        self.rendering = True
        books=self.books
        if self.needs_review.isChecked() and self.library:
            try:
                from .discovery import empty_query
                books=self.review_index().query(empty_query(),review_only=True)
            except (OSError,ValueError) as exc:self.note.setText('Review status unavailable: '+str(exc))
        self.visible = find_books(books, self.search.text(), **self.filter_values)
        if self.sort.currentIndex() == 1: self.visible.reverse()
        elif self.sort.currentIndex() == 2: self.visible.sort(key=lambda b: (b.author.casefold(), b.title.casefold()))
        self.grid.model().replace(self.visible)
        self.table.model().replace(self.visible)
        self.pages.setCurrentIndex(0 if self.state["view"] == "Grid" else 1)
        self.count.setText(f"{len(self.visible)} of {len(self.books)} books" if self.visible else "No books match this search.")
        selected = next((i for i, b in enumerate(self.visible) if b.id == self.state["selected_book"]), -1)
        self.rendering = False
        self.select(selected, review_editor=not preserve_editor)
        self.bulk_count.setText(f'{len(self.bulk_selection)} selected')

    def select(self, row, *, review_editor=True):
        if self.rendering:
            return
        target = self.visible[row].id if 0 <= row < len(self.visible) else None
        # Catalog refresh is not a user request to leave the open book.
        if review_editor and self.editor and target != self.editor.book.id:
            if not self.editor_review():
                old = next((i for i,b in enumerate(self.visible) if b.id==self.editor.book.id),-1)
                self.rendering=True
                self.grid.setCurrentRow(old)
                if old>=0:self.table.setCurrentCell(old,0)
                self.rendering=False
                return
            self.editor.done(0)
        self.rendering = True
        self.edit_button.setEnabled(bool(target and self.library) and self.compatibility_allowed)
        self.grid.setCurrentRow(row)
        if row >= 0:
            self.table.setCurrentCell(row, 0)
        else:
            self.table.clearSelection()
            self.table.setCurrentCell(-1, -1)
        while self.formats.count():
            widget = self.formats.takeAt(0).widget()
            if widget:
                widget.hide()
                widget.deleteLater()
        if 0 <= row < len(self.visible):
            book = self.visible[row]
            self.detail.setText(f"{book.title} — {book.author}\nReading status: {book.reading_status}")
            from .progress import progress_label
            values = self.book_progress.get(book.uuid, {})
            self.detail.setText(self.detail.text()+'\n'+'\n'.join(fmt+': '+progress_label(p) for fmt,p in values.items()))
            for fmt in book.formats:
                button = QPushButton(fmt)
                path = dict(book.paths).get(fmt)
                button.setEnabled(bool(path) and self.compatibility_allowed)
                button.setToolTip(path or "Sample record: no file attached.")
                button.clicked.connect(lambda checked=False, p=path: self.open_format(p))
                self.formats.addWidget(button)
            self.formats.addStretch()
            if self.state["selected_book"] != book.id:
                self.state["selected_book"] = book.id
                self.save()
        else:
            self.detail.setText("Select a book to see its formats.")
        self.rendering = False


class Hub(QMainWindow):
    def __init__(self, store, state, library=None, live=False, app_data=None, movie_catalog=None, music_catalog=None,
                 paper_library=None):
        super().__init__()
        self.store, self.state = store, state
        from .appearance import AppearanceController
        self.appearance = AppearanceController(store, state, self)
        self.appearance_dialog = None
        from .activity import ActivityStore, ActivityBridge
        from .recovery import RecoveryStore
        self.app_data=Path(app_data) if app_data else store.path.parent/'data'
        self.activity=ActivityBridge(ActivityStore(self.app_data/'Activity',state['profile_id'],state['device_id']),
                                     lambda message:self.statusBar().showMessage(message))
        self.recovery_store=RecoveryStore(self.app_data,state['profile_id'],state['device_id'],self.activity)
        from .recovery_actions import ActivityController
        self.activity_controller = ActivityController(self)
        self.live = live
        self.library = Path(state["library"]) if live and state.get("library") else library
        self.reader = Reader(state, self.persist, live=live, log_dir=store.path.parent)
        self.closing = False
        self.ready = False
        self.bookinator = None
        self.movieinator = None
        self.movie_catalog = movie_catalog
        self.musicinator = None
        self.music_catalog = music_catalog
        self.paperinator = None
        self.paper_library = paper_library
        self.prerequisites = None
        self.initial_books_pending = False
        self.help_dialog = None
        self.diagnostics_dialog = None
        self.workspace_dialog = None
        workspace_menu = self.menuBar().addMenu('Workspaces')
        workspace_menu.addAction('Manage named workspaces…').triggered.connect(self.show_workspaces)
        help_menu=self.menuBar().addMenu('Help')
        help_action=QAction('User guide',self);help_action.setShortcut(QKeySequence.StandardKey.HelpContents)
        help_action.triggered.connect(lambda:self.show_help('User guide'));help_menu.addAction(help_action)
        troubleshooting=help_menu.addAction('Troubleshooting');troubleshooting.triggered.connect(lambda:self.show_help('Troubleshooting'))
        installation=help_menu.addAction('Installation and upgrades');installation.triggered.connect(lambda:self.show_help('Installation and upgrades'))
        diagnostic=help_menu.addAction('Preview redacted diagnostics…');diagnostic.triggered.connect(self.show_diagnostics)
        about=help_menu.addAction('About Media-inator');about.triggered.connect(self.show_about)
        from .installation import window_title
        self.setWindowTitle(window_title())
        self.resize(1050, 760)
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        central = QWidget()
        self.main_layout = QVBoxLayout(central)
        self.preservation_notice=QLabel();self.preservation_notice.setWordWrap(True);self.preservation_notice.hide()
        self.main_layout.addWidget(self.preservation_notice)
        self.main_layout.addWidget(self.tabs)
        self.setCentralWidget(central)
        home = QWidget()
        layout = QVBoxLayout(home)
        title = QLabel("Media-inator Hub")
        layout.addWidget(title)
        layout.addWidget(QLabel(f"Profile: {state['profile_name']}"))
        info = QLabel("Open a module or adjust shared appearance settings. Planned modules are not yet available." if live else "Development preview using sample or disposable-library data.")
        info.setWordWrap(True)
        layout.addWidget(info)
        from .modules import MODULES, launch_module
        settings_button = QPushButton("Settings…")
        settings_button.clicked.connect(self.show_appearance)
        layout.addWidget(settings_button)
        tiles = QWidget(); grid = QGridLayout(tiles)
        self.module_tiles = {}
        for index, module in enumerate(MODULES):
            tile = QPushButton(module.name + ("" if module.available else " — Planned"))
            tile.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView if module.available else QStyle.StandardPixmap.SP_FileIcon))
            tile.setEnabled(module.available)
            tile.setToolTip(module.description if module.available else module.description + ". This module is planned for a future release and is not yet available.")
            tile.clicked.connect(lambda checked=False, mid=module.id: launch_module(mid, self))
            self.module_tiles[module.id] = tile
            grid.addWidget(tile, index // 3, index % 3)
        scroller = QScrollArea(); scroller.setWidgetResizable(True); scroller.setWidget(tiles)
        layout.addWidget(scroller, 1)
        if live:
            from .prerequisites import Prerequisites
            self.prerequisites=Prerequisites(self)
            layout.addWidget(self.prerequisites)
        from .activity_panel import ActivityPanel
        self.activity_panel = ActivityPanel(self.activity, home, lambda: self.tabs.setCurrentWidget(home))
        self.activity_panel.controller = self.activity_controller
        self.activity_panel.toggle.setChecked(False)
        layout.addWidget(self.activity_panel)
        self.main_layout.insertWidget(0, self.activity_panel.startup)
        self.tabs.addTab(home, "Hub")
        # The hub itself is closed through the main window, never as a module tab.
        from PyQt6.QtWidgets import QTabBar
        for side in (QTabBar.ButtonPosition.LeftSide, QTabBar.ButtonPosition.RightSide):
            self.tabs.tabBar().setTabButton(0, side, None)
        if state["geometry"]:
            self.restoreGeometry(QByteArray(bytes.fromhex(state["geometry"])))
        self.geometry_timer = QTimer(self)
        self.geometry_timer.setSingleShot(True)
        self.geometry_timer.setInterval(250)
        self.geometry_timer.timeout.connect(self.save_geometry)
        self.ready = True
        self.activity.invoke('recover_interrupted')
        self.sync_local_activity()
        try:self.recovery_store.sync_activity()
        except (OSError,ValueError) as exc:self.statusBar().showMessage("Recovery discovery unavailable: "+str(exc))
        if live:
            self.initial_books_pending=bool(state["bookinator_open"])
            if state["bookinator_open"]:self.open_books()
            QTimer.singleShot(0,self.prerequisites.check)
        elif state["bookinator_open"]:
            self.open_books()
        if state.get("musicinator_open"):
            self.open_music()
        if state.get("movieinator_open"):
            self.open_movies()
        if state.get("paperinator_open"):
            self.open_papers()
        self.persist()
        from .workspace_restore import WorkspaceController
        self.workspaces=WorkspaceController(self)

    def show_appearance(self):
        from .appearance import AppearanceDialog
        if self.appearance_dialog is None:
            self.appearance_dialog = AppearanceDialog(self.appearance, self)
        self.appearance_dialog.show()
        self.appearance_dialog.raise_()
        self.appearance_dialog.activateWindow()

    def show_workspaces(self):
        from .workspace_ui import WorkspaceDialog, check_idle
        from .workspaces import WorkspaceError
        import sqlite3
        try:
            check_idle(self)
            if self.workspace_dialog is None:
                self.workspace_dialog = WorkspaceDialog(self)
            else:
                self.workspace_dialog.reload()
            self.workspace_dialog.show(); self.workspace_dialog.raise_()
        except (WorkspaceError, OSError, sqlite3.Error) as exc:
            QMessageBox.warning(self, 'Workspace unavailable', str(exc))

    def show_help(self,topic='User guide'):
        from .help_ui import HelpDialog
        if self.help_dialog is None:self.help_dialog=HelpDialog(self,topic)
        else:self.help_dialog.topics.setCurrentText(topic)
        self.help_dialog.show();self.help_dialog.raise_();self.help_dialog.activateWindow()

    def show_diagnostics(self):
        from .diagnostics_ui import DiagnosticsDialog
        if self.diagnostics_dialog and self.diagnostics_dialog.isVisible():
            self.diagnostics_dialog.raise_();return
        if self.diagnostics_dialog:self.diagnostics_dialog.deleteLater()
        self.diagnostics_dialog=DiagnosticsDialog(self)
        self.diagnostics_dialog.show()

    def show_about(self):
        from .help_ui import about_text
        QMessageBox.about(self,'About Media-inator',about_text())

    def sync_local_activity(self, library=None):
        """Discover local journals even when the catalog/module stays closed."""
        library = library or self.library
        if not library:
            return
        from .import_store import ImportStore
        from .bulk import BulkStore
        try:
            imports = ImportStore(self.store.path.parent/'imports', library)
            imports.review_records()
            for path, batch in imports.batches():
                self.activity.batch(batch, path, 'import', legacy=True)
            bulk = BulkStore(self.store.path.parent/'bulk', library)
            for batch in bulk.batches():
                self.activity.batch(batch, bulk.folder/(batch['id']+'.json'), 'bulk', legacy=True)
            self.activity.invoke('resolve_notice', 'Recovery discovery', str(library))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            self.activity.record('Recovery discovery', str(library), outcome='failure', pending=True,
                source=dict(kind='discovery', library=str(library)), details=dict(error=str(exc)), deduplicate=True)

    def show_preservation_notice(self, message):
        self.preservation_notice.setText(message);self.preservation_notice.show()

    def persist(self):
        try:
            self.store.save(self.state)
            self.activity.invoke('resolve_notice','Settings save',str(self.store.path),module='hub')
            self.statusBar().showMessage("Calibre library · Private-snapshot browsing" if self.live and self.library else "Choose a Calibre library" if self.live else "Development preview · Disposable library" if self.library else "Development preview · Sample data")
            return True
        except SettingsError as exc:
            self.activity.record('Settings save',str(self.store.path),module='hub',outcome='failure',pending=True,
                source=dict(kind='settings',path=str(self.store.path)),details=dict(error=str(exc)),deduplicate=True)
            self.statusBar().showMessage(f"Settings not saved: {exc}")
            return False

    def open_books(self):
        if self.bookinator is None:
            self.bookinator = Bookinator(self.state, self.persist, self.library, self.reader, self.live, self.choose_library if self.live else None)
            self.tabs.addTab(self.bookinator, "Book-inator")
            if self.prerequisites and self.prerequisites.result:self.bookinator.set_compatibility(self.prerequisites.result)
            if self.live and self.prerequisites and self.prerequisites.result and self.prerequisites.result.verified and self.bookinator.loader:
                QTimer.singleShot(0,self.bookinator.loader.load)
        self.tabs.setCurrentWidget(self.bookinator)
        self.state["bookinator_open"] = True
        self.persist()

    def movie_store(self):
        """Movie-inator catalog: Media-inator application data, never a media folder.
        Sample/development mode without an explicit catalog stays read-only."""
        from .movie_store import MovieStore
        if self.movie_catalog:
            return MovieStore(self.movie_catalog, self.state['profile_id'])
        if self.live:
            return MovieStore(self.app_data/'Movies'/'catalog.sqlite', self.state['profile_id'])
        return None

    def open_movies(self):
        if self.movieinator is None:
            from .movie_ui import Movieinator
            self.movieinator = Movieinator(self.state, self.persist, self.movie_store(), self.activity)
            self.tabs.addTab(self.movieinator, "Movie-inator")
        self.tabs.setCurrentWidget(self.movieinator)
        self.state["movieinator_open"] = True
        self.persist()

    def remove_movies(self):
        """Close the Movie-inator tab after its review has passed."""
        panel = self.movieinator
        if panel is None:
            return
        panel.shutdown()
        self.tabs.removeTab(self.tabs.indexOf(panel))
        panel.deleteLater()
        self.movieinator = None
        self.state["movieinator_open"] = False

    def music_store(self):
        """Music-inator catalog: Media-inator application data, never a music folder.
        Sample/development mode without an explicit catalog stays read-only."""
        from .music_store import MusicStore
        if self.music_catalog:
            return MusicStore(self.music_catalog, self.state['profile_id'])
        if self.live:
            return MusicStore(self.app_data/'Music'/'catalog.sqlite', self.state['profile_id'])
        return None

    def open_music(self):
        if self.musicinator is None:
            from .music_ui import Musicinator
            store = self.music_store()
            # Play album writes its playlist to application data, beside the catalog.
            playlists = store.path.parent/'playlists' if store is not None else None
            self.musicinator = Musicinator(self.state, self.persist, store, self.activity, playlists)
            self.tabs.addTab(self.musicinator, "Music-inator")
        self.tabs.setCurrentWidget(self.musicinator)
        self.state["musicinator_open"] = True
        self.persist()

    def remove_music(self):
        """Close the Music-inator tab after its review has passed."""
        panel = self.musicinator
        if panel is None:
            return
        panel.shutdown()
        self.tabs.removeTab(self.tabs.indexOf(panel))
        panel.deleteLater()
        self.musicinator = None
        self.state["musicinator_open"] = False

    def paper_store(self):
        """Paper-inator library of the active profile: Media-inator application data,
        one directory per stable profile id. Sample/development mode without an explicit
        library stays read-only and creates nothing."""
        from .paper_store import PaperStore
        profile = self.state['profile_id']
        if self.paper_library:
            return PaperStore(Path(self.paper_library)/'profiles'/profile, profile)
        if self.live:
            return PaperStore(self.app_data/'Paper'/'profiles'/profile, profile)
        return None

    def open_papers(self):
        if self.paperinator is None:
            from .paper_ui import Paperinator
            self.paperinator = Paperinator(self.state, self.persist, self.paper_store(), self.activity)
            self.tabs.addTab(self.paperinator, "Paper-inator")
        self.tabs.setCurrentWidget(self.paperinator)
        self.state["paperinator_open"] = True
        self.persist()

    def remove_papers(self):
        """Close the Paper-inator tab after its review has passed."""
        panel = self.paperinator
        if panel is None:
            return
        panel.shutdown()
        self.tabs.removeTab(self.tabs.indexOf(panel))
        panel.deleteLater()
        self.paperinator = None
        self.state["paperinator_open"] = False

    def stop_background_reads(self):
        if self.prerequisites:self.prerequisites.shutdown()
        if self.bookinator:
            self.bookinator.closing=True
            if self.bookinator.duplicate_dialog:self.bookinator.duplicate_dialog.shutdown()
            self.bookinator.refresh_timer.stop()
            loader=self.bookinator.loader
            if loader:
                loader.shutdown()

    def release_snapshot(self):
        loader = self.bookinator.loader if self.bookinator else None
        if loader and getattr(loader, 'snapshot', None):
            loader.snapshot.close()
            loader.snapshot = None

    def choose_library(self):
        controller=getattr(self,'activity_controller',None)
        if controller and controller.pending_review:controller.pending_review['cancel']()
        if self.workspaces.transaction is not None:
            self.workspaces.abort('Restore cancelled before changing library; choose the library again when ready')
            return
        from .compatibility import require_compatible, CompatibilityError
        try:require_compatible()
        except CompatibilityError as exc:
            QMessageBox.information(self,"Calibre prerequisite",str(exc));return
        if self.bookinator and (self.bookinator.bulk_active() or self.bookinator.import_active()):return
        if self.bookinator and not self.bookinator.editor_review():return
        if self.bookinator and self.bookinator.loader and self.bookinator.loader.active:
            QMessageBox.information(self, "Loading", "Wait for the current library load before changing libraries.")
            return
        chosen = QFileDialog.getExistingDirectory(self, "Choose Calibre library")
        if not chosen:
            return
        root = Path(chosen).resolve()
        if not (root / 'metadata.db').is_file():
            QMessageBox.warning(self, "Not a Calibre library", "Choose the folder containing metadata.db.")
            return
        previous = self.state.get('library')
        self.state['library'] = str(root)
        if not self.persist():
            self.state['library'] = previous
            return
        self.library = root
        if self.bookinator:
            self.stop_background_reads()
            self.release_snapshot()
            old = self.bookinator
            self.tabs.removeTab(self.tabs.indexOf(old))
            old.deleteLater()
            self.bookinator = None
        self.open_books()

    def close_tab(self, index):
        controller=getattr(self,'activity_controller',None)
        if controller and controller.pending_review:controller.pending_review['cancel']()
        if hasattr(self,'workspaces') and self.workspaces.transaction is not None:
            self.workspaces.abort('Restore cancelled before module close; close the tab again if needed')
            return
        if index == 0 or self.closing:
            return
        if self.movieinator is not None and self.tabs.widget(index) is self.movieinator:
            self.closing=True
            if self.movieinator.review_close():
                self.remove_movies()
                self.persist()
            self.closing=False
            return
        if self.paperinator is not None and self.tabs.widget(index) is self.paperinator:
            self.closing=True
            if self.paperinator.review_close():
                self.remove_papers()
                self.persist()
            self.closing=False
            return
        if self.musicinator is not None and self.tabs.widget(index) is self.musicinator:
            self.closing=True
            if self.musicinator.review_close():
                self.remove_music()
                self.persist()
            self.closing=False
            return
        if self.tabs.widget(index) is not self.bookinator:
            return
        self.closing=True
        if not self.review_books_close():
            self.closing=False
            return
        self.stop_background_reads()
        self.release_snapshot()
        self.tabs.removeTab(index)
        self.bookinator.deleteLater()
        self.bookinator = None
        self.state["bookinator_open"] = False
        self.closing=False
        self.persist()

    def review_close(self):
        """Suite exit review: every open module. Paper-inator, Music-inator and Movie-inator
        first (they never close external readers or players), then Book-inator's
        editor/reader/refresh review."""
        from .close_review import collect, apply_editors
        editors, tasks = [], []
        for name, panel in [('Paper-inator', self.paperinator), ('Music-inator', self.musicinator), ('Movie-inator', self.movieinator)]:
            if panel is None:
                continue
            drafts = getattr(panel, 'editors', None)
            if drafts is None:
                drafts = [panel.editor] if panel.editor is not None else []
            editors.extend(e for e in drafts if e.dirty())
            if panel.busy():
                tasks.append((name + ' import', panel.import_dialog.stop))
        module_attention = bool(editors or tasks)
        book_editor = self.bookinator.editor if self.bookinator else None
        if book_editor and book_editor.dirty():
            editors.append(book_editor)
        if self.bookinator:
            if self.bookinator.bulk_active():
                tasks.append(('Book-inator bulk operation', self.bookinator.bulk_dialog.stop))
            if self.bookinator.import_active():
                tasks.append(('Book-inator import', self.bookinator.import_dialog.stop))
            loader = self.bookinator.loader
            if loader and (loader.active or (getattr(loader, 'worker', None) and loader.worker.isRunning())):
                tasks.append(('Book-inator refresh', loader.cancel))
        if module_attention and len(editors) + len(tasks) + bool(self.reader.active()) > 1:
            if book_editor and book_editor.busy:
                book_editor.status.setText('Wait for the metadata operation before closing.')
                return False
            decision = collect(self, editors, tasks, self.reader.active())
            if decision is None:
                return False
            choices, stops, reader_choice = decision
            if tasks:
                for stop in stops:
                    stop()
                return False
            book_action = next((action for editor, action in choices if editor is book_editor), None)
            if not self.review_books_close(prepared=(book_action, reader_choice)):
                return False
            return apply_editors([(editor, action) for editor, action in choices if editor is not book_editor])
        if self.paperinator is not None and not self.paperinator.review_close():
            return False
        if self.musicinator is not None and not self.musicinator.review_close():
            return False
        if self.movieinator is not None and not self.movieinator.review_close():
            return False
        return self.review_books_close()

    def review_books_close(self, prepared=None):
        if self.bookinator and self.bookinator.bulk_active():
            if QMessageBox.question(self, 'Bulk operation in progress', 'Stop after verifying the current book? Pending work will be retained. Close again when verification finishes.', QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
                self.bookinator.bulk_dialog.stop()
            return False
        if self.bookinator and self.bookinator.import_active():
            if QMessageBox.question(self,'Import in progress','Stop after verifying the current item? Pending imports will be saved for review after restart. Close again when stopping completes.',QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)==QMessageBox.StandardButton.Yes:
                self.bookinator.import_dialog.stop()
            return False
        editor = self.bookinator.editor if self.bookinator else None
        combined_action = None
        reader_choice = None
        loader = self.bookinator.loader if self.bookinator else None
        loading = bool(loader and (loader.active or (getattr(loader,'worker',None) and loader.worker.isRunning())))
        combined_interrupt = False
        if editor and editor.busy:
            editor.status.setText('Metadata operation is running. Wait for verification before closing.')
            return False
        if prepared is not None:
            combined_action, reader_choice = prepared
            if combined_action == 'save' and reader_choice == 'keep':
                QMessageBox.information(self, 'Reader must close before Save', 'Choose Close reader to save Book-inator metadata.')
                return False
        elif editor and editor.dirty() and (self.reader.active() or loading):
            from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QCheckBox
            dialog=QDialog(self);dialog.setWindowTitle('Review metadata and reader before closing')
            layout=QVBoxLayout(dialog)
            layout.addWidget(QLabel('Book-inator has unsaved metadata. Review all active work before closing.'))
            edits=QComboBox();edits.addItems(['Save metadata','Discard pending metadata'])
            reader=QComboBox();reader.addItems(['Close reader','Leave reader open'])
            layout.addWidget(edits)
            if self.reader.active():layout.addWidget(reader)
            interrupt=QCheckBox('Interrupt the running catalog refresh and continue')
            if loading:layout.addWidget(interrupt)
            layout.addWidget(QLabel('Saving requires the reader to close first. Cancel stops the entire close.'))
            buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel)
            buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject);layout.addWidget(buttons)
            if dialog.exec()!=QDialog.DialogCode.Accepted:return False
            combined_action='save' if edits.currentIndex()==0 else 'discard'
            reader_choice=('close' if reader.currentIndex()==0 else 'keep') if self.reader.active() else None
            if loading and not interrupt.isChecked():return False
            combined_interrupt=loading
            if combined_action=='save' and reader_choice=='keep':
                QMessageBox.information(self,'Reader must close before Save','Choose Close reader to save, or Discard pending metadata to leave it open.')
                return False
        elif editor and not editor.review(closing=True):return False
        loader = self.bookinator.loader if self.bookinator else None
        if loader and (loader.active or (getattr(loader, 'worker', None) and loader.worker.isRunning())):
            answer = QMessageBox.StandardButton.Yes if combined_interrupt else QMessageBox.question(self, "Interrupt library loading?",
                "Loading is still running. Cancel loading and continue closing? The source library will not be changed.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if answer != QMessageBox.StandardButton.Yes:
                return False
            loader.cancel()
            from PyQt6.QtCore import QEventLoop
            loop = QEventLoop(self)
            poll = QTimer(self)
            poll.setInterval(50)
            poll.timeout.connect(lambda: loop.quit() if not loader.active and not (getattr(loader, 'worker', None) and loader.worker.isRunning()) else None)
            poll.start()
            self.setEnabled(False)
            loop.exec()
            self.setEnabled(True)
            poll.stop()
            poll.deleteLater()
            loop.deleteLater()
        if self.reader.active():
            if reader_choice is None:
                dialog = QMessageBox(self)
                dialog.setWindowTitle("Review reader before closing")
                dialog.setText("A reader belongs to this profile. Choose what should happen before closing.")
                close = dialog.addButton("Close reader", QMessageBox.ButtonRole.AcceptRole)
                keep = dialog.addButton("Leave reader open", QMessageBox.ButtonRole.DestructiveRole)
                cancel = dialog.addButton(QMessageBox.StandardButton.Cancel)
                dialog.setDefaultButton(cancel)
                dialog.exec()
                if dialog.clickedButton() is keep:reader_choice='keep'
                elif dialog.clickedButton() is close:reader_choice='close'
                else:return False
            if reader_choice=='keep':
                return editor.discard() if combined_action=='discard' else True
            try:
                self.reader.request_close()
            except (ReaderError, OSError, TimeoutError) as exc:
                QMessageBox.warning(self, "Reader could not close", str(exc))
                return False
            # Let the reader save asynchronously; never force-kill on a timeout.
            from PyQt6.QtCore import QEventLoop
            loop = QEventLoop(self)
            poll = QTimer(self)
            poll.setInterval(100)
            poll.timeout.connect(lambda: loop.quit() if not self.reader.active() else None)
            deadline = QTimer(self)
            deadline.setSingleShot(True)
            deadline.timeout.connect(loop.quit)
            self.setEnabled(False)
            poll.start()
            deadline.start(15000)
            loop.exec()
            poll.stop()
            deadline.stop()
            poll.deleteLater()
            deadline.deleteLater()
            loop.deleteLater()
            self.setEnabled(True)
            if self.reader.active():
                QMessageBox.warning(self, "Reader still open", "Reader did not close in time. Retry the close action, leave it open, or cancel. It has not been force-closed.")
                return False
        if combined_action=='save':return editor.save_for_close()
        if combined_action=='discard':return editor.discard()
        return True

    def changeEvent(self,event):
        super().changeEvent(event)
        if event.type()==QEvent.Type.ActivationChange and self.isActiveWindow() and self.bookinator:
            QTimer.singleShot(0,self.bookinator.auto_refresh)
        if event.type()==QEvent.Type.ActivationChange and self.isActiveWindow() and self.movieinator:
            QTimer.singleShot(0,self.movieinator.auto_refresh)
        if event.type()==QEvent.Type.ActivationChange and self.isActiveWindow() and self.musicinator:
            QTimer.singleShot(0,self.musicinator.auto_refresh)
        if event.type()==QEvent.Type.ActivationChange and self.isActiveWindow() and self.paperinator:
            QTimer.singleShot(0,self.paperinator.auto_refresh)

    def save_geometry(self):
        self.state["geometry"] = bytes(self.saveGeometry()).hex()
        return self.persist()

    def moveEvent(self, event):
        super().moveEvent(event)
        if self.ready:
            self.geometry_timer.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.ready:
            self.geometry_timer.start()

    def commit_shutdown(self, manager):
        """Honor cooperative desktop shutdown; never bypass review without interaction."""
        if manager.allowsInteraction():
            if not self.close():manager.cancel()
            return
        books=self.bookinator
        loader=books.loader if books else None
        editor=books.editor if books else None
        if (self.reader.active() or (books and (books.bulk_active() or books.import_active()))
                or (loader and (loader.active or (getattr(loader,'worker',None) and loader.worker.isRunning())))
                or (editor and (editor.busy or editor.dirty()))
                or (self.movieinator and self.movieinator.unattended_close_blocked())
                or (self.musicinator and self.musicinator.unattended_close_blocked())
                or (self.paperinator and self.paperinator.unattended_close_blocked())):
            manager.cancel();return
        if not self.save_geometry():manager.cancel()

    def closeEvent(self, event):
        controller=getattr(self,'activity_controller',None)
        if controller and controller.pending_review:controller.pending_review['cancel']()
        if self.closing:
            event.ignore();return
        self.closing=True
        self.geometry_timer.stop()
        if not self.review_close():
            self.closing=False
            event.ignore()
            return
        if hasattr(self,'workspaces') and not self.workspaces.flush(closing=True):
            QMessageBox.warning(self, 'Workspace could not be saved', 'The Hub will stay open. Resolve the workspace storage problem and retry.')
            self.closing=False;event.ignore();return
        if not self.save_geometry():
            QMessageBox.warning(self, "Settings could not be saved", "The hub will stay open. Resolve the settings-file problem and try closing again.")
            self.closing=False
            event.ignore()
            return
        self.stop_background_reads()
        self.release_snapshot()
        if self.movieinator:self.movieinator.shutdown()
        if self.musicinator:self.musicinator.shutdown()
        if self.paperinator:self.paperinator.shutdown()
        # KWin may separately close the editor after approving this Hub close.
        if self.bookinator and self.bookinator.editor:
            self.bookinator.editor.approve_parent_close()
        if self.help_dialog:self.help_dialog.close()
        if self.diagnostics_dialog:self.diagnostics_dialog.close()
        # Preserve the module selection from before suite shutdown.
        event.accept()
