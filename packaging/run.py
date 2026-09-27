"""Installed entry point; isolated Python is selected by the stable launcher."""
import fcntl
import json
import os
from pathlib import Path
import sys

root = Path(__file__).resolve().parent
for key in tuple(os.environ):
    if key.startswith(('PYTHON', 'QT_')) or key in ('QML_IMPORT_PATH', 'QML2_IMPORT_PATH'):
        os.environ.pop(key, None)
sys.path.insert(0, str(root))
if '--package-check' in sys.argv or '--package-smoke' in sys.argv:
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    from PyQt6.QtCore import QTimer, QT_VERSION_STR
    from PyQt6.QtWidgets import QApplication
    from mediainator.window import Hub
    from mediainator.settings import SettingsStore, defaults
    if '--package-smoke' in sys.argv:
        import tempfile
        app = QApplication([])
        with tempfile.TemporaryDirectory(prefix='mediainator-package-smoke-') as folder:
            hub = Hub(SettingsStore(Path(folder)/'settings.json'), defaults())
            hub.show()
            QTimer.singleShot(100, hub.close)
            app.exec()
    print(json.dumps({'version': json.loads((root/'manifest.json').read_text())['version'],
                      'Qt': QT_VERSION_STR, 'application_imported': True}))
else:
    # Shared lock lives for the entire process; installer takes an exclusive lock.
    lock = (root.parent.parent/'install.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_SH)
    if (root.parent.parent/'transaction.json').exists():
        print('An installation action was interrupted. Run the trusted installer with repair before starting Media-inator. Your application data is retained.',file=sys.stderr)
        sys.exit(1)
    try:
        from mediainator.__main__ import main
    except ImportError:
        print('Media-inator cannot load its application runtime. Check the required system Python/PyQt6 versions, or reinstall the same trusted package. No library was opened. See '+str(root/'INSTALL.md')+'. Settings and recovery data were retained.', file=sys.stderr)
        sys.exit(1)
    sys.exit(main())
