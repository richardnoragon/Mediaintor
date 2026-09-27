"""Verify the M8 installed artifact without mounting the development checkout."""
import hashlib,json,shutil,subprocess,tempfile
from pathlib import Path
root=Path.cwd(); home=Path(tempfile.mkdtemp(prefix='m8-installed-user-',dir='/tmp'))
archive=Path('/tmp/m8-installed-acceptance/artifacts/mediainator-0.1.0a1-ubuntu26.04-x86_64.tar.gz')
shutil.copy2(archive,home/'candidate.tar.gz');shutil.copy2(root/'tools/package_install.py',home/'installer.py')
fixture=json.loads((root/'test_data/m8_usability/integrated_desktop_pending.json').read_text())
state=json.loads((Path(fixture['root'])/'app/settings.json').read_text())
(home/'saved_settings.json').write_text(json.dumps(state))
shutil.copytree(Path(fixture['root'])/'library',home/'library')
scenario=r'''
import os,sys,json,subprocess
from pathlib import Path
home=Path.home(); checks=[]
def run(args):
 p=subprocess.run(args,capture_output=True,text=True,timeout=90)
 if p.returncode:raise RuntimeError(p.stdout+p.stderr)
 return p.stdout
run(['/usr/bin/python3','-I','-B',str(home/'installer.py'),'install',str(home/'candidate.tar.gz')]);checks.append('clean_isolated_install')
launcher=home/'.local/bin/mediainator'
smoke=json.loads(run([str(launcher),'--package-smoke']));assert smoke['application_imported'];checks.append('installed_launcher_smoke')
release=(home/'.local/share/mediainator-install/current').resolve();sys.path.insert(0,str(release))
from PyQt6.QtWidgets import QApplication
from mediainator.settings import SettingsStore
from mediainator.window import Hub
from mediainator.library import parse_catalog
import mediainator
assert str(release) in mediainator.__file__;assert not Path('/run/media').exists();checks.append('installed_modules_only_no_checkout')
raw=run(['/usr/bin/calibredb','list','--with-library',str(home/'library'),'--for-machine','--fields','title,authors,tags,formats,cover,uuid,series'])
books=parse_catalog(home/'library',raw.encode());assert len(books)==101;checks.append('installed_catalog_parser_real_101_book_listing_with_series')
state=json.loads((home/'saved_settings.json').read_text());assert state['catalog_search']['tags']==['Essays','External edit']
store=SettingsStore(home/'ui/settings.json');store.save(state)
app=QApplication([]);w=Hub(store,store.load());panel=w.bookinator;panel.books=books;panel.rebuild_filters();panel.render()
assert panel.filter_values['tags']=={'Essays','External edit'} and panel.filter_toggle.isChecked()
assert panel.search.text()==''
expected={b.id for b in books if set(b.tags)&{'Essays','External edit'}}
assert {b.id for b in panel.visible}==expected and expected
checks.append('reopened_saved_tag_filters_panel_and_matching_results')
restored_count=len(panel.visible)
panel.search.setText('Time Machine');panel.filter_values['tags'].clear();panel.filter_changed('formats','EPUB',True);panel.filter_toggle.setChecked(False)
assert panel.visible
w.close();w.deleteLater();app.processEvents()
w=Hub(store,store.load());p=w.bookinator;p.books=books;p.rebuild_filters();p.render()
assert p.search.text()=='Time Machine' and p.filter_values['formats']=={'EPUB'} and not p.filter_toggle.isChecked() and p.visible
checks.append('installed_nonempty_search_and_filter_restart')
p.bulk_selection={'preserved-selection'};p.clear_search_filters();assert len(p.visible)==101 and p.bulk_selection=={'preserved-selection'}
w.close();w.deleteLater();app.processEvents()
w=Hub(store,store.load());p=w.bookinator;p.books=books;p.rebuild_filters();p.render()
assert p.search.text()=='' and not any(p.filter_values.values()) and len(p.visible)==101
w.close();w.deleteLater();app.processEvents();checks.append('clear_all_persisted_across_restart')
run(['desktop-file-validate',str(home/'.local/share/applications/mediainator.desktop')]);checks.append('installed_desktop_entry_valid')
print(json.dumps(dict(checks=checks,build=release.name,restored_match_count=restored_count,smoke=smoke)))
'''
(home/'scenario.py').write_text(scenario)
cmd=['bwrap','--unshare-all','--die-with-parent','--ro-bind','/usr','/usr','--ro-bind','/etc','/etc','--symlink','usr/bin','/bin','--symlink','usr/sbin','/sbin','--symlink','usr/lib','/lib','--symlink','usr/lib64','/lib64','--proc','/proc','--dev','/dev','--tmpfs','/tmp','--dir','/home','--bind',str(home),'/home/m8-test','--chdir','/tmp','--clearenv','--setenv','HOME','/home/m8-test','--setenv','PATH','/usr/bin:/bin','--setenv','LANG','C.UTF-8','--setenv','QT_QPA_PLATFORM','offscreen','/usr/bin/python3','-I','-B','/home/m8-test/scenario.py']
p=subprocess.run(cmd,capture_output=True,text=True,timeout=180)
(root/'test_data/m8_usability/installed_verification.log').write_text(p.stdout+p.stderr)
if p.returncode:raise SystemExit(p.stdout+p.stderr)
r=json.loads(p.stdout);r.update(artifact=str(archive),sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),isolated_home=str(home),isolation='private mount/user/network namespace; checkout and host home absent',limitations='Automated offscreen installed-package checks; not personal KDE menu acceptance. Uses host system dependencies, not a clean OS.')
(root/'test_data/m8_usability/installed_verification.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
