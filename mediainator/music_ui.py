"""Music-inator module tab, album editor, editions/tracks/copies and import dialogs.

Mirrors Book-inator and Movie-inator conventions: Grid/List over one filtered list,
remembered search, explicit Save / Discard / Cancel for album details, a preview that
must be confirmed before any import writes, and nothing that moves, renames, retags
or deletes audio files. Browsing by Artists, Genres or Years narrows the same album
list; the data model stays Album → Edition → Copy.
"""
from pathlib import Path
from uuid import uuid4

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, QObject, QSize, Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QGroupBox,
    QHBoxLayout, QInputDialog, QLabel, QLineEdit, QListView, QListWidget, QListWidgetItem, QMenu, QMessageBox,
    QPlainTextEdit, QPushButton, QSplitter, QStackedWidget, QTableView, QTableWidget, QTableWidgetItem,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from .music_catalog import (BROWSE_MODES, EDITION_FORMATS, PERSONAL_FILTERS, SAMPLE_ALBUMS,
                            album_sort_key, browse_values, find_albums, format_duration, parse_duration, sort_key)
from .music_store import ConflictError, MusicStoreError, validate_album

SORTS = ('Artist A–Z', 'Album A–Z', 'Album Z–A', 'Year (newest first)', 'Year (oldest first)', 'Rating (highest first)')
COLUMNS = ('Artist', 'Album', 'Year', 'Genres', 'Formats', 'Tracks', 'Rating', 'Favourite')
TRACK_COLUMNS = ('Disc', 'No.', 'Title', 'Track artist', 'Length')
MODULE = 'musicinator'


def cover_icon(album):
    if album.cover:
        icon = QIcon(album.cover)
        if not icon.isNull():
            return icon
    image = QPixmap(150, 150)
    image.fill(QColor('#24485a'))
    painter = QPainter(image)
    painter.setPen(QColor('#ffffff'))
    font = painter.font(); font.setPointSize(26); painter.setFont(font)
    painter.drawText(image.rect(), Qt.AlignmentFlag.AlignCenter, (album.title or '?')[0])
    painter.end()
    return QIcon(image)


def split_names(text):
    return [line.strip() for line in text.replace(';', '\n').splitlines() if line.strip()]


def split_list(text):
    return [part.strip() for part in text.split(',') if part.strip()]


def stars(rating):
    return '★' * rating + '☆' * (10 - rating) + f' {rating}/10' if rating else 'No rating'


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
        bridge.record(operation, key, module=MODULE, **kwargs)
    except Exception:  # activity storage problems are reported by the bridge itself
        pass


def activity_resolve(owner, operation, key):
    bridge = activity_bridge(owner)
    if bridge is not None:
        bridge.invoke('resolve_notice', operation, key, module=MODULE)


# ----------------------------------------------------------------------------- views
class AlbumModel(QAbstractTableModel):
    def __init__(self, owner, grid=False):
        super().__init__(owner); self.owner = owner; self.grid = grid; self.albums = []; self.icons = {}

    def replace(self, albums):
        self.beginResetModel(); self.albums = list(albums); self.icons.clear(); self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.albums)

    def columnCount(self, parent=QModelIndex()):
        return 1 if self.grid else len(COLUMNS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole and not self.grid:
            return COLUMNS[section]
        return super().headerData(section, orientation, role)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self.albums):
            return None
        album = self.albums[index.row()]
        if role == Qt.ItemDataRole.UserRole:
            return album.id
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.ToolTipRole):
            values = (album.display_artist, album.title, str(album.year or ''), ', '.join(album.genres),
                      ' / '.join(album.formats) or 'No editions', str(album.track_count or ''),
                      f'{album.rating}/10' if album.rating is not None else 'No rating',
                      '★' if album.favourite else '')
            if self.grid:
                title = album.title + (f' ({album.year})' if album.year else '')
                return '\n'.join(p for p in (('★ ' if album.favourite else '') + title, album.display_artist, values[4]) if p)
            return values[index.column()]
        if role == Qt.ItemDataRole.DecorationRole and self.grid:
            if album.id not in self.icons:
                self.icons[album.id] = cover_icon(album)
            return self.icons[album.id]
        return None


class AlbumGrid(QListView):
    currentRowChanged = pyqtSignal(int)

    def __init__(self, owner):
        super().__init__()
        self.setModel(AlbumModel(owner, True))
        self.setViewMode(QListView.ViewMode.IconMode)
        self.setResizeMode(QListView.ResizeMode.Adjust)
        self.setMovement(QListView.Movement.Static)
        self.setWordWrap(True); self.setSpacing(12); self.setUniformItemSizes(True)
        self.setIconSize(QSize(150, 150)); self.setGridSize(QSize(210, 240))
        self.setAccessibleName('Album covers')
        self.selectionModel().currentRowChanged.connect(lambda current, previous: self.currentRowChanged.emit(current.row()))

    def count(self):
        return self.model().rowCount()

    def setCurrentRow(self, row):
        self.setCurrentIndex(self.model().index(row, 0))


class AlbumTable(QTableView):
    currentRowChanged = pyqtSignal(int)

    def __init__(self, owner):
        super().__init__()
        self.setModel(AlbumModel(owner))
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.horizontalHeader().setStretchLastSection(True)
        self.setAccessibleName('Album list')
        for column, width in enumerate((200, 240, 60, 160, 120, 60, 80, 70)):
            self.setColumnWidth(column, width)
        self.selectionModel().currentRowChanged.connect(lambda current, previous: self.currentRowChanged.emit(current.row()))

    def rowCount(self):
        return self.model().rowCount()

    def setCurrentRow(self, row):
        self.setCurrentIndex(self.model().index(row, 0))


# ----------------------------------------------------------------------------- module tab
class Musicinator(QWidget):
    """The Music-inator tab. `store` is None for the read-only sample catalog."""

    def __init__(self, state, save, store=None, activity=None, playlist_folder=None):
        super().__init__()
        self.state, self.save, self.store, self.activity = state, save, store, activity
        self.playlist_folder = Path(playlist_folder) if playlist_folder else (store.path.parent / 'playlists' if store else None)
        self.albums = SAMPLE_ALBUMS if store is None else ()
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

        self.note = QLabel('Music catalog' if store else 'Sample music catalog · Read-only preview; nothing is saved.')
        self.note.setWordWrap(True)
        layout.addWidget(self.note)

        actions = QHBoxLayout()
        self.add_button = QPushButton('Add album…'); self.add_button.clicked.connect(self.add_album)
        self.import_button = QPushButton('Import files / scan folder…'); self.import_button.clicked.connect(self.open_import)
        self.player_button = QPushButton(); self.player_button.clicked.connect(self.choose_player)
        self.reload_button = QPushButton('Reload catalog'); self.reload_button.clicked.connect(lambda: self.reload(explicit=True))
        for button in (self.add_button, self.import_button, self.player_button, self.reload_button):
            button.setEnabled(store is not None)
            actions.addWidget(button)
        actions.addStretch()
        layout.addLayout(actions)
        self.update_player_label()

        saved = state.get('music_search', {})
        browse = state.get('music_browse', {})
        bar = QHBoxLayout()
        self.search = QLineEdit(); self.search.setClearButtonEnabled(True)
        self.search.setPlaceholderText('Find by album, artist, track or year')
        self.search.setAccessibleName('Find albums by album title, artist, track title or year')
        self.search.setText(saved.get('text', ''))
        bar.addWidget(self.search, 1)
        self.clear_search = QPushButton('Clear All'); self.clear_search.clicked.connect(self.clear_search_filters)
        bar.addWidget(self.clear_search)
        self.filter_toggle = QCheckBox('Filters'); self.filter_toggle.setChecked(saved.get('expanded', True))
        bar.addWidget(self.filter_toggle)
        bar.addWidget(QLabel('Browse:'))
        self.browse = QComboBox(); self.browse.addItems(BROWSE_MODES); self.browse.setAccessibleName('Browse albums by')
        self.browse.setCurrentText(browse.get('mode', 'Albums') if browse.get('mode') in BROWSE_MODES else 'Albums')
        bar.addWidget(self.browse)
        self.sort = QComboBox(); self.sort.addItems(SORTS); self.sort.setAccessibleName('Sort albums')
        self.sort.setCurrentIndex(SORTS.index(saved['sort']) if saved.get('sort') in SORTS else 0)
        bar.addWidget(self.sort)
        self.view = QComboBox(); self.view.addItems(['Grid', 'List']); self.view.setAccessibleName('Music catalog view')
        self.view.setCurrentText(state.get('music_view', 'Grid'))
        bar.addWidget(self.view)
        layout.addLayout(bar)

        self.filter_values = {key: set(saved.get(key, [])) for key in ('genres', 'formats', 'personal')}
        self.filter_panel = QWidget(); filters = QHBoxLayout(self.filter_panel)
        self.filter_buttons = {}
        for key, label in (('genres', 'Genres'), ('formats', 'Formats'), ('personal', 'Favourites & rating')):
            button = QPushButton(label); menu = QMenu(button); button.setMenu(menu)
            self.filter_buttons[key] = (button, menu, label); filters.addWidget(button)
        filters.addStretch()
        self.filter_panel.setVisible(self.filter_toggle.isChecked())
        layout.addWidget(self.filter_panel)

        self.count = QLabel(); layout.addWidget(self.count)
        self.browse_value = browse.get('value') or None
        self.browser = QListWidget(); self.browser.setAccessibleName('Browse values')
        self.pages = QStackedWidget()
        self.grid = AlbumGrid(self); self.table = AlbumTable(self)
        self.pages.addWidget(self.grid); self.pages.addWidget(self.table)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(self.browser); self.splitter.addWidget(self.pages)
        self.splitter.setStretchFactor(1, 1); self.splitter.setSizes([220, 780])
        layout.addWidget(self.splitter, 1)

        self.detail = QLabel('Select an album to see its editions, tracks and copies.')
        self.detail.setWordWrap(True); self.detail.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.detail)
        personal = QHBoxLayout()
        self.favourite = QCheckBox('★ Favourite'); self.favourite.setToolTip('Your own favourite mark. Other profiles keep their own.')
        self.rating = QComboBox(); self.rating.addItems(['No rating'] + [f'{n} / 10' for n in range(1, 11)])
        self.rating.setAccessibleName('Your rating')
        personal.addWidget(self.favourite); personal.addWidget(QLabel('Your rating:')); personal.addWidget(self.rating); personal.addStretch()
        layout.addLayout(personal)
        self.files = QHBoxLayout(); layout.addLayout(self.files)
        manage = QHBoxLayout()
        self.edit_button = QPushButton('Edit details…'); self.edit_button.clicked.connect(self.edit_album)
        self.editions_button = QPushButton('Editions, tracks && copies…'); self.editions_button.clicked.connect(self.open_editions)
        self.remove_button = QPushButton('Remove from catalog…'); self.remove_button.clicked.connect(self.remove_album)
        for button in (self.edit_button, self.editions_button, self.remove_button):
            manage.addWidget(button)
        manage.addStretch()
        layout.addLayout(manage)

        self.refresh_timer = QTimer(self); self.refresh_timer.setInterval(30000); self.refresh_timer.timeout.connect(self.auto_refresh)
        self.search.textChanged.connect(self.search_changed)
        self.filter_toggle.toggled.connect(self.search_changed)
        self.sort.currentIndexChanged.connect(self.search_changed)
        self.view.currentTextChanged.connect(self.change_view)
        self.browse.currentTextChanged.connect(self.browse_mode_changed)
        self.browser.currentItemChanged.connect(self.browse_value_changed)
        self.grid.currentRowChanged.connect(self.select)
        self.table.currentRowChanged.connect(self.select)
        self.grid.doubleClicked.connect(lambda *_: self.edit_album())
        self.table.doubleClicked.connect(lambda *_: self.edit_album())
        self.favourite.toggled.connect(self.personal_changed)
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
            self.albums = self.store.load()
            self.signature = self.store.signature()
            self.load_error = ''
            self.note.setText(f'Music catalog · {len(self.albums)} albums · Files stay where they are; nothing is moved, retagged or deleted.')
            activity_resolve(self, 'Music catalog', str(self.store.path))
        except MusicStoreError as exc:
            self.load_error = str(exc)
            self.note.setText('Music catalog unavailable. Previous results may be out of date. ' + str(exc))
            activity_record(self, 'Music catalog', str(self.store.path), outcome='failure', pending=True,
                            source=dict(kind='music_catalog', path=str(self.store.path)), details=dict(error=str(exc)),
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
                self.note.setText('Music catalog changed elsewhere. Refresh is pending until your edits are saved or discarded.')
            return
        if self.store.signature() != self.signature:
            self.reload()

    def busy(self):
        return bool(self.import_dialog and self.import_dialog.busy())

    # -- search/filter/browse -----------------------------------------------------
    def rebuild_filters(self):
        for key, (button, menu, label) in self.filter_buttons.items():
            choices = set(self.filter_values[key])
            for album in self.albums:
                choices.update(album.genres if key == 'genres' else album.formats if key == 'formats' else ())
            if key == 'personal':
                choices.update(PERSONAL_FILTERS)
            menu.clear()
            ordered = PERSONAL_FILTERS if key == 'personal' else sorted(choices, key=str.casefold)
            for value in ordered:
                action = menu.addAction(value); action.setCheckable(True)
                action.setChecked(value in self.filter_values[key])
                action.toggled.connect(lambda checked, k=key, v=value: self.filter_changed(k, v, checked))
            self.label_filter(key)
        self.rebuild_browser()

    def rebuild_browser(self):
        mode = self.browse.currentText()
        self.browser.setVisible(mode != 'Albums')
        self.browser.blockSignals(True)
        self.browser.clear()
        if mode != 'Albums':
            first = QListWidgetItem(f'All {mode.lower()}'); first.setData(Qt.ItemDataRole.UserRole, None)
            self.browser.addItem(first)
            current = first
            for value, count in browse_values(self.albums, mode):
                item = QListWidgetItem(f'{value} ({count})'); item.setData(Qt.ItemDataRole.UserRole, value)
                self.browser.addItem(item)
                if value == self.browse_value:
                    current = item
            if current is first:
                self.browse_value = None
            self.browser.setCurrentItem(current)
        else:
            self.browse_value = None
        self.browser.blockSignals(False)

    def browse_mode_changed(self, mode):
        self.browse_value = None
        self.rebuild_browser()
        self.search_changed()

    def browse_value_changed(self, current, previous=None):
        self.browse_value = current.data(Qt.ItemDataRole.UserRole) if current is not None else None
        self.search_changed()

    def label_filter(self, key):
        button, _, label = self.filter_buttons[key]
        values = sorted(self.filter_values[key], key=str.casefold)
        button.setText(label + (': ' + ', '.join(values) if values else ': All'))

    def filter_changed(self, key, value, checked):
        (self.filter_values[key].add if checked else self.filter_values[key].discard)(value)
        self.search_changed()

    def search_changed(self, *_):
        self.filter_panel.setVisible(self.filter_toggle.isChecked())
        self.state['music_search'] = dict(text=self.search.text(), **{k: sorted(v) for k, v in self.filter_values.items()},
                                          expanded=self.filter_toggle.isChecked(), sort=self.sort.currentText())
        self.state['music_browse'] = dict(mode=self.browse.currentText(), value=self.browse_value)
        self.save()
        for key in self.filter_buttons:
            self.label_filter(key)
        self.render()

    def clear_search_filters(self):
        self.search.blockSignals(True); self.search.clear(); self.search.blockSignals(False)
        for values in self.filter_values.values():
            values.clear()
        self.browse_value = None
        self.rebuild_filters(); self.search_changed()

    def change_view(self, value):
        self.state['music_view'] = value
        self.pages.setCurrentIndex(0 if value == 'Grid' else 1)
        self.save()

    def render(self):
        self.rendering = True
        mode = self.browse.currentText()
        self.visible = find_albums(self.albums, self.search.text(), browse=(mode, self.browse_value), **self.filter_values)
        index = self.sort.currentIndex()
        if index in (1, 2):
            self.visible.sort(key=lambda a: (sort_key(a.title), album_sort_key(a)), reverse=index == 2)
        elif index in (3, 4):
            dated = sorted((a for a in self.visible if a.year), key=lambda a: (a.year, album_sort_key(a)), reverse=index == 3)
            self.visible = dated + [a for a in self.visible if not a.year]
        elif index == 5:
            rated = sorted((a for a in self.visible if a.rating), key=lambda a: (-a.rating, not a.favourite, album_sort_key(a)))
            self.visible = rated + [a for a in self.visible if not a.rating]
        self.grid.model().replace(self.visible); self.table.model().replace(self.visible)
        self.pages.setCurrentIndex(0 if self.state.get('music_view', 'Grid') == 'Grid' else 1)
        if self.visible:
            scope = f' · {mode}: {self.browse_value}' if mode != 'Albums' and self.browse_value else ''
            self.count.setText(f'{len(self.visible)} of {len(self.albums)} albums{scope}')
        elif self.albums:
            self.count.setText('No albums match this search. Use Clear All to show everything.')
        else:
            self.count.setText('The catalog is empty. Use Add album… or Import files / scan folder… (or drop music folders here).')
        row = next((i for i, a in enumerate(self.visible) if a.id == self.state.get('selected_album')), -1)
        self.rendering = False
        self.select(row)

    def current(self):
        return next((a for a in self.albums if a.id == self.state.get('selected_album')), None)

    def select(self, row):
        if self.rendering:
            return
        self.rendering = True
        album = self.visible[row] if 0 <= row < len(self.visible) else None
        self.grid.setCurrentRow(row); self.table.setCurrentRow(row)
        while self.files.count():
            widget = self.files.takeAt(0).widget()
            if widget:
                widget.hide(); widget.deleteLater()
        editable = album is not None and self.store is not None and not self.load_error
        for widget in (self.edit_button, self.editions_button, self.remove_button, self.favourite, self.rating):
            widget.setEnabled(editable)
        if album is None:
            self.detail.setText('Select an album to see its editions, tracks and copies.')
            self.favourite.setChecked(False); self.rating.setCurrentIndex(0)
        else:
            self.detail.setText(self.describe(album))
            self.favourite.setChecked(album.favourite); self.rating.setCurrentIndex(album.rating or 0)
            for edition in album.editions:
                for copy in edition.copies:
                    if copy.kind != 'digital':
                        continue
                    missing = sum(1 for f in copy.files if not Path(f.path).is_file())
                    name = edition.label + (f' · {copy.quality}' if copy.quality else '')
                    button = QPushButton(('Play ' if not missing else 'Locate ') + name + ('' if not missing else '…'))
                    button.setToolTip(copy.folder if not missing else
                                      f'{missing} of {len(copy.files)} file(s) missing or unavailable in {copy.folder}\n'
                                      'Choose the folder where the files are now.')
                    button.setEnabled(self.store is not None)
                    button.clicked.connect(lambda checked=False, c=copy, ok=not missing: self.play(c) if ok else self.locate(c))
                    self.files.addWidget(button)
            self.files.addStretch()
            if self.state.get('selected_album') != album.id:
                self.state['selected_album'] = album.id
                self.save()
        self.rendering = False

    @staticmethod
    def describe(album):
        lines = [album.display_title]
        if album.additional_artists:
            lines.append('With: ' + ', '.join(album.additional_artists))
        facts = [p for p in (', '.join(album.genres), f'{album.track_count} tracks' if album.track_count else '') if p]
        if facts:
            lines.append(' · '.join(facts))
        personal = [p for p in ('★ Favourite' if album.favourite else '', 'Your rating: ' + stars(album.rating) if album.rating else '') if p]
        if personal:
            lines.append(' · '.join(personal))
        if not album.editions:
            lines.append('No editions or copies recorded.')
        for edition in album.editions:
            copies = '; '.join(c.describe() for c in edition.copies) or 'no copies recorded'
            lines.append(f'• {edition.describe()} — {copies}')
        listed = next((e for e in album.editions if e.tracks), None)
        if listed is not None:
            lines.append(f'Tracks ({listed.label}):')
            multi = len(listed.discs) > 1
            for track in listed.tracks[:30]:
                number = (f'{track.disc}-' if multi else '') + (f'{track.number:02d}' if track.number else '··')
                extra = ' — ' + track.artist if track.artist else ''
                length = f'  {format_duration(track.duration)}' if track.duration else ''
                lines.append(f'  {number}  {track.title}{extra}{length}')
            if len(listed.tracks) > 30:
                lines.append(f'  … and {len(listed.tracks) - 30} more')
        return '\n'.join(lines)

    # -- personal activity --------------------------------------------------------------
    def personal_changed(self, *_):
        album = self.current()
        if self.rendering or album is None or self.store is None:
            return
        favourite, rating = self.favourite.isChecked(), (self.rating.currentIndex() or None)
        if (favourite, rating) == (album.favourite, album.rating):
            return
        try:
            self.store.set_personal(album.id, favourite, rating)
        except MusicStoreError as exc:
            QMessageBox.warning(self, 'Favourite or rating not saved', f'{exc}\nThe previous value was kept.')
            self.rendering = True
            self.favourite.setChecked(album.favourite); self.rating.setCurrentIndex(album.rating or 0)
            self.rendering = False
            return
        self.reload()

    # -- playback -------------------------------------------------------------------------
    def update_player_label(self):
        command = self.state.get('music_player', '')
        self.player_button.setText('Player: ' + (command.split()[0] if command.strip() else 'System default') + '…')
        self.player_button.setToolTip('Albums open in an external player. Music-inator does not track or close it '
                                      'and keeps no listening history.')

    def choose_player(self):
        from .music_player import PlayerError, validate_command
        current = self.state.get('music_player', '')
        text, ok = QInputDialog.getText(self, 'External player',
            'Command used to play albums, for example: audacious   or   mpv --no-video   or   vlc {playlist}\n'
            'Leave empty to open the album playlist with the desktop default application.\n'
            '{playlist} = playlist file, {files} = all tracks, {file} = first track; otherwise the tracks are appended.',
            text=current)
        if not ok:
            return
        try:
            command = validate_command(text)
        except PlayerError as exc:
            QMessageBox.warning(self, 'Player not changed', str(exc)); return
        self.state['music_player'] = command
        if not self.save():
            self.state['music_player'] = current
            QMessageBox.warning(self, 'Player not changed', 'Settings could not be saved. The previous player remains in use.')
        self.update_player_label()

    def play(self, copy):
        from .music_player import PlayerError, launch_album
        key = copy.folder or copy.id
        try:
            launch_album(self.state.get('music_player', ''), copy.files, self.playlist_folder)
        except PlayerError as exc:
            activity_record(self, 'Player launch', key, outcome='failure', pending=True,
                            source=dict(kind='music_play', path=key, copy_id=copy.id),
                            details=dict(error=str(exc)), deduplicate=True)
            QMessageBox.warning(self, 'Cannot play album', str(exc)); return
        activity_resolve(self, 'Player launch', key)
        self.note.setText('Player started with this album. It runs independently; Music-inator does not track or close it.')

    def locate(self, copy):
        from .music_player import match_moved
        start = copy.folder if copy.folder and Path(copy.folder).exists() else str(Path(copy.folder or '~').expanduser().parent)
        chosen = QFileDialog.getExistingDirectory(self, 'Choose the folder where these audio files are now', start)
        if not chosen:
            return
        moves, missing = match_moved(copy.files, chosen)
        if not moves:
            QMessageBox.warning(self, 'Files not found', 'None of the missing files were found in that folder or its '
                                'subfolders. Nothing was changed.'); return
        if missing and QMessageBox.question(self, 'Some files not found',
                f'{len(moves)} file(s) were found; {len(missing)} were not. Update the files that were found?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel) != QMessageBox.StandardButton.Yes:
            return
        try:
            self.store.relocate_files(copy.id, moves)
        except MusicStoreError as exc:
            QMessageBox.warning(self, 'Location not updated', str(exc)); return
        self.reload()

    # -- editing -----------------------------------------------------------------------
    def editor_review(self):
        return self.editor is None or self.editor.review(closing=True)

    def add_album(self):
        if self.store is None or self.busy() or not self.editor_review():
            return
        self.open_editor(None)

    def edit_album(self):
        album = self.current()
        if album is None or self.store is None or self.busy():
            return
        if self.editor is not None and self.editor.album is not None and self.editor.album.id == album.id:
            self.editor.show(); self.editor.raise_(); return
        if not self.editor_review():
            return
        self.open_editor(album)

    def open_editor(self, album):
        if self.editor is not None:
            self.editor.approve_close(); self.editor.close()
        self.editor = AlbumEditor(self.store, album, self)
        self.editor.saved.connect(self.editor_saved)
        self.editor.finished.connect(self.editor_finished)
        self.editor.show()
        return self.editor

    def editor_saved(self, album_id):
        self.state['selected_album'] = album_id
        self.save()
        self.reload()
        activity_record(self, 'Album details save', album_id, outcome='success',
                        source=dict(kind='music_save', album_id=album_id), deduplicate=True)

    def editor_finished(self, *_):
        if self.editor is not None:
            self.editor.deleteLater(); self.editor = None
        self.auto_refresh()

    def open_editions(self):
        album = self.current()
        if album is None or self.store is None:
            return
        if self.editions_dialog is not None:
            self.editions_dialog.close(); self.editions_dialog.deleteLater()
        self.editions_dialog = EditionsDialog(self, album.id)
        self.editions_dialog.show()
        return self.editions_dialog

    def remove_album(self):
        album = self.current()
        if album is None or self.store is None or self.busy():
            return
        if self.editor is not None and self.editor.album is not None and self.editor.album.id == album.id:
            if not self.editor.review(closing=True):
                return
            self.editor.approve_close(); self.editor.close()
        answer = QMessageBox.question(self, 'Remove from catalog',
            f'Remove "{album.display_title}" and its {len(album.editions)} edition(s) from the catalog?\n\n'
            'Audio files and physical copies are NOT deleted. Your favourite mark and rating for it are removed.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Cancel)
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.store.remove_album(album.id)
        except MusicStoreError as exc:
            QMessageBox.warning(self, 'Album not removed', str(exc)); return
        activity_record(self, 'Album removed from catalog', album.id, outcome='success',
                        source=dict(kind='music_catalog', path=str(self.store.path)), details=dict(title=album.display_title))
        self.state['selected_album'] = None; self.save()
        self.reload()

    # -- import -------------------------------------------------------------------------
    def open_import(self, paths=()):
        if self.store is None or self.load_error:
            return None
        if self.import_dialog is None:
            self.import_dialog = MusicImportDialog(self)
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
        """Hub/tab close review: running import, then unsaved album details."""
        if self.busy():
            if QMessageBox.question(self, 'Music import in progress',
                    'Stop after the current album? Completed imports remain in the catalog; nothing else is written. '
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


# ----------------------------------------------------------------------------- album editor
class AlbumEditor(QDialog):
    """Draft editor for album details; nothing is written until Save."""
    saved = pyqtSignal(str)

    def __init__(self, store, album, parent=None):
        super().__init__(parent)
        self.store, self.album = store, album
        self.closing_approved = False
        self.first_copy = None          # (copy dict, tracks) from chosen files
        self.setWindowTitle('Add album' if album is None else f'Edit details — {album.display_title}')
        self.resize(640, 720)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.title = QLineEdit(); self.artist = QLineEdit(); self.year = QLineEdit()
        self.artist.setPlaceholderText('Primary artist, e.g. Pink Floyd or Various Artists')
        self.year.setPlaceholderText('Original release year, e.g. 1979')
        self.other_artists = QPlainTextEdit(); self.other_artists.setPlaceholderText('Other album artists, one per line')
        self.additional = QPlainTextEdit(); self.additional.setPlaceholderText('Featured artists, orchestra, conductor… one per line')
        for box in (self.other_artists, self.additional):
            box.setMaximumHeight(60)
        self.genres = QLineEdit(); self.genres.setPlaceholderText('Comma separated, e.g. Rock, Progressive rock')
        self.notes = QPlainTextEdit(); self.notes.setMaximumHeight(80)
        self.cover = QLineEdit(); self.cover.setReadOnly(True)
        cover_row = QHBoxLayout(); cover_row.addWidget(self.cover, 1)
        choose = QPushButton('Choose image…'); choose.clicked.connect(self.choose_cover); cover_row.addWidget(choose)
        clear = QPushButton('Remove'); clear.clicked.connect(lambda: self.cover.setText('')); cover_row.addWidget(clear)
        for label, widget in (('Album title *', self.title), ('Primary artist', self.artist), ('Other album artists', self.other_artists),
                              ('Additional artists', self.additional), ('Year', self.year), ('Genres', self.genres),
                              ('Cover image', cover_row), ('Private notes', self.notes)):
            form.addRow(label, widget)
        layout.addLayout(form)
        self.first_edition = None
        if album is None:
            box = QGroupBox('First edition (optional)'); edition_form = QFormLayout(box)
            self.edition_format = QComboBox(); self.edition_format.addItems(['None'] + list(EDITION_FORMATS))
            self.edition_label = QLineEdit(); self.edition_label.setPlaceholderText('e.g. Original CD, 2011 Remaster, Deluxe Edition')
            self.edition_year = QLineEdit(); self.edition_year.setPlaceholderText('Release year of this edition')
            self.edition_location = QLineEdit(); self.edition_location.setPlaceholderText('Shelf or box for a physical copy')
            files_row = QHBoxLayout(); self.edition_files = QLineEdit(); self.edition_files.setReadOnly(True)
            folder = QPushButton('Choose album folder…'); folder.clicked.connect(self.choose_folder)
            files_row.addWidget(self.edition_files, 1); files_row.addWidget(folder)
            edition_form.addRow('Format', self.edition_format); edition_form.addRow('Label', self.edition_label)
            edition_form.addRow('Release year', self.edition_year); edition_form.addRow('Physical location', self.edition_location)
            edition_form.addRow('Digital files', files_row)
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
        self.fill(album)
        for widget in (self.title, self.artist, self.year, self.genres, self.cover):
            widget.textChanged.connect(self.update_status)
        for widget in (self.other_artists, self.additional, self.notes):
            widget.textChanged.connect(self.update_status)

    # draft values
    def fill(self, album):
        self.baseline = self.values_of(album)
        artists = self.baseline['artists']
        self.title.setText(self.baseline['title']); self.artist.setText(artists[0] if artists else '')
        self.other_artists.setPlainText('\n'.join(artists[1:])); self.additional.setPlainText('\n'.join(self.baseline['additional_artists']))
        self.year.setText(str(self.baseline['year'] or '')); self.genres.setText(', '.join(self.baseline['genres']))
        self.cover.setText(self.baseline['cover']); self.notes.setPlainText(self.baseline['notes'])
        self.update_status()

    @staticmethod
    def values_of(album):
        if album is None:
            return dict(title='', artists=[], additional_artists=[], year=None, genres=[], cover='', notes='')
        return dict(title=album.title, artists=list(album.artists), additional_artists=list(album.additional_artists),
                    year=album.year, genres=list(album.genres), cover=album.cover, notes=album.notes)

    def raw_values(self):
        text = self.year.text().strip()
        year = None if not text else int(text) if text.isdigit() else text   # validation reports non-numbers
        primary = self.artist.text().strip()
        artists = ([primary] if primary else []) + split_names(self.other_artists.toPlainText())
        return dict(title=self.title.text(), artists=artists, additional_artists=split_names(self.additional.toPlainText()),
                    year=year, genres=split_list(self.genres.text()), cover=self.cover.text(), notes=self.notes.toPlainText())

    def changes(self):
        values = self.raw_values()
        normal = dict(values, title=values['title'].strip(), notes=values['notes'].strip('\n '))
        return {k: v for k, v in normal.items() if v != self.baseline[k]}

    def dirty(self):
        if self.album is None and self.first_edition is not None:
            if (self.edition_format.currentIndex() or self.edition_label.text().strip() or self.edition_files.text()
                    or self.edition_year.text().strip() or self.edition_location.text().strip()):
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

    def choose_folder(self):
        chosen = QFileDialog.getExistingDirectory(self, 'Choose the album folder (disc subfolders are included)')
        if chosen:
            self.use_files([chosen])

    def use_files(self, paths):
        """Read the chosen folder's audio files as the first edition's digital copy.
        Empty title/artist/year fields are filled from the tags or folder name."""
        from .music_scan import files_for
        copy, tracks, unit, skipped = files_for(paths)
        if copy is None:
            self.status.setText('No audio files were found there.'); return False
        self.first_copy = (copy, tracks, unit.disc_count)
        self.edition_files.setText(f'{len(copy["files"])} file(s) · {copy["quality"] or "audio"} · {unit.folder}')
        if self.edition_format.currentText() == 'None':
            self.edition_format.setCurrentText('Digital')
        for widget, value in ((self.title, unit.title), (self.artist, unit.artist), (self.year, str(unit.year or '')),
                              (self.genres, ', '.join(unit.genres)), (self.edition_label, unit.hint)):
            if value and not widget.text().strip():
                widget.setText(value)
        self.update_status()
        return True

    def first_edition_value(self):
        if self.first_edition is None or self.edition_format.currentText() == 'None':
            if self.first_edition is not None and self.first_copy is not None:
                raise MusicStoreError('Choose a format for the first edition, or start again without the chosen files.')
            return []
        fmt = self.edition_format.currentText()
        text = self.edition_year.text().strip()
        release_year = None if not text else int(text) if text.isdigit() else text
        copies, tracks, discs = [], [], 1
        if self.first_copy is not None:
            copy, tracks, discs = self.first_copy
            copies.append(copy)
        if self.edition_location.text().strip() or (fmt != 'Digital' and not copies):
            copies.append(dict(kind='physical', location=self.edition_location.text()))
        return [dict(label=self.edition_label.text().strip() or fmt, format=fmt, release_year=release_year,
                     disc_count=discs, tracks=tracks, copies=copies)]

    # save/discard/review
    def save_changes(self, changes=None):
        try:
            if self.album is None:
                fields = validate_album(self.raw_values())
                album_id = self.store.add_album(fields, self.first_edition_value())
            else:
                changes = self.changes() if changes is None else changes
                if not changes:
                    return True
                self.store.update_album(self.album.id, self.album.revision, validate_album(changes))
                album_id = self.album.id
        except ConflictError as exc:
            return self.resolve_conflict(exc.current)
        except MusicStoreError as exc:
            self.status.setText('Not saved: ' + str(exc) + ' Your edits are still here.')
            return False
        self.album = self.store.get(album_id)
        if self.first_edition is not None:
            self.first_edition.hide(); self.first_edition = None; self.first_copy = None
        self.setWindowTitle(f'Edit details — {self.album.display_title}')
        self.fill(self.album)
        self.status.setText('Saved.')
        self.saved.emit(album_id)
        return True

    def resolve_conflict(self, current):
        dialog = QMessageBox(self)
        dialog.setWindowTitle('Album changed elsewhere')
        mine = self.changes()
        theirs = self.values_of(current)
        lines = [f'{k}: yours = {mine[k]!r}; catalog = {theirs[k]!r}' for k in mine if theirs.get(k) != mine[k]]
        dialog.setText('This album was changed since you opened it. Nothing has been saved yet.\n\n' + '\n'.join(lines[:12]))
        keep = dialog.addButton('Save my values', QMessageBox.ButtonRole.AcceptRole)
        use = dialog.addButton('Use catalog values', QMessageBox.ButtonRole.DestructiveRole)
        dialog.addButton(QMessageBox.StandardButton.Cancel)
        dialog.exec()
        if dialog.clickedButton() is keep:
            # Only the fields you changed are written; other catalog changes are kept.
            self.album = current
            return self.save_changes(mine)
        if dialog.clickedButton() is use:
            self.album = current; self.fill(current); self.status.setText('Catalog values loaded; your edits were discarded.')
            return True
        self.status.setText('Save cancelled. Your edits are still here.')
        return False

    def discard(self):
        self.fill(self.album)
        if self.first_edition is not None:
            self.edition_format.setCurrentIndex(0); self.edition_label.clear(); self.edition_year.clear()
            self.edition_location.clear(); self.edition_files.clear(); self.first_copy = None
        self.update_status()
        return True

    def approve_close(self):
        self.closing_approved = True

    def review(self, closing=False):
        if not self.dirty():
            return True
        answer = QMessageBox.question(self, 'Unsaved album details', 'Save changes before continuing?',
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


# ----------------------------------------------------------------------------- edition & tracks
class EditionDialog(QDialog):
    """Edition fields and its track list. Returns values; the caller saves them."""

    def __init__(self, parent, title, edition=None, copies=()):
        super().__init__(parent)
        self.setWindowTitle(title); self.resize(720, 560)
        self.copies = [c for c in copies if c.kind == 'digital' and c.files]
        self.value = None
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.label = QLineEdit(edition.label if edition else '')
        self.label.setPlaceholderText('e.g. Original CD, 2011 Remaster, Deluxe Edition, Japanese pressing')
        self.format = QComboBox(); self.format.addItems(EDITION_FORMATS); self.format.setCurrentText(edition.format if edition else 'CD')
        self.release_year = QLineEdit(str(edition.release_year or '') if edition else '')
        self.record_label = QLineEdit(edition.record_label if edition else '')
        self.catalog_number = QLineEdit(edition.catalog_number if edition else '')
        self.disc_count = QLineEdit(str(edition.disc_count) if edition else '1')
        self.notes = QLineEdit(edition.notes if edition else '')
        for name, widget in (('Label *', self.label), ('Format', self.format), ('Release year', self.release_year),
                             ('Record label', self.record_label), ('Catalog number', self.catalog_number),
                             ('Discs', self.disc_count), ('Notes', self.notes)):
            form.addRow(name, widget)
        layout.addLayout(form)
        layout.addWidget(QLabel('Track list (Length as minutes:seconds). Leave No. empty for hidden or unnumbered tracks.'))
        self.tracks = QTableWidget(0, len(TRACK_COLUMNS)); self.tracks.setHorizontalHeaderLabels(TRACK_COLUMNS)
        self.tracks.horizontalHeader().setStretchLastSection(False)
        for column, width in enumerate((50, 50, 300, 170, 70)):
            self.tracks.setColumnWidth(column, width)
        self.tracks.setAccessibleName('Track list')
        layout.addWidget(self.tracks, 1)
        for track in (edition.tracks if edition else ()):
            self.add_track(track.disc, track.number, track.title, track.artist, format_duration(track.duration))
        bar = QHBoxLayout()
        add = QPushButton('Add track'); add.clicked.connect(lambda: self.add_track(self.last_disc(), self.next_number(), '', '', ''))
        remove = QPushButton('Remove selected tracks'); remove.clicked.connect(self.remove_tracks)
        fill = QPushButton('Fill from a copy\'s files…'); fill.clicked.connect(self.fill_from_files); fill.setEnabled(bool(self.copies))
        fill.setToolTip('Replace the track list with the titles, numbers and lengths of a digital copy of this edition.')
        for button in (add, remove, fill):
            bar.addWidget(button)
        bar.addStretch()
        layout.addLayout(bar)
        self.status = QLabel(); self.status.setWordWrap(True); layout.addWidget(self.status)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def last_disc(self):
        rows = self.tracks.rowCount()
        item = self.tracks.item(rows - 1, 0) if rows else None
        return int(item.text()) if item and item.text().strip().isdigit() else 1

    def next_number(self):
        disc = self.last_disc()
        numbers = [int(self.tracks.item(r, 1).text()) for r in range(self.tracks.rowCount())
                   if self.tracks.item(r, 1) and self.tracks.item(r, 1).text().strip().isdigit()
                   and self.tracks.item(r, 0) and self.tracks.item(r, 0).text().strip() == str(disc)]
        return max(numbers, default=0) + 1

    def add_track(self, disc, number, title, artist, length):
        row = self.tracks.rowCount(); self.tracks.insertRow(row)
        for column, value in enumerate((str(disc or 1), str(number or ''), title, artist, length)):
            self.tracks.setItem(row, column, QTableWidgetItem(value))

    def remove_tracks(self):
        for row in sorted({i.row() for i in self.tracks.selectedIndexes()}, reverse=True):
            self.tracks.removeRow(row)

    def fill_from_files(self):
        copy = self.copies[0]
        if len(self.copies) > 1:
            names = [f'{c.quality or "Digital files"} · {c.folder}' for c in self.copies]
            name, ok = QInputDialog.getItem(self, 'Fill from files', 'Use the files of:', names, 0, False)
            if not ok:
                return
            copy = self.copies[names.index(name)]
        if self.tracks.rowCount() and QMessageBox.question(self, 'Replace track list',
                'Replace the current track list with the files of this copy?') != QMessageBox.StandardButton.Yes:
            return
        self.tracks.setRowCount(0)
        for index, f in enumerate(copy.files, 1):
            self.add_track(f.disc or 1, f.number or index, f.title or Path(f.path).stem, '', format_duration(f.duration))

    def values(self):
        """(edition fields, tracks); raises ValueError with a user-facing message."""
        def whole(text, name):
            text = text.strip()
            if not text:
                return None
            if not text.isdigit():
                raise ValueError(f'{name} must be a whole number.')
            return int(text)
        fields = dict(label=self.label.text(), format=self.format.currentText(),
                      release_year=whole(self.release_year.text(), 'Release year'), record_label=self.record_label.text(),
                      catalog_number=self.catalog_number.text(), disc_count=whole(self.disc_count.text(), 'Discs') or 1,
                      notes=self.notes.text())
        tracks = []
        for row in range(self.tracks.rowCount()):
            cell = lambda column: (self.tracks.item(row, column).text() if self.tracks.item(row, column) else '')
            if not any(cell(c).strip() for c in (2, 3, 4)):
                continue            # empty rows are ignored
            tracks.append(dict(disc=whole(cell(0), f'Disc in row {row + 1}') or 1, number=whole(cell(1), f'No. in row {row + 1}'),
                               title=cell(2).strip(), artist=cell(3).strip(), duration=parse_duration(cell(4))))
        return fields, tracks

    def accept(self):
        from .music_store import validate_edition, validate_tracks
        try:
            fields, tracks = self.values()
            validate_edition(fields); validate_tracks(tracks)
        except (ValueError, MusicStoreError) as exc:
            self.status.setText('Not saved: ' + str(exc)); return
        self.value = (fields, tracks)
        super().accept()


# ----------------------------------------------------------------------------- editions & copies
class EditionsDialog(QDialog):
    """Editions, track lists and owned copies. Each action saves immediately; removals confirm first."""

    def __init__(self, owner, album_id):
        super().__init__(owner)
        self.owner, self.album_id = owner, album_id
        self.resize(820, 500)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('Each change here is saved immediately. Removing a copy only removes it from the '
                                'catalog; audio files are never deleted, moved or retagged.'))
        self.tree = QTreeWidget(); self.tree.setHeaderLabels(['Edition / copy', 'Format / type', 'Details', 'Location or folder'])
        for column, width in enumerate((230, 110, 190)):
            self.tree.setColumnWidth(column, width)
        layout.addWidget(self.tree, 1)
        self.status = QLabel(); self.status.setWordWrap(True); layout.addWidget(self.status)
        rows = (('Add edition…', self.add_edition), ('Edit edition && tracks…', self.edit_edition), ('Remove edition…', self.remove_edition)), \
               (('Add physical copy…', self.add_physical), ('Add digital files…', self.add_digital),
                ('Edit copy…', self.edit_copy), ('Locate moved files…', self.locate_copy), ('Remove copy…', self.remove_copy))
        for row in rows:
            bar = QHBoxLayout()
            for label, slot in row:
                button = QPushButton(label); button.clicked.connect(slot); bar.addWidget(button)
            layout.addLayout(bar)
        close = QPushButton('Close'); close.clicked.connect(self.close); layout.addWidget(close)
        self.refresh()

    def refresh(self):
        try:
            album = self.owner.store.get(self.album_id)
        except MusicStoreError as exc:
            self.status.setText(str(exc)); self.tree.clear(); return
        self.setWindowTitle(f'Editions, tracks & copies — {album.display_title}')
        selected = self.selected()
        restore = None
        self.tree.clear()
        for edition in album.editions:
            details = ', '.join(p for p in (str(edition.release_year or ''), f'{edition.disc_count} disc(s)',
                                            f'{len(edition.tracks)} tracks') if p)
            parent = QTreeWidgetItem([edition.label, edition.format, details,
                                      ' '.join(p for p in (edition.record_label, edition.catalog_number) if p)])
            parent.setData(0, Qt.ItemDataRole.UserRole, ('edition', edition.id, edition))
            for copy in edition.copies:
                if copy.kind == 'digital':
                    missing = sum(1 for f in copy.files if not Path(f.path).is_file())
                    where = copy.folder + (f'  ({missing} missing)' if missing else '')
                    child = QTreeWidgetItem([copy.quality or 'Digital files', 'Digital', f'{len(copy.files)} file(s)', where])
                else:
                    child = QTreeWidgetItem(['Physical copy', 'Physical', copy.quality or copy.notes, copy.location])
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
        if not album.editions:
            self.status.setText('No editions yet. Add one, e.g. "Original CD", "2011 Remaster" or "Vinyl reissue".')

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
        except MusicStoreError as exc:
            self.status.setText('Not saved: ' + str(exc)); return False
        self.status.setText(success)
        self.owner.reload(); self.refresh()
        return True

    def add_edition(self):
        dialog = EditionDialog(self, 'Add edition')
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.value:
            fields, tracks = dialog.value
            self.run(lambda: self.owner.store.add_edition(self.album_id, fields, tracks), 'Edition added.')

    def edit_edition(self):
        edition = self.selected_edition()
        if edition is None:
            return
        dialog = EditionDialog(self, f'Edit edition — {edition.label}', edition, edition.copies)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.value:
            fields, tracks = dialog.value
            self.run(lambda: self.owner.store.update_edition(edition.id, fields, tracks), 'Edition and track list saved.')

    def remove_edition(self):
        edition = self.selected_edition()
        if edition is None:
            return
        if QMessageBox.question(self, 'Remove edition', f'Remove "{edition.label}", its track list and its {len(edition.copies)} '
                                'copy record(s) from the catalog? Audio files are not deleted.') != QMessageBox.StandardButton.Yes:
            return
        self.run(lambda: self.owner.store.remove_edition(edition.id), 'Edition removed from the catalog.')

    def add_physical(self):
        edition = self.selected_edition()
        if edition is None:
            return
        location, ok = QInputDialog.getText(self, 'Add physical copy', 'Where is it kept? (shelf, box, room — optional)')
        if ok:
            self.run(lambda: self.owner.store.add_copy(edition.id, dict(kind='physical', location=location)), 'Physical copy added.')

    def add_digital(self):
        edition = self.selected_edition()
        if edition is None:
            return
        chosen = QFileDialog.getExistingDirectory(self, 'Choose the folder with this edition\'s audio files')
        if not chosen:
            return
        from .music_scan import files_for
        copy, tracks, unit, skipped = files_for([chosen])
        if copy is None:
            self.status.setText('No audio files were found in that folder.'); return
        def apply():
            self.owner.store.add_copy(edition.id, copy)
        if self.run(apply, f'{len(copy["files"])} audio file(s) added as a digital copy. The files were not moved.') \
                and not edition.tracks and tracks:
            if QMessageBox.question(self, 'Use as track list', 'This edition has no track list yet. '
                                    'Use the titles and numbers of these files?') == QMessageBox.StandardButton.Yes:
                fields = dict(label=edition.label, format=edition.format, release_year=edition.release_year,
                              record_label=edition.record_label, catalog_number=edition.catalog_number,
                              disc_count=max(edition.disc_count, unit.disc_count), notes=edition.notes)
                self.run(lambda: self.owner.store.update_edition(edition.id, fields, tracks), 'Track list filled from the files.')

    def edit_copy(self):
        copy = self.selected_copy()
        if copy is None:
            return
        dialog = QDialog(self); dialog.setWindowTitle('Edit copy')
        form = QFormLayout(dialog)
        location = QLineEdit(copy.location); quality = QLineEdit(copy.quality); notes = QLineEdit(copy.notes)
        quality.setPlaceholderText('e.g. Near mint, FLAC 24-bit/96 kHz, MP3 320 kbps')
        if copy.kind == 'physical':
            form.addRow('Location', location)
        form.addRow('Condition / quality', quality); form.addRow('Notes', notes)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept); buttons.rejected.connect(dialog.reject); form.addRow(buttons)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.run(lambda: self.owner.store.update_copy(copy.id, location.text(), quality.text(), notes.text()), 'Copy saved.')

    def locate_copy(self):
        copy = self.selected_copy()
        if copy is None:
            return
        if copy.kind != 'digital':
            self.status.setText('Physical copies have a location instead; use Edit copy….'); return
        self.owner.locate(copy)
        self.refresh()

    def remove_copy(self):
        copy = self.selected_copy()
        if copy is None:
            return
        if QMessageBox.question(self, 'Remove copy', 'Remove this copy from the catalog? '
                                + ('The audio files themselves are not deleted.' if copy.kind == 'digital' else '')) != QMessageBox.StandardButton.Yes:
            return
        self.run(lambda: self.owner.store.remove_copy(copy.id), 'Copy removed from the catalog.')


# ----------------------------------------------------------------------------- import / scan
class ScanWorker(QObject):
    progress = pyqtSignal(str)
    finished = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, paths, albums, known):
        super().__init__(); self.paths, self.albums, self.known = paths, albums, known; self.cancelled = False

    def run(self):
        from .music_scan import plan
        try:
            result = plan(self.paths, self.albums, self.known, cancelled=lambda: self.cancelled, progress=self.progress.emit)
        except Exception as exc:  # report, never crash the Hub
            self.failed.emit(str(exc)); return
        self.finished.emit(result)


ACTION_CREATE, ACTION_SKIP = 'Create new album', 'Skip'
COL_CHECK, COL_TITLE, COL_ARTIST, COL_YEAR, COL_ACTION, COL_NOTES = range(6)


class MusicImportDialog(QDialog):
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
        self.setWindowTitle('Import music')
        self.setAcceptDrops(True)
        self.resize(980, 620)
        layout = QVBoxLayout(self)
        intro = QLabel('Choose audio files or folders, or drop them here. Files are catalogued where they are: nothing is '
                       'copied, moved, renamed, retagged or deleted. Tags are used first, then folder and file names. '
                       'Each album folder becomes one copy; copies with the same track list share an edition. '
                       'Review the preview, then confirm.')
        intro.setWordWrap(True); layout.addWidget(intro)
        self.sources = QLabel('No files or folders chosen.'); self.sources.setWordWrap(True); layout.addWidget(self.sources)
        bar = QHBoxLayout()
        for label, slot in (('Add files…', self.choose_files), ('Add folder…', self.choose_folder),
                            ('Clear', self.clear), ('Build preview', self.build_preview)):
            button = QPushButton(label); button.clicked.connect(slot); bar.addWidget(button)
        self.stop_button = QPushButton('Stop'); self.stop_button.clicked.connect(self.stop); self.stop_button.setEnabled(False)
        bar.addWidget(self.stop_button)
        layout.addLayout(bar)
        self.tree = QTreeWidget(); self.tree.setHeaderLabels(['Import', 'Album', 'Artist', 'Year', 'Action', 'Files / notes'])
        for column, width in enumerate((60, 230, 170, 55, 250)):
            self.tree.setColumnWidth(column, width)
        self.tree.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.EditKeyPressed)
        layout.addWidget(self.tree, 1)
        self.status = QLabel(); self.status.setWordWrap(True); layout.addWidget(self.status)
        self.confirm = QPushButton('Confirm and import'); self.confirm.setEnabled(False); self.confirm.clicked.connect(self.apply)
        layout.addWidget(self.confirm)
        self.ffprobe_note()

    def ffprobe_note(self):
        from .music_scan import ffprobe_available
        if not ffprobe_available():
            self.status.setText('ffprobe (from FFmpeg) is not installed: tags, track lengths and audio quality cannot be '
                                'read, so albums are recognised from folder and file names only. Importing still works.')

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
        files, _ = QFileDialog.getOpenFileNames(self, 'Choose audio files')
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
            albums, known = store.load(), store.known_paths()
        except MusicStoreError as exc:
            self.status.setText('Cannot read the catalog: ' + str(exc)); return
        self.invalidate()
        self.stop_requested = False
        self.worker = ScanWorker(list(self.paths), albums, known)
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
        albums = {a.id: a for a in self.owner.albums}
        self.tree.clear()
        for group in result.groups:
            item = QTreeWidgetItem(['', group.title, group.artist, str(group.year or ''), '',
                                    f'{len(group.files)} file(s) in {len(group.units)} folder(s)'])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(COL_CHECK, Qt.CheckState.Checked)
            item.setData(COL_CHECK, Qt.ItemDataRole.UserRole, group)
            self.tree.addTopLevelItem(item)
            action = QComboBox()
            action.addItem(ACTION_CREATE, None)
            if group.album_id and group.album_id in albums:
                action.addItem(f'Add to existing: {group.match_title}', group.album_id)
                action.setCurrentIndex(1)
            action.addItem('Add to another album…', 'choose')
            action.addItem(ACTION_SKIP, 'skip')
            action.currentIndexChanged.connect(lambda index, box=action, it=item: self.action_changed(box, it))
            self.tree.setItemWidget(item, COL_ACTION, action)
            self.show_editions(item)
            for warning in group.warnings:
                item.addChild(QTreeWidgetItem(['', '⚠ ' + warning]))
            item.setExpanded(bool(group.warnings) or len(group.units) > 1)
        summary = [f'{len(result.groups)} album(s) found']
        if result.known:
            summary.append(f'{len(result.known)} file(s) already in the catalog were left out')
        if result.skipped:
            summary.append(f'{len(result.skipped)} item(s) skipped: ' + '; '.join(f'{Path(p).name}: {r}' for p, r in result.skipped[:3]))
        self.status.setText('. '.join(summary) + '. Double-click an album, artist or year to correct it. '
                            'Nothing is written until you confirm.')
        self.confirm.setEnabled(bool(result.groups))

    def target_editions(self, group, target):
        """Editions for the chosen action: matched against the target album's editions when attaching."""
        if not target:
            return group.editions(existing=())
        if target == group.album_id:
            return group.editions()
        album = next((a for a in self.owner.albums if a.id == target), None)
        return group.editions(existing=album.editions if album else ())

    def show_editions(self, item):
        group = item.data(COL_CHECK, Qt.ItemDataRole.UserRole)
        box = self.tree.itemWidget(item, COL_ACTION)
        target = box.currentData() if box else (group.album_id if group.action == 'attach' else None)
        for index in reversed(range(item.childCount())):
            if item.child(index).data(COL_CHECK, Qt.ItemDataRole.UserRole) == 'edition':
                item.takeChild(index)
        for position, edition in enumerate(self.target_editions(group, target if target not in ('skip', 'choose') else None)):
            copies = '; '.join(f'{c["quality"] or "audio"} · {len(c["files"])} file(s) · {Path(c["files"][0]["path"]).parent.name}'
                               for c in edition['copies'])
            what = 'Add copy to existing edition' if edition.get('edition_id') else 'New edition'
            child = QTreeWidgetItem(['', edition['label'], f'{len(edition["tracks"])} tracks', str(edition.get('release_year') or ''),
                                     what, copies])
            child.setData(COL_CHECK, Qt.ItemDataRole.UserRole, 'edition')
            item.insertChild(position, child)

    def action_changed(self, box, item):
        if box.currentData() == 'choose':
            albums = sorted(self.owner.albums, key=album_sort_key)
            if not albums:
                QMessageBox.information(self, 'No albums yet', 'The catalog has no albums to add to.')
                box.setCurrentIndex(0); return
            names = [a.display_title for a in albums]
            name, ok = QInputDialog.getItem(self, 'Add to another album', 'Add these files to:', names, 0, False)
            if not ok:
                box.setCurrentIndex(0); return
            album = albums[names.index(name)]
            box.blockSignals(True)
            box.insertItem(box.count() - 2, f'Add to existing: {album.display_title}', album.id)
            box.setCurrentIndex(box.count() - 3)
            box.blockSignals(False)
        self.show_editions(item)

    # apply
    def decisions(self):
        items = []
        for index in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(index)
            group = item.data(COL_CHECK, Qt.ItemDataRole.UserRole)
            box = self.tree.itemWidget(item, COL_ACTION)
            target = box.currentData() if box else None
            if item.checkState(COL_CHECK) != Qt.CheckState.Checked or target in ('skip', 'choose'):
                continue
            year_text = item.text(COL_YEAR).strip()
            year = int(year_text) if year_text.isdigit() else (year_text or None)
            items.append((item, group, item.text(COL_TITLE).strip(), item.text(COL_ARTIST).strip(), year, target))
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
            from .music_scan import revalidate
            known = store.known_paths()
            for item, group, title, artist, year, target in decisions:
                if self.stop_requested:
                    break
                problems = revalidate(group, known)
                name = f'{artist or "Unknown artist"} — {title}'
                try:
                    if problems:
                        raise MusicStoreError(' '.join(problems[:3]) + ' Build the preview again to review the current files.')
                    editions = self.target_editions(group, target)
                    if target:
                        store.apply_group('attach', editions, album_id=target)
                    else:
                        store.apply_group('create', editions, title=title, artists=[artist] if artist else [],
                                          year=year, genres=group.genres)
                    known = store.known_paths()
                except MusicStoreError as exc:
                    failed += 1
                    item.setText(COL_NOTES, 'Not imported: ' + str(exc))
                    details.append(dict(title=name, state='failed', error=str(exc)))
                else:
                    done += 1
                    item.setText(COL_NOTES, 'Imported')
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsUserCheckable & ~Qt.ItemFlag.ItemIsEditable)
                    item.setCheckState(COL_CHECK, Qt.CheckState.Unchecked)
                    details.append(dict(title=name, state='complete'))
                # Keep the window responsive between albums.
                from PyQt6.QtWidgets import QApplication
                QApplication.processEvents()
        finally:
            self.applying = False; self.stop_button.setEnabled(False)
        remaining = len(decisions) - done - failed
        outcome = 'success' if not failed and not remaining else 'partial' if done else 'failure' if failed else 'interrupted'
        activity_record(self.owner, 'Music imports', str(store.path) + '\0' + str(uuid4()), outcome=outcome,
                        pending=False, source=dict(kind='music_import', path=str(store.path)),
                        details=dict(completed=done, failed=failed, pending=remaining, items=details))
        message = f'{done} album(s) imported'
        if failed:
            message += f', {failed} not imported (see the list)'
        if remaining:
            message += f', {remaining} not attempted because you stopped'
        self.status.setText(message + '. Imported albums are in the catalog now; nothing else was written.')
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
