"""Named snapshot management. Restore/startup execution is a separate step."""
from pathlib import Path
from contextlib import closing
import sqlite3
from PyQt6.QtWidgets import QDialog,QVBoxLayout,QHBoxLayout,QLabel,QListWidget,QPushButton,QInputDialog,QMessageBox
from .workspaces import WorkspaceStore,WorkspaceError


class WorkspaceBusy(WorkspaceError):
    """Temporary protection; background persistence should retry quietly."""


def check_idle(hub):
    controller=getattr(hub,'workspaces',None)
    if controller and controller.transaction is not None:raise WorkspaceError('A workspace restore is running; wait or cancel it')
    panel=hub.bookinator
    if hub.closing:raise WorkspaceError('Wait until closing finishes')
    movies=getattr(hub,'movieinator',None)
    if movies is not None and movies.busy():
        raise WorkspaceBusy('Workspace changes are unavailable while a movie import is running. Wait, then retry.')
    music=getattr(hub,'musicinator',None)
    if music is not None and music.busy():
        raise WorkspaceBusy('Workspace changes are unavailable while a music import is running. Wait, then retry.')
    papers=getattr(hub,'paperinator',None)
    if papers is not None and papers.busy():
        raise WorkspaceBusy('Workspace changes are unavailable while a document import is running. Wait, then retry.')
    if panel and (panel.import_active() or panel.bulk_active() or
                  (panel.editor and panel.editor.busy) or (panel.loader and panel.loader.active)):
        raise WorkspaceBusy('Workspace changes are unavailable while a library operation is running. Wait, then retry.')


def capture(hub,allow_busy=False):
    if not allow_busy:check_idle(hub)
    movies=getattr(hub,'movieinator',None)
    music=getattr(hub,'musicinator',None)
    papers=getattr(hub,'paperinator',None)
    modules=(['hub']+(['bookinator'] if hub.bookinator else [])+(['musicinator'] if music else [])+(['movieinator'] if movies else [])
             +(['paperinator'] if papers else []))
    current=hub.tabs.currentWidget()
    active=('bookinator' if hub.bookinator and current is hub.bookinator else 'musicinator' if music and current is music
            else 'movieinator' if movies and current is movies else 'paperinator' if papers and current is papers else 'hub')
    selection=None
    if hub.bookinator and hub.library:
        book=next((b for b in hub.bookinator.books if b.id==hub.state.get('selected_book')),None)
        if book and book.uuid:
            with closing(sqlite3.connect((Path(hub.library)/'metadata.db').resolve().as_uri()+'?mode=ro',uri=True)) as db:
                row=db.execute('SELECT uuid FROM library_id LIMIT 1').fetchone()
            if row:selection=dict(library_uuid=row[0],book_uuid=book.uuid)
    movie_selection=None
    if movies is not None and movies.store is not None and hub.state.get('selected_movie'):
        from .movie_store import MovieStoreError
        try:catalog=movies.store.catalog_uuid()
        except MovieStoreError:catalog=None
        if catalog and any(m.id==hub.state['selected_movie'] for m in movies.movies):
            movie_selection=dict(catalog_uuid=catalog,movie_id=hub.state['selected_movie'])
    music_selection=None
    if music is not None and music.store is not None and hub.state.get('selected_album'):
        from .music_store import MusicStoreError
        try:catalog=music.store.catalog_uuid()
        except MusicStoreError:catalog=None
        if catalog and any(a.id==hub.state['selected_album'] for a in music.albums):
            music_selection=dict(catalog_uuid=catalog,album_id=hub.state['selected_album'])
    paper_selection=None
    if papers is not None and papers.store is not None and hub.state.get('selected_paper'):
        from .paper_store import PaperStoreError
        try:library=papers.store.library_uuid()
        except PaperStoreError:library=None
        if library and papers.library.item(hub.state['selected_paper']) is not None:
            paper_selection=dict(library_uuid=library,item_id=hub.state['selected_paper'])
    normal=hub.normalGeometry() if hub.isMaximized() else hub.geometry()
    screen=hub.screen();available=screen.availableGeometry()
    rect=lambda r:[r.x(),r.y(),r.width(),r.height()]
    value=dict(modules=modules,active=active,selection=selection,geometry=dict(
        qt=bytes(hub.saveGeometry()).hex(),normal=rect(normal),maximized=hub.isMaximized(),screen=screen.name(),available=rect(available)))
    if movie_selection:value['movie_selection']=movie_selection
    if music_selection:value['music_selection']=music_selection
    if paper_selection:value['paper_selection']=paper_selection
    return value


class WorkspaceDialog(QDialog):
    def __init__(self,hub):
        super().__init__(hub);self.hub=hub;self.setWindowTitle('Named workspaces');self.resize(480,340)
        self.store=hub.workspaces.store
        layout=QVBoxLayout(self)
        layout.addWidget(QLabel('Save layout and selection only; search/filters and readers are excluded.\nRestore a snapshot, or choose it as the startup workspace.'))
        self.notice=QLabel();self.notice.setWordWrap(True);layout.addWidget(self.notice)
        self.list=QListWidget();layout.addWidget(self.list)
        bar=QHBoxLayout();self.buttons=[]
        layout.addLayout(bar)
        for label,slot in [('Save new workspace',self.save_new),('Overwrite selected workspace',self.overwrite),('Rename workspace',self.rename),('Delete workspace',self.delete),('Restore selected workspace',self.restore),('Use selected workspace at startup',self.startup)]:
            if len(self.buttons)==3:
                bar=QHBoxLayout();layout.addLayout(bar)
            button=QPushButton(label);button.clicked.connect(lambda checked=False,fn=slot:self.perform(fn));bar.addWidget(button);self.buttons.append(button)
        last=QPushButton('Restore Last Session');last.clicked.connect(lambda:self.perform(lambda:self.hub.workspaces.restore_key('last_session')));layout.addWidget(last)
        default=QPushButton('Use Last Session at startup');default.clicked.connect(lambda:self.perform(self.default_startup));layout.addWidget(default)
        reload=QPushButton('Reload workspace list');reload.clicked.connect(self.reload);layout.addWidget(reload)
        close=QPushButton('Close workspaces');close.clicked.connect(self.close);layout.addWidget(close);self.reload()

    def reload(self):
        try:
            self.data=self.store.load();self.keys=list(self.data['named']);self.list.clear()
            self.list.addItems([e['name'] for e in self.data['named'].values()]);startup=self.data['startup']
            startup_name='Last Session' if startup=='last_session' else self.data['named'][startup]['name']
            self.notice.setText(f'{len(self.keys)} of 5 named workspaces. Startup: {startup_name}')
            self.hub.workspaces.disabled=False
            for b in self.buttons:b.setEnabled(True)
        except (WorkspaceError,OSError) as exc:
            self.notice.setText(str(exc))
            for b in self.buttons:b.setEnabled(False)

    def perform(self,fn):
        try:check_idle(self.hub);fn()
        except (WorkspaceError,OSError,sqlite3.Error) as exc:self.notice.setText(str(exc))

    def mutation_revision(self):
        # Last Session autosaves may advance revision while this dialog is open.
        # Only rebase when every user-managed field still matches the reviewed list.
        current=self.store.load()
        if any(current[k]!=self.data[k] for k in ('named','startup')):
            raise WorkspaceError('Workspaces changed; reload before retrying')
        return current['revision']

    def selected(self):
        row=self.list.currentRow()
        if row<0:raise WorkspaceError('Select a workspace first')
        return self.keys[row]

    def save_new(self):
        label,ok=QInputDialog.getText(self,'Save workspace','Name')
        if not ok:return
        duplicate=next((k for k,e in self.data['named'].items() if e['name'].casefold()==label.strip().casefold()),None)
        replacement=None
        if duplicate:
            if QMessageBox.question(self,'Overwrite workspace','Replace the existing snapshot with this name?',QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.Cancel,QMessageBox.StandardButton.Cancel)!=QMessageBox.StandardButton.Yes:return
        elif len(self.keys)==5:
            names=[self.data['named'][k]['name'] for k in self.keys]
            selected,ok=QInputDialog.getItem(self,'Maximum of 5 workspaces reached','Select a workspace to replace',names,0,False)
            if not ok:return
            replacement=self.keys[names.index(selected)]
        self.store.save_named(self.mutation_revision(),label,capture(self.hub),replace=replacement,overwrite=duplicate);self.reload()

    def overwrite(self):
        key=self.selected()
        if QMessageBox.question(self,'Overwrite workspace','Replace this saved snapshot?',QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.Cancel,QMessageBox.StandardButton.Cancel)!=QMessageBox.StandardButton.Yes:return
        self.store.save_named(self.mutation_revision(),self.data['named'][key]['name'],capture(self.hub),overwrite=key);self.reload()

    def rename(self):
        key=self.selected();label,ok=QInputDialog.getText(self,'Rename workspace','Name',text=self.data['named'][key]['name'])
        if ok:self.store.rename(self.mutation_revision(),key,label);self.reload()

    def delete(self):
        key=self.selected()
        if QMessageBox.question(self,'Delete workspace',f'Delete workspace “{self.data["named"][key]["name"]}”? This does not delete books.',QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.Cancel,QMessageBox.StandardButton.Cancel)!=QMessageBox.StandardButton.Yes:return
        self.store.delete(self.mutation_revision(),key);self.reload()

    def restore(self):
        self.hub.workspaces.restore_key(self.selected())

    def startup(self):
        self.store.set_startup(self.mutation_revision(),self.selected());self.reload()

    def default_startup(self):
        self.store.set_startup(self.mutation_revision(),'last_session');self.reload()
