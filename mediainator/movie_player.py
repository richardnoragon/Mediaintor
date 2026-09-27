"""External video player launch for Movie-inator. No Qt.

Movie-inator never embeds a player. It starts the configured player (or the desktop's
default application) detached, and does not adopt, track or close it: the player
belongs to the user once launched.
"""
import os
from pathlib import Path
import shlex
import shutil
import subprocess


class PlayerError(Exception):
    pass


def validate_command(command):
    """'' means the desktop default application. Otherwise an executable plus
    optional arguments; '{file}' marks where the file goes (appended when absent)."""
    if not isinstance(command, str):
        raise PlayerError('Invalid player setting.')
    command = command.strip()
    if not command:
        return ''
    if len(command) > 1000 or any(ord(c) < 32 for c in command):
        raise PlayerError('The player command is too long or contains control characters.')
    try:
        parts = shlex.split(command)
    except ValueError as exc:
        raise PlayerError(f'Cannot read the player command: {exc}') from exc
    if not parts:
        return ''
    return command


def build_command(command, path):
    command = validate_command(command)
    if not command:
        opener = shutil.which('xdg-open')
        if not opener:
            raise PlayerError('No default application launcher (xdg-open) is available. Choose a player command.')
        return [opener, str(path)]
    parts = shlex.split(command)
    executable = shutil.which(parts[0]) if os.sep not in parts[0] else parts[0]
    if not executable or not os.access(executable, os.X_OK):
        raise PlayerError(f'Player "{parts[0]}" was not found or is not executable.')
    args = [a.replace('{file}', str(path)) for a in parts[1:]]
    if not any('{file}' in a for a in parts[1:]):
        args.append(str(path))
    return [executable, *args]


def launch(command, path, popen=subprocess.Popen):
    """Start the player detached. Raises PlayerError with a user-facing message."""
    path = Path(path)
    if not path.is_file():
        raise PlayerError(f'The file is missing or unavailable: {path}\nUse Locate… if it was moved, or reconnect its drive.')
    argv = build_command(command, path)
    try:
        popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
              start_new_session=True, close_fds=True)
    except OSError as exc:
        raise PlayerError(f'The player could not be started: {exc}') from exc
    return argv
