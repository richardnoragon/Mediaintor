"""M19 Paper-inator module: Qt integration with the Hub (requires PyQt6)."""
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QApplication, QDialog, QMessageBox, QTableWidgetSelectionRange

from mediainator.modules import MODULES, launch_module
from mediainator.paper_store import PaperStore
from mediainator.paper_ui import (ConnectionDialog, ContainerDialog, FileChoiceDialog, MetadataReviewDialog,
                                  OrganizeDialog, Paperinator, VersionFieldsDialog)
from mediainator.settings import SettingsError, SettingsStore, defaults, validate
from mediainator.window import Hub
from mediainator.workspace_ui import capture
from mediainator.workspaces import MODULE_SETS, WorkspaceError, snapshot

APP = QApplication.instance() or QApplication([])
Q = QMessageBox.StandardButton
ACCEPTED = QDialog.DialogCode.Accepted


class FakeOpener:
    def __init__(self):
        self.opened = []

    def open(self, command, path):
        self.opened.append((command, path))


class FakeTool:
    def __init__(self, table=None, default=''):
        self.table, self.default = table or {}, default

    def available(self):
        return True

    def extract(self, path):
        value = self.table.get(Path(path).name, self.default)
        return dict(value) if isinstance(value, dict) else value


def pdf(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def click(label):
    """Patch for QMessageBox.exec on custom-button boxes: click the button with this text."""
    def run(box):
        button = box.button(Q.Cancel) if label == 'Cancel' else next(
            b for b in box.buttons() if b.text().replace('&', '') == label)
        button.click()
        return 0
    return run


class PaperTabTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.state = defaults()
        self.store = PaperStore(self.root / 'Paper' / 'profiles' / self.state['profile_id'], self.state['profile_id'])
        self.docs = self.root / 'docs'
        self.opener = FakeOpener()
        self.tab = Paperinator(self.state, lambda: True, self.store, opener=self.opener)
        self.addCleanup(self.tab.deleteLater)

    def add(self, title, **fields):
        item_id = self.store.add_item(dict(title=title, **fields)); self.tab.reload()
        return item_id

    def select(self, *ids):
        rows = [i for i, item in enumerate(self.tab.visible) if item.id in ids]
        self.tab.table.clearSelection()
        for row in rows:
            self.tab.table.setRangeSelected(QTableWidgetSelectionRange(row, 0, row, 7), True)

    def test_sample_mode_is_read_only(self):
        tab = Paperinator(defaults(), lambda: True, None); self.addCleanup(tab.deleteLater)
        self.assertFalse(tab.add_button.isEnabled()); self.assertFalse(tab.import_button.isEnabled())
        self.assertEqual(len(tab.visible), 3)
        self.assertIsNone(tab.add_item()); self.assertIsNone(tab.new_note())
        self.assertIn('Read-only', tab.note.text())

    def test_empty_library_starts_on_home_and_creates_profile_library(self):
        self.assertTrue(self.store.path.is_file())
        self.assertEqual(self.tab.pages.currentIndex(), 0)
        self.assertIn('importing a PDF', self.tab.home_hint.text())
        self.assertIn('empty', self.tab.count.text())

    def test_add_edit_validation_and_conflict(self):
        editor = self.tab.add_item()
        editor.title.setText('Attention Is All You Need'); editor.authors.setPlainText('Ashish Vaswani\nNoam Shazeer')
        editor.year.setText('2017'); editor.doi.setText('not-a-doi')
        self.assertFalse(editor.save_changes())
        self.assertIn('Not saved', editor.status.text()); self.assertEqual(editor.title.text(), 'Attention Is All You Need')
        editor.doi.setText('https://doi.org/10.48550/arXiv.1706.03762')
        self.assertTrue(editor.save_changes(), editor.status.text())
        item = self.tab.library.items[0]
        self.assertEqual((item.doi, item.handling, item.authors[1]), ('10.48550/arxiv.1706.03762', 'Inbox', 'Noam Shazeer'))
        self.store.update_item(item.id, item.revision, dict(venue='NeurIPS'))        # changed elsewhere
        editor.tags.setText('transformers')
        with patch.object(QMessageBox, 'exec', click('Save my values')):
            self.assertTrue(editor.save_changes())
        saved = self.store.get_item(item.id)
        self.assertEqual((saved.venue, saved.tags), ('NeurIPS', ('transformers',)))    # other change kept

    def test_quick_states_apply_to_selection_and_stay_independent(self):
        a = self.add('Paper A'); b = self.add('Paper B'); c = self.add('Paper C')
        self.select(a, b)
        self.assertIn('2 items selected', self.tab.selection_label.text())
        self.tab.reading.setCurrentText('Read')
        lib = self.store.load()
        self.assertEqual([lib.item(x).reading for x in (a, b, c)], ['Read', 'Read', 'Unread'])
        self.assertEqual(sorted(self.tab.selected_ids()), sorted([a, b]))          # selection survives the reload
        self.tab.flag_boxes['Favorite'].setChecked(True)
        self.assertTrue(all(self.store.get_item(x).favorite for x in (a, b)))
        self.select(a)
        self.tab.handling.setCurrentText('Archived'); self.tab.flag_boxes['Key Reference'].setChecked(True)
        item = self.store.get_item(a)
        self.assertEqual((item.reading, item.handling, item.flags), ('Read', 'Archived', ('Key Reference', 'Favorite')))

    def test_search_filters_saved_searches_and_document_text(self):
        a = self.add('Graph neural networks', tags=['ml']); self.add('Protein folding')
        doc = pdf(self.docs / 'x.pdf', b'x')
        b = self.store.import_document(doc, 'referenced', item_fields=dict(title='Opaque title'), text='mitochondria energy')[0]
        self.tab.reload()
        self.tab.search.setText('mitochondria')
        self.assertEqual([i.id for i in self.tab.visible], [b])
        self.assertEqual(self.state['paper_search']['text'], 'mitochondria')
        self.tab.clear_search_filters()
        menu = self.tab.filter_buttons['tags'][1]
        next(action for action in menu.actions() if action.text() == 'ml').setChecked(True)
        self.assertEqual([i.id for i in self.tab.visible], [a])
        self.assertEqual(self.state['paper_search']['tags'], ['ml'])
        with patch('mediainator.paper_ui.QInputDialog.getText', return_value=('ML papers', True)):
            self.tab.save_search()
        self.assertEqual([s.name for s in self.tab.library.searches], ['ML papers'])
        self.tab.clear_search_filters()
        self.assertEqual(len(self.tab.visible), 3)
        self.tab.saved_combo.setCurrentIndex(self.tab.saved_combo.findText('ML papers'))
        self.assertEqual([i.id for i in self.tab.visible], [a])
        self.tab.sort.setCurrentText('Title A–Z'); self.tab.update_search()
        self.assertEqual(self.tab.library.searches[0].criteria['sort'], 'Title A–Z')
        with patch('mediainator.paper_ui.QMessageBox.question', return_value=Q.Yes):
            self.tab.delete_search()
        self.assertEqual(self.tab.library.searches, ())
        self.tab.search.setText('no such thing')
        self.assertIn('No items match', self.tab.count.text())

    def test_notes_links_navigation_and_markdown_export(self):
        item_id = self.add('Source paper')
        editor = self.tab.new_note()
        editor.title.setText('Key idea'); editor.editor.setPlainText('Builds on ')
        with patch('mediainator.paper_ui.QInputDialog.getItem', return_value=('Item: Source paper', True)):
            editor.insert_link()
        editor.kind_box.setCurrentText('Finding')
        self.assertTrue(editor.dirty())
        self.assertTrue(editor.save_changes(), editor.status.text())
        note = self.tab.library.notes[0]
        self.assertEqual((note.kind, note.links(), note.item_id), ('Finding', [('item', item_id)], None))
        self.assertIn(f'paper:item/{item_id}', self.tab.note_view.toHtml())
        self.tab.link_clicked(QUrl(f'paper:item/{item_id}'))
        self.assertEqual((self.tab.pages.currentIndex(), self.state['selected_paper']), (1, item_id))
        folder = self.root / 'export'; folder.mkdir(); (folder / 'Key idea.md').write_text('keep me')
        written = self.tab.write_exports([note], folder)
        self.assertEqual([p.name for p in written], ['Key idea (2).md'])
        self.assertEqual((folder / 'Key idea.md').read_text(), 'keep me')
        self.assertIn('→ Source paper · paper:item/', written[0].read_text())
        second = self.tab.new_note(item_id=item_id)
        second.editor.setPlainText('draft')
        with patch('mediainator.paper_ui.QMessageBox.question', return_value=Q.Cancel):
            self.assertFalse(self.tab.review_close())
        with patch('mediainator.paper_ui.QMessageBox.question', return_value=Q.Save):
            self.assertTrue(self.tab.review_close())
        self.assertEqual(self.store.load().notes_of(item_id)[0].kind, 'Summary')

    def test_projects_organize_and_membership(self):
        a = self.add('A'); b = self.add('B')
        def fill(dialog):
            dialog.name.setText('Thesis chapter 2'); return ACCEPTED
        with patch.object(ContainerDialog, 'exec', fill):
            project = self.tab.new_container('project')
        self.select(a, b)
        def organize(dialog):
            dialog.add_tags.setText('chapter2'); dialog.container.setCurrentIndex(dialog.container.findData(project))
            dialog.flags['Needs Review'].setCurrentText('Set')
            return ACCEPTED
        with patch.object(OrganizeDialog, 'exec', organize):
            self.tab.organize_selected()
        lib = self.store.load()
        self.assertEqual(set(lib.container(project).item_ids), {a, b})
        self.assertEqual([lib.item(x).tags for x in (a, b)], [('chapter2',), ('chapter2',)])
        self.assertTrue(all(lib.item(x).needs_review for x in (a, b)))
        self.assertEqual([lib.item(x).reading for x in (a, b)], ['Unread', 'Unread'])          # untouched
        self.tab.go('Projects')
        self.tab.state['selected_paper_project'] = project; self.tab.render_containers()
        self.assertEqual(self.tab.member_list.count(), 2)
        self.tab.member_list.item(0).setSelected(True)
        self.tab.remove_members()
        self.assertEqual(len(self.store.load().container(project).members), 1)
        self.assertEqual(len(self.store.load().items), 2)                                     # still in the library
        self.tab.show_container_items()
        self.assertEqual((self.tab.pages.currentIndex(), len(self.tab.visible)), (1, 1))
        self.assertEqual(self.tab.home_lists['projects'].count(), 1)

    def test_connections_dialog(self):
        a = self.add('Method paper'); b = self.add('Application paper')
        def connect(dialog):
            dialog.relation.setCurrentText('Uses'); dialog.direction.setCurrentIndex(1)
            dialog.targets.setCurrentRow(0); dialog.comment.setText('applies the method')
            self.assertIn('uses', dialog.explain.text())
            return ACCEPTED
        with patch.object(ConnectionDialog, 'exec', connect):
            self.tab.connect_object('item', a)
        connection = self.store.load().connections[0]
        self.assertEqual((connection.source_id, connection.relation, connection.target_id), (b, 'Uses', a))
        self.state['selected_paper'] = a; self.tab.render()
        self.assertIn('Used by', self.tab.detail.toPlainText())
        def remove(dialog):
            dialog.existing.setCurrentRow(0)
            with patch('mediainator.paper_ui.QMessageBox.question', return_value=Q.Yes):
                dialog.remove_selected()
            return ACCEPTED
        with patch.object(ConnectionDialog, 'exec', remove):
            self.tab.connect_object('item', a)
        self.assertEqual(self.store.load().connections, ())

    def test_trash_restore_and_permanent_deletion(self):
        original = pdf(self.docs / 'managed.pdf', b'managed')
        item_id = self.store.import_document(original, 'managed', item_fields=dict(title='Doomed'))[0]
        self.store.add_note(dict(title='Its note', item_id=item_id))
        self.tab.reload()
        copy = Path(self.store.get_item(item_id).files[0].path)
        self.select(item_id)
        with patch.object(QMessageBox, 'exec', lambda box: Q.Cancel):
            self.tab.trash_selected()
        self.assertEqual(len(self.store.load().items), 1)
        with patch.object(QMessageBox, 'exec', lambda box: Q.Yes):
            self.tab.trash_selected()
        self.assertEqual((self.tab.library.items, self.tab.library.notes), ((), ()))
        self.assertEqual(self.tab.trash_list.count(), 1)
        self.tab.trash_list.setCurrentRow(0)
        self.assertIn('managed cop', self.tab.trash_detail.text())
        self.tab.restore_trash()
        self.assertEqual(len(self.tab.library.notes), 1)
        self.select(item_id)
        with patch.object(QMessageBox, 'exec', lambda box: Q.Yes):
            self.tab.trash_selected()
        self.tab.trash_list.setCurrentRow(0)
        with patch.object(QMessageBox, 'exec', click('Cancel')):
            self.tab.purge_trash()
        self.assertTrue(copy.exists())
        with patch.object(QMessageBox, 'exec', click('Delete permanently')):
            self.tab.purge_trash()
        self.assertFalse(copy.exists()); self.assertTrue(original.exists())
        self.assertEqual(self.store.load().trash, ())

    def test_import_preview_requires_choice_and_groups_versions(self):
        existing = self.add('Deep learning survey of methods')
        dup_source = pdf(self.docs / 'known.pdf', b'known')
        self.store.import_document(dup_source, 'referenced', item_id=existing)
        self.tab.reload()
        pdf(self.docs / 'in' / 'deep_learning_survey_of_methods.pdf', b'v2')
        pdf(self.docs / 'in' / 'copy of known.pdf', b'known')
        pdf(self.docs / 'in' / 'fresh.pdf', b'fresh')
        info = FakeTool({'fresh.pdf': dict(Title='A Fresh Result', Author='Ada Lovelace')}, default={})
        text = FakeTool({'fresh.pdf': 'Intro\nDOI 10.5555/fresh.1\fmore', 'deep_learning_survey_of_methods.pdf': 'words'})
        dialog = self.tab.open_import([str(self.docs / 'in')])
        with patch('mediainator.paper_import.PdfInfoExtractor', lambda: info), \
                patch('mediainator.paper_import.PdfTextExtractor', lambda: text):
            dialog.build_preview()
            deadline = time.monotonic() + 10
            while dialog.busy() and time.monotonic() < deadline:
                APP.processEvents()
                time.sleep(0.01)
        self.assertFalse(dialog.busy())
        self.assertEqual(dialog.tree.topLevelItemCount(), 3)
        self.assertFalse(dialog.confirm.isEnabled())                 # file handling must be chosen explicitly
        rows = {dialog.tree.topLevelItem(i).text(1): dialog.tree.topLevelItem(i) for i in range(3)}
        known = next(r for t, r in rows.items() if t.startswith('copy of known'))
        self.assertEqual(dialog.tree.itemWidget(known, 5).currentData(), 'skip')
        version = rows['deep learning survey of methods']
        box = dialog.tree.itemWidget(version, 5)
        self.assertIn('Add as new version of', box.itemText(1))
        box.setCurrentIndex(1)
        dialog.managed.setChecked(True)
        self.assertTrue(dialog.confirm.isEnabled())
        dialog.apply()
        deadline = time.monotonic() + 10
        while dialog.busy() and time.monotonic() < deadline:
            APP.processEvents()
            time.sleep(0.01)
        self.assertFalse(dialog.busy())
        lib = self.store.load()
        fresh = next(i for i in lib.items if i.title == 'A Fresh Result')
        self.assertEqual((fresh.authors, fresh.doi, fresh.handling, fresh.needs_review), (('Ada Lovelace',), '10.5555/fresh.1', 'Inbox', True))
        self.assertEqual(fresh.files[0].mode, 'managed')
        self.assertEqual((self.docs / 'in' / 'fresh.pdf').read_bytes(), b'fresh')              # original untouched
        self.assertEqual(len(lib.item(existing).versions), 2)
        self.assertEqual(len(lib.items), 2)
        self.assertIn('2 document(s) imported', dialog.status.text())

    def test_versions_files_open_and_locate(self):
        item_id = self.add('Work')
        self.select(item_id)
        dialog = self.tab.open_versions()
        def version(d):
            d.label.setText('arXiv v1'); d.kind.setCurrentText('Preprint'); return ACCEPTED
        with patch.object(VersionFieldsDialog, 'exec', version):
            dialog.add_version()
        dialog.tree.setCurrentItem(dialog.tree.topLevelItem(0))
        document = pdf(self.docs / 'pre.pdf', b'pre')
        def choose(d):
            d.referenced.setChecked(True); return ACCEPTED
        with patch('mediainator.paper_ui.QFileDialog.getOpenFileName', return_value=(str(document), '')), \
                patch.object(FileChoiceDialog, 'exec', choose):
            dialog.add_file()
        item = self.store.get_item(item_id)
        self.assertEqual((item.preferred_version.label, item.default_document.mode), ('arXiv v1', 'referenced'))
        self.tab.open_selected()
        self.assertEqual(self.opener.opened, [('', str(document.resolve()))])
        self.assertTrue(self.store.get_item(item_id).opened_at)
        moved = self.docs / 'moved' / 'pre.pdf'; moved.parent.mkdir(); document.rename(moved)
        self.tab.reload(); self.select(item_id)
        with patch('mediainator.paper_ui.QMessageBox.question', return_value=Q.Yes), \
                patch('mediainator.paper_ui.QFileDialog.getOpenFileName', return_value=(str(moved), '')):
            self.tab.open_selected()
        self.assertEqual(self.store.get_item(item_id).default_document.path, str(moved.resolve()))

    def test_metadata_review_applies_checked_fields_only(self):
        document = pdf(self.docs / 'm.pdf', b'm')
        item_id = self.store.import_document(document, 'referenced', item_fields=dict(title='My own title'))[0]
        self.tab.reload()
        item = self.store.get_item(item_id)
        dialog = MetadataReviewDialog(self.tab, item, item.default_document,
                                      info_tool=FakeTool({'m.pdf': dict(Title='Official Title', Author='A. Author')}, default={}),
                                      text_tool=FakeTool({'m.pdf': 'doi:10.5555/m.1'}))
        self.addCleanup(dialog.deleteLater)
        self.assertEqual([p[0] for p in dialog.proposals], ['title', 'authors', 'doi'])
        self.assertEqual(sorted(dialog.chosen()), ['authors', 'doi'])       # existing title is not preselected
        dialog.accept()
        item = self.store.get_item(item_id)
        self.assertEqual((item.title, item.authors, item.doi), ('My own title', ('A. Author',), '10.5555/m.1'))

    def test_startup_view_preferences(self):
        state = dict(defaults(), paper_startup='Restore Last View', paper_view='Notes')
        tab = Paperinator(state, lambda: True, None); self.addCleanup(tab.deleteLater)
        self.assertEqual(tab.pages.currentIndex(), 2)
        state = dict(defaults(), paper_startup='Projects')
        tab = Paperinator(state, lambda: True, None); self.addCleanup(tab.deleteLater)
        self.assertEqual(tab.pages.currentIndex(), 3)
        self.tab.startup.setCurrentText('Library')
        self.assertEqual(self.state['paper_startup'], 'Library')


class HubIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.settings = SettingsStore(Path(self.tmp.name) / 'settings.json')
        self.state = defaults(); self.state['bookinator_open'] = False
        self.library = Path(self.tmp.name) / 'paper'

    def hub(self, state=None):
        hub = Hub(self.settings, state or self.state, app_data=Path(self.tmp.name) / 'data', paper_library=self.library,
                  music_catalog=Path(self.tmp.name) / 'music.sqlite', movie_catalog=Path(self.tmp.name) / 'movies.sqlite')
        self.addCleanup(hub.deleteLater)
        return hub

    def test_registry_launch_focus_close_and_profile_library(self):
        self.assertTrue(next(m for m in MODULES if m.id == 'paperinator').available)
        hub = self.hub()
        self.assertTrue(hub.module_tiles['paperinator'].isEnabled())
        self.assertTrue(launch_module('paperinator', hub)); first = hub.paperinator
        self.assertTrue(launch_module('paperinator', hub))
        self.assertIs(hub.paperinator, first); self.assertEqual(hub.tabs.count(), 2)
        self.assertEqual(first.store.root, self.library / 'profiles' / self.state['profile_id'])
        self.assertTrue(self.settings.load()['paperinator_open'])
        launch_module('musicinator', hub); launch_module('movieinator', hub)
        self.assertEqual(hub.tabs.count(), 4)
        hub.close_tab(hub.tabs.indexOf(hub.paperinator))
        self.assertIsNone(hub.paperinator); self.assertIsNotNone(hub.musicinator)
        self.assertFalse(self.settings.load()['paperinator_open'])

    def test_restart_reopen_and_workspace_snapshot(self):
        hub = self.hub(); hub.open_music(); hub.open_papers()
        item_id = hub.paperinator.store.add_item(dict(title='Kept')); hub.paperinator.reload()
        self.state['selected_paper'] = item_id; hub.paperinator.render()
        value = capture(hub, allow_busy=True)
        self.assertEqual((value['modules'], value['active']), (['hub', 'musicinator', 'paperinator'], 'paperinator'))
        self.assertEqual(value['paper_selection']['item_id'], item_id)
        snapshot(value)
        with self.assertRaises(WorkspaceError):
            snapshot(dict(value, modules=['hub', 'musicinator'], active='hub'))
        self.assertIn(['hub', 'bookinator', 'musicinator', 'movieinator', 'paperinator'], MODULE_SETS)
        self.assertIn(['hub', 'bookinator', 'musicinator', 'movieinator'], MODULE_SETS)      # M18 snapshots stay valid
        hub.close()
        again = self.hub(self.settings.load())
        self.assertIsNotNone(again.paperinator)
        self.assertEqual(again.paperinator.current().title, 'Kept')
        again.remove_papers()
        self.assertTrue(again.workspaces.restore(value))
        self.assertIsNotNone(again.paperinator)
        self.assertIs(again.tabs.currentWidget(), again.paperinator)
        self.assertEqual(again.state['selected_paper'], item_id)

    def test_hub_close_reviews_unsaved_drafts(self):
        hub = self.hub(); hub.open_papers(); editor = hub.paperinator.add_item()
        editor.title.setText('Draft paper')
        with patch('mediainator.paper_ui.QMessageBox.question', return_value=Q.Cancel):
            self.assertFalse(hub.review_close())
        self.assertTrue(hub.paperinator.unattended_close_blocked())
        with patch('mediainator.paper_ui.QMessageBox.question', return_value=Q.Save):
            self.assertTrue(hub.review_close())
        self.assertEqual([i.title for i in hub.paperinator.store.load().items], ['Draft paper'])
        self.assertFalse(hub.paperinator.unattended_close_blocked())

    def test_sample_hub_creates_nothing(self):
        hub = Hub(self.settings, self.state, app_data=Path(self.tmp.name) / 'data'); self.addCleanup(hub.deleteLater)
        hub.open_papers()
        self.assertIsNone(hub.paperinator.store)
        self.assertFalse((Path(self.tmp.name) / 'data' / 'Paper').exists())

    def test_other_profile_gets_its_own_library(self):
        hub = self.hub(); hub.open_papers()
        hub.paperinator.store.add_item(dict(title='Mine'))
        other_state = defaults(); other_state['bookinator_open'] = False
        other = Hub(SettingsStore(Path(self.tmp.name) / 'other.json'), other_state, app_data=Path(self.tmp.name) / 'data',
                    paper_library=self.library)
        self.addCleanup(other.deleteLater)
        other.open_papers()
        self.assertEqual(other.paperinator.library.items, ())
        self.assertNotEqual(other.paperinator.store.root, hub.paperinator.store.root)

    def test_settings_validation(self):
        good = dict(defaults(), paperinator_open=True, paper_startup='Library', paper_view='Trash', selected_paper=str(uuid4()),
                    paper_reader='okular', paper_search=dict(text='x', types=['Dataset'], reading=['Read'], handling=[],
                                                              flags=['Favorite'], tags=['ml'], container=None,
                                                              sort='Title A–Z', expanded=False))
        validate(good)
        for bad in (dict(paperinator_open='yes'), dict(paper_startup='Everything'), dict(paper_view='Graph'),
                    dict(selected_paper=5), dict(paper_reader=None), dict(paper_search=dict(tags='ml')),
                    dict(paper_search=dict(container=3))):
            with self.subTest(bad=bad), self.assertRaises(SettingsError):
                validate(dict(defaults(), **bad))

    def test_library_failure_is_recorded_and_retry_reloads(self):
        import sqlite3
        from mediainator.activity_panel import guidance
        folder = self.library / 'profiles' / self.state['profile_id']; folder.mkdir(parents=True)
        with sqlite3.connect(folder / 'library.sqlite') as db:
            db.execute('CREATE TABLE unrelated(x)')
        hub = self.hub(); hub.open_papers()
        self.assertTrue(hub.paperinator.load_error)
        self.assertFalse(hub.paperinator.add_button.isEnabled())
        record = next(r for r in hub.activity.invoke('records') if r['source'].get('kind') == 'paper_library')
        self.assertEqual((record['module'], record['pending']), ('paperinator', True))
        self.assertIn('Reload library in Paper-inator', guidance(record))
        (folder / 'library.sqlite').unlink()
        hub.activity_controller.review(record)
        self.assertEqual(hub.paperinator.load_error, '')
        self.assertTrue(hub.paperinator.add_button.isEnabled())


if __name__ == '__main__':
    unittest.main()
