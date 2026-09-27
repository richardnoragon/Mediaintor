import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PyQt6.QtWidgets import QApplication
from mediainator.catalog import SAMPLE_BOOKS, find_books
from mediainator.settings import SettingsError, SettingsStore, defaults
from mediainator.window import Hub

APP = QApplication.instance() or QApplication([])


class FoundationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = SettingsStore(Path(self.temp.name) / "settings.json")

    def test_literal_search_title_author_and_empty(self):
        self.assertEqual([b.id for b in find_books(SAMPLE_BOOKS, "WELLS")], ["sample-time"])
        self.assertEqual([b.id for b in find_books(SAMPLE_BOOKS, "raven")], ["sample-raven"])
        self.assertEqual(find_books(SAMPLE_BOOKS, 'title:"Raven"'), [])
        self.assertEqual(len(find_books(SAMPLE_BOOKS, "")), 3)

    def test_settings_roundtrip_preserves_identity(self):
        state = self.store.load()
        self.store.save(state)
        self.assertEqual(self.store.load(), state)

    def test_bad_settings_are_not_overwritten(self):
        for payload in ('{', json.dumps({"schema_version": 99}), '[]'):
            self.store.path.write_text(payload)
            with self.assertRaises(SettingsError):
                self.store.load()
            self.assertEqual(self.store.path.read_text(), payload)

    def test_failed_atomic_open_preserves_previous_settings(self):
        state = defaults()
        self.store.save(state)
        previous = self.store.path.read_bytes()
        state["view"] = "List"
        with patch('mediainator.settings.QSaveFile') as factory:
            factory.return_value.open.return_value = False
            factory.return_value.errorString.return_value = "test write failure"
            with self.assertRaises(SettingsError):
                self.store.save(state)
        self.assertEqual(self.store.path.read_bytes(), previous)

    def test_shared_views_search_and_restart(self):
        window = Hub(self.store, self.store.load())
        self.addCleanup(window.deleteLater)
        books = window.bookinator
        books.search.setText("Wells")
        self.assertEqual(books.grid.count(), 1)
        self.assertEqual(books.table.rowCount(), 1)
        books.select(0)
        books.view.setCurrentText("List")
        self.assertEqual(books.pages.currentIndex(), 1)
        self.assertEqual(self.store.load()["selected_book"], "sample-time")
        books.search.setText("no such title")
        self.assertEqual(books.grid.count(), 0)
        self.assertIn("No books", books.count.text())
        window.close()
        state = self.store.load()
        self.assertTrue(state["bookinator_open"])
        self.assertEqual(state["view"], "List")
        again = Hub(self.store, state)
        self.addCleanup(again.deleteLater)
        self.assertEqual(again.bookinator.search.text(), "no such title")
        self.assertEqual(again.bookinator.grid.count(), 0)
        again.bookinator.clear_search_filters()
        self.assertEqual(again.bookinator.visible[again.bookinator.grid.currentRow()].id, "sample-time")
        again.close()

    def test_module_close_is_saved_but_hub_close_preserves_selection(self):
        window = Hub(self.store, self.store.load())
        self.addCleanup(window.deleteLater)
        window.close_tab(1)
        self.assertFalse(self.store.load()["bookinator_open"])
        window.close()
        again = Hub(self.store, self.store.load())
        self.addCleanup(again.deleteLater)
        self.assertIsNone(again.bookinator)
        again.open_books()
        again.close()
        self.assertTrue(self.store.load()["bookinator_open"])


if __name__ == '__main__':
    unittest.main()
