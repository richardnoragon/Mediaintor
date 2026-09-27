"""Package safety and installation checks using disposable user directories."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parent.parent

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/file)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

installer=module('package_installer','tools/package_install.py')
builder=module('package_builder','tools/build_package.py')

class PackagingTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='mediainator-package-')
        self.root=Path(self.tmp.name)
        self.archive,_=builder.build(self.root/'bundle')
    def tearDown(self):self.tmp.cleanup()
    def test_repeatable_build_and_inventory(self):
        other,digest=builder.build(self.root/'second')
        self.assertEqual(self.archive.read_bytes(),other.read_bytes())
        files,manifest=installer.read_bundle(other)
        self.assertFalse(any('test_data' in p or '__pycache__' in p for p in files))
        self.assertIn('NOTICES.txt',files)
    def test_archive_rejects_traversal_symlinks_duplicate_and_corruption(self):
        for kind in ('traversal','symlink','duplicate','corrupt'):
            target=self.root/(kind+'.tgz')
            with tarfile.open(self.archive) as src,tarfile.open(target,'w:gz') as out:
                for member in src:
                    data=src.extractfile(member).read()
                    if kind=='corrupt' and member.name=='run.py':data=b'x'*len(data)
                    out.addfile(member,io.BytesIO(data))
                extra=tarfile.TarInfo('../escape' if kind=='traversal' else 'run.py')
                if kind=='symlink':extra.type=tarfile.SYMTYPE;extra.linkname='/tmp/escape'
                if kind!='corrupt':out.addfile(extra,io.BytesIO())
            with self.assertRaises(ValueError):installer.read_bundle(target)
    def test_runtime_mismatch_fails(self):
        required=json.loads((ROOT/'packaging/runtime.json').read_text());required['python']='0.0.0'
        with self.assertRaisesRegex(ValueError,'Unverified runtime'):installer.check_runtime(required)
    def test_desktop_exec_escaping(self):
        value=installer.desktop_quote('/tmp/a $b "c" \\ d%/app')
        self.assertIn('%%',value);self.assertTrue(value.startswith('"'))
    def test_install_smoke_reinstall_uninstall_preserves_data(self):
        home=self.root/'Personal space ü $cash';home.mkdir()
        env=dict(os.environ,HOME=str(home),XDG_DATA_HOME=str(home/'data'),XDG_CONFIG_HOME=str(home/'config'),XDG_CACHE_HOME=str(home/'cache'),QT_QPA_PLATFORM='offscreen')
        command=['/usr/bin/python3','-I','-B',str(ROOT/'tools/package_install.py')]
        def run(*args,okay=True):
            result=subprocess.run(command+list(args),env=env,capture_output=True,text=True,timeout=60)
            if okay:self.assertEqual(result.returncode,0,result.stderr)
            else:self.assertNotEqual(result.returncode,0)
            return result
        run('install',str(self.archive))
        saved=home/'data'/'retained-recovery.json';saved.write_text('preserved work')
        launcher=home/'.local/bin/mediainator'
        result=subprocess.run([str(launcher),'--package-smoke'],env=dict(env,PYTHONPATH='/nonexistent',QT_PLUGIN_PATH='/nonexistent'),cwd='/tmp',capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertTrue(json.loads(result.stdout)['application_imported'])
        desktop=home/'data/applications/mediainator.desktop'
        valid=subprocess.run(['desktop-file-validate',str(desktop)],capture_output=True,text=True)
        self.assertEqual(valid.returncode,0,valid.stdout+valid.stderr)
        run('install',str(self.archive))
        # A complete but broken next artifact must not replace the working release.
        payload,manifest=installer.read_bundle(self.archive)
        payload['run.py']=b'raise RuntimeError("deliberate package import failure")\n'
        hashes={k:installer.digest(v) for k,v in sorted(payload.items()) if k!='manifest.json'}
        manifest['files']=hashes
        manifest['build_id']=installer.digest(json.dumps(hashes,sort_keys=True).encode())[:16]
        payload['manifest.json']=(json.dumps(manifest)+'\n').encode()
        broken=self.root/'broken.tgz'
        with tarfile.open(broken,'w:gz') as out:
            for name,data in payload.items():
                item=tarfile.TarInfo(name);item.size=len(data);out.addfile(item,io.BytesIO(data))
        before=(home/'.local/share/mediainator-install/installation.json').read_bytes()
        run('install',str(broken),okay=False)
        self.assertEqual((home/'.local/share/mediainator-install/installation.json').read_bytes(),before)
        self.assertEqual(subprocess.run([str(launcher),'--package-check'],env=env,capture_output=True).returncode,0)
        # A running installed process holds this lock, blocking mutations.
        import fcntl
        with (home/'.local/share/mediainator-install/install.lock').open('a') as held:
            fcntl.flock(held,fcntl.LOCK_SH)
            run('uninstall','--yes',okay=False)
        original=launcher.read_bytes();launcher.write_bytes(original+b'# modified\n')
        run('uninstall','--yes',okay=False)
        self.assertEqual(saved.read_text(),'preserved work')
        launcher.write_bytes(original)
        run('uninstall','--yes')
        self.assertFalse(launcher.exists());self.assertFalse(desktop.exists())
        self.assertEqual(saved.read_text(),'preserved work')
        run('install',str(self.archive))
        self.assertEqual(saved.read_text(),'preserved work')
        run('uninstall','--yes')
    def test_symlink_directory_refused(self):
        real=self.root/'real';real.mkdir();link=self.root/'link';link.symlink_to(real)
        with self.assertRaises(ValueError):installer.safe_directory(link/'nested')

if __name__=='__main__':unittest.main()
