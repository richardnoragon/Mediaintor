import sys,unittest
from pathlib import Path
sys.path.insert(0,'/run/media/sproket01/10d68e7c-8147-49ad-a503-3949560ffcbe/sproket01/Projects/Mediaintor/test_data/m18_m19_review/package/installation/releases/0.1.0a1-f66559012d82aa9f')
import mediainator
assert str(Path(mediainator.__file__).resolve()).startswith('/run/media/sproket01/10d68e7c-8147-49ad-a503-3949560ffcbe/sproket01/Projects/Mediaintor/test_data/m18_m19_review/package/installation/releases/0.1.0a1-f66559012d82aa9f')
suite=unittest.TestSuite()
for pattern in ["test_music_core.py","test_paper_core.py","test_m18_musicinator.py","test_m19_paperinator.py"]:
 suite.addTests(unittest.defaultTestLoader.discover('/run/media/sproket01/10d68e7c-8147-49ad-a503-3949560ffcbe/sproket01/Projects/Mediaintor/tests',pattern=pattern))
r=unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(not r.wasSuccessful())
