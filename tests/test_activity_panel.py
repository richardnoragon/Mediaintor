import tempfile
import unittest
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from mediainator.activity import ActivityStore, ActivityBridge
from mediainator.activity_panel import ActivityPanel, ActivityDetails
from mediainator.import_store import atomic_json

APP = QApplication.instance() or QApplication([])


class ActivityPanelTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.store = ActivityStore(Path(self.temp.name), 'person', 'device')
        self.bridge = ActivityBridge(self.store, lambda message: None)
        self.panel = ActivityPanel(self.bridge); self.panel.show()
        self.addCleanup(self.panel.close)

    def test_counts_live_updates_and_collapse(self):
        self.bridge.record('Metadata saves', 'one', outcome='failure', pending=True, recovery=True)
        APP.processEvents()
        self.assertIn('1 operations', self.panel.counts.text())
        self.assertIn('1 pending · 1 failed · 1 requiring recovery', self.panel.counts.text())
        self.assertTrue(self.panel.body.isVisible())
        self.panel.toggle.click(); self.assertFalse(self.panel.body.isVisible())
        self.panel.expand(); self.assertTrue(self.panel.body.isVisible())

    def test_summary_dismissal_preserves_work_and_does_not_reopen(self):
        self.bridge.record('Imports', 'one', outcome='interrupted', pending=True)
        APP.processEvents(); self.assertTrue(self.panel.startup.isVisible())
        self.panel.dismiss_summary()
        self.bridge.record('Imports', 'two', outcome='failure', pending=True)
        APP.processEvents(); self.assertFalse(self.panel.startup.isVisible())
        self.assertEqual(self.store.summary()['total'], 2)
        other = ActivityPanel(self.bridge); other.show(); self.addCleanup(other.close)
        self.assertTrue(other.startup.isVisible())

    def test_latest_links_preserve_failure_across_success_and_interruption(self):
        for outcome in ('failure', 'success', 'interrupted'):
            self.bridge.record('Bulk edits', 'one', outcome=outcome, pending=True)
        APP.processEvents()
        root = self.panel.tree.topLevelItem(0)
        labels = [root.child(i).text(0) for i in range(root.childCount())]
        self.assertIn('Last failure', labels); self.assertIn('Last success', labels)
        self.panel.open_item(root.child(0))
        self.assertIn('Selected attempt', self.panel.details[0].content.toPlainText())
        self.panel.details[0].close()

    def test_full_history_includes_resolved_and_dismissed_and_filters(self):
        self.store.record('Imports', 'ok', outcome='success')
        self.store.record('Imports', 'pending', outcome='interrupted', pending=True)
        data = self.store._read()
        next(r for r in data['operations'].values() if r['pending'])['dismissed'] = True
        atomic_json(self.store.path, data)
        self.panel.refresh(); self.panel.show_history()
        history = self.panel.history
        self.assertEqual(history.tree.topLevelItem(0).childCount(), 2)
        history.show_dismissed.setChecked(False)
        self.assertEqual(history.tree.topLevelItem(0).childCount(), 1)
        history.show_dismissed.setChecked(True); history.recovery_only.setChecked(True)
        self.assertEqual(history.tree.topLevelItem(0).childCount(), 1)
        history.close()

    def test_history_and_details_never_change_records(self):
        self.bridge.record('Imports', 'one', outcome='failure', pending=True,
            source={'kind': 'import', 'library': '/disposable'},
            details={'completed': 3, 'pending': 7, 'items': [{'title': '<Book>', 'error': 'Unreadable'}]})
        APP.processEvents(); before = self.store.path.read_bytes()
        self.panel.show_history(True)
        dialog = ActivityDetails(self.store.records()[0]); self.addCleanup(dialog.close)
        text = dialog.content.toPlainText()
        for expected in ('Completed: 3', 'Pending: 7', '<Book>', 'Unreadable', '/disposable', 'Next steps'):
            self.assertIn(expected, text)
        self.assertEqual(before, self.store.path.read_bytes())
        self.panel.history.close()

    def test_storage_corruption_visible_without_destroying_history(self):
        self.store.folder.mkdir(parents=True, exist_ok=True); self.store.path.write_text('broken')
        self.panel.refresh()
        self.assertIn('could not be saved/read', self.panel.error.text())
        self.assertEqual(self.store.path.read_text(), 'broken')

    def test_hub_summary_visible_above_selected_bookinator_tab(self):
        from mediainator.settings import SettingsStore
        from mediainator.window import Hub
        settings = SettingsStore(Path(self.temp.name)/'settings.json'); state = settings.load()
        store = ActivityStore(Path(self.temp.name)/'data'/'Activity', state['profile_id'], state['device_id'])
        store.record('Imports', 'one', outcome='interrupted', pending=True)
        hub = Hub(settings, state); hub.show(); self.addCleanup(hub.close)
        APP.processEvents()
        self.assertIs(hub.tabs.currentWidget(), hub.bookinator)
        self.assertTrue(hub.activity_panel.startup.isVisible())
        self.assertIsNone(hub.bookinator.import_dialog)
        hub.activity_panel.expand()
        self.assertEqual(hub.tabs.currentIndex(), 0)

    def test_local_pending_journal_discovered_with_module_closed(self):
        from mediainator.settings import SettingsStore
        from mediainator.window import Hub
        from mediainator.import_store import ImportStore
        root = Path(self.temp.name); settings = SettingsStore(root/'settings.json'); state = settings.load()
        state['bookinator_open'] = False
        imports = ImportStore(root/'imports', root/'library')
        imports.create(dict(library_uuid='lib', items=[dict(source='book.epub', state='pending', operation_uuid='op')]))
        hub = Hub(settings, state, library=root/'library'); hub.show(); self.addCleanup(hub.close)
        APP.processEvents()
        self.assertIsNone(hub.bookinator)
        self.assertEqual(hub.activity.store.summary()['pending'], 1)
        self.assertTrue(hub.activity_panel.startup.isVisible())
