"""Exercise the real editor/controller lifecycle in its own Qt process."""
import os,subprocess,sys,unittest
from pathlib import Path
class HandoffRegression(unittest.TestCase):
    def test_recovery_editor_lifecycle(self):
        result=subprocess.run([sys.executable,str(Path(__file__).with_name('check_m12_recovery_handoff.py'))],env=dict(os.environ,QT_QPA_PLATFORM='offscreen'),capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
