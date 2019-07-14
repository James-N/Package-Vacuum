import sys
import os.path

import PySide2.QtCore as QtCore
from PySide2.QtCore import Qt, Signal, Slot
import PySide2.QtWidgets as QtWidgets
import PySide2.QtGui as QtGui

from .logview import LogLevel, LogView
from .selectionview import SelectionView

import package_vacuum.module as module


SELF_MODULE_NAME = 'package_vacuum'


class ClearByNameWidgets(object):
    def __init__(self):
        self.userInput = None
        self.casecadeCheck = None
        self.ignoreInternalCheck = None

class ClearBySelectionWidgets(object):
    def __init__(self):
        self.filterInput = None
        self.ignoreInternalCheck = None
        self.selectionView = None


class SimpleToolbar(QtWidgets.QWidget):
    def __init__(self, title='', parent=None):
        super(SimpleToolbar, self).__init__(parent=parent)

        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        toolbarLayout = QtWidgets.QHBoxLayout()
        toolbarLayout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(toolbarLayout)

        titleLabel = QtWidgets.QLabel(title)
        titleLabel.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        toolbarLayout.addWidget(titleLabel)

        toolbarLayout.addSpacerItem(QtWidgets.QSpacerItem(5, 5, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))

    def addTool(self, widget):
        if not isinstance(widget, QtWidgets.QWidget):
            raise TypeError("invalid widget")

        self.layout().addWidget(widget)


class MainWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent=parent)

        if sys.platform == 'darwin':
            self.setWindowFlags(Qt.Tool)
        else:
            self.setWindowFlags(Qt.Window)

        self._clearByNameWidgets = None
        self._clearBySelectionWidgets = None

        self._tabs = None
        self._logView = None

        self._windowOpened = False

        self._initUI()

    def _getImagePath(self, name):
        dir = os.path.dirname(__file__)
        return os.path.join(dir, 'image', name)

    def _initUI(self):
        self.resize(400, 300)
        self.setWindowTitle('Package Vacuum')
        self.setWindowIcon(QtGui.QIcon(self._getImagePath('vacuum-32x32.png')))

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(layout)

        # tabs
        tabs = QtWidgets.QTabWidget(self)
        tabs.setStyleSheet("QTabBar::tab { height: 25px }")
        tabs.addTab(self._initExplicitInput(), 'Clean By Name')
        tabs.addTab(self._initModuleSelection(), 'Clean By Selection')
        tabs.currentChanged.connect(self.resizeTab)
        tabs.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self._tabs = tabs
        layout.addWidget(tabs)

        # logs
        logToolbar = SimpleToolbar('Logs', self)
        layout.addWidget(logToolbar)

        # clear log button
        clearLogBtn = QtWidgets.QPushButton(QtGui.QIcon(self._getImagePath('clean.svg')), '', logToolbar)
        clearLogBtn.setFixedSize(20, 20)
        clearLogBtn.setToolTip("clear log")
        clearLogBtn.clicked.connect(self.clearLog)
        logToolbar.addTool(clearLogBtn)

        # log view
        logView = LogView(maxSize=20, parent=self)
        layout.addWidget(logView)
        self._logView = logView

    def showEvent(self, event):
        if not self._windowOpened:
            self._windowOpened = True
            self.resizeTab(0)

    @Slot(int)
    def resizeTab(self, index):
        for i in xrange(self._tabs.count()):
            widget = self._tabs.widget(i)
            if i == index:
                widget.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
            else:
                widget.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)

        currentWidget = self._tabs.widget(index)
        currentWidget.resize(currentWidget.minimumSizeHint())
        currentWidget.adjustSize()

    def _createHeaderLabel(self, header, parent):
        headerLabel = QtWidgets.QLabel(header, parent)
        headerLabel.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)

        font = QtGui.QFont(headerLabel.font())
        font.setPixelSize(int(round(font.pixelSize() * 1.3)))
        headerLabel.setFont(font)

        return headerLabel

    def _createHeaderSeparator(self, parent):
        separator = QtWidgets.QFrame(parent)
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)

        return separator

    def _createFormLabel(self, title, parent):
        label = QtWidgets.QLabel(title, parent)
        label.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        label.setMaximumWidth(120)
        label.setMinimumWidth(100)
        label.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)

        return label

    def _initExplicitInput(self):
        widgetsSet = ClearByNameWidgets()
        container = QtWidgets.QWidget(self)

        layout = QtWidgets.QVBoxLayout()
        container.setLayout(layout)

        # description
        description = "find and clean modules by qualify name"
        layout.addWidget(self._createHeaderLabel(description, container))

        # separator
        layout.addWidget(self._createHeaderSeparator(container))

        # form
        formLayout = QtWidgets.QFormLayout()
        layout.addLayout(formLayout)

        # user input
        userInput = QtWidgets.QLineEdit(container)
        userInput.setFixedHeight(30)
        widgetsSet.userInput = userInput

        inputLabel = self._createFormLabel('Name of Module', container)
        formLayout.addRow(inputLabel, userInput)

        # cascade checkbox
        cascadeCheckbox = QtWidgets.QCheckBox('Cascade', container)
        cascadeCheckbox.setToolTip("clear all sub-modules")
        cascadeCheckbox.setChecked(True)
        widgetsSet.casecadeCheck = cascadeCheckbox

        # ignore internal checkbox
        ignoreInternalCheck = QtWidgets.QCheckBox('Ignore internal modules', container)
        ignoreInternalCheck.setChecked(True)
        widgetsSet.ignoreInternalCheck = ignoreInternalCheck

        # checkbox set
        checkboxGroup = QtWidgets.QHBoxLayout(container)
        checkboxGroup.setSpacing(20)
        checkboxGroup.addWidget(cascadeCheckbox)
        checkboxGroup.addWidget(ignoreInternalCheck)
        formLayout.addRow(self._createFormLabel('', container), checkboxGroup)

        # clean action button
        button = QtWidgets.QPushButton('Clean', container)
        button.clicked.connect(self.cleanByUserInput)
        button.setFixedHeight(30)
        layout.addWidget(button)

        layout.addSpacerItem(QtWidgets.QSpacerItem(5, 5, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding))

        self._clearByNameWidgets = widgetsSet
        return container

    def _initModuleSelection(self):
        widgetSet = ClearBySelectionWidgets()
        container = QtWidgets.QWidget(self)

        layout = QtWidgets.QVBoxLayout()
        container.setLayout(layout)

        # description
        description = "search modules and clean selected ones"
        layout.addWidget(self._createHeaderLabel(description, container))

        # separator
        layout.addWidget(self._createHeaderSeparator(container))

        # filter
        filterLabel = QtWidgets.QLabel('Filter', container)
        layout.addWidget(filterLabel)

        filterInput = QtWidgets.QLineEdit(container)
        filterInput.setFixedHeight(30)
        filterInput.textChanged.connect(self.updateModuleList)
        layout.addWidget(filterInput)
        widgetSet.filterInput = filterInput

        # ignore internal checkbox
        ignoreInternalCheck = QtWidgets.QCheckBox('Ignore internal modules', container)
        ignoreInternalCheck.setChecked(True)
        ignoreInternalCheck.stateChanged.connect(self.updateModuleList)
        layout.addWidget(ignoreInternalCheck)
        widgetSet.ignoreInternalCheck = ignoreInternalCheck

        # module list toolbar
        moduleListToolbar = SimpleToolbar(container)
        layout.addWidget(moduleListToolbar)

        # refresh button
        refreshListBtn = QtWidgets.QPushButton(QtGui.QIcon(self._getImagePath('refresh.svg')), '', moduleListToolbar)
        refreshListBtn.setFixedSize(20, 20)
        refreshListBtn.setToolTip("refresh list")
        refreshListBtn.clicked.connect(self.updateModuleList)
        moduleListToolbar.addTool(refreshListBtn)

        # module list
        selectionView = SelectionView(container)
        selectionView.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        layout.addWidget(selectionView)
        widgetSet.selectionView = selectionView

        # clean action button
        button = QtWidgets.QPushButton('Clean', container)
        button.clicked.connect(self.cleanBySelection)
        button.setFixedHeight(30)
        layout.addWidget(button)

        self._clearBySelectionWidgets = widgetSet
        return container

    @Slot()
    def cleanByUserInput(self):
        logView = self._logView

        moduleName = self._clearByNameWidgets.userInput.text().strip()
        cascade = self._clearByNameWidgets.casecadeCheck.isChecked()
        ignoreInternal = self._clearByNameWidgets.ignoreInternalCheck.isChecked()

        if moduleName.startswith(SELF_MODULE_NAME):
            logView.writeLog("cannot clean module of this tool", LogLevel.ERROR)
            return

        if len(moduleName) > 0:
            if cascade:
                modules = module.findModulesByQualifyName(moduleName, ignoreInternal=ignoreInternal)
                if len(modules) > 0:
                    for m in modules:
                        module.deregisterModule(m)
                        logView.writeLog("cleaned module: [ {0} ]".format(m))
                else:
                    logView.writeLog("no module matches prefix: [ {0} ]".format(moduleName), LogLevel.WARNING)
            else:
                if module.hasModule(moduleName):
                    module.deregisterModule(moduleName)
                    logView.writeLog("cleaned module: [ {0} ]".format(moduleName))
                else:
                    logView.writeLog("module [ {0} ] is not loaded".format(moduleName), LogLevel.WARNING)

    @Slot()
    def cleanBySelection(self):
        logView = self._logView

        modules = self._clearBySelectionWidgets.selectionView.getSelection()
        if len(modules) > 0:
            for m in modules:
                if m.startswith(SELF_MODULE_NAME):
                    logView.writeLog("cannot clean module or sub-module of this tool: [ {0} ]".format(m), LogLevel.ERROR)
                else:
                    try:
                        module.deregisterModule(m)
                        logView.writeLog("cleaned module: [ {0} ]".format(m))
                    except module.ModuleNotFoundException:
                        logView.writeLog("module [ {0} ] is not found".format(m), LogLevel.WARNING)

    @Slot()
    def updateModuleList(self):
        filterContent = self._clearBySelectionWidgets.filterInput.text().strip()
        ignoreInternal = self._clearBySelectionWidgets.ignoreInternalCheck.isChecked()
        selectionView = self._clearBySelectionWidgets.selectionView

        if len(filterContent) > 0:
            selectionView.setItems(module.filterModules(filterContent, ignoreInternal=ignoreInternal))
        else:
            selectionView.clear()

    @Slot()
    def clearLog(self):
        self._logView.clearLog()
