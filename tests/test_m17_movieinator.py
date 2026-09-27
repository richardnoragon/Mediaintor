"""M17 Movie-inator module: Qt integration with the Hub (requires PyQt6)."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from PyQt6.QtWidgets import QApplication, QMessageBox

from mediainator.modules import MODULES, launch_module
from mediainator.movie_store import MovieStore
from mediainator.movie_ui import Movieinator
from mediainator.settings import SettingsError, SettingsStore, defaults, validate
from mediainator.window import Hub
from mediainator.workspace_ui import capture
from mediainator.workspaces import snapshot, WorkspaceError

APP = QApplication.instance() or QApplication([])
Q = QMessageBox.StandardButton


class MovieTabTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.state = defaults()
        self.store = MovieStore(root / 'Movies' / 'catalog.sqlite', self.state['profile_id'])
        self.media = root / 'media'; (self.media / 'Heat (1995)').mkdir(parents=True)
        for rel in ('Alien (1979).mkv', 'Alien (1979).mp4', 'Heat (1995)/movie.mkv'):
            (self.media / rel).write_bytes(b'v' * 5)
        self.tab = Movieinator(self.state, lambda: True, self.store)
        self.addCleanup(self.tab.deleteLater)

    def add_alien(self):
        self.tab.add_movie(); editor = self.tab.editor
        editor.title.setText('Alien'); editor.year.setText('1979'); editor.directors.setPlainText('Ridley Scott')
        editor.edition_format.setCurrentText('Blu-ray'); editor.edition_location.setText('Shelf A')
        self.assertTrue(editor.save_changes(), editor.status.text())
        return editor

    def test_sample_mode_is_read_only(self):
        sample = Movieinator(defaults(), lambda: True); self.addCleanup(sample.deleteLater)
        self.assertEqual(len(sample.visible), 3)
        self.assertFalse(sample.add_button.isEnabled()); self.assertFalse(sample.import_button.isEnabled())

    def test_add_edit_review_and_personal_status(self):
        editor = self.add_alien()
        movie = self.tab.current()
        self.assertEqual((movie.title, movie.year, movie.editions[0].format), ('Alien', 1979, 'Blu-ray'))
        editor.year.setText('19x9')
        self.assertFalse(editor.save_changes())
        self.assertTrue(editor.dirty())
        with patch('mediainator.movie_ui.QMessageBox.question', return_value=Q.Cancel):
            self.assertFalse(self.tab.review_close())
        with patch('mediainator.movie_ui.QMessageBox.question', return_value=Q.Discard):
            self.assertTrue(self.tab.review_close())
        self.assertFalse(editor.dirty())
        self.tab.watched.setChecked(True); self.tab.rating.setCurrentIndex(8)
        self.assertEqual((self.store.get(movie.id).watched, self.store.get(movie.id).rating), (True, 8))
        self.assertEqual(self.store.get(movie.id).revision, 0)

    def test_save_button_validates_and_saves_existing_movie(self):
        editor = self.add_alien()
        movie_id = editor.movie.id
        editor.year.setText('19x9')
        editor.save_button.click()
        self.assertIn('Not saved:', editor.status.text())
        self.assertEqual(editor.year.text(), '19x9')
        self.assertTrue(editor.dirty())
        self.assertEqual(self.store.get(movie_id).year, 1979)
        editor.year.setText('1980')
        editor.save_button.click()
        self.assertEqual(editor.status.text(), 'Saved.')
        self.assertEqual(self.store.get(movie_id).year, 1980)
        self.assertFalse(editor.dirty())

    def test_list_rating_updates_and_survives_reload(self):
        from PyQt6.QtCore import Qt
        from mediainator.movie_ui import COLUMNS
        self.add_alien()
        self.tab.view.setCurrentText('List')
        model = self.tab.table.model()
        column = COLUMNS.index('Rating')
        self.assertEqual(model.headerData(column, Qt.Orientation.Horizontal), 'Rating')
        self.assertEqual(model.data(model.index(0, column)), 'No rating')
        self.tab.rating.setCurrentIndex(8)
        self.assertEqual(model.data(model.index(0, column)), '8/10')
        self.tab.reload()
        self.assertEqual(model.data(model.index(0, column)), '8/10')
        self.tab.rating.setCurrentIndex(0)
        self.assertEqual(model.data(model.index(0, column)), 'No rating')

    def test_search_filters_and_view_persist_in_state(self):
        self.add_alien()
        self.tab.search.setText('ridley'); self.assertEqual(len(self.tab.visible), 1)
        self.tab.search.setText('zzz'); self.assertEqual(self.tab.visible, [])
        self.tab.clear_search_filters(); self.assertEqual(self.state['movie_search']['text'], '')
        self.tab.view.setCurrentText('List'); self.assertEqual(self.state['movie_view'], 'List')
        validate(self.state)

    def test_import_preview_groups_and_attaches(self):
        self.add_alien()
        dialog = self.tab.open_import([str(self.media)])
        dialog.build_preview()
        dialog.thread.wait(10000) if dialog.thread else None
        for _ in range(50):
            APP.processEvents()
            if dialog.result is not None: break
        self.assertIsNotNone(dialog.result, dialog.status.text())
        top = [dialog.tree.topLevelItem(i) for i in range(dialog.tree.topLevelItemCount())]
        self.assertEqual([t.text(1) for t in top], ['Alien', 'Heat'])
        self.assertEqual(dialog.tree.itemWidget(top[0], 3).currentData(), self.tab.current().id)
        dialog.apply()
        alien = next(m for m in self.tab.movies if m.title == 'Alien')
        self.assertEqual((len(alien.editions), len(alien.files)), (3, 2))
        self.assertTrue(all((self.media / rel).exists() for rel in ('Alien (1979).mkv', 'Heat (1995)/movie.mkv')))

    def test_remove_keeps_files(self):
        self.add_alien(); self.tab.editor.close()
        movie_id = self.store.add_movie(dict(title='Heat', year=1995),
                                        [dict(label='MKV', copies=[dict(kind='file', path=str(self.media / 'Heat (1995)/movie.mkv'))])])
        self.tab.reload(); self.state['selected_movie'] = movie_id; self.tab.render()
        with patch('mediainator.movie_ui.QMessageBox.question', return_value=Q.Yes):
            self.tab.remove_movie()
        self.assertTrue((self.media / 'Heat (1995)/movie.mkv').exists())
        self.assertEqual([m.title for m in self.tab.movies], ['Alien'])


class HubIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.settings = SettingsStore(Path(self.tmp.name) / 'settings.json')
        self.state = defaults(); self.state['bookinator_open'] = False
        self.catalog = Path(self.tmp.name) / 'movies.sqlite'

    def hub(self):
        hub = Hub(self.settings, self.state, app_data=Path(self.tmp.name) / 'data', movie_catalog=self.catalog)
        self.addCleanup(hub.deleteLater)
        return hub

    def test_registry_launch_focus_and_close(self):
        self.assertTrue(next(m for m in MODULES if m.id == 'movieinator').available)
        hub = self.hub()
        self.assertTrue(hub.module_tiles['movieinator'].isEnabled())
        self.assertTrue(launch_module('movieinator', hub)); first = hub.movieinator
        self.assertTrue(launch_module('movieinator', hub))
        self.assertIs(hub.movieinator, first); self.assertEqual(hub.tabs.count(), 2)
        self.assertIs(hub.tabs.currentWidget(), first)
        self.assertTrue(self.settings.load()['movieinator_open'])
        launch_module('bookinator', hub); self.assertEqual(hub.tabs.count(), 3)
        hub.close_tab(hub.tabs.indexOf(hub.movieinator))
        self.assertIsNone(hub.movieinator); self.assertIsNotNone(hub.bookinator)
        self.assertFalse(self.settings.load()['movieinator_open'])
        hub.close_tab(hub.tabs.indexOf(hub.bookinator)); self.assertEqual(hub.tabs.count(), 1)

    def test_reopen_on_restart_and_workspace_snapshot(self):
        hub = self.hub(); hub.open_movies()
        movie_id = hub.movieinator.store.add_movie(dict(title='Alien', year=1979)); hub.movieinator.reload()
        self.state['selected_movie'] = movie_id; hub.movieinator.render()
        value = capture(hub, allow_busy=True)
        self.assertEqual((value['modules'], value['active']), (['hub', 'movieinator'], 'movieinator'))
        self.assertEqual(value['movie_selection']['movie_id'], movie_id)
        snapshot(value)
        with self.assertRaises(WorkspaceError):
            snapshot(dict(value, modules=['hub'], active='hub'))
        hub.close()
        again = Hub(self.settings, self.settings.load(), app_data=Path(self.tmp.name) / 'data', movie_catalog=self.catalog)
        self.addCleanup(again.deleteLater)
        self.assertIsNotNone(again.movieinator)
        self.assertEqual(again.movieinator.current().title, 'Alien')

    def test_hub_close_reviews_unsaved_movie_edits(self):
        hub = self.hub(); hub.open_movies(); hub.movieinator.add_movie()
        hub.movieinator.editor.title.setText('Draft')
        with patch('mediainator.movie_ui.QMessageBox.question', return_value=Q.Cancel):
            self.assertFalse(hub.review_close())
        with patch('mediainator.movie_ui.QMessageBox.question', return_value=Q.Save):
            self.assertTrue(hub.review_close())
        self.assertEqual([m.title for m in hub.movieinator.store.load()], ['Draft'])

    def test_sample_hub_without_catalog_is_read_only(self):
        hub = Hub(self.settings, self.state, app_data=Path(self.tmp.name) / 'data'); self.addCleanup(hub.deleteLater)
        hub.open_movies()
        self.assertIsNone(hub.movieinator.store)
        self.assertFalse((Path(self.tmp.name) / 'data' / 'Movies').exists())

    def test_settings_validation(self):
        good = dict(defaults(), movieinator_open=True, movie_view='List', selected_movie=str(uuid4()), movie_player='mpv',
                    movie_search=dict(text='x', genres=['Horror'], formats=[], statuses=['Watched'], expanded=False, sort='Title A–Z'))
        validate(good)
        for bad in (dict(movieinator_open='yes'), dict(movie_view='Cards'), dict(selected_movie=5),
                    dict(movie_player=None), dict(movie_search=dict(genres='Horror'))):
            with self.subTest(bad=bad), self.assertRaises(SettingsError):
                validate(dict(defaults(), **bad))


if __name__ == '__main__':
    unittest.main()
