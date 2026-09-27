"""Movie-inator module tab, detail editor, editions/copies and import dialogs.

Mirrors Book-inator's conventions: Grid/List over one filtered list, remembered search,
explicit Save / Discard / Cancel for detail edits, a preview that must be confirmed
before any import writes, and nothing that moves, renames or deletes media files.
"""
from pathlib import Path
from uuid import uuid4

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, QObject, QSize, Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QGroupBox,
    QHBoxLayout, QInputDialog, QLabel, QLineEdit, QListView, QMenu, QMessageBox, QPlainTextEdit, QPushButton,
    QStackedWidget, QTableView, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from .movie_catalog import EDITION_FORMATS, SAMPLE_MOVIES, STATUSES, WATCHED, find_movies, sort_key
from .movie_store import ConflictError, MovieStoreError, validate_movie

SORTS = ('Title A–Z', 'Title Z–A', 'Year (newest first)', 'Year (oldest first)')
COLUMNS = ('Title', 'Year', 'Director', 'Genres', 'Formats', 'Status', 'Rating')


def poster(movie, cover_cache=None):
    if movie.cover:
        icon = QIcon(movie.cover)
        if not icon.isNull():
            return icon
    image = QPixmap(110, 160)
    image.fill(QColor('#3b3350'))
    painter = QPainter(image)
    painter.setPen(QColor('#ffffff'))
    font = painter.font(); font.setPointSize(22); painter.setFont(font)
    painter.drawText(image.rect(), Qt.AlignmentFlag.AlignCenter, (movie.title or '?')[0])
    painter.end()
    return QIcon(image)


def split_names(text):
    return [line.strip() for line in text.replace(';', '\n').splitlines() if line.strip()]


def split_list(text):
    return [part.strip() for part in text.split(',') if part.strip()]


def activity_bridge(owner):
    """The Hub's activity bridge, or None when running outside the Hub."""
    bridge = getattr(owner, 'activity', None)
    if bridge is not None:
        return bridge
    hub = owner.window() if isinstance(owner, QWidget) else None
    return getattr(hub, 'activity', None) if hub is not None and hub is not owner else None


def activity_record(owner, operation, key, **kwargs):
    """Record through the Hub's activity bridge when present; never raise."""
    bridge = activity_bridge(owner)
    if bridge is None:
        return
    try:
        bridge.record(operation, key, module='movieinator', **kwargs)
    except Exception:  # activity storage problems are reported by the bridge itself
        pass


def activity_resolve(owner, operation, key):
    bridge = activity_bridge(owner)
    if bridge is not None:
        bridge.invoke('resolve_notice', operation, key, module='movieinator')


# ----------------------------------------------------------------------------- views
class MovieModel(QAbstractTableModel):
    def __init__(self, owner, grid=False):
        super().__init__(owner); self.owner = owner; self.grid = grid; self.movies = []; self.icons = {}

    def replace(self, movies):
        self.beginResetModel(); self.movies = list(movies); self.icons.clear(); self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.movies)

    def columnCount(self, parent=QModelIndex()):
        return 1 if self.grid else len(COLUMNS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole and not self.grid:
            return COLUMNS[section]
        return super().headerData(section, orientation, role)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self.movies):
            return None
        movie = self.movies[index.row()]
        if role == Qt.ItemDataRole.UserRole:
            return movie.id
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.ToolTipRole):
            values = (movie.title, str(movie.year or ''), ', '.join(movie.directors), ', '.join(movie.genres),
                      ' / '.join(movie.formats) or 'No editions', movie.status,
                      f'{movie.rating}/10' if movie.rating is not None else 'No rating')
            if self.grid:
                return '\n'.join((movie.display_title, values[4], movie.status))
            return values[index.column()]
        if role == Qt.ItemDataRole.DecorationRole and self.grid:
            if movie.id not in self.icons:
                self.icons[movie.id] = poster(movie)
            return self.icons[movie.id]
        return None


class MovieGrid(QListView):
    currentRowChanged = pyqtSignal(int)

    def __init__(self, owner):
        super().__init__()
        self.setModel(MovieModel(owner, True))
        self.setViewMode(QListView.ViewMode.IconMode)
        self.setResizeMode(QListView.ResizeMode.Adjust)
        self.setMovement(QListView.Movement.Static)
        self.setWordWrap(True); self.setSpacing(12); self.setUniformItemSizes(True)
        self.setIconSize(QSize(110, 160)); self.setGridSize(QSize(230, 250))
        self.setAccessibleName('Movie posters')
        self.selectionModel().currentRowChanged.connect(lambda current, previous: self.currentRowChanged.emit(current.row()))

    def count(self):
        return self.model().rowCount()

    def setCurrentRow(self, row):
        self.setCurrentIndex(self.model().index(row, 0))


class MovieTable(QTableView):
    currentRowChanged = pyqtSignal(int)

    def __init__(self, owner):
        super().__init__()
        self.setModel(MovieModel(owner))
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.horizontalHeader().setStretchLastSection(True)
        self.setAccessibleName('Movie list')
        for column, width in enumerate((260, 60, 180, 180, 140, 110, 90)):
            self.setColumnWidth(column, width)
        self.selectionModel().currentRowChanged.connect(lambda current, previous: self.currentRowChanged.emit(current.row()))

    def rowCount(self):
        return self.model().rowCount()

    def setCurrentRow(self, row):
        self.setCurrentIndex(self.model().index(row, 0))


# ----------------------------------------------------------------------------- module tab
class Movieinator(QWidget):
    """The Movie-inator tab. `store` is None for the read-only sample catalog."""

    def __init__(self, state, save, store=None, activity=None):
        super().__init__()
        self.state, self.save, self.store, self.activity = state, save, store, activity
        self.movies = SAMPLE_MOVIES if store is None else ()
        self.visible = []
        self.rendering = False
        self.closing = False
        self.editor = None
        self.editions_dialog = None
        self.import_dialog = None
        self.signature = None
        self.load_error = ''
        self.setAcceptDrops(store is not None)
        layout = QVBoxLayout(self)

        self.note = QLabel('Movie catalog' if store else 'Sample movie catalog · Read-only preview; nothing is saved.')
        self.note.setWordWrap(True)
        layout.addWidget(self.note)

        actions = QHBoxLayout()
        self.add_button = QPushButton('Add movie…'); self.add_button.clicked.connect(self.add_movie)
        self.import_button = QPushButton('Import files / scan folder…'); self.import_button.clicked.connect(self.open_import)
        self.player_button = QPushButton(); self.player_button.clicked.connect(self.choose_player)
        self.reload_button = QPushButton('Reload catalog'); self.reload_button.clicked.connect(lambda: self.reload(explicit=True))
        for button in (self.add_button, self.import_button, self.player_button, self.reload_button):
            button.setEnabled(store is not None)
            actions.addWidget(button)
        actions.addStretch()
        layout.addLayout(actions)
        self.update_player_label()

        saved = state.get('movie_search', {})
        bar = QHBoxLayout()
        self.search = QLineEdit(); self.search.setClearButtonEnabled(True)
        self.search.setPlaceholderText('Find by title, director, cast or year')
        self.search.setAccessibleName('Find movies by title, director, cast or year')
        self.search.setText(saved.get('text', ''))
        bar.addWidget(self.search, 1)
        self.clear_search = QPushButton('Clear All'); self.clear_search.clicked.connect(self.clear_search_filters)
        bar.addWidget(self.clear_search)
        self.filter_toggle = QCheckBox('Filters'); self.filter_toggle.setChecked(saved.get('expanded', True))
        bar.addWidget(self.filter_toggle)
        self.sort = QComboBox(); self.sort.addItems(SORTS); self.sort.setAccessibleName('Sort movies')
        self.sort.setCurrentIndex(SORTS.index(saved['sort']) if saved.get('sort') in SORTS else 0)
        bar.addWidget(self.sort)
        self.view = QComboBox(); self.view.addItems(['Grid', 'List']); self.view.setAccessibleName('Movie catalog view')
        self.view.setCurrentText(state.get('movie_view', 'Grid'))
        bar.addWidget(self.view)
        layout.addLayout(bar)

        self.filter_values = {key: set(saved.get(key, [])) for key in ('genres', 'formats', 'statuses')}
        self.filter_panel = QWidget(); filters = QHBoxLayout(self.filter_panel)
        self.filter_buttons = {}
        for key, label in (('genres', 'Genres'), ('formats', 'Formats'), ('statuses', 'Watched status')):
            button = QPushButton(label); menu = QMenu(button); button.setMenu(menu)
            self.filter_buttons[key] = (button, menu, label); filters.addWidget(button)
        filters.addStretch()
        self.filter_panel.setVisible(self.filter_toggle.isChecked())
        layout.addWidget(self.filter_panel)

        self.count = QLabel(); layout.addWidget(self.count)
        self.pages = QStackedWidget()
        self.grid = MovieGrid(self); self.table = MovieTable(self)
        self.pages.addWidget(self.grid); self.pages.addWidget(self.table)
        layout.addWidget(self.pages, 1)

        self.detail = QLabel('Select a movie to see its editions and copies.')
        self.detail.setWordWrap(True); self.detail.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.detail)
        personal = QHBoxLayout()
        self.watched = QCheckBox('Watched'); self.watched.setToolTip('Your own watched status. Other profiles keep their own.')
        self.rating = QComboBox(); self.rating.addItems(['No rating'] + [f'{n} / 10' for n in range(1, 11)])
        self.rating.setAccessibleName('Your rating')
        personal.addWidget(self.watched); personal.addWidget(QLabel('Your rating:')); personal.addWidget(self.rating); personal.addStretch()
        layout.addLayout(personal)
        self.files = QHBoxLayout(); layout.addLayout(self.files)
        manage = QHBoxLayout()
        self.edit_button = QPushButton('Edit details…'); self.edit_button.clicked.connect(self.edit_movie)
        self.editions_button = QPushButton('Editions && copies…'); self.editions_button.clicked.connect(self.open_editions)
        self.remove_button = QPushButton('Remove from catalog…'); self.remove_button.clicked.connect(self.remove_movie)
        for button in (self.edit_button, self.editions_button, self.remove_button):
            manage.addWidget(button)
        manage.addStretch()
        layout.addLayout(manage)

        self.refresh_timer = QTimer(self); self.refresh_timer.setInterval(30000); self.refresh_timer.timeout.connect(self.auto_refresh)
        self.search.textChanged.connect(self.search_changed)
        self.filter_toggle.toggled.connect(self.search_changed)
        self.sort.currentIndexChanged.connect(self.search_changed)
        self.view.currentTextChanged.connect(self.change_view)
        self.grid.currentRowChanged.connect(self.select)
        self.table.currentRowChanged.connect(self.select)
        self.grid.doubleClicked.connect(lambda *_: self.edit_movie())
        self.table.doubleClicked.connect(lambda *_: self.edit_movie())
        self.watched.toggled.connect(self.personal_changed)
        self.rating.currentIndexChanged.connect(self.personal_changed)
        if store is not None:
            self.reload()
            self.refresh_timer.start()
        else:
            self.rebuild_filters(); self.render()

    # -- catalog loading --------------------------------------------------------
    def reload(self, explicit=False):
        if self.store is None or self.closing:
            return False
        if explicit and not self.editor_review():
            return False
        try:
            if not self.store.path.exists():
                self.store.initialize()
            self.movies = self.store.load()
            self.signature = self.store.signature()
            self.load_error = ''
            self.note.setText(f'Movie catalog · {len(self.movies)} movies · Files stay where they are; nothing is moved or deleted.')
            activity_resolve(self, 'Movie catalog', str(self.store.path))
        except MovieStoreError as exc:
            self.load_error = str(exc)
            self.note.setText('Movie catalog unavailable. Previous results may be out of date. ' + str(exc))
            activity_record(self, 'Movie catalog', str(self.store.path), outcome='failure', pending=True,
                            source=dict(kind='movie_catalog', path=str(self.store.path)), details=dict(error=str(exc)),
                            deduplicate=True)
            for button in (self.add_button, self.import_button):
                button.setEnabled(False)
            self.rebuild_filters(); self.render()
            return False
        for button in (self.add_button, self.import_button):
            button.setEnabled(True)
        self.rebuild_filters()
        self.render()
        if self.editions_dialog is not None:
            self.editions_dialog.refresh()
        return True

    def auto_refresh(self):
        if self.store is None or self.closing or self.busy():
            return
        if self.editor is not None and self.editor.dirty():
            if self.store.signature() != self.signature:
                self.note.setText('Movie catalog changed elsewhere. Refresh is pending until your edits are saved or discarded.')
            return
        if self.store.signature() != self.signature:
            self.reload()

    def busy(self):
        return bool(self.import_dialog and self.import_dialog.busy())

    # -- search/filter ------------------------------------------------------------
    def rebuild_filters(self):
        for key, (button, menu, label) in self.filter_buttons.items():
            choices = set(self.filter_values[key])
            for movie in self.movies:
                choices.update(movie.genres if key == 'genres' else movie.formats if key == 'formats' else [movie.status])
            if key == 'statuses':
                choices.update(STATUSES)
            menu.clear()
            for value in sorted(choices, key=str.casefold):
                action = menu.addAction(value); action.setCheckable(True)
                action.setChecked(value in self.filter_values[key])
                action.toggled.connect(lambda checked, k=key, v=value: self.filter_changed(k, v, checked))
            self.label_filter(key)

    def label_filter(self, key):
        button, _, label = self.filter_buttons[key]
        values = sorted(self.filter_values[key], key=str.casefold)
        button.setText(label + (': ' + ', '.join(values) if values else ': All'))

    def filter_changed(self, key, value, checked):
        (self.filter_values[key].add if checked else self.filter_values[key].discard)(value)
        self.search_changed()

    def search_changed(self, *_):
        self.filter_panel.setVisible(self.filter_toggle.isChecked())
        self.state['movie_search'] = dict(text=self.search.text(), **{k: sorted(v) for k, v in self.filter_values.items()},
                                          expanded=self.filter_toggle.isChecked(), sort=self.sort.currentText())
        self.save()
        for key in self.filter_buttons:
            self.label_filter(key)
        self.render()

    def clear_search_filters(self):
        self.search.blockSignals(True); self.search.clear(); self.search.blockSignals(False)
        for values in self.filter_values.values():
            values.clear()
        self.rebuild_filters(); self.search_changed()

    def change_view(self, value):
        self.state['movie_view'] = value
        self.pages.setCurrentIndex(0 if value == 'Grid' else 1)
        self.save()

    def render(self):
        self.rendering = True
        self.visible = find_movies(self.movies, self.search.text(), **self.filter_values)
        index = self.sort.currentIndex()
        if index == 1:
            self.visible.reverse()
        elif index in (2, 3):
            dated = sorted((m for m in self.visible if m.year), key=lambda m: (m.year, sort_key(m.title)), reverse=index == 2)
            self.visible = dated + [m for m in self.visible if not m.year]
        self.grid.model().replace(self.visible); self.table.model().replace(self.visible)
        self.pages.setCurrentIndex(0 if self.state.get('movie_view', 'Grid') == 'Grid' else 1)
        if self.visible:
            self.count.setText(f'{len(self.visible)} of {len(self.movies)} movies')
        elif self.movies:
            self.count.setText('No movies match this search. Use Clear All to show everything.')
        else:
            self.count.setText('The catalog is empty. Use Add movie… or Import files / scan folder… (or drop video files here).')
        row = next((i for i, m in enumerate(self.visible) if m.id == self.state.get('selected_movie')), -1)
        self.rendering = False
        self.select(row)

    def current(self):
        return next((m for m in self.movies if m.id == self.state.get('selected_movie')), None)

    def select(self, row):
        if self.rendering:
            return
        self.rendering = True
        movie = self.visible[row] if 0 <= row < len(self.visible) else None
        self.grid.setCurrentRow(row); self.table.setCurrentRow(row)
        while self.files.count():
            widget = self.files.takeAt(0).widget()
            if widget:
                widget.hide(); widget.deleteLater()
        editable = movie is not None and self.store is not None and not self.load_error
        for widget in (self.edit_button, self.editions_button, self.remove_button, self.watched, self.rating):
            widget.setEnabled(editable)
        if movie is None:
            self.detail.setText('Select a movie to see its editions and copies.')
            self.watched.setChecked(False); self.rating.setCurrentIndex(0)
        else:
            self.detail.setText(self.describe(movie))
            self.watched.setChecked(movie.watched); self.rating.setCurrentIndex(movie.rating or 0)
            for edition in movie.editions:
                for copy in edition.copies:
                    if copy.kind != 'file':
                        continue
                    exists = Path(copy.path).is_file()
                    button = QPushButton(('Play ' if exists else 'Locate ') + edition.label)
                    button.setToolTip(copy.path if exists else f'Missing or unavailable: {copy.path}\nChoose where the file is now.')
                    button.setEnabled(self.store is not None)
                    button.clicked.connect(lambda checked=False, c=copy, ok=exists: self.play(c) if ok else self.locate(c))
                    self.files.addWidget(button)
            self.files.addStretch()
            if self.state.get('selected_movie') != movie.id:
                self.state['selected_movie'] = movie.id
                self.save()
        self.rendering = False

    @staticmethod
    def describe(movie):
        lines = [movie.display_title]
        if movie.original_title and movie.original_title != movie.title:
            lines.append('Original title: ' + movie.original_title)
        facts = [p for p in ('Directed by ' + ', '.join(movie.directors) if movie.directors else '',
                             ', '.join(movie.genres), f'{movie.runtime} min' if movie.runtime else '') if p]
        if facts:
            lines.append(' · '.join(facts))
        if movie.rating:
            lines.append('Your rating: ' + '★' * movie.rating + '☆' * (10 - movie.rating) + f' {movie.rating}/10')
        if movie.cast:
            lines.append('Cast: ' + ', '.join(movie.cast[:8]) + (' …' if len(movie.cast) > 8 else ''))
        if movie.synopsis:
            text = movie.synopsis.strip()
            lines.append(text if len(text) <= 400 else text[:400].rsplit(' ', 1)[0] + ' …')
        if not movie.editions:
            lines.append('No editions or copies recorded.')
        for edition in movie.editions:
            copies = '; '.join(c.describe() for c in edition.copies) or 'no copies recorded'
            lines.append(f'• {edition.label} [{edition.format}] — {copies}')
        return '\n'.join(lines)

    # -- personal activity --------------------------------------------------------------
    def personal_changed(self, *_):
        movie = self.current()
        if self.rendering or movie is None or self.store is None:
            return
        watched, rating = self.watched.isChecked(), (self.rating.currentIndex() or None)
        if (watched, rating) == (movie.watched, movie.rating):
            return
        try:
            self.store.set_personal(movie.id, watched, rating)
        except MovieStoreError as exc:
            QMessageBox.warning(self, 'Watched status not saved', f'{exc}\nThe previous value was kept.')
            self.rendering = True
            self.watched.setChecked(movie.watched); self.rating.setCurrentIndex(movie.rating or 0)
            self.rendering = False
            return
        self.reload()

    # -- playback -------------------------------------------------------------------------
    def update_player_label(self):
        command = self.state.get('movie_player', '')
        self.player_button.setText('Player: ' + (command.split()[0] if command.strip() else 'System default') + '…')
        self.player_button.setToolTip('Movies open in an external player. Movie-inator does not track or close it.')

    def choose_player(self):
        from .movie_player import PlayerError, validate_command
        current = self.state.get('movie_player', '')
        text, ok = QInputDialog.getText(self, 'External player',
            'Command used to play movies, for example: mpv   or   vlc --fullscreen\n'
            'Leave empty to use the desktop default application. {file} marks the file position.', text=current)
        if not ok:
            return
        try:
            command = validate_command(text)
        except PlayerError as exc:
            QMessageBox.warning(self, 'Player not changed', str(exc)); return
        self.state['movie_player'] = command
        if not self.save():
            self.state['movie_player'] = current
            QMessageBox.warning(self, 'Player not changed', 'Settings could not be saved. The previous player remains in use.')
        self.update_player_label()

    def play(self, copy):
        from .movie_player import PlayerError, launch
        try:
            launch(self.state.get('movie_player', ''), copy.path)
        except PlayerError as exc:
            activity_record(self, 'Player launch', copy.path, outcome='failure', pending=True,
                            source=dict(kind='movie_play', path=copy.path, copy_id=copy.id),
                            details=dict(error=str(exc)), deduplicate=True)
            QMessageBox.warning(self, 'Cannot play movie', str(exc)); return
        activity_resolve(self, 'Player launch', copy.path)
        self.note.setText('Player started. It runs independently; Movie-inator does not track or close it. '
                          'Mark the movie as Watched yourself when you are done.')

    def locate(self, copy):
        chosen, _ = QFileDialog.getOpenFileName(self, 'Locate moved video file', str(Path(copy.path).parent))
        if not chosen:
            return
        try:
            self.store.relocate_file(copy.id, chosen)
        except MovieStoreError as exc:
            QMessageBox.warning(self, 'Location not updated', str(exc)); return
        self.reload()

    # -- editing -----------------------------------------------------------------------
    def editor_review(self):
        return self.editor is None or self.editor.review(closing=True)

    def add_movie(self):
        if self.store is None or self.busy() or not self.editor_review():
            return
        self.open_editor(None)

    def edit_movie(self):
        movie = self.current()
        if movie is None or self.store is None or self.busy():
            return
        if self.editor is not None and self.editor.movie is not None and self.editor.movie.id == movie.id:
            self.editor.show(); self.editor.raise_(); return
        if not self.editor_review():
            return
        self.open_editor(movie)

    def open_editor(self, movie):
        if self.editor is not None:
            self.editor.approve_close(); self.editor.close()
        self.editor = MovieEditor(self.store, movie, self)
        self.editor.saved.connect(self.editor_saved)
        self.editor.finished.connect(self.editor_finished)
        self.editor.show()
        return self.editor

    def editor_saved(self, movie_id):
        self.state['selected_movie'] = movie_id
        self.save()
        self.reload()
        activity_record(self, 'Movie details save', movie_id, outcome='success',
                        source=dict(kind='movie_save', movie_id=movie_id), deduplicate=True)

    def editor_finished(self, *_):
        if self.editor is not None:
            self.editor.deleteLater(); self.editor = None
        self.auto_refresh()

    def open_editions(self):
        movie = self.current()
        if movie is None or self.store is None:
            return
        if self.editions_dialog is not None:
            self.editions_dialog.close(); self.editions_dialog.deleteLater()
        self.editions_dialog = EditionsDialog(self, movie.id)
        self.editions_dialog.show()
        return self.editions_dialog

    def remove_movie(self):
        movie = self.current()
        if movie is None or self.store is None or self.busy():
            return
        if self.editor is not None and self.editor.movie is not None and self.editor.movie.id == movie.id:
            if not self.editor.review(closing=True):
                return
            self.editor.approve_close(); self.editor.close()
        answer = QMessageBox.question(self, 'Remove from catalog',
            f'Remove "{movie.display_title}" and its {len(movie.editions)} edition(s) from the catalog?\n\n'
            'Video files and physical copies are NOT deleted. Your watched status and rating for it are removed.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Cancel)
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.store.remove_movie(movie.id)
        except MovieStoreError as exc:
            QMessageBox.warning(self, 'Movie not removed', str(exc)); return
        activity_record(self, 'Movie removed from catalog', movie.id, outcome='success',
                        source=dict(kind='movie_catalog', path=str(self.store.path)), details=dict(title=movie.display_title))
        self.state['selected_movie'] = None; self.save()
        self.reload()

    # -- import -------------------------------------------------------------------------
    def open_import(self, paths=()):
        if self.store is None or self.load_error:
            return None
        if self.import_dialog is None:
            self.import_dialog = MovieImportDialog(self)
        if paths:
            self.import_dialog.add_paths(paths)
        self.import_dialog.show(); self.import_dialog.raise_()
        return self.import_dialog

    def dragEnterEvent(self, event):
        if self.store is not None and event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        if paths:
            self.open_import(paths)
            event.acceptProposedAction()

    # -- lifecycle ------------------------------------------------------------------------
    def review_close(self):
        """Hub/tab close review: running import, then unsaved detail edits."""
        if self.busy():
            if QMessageBox.question(self, 'Movie import in progress',
                    'Stop after the current movie? Completed imports remain in the catalog; nothing else is written. '
                    'Close again when it has stopped.',
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
                self.import_dialog.stop()
            return False
        if self.editor is not None and not self.editor.review(closing=True):
            return False
        return True

    def unattended_close_blocked(self):
        return self.busy() or bool(self.editor and self.editor.dirty())

    def shutdown(self):
        self.closing = True
        self.refresh_timer.stop()
        if self.import_dialog is not None:
            self.import_dialog.shutdown()
        for dialog in (self.editor, self.editions_dialog, self.import_dialog):
            if dialog is not None:
                if dialog is self.editor:
                    dialog.approve_close()
                dialog.close()


# ----------------------------------------------------------------------------- detail editor
class MovieEditor(QDialog):
    """Draft editor for movie details; nothing is written until Save."""
    saved = pyqtSignal(str)

    def __init__(self, store, movie, parent=None):
        super().__init__(parent)
        self.store, self.movie = store, movie
        self.closing_approved = False
        self.setWindowTitle('Add movie' if movie is None else f'Edit details — {movie.display_title}')
        self.resize(640, 700)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.title = QLineEdit(); self.original_title = QLineEdit(); self.year = QLineEdit(); self.runtime = QLineEdit()
        self.year.setPlaceholderText('e.g. 1979'); self.runtime.setPlaceholderText('minutes')
        self.directors = QPlainTextEdit(); self.cast = QPlainTextEdit()
        self.directors.setPlaceholderText('One name per line'); self.cast.setPlaceholderText('One name per line')
        self.directors.setMaximumHeight(70)
        self.genres = QLineEdit(); self.genres.setPlaceholderText('Comma separated, e.g. Horror, Science fiction')
        self.synopsis = QPlainTextEdit(); self.notes = QPlainTextEdit(); self.notes.setMaximumHeight(70)
        self.cover = QLineEdit(); self.cover.setReadOnly(True)
        cover_row = QHBoxLayout(); cover_row.addWidget(self.cover, 1)
        choose = QPushButton('Choose image…'); choose.clicked.connect(self.choose_cover); cover_row.addWidget(choose)
        clear = QPushButton('Remove'); clear.clicked.connect(lambda: self.cover.setText('')); cover_row.addWidget(clear)
        for label, widget in (('Title *', self.title), ('Original title', self.original_title), ('Year', self.year),
                              ('Runtime', self.runtime), ('Directors', self.directors), ('Cast', self.cast),
                              ('Genres', self.genres), ('Synopsis', self.synopsis), ('Cover image', cover_row),
                              ('Private notes', self.notes)):
            form.addRow(label, widget)
        layout.addLayout(form)
        self.first_edition = None
        if movie is None:
            box = QGroupBox('First edition (optional)'); edition_form = QFormLayout(box)
            self.edition_format = QComboBox(); self.edition_format.addItems(['None'] + list(EDITION_FORMATS))
            self.edition_label = QLineEdit(); self.edition_label.setPlaceholderText("e.g. Director's Cut, Steelbook")
            self.edition_location = QLineEdit(); self.edition_location.setPlaceholderText('Shelf or box for a physical copy')
            file_row = QHBoxLayout(); self.edition_file = QLineEdit(); self.edition_file.setReadOnly(True)
            pick = QPushButton('Choose video file…'); pick.clicked.connect(self.choose_file)
            file_row.addWidget(self.edition_file, 1); file_row.addWidget(pick)
            edition_form.addRow('Format', self.edition_format); edition_form.addRow('Label', self.edition_label)
            edition_form.addRow('Physical location', self.edition_location); edition_form.addRow('Digital file', file_row)
            layout.addWidget(box)
            self.first_edition = box
        self.status = QLabel(); self.status.setWordWrap(True); layout.addWidget(self.status)
        buttons = QHBoxLayout()
        self.save_button = QPushButton('Save'); self.save_button.setDefault(True); self.save_button.clicked.connect(lambda checked=False: self.save_changes())
        self.discard_button = QPushButton('Discard changes'); self.discard_button.clicked.connect(self.discard)
        close = QPushButton('Close'); close.clicked.connect(self.close)
        for button in (self.save_button, self.discard_button, close):
            buttons.addWidget(button)
        layout.addLayout(buttons)
        self.fill(movie)
        for widget in (self.title, self.original_title, self.year, self.runtime, self.genres, self.cover):
            widget.textChanged.connect(self.update_status)
        for widget in (self.directors, self.cast, self.synopsis, self.notes):
            widget.textChanged.connect(self.update_status)

    # draft values
    def fill(self, movie):
        self.baseline = self.values_of(movie)
        self.title.setText(self.baseline['title']); self.original_title.setText(self.baseline['original_title'])
        self.year.setText(str(self.baseline['year'] or '')); self.runtime.setText(str(self.baseline['runtime'] or ''))
        self.directors.setPlainText('\n'.join(self.baseline['directors'])); self.cast.setPlainText('\n'.join(self.baseline['cast']))
        self.genres.setText(', '.join(self.baseline['genres'])); self.synopsis.setPlainText(self.baseline['synopsis'])
        self.cover.setText(self.baseline['cover']); self.notes.setPlainText(self.baseline['notes'])
        self.update_status()

    @staticmethod
    def values_of(movie):
        if movie is None:
            return dict(title='', original_title='', year=None, runtime=None, directors=[], cast=[], genres=[],
                        synopsis='', cover='', notes='')
        return dict(title=movie.title, original_title=movie.original_title, year=movie.year, runtime=movie.runtime,
                    directors=list(movie.directors), cast=list(movie.cast), genres=list(movie.genres),
                    synopsis=movie.synopsis, cover=movie.cover, notes=movie.notes)

    def raw_values(self):
        def number(text):
            text = text.strip()
            if not text:
                return None
            return int(text) if text.isdigit() else text   # validation reports non-numbers
        return dict(title=self.title.text(), original_title=self.original_title.text(), year=number(self.year.text()),
                    runtime=number(self.runtime.text()), directors=split_names(self.directors.toPlainText()),
                    cast=split_names(self.cast.toPlainText()), genres=split_list(self.genres.text()),
                    synopsis=self.synopsis.toPlainText(), cover=self.cover.text(), notes=self.notes.toPlainText())

    def changes(self):
        values = self.raw_values()
        normal = dict(values, title=values['title'].strip(), original_title=values['original_title'].strip(),
                      synopsis=values['synopsis'].strip('\n '), notes=values['notes'].strip('\n '))
        return {k: v for k, v in normal.items() if v != self.baseline[k]}

    def dirty(self):
        if self.movie is None and self.first_edition is not None:
            if self.edition_format.currentIndex() or self.edition_label.text().strip() or self.edition_file.text():
                return True
        return bool(self.changes())

    def update_status(self, *_):
        self.status.setText('Modified — not saved yet.' if self.dirty() else 'No unsaved changes.')

    def choose_cover(self):
        chosen, _ = QFileDialog.getOpenFileName(self, 'Choose cover image', '', 'Images (*.png *.jpg *.jpeg *.webp *.bmp)')
        if chosen:
            if QIcon(chosen).isNull():
                QMessageBox.warning(self, 'Cover not used', 'This image could not be read.'); return
            self.cover.setText(str(Path(chosen).resolve()))

    def choose_file(self):
        chosen, _ = QFileDialog.getOpenFileName(self, 'Choose video file')
        if chosen:
            self.edition_file.setText(chosen)
            if self.edition_format.currentText() == 'None':
                self.edition_format.setCurrentText('Digital')

    def first_edition_value(self):
        if self.first_edition is None or self.edition_format.currentText() == 'None':
            if self.first_edition is not None and self.edition_file.text():
                raise MovieStoreError('Choose a format for the first edition, or remove the chosen file.')
            return []
        fmt = self.edition_format.currentText()
        label = self.edition_label.text().strip() or fmt
        copies = []
        if self.edition_file.text():
            from .movie_scan import probe
            copies.append(probe(self.edition_file.text()).copy())
        if self.edition_location.text().strip() or (fmt != 'Digital' and not copies):
            copies.append(dict(kind='physical', location=self.edition_location.text()))
        return [dict(label=label, format=fmt, copies=copies)]

    # save/discard/review
    def save_changes(self, changes=None):
        try:
            if self.movie is None:
                fields = validate_movie(self.raw_values())
                movie_id = self.store.add_movie(fields, self.first_edition_value())
            else:
                changes = self.changes() if changes is None else changes
                if not changes:
                    return True
                self.store.update_movie(self.movie.id, self.movie.revision, validate_movie(changes))
                movie_id = self.movie.id
        except ConflictError as exc:
            return self.resolve_conflict(exc.current)
        except MovieStoreError as exc:
            self.status.setText('Not saved: ' + str(exc) + ' Your edits are still here.')
            return False
        self.movie = self.store.get(movie_id)
        if self.first_edition is not None:
            self.first_edition.hide(); self.first_edition = None
        self.setWindowTitle(f'Edit details — {self.movie.display_title}')
        self.fill(self.movie)
        self.status.setText('Saved.')
        self.saved.emit(movie_id)
        return True

    def resolve_conflict(self, current):
        dialog = QMessageBox(self)
        dialog.setWindowTitle('Movie changed elsewhere')
        mine = self.changes()
        theirs = self.values_of(current)
        lines = [f'{k}: yours = {mine[k]!r}; catalog = {theirs[k]!r}' for k in mine if theirs.get(k) != mine[k]]
        dialog.setText('This movie was changed since you opened it. Nothing has been saved yet.\n\n' + '\n'.join(lines[:12]))
        keep = dialog.addButton('Save my values', QMessageBox.ButtonRole.AcceptRole)
        use = dialog.addButton('Use catalog values', QMessageBox.ButtonRole.DestructiveRole)
        dialog.addButton(QMessageBox.StandardButton.Cancel)
        dialog.exec()
        if dialog.clickedButton() is keep:
            # Only the fields you changed are written; other catalog changes are kept.
            self.movie = current
            return self.save_changes(mine)
        if dialog.clickedButton() is use:
            self.movie = current; self.fill(current); self.status.setText('Catalog values loaded; your edits were discarded.')
            return True
        self.status.setText('Save cancelled. Your edits are still here.')
        return False

    def discard(self):
        self.fill(self.movie)
        if self.first_edition is not None:
            self.edition_format.setCurrentIndex(0); self.edition_label.clear()
            self.edition_location.clear(); self.edition_file.clear()
        self.update_status()
        return True

    def approve_close(self):
        self.closing_approved = True

    def review(self, closing=False):
        if not self.dirty():
            return True
        answer = QMessageBox.question(self, 'Unsaved movie details', 'Save changes before continuing?',
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel)
        if answer == QMessageBox.StandardButton.Save:
            ok = self.save_changes()
        elif answer == QMessageBox.StandardButton.Discard:
            ok = self.discard()
        else:
            return False
        if ok and closing:
            self.closing_approved = True
        return ok

    def closeEvent(self, event):
        if self.closing_approved or self.review(closing=True):
            event.accept(); self.done(0)
        else:
            event.ignore()

    def reject(self):
        if self.closing_approved or self.review(closing=True):
            super().reject()


# ----------------------------------------------------------------------------- editions & copies
class EditionsDialog(QDialog):
    """Editions and owned copies. Each action saves immediately; removals confirm first."""

    def __init__(self, owner, movie_id):
        super().__init__(owner)
        self.owner, self.movie_id = owner, movie_id
        self.resize(720, 460)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('Each change here is saved immediately. Removing a file copy only removes it from the '
                                'catalog; the video file itself is never deleted.'))
        self.tree = QTreeWidget(); self.tree.setHeaderLabels(['Edition / copy', 'Format / type', 'Location or file'])
        self.tree.setColumnWidth(0, 240); self.tree.setColumnWidth(1, 120)
        layout.addWidget(self.tree, 1)
        self.status = QLabel(); self.status.setWordWrap(True); layout.addWidget(self.status)
        rows = (('Add edition…', self.add_edition), ('Edit edition…', self.edit_edition), ('Remove edition…', self.remove_edition)), \
               (('Add physical copy…', self.add_physical), ('Add video file…', self.add_file),
                ('Change location…', self.change_location), ('Remove copy…', self.remove_copy))
        for row in rows:
            bar = QHBoxLayout()
            for label, slot in row:
                button = QPushButton(label); button.clicked.connect(slot); bar.addWidget(button)
            layout.addLayout(bar)
        close = QPushButton('Close'); close.clicked.connect(self.close); layout.addWidget(close)
        self.refresh()

    def refresh(self):
        try:
            movie = self.owner.store.get(self.movie_id)
        except MovieStoreError as exc:
            self.status.setText(str(exc)); self.tree.clear(); return
        self.setWindowTitle(f'Editions & copies — {movie.display_title}')
        selected = self.selected()
        restore = None
        self.tree.clear()
        for edition in movie.editions:
            parent = QTreeWidgetItem([edition.label, edition.format, edition.notes])
            parent.setData(0, Qt.ItemDataRole.UserRole, ('edition', edition.id, edition))
            for copy in edition.copies:
                missing = copy.kind == 'file' and not Path(copy.path).is_file()
                child = QTreeWidgetItem([copy.describe(), 'File' if copy.kind == 'file' else 'Physical',
                                         (copy.path + ('  (missing)' if missing else '')) if copy.kind == 'file' else copy.location])
                child.setData(0, Qt.ItemDataRole.UserRole, ('copy', copy.id, copy, edition))
                parent.addChild(child)
                if selected and selected[1] == copy.id:
                    restore = child
            self.tree.addTopLevelItem(parent)
            parent.setExpanded(True)
            if selected and selected[1] == edition.id:
                restore = parent
        if restore is not None:
            self.tree.setCurrentItem(restore)
        if not movie.editions:
            self.status.setText('No editions yet. Add one, e.g. "Blu-ray Director\'s Cut" or "MKV rip".')

    def selected(self):
        item = self.tree.currentItem() if hasattr(self, 'tree') else None
        return item.data(0, Qt.ItemDataRole.UserRole) if item else None

    def selected_edition(self):
        value = self.selected()
        if value is None:
            self.status.setText('Select an edition first.'); return None
        return value[2] if value[0] == 'edition' else value[3]

    def selected_copy(self):
        value = self.selected()
        if value is None or value[0] != 'copy':
            self.status.setText('Select a copy first.'); return None
        return value[2]

    def run(self, action, success):
        try:
            action()
        except MovieStoreError as exc:
            self.status.setText('Not saved: ' + str(exc)); return False
        self.status.setText(success)
        self.owner.reload(); self.refresh()
        return True

    def ask_edition(self, title, label='', fmt='Digital', notes=''):
        dialog = QDialog(self); dialog.setWindowTitle(title)
        form = QFormLayout(dialog)
        label_edit = QLineEdit(label); format_box = QComboBox(); format_box.addItems(EDITION_FORMATS); format_box.setCurrentText(fmt)
        notes_edit = QLineEdit(notes)
        form.addRow('Label', label_edit); form.addRow('Format', format_box); form.addRow('Notes', notes_edit)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept); buttons.rejected.connect(dialog.reject); form.addRow(buttons)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        return label_edit.text(), format_box.currentText(), notes_edit.text()

    def add_edition(self):
        value = self.ask_edition('Add edition')
        if value:
            self.run(lambda: self.owner.store.add_edition(self.movie_id, *value), 'Edition added.')

    def edit_edition(self):
        edition = self.selected_edition()
        if edition is None:
            return
        value = self.ask_edition('Edit edition', edition.label, edition.format, edition.notes)
        if value:
            self.run(lambda: self.owner.store.update_edition(edition.id, *value), 'Edition saved.')

    def remove_edition(self):
        edition = self.selected_edition()
        if edition is None:
            return
        if QMessageBox.question(self, 'Remove edition', f'Remove "{edition.label}" and its {len(edition.copies)} copy record(s) '
                                'from the catalog? Video files are not deleted.') != QMessageBox.StandardButton.Yes:
            return
        self.run(lambda: self.owner.store.remove_edition(edition.id), 'Edition removed from the catalog.')

    def add_physical(self):
        edition = self.selected_edition()
        if edition is None:
            return
        location, ok = QInputDialog.getText(self, 'Add physical copy', 'Where is it kept? (shelf, box, room — optional)')
        if ok:
            self.run(lambda: self.owner.store.add_copy(edition.id, dict(kind='physical', location=location)), 'Physical copy added.')

    def add_file(self):
        edition = self.selected_edition()
        if edition is None:
            return
        chosen, _ = QFileDialog.getOpenFileName(self, 'Add video file to this edition')
        if chosen:
            from .movie_scan import probe
            self.run(lambda: self.owner.store.add_copy(edition.id, probe(chosen).copy()), 'Video file added. The file was not moved.')

    def change_location(self):
        copy = self.selected_copy()
        if copy is None:
            return
        if copy.kind == 'file':
            chosen, _ = QFileDialog.getOpenFileName(self, 'Choose where the file is now', str(Path(copy.path).parent))
            if chosen:
                self.run(lambda: self.owner.store.relocate_file(copy.id, chosen), 'File location updated.')
        else:
            location, ok = QInputDialog.getText(self, 'Change location', 'Where is it kept?', text=copy.location)
            if ok:
                self.run(lambda: self.owner.store.update_copy_location(copy.id, location), 'Location saved.')

    def remove_copy(self):
        copy = self.selected_copy()
        if copy is None:
            return
        if QMessageBox.question(self, 'Remove copy', 'Remove this copy from the catalog? '
                                + ('The video file itself is not deleted.' if copy.kind == 'file' else '')) != QMessageBox.StandardButton.Yes:
            return
        self.run(lambda: self.owner.store.remove_copy(copy.id), 'Copy removed from the catalog.')


# ----------------------------------------------------------------------------- import / scan
class ScanWorker(QObject):
    progress = pyqtSignal(str)
    finished = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, paths, movies, known):
        super().__init__(); self.paths, self.movies, self.known = paths, movies, known; self.cancelled = False

    def run(self):
        from .movie_scan import plan
        try:
            result = plan(self.paths, self.movies, self.known, cancelled=lambda: self.cancelled, progress=self.progress.emit)
        except Exception as exc:  # report, never crash the Hub
            self.failed.emit(str(exc)); return
        self.finished.emit(result)


ACTION_CREATE, ACTION_SKIP = 'Create new movie', 'Skip'


class MovieImportDialog(QDialog):
    """Choose files/folders (or drop them), build a preview, then Confirm."""

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.paths = []
        self.result = None
        self.thread = None
        self.worker = None
        self.applying = False
        self.stop_requested = False
        self.setWindowTitle('Import movies')
        self.setAcceptDrops(True)
        self.resize(900, 600)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('Choose video files or folders, or drop them here. Files are catalogued where they are: '
                                'nothing is copied, moved, renamed or deleted. Files with the same title and year become '
                                'one movie with several editions. Review the preview, then confirm.'))
        self.sources = QLabel('No files or folders chosen.'); self.sources.setWordWrap(True); layout.addWidget(self.sources)
        bar = QHBoxLayout()
        for label, slot in (('Add files…', self.choose_files), ('Add folder…', self.choose_folder),
                            ('Clear', self.clear), ('Build preview', self.build_preview)):
            button = QPushButton(label); button.clicked.connect(slot); bar.addWidget(button)
        self.stop_button = QPushButton('Stop'); self.stop_button.clicked.connect(self.stop); self.stop_button.setEnabled(False)
        bar.addWidget(self.stop_button)
        layout.addLayout(bar)
        self.tree = QTreeWidget(); self.tree.setHeaderLabels(['Import', 'Title', 'Year', 'Action', 'Files / notes'])
        self.tree.setColumnWidth(0, 70); self.tree.setColumnWidth(1, 260); self.tree.setColumnWidth(2, 60); self.tree.setColumnWidth(3, 230)
        self.tree.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.EditKeyPressed)
        layout.addWidget(self.tree, 1)
        self.status = QLabel(); self.status.setWordWrap(True); layout.addWidget(self.status)
        self.confirm = QPushButton('Confirm and import'); self.confirm.setEnabled(False); self.confirm.clicked.connect(self.apply)
        layout.addWidget(self.confirm)
        self.ffprobe_note()

    def ffprobe_note(self):
        from .movie_scan import ffprobe_available
        if not ffprobe_available():
            self.status.setText('ffprobe (from FFmpeg) is not installed: technical details such as resolution, audio '
                                'tracks and subtitles will be left empty. Importing still works.')

    def busy(self):
        return bool(self.applying or (self.thread is not None and self.thread.isRunning()))

    # sources
    def add_paths(self, paths):
        if self.busy():
            return
        for path in paths:
            if path and path not in self.paths:
                self.paths.append(path)
        self.sources.setText('\n'.join(self.paths[:8]) + (f'\n… and {len(self.paths) - 8} more' if len(self.paths) > 8 else '')
                             if self.paths else 'No files or folders chosen.')
        self.invalidate()

    def choose_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, 'Choose video files')
        self.add_paths(files)

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Choose a folder to scan (including subfolders)')
        if folder:
            self.add_paths([folder])

    def clear(self):
        if not self.busy():
            self.paths = []; self.add_paths([])

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and not self.busy():
            event.acceptProposedAction()

    def dropEvent(self, event):
        self.add_paths([u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()])
        event.acceptProposedAction()

    def invalidate(self):
        self.result = None; self.tree.clear(); self.confirm.setEnabled(False)

    # preview
    def build_preview(self):
        if self.busy() or not self.paths:
            if not self.paths:
                self.status.setText('Choose files or a folder first.')
            return
        store = self.owner.store
        try:
            movies, known = store.load(), store.known_paths()
        except MovieStoreError as exc:
            self.status.setText('Cannot read the catalog: ' + str(exc)); return
        self.invalidate()
        self.stop_requested = False
        self.worker = ScanWorker(list(self.paths), movies, known)
        self.thread = QThread(self)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.status.setText)
        self.worker.finished.connect(self.preview_ready)
        self.worker.failed.connect(self.preview_failed)
        # Plain callables run in the worker thread; QThread.quit is thread-safe.
        thread = self.thread
        self.worker.finished.connect(lambda *_: thread.quit())
        self.worker.failed.connect(lambda *_: thread.quit())
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.scan_stopped)
        self.stop_button.setEnabled(True)
        self.status.setText('Scanning…')
        self.thread.start()

    def scan_stopped(self):
        self.stop_button.setEnabled(False)
        self.worker = None
        if self.thread is not None:
            self.thread.deleteLater(); self.thread = None

    def preview_failed(self, message):
        self.status.setText('Preview failed; nothing was imported. ' + message)

    def preview_ready(self, result):
        if self.stop_requested:
            self.status.setText('Scan stopped. Nothing was imported. Build the preview again when ready.'); return
        self.result = result
        movies = {m.id: m for m in self.owner.movies}
        self.tree.clear()
        for group in result.groups:
            item = QTreeWidgetItem(['', group.title, str(group.year or ''), '', f'{len(group.files)} file(s)'])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(0, Qt.CheckState.Checked)
            item.setData(0, Qt.ItemDataRole.UserRole, group)
            self.tree.addTopLevelItem(item)
            action = QComboBox()
            action.addItem(ACTION_CREATE, None)
            if group.movie_id and group.movie_id in movies:
                action.addItem(f'Add to existing: {group.match_title}', group.movie_id)
                action.setCurrentIndex(1)
            action.addItem('Add to another movie…', 'choose')
            action.addItem(ACTION_SKIP, 'skip')
            action.currentIndexChanged.connect(lambda index, box=action: self.action_changed(box))
            self.tree.setItemWidget(item, 3, action)
            for edition in group.editions():
                child = QTreeWidgetItem(['', edition['label'], '', 'New edition',
                                         '; '.join(Path(c['path']).name for c in edition['copies'])])
                item.addChild(child)
            for warning in group.warnings:
                item.addChild(QTreeWidgetItem(['', '⚠ ' + warning]))
            item.setExpanded(bool(group.warnings) or len(group.files) > 1)
        summary = [f'{len(result.groups)} movie(s) found']
        if result.known:
            summary.append(f'{len(result.known)} file(s) already in the catalog were left out')
        if result.skipped:
            summary.append(f'{len(result.skipped)} item(s) skipped: ' + '; '.join(f'{Path(p).name}: {r}' for p, r in result.skipped[:3]))
        self.status.setText('. '.join(summary) + '. Double-click a title or year to correct it. Nothing is written until you confirm.')
        self.confirm.setEnabled(bool(result.groups))

    def action_changed(self, box):
        if box.currentData() != 'choose':
            return
        movies = sorted(self.owner.movies, key=lambda m: sort_key(m.title))
        if not movies:
            QMessageBox.information(self, 'No movies yet', 'The catalog has no movies to add to.')
            box.setCurrentIndex(0); return
        names = [m.display_title for m in movies]
        name, ok = QInputDialog.getItem(self, 'Add to another movie', 'Add these files as new editions of:', names, 0, False)
        if not ok:
            box.setCurrentIndex(0); return
        movie = movies[names.index(name)]
        box.blockSignals(True)
        box.insertItem(box.count() - 2, f'Add to existing: {movie.display_title}', movie.id)
        box.setCurrentIndex(box.count() - 3)
        box.blockSignals(False)

    # apply
    def decisions(self):
        items = []
        for index in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(index)
            group = item.data(0, Qt.ItemDataRole.UserRole)
            box = self.tree.itemWidget(item, 3)
            target = box.currentData() if box else None
            if item.checkState(0) != Qt.CheckState.Checked or target in ('skip', 'choose'):
                continue
            year_text = item.text(2).strip()
            year = int(year_text) if year_text.isdigit() else (year_text or None)
            items.append((item, group, item.text(1).strip(), year, target))
        return items

    def apply(self):
        if self.busy() or self.result is None:
            return
        decisions = self.decisions()
        if not decisions:
            self.status.setText('Nothing selected to import.'); return
        store = self.owner.store
        self.applying = True; self.stop_requested = False
        self.confirm.setEnabled(False); self.stop_button.setEnabled(True)
        done, failed, details = 0, 0, []
        try:
            from .movie_scan import revalidate
            known = store.known_paths()
            for item, group, title, year, target in decisions:
                if self.stop_requested:
                    break
                problems = revalidate(group, known)
                try:
                    if problems:
                        raise MovieStoreError(' '.join(problems) + ' Build the preview again to review the current files.')
                    if target:
                        store.apply_group('attach', group.editions(), movie_id=target)
                    else:
                        store.apply_group('create', group.editions(), title=title, year=year, runtime=group.runtime())
                    known = store.known_paths()
                except MovieStoreError as exc:
                    failed += 1
                    item.setText(4, 'Not imported: ' + str(exc))
                    details.append(dict(title=title, state='failed', error=str(exc)))
                else:
                    done += 1
                    item.setText(4, 'Imported')
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsUserCheckable & ~Qt.ItemFlag.ItemIsEditable)
                    item.setCheckState(0, Qt.CheckState.Unchecked)
                    details.append(dict(title=title, state='complete'))
                # Keep the window responsive between movies.
                from PyQt6.QtWidgets import QApplication
                QApplication.processEvents()
        finally:
            self.applying = False; self.stop_button.setEnabled(False)
        remaining = len(decisions) - done - failed
        outcome = 'success' if not failed and not remaining else 'partial' if done else 'failure' if failed else 'interrupted'
        activity_record(self.owner, 'Movie imports', str(store.path) + '\0' + str(uuid4()), outcome=outcome,
                        pending=False, source=dict(kind='movie_import', path=str(store.path)),
                        details=dict(completed=done, failed=failed, pending=remaining, items=details))
        message = f'{done} movie(s) imported'
        if failed:
            message += f', {failed} not imported (see the list)'
        if remaining:
            message += f', {remaining} not attempted because you stopped'
        self.status.setText(message + '. Imported movies are in the catalog now; nothing else was written.')
        self.result = None if not failed and not remaining else self.result
        self.confirm.setEnabled(False)
        self.owner.reload()

    def stop(self):
        self.stop_requested = True
        if self.worker is not None:
            self.worker.cancelled = True
        self.status.setText('Stopping after the current item…')

    def shutdown(self):
        self.stop()
        if self.thread is not None and self.thread.isRunning():
            self.thread.quit(); self.thread.wait(5000)

    def closeEvent(self, event):
        if self.busy():
            self.status.setText('Stop the scan or wait for the import to finish before closing.')
            event.ignore()
        else:
            event.accept()
