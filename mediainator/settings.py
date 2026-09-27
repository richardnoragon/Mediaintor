"""Versioned, atomically replaced preferences outside the Calibre library."""
import json
from pathlib import Path
from uuid import UUID, uuid4

from PyQt6.QtCore import QIODevice, QSaveFile


class SettingsError(Exception):
    pass


APPEARANCE_CHOICES = {
    "theme": ("System", "Light", "Dark"),
    "accent": ("System", "Blue", "Green", "Purple", "Orange", "Red"),
    "size": ("Small", "Default", "Large", "Extra Large"),
    "density": ("Compact", "Normal", "Comfortable"),
}


def appearance_defaults():
    return dict(theme="System", accent="System", size="Default", density="Normal")


def validate_appearance(value):
    if not isinstance(value, dict) or set(value) != set(APPEARANCE_CHOICES):
        raise SettingsError("Invalid appearance settings.")
    for key, choices in APPEARANCE_CHOICES.items():
        if value[key] not in choices:
            raise SettingsError(f"Invalid appearance {key}.")
    return dict(value)


def defaults() -> dict:
    return {
        "schema_version": 1,
        "profile_id": str(uuid4()),
        "profile_name": "Personal",
        "device_id": str(uuid4()),
        "view": "Grid",
        "bookinator_open": True,
        "selected_book": None,
        "geometry": "",
    }


def validate(data: object) -> dict:
    if not isinstance(data, dict) or type(data.get("schema_version")) is not int:
        raise SettingsError("Settings do not contain a valid schema version.")
    if data["schema_version"] != 1:
        raise SettingsError("Unsupported settings version. The existing file was preserved.")
    for key in ("profile_id", "device_id"):
        try:
            UUID(data[key])
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            raise SettingsError(f"Invalid {key} in settings.") from exc
    if not isinstance(data.get("profile_name"), str) or not data["profile_name"].strip():
        raise SettingsError("Invalid profile name.")
    if data.get("view") not in ("Grid", "List"):
        raise SettingsError("Invalid catalog view preference.")
    if type(data.get("bookinator_open")) is not bool:
        raise SettingsError("Invalid module selection.")
    if data.get("selected_book") is not None and not isinstance(data["selected_book"], str):
        raise SettingsError("Invalid selected book.")
    geometry = data.get("geometry")
    if not isinstance(geometry, str):
        raise SettingsError("Invalid window geometry.")
    try:
        bytes.fromhex(geometry)
    except ValueError as exc:
        raise SettingsError("Invalid window geometry encoding.") from exc
    if data.get("library") is not None and not isinstance(data["library"], str):
        raise SettingsError("Invalid library location.")
    reader = data.get("reader")
    if reader is not None:
        if not isinstance(reader, dict) or type(reader.get("pid")) is not int or reader["pid"] <= 0:
            raise SettingsError("Invalid reader ownership record.")
        if not all(isinstance(reader.get(k), str) and reader[k] for k in ("start_time", "file", "profile_id", "module")):
            raise SettingsError("Incomplete reader ownership record.")
    validate_appearance(data.get("appearance", appearance_defaults()))
    search = data.get('catalog_search', {})
    if not isinstance(search, dict) or not isinstance(search.get('text', ''), str):
        raise SettingsError('Invalid catalog search settings.')
    for key in ('tags', 'formats', 'statuses'):
        values = search.get(key, [])
        if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
            raise SettingsError('Invalid catalog filter settings.')
    for key in ('expanded', 'needs_review'):
        if type(search.get(key, False)) is not bool:
            raise SettingsError('Invalid filter panel settings.')
    validate_movie_settings(data)
    validate_music_settings(data)
    validate_paper_settings(data)
    return data


def validate_movie_settings(data):
    """Optional Movie-inator preferences; absent keys use defaults (schema 1 unchanged)."""
    if type(data.get('movieinator_open', False)) is not bool:
        raise SettingsError('Invalid Movie-inator module selection.')
    if data.get('movie_view', 'Grid') not in ('Grid', 'List'):
        raise SettingsError('Invalid movie catalog view preference.')
    if data.get('selected_movie') is not None and not isinstance(data['selected_movie'], str):
        raise SettingsError('Invalid selected movie.')
    player = data.get('movie_player', '')
    if not isinstance(player, str) or len(player) > 1000:
        raise SettingsError('Invalid movie player command.')
    search = data.get('movie_search', {})
    if not isinstance(search, dict) or not isinstance(search.get('text', ''), str) or not isinstance(search.get('sort', ''), str):
        raise SettingsError('Invalid movie search settings.')
    for key in ('genres', 'formats', 'statuses'):
        values = search.get(key, [])
        if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
            raise SettingsError('Invalid movie filter settings.')
    if type(search.get('expanded', False)) is not bool:
        raise SettingsError('Invalid movie filter panel settings.')


def validate_music_settings(data):
    """Optional Music-inator preferences; absent keys use defaults (schema 1 unchanged)."""
    if type(data.get('musicinator_open', False)) is not bool:
        raise SettingsError('Invalid Music-inator module selection.')
    if data.get('music_view', 'Grid') not in ('Grid', 'List'):
        raise SettingsError('Invalid music catalog view preference.')
    if data.get('selected_album') is not None and not isinstance(data['selected_album'], str):
        raise SettingsError('Invalid selected album.')
    player = data.get('music_player', '')
    if not isinstance(player, str) or len(player) > 1000:
        raise SettingsError('Invalid music player command.')
    search = data.get('music_search', {})
    if not isinstance(search, dict) or not isinstance(search.get('text', ''), str) or not isinstance(search.get('sort', ''), str):
        raise SettingsError('Invalid music search settings.')
    for key in ('genres', 'formats', 'personal'):
        values = search.get(key, [])
        if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
            raise SettingsError('Invalid music filter settings.')
    if type(search.get('expanded', False)) is not bool:
        raise SettingsError('Invalid music filter panel settings.')
    browse = data.get('music_browse', {})
    if (not isinstance(browse, dict) or not isinstance(browse.get('mode', 'Albums'), str)
            or not (browse.get('value') is None or isinstance(browse.get('value'), str))):
        raise SettingsError('Invalid music browse settings.')


PAPER_STARTUP = ('Home Dashboard', 'Library', 'Projects', 'Restore Last View')
PAPER_VIEWS = ('Home', 'Library', 'Notes', 'Projects', 'Trash')


def validate_paper_settings(data):
    """Optional Paper-inator preferences; absent keys use defaults (schema 1 unchanged).
    Research content itself lives in the profile's Paper-inator library, not here."""
    if type(data.get('paperinator_open', False)) is not bool:
        raise SettingsError('Invalid Paper-inator module selection.')
    if data.get('paper_startup', 'Home Dashboard') not in PAPER_STARTUP:
        raise SettingsError('Invalid Paper-inator startup view.')
    if data.get('paper_view', 'Home') not in PAPER_VIEWS:
        raise SettingsError('Invalid Paper-inator view.')
    for key in ('selected_paper', 'selected_paper_note', 'selected_paper_project', 'paper_saved_search'):
        if data.get(key) is not None and not isinstance(data[key], str):
            raise SettingsError('Invalid Paper-inator selection.')
    reader = data.get('paper_reader', '')
    if not isinstance(reader, str) or len(reader) > 1000:
        raise SettingsError('Invalid Paper-inator reader command.')
    search = data.get('paper_search', {})
    if not isinstance(search, dict) or not isinstance(search.get('text', ''), str) or not isinstance(search.get('sort', ''), str):
        raise SettingsError('Invalid Paper-inator search settings.')
    for key in ('types', 'reading', 'handling', 'flags', 'tags'):
        values = search.get(key, [])
        if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
            raise SettingsError('Invalid Paper-inator filter settings.')
    if not (search.get('container') is None or isinstance(search.get('container'), str)):
        raise SettingsError('Invalid Paper-inator project filter.')
    if type(search.get('expanded', False)) is not bool:
        raise SettingsError('Invalid Paper-inator filter panel settings.')


class SettingsStore:
    def __init__(self, path: Path):
        self.path = path

    def load(self) -> dict:
        try:
            return validate(json.loads(self.path.read_text(encoding="utf-8")))
        except FileNotFoundError:
            return defaults()
        except (OSError, ValueError) as exc:
            raise SettingsError(f"Cannot read settings: {exc}") from exc

    def save(self, data: dict) -> None:
        validate(data)
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise SettingsError(f"Cannot create settings folder: {exc}") from exc
        payload = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        output = QSaveFile(str(self.path))
        output.setDirectWriteFallback(False)
        if not output.open(QIODevice.OpenModeFlag.WriteOnly):
            raise SettingsError(output.errorString())
        if output.write(payload) != len(payload):
            error = output.errorString()
            output.cancelWriting()
            raise SettingsError(error)
        if not output.commit():
            raise SettingsError(output.errorString())
