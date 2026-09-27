import tempfile,unittest
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from mediainator.catalog import Book,find_books
from mediainator.settings import SettingsStore,SettingsError,validate,defaults
from mediainator.window import Hub

class SearchTests(unittest.TestCase):
    def test_categories_and_series(self):
        a=Book('1','Foundation','Asimov',('EPUB',),('Sci-Fi',),reading_status='Reading',series='Empire')
        b=Book('2','Other','Asimov',('PDF',),('Classic',),reading_status='Unknown')
        c=Book('3','Other','Other',('MOBI',),('Sci-Fi',),reading_status='Reading')
        books=(a,b,c)
        self.assertEqual(find_books(books,'asimov',tags=['Sci-Fi','Classic'],formats=['EPUB','PDF'],statuses=['Reading']),[a])
        self.assertEqual(find_books(books,'EMPIRE'),[a])
        self.assertEqual(find_books(books,'',statuses=['Unknown']),[b])
        self.assertEqual(find_books(books,'',tags=['missing']),[])
    def test_persistence_clear_and_selection(self):
        app=QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as d:
            store=SettingsStore(Path(d)/'settings.json'); w=Hub(store,store.load()); p=w.bookinator
            p.bulk_selection={'selected-book'}
            p.search.setText('Wells'); p.filter_changed('formats','EPUB',True); p.filter_toggle.setChecked(False)
            self.assertEqual(len(p.visible),1)
            state=store.load(); self.assertEqual(state['catalog_search']['formats'],['EPUB'])
            w.close(); w.deleteLater()
            w=Hub(store,store.load()); p=w.bookinator
            self.assertEqual(p.search.text(),'Wells'); self.assertFalse(p.filter_toggle.isChecked())
            p.bulk_selection={'selected-book'}; p.clear_search_filters()
            self.assertEqual(len(p.visible),3); self.assertEqual(p.bulk_selection,{'selected-book'})
            self.assertEqual(store.load()['catalog_search']['text'],'')
            p.view.setCurrentText('List'); self.assertEqual(p.table.rowCount(),3)
            w.close(); w.deleteLater(); app.processEvents()
    def test_invalid_persisted_filters_rejected(self):
        data=defaults();data['catalog_search']={'tags':'wrong'}
        with self.assertRaises(SettingsError):validate(data)
