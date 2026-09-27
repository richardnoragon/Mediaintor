import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PyQt6.QtWidgets import QApplication
from mediainator.settings import SettingsStore, SettingsError, defaults, appearance_defaults, validate
from mediainator.appearance import AppearanceController, AppearanceDialog, SCALES, ACCENTS
from mediainator.modules import MODULES, launch_module
from mediainator.window import Hub

APP = QApplication.instance() or QApplication([])

class M16Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.store = SettingsStore(Path(self.temp.name)/'settings.json')
        self.state = defaults(); self.store.save(self.state)
        self.controller = AppearanceController(self.store, self.state)
        self.addCleanup(self.controller.deleteLater)
        self.addCleanup(lambda: self.controller.apply(appearance_defaults()))

    def test_legacy_and_invalid_settings_preserved(self):
        self.assertNotIn('appearance', self.store.load())
        for invalid in ({}, dict(appearance_defaults(), size='Huge'), []):
            with self.assertRaises(SettingsError):
                validate(dict(self.state, appearance=invalid))
        self.assertNotIn('appearance', self.store.load())

    def test_failure_rollback_and_retry_preserves_other_changes(self):
        first = dict(appearance_defaults(), theme='Dark')
        self.controller.change(first)
        dialog = AppearanceDialog(self.controller); self.addCleanup(dialog.deleteLater)
        requested = dict(first, size='Large')
        before = self.store.path.read_bytes()
        with patch.object(self.store, 'save', side_effect=SettingsError('disk full')):
            with self.assertRaises(SettingsError): self.controller.change(requested)
        self.assertEqual(self.store.path.read_bytes(), before)
        self.assertEqual(self.state['appearance'], first)
        self.assertEqual(dialog.controls['size'].currentText(), 'Default')
        self.state['view'] = 'List'
        self.controller.change(requested)
        self.assertEqual(self.store.load()['view'], 'List')
        self.assertEqual(self.store.load()['appearance'], requested)

    def test_sizes_not_cumulative_and_reset_preserves_identity(self):
        original = dict(self.state)
        for size in ('Large','Small','Extra Large','Default') * 3:
            self.controller.change(dict(appearance_defaults(), size=size))
        self.assertAlmostEqual(APP.font().pointSizeF(), self.controller.font.pointSizeF())
        self.assertEqual({k:v for k,v in self.state.items() if k != 'appearance'}, original)

    def test_palette_combinations(self):
        from PyQt6.QtGui import QPalette
        for index in range(24):
            theme = ('Light','Dark','System')[index % 3]
            accent = ('System', *ACCENTS)[index % 6]
            size = tuple(SCALES)[index % 4]
            density = ('Compact','Normal','Comfortable')[(index // 3) % 3]
            self.controller.apply(dict(theme=theme, accent=accent, size=size, density=density))
            self.assertNotEqual(APP.palette().color(QPalette.ColorRole.Highlight), APP.palette().color(QPalette.ColorRole.HighlightedText))

    def test_failed_reset_and_cancel(self):
        from PyQt6.QtWidgets import QMessageBox
        chosen = dict(appearance_defaults(), theme='Dark', size='Large')
        self.controller.change(chosen)
        dialog = AppearanceDialog(self.controller); self.addCleanup(dialog.deleteLater)
        with patch('mediainator.appearance.QMessageBox.question', return_value=QMessageBox.StandardButton.Cancel):
            dialog.reset()
        self.assertEqual(self.store.load()['appearance'], chosen)
        with patch.object(self.store, 'save', side_effect=SettingsError('disk full')):
            for _ in range(2):
                with self.assertRaises(SettingsError): self.controller.change(appearance_defaults())
        self.assertEqual(self.controller.saved, chosen)
        self.assertEqual(dialog.controls['size'].currentText(), 'Large')

    def test_registry_and_hub_settings_without_bookinator(self):
        self.state['bookinator_open'] = False
        hub = Hub(self.store, self.state); self.addCleanup(hub.deleteLater)
        self.assertIsNone(hub.bookinator)
        hub.show_appearance()
        self.assertIsNotNone(hub.appearance_dialog)
        for module in MODULES:
            if not module.available:
                self.assertFalse(hub.module_tiles[module.id].isEnabled())
                self.assertFalse(launch_module(module.id, hub))
        self.assertFalse(launch_module('videoinator', hub))
        launch_module('bookinator', hub); book = hub.bookinator
        launch_module('bookinator', hub)
        self.assertIs(hub.bookinator, book); self.assertEqual(hub.tabs.count(), 2)
        hub.close_tab(1); self.assertEqual(hub.tabs.count(), 1)
        hub.close()


class PlaceholderContrastTests(unittest.TestCase):
    def test_existing_and_new_fields_follow_theme_with_readable_placeholder(self):
        from PyQt6.QtWidgets import QLineEdit
        from PyQt6.QtGui import QPalette
        def luminance(color):
            values = (color.redF(), color.greenF(), color.blueF())
            linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in values]
            return sum(a*b for a,b in zip(linear, (.2126,.7152,.0722)))
        with tempfile.TemporaryDirectory() as temp:
            store = SettingsStore(Path(temp)/'settings.json')
            controller = AppearanceController(store, defaults())
            existing = QLineEdit(); existing.setPlaceholderText('Find by title, author or series')
            try:
                for theme in ('Dark', 'Light', 'System', 'Dark'):
                    controller.apply(dict(appearance_defaults(), theme=theme))
                    new = QLineEdit(); new.setPlaceholderText('Search')
                    for field in (existing, new):
                        field.ensurePolished()
                        for group in (QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive, QPalette.ColorGroup.Disabled):
                            palette = field.palette()
                            text = palette.color(group, QPalette.ColorRole.PlaceholderText)
                            base = palette.color(group, QPalette.ColorRole.Base)
                            bright, dim = sorted((luminance(text), luminance(base)), reverse=True)
                            self.assertEqual(text.alpha(), 255)
                            self.assertGreaterEqual((bright + .05)/(dim + .05), 4.5, (theme, group))
                    new.deleteLater()
            finally:
                controller.apply(appearance_defaults())
                existing.deleteLater(); controller.deleteLater()
