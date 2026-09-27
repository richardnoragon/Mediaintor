"""External audio player launch for Music-inator. No Qt.

Music-inator never embeds a player and keeps no listening history. **Play album**
writes a small M3U playlist into Media-inator application data (never into a music
folder) and starts the configured player — or the desktop's default application for
playlists — detached. The player is not adopted, tracked or closed.

Player command placeholders: `{playlist}` (the playlist file), `{files}` (every track
as separate arguments), `{file}` (the first track). Without a placeholder the track
files are appended, which mpv, VLC, Audacious, Strawberry and most players accept.
"""
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile

from .movie_player import PlayerError, validate_command

PLAYLIST_NAME = 'now-playing.m3u8'

__all__ = ('PlayerError', 'validate_command', 'write_playlist', 'build_command', 'launch_album')


def write_playlist(folder, tracks):
    """tracks: [(path, title or '', duration seconds or None)]. Atomic replace."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    lines = ['#EXTM3U']
    for path, title, duration in tracks:
        clean = ' '.join(str(title or Path(path).stem).split())
        lines.append(f'#EXTINF:{int(duration) if duration else -1},{clean}')
        lines.append(str(path))
    target = folder / PLAYLIST_NAME
    fd, temporary = tempfile.mkstemp(prefix='.playlist-', suffix='.m3u8', dir=folder)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            stream.write('\n'.join(lines) + '\n')
        os.replace(temporary, target)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise
    return target


def build_command(command, playlist, files):
    command = validate_command(command)
    if not command:
        opener = shutil.which('xdg-open')
        if not opener:
            raise PlayerError('No default application launcher (xdg-open) is available. Choose a player command.')
        return [opener, str(playlist)]
    parts = shlex.split(command)
    executable = shutil.which(parts[0]) if os.sep not in parts[0] else parts[0]
    if not executable or not os.access(executable, os.X_OK):
        raise PlayerError(f'Player "{parts[0]}" was not found or is not executable.')
    args, placed = [], False
    for arg in parts[1:]:
        if arg == '{files}':
            args.extend(str(f) for f in files); placed = True
        elif '{playlist}' in arg or '{file}' in arg:
            args.append(arg.replace('{playlist}', str(playlist)).replace('{file}', str(files[0]))); placed = True
        else:
            args.append(arg)
    if not placed:
        args.extend(str(f) for f in files)
    return [executable, *args]


def launch_album(command, files, playlist_folder, popen=None):
    """Play a digital copy. `files` are AudioFile-like objects (path, title, duration)
    in play order. Raises PlayerError with a user-facing message."""
    if not files:
        raise PlayerError('This copy has no audio files.')
    missing = [f.path for f in files if not Path(f.path).is_file()]
    if missing:
        raise PlayerError(f'{len(missing)} of {len(files)} file(s) are missing or unavailable, for example:\n{missing[0]}\n'
                          'Use Locate… if the folder was moved, or reconnect its drive.')
    try:
        playlist = write_playlist(playlist_folder, [(f.path, f.title, f.duration) for f in files])
    except OSError as exc:
        raise PlayerError(f'The playlist could not be written to {playlist_folder}: {exc}') from exc
    argv = build_command(command, playlist, [f.path for f in files])
    popen = popen or subprocess.Popen
    try:
        popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
              start_new_session=True, close_fds=True)
    except OSError as exc:
        raise PlayerError(f'The player could not be started: {exc}') from exc
    return argv


def match_moved(files, new_folder):
    """Suggest new paths for files of a copy whose folder was moved. Files are looked
    up by their path relative to the old common folder, then by file name alone.
    Returns ({file id: new path}, [file ids not found])."""
    new_folder = Path(new_folder)
    try:
        old_root = Path(os.path.commonpath([f.path for f in files])) if len(files) > 1 else Path(files[0].path).parent
    except (ValueError, IndexError):
        return {}, [f.id for f in files]
    by_name = {}
    for root, dirs, names in os.walk(new_folder, followlinks=False):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for name in names:
            by_name.setdefault(name, []).append(Path(root) / name)
    moves, missing = {}, []
    for f in files:
        try:
            relative = Path(f.path).relative_to(old_root)
        except ValueError:
            relative = Path(Path(f.path).name)
        candidate = new_folder / relative
        if candidate.is_file():
            moves[f.id] = str(candidate)
            continue
        same = by_name.get(Path(f.path).name, [])
        if len(same) == 1:
            moves[f.id] = str(same[0])
        else:
            missing.append(f.id)
    return moves, missing
