"""Movie-inator catalog, storage and scan planning (no Qt required)."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from mediainator.movie_catalog import (SAMPLE_MOVIES, find_movies, normalize_title, parse_filename, sort_key)
from mediainator.movie_store import ConflictError, MovieStore, MovieStoreError, validate_movie
from mediainator.movie_scan import plan, probe, revalidate, ScanFile


class ParseTests(unittest.TestCase):
    def test_common_file_names(self):
        cases = {
            'Alien (1979)': ('Alien', 1979, ''),
            'Alien.1979.Directors.Cut.1080p.BluRay.x264': ('Alien', 1979, "Director's Cut"),
            'Blade_Runner_1982_Final_Cut': ('Blade Runner', 1982, ''),
            '1917 (2019)': ('1917', 2019, ''),
            '2001 A Space Odyssey (1968)': ('2001 A Space Odyssey', 1968, ''),
            'Harry Potter and the Deathly Hallows Part 1 (2010)': ('Harry Potter and the Deathly Hallows Part 1', 2010, ''),
            'Heat': ('Heat', None, ''),
            'The.Matrix.1999.2160p.UHD.HDR': ('The Matrix', 1999, ''),
        }
        for stem, expected in cases.items():
            with self.subTest(stem=stem):
                self.assertEqual(parse_filename(stem), expected)

    def test_title_year_folder_layout(self):
        self.assertEqual(parse_filename('movie', 'Alien (1979)')[:2], ('Alien', 1979))
        self.assertEqual(parse_filename('Alien', 'Alien (1979)')[:2], ('Alien', 1979))
        # An arbitrary folder name is not trusted.
        self.assertEqual(parse_filename('Heat', 'Collection 2020')[:2], ('Heat', None))

    def test_normalize_and_sort(self):
        self.assertEqual(normalize_title('Amélie!'), normalize_title('amelie'))
        self.assertEqual(normalize_title('Fast & Furious'), 'fast and furious')
        self.assertEqual(sort_key('The General'), 'general')

    def test_search_rules(self):
        self.assertEqual([m.id for m in find_movies(SAMPLE_MOVIES, 'lang')], ['sample-metropolis'])
        self.assertEqual([m.id for m in find_movies(SAMPLE_MOVIES, '1926')], ['sample-general'])
        self.assertEqual([m.id for m in find_movies(SAMPLE_MOVIES, '', statuses=('Watched',))], ['sample-nosferatu'])
        self.assertEqual([m.id for m in find_movies(SAMPLE_MOVIES, '', genres=('Horror', 'Comedy'), formats=('DVD',))], ['sample-nosferatu'])
        # Articles are ignored for sorting: General, Metropolis, Nosferatu.
        self.assertEqual([m.id for m in find_movies(SAMPLE_MOVIES, '')], ['sample-general', 'sample-metropolis', 'sample-nosferatu'])


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.profile = str(uuid4())
        self.store = MovieStore(self.root / 'Movies' / 'catalog.sqlite', self.profile)
        self.video = self.root / 'Alien (1979).mkv'; self.video.write_bytes(b'x' * 10)

    def test_empty_catalog_and_roundtrip(self):
        self.assertEqual(self.store.load(), ())
        self.assertIsNone(self.store.catalog_uuid())
        movie_id = self.store.add_movie(dict(title=' Alien ', year=1979, directors=['Ridley Scott', 'ridley scott'], genres=['Horror']),
            [dict(label="Director's Cut", format='Blu-ray', copies=[dict(kind='physical', location='Shelf')]),
             dict(label='MKV rip', format='Digital', copies=[dict(kind='file', path=str(self.video), size=10, container='mkv')])])
        movie = self.store.get(movie_id)
        self.assertEqual((movie.title, movie.year, movie.directors), ('Alien', 1979, ('Ridley Scott',)))
        self.assertEqual([e.label for e in movie.editions], ["Director's Cut", 'MKV rip'])
        self.assertEqual(movie.formats, ('Blu-ray', 'Digital'))
        self.assertEqual(movie.files[0].path, str(self.video.resolve()))
        self.assertEqual(self.store.known_paths(), {str(self.video.resolve()): movie_id})
        self.assertIsNotNone(self.store.catalog_uuid())

    def test_validation(self):
        for bad in (dict(title=''), dict(title='A', year=1500), dict(title='A', runtime=0),
                    dict(title='A', genres='Horror'), dict(title='A\x00'), dict(title='A', unknown=1), dict(title='A', year=True)):
            with self.subTest(bad=bad), self.assertRaises(MovieStoreError):
                validate_movie(bad)
        with self.assertRaises(MovieStoreError):
            self.store.add_movie(dict(title='A'), [dict(label='X', format='Laserdisc')])
        self.assertEqual(self.store.load(), ())  # failed transaction left nothing

    def test_duplicate_file_rejected_atomically(self):
        self.store.add_movie(dict(title='Alien'), [dict(label='A', copies=[dict(kind='file', path=str(self.video))])])
        with self.assertRaises(MovieStoreError):
            self.store.add_movie(dict(title='Alien again'), [dict(label='B', copies=[dict(kind='file', path=str(self.video))])])
        self.assertEqual([m.title for m in self.store.load()], ['Alien'])

    def test_revision_conflict_and_partial_update(self):
        movie_id = self.store.add_movie(dict(title='Alien', year=1979, synopsis='In space.'))
        self.store.update_movie(movie_id, 0, dict(title='Alien'))
        with self.assertRaises(ConflictError) as ctx:
            self.store.update_movie(movie_id, 0, dict(year=1980))
        self.assertEqual(ctx.exception.current.revision, 1)
        self.store.update_movie(movie_id, 1, dict(genres=['Horror']))
        movie = self.store.get(movie_id)
        self.assertEqual((movie.year, movie.synopsis, movie.genres, movie.revision), (1979, 'In space.', ('Horror',), 2))

    def test_personal_activity_is_per_profile_and_does_not_bump_revision(self):
        movie_id = self.store.add_movie(dict(title='Alien'))
        self.store.set_personal(movie_id, True, 9)
        other = MovieStore(self.store.path, str(uuid4()))
        self.assertEqual((self.store.get(movie_id).watched, self.store.get(movie_id).rating), (True, 9))
        self.assertEqual((other.get(movie_id).watched, other.get(movie_id).rating), (False, None))
        self.assertEqual(self.store.get(movie_id).revision, 0)
        for bad in ((1, None), (True, 11), (True, 0)):
            with self.assertRaises(MovieStoreError):
                self.store.set_personal(movie_id, *bad)

    def test_remove_movie_keeps_files(self):
        movie_id = self.store.add_movie(dict(title='Alien'), [dict(label='A', copies=[dict(kind='file', path=str(self.video))])])
        self.store.set_personal(movie_id, True, None)
        self.store.remove_movie(movie_id)
        self.assertTrue(self.video.exists())
        self.assertEqual(self.store.load(), ())
        with sqlite3.connect(self.store.path) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM copies').fetchone()[0], 0)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM personal').fetchone()[0], 0)

    def test_edition_and_copy_management(self):
        movie_id = self.store.add_movie(dict(title='Alien'))
        edition = self.store.add_edition(movie_id, '4K UHD', '4K UHD')
        copy = self.store.add_copy(edition, dict(kind='physical', location='Box 1'))
        self.store.update_copy_location(copy, 'Living room')
        self.store.update_edition(edition, '4K UHD Edition', '4K UHD', 'Steelbook')
        moved = self.root / 'moved.mkv'; moved.write_bytes(b'y')
        file_copy = self.store.add_copy(edition, dict(kind='file', path=str(self.video)))
        self.store.relocate_file(file_copy, moved)
        movie = self.store.get(movie_id)
        self.assertEqual(movie.editions[0].label, '4K UHD Edition')
        self.assertEqual({c.location or c.path for c in movie.copies}, {'Living room', str(moved.resolve())})
        self.assertEqual(movie.revision, 6)
        self.store.remove_copy(copy); self.store.remove_edition(edition)
        self.assertEqual(self.store.get(movie_id).editions, ())

    def test_foreign_newer_and_damaged_files_are_preserved(self):
        path = self.root / 'other.sqlite'
        with sqlite3.connect(path) as db:
            db.execute('CREATE TABLE unrelated(x)')
        before = path.read_bytes()
        with self.assertRaises(MovieStoreError):
            MovieStore(path, self.profile).add_movie(dict(title='A'))
        self.assertEqual(before, path.read_bytes())
        self.store.initialize()
        with sqlite3.connect(self.store.path) as db:
            db.execute("UPDATE meta SET value='2' WHERE key='schema'")
        with self.assertRaises(MovieStoreError):
            self.store.load()
        with self.assertRaises(MovieStoreError):
            self.store.add_movie(dict(title='A'))
        with self.assertRaises(MovieStoreError):
            MovieStore(path, 'not-a-uuid')


class ScanTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.store = MovieStore(self.root / 'catalog.sqlite', str(uuid4()))
        self.media = self.root / 'media'
        for rel in ('Alien (1979).mkv', 'Alien (1979).mp4', 'Heat (1995)/movie.mkv', 'Heat (1995)/notes.txt',
                    'Kill Bill (2003)/Kill Bill (2003) CD1.avi', 'Kill Bill (2003)/Kill Bill (2003) CD2.avi',
                    '.hidden/Secret (2000).mkv', 'Brazil (1985).mkv'):
            path = self.media / rel; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(b'v' * 5)

    @staticmethod
    def fake_probe(path):
        return ScanFile(path=path, size=5, container=Path(path).suffix[1:], height=1080, duration=7020)

    def test_grouping_parts_hidden_and_known(self):
        brazil = str((self.media / 'Brazil (1985).mkv').resolve())
        existing = self.store.add_movie(dict(title='Brazil', year=1985), [dict(label='DVD', format='DVD')])
        heat = self.store.add_movie(dict(title='Heat', year=1995))
        result = plan([self.media], self.store.load(), {brazil: existing}, probe_file=self.fake_probe)
        self.assertEqual(result.known, [brazil])
        groups = {(g.title, g.year): g for g in result.groups}
        self.assertEqual(set(groups), {('Alien', 1979), ('Heat', 1995), ('Kill Bill', 2003)})
        alien = groups[('Alien', 1979)]
        self.assertEqual((alien.action, len(alien.files), len(alien.editions())), ('create', 2, 2))
        self.assertEqual(sorted(e['label'] for e in alien.editions()), ['Digital (MKV 1080p)', 'Digital (MP4 1080p)'])
        kill = groups[('Kill Bill', 2003)].editions()
        self.assertEqual((len(kill), len(kill[0]['copies'])), (1, 2))
        self.assertEqual((groups[('Heat', 1995)].action, groups[('Heat', 1995)].movie_id), ('attach', heat))
        self.assertEqual(groups[('Alien', 1979)].runtime(), 117)

    def test_edition_labels_keep_distinct_qualities_and_sources(self):
        from mediainator.movie_scan import edition_label
        make = lambda name, height: ScanFile(path='/m/' + name, container=name.rsplit('.', 1)[1], height=height)
        self.assertEqual(edition_label(make('Alien (1979).mkv', 1080)), 'Digital (MKV 1080p)')
        self.assertEqual(edition_label(make('Alien.1979.2160p.UHD.mkv', 2160)), 'Digital (MKV 4K)')
        self.assertEqual(edition_label(make('Alien.1979.1080p.BluRay.x264.mkv', 1080)), 'Digital (MKV 1080p, Blu-ray rip)')
        self.assertEqual(edition_label(make('Alien (1979) WEB-DL.mp4', 720)), 'Digital (MP4 720p, WEB)')
        self.assertEqual(edition_label(make('Kill Bill (2003) CD1.avi', 0)), 'Digital (AVI)')
        # Two 1080p MKVs from different sources stay separate, distinguishable editions.
        group_files = [make('Alien.1979.1080p.BluRay.mkv', 1080), make('Alien.1979.1080p.WEB-DL.mkv', 1080)]
        from mediainator.movie_scan import ScanGroup
        labels = sorted(e['label'] for e in ScanGroup('Alien', 1979, group_files).editions())
        self.assertEqual(labels, ['Digital (MKV 1080p, Blu-ray rip)', 'Digital (MKV 1080p, WEB)'])

    def test_apply_and_revalidate(self):
        result = plan([self.media / 'Alien (1979).mkv', self.media / 'Alien (1979).mp4', self.media / 'Heat (1995)' / 'notes.txt'],
                      (), {}, probe_file=self.fake_probe)
        self.assertEqual(len(result.skipped), 1)
        group = result.groups[0]
        self.assertEqual(revalidate(group, {}), [])
        movie_id = self.store.apply_group('create', group.editions(), title=group.title, year=group.year, runtime=group.runtime())
        movie = self.store.get(movie_id)
        self.assertEqual((movie.title, movie.runtime, len(movie.files)), ('Alien', 117, 2))
        self.assertTrue(revalidate(group, self.store.known_paths()))
        (self.media / 'Alien (1979).mkv').write_bytes(b'longer content')
        self.assertTrue(any('changed size' in p for p in revalidate(group, {})))

    def test_ffprobe_output_parsing_and_failures(self):
        path = str(self.media / 'Brazil (1985).mkv')
        payload = dict(format=dict(duration='8520.5'), streams=[
            dict(codec_type='video', codec_name='mjpeg', width=10, height=10, disposition=dict(attached_pic=1)),
            dict(codec_type='video', codec_name='hevc', width=3840, height=2160),
            dict(codec_type='audio', codec_name='dts', channels=6, tags=dict(language='eng')),
            dict(codec_type='subtitle', tags=dict(language='ger'))])
        ok = lambda *a, **k: SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr='')
        info = probe(path, runner=ok)
        self.assertEqual((info.width, info.height, info.video_codec, info.audio, info.subtitles), (3840, 2160, 'hevc', ('eng dts 6ch',), ('ger',)))
        fail = lambda *a, **k: SimpleNamespace(returncode=1, stdout='', stderr='Invalid data')
        self.assertEqual(probe(path, runner=fail).probe_error, 'Invalid data')
        def boom(*a, **k): raise OSError('no ffprobe')
        self.assertIn('no ffprobe', probe(path, runner=boom).probe_error)


if __name__ == '__main__':
    unittest.main()
