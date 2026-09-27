"""Read-only Hub activity presentation. Opening history never executes work."""
from PyQt6.QtCore import Qt, QTimer
from .action_labels import activity_label
from PyQt6.QtWidgets import (QWidget, QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QCheckBox, QTreeWidget, QTreeWidgetItem, QTextBrowser)


def text_value(value):
    if isinstance(value, dict):
        return '\n'.join(f'{key.replace("_", " ").capitalize()}: {text_value(val)}' for key, val in value.items())
    if isinstance(value, list):
        return '\n'.join(text_value(val) for val in value)
    return str(value) if value is not None else 'Not recorded'


def timestamp(attempt):
    return attempt.get('time') or 'Time not recorded (existing history)'


def active(record):
    return not record['dismissed'] and (record['pending'] or record['recovery'] or record.get('deletion'))


def guidance(record):
    kind = record['source'].get('kind')
    if kind == 'recovery' and not (record['pending'] or record['recovery']):
        return 'Recovery is resolved; history is retained. No recovery draft needs to be resumed.'
    return {
        'import': 'Review pending items in Import ebooks before confirming another attempt.',
        'bulk': 'Review the batch in Bulk edit / history before confirming another attempt.',
        'metadata': 'Inspect the book in Edit metadata. A failed Save followed by a failed Retry preserves outstanding edits; review the editor status.',
        'recovery': 'A preserved draft is available. Choose Open recovery draft to reconstruct a draft; a separate Save commits it.',
        'settings': 'Check the settings location and permissions before trying to save preferences again.',
        'refresh': 'Close Calibre and other readers, then choose Reload library.',
        'reader_launch': 'Check the file and close other readers before using its format button again.',
        'movie_catalog': 'Check the Movie-inator catalog location and permissions, then choose Reload catalog in Movie-inator.',
        'movie_play': 'Check that the file is available and the player command works, then use Play or Locate… again.',
        'movie_import': 'Imported movies are already in the catalog. Build a new preview in Import files / scan folder for anything not imported.',
        'movie_save': 'Movie details were saved to the catalog.',
        'music_catalog': 'Check the Music-inator catalog location and permissions, then choose Reload catalog in Music-inator.',
        'music_play': 'Check that the files are available and the player command works, then use Play or Locate… again.',
        'music_import': 'Imported albums are already in the catalog. Build a new preview in Import files / scan folder for anything not imported.',
        'music_save': 'Album details were saved to the catalog.',
        'paper_library': 'Check the Paper-inator library folder and permissions, then choose Reload library in Paper-inator.',
        'paper_open': 'Check that the document is available and the reader command works, then open it again or use Locate….',
        'paper_import': 'Imported documents are already in the library. Build a new preview in Import PDFs / folder for anything not imported.',
        'paper_save': 'The details were saved to the library.',
        'paper_trash': 'Trash keeps the removed research information. Restore it from Trash in Paper-inator if needed.',
        'paper_purge': 'The records are deleted. Remaining managed copies are removed when Paper-inator reloads the library.',
    }.get(kind, 'Review the details before taking further action. Nothing resumes automatically.')


class ActivityDetails(QDialog):
    def __init__(self, record, parent=None, attempt_id=None):
        super().__init__(parent)
        self.record_id = record['id']
        self.setWindowTitle(record['operation'] + ' — Activity details')
        self.resize(720, 530)
        layout = QVBoxLayout(self)
        self.content = QTextBrowser()
        lines = [f"Module: {record['module']}", f"Operation: {record['operation']}",
                 f"Pending: {'Yes' if record['pending'] else 'No'}",
                 f"Recovery required: {'Yes' if record['recovery'] else 'No'}",
                 f"Dismissed: {'Yes' if record['dismissed'] else 'No'}"]
        if record['source'].get('kind')=='recovery':
            lines.append('Recovery state: '+('Draft preserved; review pending' if record['pending'] or record['recovery'] else 'Resolved; history retained'))
        if record['source'].get('library'): lines.append('Library: ' + record['source']['library'])
        for attempt in reversed(record['attempts']):
            lines.extend(['', ('Selected attempt — ' if attempt['id'] == attempt_id else '') + timestamp(attempt),
                          'Outcome: ' + attempt['outcome'].capitalize(), text_value(attempt['details'])])
            if attempt.get('occurrences'): lines.append(f"Occurrences: {attempt['occurrences']}")
        if record.get('original_history_deleted'): lines.append('The original batch history was explicitly deleted; this operation is retained.')
        if record.get('deletion'): lines.append('Cleanup incomplete. Delete this history record retries the previously confirmed cleanup.')
        lines.extend(['', 'Next steps', guidance(record)])
        self.content.setPlainText('\n'.join(lines))
        layout.addWidget(self.content)
        controller = getattr(parent, 'controller', None)
        if controller:
            bar = QHBoxLayout(); self.actions = {};layout.addLayout(bar)
            for action in ('review', 'dismiss', 'discard', 'delete'):
                if len(self.actions)==2:
                    bar=QHBoxLayout();layout.addLayout(bar)
                label = activity_label(record, action)
                button = QPushButton(label); self.actions[action] = button
                button.clicked.connect(lambda _, a=action: controller.perform(a, record['id']))
                bar.addWidget(button)
            self.actions['dismiss'].setToolTip('Hide this entry from the action list; its history and recoverable work remain available.')
            self.actions['delete'].setToolTip('Unresolved work must first be reviewed and explicitly discarded.')
            if record['source'].get('kind') == 'recovery' and not (record['pending'] or record['recovery']):
                self.actions['review'].setEnabled(False)
            self.actions['delete'].setEnabled(not (record['pending'] or record['recovery']))
            self.actions['discard'].setEnabled(bool(record['pending'] or record['recovery']) and record['source'].get('kind') in ('import','bulk','recovery','metadata'))
            if record.get('deletion'):
                for action in ('review', 'dismiss', 'discard'): self.actions[action].setEnabled(False)
        close = QPushButton('Close details'); close.clicked.connect(self.close); layout.addWidget(close)


class ActivityHistory(QDialog):
    def __init__(self, panel, recovery_only=False):
        super().__init__(panel)
        self.panel = panel
        self.setWindowTitle('Full Activity History'); self.resize(850, 500)
        layout = QVBoxLayout(self)
        self.show_dismissed = QCheckBox('Show dismissed'); self.show_dismissed.setChecked(True)
        self.recovery_only = QCheckBox('Unresolved work only'); self.recovery_only.setChecked(recovery_only)
        for control in (self.show_dismissed, self.recovery_only):
            layout.addWidget(control); control.toggled.connect(self.refresh)
        self.tree = QTreeWidget(); self.tree.setHeaderLabels(['Module / Operation', 'Latest outcome', 'Time', 'Attention'])
        self.tree.itemActivated.connect(self.open_item); layout.addWidget(self.tree)
        details = QPushButton('Open selected record'); details.clicked.connect(lambda: self.open_item(self.tree.currentItem()))
        self.details_button = details
        self.tree.currentItemChanged.connect(lambda current, previous: details.setEnabled(bool(current and current.data(0, Qt.ItemDataRole.UserRole))))
        layout.addWidget(details)
        self.notice = QLabel(); self.notice.setWordWrap(True); layout.addWidget(self.notice)
        close = QPushButton('Close history'); close.clicked.connect(self.close); layout.addWidget(close)
        self.refresh()

    def refresh(self):
        selected = self.tree.currentItem()
        identity = selected.data(0, Qt.ItemDataRole.UserRole) if selected else None
        self.tree.clear(); groups = {}
        for record in sorted(self.panel.records, key=lambda r: r['attempts'][-1]['time'] or '' if r['attempts'] else '', reverse=True):
            if record['dismissed'] and not self.show_dismissed.isChecked(): continue
            if self.recovery_only.isChecked() and not (record['pending'] or record['recovery'] or record.get('deletion')): continue
            key = (record['module'], record['operation'])
            if key not in groups:
                groups[key] = QTreeWidgetItem(self.tree, [f'{key[0]} / {key[1]}'])
            attempt = record['attempts'][-1] if record['attempts'] else None
            flags = [name for name in ('pending', 'recovery', 'dismissed') if record[name]]
            row = QTreeWidgetItem(groups[key], [record['source'].get('library') or record['operation'],
                attempt['outcome'].capitalize() if attempt else 'No attempts', timestamp(attempt) if attempt else '', ', '.join(flags)])
            row.setData(0, Qt.ItemDataRole.UserRole, record['id'])
            if identity == record['id']: self.tree.setCurrentItem(row)
        self.tree.expandAll(); self.tree.resizeColumnToContents(0)
        item = self.tree.currentItem()
        self.details_button.setEnabled(bool(item and item.data(0, Qt.ItemDataRole.UserRole)))
        self.notice.setText(self.panel.error.text() or 'Select an operation to inspect all attempts. No work resumes automatically.')

    def open_item(self, item, *_):
        if item and item.data(0, Qt.ItemDataRole.UserRole): self.panel.show_details(item.data(0, Qt.ItemDataRole.UserRole))


class ActivityPanel(QWidget):
    def __init__(self, bridge, parent=None, open_activity=None):
        super().__init__(parent)
        self.bridge = bridge; self.records = []; self.history = None; self.details = []
        self.controller = None
        self.summary_dismissed = False
        self.open_activity = open_activity or (lambda: None)
        layout = QVBoxLayout(self)
        self.startup = QWidget(); start = QVBoxLayout(self.startup)
        self.startup_label = QLabel(); self.startup_label.setWordWrap(True); start.addWidget(self.startup_label)
        actions = QHBoxLayout()
        for label, callback in [('Open Activity', self.expand), ('View recovery list', lambda: self.show_history(True)), ('Hide startup summary', self.dismiss_summary)]:
            button = QPushButton(label); button.clicked.connect(callback); actions.addWidget(button)
        start.addLayout(actions); layout.addWidget(self.startup)
        self.toggle = QPushButton('Activity'); self.toggle.setCheckable(True); self.toggle.setChecked(True)
        layout.addWidget(self.toggle)
        self.body = QWidget(); body = QVBoxLayout(self.body); layout.addWidget(self.body)
        self.toggle.toggled.connect(self.body.setVisible)
        self.counts = QLabel(); self.counts.setWordWrap(True); body.addWidget(self.counts)
        self.error = QLabel(); self.error.setWordWrap(True); body.addWidget(self.error)
        self.tree = QTreeWidget(); self.tree.setHeaderLabels(['Module / Operation', 'Result', 'Time'])
        self.tree.itemActivated.connect(self.open_item); body.addWidget(self.tree)
        detail = QPushButton('Open activity details'); detail.clicked.connect(lambda: self.open_item(self.tree.currentItem())); body.addWidget(detail)
        history = QPushButton('Open full activity history'); history.clicked.connect(lambda: self.show_history()); body.addWidget(history)
        self.timer = QTimer(self); self.timer.setSingleShot(True); self.timer.timeout.connect(self.refresh)
        bridge.listeners.append(self.schedule_refresh)
        self.refresh()

    def schedule_refresh(self):
        self.timer.start(0)

    def expand(self):
        self.open_activity(); self.toggle.setChecked(True); self.tree.setFocus()

    def dismiss_summary(self):
        self.summary_dismissed = True; self.startup.hide()

    def refresh(self):
        previous_error = self.bridge.last_error
        records = self.bridge.invoke('records')
        self.error.setText(self.bridge.last_error or previous_error or '')
        if records is not None: self.records = records
        current = [r for r in self.records if active(r)]
        pending = sum(bool(r['pending'] or r.get('deletion')) for r in current); recovery = sum(r['recovery'] for r in current)
        failed = sum(bool(r['attempts'] and r['attempts'][-1]['outcome'] == 'failure') for r in current)
        counts = f'{len(current)} operations needing attention · {pending} pending · {failed} failed · {recovery} requiring recovery'
        self.counts.setText(counts + '\nIndicators may overlap; each operation is counted once in the total.')
        self.startup_label.setText('Recovery summary: ' + counts + '. Review before resuming; nothing resumes automatically.')
        self.startup.setVisible(bool(current) and not self.summary_dismissed)
        self.tree.clear(); groups = {}
        for record in self.records:
            key = (record['module'], record['operation'])
            group = groups.setdefault(key, {'latest': {}, 'active': []})
            if active(record): group['active'].append(record)
            for attempt in record['attempts']:
                outcome = attempt['outcome']
                if outcome not in ('success', 'failure'): continue
                old = group['latest'].get(outcome)
                if not old or (attempt['time'] or '') > (old[1]['time'] or ''):
                    group['latest'][outcome] = (record, attempt)
        for key, group in sorted(groups.items()):
            root = QTreeWidgetItem(self.tree, [f'{key[0]} / {key[1]}'])
            for outcome, (record, attempt) in group['latest'].items():
                row = QTreeWidgetItem(root, ['Last ' + outcome, 'View details', timestamp(attempt)])
                row.setData(0, Qt.ItemDataRole.UserRole, (record['id'], attempt['id']))
            for record in group['active']:
                attempt = record['attempts'][-1] if record['attempts'] else None
                row = QTreeWidgetItem(root, ['Needs attention', attempt['outcome'].capitalize() if attempt else 'Pending', timestamp(attempt) if attempt else ''])
                row.setData(0, Qt.ItemDataRole.UserRole, (record['id'], None))
        self.tree.expandAll(); self.tree.resizeColumnToContents(0)
        if self.history: self.history.refresh()
        for dialog in self.details:
            if hasattr(dialog, 'actions'):
                record = next((r for r in self.records if r['id']==dialog.record_id), None)
                for action, button in dialog.actions.items():
                    button.setEnabled(bool(record) and (not (record['pending'] or record['recovery']) if action=='delete' else bool(record['pending'] or record['recovery']) and record['source'].get('kind') in ('import','bulk','recovery','metadata') if action=='discard' else not record.get('deletion')))

    def open_item(self, item, *_):
        data = item.data(0, Qt.ItemDataRole.UserRole) if item else None
        if data: self.show_details(*data)

    def show_details(self, identity, attempt_id=None):
        record = next((r for r in self.records if r['id'] == identity), None)
        if record:
            dialog = ActivityDetails(record, self, attempt_id); self.details.append(dialog)
            dialog.finished.connect(lambda: self.details.remove(dialog))
            dialog.show()

    def show_history(self, recovery_only=False):
        if self.history is None: self.history = ActivityHistory(self, recovery_only)
        else: self.history.recovery_only.setChecked(recovery_only); self.history.refresh()
        self.history.show(); self.history.raise_()
