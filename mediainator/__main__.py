import sys
import argparse
from pathlib import Path
from PyQt6.QtCore import QStandardPaths, QLockFile
from PyQt6.QtWidgets import QApplication, QMessageBox
from .settings import SettingsError, SettingsStore
from .window import Hub


def main():
    parser = argparse.ArgumentParser(description="Media-inator development preview")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--test-library', type=Path, help='Explicitly registered disposable library only')
    mode.add_argument('--sample', action='store_true', help='Built-in sample catalog without library access')
    parser.add_argument('--movie-catalog', type=Path, help='Movie-inator catalog file to use instead of the default (e.g. a disposable test catalog)')
    parser.add_argument('--music-catalog', type=Path, help='Music-inator catalog file to use instead of the default (e.g. a disposable test catalog)')
    parser.add_argument('--paper-library', type=Path, help='Paper-inator library folder to use instead of the default (e.g. a disposable test library); each profile gets its own subfolder')
    args = parser.parse_args()
    app = QApplication(sys.argv)
    app.setApplicationName("Media-inator")
    app.setOrganizationName("Media-inator")
    folder = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation))
    try:
        folder.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        QMessageBox.critical(None, "Cannot create settings folder", f"Check available disk space and write permissions, then restart. Your library was not opened.\n\n{exc}")
        return 1
    lock = QLockFile(str(folder / "instance.lock"))
    if not lock.tryLock(0):
        QMessageBox.warning(None, "Media-inator cannot start", "Close the other Media-inator window and try again. If none is open, check that your settings folder is writable. Do not delete settings or recovery data.")
        return 1
    store = SettingsStore(folder / "settings.json")
    try:
        state = store.load()
    except SettingsError as exc:
        QMessageBox.critical(None, "Cannot load settings", f"{exc}\nExisting settings were not overwritten. Keep a copy and repair the settings file, or use an application version supporting its schema. Do not delete recovery data. Settings location:\n{store.path}")
        return 1
    if args.test_library:
        from .library import check_library
        try:
            args.test_library = check_library(args.test_library)
        except (OSError, ValueError) as exc:
            QMessageBox.critical(None, "Cannot use test library", str(exc))
            return 1
    window = Hub(store, state, args.test_library, live=not (args.sample or args.test_library),
                 app_data=Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)),
                 movie_catalog=args.movie_catalog.expanduser().resolve() if args.movie_catalog else None,
                 music_catalog=args.music_catalog.expanduser().resolve() if args.music_catalog else None,
                 paper_library=args.paper_library.expanduser().resolve() if args.paper_library else None)
    app.commitDataRequest.connect(window.commit_shutdown)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
