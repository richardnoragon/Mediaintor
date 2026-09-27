import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch,Mock
from mediainator.compatibility import Service,Result,CompatibilityError,require_helper_version
from mediainator import compatibility
REAL_PROBE=compatibility.probe_version

class CompatibilityTests(unittest.TestCase):
    def setUp(self):
        for name,value in [('runtime_problem',''),('signature',('original',)),('probe_version','9.2.1')]:
            p=patch('mediainator.compatibility.'+name,return_value=value);setattr(self,name,p.start());self.addCleanup(p.stop)
        self.service=Service()
    def test_verified_cache_rechecks_identity(self):
        self.assertTrue(self.service.check().verified);self.assertEqual(self.probe_version.call_count,4)
        self.assertTrue(self.service.check().verified);self.assertEqual(self.probe_version.call_count,4)
        self.signature.return_value=('replaced',);self.probe_version.return_value='9.3.0'
        self.assertFalse(self.service.check().verified);self.assertEqual(self.probe_version.call_count,8)
    def test_old_new_and_mixed_versions_block(self):
        for version in ['8.2.0','10.0.0']:
            self.probe_version.return_value=version
            result=self.service.check(force=True);self.assertEqual(result.state,'unverified');self.assertIn(version,result.message)
        self.probe_version.side_effect=['9.2.1','9.2.0','9.2.1','9.2.1']
        self.assertEqual(self.service.check(force=True).state,'inconsistent-toolchain')
    def test_missing_failed_and_runtime_block(self):
        self.signature.side_effect=FileNotFoundError()
        self.assertEqual(self.service.check().state,'missing')
        self.signature.side_effect=None;self.probe_version.side_effect=ValueError('bad output')
        self.assertEqual(self.service.check().state,'probe-failed')
        self.runtime_problem.return_value='wrong runtime'
        self.assertEqual(self.service.check().state,'unverified')
    def test_changed_during_probe_blocks(self):
        self.signature.side_effect=[('before',),('after',)]
        self.assertEqual(self.service.check().state,'probe-failed')
    def test_boundaries_block_before_library_or_process(self):
        with patch('mediainator.compatibility.require_compatible',side_effect=CompatibilityError('blocked')):
            from mediainator.metadata import run_request
            from mediainator.imports import call_helper
            from mediainator.snapshot import Snapshot
            for call in [lambda:run_request('/missing',{},'/missing'),lambda:call_helper({}),lambda:Snapshot('/missing')]:
                with self.assertRaisesRegex(CompatibilityError,'blocked'):call()
    def test_helper_guard_before_database_import(self):
        import sys,types
        calibre=types.ModuleType('calibre');constants=types.ModuleType('calibre.constants');constants.__version__='10.0.0'
        with patch.dict(sys.modules,{'calibre':calibre,'calibre.constants':constants}):
            with self.assertRaises(CompatibilityError):require_helper_version()
            from mediainator.calibre_metadata_helper import execute
            with self.assertRaises(CompatibilityError):execute({})
    def test_version_parser_rejects_noise_and_timeout(self):
        import subprocess
        with patch('mediainator.compatibility.subprocess.run',return_value=Mock(returncode=0,stdout=b'calibredb (calibre 9.2.1)\n')):
            self.assertEqual(REAL_PROBE('calibredb'),'9.2.1')
        with patch('mediainator.compatibility.subprocess.run',return_value=Mock(returncode=0,stdout=b'garbage 9.2.1')):
            with self.assertRaises(ValueError):REAL_PROBE('calibredb')
        self.probe_version.side_effect=subprocess.TimeoutExpired('probe',8)
        self.assertEqual(self.service.check().state,'probe-failed')
        self.assertIn('no override',Result('unverified','10','blocked').message.lower())

class GuidanceTests(unittest.TestCase):
    def test_first_run_block_and_recheck_do_not_resume_work(self):
        from PyQt6.QtWidgets import QApplication
        from mediainator.settings import SettingsStore
        from mediainator.window import Hub
        app=QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as temp:
            store=SettingsStore(Path(temp)/'settings.json')
            hub=Hub(store,store.load(),live=True)
            hub.prerequisites.checked(Result('missing','missing','Install prerequisite.'))
            self.assertFalse(hub.prerequisites.choose.isEnabled())
            self.assertFalse(hub.bookinator.import_button.isEnabled())
            self.assertIn('metadata.db',hub.prerequisites.guide.text())
            with patch.object(hub,'open_books') as opening:
                hub.prerequisites.checked(Result('verified','9.2.1','Ready.'))
                opening.assert_not_called()
            self.assertTrue(hub.prerequisites.choose.isEnabled())
            self.assertIsNotNone(hub.recovery_store)
            hub.close()
    def test_loader_blocks_without_starting_process(self):
        from PyQt6.QtWidgets import QApplication
        from mediainator.library import LibraryLoader
        app=QApplication.instance() or QApplication([])
        loader=LibraryLoader(Path('/missing'));errors=[];loader.failed.connect(errors.append)
        with patch('mediainator.compatibility.require_compatible',side_effect=CompatibilityError('blocked')),patch.object(loader.process,'start') as start:
            loader.load();start.assert_not_called()
        self.assertEqual(errors,['blocked'])
