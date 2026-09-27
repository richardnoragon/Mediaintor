"""Music-inator catalog, storage, scan planning and player launch (no Qt required)."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from mediainator.music_catalog import (SAMPLE_ALBUMS, VARIOUS_ARTISTS, Album, Edition, Track, browse_values, find_albums,
                                       format_duration, parse_album_folder, parse_duration, parse_track_filename,
                                       split_edition)
from mediainator.music_player import PlayerError, build_command, launch_album, match_moved, write_playlist
from mediainator.music_scan import ScanFile, plan, probe, quality, revalidate, files_for
from mediainator.music_store import ConflictError, MusicStore, MusicStoreError, validate_album, validate_tracks


class ParseTests(unittest.TestCase):
    def test_album_folder_names(self):
        cases = {
            ('Pink Floyd - The Wall (1979)', ''): ('Pink Floyd', 'The Wall', 1979, ''),
            ('Pink Floyd - 1979 - The Wall', ''): ('Pink Floyd', 'The Wall', 1979, ''),
            ('1979 - The Wall', 'Pink Floyd'): ('Pink Floyd', 'The Wall', 1979, ''),
            ('The Wall (2011 Remaster) [FLAC 24-96]', 'Pink Floyd'): ('Pink Floyd', 'The Wall', None, '2011 Remaster'),
            ('Animals (1977)', 'Music'): ('', 'Animals', 1977, ''),
            ('Kind of Blue [Legacy Edition] (1959)', 'Miles Davis'): ('Miles Davis', 'Kind of Blue', 1959, 'Legacy Edition'),
            ('Songs (For Lovers)', 'Artist'): ('Artist', 'Songs (For Lovers)', None, ''),
        }
        for (name, parent), expected in cases.items():
            with self.subTest(name=name):
                self.assertEqual(parse_album_folder(name, parent), expected)

    def test_track_file_names(self):
        cases = {
            '01 - In the Flesh': (None, 1, 'In the Flesh'),
            '1-03 Another Brick': (1, 3, 'Another Brick'),
            '07. Mother': (None, 7, 'Mother'),
            '12_Hey_You': (None, 12, 'Hey You'),
            'Pink Floyd - The Wall - 05 - Young Lust': (None, 5, 'Young Lust'),
            'Comfortably Numb': (None, None, 'Comfortably Numb'),
        }
        for stem, expected in cases.items():
            with self.subTest(stem=stem):
                self.assertEqual(parse_track_filename(stem), expected)

    def test_edition_split_and_durations(self):
        self.assertEqual(split_edition('The Wall (Remastered 2011)'), ('The Wall', 'Remastered 2011', None))
        self.assertEqual(split_edition('Abbey Road [Super Deluxe]'), ('Abbey Road', 'Super Deluxe', None))
        self.assertEqual((format_duration(225), format_duration(3723), format_duration(None)), ('3:45', '1:02:03', ''))
        self.assertEqual((parse_duration('3:45'), parse_duration(''), parse_duration('90')), (225.0, None, 90.0))
        with self.assertRaises(ValueError):
            parse_duration('3m45')

    def test_search_filters_and_browse(self):
        ids = lambda albums: [a.id for a in albums]
        self.assertEqual(ids(find_albums(SAMPLE_ALBUMS, 'gould')), ['sample-goldberg'])
        self.assertEqual(ids(find_albums(SAMPLE_ALBUMS, 'freddie')), ['sample-kind-of-blue'])   # track titles
        self.assertEqual(ids(find_albums(SAMPLE_ALBUMS, '', personal=('Favourite',))), ['sample-goldberg'])
        self.assertEqual(ids(find_albums(SAMPLE_ALBUMS, '', personal=('Not rated',), formats=('CD',))), ['sample-kind-of-blue'])
        self.assertEqual(ids(find_albums(SAMPLE_ALBUMS, '', genres=('Jazz',), browse=('Years', '1924'))), ['sample-rhapsody'])
        self.assertEqual(ids(find_albums(SAMPLE_ALBUMS, '', browse=('Artists', 'miles davis'))), ['sample-kind-of-blue'])
        # Sorted by primary artist as written: George Gershwin, Glenn Gould, Miles Davis.
        self.assertEqual(ids(find_albums(SAMPLE_ALBUMS, '')), ['sample-rhapsody', 'sample-goldberg', 'sample-kind-of-blue'])
        self.assertEqual(dict(browse_values(SAMPLE_ALBUMS, 'Genres')), {'Classical': 2, 'Jazz': 2})
        self.assertEqual([v for v, _ in browse_values(SAMPLE_ALBUMS, 'Years')], ['1924', '1955', '1959'])
        compilation = Album('c', 'Hits', (VARIOUS_ARTISTS,), editions=(Edition('e', 'CD', tracks=(Track('A', artist='Solo Singer'),)),))
        self.assertIn('Solo Singer', dict(browse_values((compilation,), 'Artists')))


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.profile = str(uuid4())
        self.store = MusicStore(self.root / 'Music' / 'catalog.sqlite', self.profile)
        self.folder = self.root / 'The Wall'; self.folder.mkdir()
        self.flac = [self.folder / f'0{n} - Track {n}.flac' for n in (1, 2)]
        for path in self.flac:
            path.write_bytes(b'f' * 10)

    def edition(self, **extra):
        return dict(dict(label='2011 Remaster', format='CD', release_year=2011, disc_count=1,
                         tracks=[dict(title='In the Flesh?', number=1, duration=199.0),
                                 dict(title='The Thin Ice', number=2, disc=2)],
                         copies=[dict(kind='physical', location='CD shelf'),
                                 dict(kind='digital', quality='FLAC', files=[dict(path=str(p), number=i + 1)
                                                                             for i, p in enumerate(self.flac)])]), **extra)

    def test_empty_catalog_and_roundtrip(self):
        self.assertEqual(self.store.load(), ())
        self.assertIsNone(self.store.catalog_uuid())
        album_id = self.store.add_album(dict(title=' The Wall ', artists=['Pink Floyd', 'pink floyd'], year=1979,
                                             additional_artists=['Pink Floyd', 'Michael Kamen'], genres=['Rock']),
                                        [self.edition()])
        album = self.store.get(album_id)
        self.assertEqual((album.title, album.artists, album.additional_artists), ('The Wall', ('Pink Floyd',), ('Michael Kamen',)))
        edition = album.editions[0]
        self.assertEqual((edition.label, edition.format, edition.release_year, edition.disc_count), ('2011 Remaster', 'CD', 2011, 2))
        self.assertEqual([(t.disc, t.number, t.title) for t in edition.tracks], [(1, 1, 'In the Flesh?'), (2, 2, 'The Thin Ice')])
        self.assertEqual([len(d[1]) for d in edition.discs], [1, 1])
        self.assertEqual([c.kind for c in edition.copies], ['physical', 'digital'])
        self.assertEqual([f.path for f in album.files], [str(p.resolve()) for p in self.flac])
        self.assertEqual(album.copies[1].folder, str(self.folder.resolve()))
        self.assertEqual(set(self.store.known_paths()), {str(p.resolve()) for p in self.flac})
        self.assertIsNotNone(self.store.catalog_uuid())

    def test_validation_is_atomic(self):
        for bad in (dict(title=''), dict(title='A', year=500), dict(title='A', artists='Band'),
                    dict(title='A\x00'), dict(title='A', unknown=1), dict(title='A', year=True)):
            with self.subTest(bad=bad), self.assertRaises(MusicStoreError):
                validate_album(bad)
        for bad in ([dict(title='')], [dict(title='A', disc=0)], [dict(title='A', number=1000)],
                    [dict(title='A', duration=-1)], [dict(title='A', extra=1)], 'A'):
            with self.subTest(bad=bad), self.assertRaises(MusicStoreError):
                validate_tracks(bad)
        for edition in (dict(label='X', format='8-track'), dict(label=''), dict(label='X', copies=[dict(kind='digital')]),
                        dict(label='X', copies=[dict(kind='physical', files=[dict(path=str(self.flac[0]))])])):
            with self.subTest(edition=edition), self.assertRaises(MusicStoreError):
                self.store.add_album(dict(title='A'), [edition])
        self.assertEqual(self.store.load(), ())

    def test_duplicate_file_rejected_atomically(self):
        self.store.add_album(dict(title='The Wall'), [self.edition()])
        with self.assertRaises(MusicStoreError):
            self.store.add_album(dict(title='Again'), [self.edition()])
        self.assertEqual([a.title for a in self.store.load()], ['The Wall'])

    def test_revision_conflict_and_partial_update(self):
        album_id = self.store.add_album(dict(title='The Wall', artists=['Pink Floyd'], year=1979))
        self.store.update_album(album_id, 0, dict(genres=['Rock']))
        with self.assertRaises(ConflictError) as ctx:
            self.store.update_album(album_id, 0, dict(year=1980))
        self.assertEqual(ctx.exception.current.revision, 1)
        self.store.update_album(album_id, 1, dict(additional_artists=['Pink Floyd', 'Bob Ezrin']))
        album = self.store.get(album_id)
        self.assertEqual((album.year, album.genres, album.additional_artists, album.revision), (1979, ('Rock',), ('Bob Ezrin',), 2))

    def test_personal_is_per_profile_and_keeps_revision(self):
        album_id = self.store.add_album(dict(title='The Wall'))
        self.store.set_personal(album_id, True, 9)
        other = MusicStore(self.store.path, str(uuid4()))
        self.assertEqual((self.store.get(album_id).favourite, self.store.get(album_id).rating), (True, 9))
        self.assertEqual((other.get(album_id).favourite, other.get(album_id).rating), (False, None))
        self.assertEqual(self.store.get(album_id).revision, 0)
        for bad in ((1, None), (True, 11), (True, 0)):
            with self.assertRaises(MusicStoreError):
                self.store.set_personal(album_id, *bad)

    def test_remove_album_keeps_files(self):
        album_id = self.store.add_album(dict(title='The Wall'), [self.edition()])
        self.store.set_personal(album_id, True, None)
        self.store.remove_album(album_id)
        self.assertTrue(all(p.exists() for p in self.flac))
        with sqlite3.connect(self.store.path) as db:
            for table in ('editions', 'tracks', 'copies', 'files', 'personal'):
                self.assertEqual(db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0], 0, table)

    def test_edition_tracks_and_copy_management(self):
        album_id = self.store.add_album(dict(title='The Wall'))
        edition = self.store.add_edition(album_id, dict(label='Vinyl', format='Vinyl'))
        copy = self.store.add_copy(edition, dict(kind='physical', location='Box 1'))
        self.store.update_copy(copy, 'Living room', 'Near mint', 'Gatefold')
        self.store.update_edition(edition, dict(label='Original LP', format='Vinyl', release_year=1979, disc_count=2),
                                  [dict(title='Side A', number=1), dict(title='Side C', disc=2, number=1)])
        digital = self.store.add_copy(edition, dict(kind='digital', files=[dict(path=str(p)) for p in self.flac]))
        album = self.store.get(album_id)
        self.assertEqual((album.editions[0].label, album.editions[0].disc_count, len(album.editions[0].tracks)), ('Original LP', 2, 2))
        self.assertEqual(album.copies[0].location, 'Living room')
        self.assertEqual(album.revision, 5)
        # Edition fields only: tracks untouched.
        self.store.update_edition(edition, dict(label='Original LP', format='Vinyl', disc_count=1))
        self.assertEqual(self.store.get(album_id).editions[0].disc_count, 2)
        self.store.remove_copy(digital); self.store.remove_copy(copy); self.store.remove_edition(edition)
        self.assertEqual(self.store.get(album_id).editions, ())
        self.assertTrue(all(p.exists() for p in self.flac))

    def test_relocate_files_all_or_nothing(self):
        album_id = self.store.add_album(dict(title='The Wall'), [self.edition()])
        copy = self.store.get(album_id).digital_copies[0]
        moved = self.root / 'moved'; moved.mkdir()
        targets = {f.id: moved / Path(f.path).name for f in copy.files}
        for path in targets.values():
            path.write_bytes(b'f')
        self.store.relocate_files(copy.id, targets)
        self.assertEqual(sorted(f.path for f in self.store.get(album_id).files), sorted(str(p.resolve()) for p in targets.values()))
        first, second = copy.files
        with self.assertRaises(MusicStoreError):   # both to one path
            self.store.relocate_files(copy.id, {first.id: targets[first.id], second.id: targets[first.id]})
        # Swapping two paths is allowed.
        self.store.relocate_files(copy.id, {first.id: targets[second.id], second.id: targets[first.id]})
        with self.assertRaises(MusicStoreError):
            self.store.relocate_files(copy.id, {'unknown': self.flac[0]})

    def test_foreign_newer_and_movie_catalogs_are_preserved(self):
        path = self.root / 'other.sqlite'
        with sqlite3.connect(path) as db:
            db.execute('CREATE TABLE unrelated(x)')
        before = path.read_bytes()
        with self.assertRaises(MusicStoreError):
            MusicStore(path, self.profile).add_album(dict(title='A'))
        self.assertEqual(before, path.read_bytes())
        from mediainator.movie_store import MovieStore
        movies = self.root / 'movies.sqlite'
        MovieStore(movies, self.profile).initialize()
        before = movies.read_bytes()
        with self.assertRaises(MusicStoreError):
            MusicStore(movies, self.profile).add_album(dict(title='A'))
        with self.assertRaises(MusicStoreError):
            MusicStore(movies, self.profile).load()
        self.assertEqual(before, movies.read_bytes())
        self.store.initialize()
        with sqlite3.connect(self.store.path) as db:
            db.execute("UPDATE meta SET value='2' WHERE key='schema'")
        with self.assertRaises(MusicStoreError):
            self.store.load()
        with self.assertRaises(MusicStoreError):
            self.store.add_album(dict(title='A'))
        with self.assertRaises(MusicStoreError):
            MusicStore(path, 'not-a-uuid')


def tagged(path, **tags):
    return ScanFile(path=path, size=5, container=Path(path).suffix[1:], codec=Path(path).suffix[1:],
                    duration=200.0, bit_depth=16 if path.endswith('.flac') else None,
                    sample_rate=44100, bitrate=None if path.endswith('.flac') else 320000, tags=tags)


class ScanTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.store = MusicStore(self.root / 'catalog.sqlite', str(uuid4()))
        self.media = self.root / 'music'
        self.files = {
            # Tagged FLAC and MP3 rips of the same release → one edition, two copies.
            'Wall FLAC/01.flac': dict(album='The Wall', album_artist='Pink Floyd', title='In the Flesh?', track='1/2', date='1979-11-30'),
            'Wall FLAC/02.flac': dict(album='The Wall', album_artist='Pink Floyd', title='The Thin Ice', track='2/2', date='1979'),
            'Wall MP3/a.mp3': dict(album='The Wall', artist='Pink Floyd', title='In the Flesh?', track='1'),
            'Wall MP3/b.mp3': dict(album='The Wall', artist='Pink Floyd', title='The Thin Ice', track='2'),
            # Same album, different track list and hint → separate edition.
            'Wall Deluxe/01.flac': dict(album='The Wall (Deluxe Edition)', album_artist='Pink Floyd', title='In the Flesh?', track='1'),
            'Wall Deluxe/02.flac': dict(album='The Wall (Deluxe Edition)', album_artist='Pink Floyd', title='Demo', track='2'),
            # Untagged, folder layout with disc subfolders.
            'Miles Davis/Kind of Blue (1959)/CD1/01 - So What.flac': {},
            'Miles Davis/Kind of Blue (1959)/CD2/01 - Flamenco Sketches.flac': {},
            # Compilation: different track artists, no album artist.
            'Hits/01.mp3': dict(album='Hits 1990', artist='Singer A', title='One', track='1'),
            'Hits/02.mp3': dict(album='Hits 1990', artist='Singer B', title='Two', track='2'),
            'Hits/cover.jpg': None,
            '.hidden/x.flac': {},
        }
        for rel in self.files:
            path = self.media / rel; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(b'a' * 5)

    def fake_probe(self, path):
        rel = str(Path(path).relative_to(self.media.resolve()))
        return tagged(path, **(self.files.get(rel) or {}))

    def groups(self, result):
        return {(g.artist, g.title): g for g in result.groups}

    def test_tags_first_folder_fallback_discs_and_compilations(self):
        result = plan([self.media], (), {}, probe_file=self.fake_probe)
        groups = self.groups(result)
        self.assertEqual(set(groups), {('Pink Floyd', 'The Wall'), ('Miles Davis', 'Kind of Blue'), (VARIOUS_ARTISTS, 'Hits 1990')})
        wall = groups[('Pink Floyd', 'The Wall')]
        self.assertEqual(wall.year, 1979)
        editions = sorted(wall.editions(), key=lambda e: e['label'])
        self.assertEqual([e['label'] for e in editions], ['Deluxe Edition', 'Standard'])
        standard = editions[1]
        self.assertEqual(len(standard['copies']), 2)
        self.assertEqual(sorted(c['quality'] for c in standard['copies']), ['FLAC 16-bit/44.1 kHz', 'MP3 320 kbps'])
        self.assertEqual([t['title'] for t in standard['tracks']], ['In the Flesh?', 'The Thin Ice'])
        blue = groups[('Miles Davis', 'Kind of Blue')]
        edition = blue.editions()[0]
        self.assertEqual((blue.year, edition['disc_count'], [(t['disc'], t['number']) for t in edition['tracks']]),
                         (1959, 2, [(1, 1), (2, 1)]))
        self.assertTrue(any('no album tags' in w for w in blue.warnings))
        hits = groups[(VARIOUS_ARTISTS, 'Hits 1990')].editions()[0]
        self.assertEqual([t['artist'] for t in hits['tracks']], ['Singer A', 'Singer B'])
        self.assertFalse(any('.hidden' in f.path for g in result.groups for f in g.files))

    def test_attach_matches_existing_edition_and_skips_known(self):
        first = plan([self.media / 'Wall FLAC'], (), {}, probe_file=self.fake_probe).groups[0]
        album_id = self.store.apply_group('create', first.editions(), title=first.title, artists=[first.artist], year=first.year)
        result = plan([self.media], self.store.load(), self.store.known_paths(), probe_file=self.fake_probe)
        self.assertEqual(len(result.known), 2)
        wall = self.groups(result)[('Pink Floyd', 'The Wall')]
        self.assertEqual((wall.action, wall.album_id), ('attach', album_id))
        editions = wall.editions()
        matched = [e for e in editions if 'edition_id' in e]
        self.assertEqual(len(matched), 1)
        self.store.apply_group('attach', editions, album_id=album_id)
        album = self.store.get(album_id)
        self.assertEqual(sorted((e.label, len(e.copies)) for e in album.editions), [('Deluxe Edition', 1), ('Standard', 2)])
        self.assertEqual(len(album.files), 6)

    def test_revalidate_and_apply_create(self):
        group = plan([self.media / 'Hits'], (), {}, probe_file=self.fake_probe).groups[0]
        self.assertEqual(revalidate(group, {}), [])
        album_id = self.store.apply_group('create', group.editions(), title=group.title, artists=[group.artist])
        self.assertEqual(self.store.get(album_id).artists, (VARIOUS_ARTISTS,))
        self.assertTrue(revalidate(group, self.store.known_paths()))
        (self.media / 'Hits' / '01.mp3').write_bytes(b'longer content')
        self.assertTrue(any('changed size' in p for p in revalidate(group, {})))
        skipped = plan([self.media / 'Hits' / 'cover.jpg'], (), {}, probe_file=self.fake_probe).skipped
        self.assertEqual(len(skipped), 1)

    def test_files_for_manual_copy(self):
        copy, tracks, unit, skipped = files_for([str(self.media / 'Miles Davis' / 'Kind of Blue (1959)')], probe_file=self.fake_probe)
        self.assertEqual((len(copy['files']), [t['disc'] for t in tracks], unit.title), (2, [1, 2], 'Kind of Blue'))

    def test_ffprobe_output_parsing_and_failures(self):
        path = str(self.media / 'Hits' / '01.mp3')
        payload = dict(format=dict(duration='201.5', bit_rate='320000', tags=dict(ALBUM='Hits', album_artist='VA', TRACK='3/12', disc='1/2')),
                       streams=[dict(codec_type='video', codec_name='mjpeg'),
                                dict(codec_type='audio', codec_name='mp3', sample_rate='44100', channels=2, bit_rate='320000')])
        ok = lambda *a, **k: SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr='')
        info = probe(path, runner=ok)
        self.assertEqual((info.codec, info.sample_rate, info.bitrate, info.channels, info.duration), ('mp3', 44100, 320000, 2, 201.5))
        self.assertEqual((info.tags['album'], info.tags['album_artist'], info.tags['track']), ('Hits', 'VA', '3/12'))
        ogg = dict(format=dict(), streams=[dict(codec_type='audio', codec_name='flac', bits_per_raw_sample='24',
                                                sample_rate='96000', tags=dict(ALBUM='Stream tags'))])
        info = probe(path, runner=lambda *a, **k: SimpleNamespace(returncode=0, stdout=json.dumps(ogg), stderr=''))
        self.assertEqual((info.tags['album'], info.bit_depth), ('Stream tags', 24))
        self.assertEqual(quality([info]), 'FLAC 24-bit/96 kHz')
        fail = lambda *a, **k: SimpleNamespace(returncode=1, stdout='', stderr='Invalid data')
        self.assertEqual(probe(path, runner=fail).probe_error, 'Invalid data')
        def boom(*a, **k): raise OSError('no ffprobe')
        self.assertIn('no ffprobe', probe(path, runner=boom).probe_error)

    def test_quality_labels(self):
        vbr = [ScanFile('a', codec='mp3', bitrate=245000), ScanFile('b', codec='mp3', bitrate=210000)]
        self.assertEqual(quality(vbr), 'MP3 ~228 kbps')
        mixed = [ScanFile('a', codec='flac', bit_depth=16, sample_rate=44100), ScanFile('b', codec='mp3', bitrate=320000),
                 ScanFile('c', codec='flac', bit_depth=16, sample_rate=44100)]
        self.assertEqual(quality(mixed), 'FLAC 16-bit/44.1 kHz (mixed)')


class PlayerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.tracks = []
        for n in (1, 2):
            path = self.root / 'album' / f'0{n}.flac'; path.parent.mkdir(exist_ok=True); path.write_bytes(b'x')
            self.tracks.append(SimpleNamespace(id=f'f{n}', path=str(path), title=f'Song {n}', duration=61.4))

    def test_playlist_and_launch(self):
        calls = []
        argv = launch_album('', self.tracks, self.root / 'playlists', popen=lambda argv, **kw: calls.append((argv, kw)))
        playlist = self.root / 'playlists' / 'now-playing.m3u8'
        self.assertEqual(playlist.read_text().splitlines(),
                         ['#EXTM3U', '#EXTINF:61,Song 1', self.tracks[0].path, '#EXTINF:61,Song 2', self.tracks[1].path])
        self.assertEqual(argv[-1], str(playlist))
        self.assertTrue(calls[0][1]['start_new_session'])
        self.assertFalse(any((self.root / 'album').glob('*.m3u*')))   # nothing written beside the music

    def test_command_placeholders(self):
        files = [t.path for t in self.tracks]
        sh = '/bin/sh'
        self.assertEqual(build_command(sh, 'P', files), [sh, *files])
        self.assertEqual(build_command(f'{sh} --x {{playlist}}', 'P', files), [sh, '--x', 'P'])
        self.assertEqual(build_command(f'{sh} {{files}} --end', 'P', files), [sh, *files, '--end'])
        self.assertEqual(build_command(f'{sh} {{file}}', 'P', files), [sh, files[0]])
        with self.assertRaises(PlayerError):
            build_command('/nonexistent/player', 'P', files)

    def test_missing_files_and_relocation_matching(self):
        Path(self.tracks[1].path).unlink()
        with self.assertRaises(PlayerError) as ctx:
            launch_album('', self.tracks, self.root / 'playlists', popen=lambda *a, **k: None)
        self.assertIn('1 of 2', str(ctx.exception))
        new = self.root / 'new' / 'Album'; (new / 'sub').mkdir(parents=True)
        (new / '01.flac').write_bytes(b'x'); (new / 'sub' / '02.flac').write_bytes(b'x')
        moves, missing = match_moved(self.tracks, self.root / 'new')
        self.assertEqual((moves, missing), ({'f1': str(new / '01.flac'), 'f2': str(new / 'sub' / '02.flac')}, []))
        write_playlist(self.root / 'p', [])


if __name__ == '__main__':
    unittest.main()
