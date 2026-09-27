"""Run a native Wayland deployment with explicitly scoped persistent mounts."""
import argparse
import os
from pathlib import Path
import subprocess


def command(root, image, action, detached=False):
    root = Path(root).resolve()
    uid, gid = os.getuid(), os.getgid()
    args = ['docker', 'run', '--rm', '--init', '--network', 'none', '--read-only',
            '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
            '--user', f'{uid}:{gid}', '--tmpfs', '/tmp:rw,nosuid,nodev,mode=1777',
            '--tmpfs', f'/tmp/runtime:rw,nosuid,nodev,mode=700,uid={uid},gid={gid}']
    for folder, target in [('home', '/home/mediainator'), ('library', '/data/library'),
                           ('import-sources', '/data/import-sources')]:
        source = root / 'active' / folder
        if not source.is_dir():
            raise ValueError(f'Missing persistent directory: {source}')
        args += ['--mount', f'type=bind,src={source},dst={target}']
    if action == 'run':
        runtime = Path(os.environ.get('XDG_RUNTIME_DIR', f'/run/user/{uid}'))
        socket = runtime / os.environ.get('WAYLAND_DISPLAY', 'wayland-0')
        if not socket.is_socket():
            raise ValueError('Launch from an active Wayland desktop session.')
        args += ['--mount', f'type=bind,src={socket},dst=/tmp/runtime/wayland-0,readonly']
        pulse = runtime / 'pulse/native'
        if pulse.is_socket():
            args += ['--mount', f'type=bind,src={pulse},dst=/tmp/runtime/pulse-native,readonly',
                     '-e', 'PULSE_SERVER=unix:/tmp/runtime/pulse-native']
        args += ['--name', 'mediainator-m19-everyday']
        if detached:
            args += ['--detach']
    else:
        args += ['-e', 'QT_QPA_PLATFORM=offscreen']
    return args + [image, action]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['install', 'verify', 'run'])
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--image', default='mediainator:m19')
    parser.add_argument('--detach', action='store_true')
    args = parser.parse_args()
    try:
        return subprocess.call(command(args.root, args.image, args.action, args.detach))
    except ValueError as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    raise SystemExit(main())
