"""Launch the real installed entry point in its disposable acceptance HOME."""
import json, os, subprocess, sys
from pathlib import Path
PROJECT=Path(__file__).resolve().parent.parent
OUT=PROJECT/'test_data/m6_07_acceptance'
report=json.loads((OUT/'report.json').read_text())
assert len(report['checks']) == 2 and all(c['passed'] for c in report['checks'])
home=Path(report['home'])
assert home.is_relative_to('/tmp') and home.parent.name.startswith('mediainator-m6-acceptance-')
# Keep all journals at their recorded paths while exposing standard Qt locations
# to the real, unmodified installed entry point (links are only in this test HOME).
fixture = Path(json.loads((OUT/'application_report.json').read_text())['root'])
for base, target in ((home/'config', fixture), (home/'data', fixture/'data')):
    parent = base/'Media-inator'
    parent.mkdir(parents=True, exist_ok=True)
    link = parent/'Media-inator'
    if link.is_dir() and not link.is_symlink():
        link.rmdir()  # Only the installer's empty instance-lock directory is permitted.
    if not link.is_symlink():
        link.symlink_to(target, target_is_directory=True)
    assert link.resolve() == target.resolve()
if 'fixture' not in report:
    settings = json.loads((fixture/'settings.json').read_text())
    settings.update(library=str(fixture/'library'), bookinator_open=True, view='List')
    (fixture/'settings.json').write_text(json.dumps(settings, indent=2)+'\n')
report.update(fixture=str(fixture), launcher=str(home/'.local/bin/mediainator'),
              desktop_entry=str(home/'data/applications/mediainator.desktop'))
(OUT/'report.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))

if '--prepare-only' not in sys.argv:
    env=dict(os.environ, HOME=str(home), XDG_CONFIG_HOME=str(home/'config'),
             XDG_DATA_HOME=str(home/'data'), XDG_CACHE_HOME=str(home/'cache'))
    for key in ('QT_QPA_PLATFORM','PYTHONPATH','PYTHONHOME'):
        env.pop(key,None)
    # Execute exactly the installed desktop entry's Exec command, outside checkout.
    import shlex
    entry=Path(report['desktop_entry']).read_text()
    command=shlex.split(next(line[5:] for line in entry.splitlines() if line.startswith('Exec=')))
    assert command == [report['launcher']]
    with (OUT/'desktop.log').open('a') as log:
        process=subprocess.Popen(command, env=env, cwd=home, stdout=log, stderr=log)
    (OUT/'desktop_process.json').write_text(json.dumps(dict(pid=process.pid,command=command,home=str(home)),indent=2)+'\n')
    print('Installed disposable desktop process:',process.pid,flush=True)
    code=process.wait()
    (OUT/'desktop_exit.json').write_text(json.dumps(dict(pid=process.pid,returncode=code),indent=2)+'\n')
    sys.exit(code)
