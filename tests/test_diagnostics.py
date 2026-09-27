import json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from PyQt6.QtWidgets import QApplication
from mediainator import diagnostics as d
from mediainator.settings import SettingsStore
from mediainator.window import Hub

APP=QApplication.instance() or QApplication([])
SECRET='PRIVATE_雪_book_author_ISBN_/home/person/library_recovery'

class DiagnosticsTests(unittest.TestCase):
    def setUp(self):
        with d._lock:d._events.clear();d._dropped=0
        p=patch('mediainator.diagnostics.kde_version',return_value='6.6.6');p.start();self.addCleanup(p.stop)
    def test_arbitrary_values_and_nested_data_never_exported(self):
        with patch('mediainator.diagnostics.platform.freedesktop_os_release',return_value={'ID':SECRET,'VERSION_ID':SECRET}),patch('mediainator.diagnostics.platform.python_version',return_value=SECRET),patch('mediainator.diagnostics.importlib.metadata.version',return_value=SECRET):
            report=d.collect_snapshot({'library_configured':SECRET,'profile':SECRET,'logs':{'message':SECRET},'environment':os.environ,'bookinator_open':True},SECRET,SECRET)
        text=report.payload.decode();self.assertNotIn('PRIVATE',text);self.assertNotIn('/home',text)
        parsed=json.loads(text);self.assertEqual(parsed['features'],{'bookinator_open':True});self.assertEqual(parsed['environment_validation']['last_ui_check'],'not-checked')
    def test_exception_messages_locals_paths_and_chains_excluded(self):
        local_private=SECRET
        try:
            try:raise ValueError(local_private)
            except ValueError as cause:raise RuntimeError(SECRET) from cause
        except RuntimeError as exc:d.record_error(SECRET,exc)
        text=d.collect_snapshot().payload.decode();self.assertNotIn('PRIVATE',text);self.assertNotIn('/home',text)
        event=json.loads(text)['events'][0];self.assertEqual(event['code'],'operation-failure');self.assertEqual(event['category'],'RuntimeError');self.assertGreater(event['omitted_frames'],0)
    def test_only_safe_app_frames_survive(self):
        from mediainator.metadata import run_request
        with patch('mediainator.compatibility.require_compatible',side_effect=RuntimeError(SECRET)):
            try:run_request('/missing',{},'/private')
            except RuntimeError as exc:d.record_error('metadata-failure',exc)
        event=json.loads(d.collect_snapshot().payload)['events'][0]
        self.assertTrue(any(f['module']=='mediainator.metadata' and f['function']=='run_request' for f in event['frames']))
        self.assertNotIn('PRIVATE',json.dumps(event))
        self.assertTrue(all(set(frame)=={'module','function','line'} for frame in event['frames']))
    def test_bounded_session_log_and_fixed_messages(self):
        for i in range(75):d.record_operation(SECRET,'failure')
        parsed=json.loads(d.collect_snapshot().payload)
        self.assertEqual(len(parsed['events']),50);self.assertEqual(parsed['omissions']['older_session_events'],25)
        self.assertNotIn('PRIVATE',json.dumps(parsed))
    def test_exact_calibre_versions_only(self):
        detected='calibre 9.2.1, calibredb 9.2.1, calibre-debug 9.2.1, ebook-viewer 9.2.1'
        self.assertEqual(len(json.loads(d.collect_snapshot(detected=detected).payload)['versions']['Calibre_tools_at_last_check']),4)
        self.assertEqual(json.loads(d.collect_snapshot(detected=detected+SECRET).payload)['versions']['Calibre_tools_at_last_check'],{})
    def test_atomic_permissions_and_failed_replace_preserves_original(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'report.json';path.write_text('original');os.chmod(path,0o644)
            snapshot=d.collect_snapshot()
            with patch('mediainator.diagnostics.os.replace',side_effect=OSError(SECRET)):
                with self.assertRaises(OSError):d.write_snapshot(path,snapshot)
            self.assertEqual(path.read_text(),'original');self.assertEqual(list(Path(folder).iterdir()),[path])
            d.write_snapshot(path,snapshot);self.assertEqual(path.read_bytes(),snapshot.payload)
            self.assertEqual(path.stat().st_mode & 0o777,0o600)
            link=Path(folder)/'link';link.symlink_to(path)
            with self.assertRaises(ValueError):d.write_snapshot(link,snapshot)
    def test_preview_cancel_failure_retry_and_freeze(self):
        with tempfile.TemporaryDirectory() as folder:
            store=SettingsStore(Path(folder)/'settings.json');hub=Hub(store,store.load())
            with patch('socket.socket',side_effect=AssertionError('network access')),patch('mediainator.compatibility.service.check',side_effect=AssertionError('probe')):
                hub.show_diagnostics();dialog=hub.diagnostics_dialog
            original=dialog.snapshot.payload
            self.assertEqual(dialog.preview.toPlainText().encode(),original)
            d.record_error('reader-failure',RuntimeError(SECRET))
            with patch('mediainator.diagnostics_ui.QFileDialog.getSaveFileName',return_value=('','')):dialog.export()
            self.assertIn('cancelled',dialog.status.text());self.assertEqual(dialog.snapshot.payload,original)
            target=Path(folder)/'export.json'
            with patch('mediainator.diagnostics_ui.QFileDialog.getSaveFileName',return_value=(str(target),'')),patch('mediainator.diagnostics_ui.write_snapshot',side_effect=OSError(SECRET)):
                dialog.export();self.assertIn('Export failed',dialog.status.text());self.assertNotIn('PRIVATE',dialog.status.text())
            self.assertFalse(target.exists())
            with patch('mediainator.diagnostics_ui.QFileDialog.getSaveFileName',return_value=(str(target),'')):dialog.export()
            self.assertEqual(target.read_bytes(),original);self.assertEqual(dialog.snapshot.payload,original)
            hub.close();self.assertFalse(dialog.isVisible())
    def test_activity_records_fixed_code_not_details(self):
        from mediainator.activity import ActivityBridge
        from unittest.mock import Mock
        bridge=ActivityBridge(Mock(),lambda message:None)
        bridge.record('Settings save',SECRET,outcome='failure',details={'error':SECRET},source={'path':SECRET})
        report=d.collect_snapshot().payload.decode();self.assertIn('settings-failure',report);self.assertNotIn('PRIVATE',report)
