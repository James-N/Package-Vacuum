import PySide2.QtCore as QtCore
from PySide2.QtCore import Qt, Signal, Slot
import PySide2.QtWidgets as QtWidgets
import PySide2.QtGui as QtGui


class SelectionListModel(QtCore.QAbstractListModel):
    def __init__(self, parent=None):
        super(SelectionListModel, self).__init__(parent=parent)

        self._items = []
        self._selections = []

    # overrides #

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._items)

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid() and role == Qt.DisplayRole:
            return self._items[index.row()]
        else:
            return None

    # custom api #

    def notifyChange(self, first, last):
        self.dataChanged.emit(self.index(first, 0), self.index(last, 0))

    def notifyChangeAll(self):
        self.dataChanged.emit(self.index(0, 0), self.index(len(self._items) - 1, 0))

    def select(self, index, replace=False):
        if index.isValid():
            if replace:
                self._selections = []

            row = index.row()
            if row not in self._selections:
                self._selections.append(row)
                self.dataChanged.emit(index, index)

    def deselect(self, index):
        if index.isValid():
            row = index.row()
            try:
                self._selections.remove(row)
            except:
                pass

    def selectTo(self, index, replace=False):
        if index.isValid():
            if len(self._selections) > 0:
                lastSelect = self._selections[-1]
                if replace:
                    self._selections = []

                newRow = index.row()
                if lastSelect == newRow:
                    self.select(index)
                else:
                    if newRow > lastSelect:
                        idcs = xrange(lastSelect, newRow + 1, 1)
                    else:
                        idcs = xrange(lastSelect, newRow - 1, -1)

                    for i in idcs:
                        if i not in self._selections:
                            self._selections.append(i)

                    if replace:
                        self.notifyChangeAll()
                    else:
                        if newRow > lastSelect:
                            self.notifyChange(lastSelect + 1, newRow)
                        else:
                            self.notifyChange(newRow, lastSelect - 1)
            else:
                self.select(index, replace)

    def selectRange(self, start, end, replace=False):
        if start.isValid() and end.isValid():
            if replace:
                self._selections = []

            startRow, endRow = start.row(), end.row()
            for i in xrange(startRow, endRow + 1):
                if i not in self._selections:
                    self._selections.append(i)

            if replace:
                self.notifyChangeAll()
            else:
                self.notifyChange(startRow, endRow)

    def selectAll(self):
        itemCount = len(self._items)
        self._selections = range(itemCount)
        self.notifyChangeAll()

    def invertSelection(self):
        itemCount = len(self._items)
        newSelections = [i for i in xrange(itemCount) if i not in self._selections]
        self._selections = newSelections
        self.notifyChangeAll()

    def isSelected(self, index):
        return index.row() in self._selections

    def getSelectedItems(self):
        return [self._items[i] for i in self._selections]

    def clear(self):
        itemCount = len(self._items)
        if itemCount > 0:
            self.beginRemoveRows(self.index(0, 0), 0, itemCount - 1)
            self._items = []
            self._selections = []
            self.endRemoveRows()

    def setItems(self, items):
        if len(self._selections) > 0:
            self._selections = []

        self.clear()

        newItems = list(items)
        newItemCount = len(newItems)
        if newItemCount > 0:
            self.beginInsertRows(self.index(0, 0), newItemCount, newItemCount + 1)
            self._items = newItems
            self.endInsertRows()

class SelectionListDelegate(QtWidgets.QStyledItemDelegate):
    class SelectionRange(object):
        def __init__(self, start):
            self.start = QtCore.QPersistentModelIndex(start)
            self.end = self.start

            self.minIndex = start.row()
            self.maxIndex = self.minIndex

        def setEnd(self, end):
            self.end = QtCore.QPersistentModelIndex(end)

            endIndex = end.row()
            if endIndex < self.minIndex:
                self.minIndex = endIndex
            elif endIndex > self.maxIndex:
                self.maxIndex = endIndex

        def getRange(self):
            if self.start.row() <= self.end.row():
                return (self.start, self.end)
            else:
                return (self.end, self.start)

        def isInRange(self, index):
            start, end = self.getRange()
            startRow, endRow = start.row(), end.row()
            row = index.row()
            return row >= startRow and row <= endRow

        def isCollapsed(self):
            return self.start == self.end


    dragSelectionChange = Signal(int, name='dragSelectionChange')

    SELECTED_ITEM_BRUSH = QtGui.QBrush(QtGui.QColor('#44A5E2'))
    SELECTED_ITEM_PEN = QtGui.QPen(QtGui.QColor('#242424'))
    UNSELECTED_ITEM_BRUSH = QtGui.QBrush(Qt.transparent)
    UNSELECTED_ITEM_PEN = QtGui.QPen(Qt.white)
    TEXT_PADDING = 3

    def __init__(self, parent=None):
        super(SelectionListDelegate, self).__init__(parent=parent)

        self._selectionRange = None

    def isDragSelection(self):
        return self._selectionRange is not None

    def sizeHint(self, option, index):
        content = index.data(Qt.DisplayRole)
        if content is not None:
            metrics = QtGui.QFontMetrics(self.parent().font())
            contentWidth = metrics.width(content) + SelectionListDelegate.TEXT_PADDING * 2
            return QtCore.QSize(max(contentWidth, option.rect.width()), 20)
        else:
            return QtCore.QSize(0, 0)

    def editorEvent(self, event, model, option, index):
        evtType = event.type()
        btn = event.button()
        if (evtType == QtCore.QEvent.MouseButtonPress and btn == Qt.LeftButton):
            modifiers = event.modifiers()
            hasCtrl = bool(modifiers & Qt.ControlModifier)
            if modifiers & Qt.ShiftModifier:
                model.selectTo(index, not hasCtrl)
            else:
                if hasCtrl and model.isSelected(index):
                    model.deselect(index)
                else:
                    model.select(index, not hasCtrl)
                    self._selectionRange = SelectionListDelegate.SelectionRange(index)
            return True
        elif (evtType == QtCore.QEvent.MouseMove) and self.isDragSelection():
            self._selectionRange.setEnd(index)
            model.notifyChange(self._selectionRange.minIndex, self._selectionRange.maxIndex)
            self.dragSelectionChange.emit(index.row())
            return True
        elif (evtType == QtCore.QEvent.MouseButtonRelease) and (btn == Qt.LeftButton) and self.isDragSelection():
            self.commitDragSelection(model)
            return True
        else:
            return super(SelectionListDelegate, self).editorEvent(event, model, option, index)

    def commitDragSelection(self, model):
        if not self._selectionRange.isCollapsed():
            r = self._selectionRange.getRange()
            model.selectRange(r[0], r[1], False)
        self._selectionRange = None

    def paint(self, painter, option, index):
        painter.save()

        if index.model().isSelected(index):
            brush = SelectionListDelegate.SELECTED_ITEM_BRUSH
            pen = SelectionListDelegate.SELECTED_ITEM_PEN
        elif self.isDragSelection() and self._selectionRange.isInRange(index):
            brush = SelectionListDelegate.SELECTED_ITEM_BRUSH
            pen = SelectionListDelegate.SELECTED_ITEM_PEN
        else:
            brush = SelectionListDelegate.UNSELECTED_ITEM_BRUSH
            pen = SelectionListDelegate.UNSELECTED_ITEM_PEN

        # background color
        painter.setPen(QtGui.QPen(Qt.NoPen))
        painter.setBrush(brush)
        painter.drawRect(option.rect)

        # text
        item = index.data(Qt.DisplayRole)

        textRect = option.rect
        textRect.setLeft(textRect.left() + SelectionListDelegate.TEXT_PADDING)
        textRect.setWidth(textRect.width() + SelectionListDelegate.TEXT_PADDING * 2)

        painter.setPen(pen)
        painter.drawText(textRect, Qt.AlignLeft|Qt.AlignVCenter, item)

        painter.restore()


class SelectionView(QtWidgets.QListView):
    def __init__(self, parent=None):
        super(SelectionView, self).__init__(parent=parent)

        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        model = SelectionListModel(parent=self)
        self.setModel(model)

        delegate = SelectionListDelegate(self)
        delegate.dragSelectionChange.connect(self.onDragSelectionUpdate)
        self.setItemDelegate(delegate)

    def keyPressEvent(self, event):
        if (event.type() == QtCore.QEvent.KeyPress and
            event.key() == Qt.Key_A and
            event.modifiers() == Qt.ControlModifier):
            self.model().selectAll()
        elif (event.type() == QtCore.QEvent.KeyPress and
              event.key() == Qt.Key_I and
              event.modifiers() == Qt.ControlModifier):
            self.model().invertSelection()
        else:
            super(SelectionView, self).keyPressEvent(event)

    def mouseReleaseEvent(self, event):
        delegate = self.itemDelegate()
        if event.button() == Qt.LeftButton and delegate.isDragSelection():
            delegate.commitDragSelection(self.model())

        return super(SelectionView, self).mouseReleaseEvent(event)

    @Slot()
    def onDragSelectionUpdate(self, index):
        # when drag selection goes outside of visible area,
        # scroll to the last actived item
        scrollBar = self.verticalScrollBar()
        pos = scrollBar.value()
        total = self.model().rowCount()
        screenCount = total - scrollBar.maximum()

        index += 1
        if index < pos:
            QtCore.QTimer.singleShot(40, lambda: scrollBar.setValue(index))
        elif index > (pos + screenCount):
            QtCore.QTimer.singleShot(40, lambda: scrollBar.setValue(index - screenCount))

    def clear(self):
        self.model().clear()

    def setItems(self, items):
        self.model().setItems(items)

    def getSelection(self):
        return self.model().getSelectedItems()
