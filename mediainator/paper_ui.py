"""Paper-inator module tab: Home, Library, Notes, Projects and Trash.

Mirrors the other Hub modules: one profile library, remembered search and view,
explicit Save / Discard / Cancel for drafts, previews that must be confirmed before an
import or a permanent deletion writes anything, and no silent change to a user's
files. Knowledge management comes first: items, notes, projects and typed
connections work from the start; documents open in an external reader in M19.
"""
from pathlib import Path
from uuid import uuid4

from PyQt6.QtCore import QObject, Qt, QThread, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QAbstractItemView, QButtonGroup, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout,
    QGridLayout, QGroupBox, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMenu,
    QMessageBox, QPlainTextEdit, QPushButton, QRadioButton, QSplitter, QStackedWidget, QTableWidget, QTableWidgetItem,
    QTableWidgetSelectionRange, QTextBrowser, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from .paper_model import (
    FLAG_FIELDS, FLAGS, HANDLING, ITEM_TYPES, NOTE_KINDS, PROJECT_STATUSES, READING, RELATIONS,
    SAMPLE_LIBRARY, SORTS, STARTUP_VIEWS, SYMMETRIC, VERSION_KINDS, VIEWS, Library, default_criteria, export_markdown,
    find_items, find_notes, home_sections, note_excerpt, note_link, safe_filename,
)
from .paper_store import ChangedFileError, ConflictError, PaperStoreError, validate_item

MODULE = 'paperinator'
COLUMNS = ('Title', 'Authors', 'Year', 'Type', 'Reading', 'Handling', 'Flags', 'Tags')
FILTERS = (('types', 'Type', ITEM_TYPES), ('reading', 'Reading', READING), ('handling', 'Handling', HANDLING),
           ('flags', 'Flags', FLAGS), ('tags', 'Tags', ()))
NO_CHANGE = 'No change'
Q = QMessageBox.StandardButton


def activity_bridge(owner):
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
        try:
            bridge.invoke('resolve_notice', operation, key, module=MODULE)
        except Exception:
            pass


def split_lines(text):
    return [line.strip() for line in (text or '').replace(';', '\n').splitlines() if line.strip()]


def split_commas(text):
    return [part.strip() for part in (text or '').split(',') if part.strip()]


def year_value(text):
    text = (text or '').strip()
    return None if not text else int(text) if text.isdigit() else text     # validation reports non-numbers


def parse_identifiers(text):
    result = []
    for line in (text or '').splitlines():
        if line.strip():
            scheme, sep, value = line.partition(':')
            result.append([scheme.strip(), value.strip()] if sep else ['', line.strip()])
    return result


def human_size(size):
    size = float(size or 0)
    for unit in ('bytes', 'KB', 'MB', 'GB'):
        if size < 1024 or unit == 'GB':
            return f'{size:.0f} {unit}' if unit == 'bytes' else f'{size:.1f} {unit}'
        size /= 1024


def describe_scope(preview, permanent=False):
    """Plain description of what a removal affects, from a store preview."""
    lines = []
    for kind, _, label in preview['objects']:
        lines.append(f'• {"Project/collection" if kind == "project" else kind.capitalize()}: {label}')
    for state in preview.get('states', ()):
        lines.append(f'  Reading state kept with it: {state["reading"]}, {state["handling"]}')
    if preview['connections']:
        lines.append(f'• {preview["connections"]} connection(s) '
                     + ('will be deleted.' if permanent else 'are hidden while in Trash and come back on restore.'))
    if preview['memberships']:
        lines.append(f'• {preview["memberships"]} project/collection membership(s) '
                     + ('will be deleted.' if permanent else 'are kept for restore.'))
    managed = preview['managed_files']
    if managed:
        lines.append(f'• {len(managed)} managed cop{"y" if len(managed) == 1 else "ies"} inside the library '
                     f'({human_size(preview["managed_bytes"])}) '
                     + ('will be DELETED from disk.' if permanent else 'stay on disk until you delete permanently.'))
        lines += [f'    {path}' for path in managed[:5]]
    referenced = preview['referenced_files']
    if referenced:
        lines.append(f'• {len(referenced)} referenced file(s) are NOT deleted and remain where they are:')
        lines += [f'    {path}' for path in referenced[:5]]
    return '\n'.join(lines)


class SafeBrowser(QTextBrowser):
    """Rendered Markdown that never loads remote or local resources on its own and
    reports link clicks instead of following them."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setOpenLinks(False)
        self.setOpenExternalLinks(False)

    def loadResource(self, kind, url):
        return None


# ----------------------------------------------------------------------------- module tab
class Paperinator(QWidget):
    """The Paper-inator tab. `store` is None for the read-only sample library."""

    def __init__(self, state, save, store=None, activity=None, opener=None):
        super().__init__()
        from .paper_adapters import ExternalOpener
        self.state, self.save, self.store, self.activity = state, save, store, activity
        self.opener = opener or ExternalOpener()
        self.library = SAMPLE_LIBRARY if store is None else Library()
        self.visible = []
        self.document_hits = frozenset()
        self.keep_selection = None       # ids to reselect after a bulk change reloads the list
        self.rendering = False
        self.closing = False
        self.editors = []                 # open item and note editors (drafts)
        self.dialogs = []                 # other open dialogs
        self.import_dialog = None
        self.signature = None
        self.load_error = ''
        self.setAcceptDrops(store is not None)
        layout = QVBoxLayout(self)

        self.note = QLabel('Paper-inator library' if store else 'Sample research library · Read-only preview; nothing is saved.')
        self.note.setWordWrap(True)
        layout.addWidget(self.note)

        actions = QHBoxLayout()
        self.add_button = QPushButton('Add item…'); self.add_button.clicked.connect(self.add_item)
        self.import_button = QPushButton('Import PDFs / folder…'); self.import_button.clicked.connect(self.open_import)
        self.new_note_button = QPushButton('New note…'); self.new_note_button.clicked.connect(lambda: self.new_note())
        self.reader_button = QPushButton(); self.reader_button.clicked.connect(self.choose_reader)
        self.reload_button = QPushButton('Reload library'); self.reload_button.clicked.connect(lambda: self.reload(explicit=True))
        for button in (self.add_button, self.import_button, self.new_note_button, self.reader_button, self.reload_button):
            button.setEnabled(store is not None)
            actions.addWidget(button)
        actions.addStretch()
        actions.addWidget(QLabel('Start with:'))
        self.startup = QComboBox(); self.startup.addItems(STARTUP_VIEWS); self.startup.setAccessibleName('Paper-inator startup view')
        self.startup.setCurrentText(state.get('paper_startup', 'Home Dashboard'))
        actions.addWidget(self.startup)
        layout.addLayout(actions)
        self.update_reader_label()

        self.nav = QListWidget(); self.nav.setAccessibleName('Paper-inator sections'); self.nav.addItems(VIEWS)
        self.nav.setMaximumWidth(170)
        self.pages = QStackedWidget()
        self.home = self.build_home()
        self.library_page = self.build_library()
        self.notes_page = self.build_notes()
        self.projects_page = self.build_projects()
        self.trash_page = self.build_trash()
        for page in (self.home, self.library_page, self.notes_page, self.projects_page, self.trash_page):
            self.pages.addWidget(page)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.nav); splitter.addWidget(self.pages); splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter, 1)

        self.refresh_timer = QTimer(self); self.refresh_timer.setInterval(30000); self.refresh_timer.timeout.connect(self.auto_refresh)
        self.nav.currentRowChanged.connect(self.show_view)
        self.startup.currentTextChanged.connect(self.startup_changed)
        if store is not None:
            self.reload()
            self.refresh_timer.start()
        else:
            self.rebuild_filters(); self.render_all()
        start = {'Home Dashboard': 'Home', 'Library': 'Library', 'Projects': 'Projects'}.get(
            state.get('paper_startup', 'Home Dashboard'), state.get('paper_view') if state.get('paper_view') in VIEWS else 'Home')
        self.nav.setCurrentRow(VIEWS.index(start))

    # -- page construction ----------------------------------------------------------
    def build_home(self):
        page = QWidget(); grid = QGridLayout(page)
        self.home_lists = {}
        sections = (('inbox', 'Inbox'), ('continue_reading', 'Continue reading'), ('review', 'Needs review'),
                    ('recent', 'Recently opened'), ('projects', 'Active projects'), ('notes', 'Recent notes'))
        for index, (key, title) in enumerate(sections):
            box = QGroupBox(title); inner = QVBoxLayout(box)
            widget = QListWidget(); widget.setAccessibleName(title)
            widget.itemActivated.connect(self.home_activated)
            widget.itemDoubleClicked.connect(self.home_activated)
            inner.addWidget(widget)
            self.home_lists[key] = widget
            grid.addWidget(box, index // 3, index % 3)
        self.home_hint = QLabel(); self.home_hint.setWordWrap(True)
        grid.addWidget(self.home_hint, 2, 0, 1, 3)
        return page

    def build_library(self):
        page = QWidget(); layout = QVBoxLayout(page)
        saved = dict(default_criteria(), **{k: v for k, v in self.state.get('paper_search', {}).items() if k != 'expanded'})
        bar = QHBoxLayout()
        self.search = QLineEdit(); self.search.setClearButtonEnabled(True)
        self.search.setPlaceholderText('Find in titles, authors, abstracts, tags, notes and document text')
        self.search.setAccessibleName('Find knowledge items')
        self.search.setText(saved.get('text', ''))
        bar.addWidget(self.search, 1)
        self.clear_search = QPushButton('Clear All'); self.clear_search.clicked.connect(self.clear_search_filters)
        bar.addWidget(self.clear_search)
        self.filter_toggle = QCheckBox('Filters'); self.filter_toggle.setChecked(self.state.get('paper_search', {}).get('expanded', True))
        bar.addWidget(self.filter_toggle)
        self.sort = QComboBox(); self.sort.addItems(SORTS); self.sort.setAccessibleName('Sort items')
        self.sort.setCurrentText(saved['sort'] if saved.get('sort') in SORTS else SORTS[0])
        bar.addWidget(self.sort)
        layout.addLayout(bar)

        self.filter_values = {key: set(saved.get(key, [])) for key, _, _ in FILTERS}
        self.container_filter = saved.get('container')
        self.filter_panel = QWidget(); filters = QHBoxLayout(self.filter_panel)
        self.filter_buttons = {}
        for key, label, _ in FILTERS:
            button = QPushButton(label); menu = QMenu(button); button.setMenu(menu)
            self.filter_buttons[key] = (button, menu, label); filters.addWidget(button)
        filters.addWidget(QLabel('In:'))
        self.container_combo = QComboBox(); self.container_combo.setAccessibleName('Limit to project or collection')
        filters.addWidget(self.container_combo)
        filters.addStretch()
        filters.addWidget(QLabel('Saved searches:'))
        self.saved_combo = QComboBox(); self.saved_combo.setAccessibleName('Saved searches'); self.saved_combo.setMinimumWidth(160)
        filters.addWidget(self.saved_combo)
        self.save_search_button = QPushButton('Save search…'); self.save_search_button.clicked.connect(self.save_search)
        self.update_search_button = QPushButton('Update'); self.update_search_button.clicked.connect(self.update_search)
        self.delete_search_button = QPushButton('Remove'); self.delete_search_button.clicked.connect(self.delete_search)
        for button in (self.save_search_button, self.update_search_button, self.delete_search_button):
            filters.addWidget(button)
        self.filter_panel.setVisible(self.filter_toggle.isChecked())
        layout.addWidget(self.filter_panel)

        self.count = QLabel(); layout.addWidget(self.count)
        split = QSplitter(Qt.Orientation.Vertical)
        self.table = QTableWidget(0, len(COLUMNS)); self.table.setHorizontalHeaderLabels(list(COLUMNS))
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAccessibleName('Knowledge items')
        for column, width in enumerate((330, 180, 55, 130, 70, 75, 150, 150)):
            self.table.setColumnWidth(column, width)
        split.addWidget(self.table)
        lower = QWidget(); lower_layout = QVBoxLayout(lower)
        self.selection_label = QLabel(); lower_layout.addWidget(self.selection_label)
        quick = QHBoxLayout()
        quick.addWidget(QLabel('Reading:'))
        self.reading = QComboBox(); self.reading.addItems(READING); self.reading.setAccessibleName('Reading progress')
        quick.addWidget(self.reading)
        quick.addWidget(QLabel('Handling:'))
        self.handling = QComboBox(); self.handling.addItems(HANDLING); self.handling.setAccessibleName('Library handling')
        quick.addWidget(self.handling)
        self.flag_boxes = {}
        for flag in FLAGS:
            box = QCheckBox(flag); self.flag_boxes[flag] = box; quick.addWidget(box)
        quick.addStretch()
        lower_layout.addLayout(quick)
        self.detail = SafeBrowser(); self.detail.setAccessibleName('Item details')
        self.detail.anchorClicked.connect(self.link_clicked)
        lower_layout.addWidget(self.detail, 1)
        buttons = QHBoxLayout()
        self.item_buttons = {}
        for key, label, slot in (('open', 'Open document', self.open_selected), ('edit', 'Edit details…', self.edit_item),
                                 ('versions', 'Versions && files…', self.open_versions),
                                 ('propose', 'Propose metadata from PDF…', self.propose_metadata),
                                 ('note', 'Add note…', lambda: self.new_note(item_id=self.current_id())),
                                 ('connect', 'Connect…', lambda: self.connect_object('item', self.current_id())),
                                 ('organize', 'Organize selected…', self.organize_selected),
                                 ('trash', 'Move to Trash…', self.trash_selected)):
            button = QPushButton(label); button.clicked.connect(slot); self.item_buttons[key] = button; buttons.addWidget(button)
        buttons.addStretch()
        lower_layout.addLayout(buttons)
        split.addWidget(lower)
        split.setStretchFactor(0, 3); split.setStretchFactor(1, 2)
        layout.addWidget(split, 1)

        self.search.textChanged.connect(self.search_changed)
        self.filter_toggle.toggled.connect(self.search_changed)
        self.sort.currentIndexChanged.connect(self.search_changed)
        self.container_combo.currentIndexChanged.connect(self.container_changed)
        self.saved_combo.currentIndexChanged.connect(self.saved_search_chosen)
        self.table.itemSelectionChanged.connect(self.selection_changed)
        self.table.itemDoubleClicked.connect(lambda *_: self.open_selected())
        self.reading.currentTextChanged.connect(lambda value: self.quick_state(reading=value))
        self.handling.currentTextChanged.connect(lambda value: self.quick_state(handling=value))
        for flag, box in self.flag_boxes.items():
            box.toggled.connect(lambda checked, f=flag: self.quick_state(flags={f: checked}))
        return page

    def build_notes(self):
        page = QWidget(); layout = QVBoxLayout(page)
        bar = QHBoxLayout()
        self.note_search = QLineEdit(); self.note_search.setClearButtonEnabled(True)
        self.note_search.setPlaceholderText('Find notes'); self.note_search.setAccessibleName('Find notes')
        bar.addWidget(self.note_search, 1)
        self.note_kind = QComboBox(); self.note_kind.addItem('All note types'); self.note_kind.addItems(NOTE_KINDS)
        self.note_kind.setAccessibleName('Note type')
        bar.addWidget(self.note_kind)
        layout.addLayout(bar)
        split = QSplitter(Qt.Orientation.Horizontal)
        self.note_list = QListWidget(); self.note_list.setAccessibleName('Notes')
        self.note_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        split.addWidget(self.note_list)
        self.note_view = SafeBrowser(); self.note_view.setAccessibleName('Note preview')
        self.note_view.anchorClicked.connect(self.link_clicked)
        split.addWidget(self.note_view); split.setStretchFactor(1, 1)
        layout.addWidget(split, 1)
        buttons = QHBoxLayout()
        self.note_buttons = {}
        for key, label, slot in (('new', 'New note…', lambda: self.new_note()), ('edit', 'Edit note…', self.edit_note),
                                 ('connect', 'Connect…', lambda: self.connect_object('note', self.current_note_id())),
                                 ('project', 'Add to project…', self.note_to_project),
                                 ('export', 'Export as Markdown…', self.export_notes),
                                 ('trash', 'Move to Trash…', self.trash_notes)):
            button = QPushButton(label); button.clicked.connect(slot); self.note_buttons[key] = button; buttons.addWidget(button)
        buttons.addStretch()
        layout.addLayout(buttons)
        self.note_search.textChanged.connect(self.render_notes)
        self.note_kind.currentIndexChanged.connect(self.render_notes)
        self.note_list.itemSelectionChanged.connect(self.note_selected)
        self.note_list.itemDoubleClicked.connect(lambda *_: self.edit_note())
        return page

    def build_projects(self):
        page = QWidget(); layout = QVBoxLayout(page)
        split = QSplitter(Qt.Orientation.Horizontal)
        self.container_list = QListWidget(); self.container_list.setAccessibleName('Projects and collections')
        split.addWidget(self.container_list)
        right = QWidget(); right_layout = QVBoxLayout(right)
        self.container_detail = SafeBrowser(); self.container_detail.setAccessibleName('Project details')
        self.container_detail.anchorClicked.connect(self.link_clicked)
        right_layout.addWidget(self.container_detail, 1)
        self.member_list = QListWidget(); self.member_list.setAccessibleName('Members')
        self.member_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.member_list.itemDoubleClicked.connect(self.member_activated)
        right_layout.addWidget(self.member_list, 1)
        split.addWidget(right); split.setStretchFactor(1, 1)
        layout.addWidget(split, 1)
        buttons = QHBoxLayout()
        self.project_buttons = {}
        for key, label, slot in (('project', 'New project…', lambda: self.new_container('project')),
                                 ('collection', 'New collection…', lambda: self.new_container('collection')),
                                 ('edit', 'Edit…', self.edit_container),
                                 ('show', 'Show items in Library', self.show_container_items),
                                 ('remove', 'Remove selected members', self.remove_members),
                                 ('connect', 'Connect…', lambda: self.connect_object('project', self.current_container_id())),
                                 ('trash', 'Move to Trash…', self.trash_container)):
            button = QPushButton(label); button.clicked.connect(slot); self.project_buttons[key] = button; buttons.addWidget(button)
        buttons.addStretch()
        layout.addLayout(buttons)
        self.container_list.currentRowChanged.connect(lambda *_: self.container_selected())
        return page

    def build_trash(self):
        page = QWidget(); layout = QVBoxLayout(page)
        info = QLabel('Items, notes and projects removed from the library wait here with their notes, connections, '
                      'reading state and project links. Restore brings everything back. Delete permanently removes '
                      'the records and managed copies; referenced files always stay on disk. Trash is not a backup.')
        info.setWordWrap(True); layout.addWidget(info)
        self.trash_list = QListWidget(); self.trash_list.setAccessibleName('Trash')
        layout.addWidget(self.trash_list, 1)
        self.trash_detail = QLabel(); self.trash_detail.setWordWrap(True)
        self.trash_detail.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.trash_detail)
        buttons = QHBoxLayout()
        self.restore_button = QPushButton('Restore'); self.restore_button.clicked.connect(self.restore_trash)
        self.purge_button = QPushButton('Delete permanently…'); self.purge_button.clicked.connect(self.purge_trash)
        buttons.addWidget(self.restore_button); buttons.addWidget(self.purge_button); buttons.addStretch()
        layout.addLayout(buttons)
        self.trash_list.currentRowChanged.connect(lambda *_: self.trash_selected_changed())
        return page

    # -- loading ------------------------------------------------------------------------
    def reload(self, explicit=False):
        if self.store is None or self.closing:
            return False
        if explicit and not self.review_editors():
            return False
        try:
            if not self.store.path.exists():
                self.store.initialize()
            elif not self.busy():
                problems = self.store.recover()
                if problems:
                    self.note.setText('Some interrupted clean-up could not finish: ' + '; '.join(problems[:3]))
            self.library = self.store.load()
            self.signature = self.store.signature()
            self.load_error = ''
            activity_resolve(self, 'Paper-inator library', str(self.store.root))
        except PaperStoreError as exc:
            self.load_error = str(exc)
            self.note.setText('Paper-inator library unavailable. Previous results may be out of date. ' + str(exc))
            activity_record(self, 'Paper-inator library', str(self.store.root), outcome='failure', pending=True,
                            source=dict(kind='paper_library', path=str(self.store.root)), details=dict(error=str(exc)),
                            deduplicate=True)
            self.set_writable(False)
            self.rebuild_filters(); self.render_all()
            return False
        self.note.setText(f'Research library · {len(self.library.items)} items · {len(self.library.notes)} notes · '
                          f'{len(self.library.projects)} projects. Everything stays on this computer; nothing is uploaded.')
        self.set_writable(True)
        self.rebuild_filters()
        self.render_all()
        return True

    def set_writable(self, writable):
        for button in (self.add_button, self.import_button, self.new_note_button):
            button.setEnabled(writable and self.store is not None)

    def writable(self):
        return self.store is not None and not self.load_error

    def auto_refresh(self):
        if self.store is None or self.closing or self.busy():
            return
        if self.store.signature() == self.signature:
            return
        if any(editor.dirty() for editor in self.editors):
            self.note.setText('The library changed elsewhere. Refresh is pending until your drafts are saved or discarded.')
            return
        self.reload()

    def busy(self):
        return bool(self.import_dialog and self.import_dialog.busy())

    # -- views --------------------------------------------------------------------------
    def show_view(self, row):
        if 0 <= row < len(VIEWS):
            self.pages.setCurrentIndex(row)
            if self.state.get('paper_view') != VIEWS[row]:
                self.state['paper_view'] = VIEWS[row]
                self.save()

    def go(self, view):
        self.nav.setCurrentRow(VIEWS.index(view))

    def startup_changed(self, value):
        self.state['paper_startup'] = value
        self.save()

    def render_all(self):
        self.render()
        self.render_home()
        self.render_notes()
        self.render_containers()
        self.render_trash()

    def render_home(self):
        sections = home_sections(self.library)
        for key, widget in self.home_lists.items():
            widget.clear()
            for entry in sections[key]:
                if key == 'projects':
                    text, target = f'{entry.name} · {len(entry.members)} members', ('project', entry.id)
                elif key == 'notes':
                    text, target = f'{entry.display_title} · {entry.kind}', ('note', entry.id)
                else:
                    text, target = f'{entry.display_title} — {entry.display_authors}', ('item', entry.id)
                row = QListWidgetItem(text); row.setData(Qt.ItemDataRole.UserRole, target); widget.addItem(row)
            if not sections[key]:
                empty = QListWidgetItem('Nothing here.'); empty.setData(Qt.ItemDataRole.UserRole, None); widget.addItem(empty)
        if not self.library.items and not self.library.notes:
            self.home_hint.setText('Start by importing a PDF or folder, adding an item by hand, or writing a note. '
                                   'Projects are optional.')
        else:
            self.home_hint.setText('Double-click an entry to open it.')

    def home_activated(self, row):
        target = row.data(Qt.ItemDataRole.UserRole) if row is not None else None
        if target:
            self.navigate(*target)

    def navigate(self, kind, object_id):
        """Show an object wherever it lives (used by Home, links and connections)."""
        if kind == 'item':
            if self.library.item(object_id) is None:
                QMessageBox.information(self, 'Item unavailable', 'This item is not in the library (it may be in Trash).'); return
            self.state['selected_paper'] = object_id
            if not any(i.id == object_id for i in self.visible):
                self.clear_search_filters()
            self.go('Library'); self.render()
        elif kind == 'note':
            if self.library.note(object_id) is None:
                QMessageBox.information(self, 'Note unavailable', 'This note is not in the library (it may be in Trash).'); return
            self.state['selected_paper_note'] = object_id
            self.note_search.blockSignals(True); self.note_search.clear(); self.note_search.blockSignals(False)
            self.note_kind.blockSignals(True); self.note_kind.setCurrentIndex(0); self.note_kind.blockSignals(False)
            self.go('Notes'); self.render_notes()
        elif kind == 'project':
            if self.library.container(object_id) is None:
                QMessageBox.information(self, 'Project unavailable', 'This project is not in the library (it may be in Trash).'); return
            self.state['selected_paper_project'] = object_id
            self.go('Projects'); self.render_containers()
        self.save()

    def link_clicked(self, url):
        if url.scheme() == 'paper':
            kind, _, object_id = url.path().partition('/')
            if kind in ('item', 'note', 'project') and object_id:
                self.navigate(kind, object_id)
            return
        if url.scheme() in ('http', 'https') and QMessageBox.question(
                self, 'Open web link', f'Open this link in your web browser?\n{url.toString()}',
                Q.Yes | Q.Cancel, Q.Cancel) == Q.Yes:
            QDesktopServices.openUrl(url)

    # -- library search and filters ---------------------------------------------------------
    def criteria(self):
        return dict(text=self.search.text(), **{k: sorted(v) for k, v in self.filter_values.items()},
                    container=self.container_filter, sort=self.sort.currentText())

    def rebuild_filters(self):
        for key, (button, menu, label) in self.filter_buttons.items():
            choices = dict(FILTERS_BY_KEY[key])
            menu.clear()
            values = list(choices['values']) if key != 'tags' else sorted(set(self.library.tags) | self.filter_values['tags'],
                                                                           key=str.casefold)
            for value in values:
                action = menu.addAction(value); action.setCheckable(True)
                action.setChecked(value in self.filter_values[key])
                action.toggled.connect(lambda checked, k=key, v=value: self.filter_changed(k, v, checked))
            self.label_filter(key)
        self.container_combo.blockSignals(True)
        self.container_combo.clear()
        self.container_combo.addItem('Whole library', None)
        for container in self.library.containers:
            self.container_combo.addItem(('Project: ' if container.kind == 'project' else 'Collection: ') + container.name,
                                         container.id)
        index = self.container_combo.findData(self.container_filter)
        if index < 0:
            self.container_filter = None; index = 0
        self.container_combo.setCurrentIndex(index)
        self.container_combo.blockSignals(False)
        self.saved_combo.blockSignals(True)
        self.saved_combo.clear(); self.saved_combo.addItem('—', None)
        for search in self.library.searches:
            self.saved_combo.addItem(search.name, search.id)
        chosen = self.saved_combo.findData(self.state.get('paper_saved_search'))
        self.saved_combo.setCurrentIndex(max(chosen, 0))
        self.saved_combo.blockSignals(False)
        self.update_search_buttons()

    def label_filter(self, key):
        button, _, label = self.filter_buttons[key]
        values = sorted(self.filter_values[key], key=str.casefold)
        button.setText(label + (': ' + ', '.join(values) if values else ': All'))

    def filter_changed(self, key, value, checked):
        (self.filter_values[key].add if checked else self.filter_values[key].discard)(value)
        self.search_changed()

    def container_changed(self, *_):
        self.container_filter = self.container_combo.currentData()
        self.search_changed()

    def search_changed(self, *_):
        self.filter_panel.setVisible(self.filter_toggle.isChecked())
        self.state['paper_search'] = dict(self.criteria(), expanded=self.filter_toggle.isChecked())
        self.save()
        for key in self.filter_buttons:
            self.label_filter(key)
        self.render()

    def clear_search_filters(self):
        self.search.blockSignals(True); self.search.clear(); self.search.blockSignals(False)
        for values in self.filter_values.values():
            values.clear()
        self.container_filter = None
        self.state['paper_saved_search'] = None
        self.rebuild_filters(); self.search_changed()

    def render(self):
        self.rendering = True
        text = self.search.text()
        try:
            self.document_hits = self.store.search_documents(text) if self.store is not None and text.strip() and not self.load_error else frozenset()
        except PaperStoreError:
            self.document_hits = frozenset()
        self.visible = find_items(self.library, self.criteria(), self.document_hits)
        self.table.setRowCount(len(self.visible))
        for row, item in enumerate(self.visible):
            values = (item.title, item.display_authors if item.authors else '', str(item.year or ''), item.type, item.reading,
                      item.handling, ', '.join(item.flags), ', '.join(item.tags))
            for column, value in enumerate(values):
                cell = QTableWidgetItem(value)
                cell.setData(Qt.ItemDataRole.UserRole, item.id)
                if column == 0 and item.id in self.document_hits:
                    cell.setToolTip('Found in the document text')
                self.table.setItem(row, column, cell)
        if self.visible:
            scope = ''
            if self.container_filter and self.library.container(self.container_filter):
                scope = ' · in ' + self.library.label('project', self.container_filter)
            self.count.setText(f'{len(self.visible)} of {len(self.library.items)} items{scope}')
        elif self.library.items:
            self.count.setText('No items match this search. Use Clear All to show everything.')
        else:
            self.count.setText('The library is empty. Use Import PDFs / folder…, Add item… or drop PDF files here.')
        selected = self.state.get('selected_paper')
        self.table.clearSelection()
        keep, self.keep_selection = self.keep_selection, None
        rows = [i for i, item in enumerate(self.visible) if item.id in keep] if keep else []
        if len(rows) > 1:
            for row in rows:
                self.table.setRangeSelected(QTableWidgetSelectionRange(row, 0, row, len(COLUMNS) - 1), True)
        else:
            row = next((i for i, item in enumerate(self.visible) if item.id == selected), -1)
            if row >= 0:
                self.table.selectRow(row)
                self.table.setCurrentCell(row, 0)
        self.rendering = False
        self.selection_changed()

    def selected_ids(self):
        rows = sorted({cell.row() for cell in self.table.selectedItems()})
        return [self.visible[row].id for row in rows if 0 <= row < len(self.visible)]

    def current_id(self):
        selected = self.selected_ids()
        current = self.state.get('selected_paper')
        return current if current in selected else (selected[0] if selected else None)

    def current(self):
        return self.library.item(self.current_id()) if self.current_id() else None

    def selection_changed(self):
        if self.rendering:
            return
        ids = self.selected_ids()
        items = [self.library.item(i) for i in ids]
        editable = bool(items) and self.writable()
        for key, button in self.item_buttons.items():
            button.setEnabled(editable and (len(items) == 1 or key in ('organize', 'trash')))
        self.item_buttons['open'].setEnabled(len(items) == 1 and items[0].default_document is not None)
        self.rendering = True
        for widget in (self.reading, self.handling, *self.flag_boxes.values()):
            widget.setEnabled(editable)
        if items:
            first = items[0]
            same = lambda attr: all(getattr(i, attr) == getattr(first, attr) for i in items)
            self.reading.setCurrentText(first.reading); self.handling.setCurrentText(first.handling)
            for flag, box in self.flag_boxes.items():
                box.setChecked(getattr(first, FLAG_FIELDS[flag]))
            mixed = [name for name, attr in (('reading', 'reading'), ('handling', 'handling')) if not same(attr)]
            mixed += [flag for flag in FLAGS if not same(FLAG_FIELDS[flag])]
            self.selection_label.setText(
                f'{len(items)} items selected — reading, handling and flag changes apply to all of them.'
                + (f' Currently mixed: {", ".join(mixed)}.' if mixed else '') if len(items) > 1 else '')
        else:
            self.selection_label.setText('')
        self.rendering = False
        if len(items) == 1:
            if self.state.get('selected_paper') != items[0].id:
                self.state['selected_paper'] = items[0].id
                self.save()
            self.detail.setHtml(self.describe(items[0]))
        elif items:
            self.detail.setPlainText('\n'.join(f'• {i.display_title} — {i.display_authors}' for i in items[:40]))
        else:
            self.detail.setPlainText('Select an item to see its versions, files, notes, connections and projects.')

    def describe(self, item):
        from html import escape
        lib = self.library
        parts = [f'<h3>{escape(item.display_title)}</h3>', f'<p>{escape(item.display_authors)}<br>{escape(item.type)}'
                 + (f' · {escape(item.venue)}' if item.venue else '') + '</p>']
        facts = []
        if item.doi:
            facts.append('DOI: ' + escape(item.doi))
        if item.url:
            facts.append(f'<a href="{escape(item.url)}">{escape(item.url)}</a>')
        facts += [f'{escape(s)}: {escape(v)}' for s, v in item.identifiers]
        if item.keywords:
            facts.append('Keywords: ' + escape(', '.join(item.keywords)))
        if item.tags:
            facts.append('Tags: ' + escape(', '.join(item.tags)))
        facts.append(f'Reading: {item.reading} · Handling: {item.handling}' + (' · ' + ', '.join(item.flags) if item.flags else ''))
        missing = item.incomplete()
        if missing:
            facts.append('<i>Missing: ' + escape(', '.join(missing)) + '</i>')
        parts.append('<p>' + '<br>'.join(facts) + '</p>')
        if item.abstract:
            parts.append('<p><b>Abstract.</b> ' + escape(item.abstract[:1500]) + ('…' if len(item.abstract) > 1500 else '') + '</p>')
        parts.append('<p><b>Versions and files</b></p><ul>')
        if not item.versions:
            parts.append('<li>No versions or files. The item can refer to an external resource.</li>')
        for version in item.versions:
            preferred = ' <b>(preferred)</b>' if version.id == item.preferred_version_id else ''
            parts.append(f'<li>{escape(version.describe())}{preferred}<ul>')
            for f in version.files:
                if f.trashed:
                    continue
                state = '' if Path(f.path).is_file() else ' — <b>missing</b>'
                mode = 'managed copy' if f.mode == 'managed' else 'referenced file'
                searchable = '' if f.has_text else ', text not searchable'
                parts.append(f'<li>{escape(f.name)} ({escape(f.role)}, {mode}{searchable}){state}</li>')
            parts.append('</ul></li>')
        parts.append('</ul>')
        notes = lib.notes_of(item.id)
        parts.append(f'<p><b>Notes ({len(notes)})</b></p><ul>')
        for note in notes:
            parts.append(f'<li><a href="paper:note/{note.id}">{escape(note.display_title)}</a> · {escape(note.kind)}</li>')
        parts.append('</ul>')
        connections = lib.connections_of('item', item.id)
        parts.append(f'<p><b>Connections ({len(connections)})</b></p><ul>')
        for connection in connections:
            relation, kind, other = connection.seen_from('item', item.id)
            comment = f' — {escape(connection.comment)}' if connection.comment else ''
            parts.append(f'<li>{escape(relation)}: <a href="paper:{kind}/{other}">{escape(lib.label(kind, other))}</a>{comment}</li>')
        parts.append('</ul>')
        containers = lib.containers_of('item', item.id)
        if containers:
            parts.append('<p><b>In:</b> ' + ', '.join(f'<a href="paper:project/{c.id}">{escape(lib.label("project", c.id))}</a>'
                                                   for c in containers) + '</p>')
        return ''.join(parts)

    # -- states and organization -------------------------------------------------------------
    def quick_state(self, reading=None, handling=None, flags=None):
        if self.rendering or not self.writable():
            return
        ids = self.selected_ids()
        if not ids:
            return
        try:
            self.store.set_states(ids, reading=reading, handling=handling, flags=flags)
        except PaperStoreError as exc:
            QMessageBox.warning(self, 'State not changed', f'{exc}\nThe previous values were kept.')
        self.keep_selection = ids
        self.reload()

    def organize_selected(self):
        ids = self.selected_ids()
        if not ids or not self.writable():
            return
        dialog = OrganizeDialog(self, ids)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        values = dialog.values()
        try:
            if values['add_tags'] or values['remove_tags']:
                self.store.change_tags(ids, values['add_tags'], values['remove_tags'])
            if values['reading'] or values['handling'] or values['flags']:
                self.store.set_states(ids, values['reading'], values['handling'], values['flags'])
            if values['container']:
                self.store.add_members(values['container'], [('item', i) for i in ids])
        except PaperStoreError as exc:
            QMessageBox.warning(self, 'Organize', f'{exc}\nChanges already saved stay saved; review the items.')
        self.keep_selection = ids
        self.reload()

    # -- saved searches -------------------------------------------------------------------------
    def saved_search_chosen(self, *_):
        search_id = self.saved_combo.currentData()
        self.state['paper_saved_search'] = search_id
        self.update_search_buttons()
        search = next((s for s in self.library.searches if s.id == search_id), None)
        if search is None:
            self.save(); return
        criteria = dict(default_criteria(), **search.criteria)
        self.search.blockSignals(True); self.search.setText(criteria['text']); self.search.blockSignals(False)
        for key in self.filter_values:
            self.filter_values[key] = set(criteria.get(key, []))
        self.container_filter = criteria.get('container')
        self.sort.blockSignals(True); self.sort.setCurrentText(criteria['sort']); self.sort.blockSignals(False)
        self.rebuild_filters()
        if self.container_filter and self.library.container(self.container_filter) is None:
            self.note.setText('This saved search refers to a project or collection that is no longer available; '
                              'the whole library is searched instead.')
        self.search_changed()

    def update_search_buttons(self):
        chosen = self.saved_combo.currentData() is not None
        self.save_search_button.setEnabled(self.writable())
        self.update_search_button.setEnabled(chosen and self.writable())
        self.delete_search_button.setEnabled(chosen and self.writable())

    def save_search(self):
        if not self.writable():
            return
        name, ok = QInputDialog.getText(self, 'Save search', 'Name for this search (the criteria are saved, not the results):')
        if not ok or not name.strip():
            return
        try:
            search_id = self.store.save_search(name, self.criteria())
        except PaperStoreError as exc:
            QMessageBox.warning(self, 'Search not saved', str(exc)); return
        self.state['paper_saved_search'] = search_id
        self.reload()

    def update_search(self):
        search_id = self.saved_combo.currentData()
        search = next((s for s in self.library.searches if s.id == search_id), None)
        if search is None or not self.writable():
            return
        try:
            self.store.save_search(search.name, self.criteria(), search_id)
        except PaperStoreError as exc:
            QMessageBox.warning(self, 'Search not updated', str(exc)); return
        self.reload()

    def delete_search(self):
        search_id = self.saved_combo.currentData()
        if search_id is None or not self.writable():
            return
        if QMessageBox.question(self, 'Remove saved search', f'Remove the saved search "{self.saved_combo.currentText()}"? '
                                'Items are not affected.', Q.Yes | Q.Cancel, Q.Cancel) != Q.Yes:
            return
        try:
            self.store.delete_search(search_id)
        except PaperStoreError as exc:
            QMessageBox.warning(self, 'Search not removed', str(exc)); return
        self.state['paper_saved_search'] = None
        self.reload()

    # -- documents ------------------------------------------------------------------------------
    def update_reader_label(self):
        command = self.state.get('paper_reader', '')
        self.reader_button.setText('Reader: ' + (command.split()[0] if command.strip() else 'System default') + '…')
        self.reader_button.setToolTip('Documents open in an external reader. Paper-inator does not track or close it; '
                                      'positions and annotations made there are not synchronised.')

    def choose_reader(self):
        from .paper_adapters import validate_command
        current = self.state.get('paper_reader', '')
        text, ok = QInputDialog.getText(self, 'External reader',
            'Command used to open documents, for example: okular   or   evince   or   zathura {file}\n'
            'Leave empty to use the desktop default application.', text=current)
        if not ok:
            return
        try:
            command = validate_command(text)
        except PaperStoreError as exc:
            QMessageBox.warning(self, 'Reader not changed', str(exc)); return
        self.state['paper_reader'] = command
        if not self.save():
            self.state['paper_reader'] = current
            QMessageBox.warning(self, 'Reader not changed', 'Settings could not be saved. The previous reader remains in use.')
        self.update_reader_label()

    def open_selected(self):
        item = self.current()
        if item is None:
            return
        document = item.default_document
        if document is None:
            if item.url:
                self.link_clicked(QUrl(item.url))
            else:
                QMessageBox.information(self, 'No document', 'This item has no document. Add one in Versions & files….')
            return
        self.open_file(item, document)

    def open_file(self, item, document):
        if not Path(document.path).is_file():
            if document.mode == 'referenced' and QMessageBox.question(
                    self, 'File not found', f'The file is not available:\n{document.path}\n\nLocate it now?',
                    Q.Yes | Q.Cancel, Q.Yes) == Q.Yes:
                self.locate_file(document)
            elif document.mode == 'managed':
                QMessageBox.warning(self, 'Managed copy missing', 'The managed copy inside the library is missing. '
                                    'Check the library folder or restore it from a backup; the record was kept.')
            return
        try:
            self.opener.open(self.state.get('paper_reader', ''), document.path)
        except PaperStoreError as exc:
            activity_record(self, 'Open document', document.path, outcome='failure', pending=True,
                            source=dict(kind='paper_open', path=document.path, item_id=item.id),
                            details=dict(error=str(exc)), deduplicate=True)
            QMessageBox.warning(self, 'Cannot open document', str(exc)); return
        activity_resolve(self, 'Open document', document.path)
        if self.store is not None and not self.load_error:
            try:
                self.store.mark_opened(item.id)
            except PaperStoreError:
                pass
            self.reload()
        version = next((v for v in item.versions if v.id == document.version_id), None)
        self.note.setText(f'Opened {document.name}' + (f' ({version.label})' if version else '')
                          + ' in the external reader. It runs independently; Paper-inator does not track or close it.')

    def locate_file(self, document):
        start = str(Path(document.path).parent) if Path(document.path).parent.exists() else str(Path.home())
        chosen, _ = QFileDialog.getOpenFileName(self, f'Locate {document.name}', start)
        if not chosen:
            return False
        try:
            self.store.relocate_file(document.id, chosen)
        except ChangedFileError as exc:
            if QMessageBox.question(self, 'Different file', f'{exc}\n\nUse it anyway?', Q.Yes | Q.Cancel, Q.Cancel) != Q.Yes:
                return False
            try:
                self.store.relocate_file(document.id, chosen, accept_changed=True)
            except PaperStoreError as again:
                QMessageBox.warning(self, 'Location not updated', str(again)); return False
        except PaperStoreError as exc:
            QMessageBox.warning(self, 'Location not updated', str(exc)); return False
        self.reload()
        return True

    # -- editing items ------------------------------------------------------------------------------
    def review_editors(self):
        dirty = [editor for editor in self.editors if editor.dirty()]
        if len(dirty) > 1:
            from .close_review import collect, apply_editors
            decision = collect(self, dirty)
            return decision is not None and apply_editors(decision[0])
        for editor in list(self.editors):
            if not editor.review(closing=True):
                return False
        return True

    def find_editor(self, kind, object_id):
        return next((e for e in self.editors if e.kind == kind and e.object_id == object_id and object_id), None)

    def track(self, editor):
        self.editors.append(editor)
        editor.saved.connect(self.editor_saved)
        editor.finished.connect(lambda *_: self.editor_finished(editor))
        editor.show()
        return editor

    def editor_saved(self, kind, object_id):
        if kind == 'item':
            self.state['selected_paper'] = object_id
        else:
            self.state['selected_paper_note'] = object_id
        self.save()
        self.reload()
        activity_record(self, 'Item details save' if kind == 'item' else 'Note save', object_id, outcome='success',
                        source=dict(kind='paper_save', object=kind, id=object_id), deduplicate=True)

    def editor_finished(self, editor):
        if editor in self.editors:
            self.editors.remove(editor)
            editor.deleteLater()
        self.auto_refresh()

    def add_item(self):
        if not self.writable() or self.busy():
            return None
        return self.track(ItemEditor(self.store, None, self))

    def edit_item(self):
        item = self.current()
        if item is None or not self.writable():
            return None
        existing = self.find_editor('item', item.id)
        if existing is not None:
            existing.show(); existing.raise_(); return existing
        return self.track(ItemEditor(self.store, item, self))

    def open_versions(self):
        item = self.current()
        if item is None or not self.writable():
            return None
        dialog = VersionsDialog(self, item.id)
        self.dialogs.append(dialog)
        dialog.finished.connect(lambda *_: self.dialogs.remove(dialog) if dialog in self.dialogs else None)
        dialog.show()
        return dialog

    def propose_metadata(self):
        item = self.current()
        if item is None or not self.writable():
            return None
        document = item.default_document
        if document is None or not Path(document.path).is_file():
            QMessageBox.information(self, 'No document', 'Metadata proposals are read from an available PDF document.')
            return None
        dialog = MetadataReviewDialog(self, item, document)
        if not dialog.proposals:
            QMessageBox.information(self, 'No proposals', dialog.empty_reason); return None
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.reload()
        return dialog

    # -- notes ------------------------------------------------------------------------------------
    def render_notes(self, *_):
        kind = self.note_kind.currentText()
        notes = find_notes(self.library, self.note_search.text(), () if kind == 'All note types' else (kind,))
        self.note_list.blockSignals(True)
        self.note_list.clear()
        current = None
        for note in notes:
            source = self.library.item(note.item_id) if note.item_id else None
            text = f'{note.display_title} · {note.kind}' + (f' · on {source.title}' if source else '')
            row = QListWidgetItem(text); row.setData(Qt.ItemDataRole.UserRole, note.id)
            row.setToolTip(note_excerpt(note))
            self.note_list.addItem(row)
            if note.id == self.state.get('selected_paper_note'):
                current = row
        if current is not None:
            self.note_list.setCurrentItem(current)
        self.note_list.blockSignals(False)
        self.note_selected()

    def selected_note_ids(self):
        return [row.data(Qt.ItemDataRole.UserRole) for row in self.note_list.selectedItems()]

    def current_note_id(self):
        row = self.note_list.currentItem()
        return row.data(Qt.ItemDataRole.UserRole) if row is not None else None

    def note_selected(self):
        note = self.library.note(self.current_note_id()) if self.current_note_id() else None
        editable = note is not None and self.writable()
        for key, button in self.note_buttons.items():
            button.setEnabled(self.writable() if key == 'new' else editable)
        self.note_buttons['export'].setEnabled(bool(self.selected_note_ids()) or note is not None)
        if note is None:
            self.note_view.setPlainText('Select a note, or create one. Notes can stand alone or belong to an item.'
                                        if self.library.notes else 'No notes yet. Use New note… to capture an idea.')
            return
        if self.state.get('selected_paper_note') != note.id:
            self.state['selected_paper_note'] = note.id
            self.save()
        source = self.library.item(note.item_id) if note.item_id else None
        header = f'# {note.display_title}\n\n*{note.kind}*' + (
            f' · Source: {note_link("item", source.id, source.display_title)}' if source else '') + '\n\n'
        connections = self.library.connections_of('note', note.id)
        footer = ''
        if connections:
            footer = '\n\n---\n**Connections:** ' + '; '.join(
                f'{c.seen_from("note", note.id)[0]} {note_link(c.seen_from("note", note.id)[1], c.seen_from("note", note.id)[2], self.library.label(*c.seen_from("note", note.id)[1:]))}'
                for c in connections)
        self.note_view.setMarkdown(header + note.body + footer)

    def new_note(self, item_id=None, body=''):
        if not self.writable():
            return None
        return self.track(NoteEditor(self, None, item_id=item_id, body=body))

    def edit_note(self):
        note = self.library.note(self.current_note_id()) if self.current_note_id() else None
        if note is None or not self.writable():
            return None
        existing = self.find_editor('note', note.id)
        if existing is not None:
            existing.show(); existing.raise_(); return existing
        return self.track(NoteEditor(self, note))

    def note_to_project(self):
        ids = self.selected_note_ids() or ([self.current_note_id()] if self.current_note_id() else [])
        projects = list(self.library.projects)
        if not ids or not self.writable():
            return
        if not projects:
            QMessageBox.information(self, 'No projects', 'Create a project first on the Projects page.'); return
        names = [p.name for p in projects]
        name, ok = QInputDialog.getItem(self, 'Add to project', 'Add the selected note(s) to:', names, 0, False)
        if not ok:
            return
        try:
            self.store.add_members(projects[names.index(name)].id, [('note', i) for i in ids])
        except PaperStoreError as exc:
            QMessageBox.warning(self, 'Not added', str(exc)); return
        self.reload()

    def export_notes(self):
        ids = self.selected_note_ids() or ([self.current_note_id()] if self.current_note_id() else [])
        notes = [self.library.note(i) for i in ids if self.library.note(i)]
        if not notes:
            return None
        folder = QFileDialog.getExistingDirectory(self, 'Export notes as Markdown files into')
        if not folder:
            return None
        return self.write_exports(notes, Path(folder))

    def write_exports(self, notes, folder):
        """Write one readable .md file per note. Existing files are never overwritten.
        Exported files are copies; the library keeps the authoritative note."""
        written = []
        try:
            for note in notes:
                base = safe_filename(note.display_title)
                target = folder / f'{base}.md'
                counter = 2
                while target.exists():
                    target = folder / f'{base} ({counter}).md'; counter += 1
                with open(target, 'x', encoding='utf-8') as stream:
                    stream.write(export_markdown(note, self.library))
                written.append(target)
        except OSError as exc:
            QMessageBox.warning(self, 'Export incomplete', f'{len(written)} note(s) exported before an error: {exc}')
            return written
        self.note.setText(f'{len(written)} note(s) exported as Markdown to {folder}. The library keeps the '
                          'authoritative notes; exported files are copies.')
        return written

    # -- projects and collections -------------------------------------------------------------------
    def render_containers(self):
        self.container_list.blockSignals(True)
        self.container_list.clear()
        current = -1
        for index, container in enumerate(sorted(self.library.containers, key=lambda c: (c.kind != 'project', c.name.casefold()))):
            label = (f'Project: {container.name} · {container.status}' if container.kind == 'project'
                     else f'Collection: {container.name}') + f' · {len(container.members)}'
            row = QListWidgetItem(label); row.setData(Qt.ItemDataRole.UserRole, container.id)
            self.container_list.addItem(row)
            if container.id == self.state.get('selected_paper_project'):
                current = index
        self.container_list.setCurrentRow(current)
        self.container_list.blockSignals(False)
        self.container_selected()

    def current_container_id(self):
        row = self.container_list.currentItem()
        return row.data(Qt.ItemDataRole.UserRole) if row is not None else None

    def container_selected(self):
        from html import escape
        container = self.library.container(self.current_container_id()) if self.current_container_id() else None
        for key, button in self.project_buttons.items():
            button.setEnabled(self.writable() and (key in ('project', 'collection') or container is not None))
        self.project_buttons['show'].setEnabled(container is not None)
        self.project_buttons['connect'].setEnabled(container is not None and container.kind == 'project' and self.writable())
        self.member_list.clear()
        if container is None:
            self.container_detail.setPlainText('Projects gather items and notes for an investigation; collections group '
                                               'items. Both are optional and never duplicate library items.')
            return
        if self.state.get('selected_paper_project') != container.id:
            self.state['selected_paper_project'] = container.id
            self.save()
        html = [f'<h3>{escape(container.name)}</h3><p>{"Project · " + escape(container.status) if container.kind == "project" else "Collection"}</p>']
        if container.description:
            html.append('<p>' + escape(container.description).replace('\n', '<br>') + '</p>')
        connections = self.library.connections_of('project', container.id)
        if connections:
            html.append('<p><b>Connections</b></p><ul>')
            for c in connections:
                relation, kind, other = c.seen_from('project', container.id)
                html.append(f'<li>{escape(relation)}: <a href="paper:{kind}/{other}">{escape(self.library.label(kind, other))}</a></li>')
            html.append('</ul>')
        self.container_detail.setHtml(''.join(html))
        for kind, object_id in container.members:
            row = QListWidgetItem(('Item: ' if kind == 'item' else 'Note: ') + self.library.label(kind, object_id))
            row.setData(Qt.ItemDataRole.UserRole, (kind, object_id))
            self.member_list.addItem(row)

    def member_activated(self, row):
        if row is not None:
            self.navigate(*row.data(Qt.ItemDataRole.UserRole))

    def new_container(self, kind):
        if not self.writable():
            return None
        dialog = ContainerDialog(self, kind)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        values = dialog.values()
        try:
            container_id = self.store.add_container(kind, values['name'], values['description'], values['status'])
        except PaperStoreError as exc:
            QMessageBox.warning(self, 'Not created', str(exc)); return None
        self.state['selected_paper_project'] = container_id
        self.reload()
        return container_id

    def edit_container(self):
        container = self.library.container(self.current_container_id()) if self.current_container_id() else None
        if container is None or not self.writable():
            return
        dialog = ContainerDialog(self, container.kind, container)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        values = dialog.values()
        try:
            self.store.update_container(container.id, values['name'], values['description'], values['status'])
        except PaperStoreError as exc:
            QMessageBox.warning(self, 'Not saved', str(exc)); return
        self.reload()

    def show_container_items(self):
        container_id = self.current_container_id()
        if container_id is None:
            return
        self.search.blockSignals(True); self.search.clear(); self.search.blockSignals(False)
        for values in self.filter_values.values():
            values.clear()
        self.container_filter = container_id
        self.rebuild_filters(); self.search_changed()
        self.go('Library')

    def remove_members(self):
        container_id = self.current_container_id()
        members = [row.data(Qt.ItemDataRole.UserRole) for row in self.member_list.selectedItems()]
        if not container_id or not members or not self.writable():
            return
        try:
            self.store.remove_members(container_id, members)
        except PaperStoreError as exc:
            QMessageBox.warning(self, 'Not removed', str(exc)); return
        self.note.setText(f'{len(members)} member(s) taken out of the project or collection. They remain in the library.')
        self.reload()

    # -- connections -------------------------------------------------------------------------------------
    def connect_object(self, kind, object_id):
        if not object_id or not self.writable() or not self.library.exists(kind, object_id):
            return None
        dialog = ConnectionDialog(self, kind, object_id)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return dialog
        values = dialog.values()
        try:
            if values['remove']:
                self.store.remove_connection(values['remove'])
            else:
                self.store.add_connection(values['source'], values['relation'], values['target'], values['comment'])
        except PaperStoreError as exc:
            QMessageBox.warning(self, 'Connection not saved', str(exc)); return dialog
        self.reload()
        return dialog

    # -- trash ---------------------------------------------------------------------------------------------
    def confirm_trash(self, objects, title):
        try:
            preview = self.store.trash_preview(objects)
        except PaperStoreError as exc:
            QMessageBox.warning(self, title, str(exc)); return False
        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setText('Move to Trash? Everything below can be restored from Trash.\n\n' + describe_scope(preview))
        box.setStandardButtons(Q.Yes | Q.Cancel); box.setDefaultButton(Q.Cancel)
        if box.exec() != Q.Yes:
            return False
        try:
            batch = self.store.trash(objects)
        except PaperStoreError as exc:
            QMessageBox.warning(self, title, str(exc)); return False
        activity_record(self, 'Moved to Trash', batch, outcome='success', source=dict(kind='paper_trash', batch=batch),
                        details=dict(objects=[o[2] for o in preview['objects']][:20]))
        return True

    def trash_selected(self):
        ids = self.selected_ids()
        if not ids or not self.writable() or self.busy():
            return
        for editor in [e for e in self.editors if e.kind == 'item' and e.object_id in ids]:
            if not editor.review(closing=True):
                return
            editor.approve_close(); editor.close()
        if self.confirm_trash([('item', i) for i in ids], 'Move items to Trash'):
            self.state['selected_paper'] = None
            self.reload()

    def trash_notes(self):
        ids = self.selected_note_ids() or ([self.current_note_id()] if self.current_note_id() else [])
        if not ids or not self.writable():
            return
        for editor in [e for e in self.editors if e.kind == 'note' and e.object_id in ids]:
            if not editor.review(closing=True):
                return
            editor.approve_close(); editor.close()
        if self.confirm_trash([('note', i) for i in ids], 'Move notes to Trash'):
            self.state['selected_paper_note'] = None
            self.reload()

    def trash_container(self):
        container_id = self.current_container_id()
        if container_id and self.writable() and self.confirm_trash([('project', container_id)], 'Move to Trash'):
            self.state['selected_paper_project'] = None
            self.reload()

    def render_trash(self):
        self.trash_list.blockSignals(True)
        self.trash_list.clear()
        for batch in self.library.trash:
            state = ' · deletion unfinished — reload to retry' if batch.state == 'purging' else ''
            row = QListWidgetItem(f'{batch.label} · removed {batch.created_at[:16].replace("T", " ")} UTC{state}')
            row.setData(Qt.ItemDataRole.UserRole, batch.id)
            self.trash_list.addItem(row)
        self.trash_list.blockSignals(False)
        self.trash_selected_changed()

    def current_batch(self):
        row = self.trash_list.currentItem()
        batch_id = row.data(Qt.ItemDataRole.UserRole) if row is not None else None
        return next((b for b in self.library.trash if b.id == batch_id), None)

    def trash_selected_changed(self):
        batch = self.current_batch()
        ready = batch is not None and batch.state == 'trashed' and self.writable()
        self.restore_button.setEnabled(ready); self.purge_button.setEnabled(ready)
        if batch is None:
            self.trash_detail.setText('Trash is empty.' if not self.library.trash else 'Select an entry.')
            return
        try:
            self.trash_detail.setText(describe_scope(self.store.purge_preview(batch.id)) if self.store else '')
        except PaperStoreError as exc:
            self.trash_detail.setText(str(exc))

    def restore_trash(self):
        batch = self.current_batch()
        if batch is None or not self.writable():
            return
        try:
            self.store.restore(batch.id)
        except PaperStoreError as exc:
            QMessageBox.warning(self, 'Not restored', str(exc)); return
        activity_record(self, 'Restored from Trash', batch.id, outcome='success', source=dict(kind='paper_trash', batch=batch.id))
        self.note.setText(f'Restored: {batch.label}')
        self.reload()

    def purge_trash(self):
        batch = self.current_batch()
        if batch is None or not self.writable() or self.busy():
            return
        try:
            preview = self.store.purge_preview(batch.id)
        except PaperStoreError as exc:
            QMessageBox.warning(self, 'Delete permanently', str(exc)); return
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle('Delete permanently')
        box.setText('Permanently delete this Trash entry? This cannot be undone.\n\n' + describe_scope(preview, permanent=True)
                    + '\n\nOriginal files you imported from, and all referenced files, remain on disk.')
        delete = box.addButton('Delete permanently', QMessageBox.ButtonRole.DestructiveRole)
        box.addButton(Q.Cancel)
        box.exec()
        if box.clickedButton() is not delete:
            return
        try:
            problems = self.store.purge(batch.id)
        except PaperStoreError as exc:
            QMessageBox.warning(self, 'Not deleted', str(exc)); return
        activity_record(self, 'Deleted permanently', batch.id, outcome='partial' if problems else 'success',
                        pending=bool(problems), source=dict(kind='paper_purge', batch=batch.id, path=str(self.store.root)),
                        details=dict(problems=problems[:10]))
        if problems:
            QMessageBox.warning(self, 'Deletion unfinished', 'The records were deleted, but some managed copies could not '
                                'be removed yet. They are retried when the library is reloaded:\n' + '\n'.join(problems[:5]))
        self.reload()

    # -- import ------------------------------------------------------------------------------------------------
    def open_import(self, paths=()):
        if not self.writable():
            return None
        if self.import_dialog is None:
            self.import_dialog = PaperImportDialog(self)
        if paths:
            self.import_dialog.add_paths(paths)
        self.import_dialog.show(); self.import_dialog.raise_()
        return self.import_dialog

    def dragEnterEvent(self, event):
        if self.writable() and event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        if paths:
            self.open_import(paths)
            event.acceptProposedAction()

    # -- lifecycle -------------------------------------------------------------------------------------------------
    @property
    def editor(self):
        """The first open draft editor (Hub workspace review compatibility)."""
        return self.editors[0] if self.editors else None

    def review_close(self):
        """Hub/tab close review: running import, then unsaved item and note drafts."""
        if self.busy():
            if QMessageBox.question(self, 'Import in progress',
                    'Stop after the current document? Completed imports remain in the library; nothing else is written. '
                    'Close again when it has stopped.', Q.Yes | Q.No, Q.No) == Q.Yes:
                self.import_dialog.stop()
            return False
        return self.review_editors()

    def unattended_close_blocked(self):
        return self.busy() or any(editor.dirty() for editor in self.editors)

    def shutdown(self):
        self.closing = True
        self.refresh_timer.stop()
        if self.import_dialog is not None:
            self.import_dialog.shutdown()
        for editor in list(self.editors):
            editor.approve_close(); editor.close()
        for dialog in list(self.dialogs) + ([self.import_dialog] if self.import_dialog else []):
            dialog.close()


FILTERS_BY_KEY = {key: dict(label=label, values=values) for key, label, values in FILTERS}


# ----------------------------------------------------------------------------- draft editors
class DraftEditor(QDialog):
    """Common Save / Discard / Close review for item and note drafts."""
    saved = pyqtSignal(str, str)
    kind = ''

    def __init__(self, parent):
        super().__init__(parent)
        self.closing_approved = False
        self.status = QLabel(); self.status.setWordWrap(True)

    @property
    def object_id(self):
        return None

    def add_buttons(self, layout):
        layout.addWidget(self.status)
        buttons = QHBoxLayout()
        self.save_button = QPushButton('Save'); self.save_button.setDefault(True)
        self.save_button.clicked.connect(lambda checked=False: self.save_changes())
        self.discard_button = QPushButton('Discard changes'); self.discard_button.clicked.connect(self.discard)
        close = QPushButton('Close'); close.clicked.connect(self.close)
        for button in (self.save_button, self.discard_button, close):
            buttons.addWidget(button)
        layout.addLayout(buttons)

    def update_status(self, *_):
        self.status.setText('Modified — not saved yet.' if self.dirty() else 'No unsaved changes.')

    def approve_close(self):
        self.closing_approved = True

    def review(self, closing=False):
        if not self.dirty():
            return True
        answer = QMessageBox.question(self, 'Unsaved changes', f'Save changes to {self.describe()} before continuing?',
                                      Q.Save | Q.Discard | Q.Cancel, Q.Cancel)
        if answer == Q.Save:
            ok = self.save_changes()
        elif answer == Q.Discard:
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


class ItemEditor(DraftEditor):
    """Draft editor for Knowledge Item metadata; nothing is written until Save."""
    kind = 'item'

    def __init__(self, store, item, parent=None):
        super().__init__(parent)
        self.store, self.item = store, item
        self.setWindowTitle('Add item' if item is None else f'Edit details — {item.display_title}')
        self.resize(680, 760)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.type = QComboBox(); self.type.addItems(ITEM_TYPES)
        self.title = QLineEdit(); self.year = QLineEdit(); self.venue = QLineEdit(); self.doi = QLineEdit(); self.url = QLineEdit()
        self.year.setPlaceholderText('Publication year, e.g. 2021')
        self.venue.setPlaceholderText('Journal, conference, publisher, institution or site')
        self.doi.setPlaceholderText('e.g. 10.1234/abcd (optional)')
        self.url.setPlaceholderText('https://… (for web resources and datasets)')
        self.authors = QPlainTextEdit(); self.authors.setPlaceholderText('One author or contributor per line'); self.authors.setMaximumHeight(80)
        self.identifiers = QPlainTextEdit(); self.identifiers.setPlaceholderText('One per line, e.g. arXiv: 1706.03762  ·  ISBN: …')
        self.identifiers.setMaximumHeight(60)
        self.keywords = QLineEdit(); self.keywords.setPlaceholderText('Comma separated')
        self.tags = QLineEdit(); self.tags.setPlaceholderText('Your own tags, comma separated')
        self.abstract = QPlainTextEdit(); self.abstract.setMaximumHeight(140)
        for label, widget in (('Type', self.type), ('Title *', self.title), ('Authors', self.authors), ('Year', self.year),
                              ('Published in', self.venue), ('DOI', self.doi), ('URL', self.url),
                              ('Other identifiers', self.identifiers), ('Keywords', self.keywords), ('Tags', self.tags),
                              ('Abstract', self.abstract)):
            form.addRow(label, widget)
        layout.addLayout(form)
        self.add_buttons(layout)
        self.fill(item)
        for widget in (self.title, self.year, self.venue, self.doi, self.url, self.keywords, self.tags):
            widget.textChanged.connect(self.update_status)
        for widget in (self.authors, self.identifiers, self.abstract):
            widget.textChanged.connect(self.update_status)
        self.type.currentTextChanged.connect(self.update_status)

    @property
    def object_id(self):
        return self.item.id if self.item else None

    def describe(self):
        return 'the item details'

    @staticmethod
    def values_of(item):
        if item is None:
            return dict(type='Research paper', title='', authors=[], year=None, venue='', abstract='', keywords=[], doi='',
                        identifiers=[], url='', tags=[])
        return dict(type=item.type, title=item.title, authors=list(item.authors), year=item.year, venue=item.venue,
                    abstract=item.abstract, keywords=list(item.keywords), doi=item.doi,
                    identifiers=[list(x) for x in item.identifiers], url=item.url, tags=list(item.tags))

    def fill(self, item):
        self.baseline = self.values_of(item)
        b = self.baseline
        self.type.setCurrentText(b['type']); self.title.setText(b['title']); self.authors.setPlainText('\n'.join(b['authors']))
        self.year.setText(str(b['year'] or '')); self.venue.setText(b['venue']); self.doi.setText(b['doi']); self.url.setText(b['url'])
        self.identifiers.setPlainText('\n'.join(f'{s}: {v}' for s, v in b['identifiers']))
        self.keywords.setText(', '.join(b['keywords'])); self.tags.setText(', '.join(b['tags']))
        self.abstract.setPlainText(b['abstract'])
        self.update_status()

    def raw_values(self):
        return dict(type=self.type.currentText(), title=self.title.text(), authors=split_lines(self.authors.toPlainText()),
                    year=year_value(self.year.text()), venue=self.venue.text(), abstract=self.abstract.toPlainText(),
                    keywords=split_commas(self.keywords.text()), doi=self.doi.text(),
                    identifiers=parse_identifiers(self.identifiers.toPlainText()), url=self.url.text(),
                    tags=split_commas(self.tags.text()))

    def changes(self):
        values = self.raw_values()
        normal = {k: (v.strip() if isinstance(v, str) and k != 'abstract' else v) for k, v in values.items()}
        normal['abstract'] = values['abstract'].strip('\n ')
        return {k: v for k, v in normal.items() if v != self.baseline[k]}

    def dirty(self):
        return bool(self.changes())

    def save_changes(self, changes=None):
        try:
            if self.item is None:
                item_id = self.store.add_item(validate_item(self.raw_values()))
            else:
                changes = self.changes() if changes is None else changes
                if not changes:
                    return True
                self.store.update_item(self.item.id, self.item.revision, validate_item(changes))
                item_id = self.item.id
        except ConflictError as exc:
            return self.resolve_conflict(exc.current)
        except PaperStoreError as exc:
            self.status.setText('Not saved: ' + str(exc) + ' Your edits are still here.')
            return False
        self.item = self.store.get_item(item_id)
        self.setWindowTitle(f'Edit details — {self.item.display_title}')
        self.fill(self.item)
        self.status.setText('Saved.')
        self.saved.emit('item', item_id)
        return True

    def resolve_conflict(self, current):
        dialog = QMessageBox(self)
        dialog.setWindowTitle('Item changed elsewhere')
        mine = self.changes()
        theirs = self.values_of(current)
        lines = [f'{k}: yours = {mine[k]!r}; library = {theirs[k]!r}' for k in mine if theirs.get(k) != mine[k]]
        dialog.setText('This item was changed since you opened it. Nothing has been saved yet.\n\n' + '\n'.join(lines[:12]))
        keep = dialog.addButton('Save my values', QMessageBox.ButtonRole.AcceptRole)
        use = dialog.addButton('Use library values', QMessageBox.ButtonRole.DestructiveRole)
        dialog.addButton(Q.Cancel)
        dialog.exec()
        if current is None:
            self.status.setText('The item is no longer in the library. Your edits are still here.'); return False
        if dialog.clickedButton() is keep:
            self.item = current      # only the fields you changed are written
            return self.save_changes(mine)
        if dialog.clickedButton() is use:
            self.item = current; self.fill(current); self.status.setText('Library values loaded; your edits were discarded.')
            return True
        self.status.setText('Save cancelled. Your edits are still here.')
        return False

    def discard(self):
        self.fill(self.item)
        return True


class MarkdownEdit(QPlainTextEdit):
    def wrap(self, before, after=''):
        cursor = self.textCursor()
        text = cursor.selectedText() or 'text'
        cursor.insertText(before + text + (after if after else before))
        self.setTextCursor(cursor)

    def prefix(self, marker):
        cursor = self.textCursor()
        cursor.movePosition(cursor.MoveOperation.StartOfBlock)
        cursor.insertText(marker)
        self.setTextCursor(cursor)


class NoteEditor(DraftEditor):
    """Markdown note editor with formatting commands, internal links and a safe preview."""
    kind = 'note'

    def __init__(self, owner, note, item_id=None, body=''):
        super().__init__(owner)
        self.owner, self.store, self.note = owner, owner.store, note
        self.setWindowTitle('New note' if note is None else f'Edit note — {note.display_title}')
        self.resize(900, 680)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.title = QLineEdit(); self.title.setPlaceholderText('Optional; the first line is used otherwise')
        self.kind_box = QComboBox(); self.kind_box.addItems(NOTE_KINDS)
        self.source = QComboBox(); self.source.addItem('None — independent note', None)
        for item in sorted(owner.library.items, key=lambda i: i.title.casefold()):
            self.source.addItem(item.display_title, item.id)
        form.addRow('Title', self.title); form.addRow('Type', self.kind_box); form.addRow('Source item', self.source)
        layout.addLayout(form)
        tools = QHBoxLayout()
        self.editor = MarkdownEdit(); self.editor.setAccessibleName('Note text (Markdown)')
        for label, action in (('Bold', lambda: self.editor.wrap('**')), ('Italic', lambda: self.editor.wrap('*')),
                              ('Heading', lambda: self.editor.prefix('## ')), ('List item', lambda: self.editor.prefix('- ')),
                              ('Quote', lambda: self.editor.prefix('> ')), ('Code', lambda: self.editor.wrap('`')),
                              ('Link to item, note or project…', self.insert_link)):
            button = QPushButton(label); button.clicked.connect(action); tools.addWidget(button)
        tools.addStretch()
        layout.addLayout(tools)
        split = QSplitter(Qt.Orientation.Horizontal)
        split.addWidget(self.editor)
        self.preview = SafeBrowser(); self.preview.setAccessibleName('Rendered preview')
        split.addWidget(self.preview)
        layout.addWidget(split, 1)
        self.add_buttons(layout)
        self.fill(note, item_id, body)
        self.title.textChanged.connect(self.update_status)
        self.editor.textChanged.connect(self.update_status)
        self.editor.textChanged.connect(self.update_preview)
        self.kind_box.currentTextChanged.connect(self.update_status)
        self.source.currentIndexChanged.connect(self.update_status)

    @property
    def object_id(self):
        return self.note.id if self.note else None

    def describe(self):
        return 'the note'

    def fill(self, note, item_id=None, body=''):
        if note is None:
            self.baseline = dict(title='', body='', kind='Note' if item_id is None else 'Summary', item_id=item_id)
        else:
            self.baseline = dict(title=note.title, body=note.body, kind=note.kind, item_id=note.item_id)
        self.title.setText(self.baseline['title']); self.editor.setPlainText(self.baseline['body'] or body)
        self.kind_box.setCurrentText(self.baseline['kind'])
        index = self.source.findData(self.baseline['item_id'])
        if index < 0 and self.baseline['item_id']:
            self.source.addItem('Unavailable item', self.baseline['item_id']); index = self.source.count() - 1
        self.source.setCurrentIndex(max(index, 0))
        self.update_preview(); self.update_status()

    def values(self):
        return dict(title=self.title.text().strip(), body=self.editor.toPlainText(), kind=self.kind_box.currentText(),
                    item_id=self.source.currentData())

    def changes(self):
        return {k: v for k, v in self.values().items() if v != self.baseline[k]}

    def dirty(self):
        return bool(self.changes())

    def update_preview(self, *_):
        self.preview.setMarkdown(self.editor.toPlainText())

    def insert_link(self):
        lib = self.owner.library
        choices = ([('item', i.id, 'Item: ' + i.display_title) for i in lib.items]
                   + [('note', n.id, 'Note: ' + n.display_title) for n in lib.notes if not self.note or n.id != self.note.id]
                   + [('project', c.id, lib.label('project', c.id)) for c in lib.containers])
        if not choices:
            QMessageBox.information(self, 'Nothing to link', 'The library has no items, other notes or projects yet.'); return None
        names = [label for _, _, label in choices]
        name, ok = QInputDialog.getItem(self, 'Insert link', 'Link to:', names, 0, False)
        if not ok:
            return None
        kind, object_id, label = choices[names.index(name)]
        label = label.split(': ', 1)[-1]
        self.editor.insertPlainText(note_link(kind, object_id, label))
        return kind, object_id

    def save_changes(self, changes=None):
        try:
            if self.note is None:
                note_id = self.store.add_note(self.values())
            else:
                changes = self.changes() if changes is None else changes
                if not changes:
                    return True
                self.store.update_note(self.note.id, self.note.revision, changes)
                note_id = self.note.id
        except ConflictError as exc:
            return self.resolve_conflict(exc.current)
        except PaperStoreError as exc:
            self.status.setText('Not saved: ' + str(exc) + ' Your text is still here.')
            return False
        self.note = self.store.get_note(note_id)
        self.setWindowTitle(f'Edit note — {self.note.display_title}')
        self.fill(self.note)
        self.status.setText('Saved.')
        self.saved.emit('note', note_id)
        return True

    def resolve_conflict(self, current):
        dialog = QMessageBox(self)
        dialog.setWindowTitle('Note changed elsewhere')
        dialog.setText('This note was changed since you opened it. Nothing has been saved yet. Keep your version, '
                       'load the library version (your text is discarded), or cancel and copy your text first.')
        keep = dialog.addButton('Save my version', QMessageBox.ButtonRole.AcceptRole)
        use = dialog.addButton('Load library version', QMessageBox.ButtonRole.DestructiveRole)
        dialog.addButton(Q.Cancel)
        dialog.exec()
        if current is None:
            self.status.setText('The note is no longer in the library. Your text is still here.'); return False
        mine = self.changes()
        if dialog.clickedButton() is keep:
            self.note = current
            return self.save_changes(mine)
        if dialog.clickedButton() is use:
            self.note = current; self.fill(current); self.status.setText('Library version loaded.')
            return True
        self.status.setText('Save cancelled. Your text is still here.')
        return False

    def discard(self):
        self.fill(self.note, self.baseline['item_id'] if self.note is None else None)
        return True


# ----------------------------------------------------------------------------- versions and files
class VersionFieldsDialog(QDialog):
    def __init__(self, parent, version=None):
        super().__init__(parent)
        self.setWindowTitle('Version')
        layout = QVBoxLayout(self); form = QFormLayout()
        self.label = QLineEdit(); self.label.setPlaceholderText('e.g. arXiv v2, Journal version')
        self.kind = QComboBox(); self.kind.addItems(VERSION_KINDS)
        self.year = QLineEdit(); self.doi = QLineEdit(); self.venue = QLineEdit()
        self.notes = QPlainTextEdit(); self.notes.setMaximumHeight(70)
        for label, widget in (('Label *', self.label), ('Kind', self.kind), ('Year', self.year), ('DOI', self.doi),
                              ('Published in', self.venue), ('Notes', self.notes)):
            form.addRow(label, widget)
        layout.addLayout(form)
        self.error = QLabel(); self.error.setWordWrap(True); layout.addWidget(self.error)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        if version is not None:
            self.label.setText(version.label); self.kind.setCurrentText(version.kind); self.year.setText(str(version.year or ''))
            self.doi.setText(version.doi); self.venue.setText(version.venue); self.notes.setPlainText(version.notes)

    def values(self):
        return dict(label=self.label.text().strip(), kind=self.kind.currentText(), year=year_value(self.year.text()),
                    doi=self.doi.text(), venue=self.venue.text(), notes=self.notes.toPlainText())

    def accept(self):
        from .paper_store import validate_version
        try:
            validate_version(self.values())
        except PaperStoreError as exc:
            self.error.setText(str(exc)); return
        super().accept()


class FileChoiceDialog(QDialog):
    """Explicit choice between a managed copy and a referenced file, plus the file's role."""

    def __init__(self, parent, path):
        super().__init__(parent)
        self.setWindowTitle('Add file')
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f'File: {path}'))
        self.managed = QRadioButton('Managed copy — copy the file into the Paper-inator library (the original stays as it is)')
        self.referenced = QRadioButton('Referenced file — leave the file where it is and record its location')
        group = QButtonGroup(self); group.addButton(self.managed); group.addButton(self.referenced)
        layout.addWidget(self.managed); layout.addWidget(self.referenced)
        form = QFormLayout()
        self.role = QComboBox(); self.role.addItems(['document', 'attachment'])
        self.label = QLineEdit(); self.label.setPlaceholderText('Optional display name, e.g. Supplementary data')
        form.addRow('Role', self.role); form.addRow('Label', self.label)
        layout.addLayout(form)
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept); self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        self.ok = self.buttons.button(QDialogButtonBox.StandardButton.Ok)
        self.ok.setEnabled(False)
        for radio in (self.managed, self.referenced):
            radio.toggled.connect(lambda *_: self.ok.setEnabled(self.mode() is not None))

    def mode(self):
        return 'managed' if self.managed.isChecked() else 'referenced' if self.referenced.isChecked() else None


class VersionsDialog(QDialog):
    """Versions of one item and their documents and attachments."""

    def __init__(self, owner, item_id):
        super().__init__(owner)
        self.owner, self.item_id = owner, item_id
        self.setWindowTitle('Versions & files')
        self.resize(820, 520)
        layout = QVBoxLayout(self)
        intro = QLabel('Versions of the same work (preprint, accepted manuscript, published version). Highlights and '
                       'reading positions will belong to the exact version they were made in. The preferred version '
                       'opens by default; choosing it never changes the item metadata.')
        intro.setWordWrap(True); layout.addWidget(intro)
        self.tree = QTreeWidget(); self.tree.setHeaderLabels(['Version / file', 'Kind', 'Year', 'Storage', 'Status'])
        self.tree.setColumnWidth(0, 330)
        layout.addWidget(self.tree, 1)
        self.message = QLabel(); self.message.setWordWrap(True); layout.addWidget(self.message)
        buttons = QHBoxLayout()
        for label, slot in (('Add version…', self.add_version), ('Edit version…', self.edit_version),
                            ('Set preferred', self.set_preferred), ('Remove empty version', self.remove_version),
                            ('Add file…', self.add_file), ('Open', self.open_file), ('Locate…', self.locate),
                            ('Remove file…', self.remove_file)):
            button = QPushButton(label); button.clicked.connect(slot); buttons.addWidget(button)
        layout.addLayout(buttons)
        close = QPushButton('Close'); close.clicked.connect(self.close); layout.addWidget(close)
        self.refresh()

    def item(self):
        return self.owner.library.item(self.item_id)

    def refresh(self):
        item = self.item()
        self.tree.clear()
        if item is None:
            self.message.setText('This item is no longer in the library.'); return
        self.setWindowTitle(f'Versions & files — {item.display_title}')
        for version in item.versions:
            top = QTreeWidgetItem([version.label + (' ★ preferred' if version.id == item.preferred_version_id else ''),
                                   version.kind, str(version.year or ''), '', version.doi])
            top.setData(0, Qt.ItemDataRole.UserRole, ('version', version.id))
            self.tree.addTopLevelItem(top)
            for f in version.files:
                if f.trashed:
                    continue
                available = Path(f.path).is_file()
                child = QTreeWidgetItem([f.name, f.role, '', 'Managed copy' if f.mode == 'managed' else 'Referenced file',
                                         ('Available' if available else 'Missing') + ('' if f.has_text else ' · no searchable text')])
                child.setToolTip(0, f.path)
                child.setData(0, Qt.ItemDataRole.UserRole, ('file', f.id))
                top.addChild(child)
            top.setExpanded(True)
        if not item.versions:
            self.message.setText('No versions yet. Add a version, then add its document.')

    def selected(self):
        row = self.tree.currentItem()
        return row.data(0, Qt.ItemDataRole.UserRole) if row is not None else None

    def selected_version(self):
        chosen = self.selected()
        item = self.item()
        if chosen is None or item is None:
            return None
        if chosen[0] == 'version':
            return next((v for v in item.versions if v.id == chosen[1]), None)
        return next((v for v in item.versions if any(f.id == chosen[1] for f in v.files)), None)

    def selected_file(self):
        chosen = self.selected()
        item = self.item()
        if chosen is None or chosen[0] != 'file' or item is None:
            return None
        return next((f for f in item.files if f.id == chosen[1]), None)

    def run(self, action, success=''):
        try:
            result = action()
        except PaperStoreError as exc:
            self.message.setText('Not changed: ' + str(exc)); return None
        self.owner.reload(); self.refresh()
        self.message.setText(success)
        return result if result is not None else True

    def add_version(self):
        dialog = VersionFieldsDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return self.run(lambda: self.owner.store.add_version(self.item_id, dialog.values()), 'Version added.')
        return None

    def edit_version(self):
        version = self.selected_version()
        if version is None:
            self.message.setText('Select a version.'); return None
        dialog = VersionFieldsDialog(self, version)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return self.run(lambda: self.owner.store.update_version(version.id, dialog.values()), 'Version saved.')
        return None

    def set_preferred(self):
        version = self.selected_version()
        if version is None:
            self.message.setText('Select a version.'); return None
        return self.run(lambda: self.owner.store.set_preferred_version(self.item_id, version.id),
                        f'"{version.label}" is now the preferred version. Metadata was not changed.')

    def remove_version(self):
        version = self.selected_version()
        if version is None:
            return None
        return self.run(lambda: self.owner.store.remove_version(version.id), 'Version removed.')

    def add_file(self):
        version = self.selected_version()
        if version is None:
            self.message.setText('Select the version the file belongs to (add a version first if needed).'); return None
        chosen, _ = QFileDialog.getOpenFileName(self, 'Choose a document or supplementary file')
        if not chosen:
            return None
        dialog = FileChoiceDialog(self, chosen)
        if dialog.exec() != QDialog.DialogCode.Accepted or dialog.mode() is None:
            return None
        text = ''
        if dialog.role.currentText() == 'document' and chosen.lower().endswith('.pdf'):
            from .paper_adapters import PdfTextExtractor
            try:
                text = PdfTextExtractor().extract(chosen)
            except PaperStoreError:
                text = ''
        mode, role, label = dialog.mode(), dialog.role.currentText(), dialog.label.text()
        return self.run(lambda: self.owner.store.add_file(version.id, chosen, mode, role, label, text),
                        'File added.' + (' It was copied into the library; the original was not changed.' if mode == 'managed' else ''))

    def open_file(self):
        f = self.selected_file()
        if f is not None:
            self.owner.open_file(self.item(), f); self.refresh()

    def locate(self):
        f = self.selected_file()
        if f is None or f.mode != 'referenced':
            self.message.setText('Select a referenced file to locate.'); return
        if self.owner.locate_file(f):
            self.refresh()

    def remove_file(self):
        f = self.selected_file()
        if f is None:
            return
        if self.owner.confirm_trash([('file', f.id)], 'Remove file'):
            self.owner.reload(); self.refresh()


# ----------------------------------------------------------------------------- small dialogs
class ContainerDialog(QDialog):
    def __init__(self, parent, kind, container=None):
        super().__init__(parent)
        self.kind = kind
        self.setWindowTitle(('New ' if container is None else 'Edit ') + kind)
        layout = QVBoxLayout(self); form = QFormLayout()
        self.name = QLineEdit(); self.description = QPlainTextEdit(); self.description.setMaximumHeight(100)
        self.status = QComboBox(); self.status.addItems(PROJECT_STATUSES)
        form.addRow('Name *', self.name); form.addRow('Description', self.description)
        if kind == 'project':
            form.addRow('Status', self.status)
        layout.addLayout(form)
        self.error = QLabel(); layout.addWidget(self.error)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        if container is not None:
            self.name.setText(container.name); self.description.setPlainText(container.description)
            self.status.setCurrentText(container.status)

    def values(self):
        return dict(name=self.name.text().strip(), description=self.description.toPlainText(), status=self.status.currentText())

    def accept(self):
        if not self.name.text().strip():
            self.error.setText('A name is required.'); return
        super().accept()


class ConnectionDialog(QDialog):
    """Inspect, add or remove typed connections of one object."""

    def __init__(self, owner, kind, object_id):
        super().__init__(owner)
        self.owner, self.kind, self.object_id = owner, kind, object_id
        lib = owner.library
        self.setWindowTitle('Connections — ' + lib.label(kind, object_id))
        self.resize(720, 560)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('Existing connections (direction shown from this object):'))
        self.existing = QListWidget(); self.existing.setAccessibleName('Existing connections')
        for connection in lib.connections_of(kind, object_id):
            relation, other_kind, other = connection.seen_from(kind, object_id)
            row = QListWidgetItem(f'{relation} → {lib.label(other_kind, other)}' + (f' — {connection.comment}' if connection.comment else ''))
            row.setData(Qt.ItemDataRole.UserRole, connection.id)
            self.existing.addItem(row)
        layout.addWidget(self.existing)
        remove = QPushButton('Remove selected connection'); remove.clicked.connect(self.remove_selected)
        layout.addWidget(remove)
        box = QGroupBox('New connection'); form = QFormLayout(box)
        self.relation = QComboBox(); self.relation.addItems(RELATIONS)
        self.direction = QComboBox()
        self.direction.addItems(['This object → chosen object', 'Chosen object → this object'])
        self.target_kind = QComboBox()
        self.target_kind.addItem('Item', 'item'); self.target_kind.addItem('Note', 'note'); self.target_kind.addItem('Project', 'project')
        self.filter = QLineEdit(); self.filter.setPlaceholderText('Filter by title')
        self.targets = QListWidget(); self.targets.setAccessibleName('Connection target')
        self.comment = QLineEdit(); self.comment.setPlaceholderText('Optional: why they are connected')
        self.explain = QLabel(); self.explain.setWordWrap(True)
        form.addRow('Relationship', self.relation); form.addRow('Direction', self.direction)
        form.addRow('Connect to', self.target_kind); form.addRow('', self.filter); form.addRow('', self.targets)
        form.addRow('Comment', self.comment); form.addRow('', self.explain)
        layout.addWidget(box)
        self.error = QLabel(); self.error.setWordWrap(True); layout.addWidget(self.error)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText('Add connection')
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.removing = None
        self.target_kind.currentIndexChanged.connect(self.fill_targets)
        self.filter.textChanged.connect(self.fill_targets)
        for widget in (self.relation, self.direction):
            widget.currentIndexChanged.connect(self.update_explain)
        self.targets.currentRowChanged.connect(self.update_explain)
        self.fill_targets()

    def fill_targets(self, *_):
        lib = self.owner.library
        kind = self.target_kind.currentData()
        text = self.filter.text().casefold()
        pool = {'item': [(i.id, i.display_title) for i in lib.items], 'note': [(n.id, n.display_title) for n in lib.notes],
                'project': [(c.id, lib.label('project', c.id)) for c in lib.projects]}[kind]
        self.targets.clear()
        for object_id, label in sorted(pool, key=lambda p: p[1].casefold()):
            if (kind, object_id) == (self.kind, self.object_id) or (text and text not in label.casefold()):
                continue
            row = QListWidgetItem(label); row.setData(Qt.ItemDataRole.UserRole, object_id); self.targets.addItem(row)
        self.update_explain()

    def target(self):
        row = self.targets.currentItem()
        return (self.target_kind.currentData(), row.data(Qt.ItemDataRole.UserRole)) if row is not None else None

    def update_explain(self, *_):
        target = self.target()
        if target is None:
            self.explain.setText('Choose what to connect to.'); return
        lib = self.owner.library
        this, other = lib.label(self.kind, self.object_id), lib.label(*target)
        relation = self.relation.currentText()
        if relation in SYMMETRIC:
            self.explain.setText(f'“{this}” is related to “{other}”.')
        elif self.direction.currentIndex() == 0:
            self.explain.setText(f'“{this}” {relation.lower()} “{other}”.')
        else:
            self.explain.setText(f'“{other}” {relation.lower()} “{this}”.')

    def remove_selected(self):
        row = self.existing.currentItem()
        if row is None:
            self.error.setText('Select a connection to remove.'); return
        if QMessageBox.question(self, 'Remove connection', 'Remove this connection? The connected objects are not changed.',
                                Q.Yes | Q.Cancel, Q.Cancel) == Q.Yes:
            self.removing = row.data(Qt.ItemDataRole.UserRole)
            super().accept()

    def values(self):
        target = self.target()
        me = (self.kind, self.object_id)
        source, destination = (me, target) if self.direction.currentIndex() == 0 else (target, me)
        return dict(remove=self.removing, source=source, target=destination, relation=self.relation.currentText(),
                    comment=self.comment.text())

    def accept(self):
        if self.target() is None:
            self.error.setText('Choose what to connect to.'); return
        super().accept()


class OrganizeDialog(QDialog):
    """Bulk organization of the selected items with an explicit scope."""

    def __init__(self, owner, ids):
        super().__init__(owner)
        self.owner, self.ids = owner, ids
        self.setWindowTitle(f'Organize {len(ids)} selected item(s)')
        layout = QVBoxLayout(self)
        titles = [owner.library.item(i).display_title for i in ids[:8]]
        scope = QLabel(f'These changes apply to exactly {len(ids)} selected item(s):\n• ' + '\n• '.join(titles)
                       + ('\n• …' if len(ids) > 8 else ''))
        scope.setWordWrap(True); layout.addWidget(scope)
        form = QFormLayout()
        self.add_tags = QLineEdit(); self.add_tags.setPlaceholderText('Comma separated')
        self.remove_tags = QLineEdit(); self.remove_tags.setPlaceholderText('Comma separated')
        self.reading = QComboBox(); self.reading.addItems([NO_CHANGE, *READING])
        self.handling = QComboBox(); self.handling.addItems([NO_CHANGE, *HANDLING])
        self.flags = {}
        for flag in FLAGS:
            box = QComboBox(); box.addItems([NO_CHANGE, 'Set', 'Clear']); self.flags[flag] = box
        self.container = QComboBox(); self.container.addItem(NO_CHANGE, None)
        for c in owner.library.containers:
            self.container.addItem(owner.library.label('project', c.id), c.id)
        form.addRow('Add tags', self.add_tags); form.addRow('Remove tags', self.remove_tags)
        form.addRow('Reading progress', self.reading); form.addRow('Library handling', self.handling)
        for flag, box in self.flags.items():
            form.addRow(flag, box)
        form.addRow('Add to project/collection', self.container)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText('Apply to selected')
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def values(self):
        return dict(add_tags=split_commas(self.add_tags.text()), remove_tags=split_commas(self.remove_tags.text()),
                    reading=None if self.reading.currentText() == NO_CHANGE else self.reading.currentText(),
                    handling=None if self.handling.currentText() == NO_CHANGE else self.handling.currentText(),
                    flags={f: box.currentText() == 'Set' for f, box in self.flags.items() if box.currentText() != NO_CHANGE},
                    container=self.container.currentData())


class MetadataReviewDialog(QDialog):
    """Local metadata proposals from the item's PDF, applied only field by field after review."""
    FIELDS = ('title', 'authors', 'keywords', 'doi')

    def __init__(self, owner, item, document, info_tool=None, text_tool=None):
        super().__init__(owner)
        from .paper_adapters import PdfInfoExtractor, PdfTextExtractor
        from .paper_import import propose, SOURCE_FILENAME
        self.owner, self.item = owner, item
        self.setWindowTitle('Review proposed metadata')
        self.resize(820, 420)
        info_tool = info_tool or PdfInfoExtractor(); text_tool = text_tool or PdfTextExtractor()
        self.empty_reason = 'The document offers no information that differs from the current details.'
        if not info_tool.available() and not text_tool.available():
            self.empty_reason = ('pdfinfo and pdftotext (Poppler utilities) are not installed, so nothing can be read '
                                 'from the PDF. Install poppler-utils to get proposals.')
        try:
            info = info_tool.extract(document.path)
            text = text_tool.extract(document.path)
        except PaperStoreError as exc:
            info, text = {}, ''
            self.empty_reason = f'The document could not be read: {exc}'
        fields, sources = propose(document.path, info, text)
        current = ItemEditor.values_of(item)
        self.proposals = []
        for key in self.FIELDS:
            if key not in fields or sources.get(key) == SOURCE_FILENAME:
                continue
            value = fields[key]
            if value != current[key]:
                self.proposals.append((key, current[key], value, sources[key]))
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f'Proposals read from {document.name}. Only checked fields are changed; existing '
                                'values are kept unless you check them.'))
        self.table = QTableWidget(len(self.proposals), 4)
        self.table.setHorizontalHeaderLabels(['Field', 'Current', 'Proposed', 'Source'])
        show = lambda v: ', '.join(v) if isinstance(v, list) else str(v or '—')
        for row, (key, old, new, source) in enumerate(self.proposals):
            check = QTableWidgetItem(key.capitalize())
            check.setFlags(check.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            check.setCheckState(Qt.CheckState.Checked if not old else Qt.CheckState.Unchecked)
            self.table.setItem(row, 0, check)
            for column, value in ((1, show(old)), (2, show(new)), (3, source)):
                self.table.setItem(row, column, QTableWidgetItem(value))
        layout.addWidget(self.table, 1)
        self.error = QLabel(); self.error.setWordWrap(True); layout.addWidget(self.error)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText('Apply checked fields')
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def chosen(self):
        return {self.proposals[row][0]: self.proposals[row][2] for row in range(self.table.rowCount())
                if self.table.item(row, 0).checkState() == Qt.CheckState.Checked}

    def accept(self):
        chosen = self.chosen()
        if not chosen:
            super().reject(); return
        try:
            self.owner.store.update_item(self.item.id, self.item.revision, chosen)
        except ConflictError:
            self.error.setText('The item changed since the proposals were read. Close this window and try again.'); return
        except PaperStoreError as exc:
            self.error.setText(str(exc)); return
        super().accept()


# ----------------------------------------------------------------------------- import
class ScanWorker(QObject):
    progress = pyqtSignal(str)
    finished = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, paths, library, by_hash, by_path):
        super().__init__()
        self.paths, self.library, self.by_hash, self.by_path = paths, library, by_hash, by_path
        self.cancelled = False

    def run(self):
        from .paper_import import plan
        try:
            result = plan(self.paths, self.library, self.by_hash, self.by_path, cancelled=lambda: self.cancelled,
                          progress=self.progress.emit)
        except Exception as exc:  # report, never crash the Hub
            self.failed.emit(str(exc)); return
        self.finished.emit(result)


ACTION_CREATE, ACTION_SKIP = 'Create new item', 'Skip'
COL_CHECK, COL_TITLE, COL_AUTHORS, COL_YEAR, COL_DOI, COL_ACTION, COL_NOTES = range(7)


class PaperImportDialog(QDialog):
    """Choose PDFs or folders (or drop them), choose file handling, build a preview, confirm."""

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner
        self.paths = []
        self.result = None
        self.thread = None
        self.worker = None
        self.applying = False
        self.stop_requested = False
        self.setWindowTitle('Import documents')
        self.setAcceptDrops(True)
        self.resize(1080, 660)
        layout = QVBoxLayout(self)
        intro = QLabel('Choose PDF files or folders, or drop them here. Metadata is read locally from each PDF and '
                       'shown as a proposal you can correct; nothing is looked up online. Identical files and possible '
                       'versions of items you already have are shown for your decision. Nothing is written until you confirm.')
        intro.setWordWrap(True); layout.addWidget(intro)
        self.sources = QLabel('No files or folders chosen.'); self.sources.setWordWrap(True); layout.addWidget(self.sources)
        handling = QGroupBox('File handling (required)'); handling_layout = QVBoxLayout(handling)
        self.managed = QRadioButton('Managed copy — copy each file into the Paper-inator library. Your originals stay '
                                    'exactly as they are.')
        self.referenced = QRadioButton('Referenced file — leave each file where it is and record its location. Moving '
                                       'it later needs Locate….')
        self.mode_group = QButtonGroup(self); self.mode_group.addButton(self.managed); self.mode_group.addButton(self.referenced)
        handling_layout.addWidget(self.managed); handling_layout.addWidget(self.referenced)
        layout.addWidget(handling)
        bar = QHBoxLayout()
        for label, slot in (('Add files…', self.choose_files), ('Add folder…', self.choose_folder),
                            ('Clear', self.clear), ('Build preview', self.build_preview)):
            button = QPushButton(label); button.clicked.connect(slot); bar.addWidget(button)
        self.stop_button = QPushButton('Stop'); self.stop_button.clicked.connect(self.stop); self.stop_button.setEnabled(False)
        bar.addWidget(self.stop_button)
        layout.addLayout(bar)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(['Import', 'Title', 'Authors', 'Year', 'DOI', 'Action', 'Sources / notes'])
        for column, width in enumerate((60, 280, 170, 50, 150, 240)):
            self.tree.setColumnWidth(column, width)
        self.tree.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.EditKeyPressed)
        layout.addWidget(self.tree, 1)
        self.status = QLabel(); self.status.setWordWrap(True); layout.addWidget(self.status)
        self.confirm = QPushButton('Confirm and import'); self.confirm.setEnabled(False); self.confirm.clicked.connect(self.apply)
        layout.addWidget(self.confirm)
        for radio in (self.managed, self.referenced):
            radio.toggled.connect(self.update_confirm)
        self.tools_note()

    def tools_note(self):
        from .paper_adapters import PdfInfoExtractor, PdfTextExtractor
        missing = [name for name, tool in (('pdfinfo', PdfInfoExtractor()), ('pdftotext', PdfTextExtractor())) if not tool.available()]
        if missing:
            self.status.setText(', '.join(missing) + ' (Poppler utilities) not installed: titles fall back to file names '
                                'and document text cannot be searched. Importing still works.')

    def mode(self):
        return 'managed' if self.managed.isChecked() else 'referenced' if self.referenced.isChecked() else None

    def busy(self):
        return bool(self.applying or (self.thread is not None and self.thread.isRunning()))

    def update_confirm(self, *_):
        self.confirm.setEnabled(bool(self.result and self.result.proposals) and self.mode() is not None and not self.busy())
        if self.result and self.result.proposals and self.mode() is None:
            self.status.setText('Choose Managed copy or Referenced file before confirming.')

    # sources
    def add_paths(self, paths):
        if self.busy():
            return
        for path in paths:
            if path and path not in self.paths:
                self.paths.append(str(path))
        self.sources.setText('\n'.join(self.paths[:8]) + (f'\n… and {len(self.paths) - 8} more' if len(self.paths) > 8 else '')
                             if self.paths else 'No files or folders chosen.')
        self.invalidate()

    def choose_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, 'Choose documents', '', 'PDF documents (*.pdf);;All files (*)')
        self.add_paths(files)

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Choose a folder to scan for PDFs (including subfolders)')
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
            library = store.load()
            by_hash, by_path = store.known_files()
        except PaperStoreError as exc:
            self.status.setText('Cannot read the library: ' + str(exc)); return
        self.invalidate()
        self.stop_requested = False
        self.worker = ScanWorker(list(self.paths), library, by_hash, by_path)
        self.thread = QThread(self)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.status.setText)
        self.worker.finished.connect(self.preview_ready)
        self.worker.failed.connect(self.preview_failed)
        thread = self.thread
        self.worker.finished.connect(lambda *_: thread.quit())
        self.worker.failed.connect(lambda *_: thread.quit())
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.scan_stopped)
        self.stop_button.setEnabled(True)
        self.status.setText('Inspecting…')
        self.thread.start()

    def scan_stopped(self):
        self.stop_button.setEnabled(False)
        self.worker = None
        if self.thread is not None:
            self.thread.deleteLater(); self.thread = None
        self.update_confirm()

    def preview_failed(self, message):
        self.status.setText('Preview failed; nothing was imported. ' + message)

    def preview_ready(self, result):
        if self.stop_requested:
            self.status.setText('Inspection stopped. Nothing was imported. Build the preview again when ready.'); return
        self.result = result
        self.tree.clear()
        for proposal in result.proposals:
            fields = proposal.fields
            item = QTreeWidgetItem(['', fields.get('title', ''), '; '.join(fields.get('authors', [])),
                                    str(fields.get('year') or ''), fields.get('doi', ''), '', ''])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsUserCheckable)
            item.setData(COL_CHECK, Qt.ItemDataRole.UserRole, proposal)
            item.setToolTip(COL_TITLE, proposal.path)
            self.tree.addTopLevelItem(item)
            action = QComboBox()
            if proposal.duplicate:
                action.addItem(f'Skip — identical file already in the library{" (in Trash)" if proposal.duplicate[2] else ""}', 'skip')
                item.setCheckState(COL_CHECK, Qt.CheckState.Unchecked)
            else:
                action.addItem(ACTION_CREATE, None)
                for item_id, title, reason in proposal.candidates:
                    action.addItem(f'Add as new version of: {title} ({reason})', item_id)
                action.addItem(ACTION_SKIP, 'skip')
                item.setCheckState(COL_CHECK, Qt.CheckState.Checked)
            self.tree.setItemWidget(item, COL_ACTION, action)
            sources = ', '.join(f'{k}: {v}' for k, v in proposal.sources.items())
            item.setText(COL_NOTES, f'{proposal.name} · {sources}')
            notes = list(proposal.warnings)
            if proposal.candidates:
                notes.insert(0, 'Possibly another version of an item you have. Choose the action; nothing is merged automatically.')
            if proposal.incomplete():
                notes.append('Will be flagged Needs Review: missing ' + ', '.join(proposal.incomplete()) + '.')
            for text in notes:
                item.addChild(QTreeWidgetItem(['', '⚠ ' + text]))
            item.setExpanded(bool(notes))
        summary = [f'{len(result.proposals)} document(s) found']
        if result.skipped:
            summary.append(f'{len(result.skipped)} skipped: ' + '; '.join(f'{Path(p).name}: {r}' for p, r in result.skipped[:3]))
        self.status.setText('. '.join(summary) + '. Double-click a title, authors (separated by ;), year or DOI to correct '
                            'it. New items go to the Inbox. Nothing is written until you confirm.')
        self.update_confirm()

    def decisions(self):
        items = []
        for index in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(index)
            proposal = item.data(COL_CHECK, Qt.ItemDataRole.UserRole)
            box = self.tree.itemWidget(item, COL_ACTION)
            target = box.currentData() if box else None
            if item.checkState(COL_CHECK) != Qt.CheckState.Checked or target == 'skip':
                continue
            fields = dict(proposal.fields, title=item.text(COL_TITLE).strip(),
                          authors=[a.strip() for a in item.text(COL_AUTHORS).split(';') if a.strip()],
                          year=year_value(item.text(COL_YEAR)), doi=item.text(COL_DOI).strip())
            items.append((item, proposal, fields, target))
        return items

    def apply(self):
        from concurrent.futures import ThreadPoolExecutor
        mode = self.mode()
        if self.busy() or self.result is None or mode is None:
            if mode is None:
                self.status.setText('Choose Managed copy or Referenced file before confirming.')
            return
        decisions = self.decisions()
        if not decisions:
            self.status.setText('Nothing selected to import.')
            return
        self.applying = True
        self.stop_requested = False
        self.confirm.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.tree.setEnabled(False)
        self._apply_mode = mode
        self._apply_decisions = decisions
        self._apply_index = 0
        self._apply_done = self._apply_failed = 0
        self._apply_details = []
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='paper-import')
        self._apply_timer = QTimer(self)
        self._apply_timer.setInterval(20)
        self._apply_timer.timeout.connect(self._poll_apply)
        self._submit_apply()
        self._apply_timer.start()

    def _submit_apply(self):
        _, proposal, fields, target = self._apply_decisions[self._apply_index]
        store, mode = self.owner.store, self._apply_mode
        def perform():
            from .paper_import import revalidate
            problems = revalidate(proposal)
            if problems:
                raise PaperStoreError(' '.join(problems) + ' Build the preview again.')
            common = dict(expected=(proposal.size, proposal.sha256), text=proposal.text,
                          cancelled=lambda: self.stop_requested)
            if target:
                return store.import_document(proposal.path, mode, item_id=target,
                    version_fields=dict(label=f'Version from {proposal.name}'[:200], kind='Other version'), **common)
            incomplete = bool(proposal.incomplete()) or not fields.get('authors') or not fields.get('year')
            return store.import_document(proposal.path, mode,
                item_fields={k: v for k, v in fields.items() if v not in (None, '', [])},
                states=dict(handling='Inbox', needs_review=incomplete),
                version_fields=dict(label='Imported document', kind='Other version'), **common)
        self._apply_future = self._executor.submit(perform)

    def _poll_apply(self):
        if not self._apply_future.done():
            return
        item, proposal, fields, _ = self._apply_decisions[self._apply_index]
        try:
            self._apply_future.result()
        except Exception as exc:
            self._apply_failed += 1
            item.setText(COL_NOTES, 'Not imported: ' + str(exc))
            self._apply_details.append(dict(title=fields.get('title', proposal.name), state='failed', error=str(exc)))
        else:
            self._apply_done += 1
            item.setText(COL_NOTES, 'Imported')
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsUserCheckable & ~Qt.ItemFlag.ItemIsEditable)
            item.setCheckState(COL_CHECK, Qt.CheckState.Unchecked)
            self._apply_details.append(dict(title=fields.get('title', proposal.name), state='complete'))
        self._apply_index += 1
        if not self.stop_requested and self._apply_index < len(self._apply_decisions):
            self._submit_apply()
            return
        self._apply_timer.stop()
        self._apply_timer.deleteLater()
        self._executor.shutdown(wait=False)
        self.applying = False
        self.tree.setEnabled(True)
        self.stop_button.setEnabled(False)
        done, failed = self._apply_done, self._apply_failed
        remaining = len(self._apply_decisions) - self._apply_index
        outcome = 'success' if not failed and not remaining else 'partial' if done else 'interrupted' if self.stop_requested else 'failure'
        activity_record(self.owner, 'Document imports', str(self.owner.store.root) + '\0' + str(uuid4()),
            outcome=outcome, pending=False, source=dict(kind='paper_import', path=str(self.owner.store.root)),
            details=dict(completed=done, failed=failed, pending=remaining, mode=self._apply_mode, items=self._apply_details[:50]))
        self.status.setText(f'{done} document(s) imported, {failed} not imported, {remaining} not attempted. See the list for details.')
        if not failed and not remaining:
            self.result = None
        self.confirm.setEnabled(False)
        self.owner.reload()

    def stop(self):
        self.stop_requested = True
        if self.worker is not None:
            self.worker.cancelled = True
        self.status.setText('Stopping after the current document…')

    def shutdown(self):
        self.stop()
        if self.thread is not None and self.thread.isRunning():
            self.thread.quit(); self.thread.wait(5000)

    def closeEvent(self, event):
        if self.busy():
            self.status.setText('Stop the inspection or wait for the import to finish before closing.')
            event.ignore()
        else:
            event.accept()
