"""Virtual catalog views: stable book identities, viewport icons, shared selection."""
from collections import OrderedDict
from PyQt6.QtCore import QAbstractTableModel, Qt, QModelIndex, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QListView, QTableView

class CatalogModel(QAbstractTableModel):
    checked = pyqtSignal()
    def __init__(self, owner, grid=False):
        super().__init__(owner); self.owner=owner; self.grid=grid; self.books=[]; self.icons=OrderedDict()
    def replace(self, books):
        self.beginResetModel(); self.books=books; self.icons.clear(); self.endResetModel()
    def rowCount(self, parent=QModelIndex()):return 0 if parent.isValid() else len(self.books)
    def columnCount(self, parent=QModelIndex()):return 1 if self.grid else 5
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation==Qt.Orientation.Horizontal and role==Qt.ItemDataRole.DisplayRole:
            return ['Title','Author','Formats','Tags','Reading status'][section]
        return super().headerData(section,orientation,role)
    def data(self,index,role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0<=index.row()<len(self.books):return None
        book=self.books[index.row()];col=index.column()
        if role==Qt.ItemDataRole.UserRole:return book.uuid
        if role==Qt.ItemDataRole.CheckStateRole and col==0 and book.uuid:
            return Qt.CheckState.Checked if book.uuid in self.owner.bulk_selection else Qt.CheckState.Unchecked
        if role in (Qt.ItemDataRole.DisplayRole,Qt.ItemDataRole.ToolTipRole):
            values=(book.title,book.author,' / '.join(book.formats),', '.join(book.tags),self.owner.progress_summary(book))
            return '\n'.join(values) if self.grid else values[col]
        if role==Qt.ItemDataRole.DecorationRole and self.grid:
            key=(book.cover,book.title[:1])
            if key not in self.icons:
                from .window import placeholder
                icon=QIcon(book.cover) if book.cover else QIcon()
                self.icons[key]=icon if not icon.isNull() else placeholder(book.title or '?')
                if len(self.icons)>128:self.icons.popitem(last=False)
            self.icons.move_to_end(key);return self.icons[key]
    def flags(self,index):
        flags=Qt.ItemFlag.ItemIsEnabled|Qt.ItemFlag.ItemIsSelectable
        if index.isValid() and index.column()==0 and self.books[index.row()].uuid:flags|=Qt.ItemFlag.ItemIsUserCheckable
        return flags
    def setData(self,index,value,role=Qt.ItemDataRole.EditRole):
        if role!=Qt.ItemDataRole.CheckStateRole or not index.isValid() or index.column()!=0:return False
        uid=self.books[index.row()].uuid
        if not uid:return False
        if value in (Qt.CheckState.Checked,Qt.CheckState.Checked.value):self.owner.bulk_selection.add(uid)
        else:self.owner.bulk_selection.discard(uid)
        self.checked.emit();return True
    def refresh_checks(self):
        if self.books:self.dataChanged.emit(self.index(0,0),self.index(len(self.books)-1,0),[Qt.ItemDataRole.CheckStateRole])

class CatalogItem:
    """Small compatibility interface for existing selection clients."""
    def __init__(self,model,row,col=0):self.model,self.index=model,model.index(row,col)
    def setCheckState(self,value):self.model.setData(self.index,value,Qt.ItemDataRole.CheckStateRole)
    def checkState(self):return self.model.data(self.index,Qt.ItemDataRole.CheckStateRole)
    def data(self,role):return self.model.data(self.index,role)
    def text(self):return self.model.data(self.index)

class CatalogGrid(QListView):
    currentRowChanged=pyqtSignal(int)
    def __init__(self,owner):
        super().__init__(); self.setModel(CatalogModel(owner,True));self.setUniformItemSizes(True)
        self.selectionModel().currentRowChanged.connect(lambda current,previous:self.currentRowChanged.emit(current.row()))
    def count(self):return self.model().rowCount()
    def currentRow(self):return self.currentIndex().row()
    def setCurrentRow(self,row):self.setCurrentIndex(self.model().index(row,0))
    def item(self,row):return CatalogItem(self.model(),row)

class CatalogTable(QTableView):
    currentCellChanged=pyqtSignal(int,int,int,int)
    def __init__(self,owner):
        super().__init__();self.setModel(CatalogModel(owner));self.verticalHeader().setDefaultSectionSize(26)
        self.selectionModel().currentChanged.connect(lambda c,p:self.currentCellChanged.emit(c.row(),c.column(),p.row(),p.column()))
        for col,width in enumerate((250,220,100,220,220)):self.setColumnWidth(col,width)
    def rowCount(self):return self.model().rowCount()
    def setCurrentCell(self,row,col):self.setCurrentIndex(self.model().index(row,col))
    def item(self,row,col):return CatalogItem(self.model(),row,col)
