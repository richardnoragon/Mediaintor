"""Fresh helper interpreters must not add files to an installed release."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

class HelperInstallIntegrityTests(unittest.TestCase):
    def test_helper_imports_preserve_release_inventory(self):
        source=Path(__file__).resolve().parent.parent/'mediainator'
        for helper in ('calibre_metadata_helper.py','calibre_import_helper.py'):
            with self.subTest(helper=helper), tempfile.TemporaryDirectory() as folder:
                target=Path(folder)/'mediainator';target.mkdir()
                for file in source.glob('*.py'):shutil.copy2(file,target/file.name)
                before={p.name:p.read_bytes() for p in target.iterdir()}
                env={k:v for k,v in os.environ.items() if not k.startswith('PYTHON')}
                run=subprocess.run([sys.executable,'-I','-c','import runpy,sys;runpy.run_path(sys.argv[1])',str(target/helper)],env=env,capture_output=True,text=True)
                self.assertEqual(run.returncode,0,run.stderr)
                self.assertEqual({p.name:p.read_bytes() for p in target.iterdir() if p.is_file()},before)
                self.assertFalse(list(target.rglob('*.pyc')))
                self.assertFalse(list(target.rglob('__pycache__')))
