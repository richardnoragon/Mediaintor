import os,sys,json,subprocess,shutil
from pathlib import Path
from unittest.mock import patch
root=Path.cwd();sys.path.insert(0,str(root))
from tools import build_package,package_install
base=root/'test_data/m18_m19_review/final_package'
base.mkdir(parents=True,exist_ok=True)
for key,folder in [('XDG_CONFIG_HOME','config'),('XDG_DATA_HOME','data'),('XDG_CACHE_HOME','cache')]: os.environ[key]=str(base/folder)
os.environ['QT_QPA_PLATFORM']='offscreen'
archive,digest=build_package.build(base/'artifact')
install=base/'installation'; launcher=base/'bin/mediainator'; desktop=base/'data/applications/mediainator.desktop'
with patch.object(package_install,'integration_paths',lambda:(install,launcher,desktop)):
 package_install.run('install',archive)
 package_install.run('install',archive)
release=(install/'current').resolve()
checks=[]
for args in [[str(launcher),'--package-smoke'],['desktop-file-validate',str(desktop)]]:
 p=subprocess.run(args,cwd='/tmp',capture_output=True,text=True,timeout=60)
 checks.append(dict(args=args,returncode=p.returncode,output=p.stdout+p.stderr))
 assert p.returncode==0,checks[-1]
# Run tests against installed modules; the checkout is not on Python's import path.
script=base/'run_installed_tests.py'
script.write_text('import sys,unittest\nfrom pathlib import Path\nsys.path.insert(0,'+repr(str(release))+')\nimport mediainator\nassert str(Path(mediainator.__file__).resolve()).startswith('+repr(str(release))+')\nsuite=unittest.TestSuite()\nfor pattern in ["test_music_core.py","test_paper_core.py","test_m18_musicinator.py","test_m19_paperinator.py","test_m19_review_fixes.py"]:\n suite.addTests(unittest.defaultTestLoader.discover('+repr(str(root/'tests'))+',pattern=pattern))\nr=unittest.TextTestRunner(verbosity=2).run(suite)\nsys.exit(not r.wasSuccessful())\n')
p=subprocess.run(['/usr/bin/python3','-I','-B',str(script)],cwd='/tmp',capture_output=True,text=True,timeout=120)
(base/'installed_tests.log').write_text(p.stdout+p.stderr)
checks.append(dict(test='installed M18/M19 tests',returncode=p.returncode))
report=dict(archive=str(archive),sha256=digest,release=str(release),checks=checks,isolation='Real installer and runtime checks; integration_paths redirected to review folder. XDG directories isolated. Not a fresh OS or mount namespace.')
(base/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
