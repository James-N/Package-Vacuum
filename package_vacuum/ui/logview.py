import PySide.QtCore as QtCore
from PySide.QtCore import Qt, Signal, Slot
import PySide.QtWidgets as QtWidgets
import PySide.QtGui as QtGui


def constructPen(color, style):
    pen = QtGui.QPen(color)
    pen.setStyle(style)

    return pen


class LogLevel(object):
    NORMAL = 0x01
    WARNING = 0x02
    ERROR = 0x03


class LogViewModel(QtCore.QAbstractListModel):
    def __init__(self, maxSize=0, parent=None):
        super(LogViewModel, self).__init__(parent=parent)

        self._maxSize = maxSize
        self._logs = []
        self._focusIndex = -1

    # overrides #

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._logs)

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid() and role == Qt.DisplayRole:
            return self._logs[index.row()]
        else:
            return (None, None)

    # custom api #

    def _removeOldestLog(self):
        self.beginRemoveRows(self.index(0, 0), 0, 1)
        self._logs.pop(0)
        self.endRemoveRows()

        if self._focusIndex >= 0:
            self._focusIndex -= 1

    def addLog(self, message, level=LogLevel.NORMAL):
        logCount = len(self._logs)

        if self._maxSize > 0 and logCount >= self._maxSize:
            self._removeOldestLog()
            logCount -= 1

        self.beginInsertRows(self.index(0, 0), logCount, logCount + 1)
        self._logs.append((message, level))
        self.endInsertRows()

    def clear(self):
        logCount = len(self._logs)
        if logCount > 0:
            self.beginRemoveRows(self.index(0, 0), 0, logCount - 1)
            self._logs = []
            self.endRemoveRows()
            self._focusIndex = -1

    def isFocused(self, index):
        return index.isValid() and self._focusIndex == index.row()

    def setFocusRow(self, index):
        if index.isValid():
            self._focusIndex = index.row()
            self.dataChanged.emit(index, index)


class LogViewDelegate(QtWidgets.QStyledItemDelegate):
    LOG_NORMAL_BRUSH = QtGui.QBrush(Qt.transparent)
    LOG_NORMAL_PEN = QtGui.QPen(Qt.white)
    LOG_WARNING_BRUSH = QtGui.QBrush(QtGui.QColor('#FFF26E'))
    LOG_WARNING_PEN = QtGui.QPen(Qt.black)
    LOG_ERROR_BRUSH = QtGui.QBrush(QtGui.QColor('#FF7A6B'))
    LOG_ERROR_PEN = QtGui.QPen(Qt.white)

    ROW_FOCUS_PEN = constructPen(QtGui.QColor('#44A5E2'), Qt.DashLine)

    TEXT_PADDING = 3

    def __init__(self, parent=None):
        super(LogViewDelegate, self).__init__(parent=parent)

    def sizeHint(self, option, index):
        content = index.data(Qt.DisplayRole)[0]
        if content is not None:
            metrics = QtGui.QFontMetrics(self.parent().font())
            contentWidth = metrics.horizontalAdvance(content) + LogViewDelegate.TEXT_PADDING * 2
            return QtCore.QSize(max(contentWidth, option.rect.width()), 20)
        else:
            return QtCore.QSize(0, 0)

    def editorEvent(self, event, model, option, index):
        if (event.type() == QtCore.QEvent.MouseButtonPress and event.button() == Qt.LeftButton):
            model.setFocusRow(index)
            return True
        else:
            return super(LogViewDelegate, self).editorEvent(event, model, option, index)

    def paint(self, painter, option, index):
        painter.save()

        msg, level = index.data(Qt.DisplayRole)
        brush = pen = None

        if level == LogLevel.WARNING:
            brush = LogViewDelegate.LOG_WARNING_BRUSH
            pen = LogViewDelegate.LOG_WARNING_PEN
        elif level == LogLevel.ERROR:
            brush = LogViewDelegate.LOG_ERROR_BRUSH
            pen = LogViewDelegate.LOG_ERROR_PEN
        else:
            brush = LogViewDelegate.LOG_NORMAL_BRUSH
            pen = LogViewDelegate.LOG_NORMAL_PEN

        bgRect = option.rect

        # background color
        if index.model().isFocused(index):
            painter.setPen(LogViewDelegate.ROW_FOCUS_PEN)
            bgRect = QtCore.QRect(bgRect)
            bgRect.setWidth(bgRect.width() - 1)
            bgRect.setHeight(bgRect.height() - 1)
        else:
            painter.setPen(QtGui.QPen(Qt.NoPen))
        painter.setBrush(brush)
        painter.drawRect(bgRect)

        # text
        painter.setPen(pen)
        textRect = option.rect
        textRect.setLeft(textRect.left() + LogViewDelegate.TEXT_PADDING)
        textRect.setWidth(textRect.width() + LogViewDelegate.TEXT_PADDING * 2)
        painter.drawText(textRect, Qt.AlignLeft|Qt.AlignVCenter, msg)

        painter.restore()

class LogView(QtWidgets.QListView):
    def __init__(self, maxSize=20, parent=None):
        super(LogView, self).__init__(parent=parent)

        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        model = LogViewModel(maxSize=maxSize, parent=self)
        self.setModel(model)

        delegate = LogViewDelegate(self)
        self.setItemDelegate(delegate)

    def _logViewToBottom(self):
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def writeLog(self, message, logLevel=LogLevel.NORMAL):
        self.model().addLog(message, logLevel)
        QtCore.QTimer.singleShot(40, self._logViewToBottom)

    def clearLog(self):
        self.model().clear()
