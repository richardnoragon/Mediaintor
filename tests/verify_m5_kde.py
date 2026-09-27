"""Real KWin close requests on a PRIVATE bus/runtime; never logs out the user's session."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

PROJECT=Path(__file__).resolve().parent.parent
OUT=Path(os.environ.get('MEDIAINATOR_ACCEPTANCE_OUTPUT',PROJECT/'test_data/m5_acceptance'))
MODULE_ROOT=Path(os.environ.get('MEDIAINATOR_ACCEPTANCE_RELEASE',PROJECT)).resolve()


def client(root, scenario):
    sys.path.insert(0,str(MODULE_ROOT))
    import mediainator
    assert Path(mediainator.__file__).resolve().parent.parent == MODULE_ROOT
    from PyQt6.QtCore import QTimer
    from PyQt6.QtWidgets import QApplication, QMessageBox
    from mediainator.window import Hub
    from mediainator.settings import SettingsStore
    from mediainator.editor import MetadataEditor
    from mediainator.catalog import Book
    app=QApplication([]);app.setQuitOnLastWindowClosed(False)
    store=SettingsStore(root/'settings.json');hub=Hub(store,store.load());hub.setWindowTitle('M5 isolated KWin test')
    editor=MetadataEditor(root/'library',Book('lib:1','Title','Author',(),(),uuid='book'),root/'covers',hub.bookinator)
    editor.activity=hub.activity;editor.recovery_store=hub.recovery_store;editor.library_uuid='lib'
    editor.on_preserved=hub.show_preservation_notice
    editor.fill(dict(title='Title',authors=['Author'],tags=[],series='',series_index=None,comments='',cover=None,uuid='book'))
    editor.title.setText('Unsaved KWin test')
    editor.request=lambda *args,**kwargs:None  # Controlled storage failure; no real library attached.
    hub.bookinator.editor=editor
    closes=[];commits=[];original=hub.closeEvent
    def close(event):
        original(event);closes.append(event.isAccepted())
    hub.closeEvent=close
    app.commitDataRequest.connect(lambda manager:commits.append(True))
    hub.show();editor.show()
    (root/'ready').write_text('ready')
    started=time.monotonic();clicked=[];cancel_seen=[None]
    def tick():
        dialog=app.activeModalWidget()
        if isinstance(dialog,QMessageBox):
            if scenario=='cancel':
                button=dialog.button(QMessageBox.StandardButton.Cancel)
            else:
                button=dialog.button(QMessageBox.StandardButton.Save)
                if button is None:button=next((b for b in dialog.buttons() if b.text()=='Retry Save'),None)
            if button:
                clicked.append(button.text());button.click()
        protected=editor.protected_current_draft()
        passed=(scenario=='cancel' and bool(closes) and not any(closes) and hub.isVisible() and editor.dirty()) or (scenario=='preserve' and any(closes) and protected and not hub.isVisible())
        if scenario=='cancel' and passed:
            if cancel_seen[0] is None:
                cancel_seen[0]=time.monotonic();(root/'cancel-observed').write_text('retained')
            if time.monotonic()-cancel_seen[0]<3:return
        if passed or time.monotonic()-started>20:
            (root/'client.json').write_text(json.dumps(dict(scenario=scenario,passed=passed,platform=app.platformName(),close_events=closes,
                commit_signals=len(commits),clicked=clicked,protected=protected,hub_visible=hub.isVisible(),no_duplicate_save_prompt=clicked.count('&Save')<=1),indent=2))
            app.exit(0 if passed else 1)
    timer=QTimer();timer.timeout.connect(tick);timer.start(100)
    QTimer.singleShot(22000,lambda:app.exit(2))
    return app.exec()


def session(root, scenario):
    # This branch is launched only under dbus-run-session and a new runtime directory.
    if os.environ.get('DBUS_SESSION_BUS_ADDRESS')==os.environ.get('M5_OUTER_BUS'):
        raise RuntimeError('Refusing to use the desktop bus')
    if Path(os.environ['XDG_RUNTIME_DIR'])!=root/'runtime':raise RuntimeError('Runtime isolation missing')
    env=dict(os.environ);env.pop('DISPLAY',None);env.pop('WAYLAND_DISPLAY',None);env.pop('SESSION_MANAGER',None)
    env.pop('QT_QPA_PLATFORM',None);env['KWIN_COMPOSE']='Q';env['QT_LOGGING_RULES']='*.debug=false'
    with (root/'kwin.log').open('w') as log:
        compositor=subprocess.Popen(['/usr/bin/kwin_wayland','--virtual','--no-lockscreen','--no-global-shortcuts','--no-kactivities','--socket','m5-wayland'],env=env,stdout=log,stderr=log)
        process=None;request=None
        try:
            for _ in range(150):
                if (root/'runtime/m5-wayland').exists():break
                if compositor.poll() is not None:raise RuntimeError('Isolated KWin did not start; see kwin.log')
                time.sleep(.1)
            else:raise RuntimeError('Isolated Wayland socket did not appear')
            env['WAYLAND_DISPLAY']='m5-wayland';env['QT_QPA_PLATFORM']='wayland'
            with (root/'client.log').open('w') as app_log:
                process=subprocess.Popen([sys.executable,__file__,'client',str(root),scenario],env=env,stdout=app_log,stderr=app_log)
                for _ in range(100):
                    if (root/'ready').exists():break
                    if process.poll() is not None:raise RuntimeError('Test client did not start')
                    time.sleep(.1)
                time.sleep(1)
                # ONLY this private bus contains org.kde.KWin; do not call plasma-shutdown/login1/systemd.
                with (root/'dbus.log').open('w') as bus_log:
                    request=subprocess.Popen(['/usr/bin/qdbus6','org.kde.KWin','/Session','org.kde.KWin.Session.closeWaylandWindows'],env=env,stdout=bus_log,stderr=bus_log)
                    deadline=time.monotonic()+30;pending_observed=False
                    while process.poll() is None and time.monotonic()<deadline:
                        if (root/'cancel-observed').exists() and request.poll() is None:pending_observed=True
                        time.sleep(.1)
                    code=process.wait(timeout=1)
                    if scenario=='cancel':
                        result=json.loads((root/'client.json').read_text());result['kwin_waited_while_cancelled']=pending_observed
                        result['passed']=result['passed'] and pending_observed
                        (root/'client.json').write_text(json.dumps(result,indent=2))
                        if not pending_observed:raise RuntimeError('KWin did not wait for cancelled close')
                    if code:raise RuntimeError('KWin close test failed; see client.json/client.log')
        finally:
            for owned in (process,request,compositor):
                if owned and owned.poll() is None:
                    owned.terminate()
                    try:owned.wait(timeout=5)
                    except subprocess.TimeoutExpired:owned.kill();owned.wait()


def main():
    OUT.mkdir(exist_ok=True);results=[]
    for scenario in ('cancel','preserve'):
        root=Path(tempfile.mkdtemp(prefix='mediainator-m5-kde-'))
        for folder in ('runtime','config','data','cache'):(root/folder).mkdir(mode=0o700)
        env=dict(os.environ,XDG_RUNTIME_DIR=str(root/'runtime'),XDG_CONFIG_HOME=str(root/'config'),XDG_DATA_HOME=str(root/'data'),XDG_CACHE_HOME=str(root/'cache'),M5_OUTER_BUS=os.environ.get('DBUS_SESSION_BUS_ADDRESS',''))
        with (root/'session.log').open('w') as log:
            run=subprocess.run(['dbus-run-session','--',sys.executable,__file__,'session',str(root),scenario],env=env,stdout=log,stderr=log,timeout=55)
        result=dict(scenario=scenario,root=str(root),returncode=run.returncode,output=(root/'session.log').read_text())
        if (root/'client.json').exists():result.update(json.loads((root/'client.json').read_text()))
        if scenario=='preserve':result['passed']=result.get('passed',False) and result.get('no_duplicate_save_prompt',False)
        results.append(result);print(json.dumps({k:v for k,v in result.items() if k!='output'}),flush=True)
        (OUT/'kde_report.json').write_text(json.dumps(dict(module_root=str(MODULE_ROOT),kind='isolated real KWin Wayland window-close protocol, not host logout',checks=results),indent=2))
        if run.returncode or not result.get('passed'):return 1
    return 0

if __name__=='__main__':
    if len(sys.argv)>1:
        if sys.argv[1]=='client':sys.exit(client(Path(sys.argv[2]),sys.argv[3]))
        session(Path(sys.argv[2]),sys.argv[3])
    else:sys.exit(main())
