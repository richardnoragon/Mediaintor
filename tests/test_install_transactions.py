"""Terminate isolated installers between durable steps and explicitly repair."""
import json,os,subprocess,tempfile,unittest
from pathlib import Path
from test_packaging import builder
ROOT=Path(__file__).resolve().parent.parent

class TransactionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='mediainator-transaction-');self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.home=self.root/'user';self.home.mkdir()
        self.env=dict(os.environ,HOME=str(self.home),XDG_CONFIG_HOME=str(self.home/'config'),XDG_DATA_HOME=str(self.home/'data'),QT_QPA_PLATFORM='offscreen')
        self.archive,_=builder.build(self.root/'bundle');self.installer=ROOT/'tools/package_install.py'
        self.base=self.home/'.local/share/mediainator-install'
    def run_cli(self,*args):
        return subprocess.run(['/usr/bin/python3','-I','-B',str(self.installer),*map(str,args)],env=self.env,capture_output=True,text=True,timeout=45)
    def crash(self,action,point):
        code='''
import importlib.util,os,sys
from pathlib import Path
spec=importlib.util.spec_from_file_location('installer',sys.argv[1]);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
point=sys.argv[4]
if point=='uninstall':
 original=Path.unlink
 def unlink(p,*a,**kw):
  original(p,*a,**kw)
  if p.name=='mediainator.desktop':os._exit(75)
 Path.unlink=unlink
elif point=='current':
 original=os.replace
 def replace(a,b):
  original(a,b)
  if Path(b).name=='current':os._exit(75)
 os.replace=replace
else:
 original=m.atomic
 def atomic(p,*args,**kwargs):
  original(p,*args,**kwargs)
  if p.name==point:os._exit(75)
 m.atomic=atomic
m.run(sys.argv[2],Path(sys.argv[3]),True)
'''
        r=subprocess.run(['/usr/bin/python3','-I','-B','-c',code,str(self.installer),action,str(self.archive),point],env=self.env,capture_output=True,text=True,timeout=45)
        self.assertEqual(r.returncode,75,r.stderr)
    def test_install_interruptions_repair_and_repeat(self):
        for point in ['mediainator.desktop','installation.json','current']:
            self.crash('install',point)
            self.assertTrue((self.base/'transaction.json').exists())
            launch=subprocess.run([str(self.home/'.local/bin/mediainator'),'--package-check'],env=self.env,capture_output=True,text=True)
            self.assertNotEqual(launch.returncode,0)
            if point=='mediainator.desktop':self.crash('repair','installation.json')
            self.assertNotEqual(self.run_cli('install',self.archive).returncode,0)
            repair=self.run_cli('repair');self.assertEqual(repair.returncode,0,repair.stderr)
            self.assertFalse((self.base/'transaction.json').exists())
            self.assertEqual(self.run_cli('repair').returncode,0)
            self.assertEqual(self.run_cli('uninstall','--yes').returncode,0)
    def test_uninstall_interrupt_repair_retains_data(self):
        self.assertEqual(self.run_cli('install',self.archive).returncode,0)
        recovery=self.home/'data'/'recovery.json';recovery.write_text('precious pending edits')
        self.crash('uninstall','uninstall')
        repair=self.run_cli('repair');self.assertEqual(repair.returncode,0,repair.stderr)
        self.assertEqual(recovery.read_text(),'precious pending edits')
        self.assertFalse((self.base/'current').exists())
        self.assertEqual(self.run_cli('install',self.archive).returncode,0)
    def test_repair_refuses_modified_file(self):
        self.crash('install','installation.json')
        launch=self.home/'.local/bin/mediainator';launch.write_text('user changed this')
        self.assertNotEqual(self.run_cli('repair').returncode,0)
        self.assertEqual(launch.read_text(),'user changed this')
        self.assertTrue((self.base/'transaction.json').exists())
