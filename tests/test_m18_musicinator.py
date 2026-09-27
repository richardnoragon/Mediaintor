"""M18 Music-inator module: Qt integration with the Hub (requires PyQt6)."""
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QDialog, QMessageBox

from mediainator.modules import MODULES, launch_module
from mediainator.music_scan import ScanFile
from mediainator.music_store import MusicStore
from mediainator.music_ui import COLUMNS, EditionDialog, Musicinator
from mediainator.settings import SettingsError, SettingsStore, defaults, validate
from mediainator.window import Hub
from mediainator.workspace_ui import capture
from mediainator.workspaces import MODULE_SETS, WorkspaceError, snapshot

APP = QApplication.instance() or QApplication([])
Q = QMessageBox.StandardButton

TAGS = {
    'Pink Floyd - The Wall (1979)/CD1/01 - In the Flesh.flac': dict(album='The Wall', album_artist='Pink Floyd', title='In the Flesh?', track='1', disc='1', date='1979'),
    'Pink Floyd - The Wall (1979)/CD2/01 - Hey You.flac': dict(album='The Wall', album_artist='Pink Floyd', title='Hey You', track='1', disc='2', date='1979'),
    'Miles Davis - Kind of Blue (1959)/01 - So What.mp3': {},
    'Miles Davis - Kind of Blue (1959)/02 - Freddie Freeloader.mp3': {},
}


def fake_probe(path):
    rel = next((r for r in TAGS if path.endswith(r)), '')
    return ScanFile(path=path, size=5, container=Path(path).suffix[1:], codec=Path(path).suffix[1:], duration=180.0,
                    bit_depth=16 if path.endswith('.flac') else None, sample_rate=44100,
                    bitrate=None if path.endswith('.flac') else 320000, tags=dict(TAGS.get(rel, {})))


class MusicTabTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.state = defaults()
        self.store = MusicStore(root / 'Music' / 'catalog.sqlite', self.state['profile_id'])
        self.media = root / 'media'
        for rel in TAGS:
            path = self.media / rel; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(b'a' * 5)
        self.tab = Musicinator(self.state, lambda: True, self.store, playlist_folder=root / 'playlists')
        self.addCleanup(self.tab.deleteLater)

    def add_wall(self):
        self.tab.add_album(); editor = self.tab.editor
        editor.title.setText('The Wall'); editor.artist.setText('Pink Floyd'); editor.year.setText('1979')
        editor.additional.setPlainText('Bob Ezrin')
        editor.edition_format.setCurrentText('CD'); editor.edition_label.setText('Original CD'); editor.edition_location.setText('Shelf A')
        self.assertTrue(editor.save_changes(), editor.status.text())
        return editor

    def import_media(self):
        with patch('mediainator.music_scan.probe', fake_probe):
            dialog = self.tab.open_import([str(self.media)])
            dialog.build_preview()
            deadline = time.monotonic() + 10
            while dialog.busy() and time.monotonic() < deadline:
                APP.processEvents()
                time.sleep(0.01)
        self.assertIsNotNone(dialog.result, dialog.status.text())
        return dialog

    def test_sample_mode_is_read_only(self):
        sample = Musicinator(defaults(), lambda: True); self.addCleanup(sample.deleteLater)
        self.assertEqual(len(sample.visible), 3)
        self.assertFalse(sample.add_button.isEnabled()); self.assertFalse(sample.import_button.isEnabled())

    def test_add_edit_review_and_personal_values(self):
        editor = self.add_wall()
        album = self.tab.current()
        self.assertEqual((album.title, album.artists, album.additional_artists, album.year), ('The Wall', ('Pink Floyd',), ('Bob Ezrin',), 1979))
        self.assertEqual((album.editions[0].label, album.editions[0].format, album.copies[0].location), ('Original CD', 'CD', 'Shelf A'))
        editor.year.setText('19x9')
        self.assertFalse(editor.save_changes())
        self.assertTrue(editor.dirty())
        with patch('mediainator.music_ui.QMessageBox.question', return_value=Q.Cancel):
            self.assertFalse(self.tab.review_close())
        with patch('mediainator.music_ui.QMessageBox.question', return_value=Q.Discard):
            self.assertTrue(self.tab.review_close())
        self.assertFalse(editor.dirty())
        self.tab.favourite.setChecked(True); self.tab.rating.setCurrentIndex(9)
        stored = self.store.get(album.id)
        self.assertEqual((stored.favourite, stored.rating, stored.revision), (True, 9, 0))
        self.assertIn('★ Favourite', self.tab.detail.text())

    def test_list_columns_sort_and_state(self):
        self.add_wall()
        other = self.store.add_album(dict(title='Animals', artists=['Pink Floyd'], year=1977))
        self.store.set_personal(other, False, 10)
        self.tab.reload()
        self.tab.view.setCurrentText('List'); self.assertEqual(self.state['music_view'], 'List')
        model = self.tab.table.model()
        self.assertEqual(model.headerData(COLUMNS.index('Rating'), Qt.Orientation.Horizontal), 'Rating')
        self.tab.sort.setCurrentText('Rating (highest first)')
        self.assertEqual([a.title for a in self.tab.visible], ['Animals', 'The Wall'])
        self.assertEqual(model.data(model.index(0, COLUMNS.index('Rating'))), '10/10')
        self.tab.sort.setCurrentText('Year (oldest first)')
        self.assertEqual([a.title for a in self.tab.visible], ['Animals', 'The Wall'])
        self.tab.search.setText('ezrin'); self.assertEqual([a.title for a in self.tab.visible], ['The Wall'])
        self.tab.clear_search_filters(); self.assertEqual(self.state['music_search']['text'], '')
        validate(self.state)

    def test_browse_by_artist_genre_year(self):
        self.store.add_album(dict(title='The Wall', artists=['Pink Floyd'], year=1979, genres=['Rock']))
        self.store.add_album(dict(title='Kind of Blue', artists=['Miles Davis'], year=1959, genres=['Jazz']))
        self.tab.reload()
        self.tab.browse.setCurrentText('Artists')
        self.assertTrue(self.tab.browser.isVisible() or not self.tab.browser.isHidden())
        values = [self.tab.browser.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.tab.browser.count())]
        self.assertEqual(values, [None, 'Miles Davis', 'Pink Floyd'])
        self.tab.browser.setCurrentRow(1)
        self.assertEqual([a.title for a in self.tab.visible], ['Kind of Blue'])
        self.assertEqual(self.state['music_browse'], dict(mode='Artists', value='Miles Davis'))
        self.tab.browse.setCurrentText('Years')
        self.assertEqual(len(self.tab.visible), 2)
        self.tab.browser.setCurrentRow(2)       # 1979
        self.assertEqual([a.title for a in self.tab.visible], ['The Wall'])
        validate(self.state)
        # Restored on reopen.
        again = Musicinator(self.state, lambda: True, self.store); self.addCleanup(again.deleteLater)
        self.assertEqual([a.title for a in again.visible], ['The Wall'])

    def test_import_preview_groups_discs_and_attaches(self):
        self.add_wall(); self.tab.editor.close()
        dialog = self.import_media()
        top = [dialog.tree.topLevelItem(i) for i in range(dialog.tree.topLevelItemCount())]
        self.assertEqual([(t.text(2), t.text(1)) for t in top], [('Miles Davis', 'Kind of Blue'), ('Pink Floyd', 'The Wall')])
        self.assertEqual(dialog.tree.itemWidget(top[1], 4).currentData(), self.tab.current().id)
        dialog.apply()
        wall = next(a for a in self.tab.albums if a.title == 'The Wall')
        digital = next(e for e in wall.editions if e.format == 'Digital')
        self.assertEqual((len(wall.editions), digital.disc_count, len(digital.tracks), len(wall.files)), (2, 2, 2, 2))
        blue = next(a for a in self.tab.albums if a.title == 'Kind of Blue')
        self.assertEqual((blue.artists, blue.year, [t.number for t in blue.editions[0].tracks]), (('Miles Davis',), 1959, [1, 2]))
        self.assertTrue(all((self.media / rel).exists() for rel in TAGS))

    def test_play_writes_playlist_outside_music_and_locate_relocates(self):
        self.import_media().apply()
        album = next(a for a in self.tab.albums if a.title == 'Kind of Blue')
        self.state['selected_album'] = album.id; self.tab.render()
        calls = []
        with patch('mediainator.music_player.subprocess.Popen', side_effect=lambda argv, **k: calls.append(argv)), \
                patch('mediainator.music_player.shutil.which', return_value='/usr/bin/xdg-open'):
            self.tab.play(album.digital_copies[0])
        self.assertTrue(calls and calls[0][-1].endswith('now-playing.m3u8'))
        self.assertTrue((Path(self.tmp.name) / 'playlists' / 'now-playing.m3u8').exists())
        old = self.media / 'Miles Davis - Kind of Blue (1959)'
        new = Path(self.tmp.name) / 'moved' / 'Kind of Blue'; new.parent.mkdir()
        old.rename(new)
        with patch('mediainator.music_ui.QFileDialog.getExistingDirectory', return_value=str(new.parent)):
            self.tab.locate(self.tab.current().digital_copies[0])
        self.assertTrue(all(Path(f.path).parent == new.resolve() for f in self.tab.current().files))

    def test_edition_dialog_tracks_validation(self):
        dialog = EditionDialog(self.tab, 'Add edition'); self.addCleanup(dialog.deleteLater)
        dialog.label.setText('Remaster'); dialog.format.setCurrentText('CD')
        dialog.add_track(1, 1, 'Side one', '', '3:45'); dialog.add_track(2, 1, 'Side two', 'Guest', 'x')
        dialog.accept()
        self.assertIsNone(dialog.value); self.assertIn('Not saved', dialog.status.text())
        dialog.tracks.item(1, 4).setText('1:02:03')
        dialog.accept()
        fields, tracks = dialog.value
        self.assertEqual((fields['label'], [(t['disc'], t['duration']) for t in tracks]), ('Remaster', [(1, 225.0), (2, 3723.0)]))

    def test_editions_dialog_add_edition_and_remove_keeps_files(self):
        self.import_media().apply()
        album = next(a for a in self.tab.albums if a.title == 'Kind of Blue')
        self.state['selected_album'] = album.id; self.tab.render()
        editions = self.tab.open_editions()
        def fill(dialog):
            dialog.label.setText('Original LP'); dialog.format.setCurrentText('Vinyl'); dialog.add_track(1, 1, 'So What', '', '9:22')
            dialog.accept(); return QDialog.DialogCode.Accepted
        with patch.object(QDialog, 'exec', fill):
            editions.add_edition()
        self.assertEqual(sorted(e.label for e in self.store.get(album.id).editions), ['Original LP', 'Standard'])
        with patch('mediainator.music_ui.QMessageBox.question', return_value=Q.Yes):
            self.tab.remove_album()
        self.assertTrue(all((self.media / rel).exists() for rel in TAGS))
        self.assertNotIn('Kind of Blue', [a.title for a in self.tab.albums])


class HubIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.settings = SettingsStore(Path(self.tmp.name) / 'settings.json')
        self.state = defaults(); self.state['bookinator_open'] = False
        self.catalog = Path(self.tmp.name) / 'music.sqlite'

    def hub(self):
        hub = Hub(self.settings, self.state, app_data=Path(self.tmp.name) / 'data', music_catalog=self.catalog,
                  movie_catalog=Path(self.tmp.name) / 'movies.sqlite')
        self.addCleanup(hub.deleteLater)
        return hub

    def test_registry_launch_focus_and_close(self):
        self.assertTrue(next(m for m in MODULES if m.id == 'musicinator').available)
        hub = self.hub()
        self.assertTrue(hub.module_tiles['musicinator'].isEnabled())
        self.assertTrue(launch_module('musicinator', hub)); first = hub.musicinator
        self.assertTrue(launch_module('musicinator', hub))
        self.assertIs(hub.musicinator, first); self.assertEqual(hub.tabs.count(), 2)
        self.assertIs(hub.tabs.currentWidget(), first)
        self.assertTrue(self.settings.load()['musicinator_open'])
        launch_module('movieinator', hub); launch_module('bookinator', hub); self.assertEqual(hub.tabs.count(), 4)
        hub.close_tab(hub.tabs.indexOf(hub.musicinator))
        self.assertIsNone(hub.musicinator); self.assertIsNotNone(hub.movieinator); self.assertIsNotNone(hub.bookinator)
        self.assertFalse(self.settings.load()['musicinator_open'])

    def test_reopen_on_restart_and_workspace_snapshot(self):
        hub = self.hub(); hub.open_movies(); hub.open_music()
        album_id = hub.musicinator.store.add_album(dict(title='The Wall', artists=['Pink Floyd'])); hub.musicinator.reload()
        self.state['selected_album'] = album_id; hub.musicinator.render()
        value = capture(hub, allow_busy=True)
        self.assertEqual((value['modules'], value['active']), (['hub', 'musicinator', 'movieinator'], 'musicinator'))
        self.assertEqual(value['music_selection']['album_id'], album_id)
        snapshot(value)
        with self.assertRaises(WorkspaceError):
            snapshot(dict(value, modules=['hub', 'movieinator'], active='hub'))
        self.assertIn(['hub', 'bookinator', 'musicinator', 'movieinator'], MODULE_SETS)
        self.assertIn(['hub', 'bookinator', 'movieinator'], MODULE_SETS)   # M17 snapshots stay valid
        hub.close()
        again = Hub(self.settings, self.settings.load(), app_data=Path(self.tmp.name) / 'data', music_catalog=self.catalog,
                    movie_catalog=Path(self.tmp.name) / 'movies.sqlite')
        self.addCleanup(again.deleteLater)
        self.assertIsNotNone(again.musicinator)
        self.assertEqual(again.musicinator.current().title, 'The Wall')

    def test_hub_close_reviews_unsaved_album_edits(self):
        hub = self.hub(); hub.open_music(); hub.musicinator.add_album()
        hub.musicinator.editor.title.setText('Draft')
        with patch('mediainator.music_ui.QMessageBox.question', return_value=Q.Cancel):
            self.assertFalse(hub.review_close())
        with patch('mediainator.music_ui.QMessageBox.question', return_value=Q.Save):
            self.assertTrue(hub.review_close())
        self.assertEqual([a.title for a in hub.musicinator.store.load()], ['Draft'])
        self.assertTrue(hub.musicinator.unattended_close_blocked() is False)

    def test_sample_hub_without_catalog_is_read_only(self):
        hub = Hub(self.settings, self.state, app_data=Path(self.tmp.name) / 'data'); self.addCleanup(hub.deleteLater)
        hub.open_music()
        self.assertIsNone(hub.musicinator.store)
        self.assertFalse((Path(self.tmp.name) / 'data' / 'Music').exists())

    def test_live_catalog_and_playlists_live_in_app_data(self):
        hub = Hub(self.settings, self.state, live=False, app_data=Path(self.tmp.name) / 'data', music_catalog=self.catalog)
        self.addCleanup(hub.deleteLater)
        hub.open_music()
        self.assertEqual(hub.musicinator.playlist_folder, self.catalog.parent / 'playlists')

    def test_settings_validation(self):
        good = dict(defaults(), musicinator_open=True, music_view='List', selected_album=str(uuid4()), music_player='mpv',
                    music_search=dict(text='x', genres=['Rock'], formats=['CD'], personal=['Favourite'], expanded=False,
                                      sort='Artist A–Z'),
                    music_browse=dict(mode='Artists', value='Pink Floyd'))
        validate(good)
        for bad in (dict(musicinator_open='yes'), dict(music_view='Cards'), dict(selected_album=5),
                    dict(music_player=None), dict(music_search=dict(personal='Favourite')),
                    dict(music_browse=dict(mode=1)), dict(music_browse=dict(value=3))):
            with self.subTest(bad=bad), self.assertRaises(SettingsError):
                validate(dict(defaults(), **bad))

    def test_catalog_failure_is_recorded_and_retry_reloads(self):
        import sqlite3
        from mediainator.activity_panel import guidance
        with sqlite3.connect(self.catalog) as db:
            db.execute('CREATE TABLE unrelated(x)')        # not a Music-inator catalog
        hub = self.hub(); hub.open_music()
        self.assertTrue(hub.musicinator.load_error)
        self.assertFalse(hub.musicinator.add_button.isEnabled())
        record = next(r for r in hub.activity.invoke('records') if r['source'].get('kind') == 'music_catalog')
        self.assertEqual((record['module'], record['pending']), ('musicinator', True))
        self.assertIn('Reload catalog in Music-inator', guidance(record))
        self.catalog.unlink()                               # the owner repaired the location
        hub.activity_controller.review(record)
        self.assertEqual(hub.musicinator.load_error, '')
        self.assertTrue(hub.musicinator.add_button.isEnabled())
        self.assertFalse(any(r['source'].get('kind') == 'music_catalog' and r['pending']
                             for r in hub.activity.invoke('records')))

if __name__ == '__main__':
    unittest.main()
