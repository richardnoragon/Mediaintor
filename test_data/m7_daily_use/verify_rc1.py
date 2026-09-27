"""Qualify the extracted RC1 bundle; never mount the active environment."""
from pathlib import Path
import datetime,hashlib,json,os,shutil,subprocess,tarfile,time
root=Path(__file__).resolve().parents[2]  # independent root/deployment/rc1_validation/script
release=root/'releases/mediainator-rc1';archive=root/'releases/mediainator-rc1.tar.gz'
stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S');work=root/'qualification'/('rc1-'+stamp);work.mkdir(parents=True)
with tarfile.open(archive) as t:t.extractall(work/'extracted',filter='data')
bundle=work/'extracted/mediainator-rc1'
report={'status':'incomplete','root':str(work),'bundle_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'checks':[],'trial_started':False}
resultfile=root/'evidence/rc1_qualification.json'
def check(name,value):
    report['checks'].append({'test':name,'passed':bool(value)});resultfile.write_text(json.dumps(report,indent=2)+'\n');print(name,bool(value),flush=True);assert value,name
def run(args,cwd=bundle,ok=True):
    p=subprocess.run(args,cwd=cwd,capture_output=True,text=True,timeout=180)
    with (work/'commands.log').open('a') as f:f.write(json.dumps(args)+'\n'+p.stdout+p.stderr+'\n')
    if ok:assert p.returncode==0,p.stderr[-2000:]
    return p
manage=['python3','manage.py']
run(manage+['verify-bundle']);check('extracted_bundle_integrity',True)
run(manage+['load-image']);check('bundled_image_loads_without_rebuild',True)
# Fresh home: install from bundled image, copy only existing test library and preferences.
state=work/'fresh-state';(state/'home').mkdir(parents=True);(state/'import-sources').mkdir()
seed=root/'active/library'
def hashes(p):return {str(f.relative_to(p)):hashlib.sha256(f.read_bytes()).hexdigest() for f in p.rglob('*') if f.is_file() and not f.is_symlink()}
seed_before=hashes(seed);shutil.copytree(seed,state/'library');assert hashes(state/'library')==seed_before
run(manage+['configure','--state-root',str(state)])
compose=['docker','compose','--project-name','mediainator-rc1-qualification']
run(compose+['config','--quiet']);check('compose_config_valid',True)
run(compose+['run','--rm','init']);check('fresh_home_install', (state/'home/.local/bin/mediainator').is_file())
settings=state/'home/.config/Media-inator/Media-inator/settings.json';settings.parent.mkdir(parents=True,exist_ok=True)
shutil.copy2(root/'active/home/.config/Media-inator/Media-inator/settings.json',settings)
# Current deployment uses existing library paths inside the container; no remap needed.
def running():
    p=run(compose+['ps','-q','hub']);identity=p.stdout.strip();assert identity
    info=json.loads(run(['docker','inspect',identity]).stdout)[0];assert info['State']['Running'];return info
try:
    run(compose+['up','-d']);time.sleep(4);info=running()
    check('compose_up_starts_native_hub',info['HostConfig']['NetworkMode']=='none')
    check('only_isolated_state_and_display_mounted',all(m['Source'].startswith(str(state)) or m['Source'].startswith(str(bundle)) or m['Source']=='/run/user/1000/wayland-0' for m in info['Mounts']))
    blocked=run(manage+['backup',str(state),str(work/'must-not-exist')],ok=False)
    check('backup_refuses_running_container',blocked.returncode!=0 and not (work/'must-not-exist').exists())
    # Clean fixture only: no user edits/readers are open in this qualification instance.
    run(compose+['down']);before=hashes(state)
    run(compose+['up','-d']);time.sleep(3);running()
    check('compose_down_up_retains_settings',json.loads(settings.read_text())['profile_id']==json.loads((root/'active/home/.config/Media-inator/Media-inator/settings.json').read_text())['profile_id'])
    run(compose+['down'])
    backup=work/'backup';restored=work/'restored'
    run(['./backup.sh',str(state),str(backup)])
    check('backup_script_verifies_full_state',(backup/'manifest.json').is_file())
    check('backup_refuses_existing_destination',run(['./backup.sh',str(state),str(backup)],ok=False).returncode!=0)
    check('backup_refuses_overlapping_destination',run(['./backup.sh',str(state),str(state/'bad-backup')],ok=False).returncode!=0)
    run(['./restore.sh',str(backup),str(restored)])
    check('restore_script_verifies_data',hashes(restored)==hashes(state))
    check('restore_refuses_existing_destination',run(['./restore.sh',str(backup),str(state)],ok=False).returncode!=0)
    # Tampered backup must fail before creating the restore destination.
    damaged=work/'damaged';shutil.copytree(backup,damaged,symlinks=True)
    (damaged/'data/library/metadata.db').write_bytes(b'damaged test fixture')
    check('restore_rejects_corrupt_backup',run(['./restore.sh',str(damaged),str(work/'bad-restore')],ok=False).returncode!=0 and not (work/'bad-restore').exists())
    # Repoint only this extracted test configuration; do not modify the frozen bundle.
    envfile=bundle/'.env';envfile.write_text(envfile.read_text().replace(str(state),str(restored)))
    run(compose+['up','-d']);time.sleep(3);info=running()
    check('restored_environment_starts_after_container_removal',any(m['Source']==str(restored/'library') for m in info['Mounts']))
    run(compose+['down'])
    verified=run(compose+['run','--rm','--no-deps','hub','verify'])
    check('restored_101_books_runtime_snapshot_and_adapter_pass','"books": 101' in verified.stdout and '"calibre_adapter_write_readback_restore": "passed on throwaway copy"' in verified.stdout)
    run(manage+['verify-bundle']);check('bundle_unchanged_after_use',True)
    check('active_seed_unchanged',hashes(seed)==seed_before)
    report['status']='passed';resultfile.write_text(json.dumps(report,indent=2)+'\n')
finally:
    run(compose+['down'],ok=False)
