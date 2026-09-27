import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PyQt6.QtWidgets import QApplication
from mediainator.help_ui import HelpDialog,TOPICS,read_topic,about_text
from mediainator.settings import SettingsStore
from mediainator.window import Hub

APP=QApplication.instance() or QApplication([])

class HelpTests(unittest.TestCase):
    def test_all_topics_offline_and_search_wraps(self):
        with patch('mediainator.compatibility.service.check',side_effect=AssertionError('Help must not probe dependencies')):
            dialog=HelpDialog()
            for topic in TOPICS:
                dialog.topics.setCurrentText(topic)
                self.assertGreater(len(dialog.browser.toPlainText()),500)
            dialog.topics.setCurrentText('User guide');dialog.search.setText('Calibre')
            dialog.find_next();self.assertEqual(dialog.notice.text(),'Match selected.')
            dialog.search.setText('no-such-text-93839');dialog.find_next();self.assertIn('not found',dialog.notice.text())
            self.assertFalse(dialog.browser.openExternalLinks());self.assertFalse(dialog.browser.openLinks());dialog.close()
    def test_missing_help_has_actionable_fallback(self):
        with tempfile.TemporaryDirectory() as folder,patch('mediainator.help_ui.documentation_root',return_value=Path(folder)):
            self.assertIn('Keep your settings and recovery data',read_topic('User guide'))
    def test_help_reuse_and_hub_close(self):
        with tempfile.TemporaryDirectory() as folder:
            store=SettingsStore(Path(folder)/'settings.json');hub=Hub(store,store.load());hub.show()
            hub.show_help();first=hub.help_dialog
            hub.show_help('Troubleshooting');self.assertIs(first,hub.help_dialog)
            self.assertEqual(first.topics.currentText(),'Troubleshooting')
            hub.close();self.assertFalse(first.isVisible())
    def test_about_matches_project_version(self):
        import tomllib
        from mediainator import __version__
        project=Path(__file__).resolve().parent.parent
        self.assertEqual(__version__,tomllib.loads((project/'pyproject.toml').read_text())['project']['version'])
        self.assertIn(__version__,about_text());self.assertIn('Build:',about_text())
