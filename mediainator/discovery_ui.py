"""Discovery/review workbench. Book writes delegate to the existing bulk editor."""
from copy import deepcopy
from uuid import uuid4
from PyQt6.QtCore import Qt,QAbstractTableModel,QModelIndex,QTimer
from PyQt6.QtWidgets import (QDialog,QVBoxLayout,QHBoxLayout,QLabel,QLineEdit,QComboBox,QPushButton,
    QListWidget,QTableView,QCheckBox,QInputDialog,QMessageBox,QAbstractItemView)
from .discovery import DiscoveryIndex,empty_query
from .review_service import acknowledge

class ReviewModel(QAbstractTableModel):
    def __init__(self,dialog):super().__init__(dialog);self.dialog=dialog;self.books=[]
    def replace(self,books):self.beginResetModel();self.books=books;self.endResetModel()
    def rowCount(self,parent=QModelIndex()):return 0 if parent.isValid() else len(self.books)
    def columnCount(self,parent=QModelIndex()):return 7
    def headerData(self,n,orientation,role=Qt.ItemDataRole.DisplayRole):
        if orientation==Qt.Orientation.Horizontal and role==Qt.ItemDataRole.DisplayRole:return ['Title','Author','Series','Tags','Formats','Reading status','Review reasons'][n]
        return super().headerData(n,orientation,role)
    def data(self,i,role=Qt.ItemDataRole.DisplayRole):
        if not i.isValid():return
        b=self.books[i.row()]
        if role==Qt.ItemDataRole.CheckStateRole and i.column()==0:return Qt.CheckState.Checked if b.uuid in self.dialog.selected else Qt.CheckState.Unchecked
        if role in (Qt.ItemDataRole.DisplayRole,Qt.ItemDataRole.ToolTipRole):return (b.title,b.author,b.series,', '.join(b.tags),' / '.join(b.formats),b.reading_status,'; '.join(self.dialog.index.reasons.get(b.uuid,())))[i.column()]
    def flags(self,i):
        if not i.isValid():return Qt.ItemFlag.NoItemFlags
        return Qt.ItemFlag.ItemIsEnabled|Qt.ItemFlag.ItemIsSelectable|(Qt.ItemFlag.ItemIsUserCheckable if i.column()==0 and self.books[i.row()].uuid else Qt.ItemFlag.NoItemFlags)
    def setData(self,i,value,role=Qt.ItemDataRole.EditRole):
        if role!=Qt.ItemDataRole.CheckStateRole or not i.isValid() or i.column()!=0:return False
        uid=self.books[i.row()].uuid
        if value in (Qt.CheckState.Checked,2):self.dialog.selected.add(uid)
        else:self.dialog.selected.discard(uid)
        self.dataChanged.emit(i,i,[role]);self.dialog.count();return True

class DiscoveryDialog(QDialog):
    def __init__(self,books):
        super().__init__(books);self.host=books;self.selected=set();self.conditions=[];self.filling=False;self.outer={k:sorted(books.filter_values[k]) for k in ('tags','statuses')}
        self.timer=QTimer(self);self.timer.setSingleShot(True);self.timer.setInterval(150);self.timer.timeout.connect(self.refresh)
        self.store,self.state,self.warnings=books.discovery_context()
        self.index=DiscoveryIndex(books.books,self.state,self.warnings)
        self.setWindowTitle('Find and review books');self.resize(1150,760)
        layout=QVBoxLayout(self);self.message=QLabel('Search and review; metadata changes require a separate preview and confirmation.');self.message.setWordWrap(True);layout.addWidget(self.message)
        bar=QHBoxLayout();bar.addWidget(QLabel('Saved search'));self.saved=QComboBox();bar.addWidget(self.saved,1)
        for label,slot in [('Save new search',self.save_new),('Update selected',self.update_saved),('Rename',self.rename_saved),('Delete search',self.delete_saved),('Reload',self.reload)]:
            b=QPushButton(label);b.clicked.connect(slot);bar.addWidget(b)
        layout.addLayout(bar);self.saved.activated.connect(self.apply_saved)
        layout.addWidget(QLabel('Text search — title, author or series'))
        self.text=QLineEdit(books.search.text());self.text.setPlaceholderText('Find by title, author or series');self.text.setAccessibleName('Discovery text search');layout.addWidget(self.text)
        layout.addWidget(QLabel('Filters — choose a field and value, then click Add condition. Text search narrows both modes.'))
        bar=QHBoxLayout();self.mode=QComboBox();self.mode.addItems(['Match all','Match any']);bar.addWidget(self.mode)
        self.field=QComboBox()
        for label,key in [('Reading status','reading_status'),('Missing metadata','missing_metadata'),('Series','series'),('Tags','tag')]:self.field.addItem(label,key)
        self.value=QComboBox();self.value.setEditable(True);self.value.setAccessibleName('Condition value; type to search values');bar.addWidget(self.field);bar.addWidget(QLabel('Value'));bar.addWidget(self.value,1)
        b=QPushButton('Add condition');b.clicked.connect(self.add_condition);bar.addWidget(b);layout.addLayout(bar)
        self.outer_label=QLabel();layout.addWidget(self.outer_label)
        clear_outer=QPushButton('Clear inherited catalog narrowing');clear_outer.clicked.connect(self.clear_outer);layout.addWidget(clear_outer)
        self.rows=QListWidget();self.rows.setMaximumHeight(100);layout.addWidget(self.rows)
        b=QPushButton('Remove selected condition');b.clicked.connect(self.remove_condition);layout.addWidget(b)
        bar=QHBoxLayout();self.review=QCheckBox('Needs Review queue');self.series_review=QCheckBox('Treat missing series as review-worthy');self.series_review.setChecked(self.state['review_missing_series']);bar.addWidget(self.review);bar.addWidget(self.series_review);layout.addLayout(bar)
        bar=QHBoxLayout();bar.addWidget(QLabel('Formats (comma separated; narrows both modes)'));self.formats=QLineEdit(', '.join(sorted(books.filter_values['formats'])));bar.addWidget(self.formats,1)
        self.sort=QComboBox();self.sort.addItems(['Title A–Z','Title Z–A','Author A–Z']);self.sort.setCurrentIndex(books.sort.currentIndex());bar.addWidget(self.sort);layout.addLayout(bar)
        self.summary=QLabel();layout.addWidget(self.summary)
        self.table=QTableView();self.model=ReviewModel(self);self.table.setModel(self.model);self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows);self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        for col,width in enumerate((210,180,140,160,85,110,270)):self.table.setColumnWidth(col,width)
        layout.addWidget(self.table,1);bar=QHBoxLayout()
        for label,slot in [('Select all results',self.select_all),('Clear selection',self.clear_selection),('Flag Needs Review',lambda:self.review_selected(False)),('Mark reviewed',lambda:self.review_selected(True)),('Bulk edit selected…',self.bulk)]:
            b=QPushButton(label);b.clicked.connect(slot);bar.addWidget(b)
        layout.addLayout(bar)
        b=QPushButton('Close workbench');b.clicked.connect(self.close);layout.addWidget(b)
        for b in self.findChildren(QPushButton):b.setAutoDefault(False)
        self.field.currentIndexChanged.connect(self.values);self.text.textChanged.connect(lambda:self.timer.start());self.mode.currentIndexChanged.connect(self.refresh);self.review.toggled.connect(self.refresh);self.series_review.toggled.connect(self.preference)
        self.formats.textChanged.connect(lambda:self.timer.start());self.sort.currentIndexChanged.connect(self.refresh)
        self.values();self.reload_names();self.refresh()
    def values(self):
        field=self.field.currentData()
        if field=='missing_metadata':values=['title','author','cover','series']
        else:values=sorted({v for b in self.host.books for v in (b.tags if field=='tag' else (b.series,) if field=='series' else (b.reading_status,)) if v},key=str.casefold)
        self.value.clear();self.value.addItems(values)
        if self.value.completer():self.value.completer().setFilterMode(Qt.MatchFlag.MatchContains)
    def query(self):return dict(version=1,text=self.text.text(),mode='all' if self.mode.currentIndex()==0 else 'any',conditions=deepcopy(self.conditions),formats=[v.strip().upper() for v in self.formats.text().split(',') if v.strip()],sort=['title_asc','title_desc','author_asc'][self.sort.currentIndex()],review_only=self.review.isChecked(),catalog_filters=deepcopy(self.outer))
    def add_condition(self):
        value=self.value.currentText().strip()
        if not value:return
        condition=dict(field=self.field.currentData(),value=value)
        if condition in self.conditions:
            self.message.setText('This condition is already applied.');return
        self.conditions.append(condition);self.render_conditions();self.refresh()
    def remove_condition(self):
        row=self.rows.currentRow()
        if 0<=row<len(self.conditions):self.conditions.pop(row);self.render_conditions();self.refresh()
    def render_conditions(self):self.rows.clear();self.rows.addItems([r['field'].replace('_',' ')+' = '+r['value'] for r in self.conditions])
    def clear_outer(self):self.outer={};self.refresh()
    def closeEvent(self,event):self.timer.stop();event.accept()
    def refresh(self,*_):
        if self.filling:return
        self.outer_label.setText('Inherited catalog narrowing (AND): '+(', '.join(k+' = '+ ' OR '.join(v) for k,v in self.outer.items() if v) or 'none'))
        try:books=self.index.query(self.query(),self.review.isChecked())
        except ValueError as exc:self.message.setText(str(exc));return
        self.model.replace(books);self.count()
        chosen=self.state['saved_searches'].get(self.saved.currentData())
        self.message.setText('Search definition modified; use Update selected to save.' if chosen and chosen['query']!=self.query() else 'Results reflect the loaded catalog. Mark reviewed retains factual missing-field reasons.')
    def count(self):
        visible={b.uuid for b in self.model.books}
        hidden=len(self.selected-visible)
        self.summary.setText(f'{len(self.model.books)} of {len(self.host.books)} books · {len(self.selected)} selected ({hidden} hidden by current filters)')
    def select_all(self):self.selected.update(b.uuid for b in self.model.books if b.uuid);self.model.layoutChanged.emit();self.count()
    def clear_selection(self):self.selected.clear();self.model.layoutChanged.emit();self.count()
    def change(self,callback):
        self.host.review_cache=None
        try:self.state=self.store.update(self.state['revision'],callback)
        except (OSError,ValueError) as exc:self.message.setText(str(exc));return False
        self.index=DiscoveryIndex(self.host.books,self.state,self.warnings);self.refresh();return True
    def reload_names(self,selected=None):
        self.saved.clear();self.saved.addItem('Unsaved search',None)
        for key,item in sorted(self.state['saved_searches'].items(),key=lambda pair:pair[1]['name'].casefold()):self.saved.addItem(item['name'],key)
        self.saved.setCurrentIndex(max(0,self.saved.findData(selected)))
    def reload(self):
        self.host.review_cache=None
        try:self.store,self.state,self.warnings=self.host.discovery_context()
        except (OSError,ValueError) as exc:self.message.setText(str(exc));return
        self.selected.intersection_update(b.uuid for b in self.host.books);self.index=DiscoveryIndex(self.host.books,self.state,self.warnings)
        self.series_review.blockSignals(True);self.series_review.setChecked(self.state['review_missing_series']);self.series_review.blockSignals(False)
        self.reload_names(self.saved.currentData());self.values();self.refresh()
    def apply_saved(self,*_):
        item=self.state['saved_searches'].get(self.saved.currentData())
        if not item:return
        q=item['query'];self.outer=deepcopy(q.get('catalog_filters',{}));self.filling=True;self.formats.setText(', '.join(q.get('formats',[])));self.sort.setCurrentIndex(['title_asc','title_desc','author_asc'].index(q.get('sort','title_asc')));self.review.setChecked(q.get('review_only',False));self.text.setText(q['text']);self.mode.setCurrentIndex(0 if q['mode']=='all' else 1);self.conditions=deepcopy(q['conditions']);self.render_conditions();self.filling=False;self.refresh()
    def save_new(self):
        name,ok=QInputDialog.getText(self,'Save search','Name')
        if ok:
            key=str(uuid4());q=self.query()
            if self.change(lambda d:d['saved_searches'].update({key:dict(name=name.strip(),query=q)})):self.reload_names(key)
    def update_saved(self):
        key=self.saved.currentData()
        if key and self.change(lambda d:d['saved_searches'][key].update(query=self.query())):self.reload_names(key)
    def rename_saved(self):
        key=self.saved.currentData()
        if not key:return
        name,ok=QInputDialog.getText(self,'Rename search','Name',text=self.state['saved_searches'][key]['name'])
        if ok and self.change(lambda d:d['saved_searches'][key].update(name=name.strip())):self.reload_names(key)
    def delete_saved(self):
        key=self.saved.currentData()
        if not key:return
        if QMessageBox.question(self,'Delete saved search',f"Delete search {self.state['saved_searches'][key]['name']}? Books are unaffected.",QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)==QMessageBox.StandardButton.Yes:
            if self.change(lambda d:d['saved_searches'].pop(key)):self.reload_names()
    def preference(self,value):
        if not self.change(lambda d:d.update(review_missing_series=value)):
            self.series_review.blockSignals(True);self.series_review.setChecked(self.state['review_missing_series']);self.series_review.blockSignals(False)
    def review_selected(self,reviewed):
        self.host.review_cache=None
        selected=set(self.selected)
        if not selected:return
        try:self.state=acknowledge(self.store,self.state,self.index,selected,reviewed)
        except (OSError,ValueError) as exc:self.message.setText(str(exc));return
        self.index=DiscoveryIndex(self.host.books,self.state,self.warnings);self.refresh()
        self.message.setText(f'{len(selected)} selected books marked reviewed. Missing metadata still appears in the review queue.' if reviewed else f'{len(selected)} selected books flagged Needs Review.')
    def bulk(self):
        self.host.bulk_selection.clear();self.host.bulk_selection.update(self.selected);self.host.sync_bulk_checks()
        dialog=self.host.open_bulk()
        if dialog:self.hide()
