"""Run the existing full workflow/KWin checks against a fresh installed release.

No source application imports, original-library writes, or host logout. Desktop
acceptance remains a separate human step using the resulting installed launcher.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

PROJECT = Path(__file__).resolve().parent.parent
OUT = PROJECT / 'test_data/m6_07_acceptance'
OUT.mkdir(parents=True, exist_ok=True)
root = Path(tempfile.mkdtemp(prefix='mediainator-m6-acceptance-'))
home = root / 'user'
home.mkdir()
archive = PROJECT / 'dist/mediainator-0.1.0a1-ubuntu26.04-x86_64.tar.gz'
env = dict(os.environ, HOME=str(home), XDG_CONFIG_HOME=str(home/'config'),
           XDG_DATA_HOME=str(home/'data'), XDG_CACHE_HOME=str(home/'cache'),
           QT_QPA_PLATFORM='offscreen')
for key in ('PYTHONPATH', 'PYTHONHOME'):
    env.pop(key, None)
result = subprocess.run(['/usr/bin/python3', '-I', '-B', str(PROJECT/'tools/package_install.py'),
                         'install', str(archive)], env=env, capture_output=True, text=True, timeout=60)
(OUT/'install.log').write_text(result.stdout + result.stderr)
assert result.returncode == 0, result.stderr
release = (home/'.local/share/mediainator-install/current').resolve()
report = dict(artifact_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
              root=str(root), home=str(home), release=str(release),
              original_library_used=False, published=False, desktop_acceptance='pending', checks=[])
(OUT/'report.json').write_text(json.dumps(report, indent=2)+'\n')
env.update(MEDIAINATOR_ACCEPTANCE_RELEASE=str(release), MEDIAINATOR_ACCEPTANCE_OUTPUT=str(OUT))
for script in ('verify_m5_acceptance.py', 'verify_m5_kde.py'):
    with (OUT/(script+'.log')).open('w') as log:
        result = subprocess.run(['/usr/bin/python3', '-I', '-B', str(PROJECT/'tests'/script)],
                                env=env, cwd=root, stdout=log, stderr=log, timeout=600)
    report['checks'].append(dict(test=script, passed=result.returncode == 0))
    (OUT/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    assert result.returncode == 0, f'{script} failed; see {OUT/script}.log'
    print(script, 'PASS', flush=True)
subprocess.run(['/usr/bin/python3', '-I', '-B', str(PROJECT/'tests/launch_m6_desktop.py'), '--prepare-only'], check=True)
