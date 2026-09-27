"""Manual-copy qualification. Every mutation is restricted to new restore roots."""
import datetime,hashlib,json,os,shutil,stat,subprocess,sys,tarfile
from pathlib import Path
root=Path(__file__).resolve().parents[2]  # independent test root /deployment/recovery_validation
active=root/'active';evidence=root/'evidence'
stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
backup=root/'backups'/('manual-'+stamp);restored=root/'restores'/('manual-'+stamp)
candidate=json.loads((root/'candidate.json').read_text());image=candidate['container_image_digest']
script=Path(__file__).resolve().parent
report={'started':stamp,'backup':str(backup),'restore':str(restored),'image':image,'artifact_sha256':candidate['artifact_sha256'],'checks':[],'trial_started':False,'status':'incomplete'}
output=evidence/'m7_03_report.json'
def save():output.write_text(json.dumps(report,indent=2)+'\n')
def check(name,ok):
    report['checks'].append(dict(test=name,passed=bool(ok)));save();print(name,ok,flush=True);assert ok,name
def inventory(folder):
    result={}
    for base,dirs,files in os.walk(folder,followlinks=False):
        for name in dirs+files:
            p=Path(base)/name;key=str(p.relative_to(folder));mode=p.lstat().st_mode
            if stat.S_ISLNK(mode):result[key]=dict(link=os.readlink(p))
            elif stat.S_ISREG(mode):result[key]=dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),mode=stat.S_IMODE(mode))
            elif not stat.S_ISDIR(mode):raise RuntimeError('Non-copyable special file: '+str(p))
    return result
def copy(source,target):
    before=inventory(source);shutil.copytree(source,target,symlinks=True)
    assert inventory(source)==before and inventory(target)==before
    return before
def docker(envroot,args):
    # A restore mounts ONLY restored state. Stable internal paths preserve all indexes.
    cmd=['docker','run','--rm','--init','--name','mediainator-m7-restore-check','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--user',f'{os.getuid()}:{os.getgid()}',
         '--tmpfs','/tmp:rw,mode=1777','--env','QT_QPA_PLATFORM=offscreen']
    for src,dst,ro in [(envroot/'home','/home/mediainator',False),(envroot/'library','/data/library',False),(envroot/'import-sources','/data/import-sources',False),(script,'/qualification',True),(root/'artifacts','/artifacts',True)]:
        cmd+=['--mount',f'type=bind,src={src},dst={dst}'+(',readonly' if ro else '')]
    # Calibre version checks strip QT_*; native Wayland remains available.
    sock=Path(os.environ['XDG_RUNTIME_DIR'])/os.environ.get('WAYLAND_DISPLAY','wayland-0')
    cmd+=['--tmpfs',f'/tmp/runtime:rw,mode=700,uid={os.getuid()},gid={os.getgid()}', '--mount',f'type=bind,src={sock},dst=/tmp/runtime/wayland-0,readonly','--entrypoint','/usr/bin/python3',image,'-I','-B']+args
    run=subprocess.run(cmd,capture_output=True,text=True,timeout=240)
    with (evidence/'m7_03_commands.log').open('a') as log:log.write(json.dumps(args)+'\n'+run.stdout+run.stderr+'\n')
    assert run.returncode==0,run.stderr[-3000:]
    return run.stdout
def api(mode):return docker(restored,['/qualification/container_check.py',mode])
def retained():
    allfiles=inventory(restored)
    prefixes=('home/.local/share/mediainator-install/','home/.local/bin/mediainator','home/.local/share/applications/mediainator.desktop')
    return {k:v for k,v in allfiles.items() if not any(k.startswith(prefix) for prefix in prefixes)}
# Any running container touching active data makes the copy unsafe.
ids=subprocess.check_output(['docker','ps','-q'],text=True).split()
if ids:
    infos=json.loads(subprocess.check_output(['docker','inspect',*ids]))
    assert not any(Path(m.get('Source','/')).is_relative_to(active) for i in infos for m in i['Mounts']),'Close M7 before copying'
original=inventory(active)
shutil.copy2(active/'home/.config/Media-inator/Media-inator/settings.json',script/'expected_settings.json')
save()
try:
    copy(active,backup);check('manual_backup_exact_library_home_and_sources',inventory(backup)==original)
    copy(backup,restored);check('restore_exact_before_open',inventory(restored)==original)
    api('catalog');check('restored_catalog_settings_identity_and_integrity_usable',True)
    api('seed');check('preserved_recovery_and_pending_import_bulk_without_save',True)
    # Back up the enriched test environment to prove recovery payload/index copying.
    enriched=root/'backups'/('with-recovery-'+stamp);copy(restored,enriched)
    second=root/'restores'/('with-recovery-'+stamp);copy(enriched,second);restored=second;report['recovery_restore']=str(second)
    api('check');check('fresh_container_rediscovers_recovery_and_journals_without_replay',True)
    # Legacy helper caches are quarantined only after every tracked file matches.
    base=restored/'home/.local/share/mediainator-install'
    installation=json.loads((base/'installation.json').read_text())
    for release,expected in installation['releases'].items():
        folder=base/'releases'/release
        actual={str(p.relative_to(folder)):hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*') if p.is_file()}
        assert all(actual.get(k)==v for k,v in expected.items())
        extras=set(actual)-set(expected)
        assert all(k.startswith('mediainator/__pycache__/') and k.endswith('.pyc') for k in extras)
        cache=folder/'mediainator/__pycache__'
        if cache.exists():
            assert not any(p.is_symlink() for p in cache.rglob('*'))
            dest=evidence/('cache-quarantine-'+stamp)/release
            dest.parent.mkdir(parents=True,exist_ok=True);shutil.move(str(cache),dest)
    check('legacy_caches_quarantined_with_tracked_program_hashes_verified',True)
    baseline=retained()
    prior='/qualification/prior_installer.py';archive='/artifacts/prior-m6-05.tar.gz'
    docker(restored,[prior,'install',archive]);check('prior_build_installed_without_data_change',retained()==baseline)
    docker(restored,['/opt/mediainator/installer/package_install.py','install','/opt/mediainator/candidate.tar.gz']);check('upgrade_to_candidate_retains_all_data',retained()==baseline)
    api('check');check('upgraded_state_usable',True)
    baseline=retained()
    docker(restored,['/opt/mediainator/installer/package_install.py','uninstall','--yes']);check('uninstall_preserves_library_settings_history_recovery',retained()==baseline)
    check('uninstall_removes_launcher',not (restored/'home/.local/bin/mediainator').exists())
    docker(restored,['/opt/mediainator/installer/package_install.py','install','/opt/mediainator/candidate.tar.gz']);check('reinstall_preserves_retained_bytes',retained()==baseline)
    api('check');check('reinstalled_state_usable_and_not_resumed',True)
    api('recover');check('review_draft_explicit_save_resolves_recovery_and_tag_restored',True)
    check('primary_backup_unchanged',inventory(backup)==original)
    report['status']='passed'
finally:
    check('active_environment_unchanged',inventory(active)==original)
    save()
