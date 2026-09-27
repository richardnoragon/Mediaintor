"""Deployment display identity, separate from user/workspace state."""
import json,os
from pathlib import Path

def identity():
    manifest=Path(__file__).resolve().parent.parent/'manifest.json'
    version='development/unpackaged';default='Development'
    if manifest.is_file():
        default='Installed'
        try:
            value=json.loads(manifest.read_text());version=f"{value['version']}-{value['build_id']}"
        except (OSError,ValueError,KeyError,TypeError):version='installed build unavailable'
    label=os.environ.get('MEDIAINATOR_INSTALLATION_LABEL',default).strip()
    if not label or len(label)>80 or not all(c.isprintable() for c in label):label=default
    return label,version

def window_title():
    label,build=identity()
    return f'Media-inator — {label} ({build})'
