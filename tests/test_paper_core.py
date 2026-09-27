"""M19 Paper-inator core: model, profile library store, import planning, adapters. No Qt."""
import os
import sqlite3
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from mediainator.paper_adapters import (AnnotationAdapter, ExternalOpener, PdfInfoExtractor, PdfReaderAdapter,
                                        PdfTextExtractor, ReaderUnavailable, UnavailableReader, validate_command)
from mediainator.paper_import import SOURCE_FILENAME, SOURCE_METADATA, SOURCE_TEXT, discover, plan, propose, revalidate
from mediainator.paper_model import (SAMPLE_LIBRARY, clean_doi, export_markdown, find_items, find_notes, home_sections,
                                     note_excerpt, note_link, safe_filename)
from mediainator.paper_store import ChangedFileError, ConflictError, PaperStore, PaperStoreError, validate_item


class FakeInfo:
    def __init__(self, table=None, present=True):
        self.table, self.present = table or {}, present

    def available(self):
        return self.present

    def extract(self, path):
        return dict(self.table.get(Path(path).name, {}))


class FakeText(FakeInfo):
    def extract(self, path):
        return self.table.get(Path(path).name, '')


def pdf(path, content=b'%PDF-1.4 sample'):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.profile = str(uuid4())
        self.store = PaperStore(self.dir / 'Paper' / 'profiles' / self.profile, self.profile)
        self.store.initialize()
        self.docs = self.dir / 'docs'


class ModelTests(unittest.TestCase):
    def test_doi_cleaning_and_filenames(self):
        self.assertEqual(clean_doi('https://doi.org/10.1000/ABC.123.'), '10.1000/abc.123')
        self.assertEqual(clean_doi('doi: 10.48550/arXiv.1706.03762'), '10.48550/arxiv.1706.03762')
        self.assertEqual(clean_doi('not a doi'), '')
        self.assertEqual(safe_filename('a/b:c*?'), 'a b c')

    def test_find_items_filters_and_sorts(self):
        lib = SAMPLE_LIBRARY
        self.assertEqual([i.title for i in find_items(lib, dict(text='attention vaswani'))], ['Attention Is All You Need'])
        self.assertEqual(len(find_items(lib, dict(handling=['Inbox']))), 2)
        self.assertEqual(len(find_items(lib, dict(handling=['Inbox'], reading=['Reading']))), 1)       # AND across
        self.assertEqual(len(find_items(lib, dict(reading=['Reading', 'Read']))), 2)                    # OR within
        self.assertEqual([i.title for i in find_items(lib, dict(flags=['Key Reference']))], ['Attention Is All You Need'])
        project = lib.projects[0]
        self.assertEqual(len(find_items(lib, dict(container=project.id))), 2)
        self.assertEqual([i.year for i in find_items(lib, dict(sort='Year (oldest first)'))], [2017, 2023, 2024])
        # Words found only in notes still find the item.
        self.assertEqual([i.title for i in find_items(lib, dict(text='why attention works'))], ['Attention Is All You Need'])
        # Document text hits come from the store's index.
        other = lib.items[2]
        self.assertEqual(find_items(lib, dict(text='zzqx'), document_hits={other.id}), [other])

    def test_home_and_notes(self):
        home = home_sections(SAMPLE_LIBRARY)
        self.assertEqual(len(home['inbox']), 2)
        self.assertEqual([i.title for i in home['review']], ['Sample technical report on data sharing'])
        self.assertEqual([p.name for p in home['projects']], ['Literature review'])
        note = SAMPLE_LIBRARY.notes[0]
        self.assertEqual(note.links(), [('item', SAMPLE_LIBRARY.items[0].id)])
        self.assertEqual(find_notes(SAMPLE_LIBRARY, 'attention'), [note])
        self.assertNotIn('paper:item', note_excerpt(note))
        text = export_markdown(note, SAMPLE_LIBRARY)
        self.assertIn('source_doi: 10.48550/arxiv.1706.03762', text)
        self.assertIn('→ Attention Is All You Need (2017)', text)
        self.assertEqual(note_link('item', 'x', 'A [b]'), '[A (b)](paper:item/x)')

    def test_connection_direction(self):
        connection = SAMPLE_LIBRARY.connections[0]
        report, paper = SAMPLE_LIBRARY.items[1].id, SAMPLE_LIBRARY.items[0].id
        self.assertEqual(connection.seen_from('item', report)[0], 'References')
        self.assertEqual(connection.seen_from('item', paper)[0], 'Referenced by')


class StoreTests(Base):
    def test_layout_identity_and_validation(self):
        self.assertTrue(self.store.path.is_file())
        self.assertTrue(self.store.library_uuid())
        with self.assertRaises(PaperStoreError):
            validate_item(dict(title=' '))
        with self.assertRaises(PaperStoreError):
            validate_item(dict(title='x', doi='abc'))
        with self.assertRaises(PaperStoreError):
            validate_item(dict(title='x', url='javascript:alert(1)'))
        with self.assertRaises(PaperStoreError):
            validate_item(dict(title='x', year=99))
        fields = validate_item(dict(title=' T ', authors=['A', 'a', ' '], doi='https://doi.org/10.1000/X',
                                    identifiers=[['arXiv', '1706.03762']]))
        self.assertEqual((fields['title'], fields['authors'], fields['doi']), ('T', ['A'], '10.1000/x'))
        # A failed write changes nothing.
        with self.assertRaises(PaperStoreError):
            self.store.add_item(dict(title='ok'), versions=[dict(kind='Nonsense')])
        self.assertEqual(self.store.load().items, ())

    def test_item_edit_conflict_and_independent_states(self):
        item_id = self.store.add_item(dict(title='Paper', type='Research paper'))
        item = self.store.get_item(item_id)
        self.assertEqual((item.reading, item.handling, item.flags), ('Unread', 'Inbox', ()))
        self.store.update_item(item_id, item.revision, dict(title='Paper v2', authors=['Ada']))
        with self.assertRaises(ConflictError) as caught:
            self.store.update_item(item_id, item.revision, dict(title='Stale'))
        self.assertEqual(caught.exception.current.title, 'Paper v2')
        self.store.set_states([item_id], reading='Read')
        self.store.set_states([item_id], handling='Archived', flags={'Key Reference': True})
        item = self.store.get_item(item_id)
        self.assertEqual((item.reading, item.handling, item.flags), ('Read', 'Archived', ('Key Reference',)))
        self.assertEqual(item.revision, 1)          # states do not count as metadata edits
        self.store.set_states([item_id], handling='Active')
        self.assertEqual(self.store.get_item(item_id).reading, 'Read')   # archiving never resets progress
        with self.assertRaises(PaperStoreError):
            self.store.set_states([item_id], flags={'Nope': True})

    def test_bulk_tags_and_opened(self):
        a = self.store.add_item(dict(title='A', tags=['ml'])); b = self.store.add_item(dict(title='B'))
        self.store.change_tags([a, b], add=['Survey', 'ML'])
        lib = self.store.load()
        self.assertEqual(lib.item(a).tags, ('ml', 'Survey')); self.assertEqual(lib.item(b).tags, ('Survey', 'ML'))
        self.store.change_tags([a, b], remove=['survey'])
        self.assertEqual(self.store.load().item(b).tags, ('ML',))
        self.store.mark_opened(a)
        self.assertTrue(self.store.get_item(a).opened_at)

    def test_versions_and_preferred_version(self):
        item_id = self.store.add_item(dict(title='Work', doi='10.1000/pub'),
                                      versions=[dict(label='arXiv preprint', kind='Preprint', year=2020, doi='10.1000/pre')])
        pre = self.store.get_item(item_id).versions[0]
        self.assertEqual(self.store.get_item(item_id).preferred_version_id, pre.id)
        pub = self.store.add_version(item_id, dict(label='Journal', kind='Published version', year=2021))
        self.store.set_preferred_version(item_id, pub)
        item = self.store.get_item(item_id)
        self.assertEqual((item.preferred_version.label, item.doi), ('Journal', '10.1000/pub'))   # metadata unchanged
        self.assertEqual(item.versions[0].doi, '10.1000/pre')                                   # version details kept
        self.store.remove_version(pub)
        self.assertEqual(self.store.get_item(item_id).preferred_version_id, pre.id)
        other = self.store.add_item(dict(title='Other'))
        with self.assertRaises(PaperStoreError):
            self.store.set_preferred_version(other, pre.id)

    def test_notes_standalone_linked_and_conflicts(self):
        idea = self.store.add_note(dict(title='Idea', body='# Idea\nNo source needed', kind='Research idea'))
        item_id = self.store.add_item(dict(title='Source'))
        summary = self.store.add_note(dict(body='Summary with ' + note_link('item', item_id, 'Source'), kind='Summary',
                                           item_id=item_id))
        lib = self.store.load()
        self.assertIsNone(lib.note(idea).item_id)
        self.assertEqual(lib.notes_of(item_id)[0].id, summary)
        self.assertEqual(lib.note(summary).links(), [('item', item_id)])
        note = lib.note(idea)
        self.store.update_note(idea, note.revision, dict(body='changed'))
        with self.assertRaises(ConflictError):
            self.store.update_note(idea, note.revision, dict(body='stale'))
        with self.assertRaises(PaperStoreError):
            self.store.add_note(dict(kind='Poem'))

    def test_projects_collections_memberships(self):
        a = self.store.add_item(dict(title='A')); n = self.store.add_note(dict(title='N'))
        project = self.store.add_container('project', 'Thesis', 'chapter 2')
        collection = self.store.add_container('collection', 'Reading group')
        with self.assertRaises(PaperStoreError):
            self.store.add_container('project', 'thesis')
        self.assertEqual(self.store.add_members(project, [('item', a), ('note', n), ('item', a)]), 2)
        self.store.add_members(collection, [('item', a)])
        with self.assertRaises(PaperStoreError):
            self.store.add_members(collection, [('note', n)])
        lib = self.store.load()
        self.assertEqual(len(lib.items), 1)                           # no duplication
        self.assertEqual(len(lib.containers_of('item', a)), 2)
        self.store.update_container(project, status='Paused')
        self.store.remove_members(project, [('item', a)])
        lib = self.store.load()
        self.assertEqual(lib.container(project).members, (('note', n),))
        self.assertIsNotNone(lib.item(a))

    def test_connections(self):
        a = self.store.add_item(dict(title='A')); b = self.store.add_item(dict(title='B'))
        n = self.store.add_note(dict(title='N')); p = self.store.add_container('project', 'P')
        c1 = self.store.add_connection(('item', a), 'Extends', ('item', b), 'builds on the method')
        self.store.add_connection(('note', n), 'Supports', ('item', a))
        self.store.add_connection(('item', b), 'Related To', ('project', p))
        with self.assertRaises(PaperStoreError):
            self.store.add_connection(('item', a), 'Extends', ('item', b))
        with self.assertRaises(PaperStoreError):
            self.store.add_connection(('project', p), 'Related To', ('item', b))     # symmetric duplicate
        with self.assertRaises(PaperStoreError):
            self.store.add_connection(('item', a), 'Uses', ('item', a))
        with self.assertRaises(PaperStoreError):
            self.store.add_connection(('item', a), 'Loves', ('item', b))
        lib = self.store.load()
        self.assertEqual(sorted(c.seen_from('item', a)[0] for c in lib.connections_of('item', a)), ['Extends', 'Supported by'])
        self.store.update_connection(c1, relation='Uses', reverse=True)
        lib = self.store.load()
        moved = next(c for c in lib.connections if c.id == c1)
        self.assertEqual((moved.source_id, moved.relation, moved.target_id, moved.comment), (b, 'Uses', a, 'builds on the method'))
        self.store.remove_connection(c1)
        self.assertEqual(len(self.store.load().connections), 2)

    def test_saved_searches(self):
        search = self.store.save_search('To read', dict(reading=['Unread'], sort='Title A–Z'))
        with self.assertRaises(PaperStoreError):
            self.store.save_search('to read', dict())
        self.store.save_search('To read soon', dict(reading=['Unread'], flags=['Needs Review']), search)
        lib = self.store.load()
        self.assertEqual((lib.searches[0].name, lib.searches[0].criteria['flags']), ('To read soon', ['Needs Review']))
        for bad in (dict(reading=['Skimmed']), dict(sort='Random'), dict(unknown=1), dict(tags='x')):
            with self.subTest(bad=bad), self.assertRaises(PaperStoreError):
                self.store.save_search('Bad', bad)
        self.store.delete_search(search)
        self.assertEqual(self.store.load().searches, ())

    def test_profile_isolation_and_foreign_files(self):
        other = PaperStore(self.store.root, str(uuid4()))
        before = self.store.path.read_bytes()
        with self.assertRaises(PaperStoreError) as caught:
            other.load()
        self.assertIn('another profile', str(caught.exception))
        with self.assertRaises(PaperStoreError):
            other.add_item(dict(title='x'))
        self.assertEqual(self.store.path.read_bytes(), before)
        foreign = self.dir / 'foreign'
        foreign.mkdir()
        with sqlite3.connect(foreign / 'library.sqlite') as db:
            db.execute('CREATE TABLE albums(x)')
        stranger = PaperStore(foreign, self.profile)
        for call in (stranger.load, lambda: stranger.add_item(dict(title='x'))):
            with self.assertRaises(PaperStoreError):
                call()
        with sqlite3.connect(self.store.path) as db:
            db.execute("UPDATE meta SET value='9' WHERE key='schema'")
        with self.assertRaises(PaperStoreError):
            self.store.load()
        with self.assertRaises(PaperStoreError):
            PaperStore(self.dir, 'not-a-uuid')


class FileTests(Base):
    def test_managed_copy_keeps_original(self):
        original = pdf(self.docs / 'paper.pdf', b'%PDF managed')
        os.utime(original, (1_000_000, 1_000_000))
        item_id, version_id, file_id = self.store.import_document(
            original, 'managed', item_fields=dict(title='Managed'), text='deep learning\fpage two')
        stored = self.store.get_item(item_id).files[0]
        self.assertEqual((stored.mode, stored.original_path), ('managed', str(original.resolve())))
        self.assertTrue(Path(stored.path).is_file())
        self.assertIn(self.store.files_dir.resolve(), Path(stored.path).resolve().parents)
        self.assertEqual(Path(stored.path).read_bytes(), b'%PDF managed')
        self.assertEqual((original.read_bytes(), original.stat().st_mtime), (b'%PDF managed', 1_000_000))
        self.assertTrue(stored.has_text)
        self.assertEqual(self.store.search_documents('learning'), {item_id})
        self.assertEqual(self.store.search_documents('learn'), {item_id})       # prefix match
        self.assertEqual(self.store.search_documents('absent words'), frozenset())

    def test_document_search_without_fts5(self):
        with sqlite3.connect(self.store.path) as db:
            db.execute("UPDATE meta SET value='0' WHERE key='fts'")
        store = PaperStore(self.store.root, self.profile)
        item_id = store.import_document(pdf(self.docs / 'p.pdf', b'p'), 'referenced', item_fields=dict(title='P'),
                                        text='Quantum Entanglement')[0]
        self.assertEqual(store.search_documents('entangle quantum'), {item_id})
        self.assertEqual(store.search_documents('classical'), frozenset())

    def test_referenced_file_and_duplicates(self):
        original = pdf(self.docs / 'ref.pdf', b'%PDF referenced')
        item_id, _, _ = self.store.import_document(original, 'referenced', item_fields=dict(title='Ref'))
        stored = self.store.get_item(item_id).files[0]
        self.assertEqual((stored.mode, stored.path), ('referenced', str(original.resolve())))
        self.assertFalse(any(p.is_file() for p in self.store.files_dir.rglob('*')) if self.store.files_dir.exists() else False)
        copy = pdf(self.docs / 'copy.pdf', b'%PDF referenced')
        with self.assertRaises(PaperStoreError) as caught:
            self.store.import_document(copy, 'managed', item_fields=dict(title='Dup'))
        self.assertIn('identical file', str(caught.exception))
        self.assertFalse([p for p in self.store.files_dir.rglob('*') if p.is_file()])   # our copy was removed again
        self.assertTrue(copy.exists())
        with self.assertRaises(PaperStoreError):
            self.store.import_document(original, 'referenced', item_fields=dict(title='Again'), allow_duplicate=True)

    def test_changed_after_preview_and_failed_transaction_cleanup(self):
        original = pdf(self.docs / 'a.pdf', b'one')
        with self.assertRaises(PaperStoreError) as caught:
            self.store.import_document(original, 'managed', item_fields=dict(title='A'), expected=(3, 'different'))
        self.assertIn('changed since the preview', str(caught.exception))
        with self.assertRaises(PaperStoreError):
            self.store.import_document(original, 'managed', item_id=str(uuid4()))   # item missing → rollback
        self.assertFalse([p for p in self.store.files_dir.rglob('*') if p.is_file()])
        self.assertEqual(original.read_bytes(), b'one')
        self.assertEqual(self.store.load().items, ())

    def test_add_version_file_and_attachment(self):
        first = pdf(self.docs / 'pre.pdf', b'preprint')
        item_id, pre_version, _ = self.store.import_document(first, 'referenced', item_fields=dict(title='Work'),
                                                             version_fields=dict(label='arXiv', kind='Preprint'))
        pub = pdf(self.docs / 'pub.pdf', b'published')
        _, pub_version, _ = self.store.import_document(pub, 'managed', item_id=item_id,
                                                       version_fields=dict(label='Journal', kind='Published version'))
        data = pdf(self.docs / 'data.csv', b'a,b')
        self.store.add_file(pub_version, data, 'referenced', role='attachment', label='Data')
        item = self.store.get_item(item_id)
        self.assertEqual([v.label for v in item.versions], ['arXiv', 'Journal'])
        self.assertEqual(item.preferred_version_id, pre_version)
        self.assertEqual(item.default_document.path, str(first.resolve()))
        self.store.set_preferred_version(item_id, pub_version)
        item = self.store.get_item(item_id)
        self.assertEqual(Path(item.default_document.path).read_bytes(), b'published')
        self.assertEqual([f.name for f in item.preferred_version.attachments], ['Data'])
        with self.assertRaises(PaperStoreError):
            self.store.remove_version(pub_version)

    def test_relocate_referenced_file(self):
        original = pdf(self.docs / 'old' / 'x.pdf', b'content')
        item_id, _, file_id = self.store.import_document(original, 'referenced', item_fields=dict(title='X'), text='alpha')
        moved = self.docs / 'new' / 'x.pdf'; moved.parent.mkdir(); original.rename(moved)
        self.store.relocate_file(file_id, moved)
        self.assertEqual(self.store.get_item(item_id).files[0].path, str(moved.resolve()))
        self.assertEqual(self.store.search_documents('alpha'), {item_id})
        other = pdf(self.docs / 'other.pdf', b'changed content')
        with self.assertRaises(ChangedFileError):
            self.store.relocate_file(file_id, other)
        self.store.relocate_file(file_id, other, accept_changed=True)
        self.assertEqual(self.store.search_documents('alpha'), frozenset())      # stale text dropped
        managed_id = self.store.import_document(pdf(self.docs / 'm.pdf', b'm'), 'managed', item_fields=dict(title='M'))[2]
        with self.assertRaises(PaperStoreError):
            self.store.relocate_file(managed_id, other)


class TrashTests(Base):
    def populated(self):
        managed = pdf(self.docs / 'managed.pdf', b'managed bytes')
        referenced = pdf(self.docs / 'referenced.pdf', b'referenced bytes')
        item_id, version_id, _ = self.store.import_document(managed, 'managed', item_fields=dict(title='Doomed'), text='zebra')
        self.store.import_document(referenced, 'referenced', item_id=item_id, version_id=version_id)
        self.store.set_states([item_id], reading='Reading', flags={'Favorite': True})
        other = self.store.add_item(dict(title='Survivor'))
        source_note = self.store.add_note(dict(title='About doomed', item_id=item_id))
        independent = self.store.add_note(dict(title='Independent idea'))
        project = self.store.add_container('project', 'Review')
        self.store.add_members(project, [('item', item_id), ('item', other), ('note', independent)])
        self.store.add_connection(('item', item_id), 'Supports', ('item', other))
        self.store.add_connection(('note', independent), 'Contradicts', ('item', item_id))
        return item_id, other, source_note, independent, project, managed, referenced

    def test_trash_restore_keeps_research_context(self):
        item_id, other, source_note, independent, project, managed, referenced = self.populated()
        managed_copy = Path(self.store.get_item(item_id).files[0].path)
        preview = self.store.trash_preview([('item', item_id)])
        self.assertEqual([o[0] for o in preview['objects']], ['item', 'note'])
        self.assertEqual((preview['connections'], preview['memberships']), (2, 1))
        self.assertEqual((len(preview['managed_files']), preview['referenced_files']), (1, [str(referenced.resolve())]))
        batch = self.store.trash([('item', item_id)])
        lib = self.store.load()
        self.assertIsNone(lib.item(item_id)); self.assertIsNone(lib.note(source_note))
        self.assertIsNotNone(lib.note(independent)); self.assertIsNotNone(lib.item(other))    # independent survives
        self.assertEqual(lib.connections_of('item', other), ())                              # hidden, not deleted
        self.assertEqual(lib.container(project).members, (('item', other), ('note', independent)))
        self.assertEqual(self.store.search_documents('zebra'), frozenset())
        self.assertTrue(managed_copy.is_file() and managed.is_file() and referenced.is_file())  # no file touched
        self.assertEqual(lib.trash[0].objects, (('item', item_id), ('note', source_note)))
        self.store.restore(batch)
        lib = self.store.load()
        item = lib.item(item_id)
        self.assertEqual((item.reading, item.favorite), ('Reading', True))
        self.assertEqual(len(lib.connections_of('item', item_id)), 2)
        self.assertIn(('item', item_id), lib.container(project).members)
        self.assertEqual(lib.note(source_note).item_id, item_id)
        self.assertEqual(lib.trash, ())
        self.assertEqual(self.store.search_documents('zebra'), {item_id})

    def test_permanent_deletion_removes_managed_only(self):
        item_id, other, source_note, independent, project, managed, referenced = self.populated()
        managed_copy = Path(self.store.get_item(item_id).files[0].path)
        batch = self.store.trash([('item', item_id)])
        preview = self.store.purge_preview(batch)
        self.assertEqual(preview['managed_files'], [str(managed_copy)])
        self.assertEqual(self.store.purge(batch), [])
        self.assertFalse(managed_copy.exists())
        self.assertTrue(managed.is_file() and referenced.is_file())          # originals and referenced files remain
        lib = self.store.load()
        self.assertEqual((lib.trash, lib.trashed_items, lib.trashed_notes), ((), (), ()))
        self.assertEqual(lib.connections, ())
        self.assertEqual(lib.container(project).members, (('item', other), ('note', independent)))
        self.assertIsNotNone(lib.note(independent))
        with self.assertRaises(PaperStoreError):
            self.store.restore(batch)

    def test_interrupted_purge_is_completed_on_recover(self):
        item_id, *_ = self.populated()
        managed_copy = Path(self.store.get_item(item_id).files[0].path)
        batch = self.store.trash([('item', item_id)])
        real_unlink = Path.unlink
        def failing(path, missing_ok=False):
            if path == managed_copy:
                raise PermissionError('busy')
            return real_unlink(path, missing_ok=missing_ok)
        with patch.object(Path, 'unlink', failing):
            problems = self.store.purge(batch)
        self.assertTrue(problems and managed_copy.exists())
        self.assertEqual(self.store.load().trash[0].state, 'purging')
        with self.assertRaises(PaperStoreError):
            self.store.restore(batch)
        self.assertEqual(self.store.recover(), [])
        self.assertFalse(managed_copy.exists())
        self.assertEqual(self.store.load().trash, ())

    def test_trash_single_note_project_and_file(self):
        item_id, other, source_note, independent, project, *_ = self.populated()
        attachment = self.store.get_item(item_id).files[1]
        b1 = self.store.trash([('note', independent)])
        b2 = self.store.trash([('project', project)])
        b3 = self.store.trash([('file', attachment.id)])
        lib = self.store.load()
        self.assertIsNone(lib.note(independent)); self.assertEqual(lib.projects, ())
        self.assertEqual(len(lib.item(item_id).files), 1)
        with self.assertRaises(PaperStoreError):
            self.store.trash([('note', independent)])
        self.store.add_container('project', 'Review')                  # the name is free while in Trash
        for batch in (b1, b2, b3):
            self.store.restore(batch)
        lib = self.store.load()
        self.assertEqual(sorted(p.name for p in lib.projects), ['Review', 'Review (restored)'])
        self.assertEqual(len(lib.item(item_id).files), 2)
        self.assertEqual(self.store.purge(self.store.trash([('file', attachment.id)])), [])
        self.assertTrue(Path(attachment.path).exists())               # a referenced file is never deleted

    def test_recover_removes_staging_and_reports_orphans(self):
        staging = self.store.files_dir / '.staging'; staging.mkdir(parents=True)
        (staging / 'x.part').write_bytes(b'tmp')
        orphan = self.store.files_dir / 'ab' / 'orphan.pdf'; orphan.parent.mkdir(); orphan.write_bytes(b'o')
        self.store.recover()
        self.assertFalse((staging / 'x.part').exists())
        self.assertEqual(self.store.orphans(), [str(orphan)])
        self.assertTrue(orphan.exists())


class ImportPlanTests(Base):
    def test_discover_and_propose(self):
        pdf(self.docs / 'a' / 'one.pdf'); pdf(self.docs / '.hidden' / 'two.pdf'); pdf(self.docs / 'notes.txt')
        (self.docs / 'link').symlink_to(self.docs / 'a', target_is_directory=True)
        files, skipped = discover([self.docs, self.docs / 'missing.pdf'])
        self.assertEqual([Path(f).name for f in files], ['one.pdf'])
        self.assertEqual(skipped[0][1], 'not found')
        fields, sources = propose('smith_2020_deep-learning.pdf', dict(Title='Microsoft Word - draft.docx', Author='A. Smith; B. Jones'),
                                  'Title\nDOI: 10.1234/ABC.5.\fpage 2 doi 10.9/zzz')
        self.assertEqual((fields['title'], sources['title']), ('smith 2020 deep learning', SOURCE_FILENAME))
        self.assertEqual((fields['authors'], sources['authors']), (['A. Smith', 'B. Jones'], SOURCE_METADATA))
        self.assertEqual((fields['doi'], sources['doi']), ('10.1234/abc.5', SOURCE_TEXT))
        fields, sources = propose('x.pdf', dict(Title='A Real Paper Title'), '')
        self.assertEqual((fields['title'], sources['title']), ('A Real Paper Title', SOURCE_METADATA))
        self.assertNotIn('year', fields)                        # never invented from file dates

    def test_plan_duplicates_versions_and_revalidation(self):
        existing = pdf(self.docs / 'existing.pdf', b'same')
        item_id, _, _ = self.store.import_document(existing, 'referenced', item_fields=dict(title='Known Work Title', doi='10.5555/x'))
        pdf(self.docs / 'in' / 'copy-of-existing.pdf', b'same')
        pdf(self.docs / 'in' / 'preprint.pdf', b'pre')
        pdf(self.docs / 'in' / 'twin1.pdf', b'twin'); pdf(self.docs / 'in' / 'twin2.pdf', b'twin')
        pdf(self.docs / 'in' / 'scan.pdf', b'scan')
        info = FakeInfo({'preprint.pdf': dict(Title='Something else entirely')})
        text = FakeText({'preprint.pdf': 'doi:10.5555/X', 'twin1.pdf': 'text', 'copy-of-existing.pdf': 't'})
        by_hash, by_path = self.store.known_files()
        result = plan([self.docs / 'in', existing], self.store.load(), by_hash, by_path, info_tool=info, text_tool=text)
        names = {Path(p.path).name: p for p in result.proposals}
        self.assertEqual(sorted(names), ['copy-of-existing.pdf', 'preprint.pdf', 'scan.pdf', 'twin1.pdf'])
        self.assertEqual(result.skipped, [(str(existing.resolve()), 'already referenced by the library')])
        self.assertEqual(names['copy-of-existing.pdf'].duplicate[0], item_id)
        self.assertEqual(names['preprint.pdf'].candidates, [(item_id, 'Known Work Title', 'same DOI')])
        self.assertEqual(len(names['twin1.pdf'].also), 1)
        self.assertTrue(any('image-only' in w for w in names['scan.pdf'].warnings))
        self.assertEqual(result.tools, dict(pdfinfo=True, pdftotext=True))
        proposal = names['scan.pdf']
        self.assertEqual(revalidate(proposal), [])
        Path(proposal.path).write_bytes(b'longer now')
        self.assertTrue(revalidate(proposal))
        missing = plan([self.docs / 'in'], self.store.load(), by_hash, by_path,
                       info_tool=FakeInfo(present=False), text_tool=FakeText(present=False))
        self.assertTrue(all(any('pdftotext is not installed' in w for w in p.warnings) for p in missing.proposals))


class AdapterTests(unittest.TestCase):
    def test_reader_contract_is_defined_but_not_implemented(self):
        with self.assertRaises(TypeError):
            PdfReaderAdapter()
        with self.assertRaises(TypeError):
            AnnotationAdapter()
        reader = UnavailableReader()
        for call in (lambda: reader.open_document('x.pdf', 'id'), lambda: reader.page_count(None),
                     lambda: reader.search_text(None, 'x')):
            with self.assertRaises(ReaderUnavailable):
                call()

    def test_poppler_extractors_and_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            tool = Path(tmp) / 'fakeinfo'
            tool.write_text('#!/bin/sh\nprintf "Title:          My Title\\nAuthor:  Ada\\nPages: 3\\n"\n')
            tool.chmod(tool.stat().st_mode | stat.S_IEXEC)
            self.assertEqual(PdfInfoExtractor(str(tool)).extract('x.pdf'), dict(Title='My Title', Author='Ada', Pages='3'))
            text = Path(tmp) / 'faketext'
            text.write_text('#!/bin/sh\nprintf "page one\\fpage two"\n'); text.chmod(0o755)
            self.assertEqual(PdfTextExtractor(str(text)).extract('x.pdf'), 'page one\fpage two')
            broken = Path(tmp) / 'broken'
            broken.write_text('#!/bin/sh\necho "Syntax Error: bad file" >&2\nexit 1\n'); broken.chmod(0o755)
            with self.assertRaises(PaperStoreError):
                PdfTextExtractor(str(broken)).extract('x.pdf')
            self.assertEqual(PdfTextExtractor(None).extract('x.pdf') if not PdfTextExtractor(None).available() else '', '')
        self.assertEqual(validate_command('  '), '')
        self.assertEqual(validate_command('sh -c true'), 'sh -c true')
        for bad in ('no-such-reader-xyz', 'a\x01', 'unterminated "quote'):
            with self.subTest(bad=bad), self.assertRaises(PaperStoreError):
                validate_command(bad)
        with self.assertRaises(PaperStoreError):
            ExternalOpener().open('', '/definitely/missing.pdf')

    def test_external_opener_substitutes_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            document = pdf(Path(tmp) / 'doc.pdf')
            with patch('mediainator.paper_adapters.subprocess.Popen') as popen:
                ExternalOpener().open('sh -c "exit 0" {file}', str(document))
                args = popen.call_args[0][0]
                self.assertEqual(args[-1], str(document))
                self.assertTrue(popen.call_args[1]['start_new_session'])


if __name__ == '__main__':
    unittest.main()
