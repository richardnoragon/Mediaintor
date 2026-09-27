"""Transactional workspace restore; readers and shared filters stay independent."""
from copy import deepcopy
from contextlib import closing
from pathlib import Path
import sqlite3
from PyQt6.QtCore import QObject,QTimer,QByteArray,QRect
from PyQt6.QtGui import QGuiApplication
from .workspaces import WorkspaceStore,WorkspaceError,snapshot
from .workspace_ui import capture,check_idle,WorkspaceBusy


def bounded_rect(rect,available):
    """Logical-pixel fallback preserving on-screen positions where possible."""
    if available.width()<=0 or available.height()<=0:raise WorkspaceError('No usable display available')
    r=QRect(rect);r.setWidth(max(1,min(r.width(),available.width())));r.setHeight(max(1,min(r.height(),available.height())))
    r.moveLeft(max(available.left(),min(r.left(),available.right()-r.width()+1)))
    r.moveTop(max(available.top(),min(r.top(),available.bottom()-r.height()+1)))
    return r


class WorkspaceController(QObject):
    def __init__(self,hub):
        super().__init__(hub);self.hub=hub;self.applying=False;self.pending=None;self.disabled=False
        self.transaction=None;self.generation=0;self.last_error=''
        self.store=WorkspaceStore(hub.store.path.parent/'workspaces.json',hub.state['profile_id'],hub.state['device_id'],capture(hub,allow_busy=True))
        self.starting=True;self.timer=QTimer(self);self.timer.setInterval(250);self.timer.timeout.connect(self.tick);self.timer.start()
        app=QGuiApplication.instance();app.screenRemoved.connect(self.screen_changed);app.screenAdded.connect(self.watch_screen)
        for screen in app.screens():self.watch_screen(screen)

    def watch_screen(self,screen):
        screen.availableGeometryChanged.connect(self.screen_changed)

    def screen_changed(self,*_):
        QTimer.singleShot(0,self.recover_monitor)

    def recover_monitor(self):
        try:
            if not self.hub.closing and not self.applying:
                self.apply_geometry(capture(self.hub,allow_busy=True)['geometry'],fallback_only=True)
        except (WorkspaceError,OSError,sqlite3.Error,RuntimeError) as exc:self.fail(exc)

    def fail(self,exc):
        self.last_error=str(exc);self.hub.statusBar().showMessage('Workspace not saved/restored: '+str(exc))

    def tick(self):
        if self.disabled or self.hub.closing or self.applying:return
        try:
            if self.starting:
                check_idle(self.hub);exists=self.store.path.exists();data=self.store.load();self.starting=False
                if exists:
                    entry=data['last_session'] if data['startup']=='last_session' else data['named'][data['startup']]
                    self.restore(entry['snapshot'],startup=True)
            if self.transaction is not None:return
            self.flush()
        except WorkspaceError as exc:
            if 'operation is running' not in str(exc):self.disabled=True;self.fail(exc)
        except (OSError,sqlite3.Error) as exc:self.disabled=True;self.fail(exc)

    def flush(self,closing=False):
        if self.disabled:return False
        if self.transaction is not None:
            if closing:self.abort('Restore cancelled by shutdown')
            else:return True
        if self.starting and closing:self.starting=False
        if self.starting or self.applying:return True
        try:
            value=capture(self.hub,allow_busy=closing);data=self.store.load()
            if not self.store.path.exists() or value!=data['last_session']['snapshot']:self.store.save_last_session(data['revision'],value)
            return True
        except WorkspaceBusy:
            # An ordinary background refresh/write is not a persistence failure.
            return False
        except (WorkspaceError,OSError,sqlite3.Error) as exc:self.fail(exc);return False

    def apply_geometry(self,g,fallback_only=False):
        screens=QGuiApplication.screens()
        if not screens:raise WorkspaceError('No usable display available')
        screen=next((s for s in screens if s.name()==g['screen']),None)
        screen=screen or self.hub.screen() or screens[0]
        available=screen.availableGeometry()
        if fallback_only:rect=self.hub.geometry()
        else:
            self.hub.showNormal()
            restored=bool(g['qt']) and self.hub.restoreGeometry(QByteArray.fromHex(g['qt'].encode()))
            rect=self.hub.geometry() if restored else QRect(*g['normal'])
        fixed=bounded_rect(rect,available)
        if fixed!=self.hub.geometry():self.hub.setGeometry(fixed)
        if g['maximized'] and not fallback_only:self.hub.showMaximized()

    def set_modules(self,value):
        panel=self.hub.bookinator
        if 'bookinator' not in value['modules'] and panel:
            self.hub.stop_background_reads();self.hub.release_snapshot()
            self.hub.tabs.removeTab(self.hub.tabs.indexOf(panel));panel.deleteLater();self.hub.bookinator=None
            self.hub.state['bookinator_open']=False
        elif 'bookinator' in value['modules'] and not panel:self.hub.open_books()
        music=getattr(self.hub,'musicinator',None)
        if 'musicinator' not in value['modules'] and music:self.hub.remove_music()
        elif 'musicinator' in value['modules'] and not music:self.hub.open_music()
        movies=getattr(self.hub,'movieinator',None)
        if 'movieinator' not in value['modules'] and movies:self.hub.remove_movies()
        elif 'movieinator' in value['modules'] and not movies:self.hub.open_movies()
        papers=getattr(self.hub,'paperinator',None)
        if 'paperinator' not in value['modules'] and papers:self.hub.remove_papers()
        elif 'paperinator' in value['modules'] and not papers:self.hub.open_papers()
        target={'bookinator':self.hub.bookinator,'musicinator':getattr(self.hub,'musicinator',None),
                'movieinator':getattr(self.hub,'movieinator',None),'paperinator':getattr(self.hub,'paperinator',None)}.get(value['active'])
        if target is not None:self.hub.tabs.setCurrentWidget(target)
        else:self.hub.tabs.setCurrentIndex(0)

    def restore(self,value,startup=False):
        value=snapshot(value)
        if self.transaction is not None:raise WorkspaceError('A workspace restore is already running; wait or cancel it')
        check_idle(self.hub);panel=self.hub.bookinator
        drafts=[]
        for name in ('movieinator','musicinator','paperinator','bookinator'):
            module=getattr(self.hub,name,None)
            if module is None:continue
            editors=getattr(module,'editors',None)
            if editors is None:editors=[module.editor] if module.editor else []
            drafts.extend(editor for editor in editors if editor.dirty())
        if len(drafts)>1:
            from .close_review import collect,apply_editors
            decision=collect(self.hub,drafts)
            if decision is None or not apply_editors(decision[0]):return False
        else:
            movies=getattr(self.hub,'movieinator',None)
            if movies is not None and movies.editor is not None and not movies.review_close():return False
            music=getattr(self.hub,'musicinator',None)
            if music is not None and music.editor is not None and not music.review_close():return False
            papers=getattr(self.hub,'paperinator',None)
            if papers is not None and papers.editors and not papers.review_close():return False
            if panel and panel.editor:
                if not panel.editor.review():return False
                if panel.editor.busy or panel.editor.dirty():raise WorkspaceError('Resolve remaining metadata edits before restoring')
        check_idle(self.hub)
        before=capture(self.hub);self.generation+=1;token=self.generation
        self.transaction=dict(before=before,settings=deepcopy(self.hub.state),target=value,token=token,panel=None)
        self.pending=value['selection'];self.applying=True
        try:
            self.set_modules(value);self.apply_geometry(value['geometry'])
            self.hub.state['selected_book']=None;panel=self.hub.bookinator
            self.transaction['panel']=panel
            # Existing loaded catalog can be used immediately; new loads must finish.
            if panel and panel.loader and (panel.loader.active or not panel.books):
                panel.loader.loaded.connect(lambda books,t=token,p=panel:self.catalog_complete(t,p))
                panel.loader.failed.connect(lambda message,t=token,p=panel:self.catalog_failed(t,p,message))
                QTimer.singleShot(35000,lambda t=token:self.timeout(t))
                return True
            self.finish(token,panel);return True
        except Exception as exc:
            self.abort(exc);raise WorkspaceError(str(exc)) from exc
        finally:self.applying=False

    def catalog_complete(self,token,panel):
        if self.matches(token,panel):
            try:self.finish(token,panel)
            except Exception as exc:self.abort(exc)

    def catalog_failed(self,token,panel,message):
        if self.matches(token,panel):self.abort('Catalog restore failed: '+message)

    def matches(self,token,panel):
        return bool(self.transaction and self.transaction['token']==token and self.transaction['panel'] is panel and self.hub.bookinator is panel)

    def timeout(self,token):
        if self.transaction and self.transaction['token']==token:self.abort('Catalog restore timed out; previous workspace retained')

    def resolve_movie_selection(self,value):
        movies=getattr(self.hub,'movieinator',None)
        target=value.get('movie_selection') if value else None
        if movies is None:return
        if target and movies.store is not None:
            from .movie_store import MovieStoreError
            try:catalog=movies.store.catalog_uuid()
            except MovieStoreError:catalog=None
            found=catalog==target['catalog_uuid'] and any(m.id==target['movie_id'] for m in movies.movies)
            self.hub.state['selected_movie']=target['movie_id'] if found else None
            movies.render()
            if not found:movies.note.setText('Workspace restored. Selected movie is unavailable in this catalog.')
            elif not any(m.id==target['movie_id'] for m in movies.visible):
                movies.note.setText('Workspace restored. Selected movie is hidden by active filters. Use Clear All to reveal it.')

    def resolve_music_selection(self,value):
        music=getattr(self.hub,'musicinator',None)
        target=value.get('music_selection') if value else None
        if music is None:return
        if target and music.store is not None:
            from .music_store import MusicStoreError
            try:catalog=music.store.catalog_uuid()
            except MusicStoreError:catalog=None
            found=catalog==target['catalog_uuid'] and any(a.id==target['album_id'] for a in music.albums)
            self.hub.state['selected_album']=target['album_id'] if found else None
            music.render()
            if not found:music.note.setText('Workspace restored. Selected album is unavailable in this catalog.')
            elif not any(a.id==target['album_id'] for a in music.visible):
                music.note.setText('Workspace restored. Selected album is hidden by active filters or browsing. Use Clear All to reveal it.')

    def resolve_paper_selection(self,value):
        papers=getattr(self.hub,'paperinator',None)
        target=value.get('paper_selection') if value else None
        if papers is None:return
        if target and papers.store is not None:
            from .paper_store import PaperStoreError
            try:library=papers.store.library_uuid()
            except PaperStoreError:library=None
            found=library==target['library_uuid'] and papers.library.item(target['item_id']) is not None
            self.hub.state['selected_paper']=target['item_id'] if found else None
            papers.render()
            if not found:papers.note.setText('Workspace restored. Selected item is unavailable in this library.')
            elif not any(i.id==target['item_id'] for i in papers.visible):
                papers.note.setText('Workspace restored. Selected item is hidden by active filters. Use Clear All to reveal it.')

    def resolve_selection(self):
        target=self.pending;panel=self.hub.bookinator
        if not target or panel is None:return
        book=None
        if panel.library:
            with closing(sqlite3.connect((Path(panel.library)/'metadata.db').resolve().as_uri()+'?mode=ro',uri=True)) as db:
                row=db.execute('SELECT uuid FROM library_id LIMIT 1').fetchone()
            if row and row[0]==target['library_uuid']:book=next((b for b in panel.books if b.uuid==target['book_uuid']),None)
        self.hub.state['selected_book']=book.id if book else None
        panel.render()
        if book and book not in panel.visible:panel.note.setText('Workspace restored. Selected book is hidden by active filters. Use Clear All to reveal it, or keep the filters.')
        elif not book:panel.note.setText('Workspace restored. Selected book is unavailable in this library.')

    def finish(self,token,panel):
        if not self.matches(token,panel):return
        self.applying=True
        try:
            self.resolve_selection()
            self.resolve_movie_selection(self.transaction.get('target') if self.transaction else None)
            self.resolve_music_selection(self.transaction.get('target') if self.transaction else None)
            self.resolve_paper_selection(self.transaction.get('target') if self.transaction else None)
            if panel and self.pending is None:panel.render()
            if not self.hub.persist():raise WorkspaceError('Settings save failed; restoration cancelled')
            data=self.store.load();self.store.save_last_session(data['revision'],capture(self.hub,allow_busy=True))
            self.transaction=None;self.pending=None
            self.last_error=''
            self.hub.statusBar().showMessage('Workspace restored.')
        finally:self.applying=False

    def abort(self,reason):
        tx=self.transaction
        if not tx:return
        self.transaction=None;self.pending=None;self.generation+=1;self.applying=True
        try:
            self.set_modules(tx['before']);self.apply_geometry(tx['before']['geometry'])
            # Roll back structural preferences only; never overwrite filters or metadata writes.
            for key in ('selected_book','bookinator_open','geometry','selected_movie','movieinator_open','selected_album','musicinator_open','selected_paper','paperinator_open'):
                if key in tx['settings']:self.hub.state[key]=tx['settings'][key]
            if self.hub.bookinator:self.hub.bookinator.render()
            if not self.hub.persist():raise WorkspaceError('Rollback settings could not be saved; repair storage and reload workspaces')
        except Exception as exc:
            self.disabled=True;reason=str(reason)+'; layout rollback needs attention: '+str(exc)
        finally:self.applying=False;self.fail(reason)

    def restore_key(self,key):
        data=self.store.load()
        if key!='last_session' and key not in data['named']:raise WorkspaceError('Workspace no longer exists; reload the list')
        return self.restore((data['last_session'] if key=='last_session' else data['named'][key])['snapshot'])
