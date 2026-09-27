"""Offline application help. Opening help never probes Calibre or user data."""
from pathlib import Path
from PyQt6.QtWidgets import QDialog,QVBoxLayout,QHBoxLayout,QComboBox,QTextBrowser,QLineEdit,QPushButton,QLabel
from . import __version__

TOPICS = {'User guide':'USER_GUIDE.md','Installation and upgrades':'INSTALL.md','Troubleshooting':'TROUBLESHOOTING.md'}

def documentation_root():
    root=Path(__file__).resolve().parent.parent
    return root/'packaging' if (root/'packaging').is_dir() else root

def read_topic(topic):
    try:return (documentation_root()/TOPICS[topic]).read_text(encoding='utf-8')
    except OSError:
        return '# Help file unavailable\n\nThe installed help file is missing or unreadable. Reinstall the same trusted bundle after closing Media-inator. Keep your settings and recovery data. Library operations are not needed to read help.'

class HelpDialog(QDialog):
    def __init__(self,parent=None,topic='User guide'):
        super().__init__(parent);self.setWindowTitle('Media-inator Help');self.resize(820,640)
        layout=QVBoxLayout(self)
        self.topics=QComboBox();self.topics.addItems(TOPICS);self.topics.setAccessibleName('Help topic');layout.addWidget(self.topics)
        bar=QHBoxLayout();self.search=QLineEdit();self.search.setPlaceholderText('Find in this topic');self.search.setAccessibleName('Find in help');bar.addWidget(self.search)
        next_button=QPushButton('Find next');next_button.clicked.connect(self.find_next);self.search.returnPressed.connect(self.find_next);bar.addWidget(next_button);layout.addLayout(bar)
        self.browser=QTextBrowser();self.browser.setOpenLinks(False);self.browser.setOpenExternalLinks(False);layout.addWidget(self.browser)
        self.notice=QLabel();layout.addWidget(self.notice)
        close=QPushButton('Close help');close.clicked.connect(self.close);layout.addWidget(close)
        self.topics.currentTextChanged.connect(self.show_topic);self.topics.setCurrentText(topic);self.show_topic(topic)
    def show_topic(self,topic):
        self.browser.setMarkdown(read_topic(topic));self.notice.setText('Offline help — no library data is accessed.')
    def find_next(self):
        term=self.search.text()
        if not term:return
        if not self.browser.find(term):
            cursor=self.browser.textCursor();cursor.movePosition(cursor.MoveOperation.Start);self.browser.setTextCursor(cursor)
            if not self.browser.find(term):self.notice.setText('Text not found in this topic.');return
        self.notice.setText('Match selected.')

def about_text():
    import platform
    from .installation import identity
    label,build=identity()
    from PyQt6.QtCore import PYQT_VERSION_STR,qVersion
    return (f'Media-inator {__version__} · {label}\nBuild: {build}\nPython {platform.python_version()} · PyQt6 {PYQT_VERSION_STR} · Qt {qVersion()}\n\n'
            'Personal-use preview for Ubuntu 26.04.1 KDE (x86_64).\nVerified Calibre: 9.2.1, installed separately.\nPersonal-use build. Promotion is separate from milestone acceptance. No release has been published.\n\n'
            'Use Help for installation, protected-access rules and recovery guidance. Use Help → Preview redacted diagnostics for an explicit local export. Nothing is uploaded.')
