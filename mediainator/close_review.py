"""Collect close decisions without mutating drafts or running tasks."""
from PyQt6.QtWidgets import QDialog,QDialogButtonBox,QVBoxLayout,QLabel,QComboBox,QCheckBox


def collect(parent, editors, tasks=(), reader=False):
    dialog=QDialog(parent);dialog.setWindowTitle('Review before closing')
    layout=QVBoxLayout(dialog)
    layout.addWidget(QLabel('Review all pending work. Cancel leaves every draft and task unchanged.'))
    choices=[]
    for editor in editors:
        layout.addWidget(QLabel(editor.windowTitle()))
        choice=QComboBox();choice.addItems(['Save','Discard']);layout.addWidget(choice)
        choices.append((editor,choice))
    stops=[]
    for label,stop in tasks:
        check=QCheckBox('Stop '+label+'; close again when it has stopped')
        layout.addWidget(check);stops.append((check,stop))
    reader_choice=None
    if reader:
        reader_choice=QComboBox();reader_choice.addItems(['Close reader','Leave reader open'])
        layout.addWidget(reader_choice)
    buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Ok|QDialogButtonBox.StandardButton.Cancel)
    buttons.accepted.connect(dialog.accept);buttons.rejected.connect(dialog.reject);layout.addWidget(buttons)
    if dialog.exec()!=QDialog.DialogCode.Accepted:
        return None
    return ([(e,'save' if c.currentIndex()==0 else 'discard') for e,c in choices],
            [stop for check,stop in stops if check.isChecked()],
            ('close' if reader_choice.currentIndex()==0 else 'keep') if reader_choice else None)


def apply_editors(choices):
    # Save before discarding, so a failed Save does not discard another draft.
    for editor,action in sorted(choices,key=lambda row: row[1]!='save'):
        method=getattr(editor,'save_for_close',None) or editor.save_changes
        if not (method() if action=='save' else editor.discard()):
            return False
    return True
