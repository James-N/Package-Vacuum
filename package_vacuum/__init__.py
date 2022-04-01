__author__ = 'James.Ni'
__version__ = '1.0.2'

import sys
import os.path

from shiboken2 import wrapInstance
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QMainWindow

import maya.OpenMayaUI as omui
import maya.cmds as cmds
import maya.mel as mel

from .ui import MainWindow


gToolWindowInstance = None


def getMayaMainWindow():
    if sys.version_info.major >= 3:
        return wrapInstance(int(omui.MQtUtil.mainWindow()), QMainWindow)
    else:
        return wrapInstance(long(omui.MQtUtil.mainWindow()), QMainWindow)

def resetGlobalWindowReference():
    global gToolWindowInstance
    gToolWindowInstance = None

def showToolWindow(singleInstance=False):
    global gToolWindowInstance

    if singleInstance:
        if not gToolWindowInstance:
            gToolWindowInstance = MainWindow(parent=getMayaMainWindow())
            gToolWindowInstance.destroyed.connect(resetGlobalWindowReference)
            gToolWindowInstance.setAttribute(Qt.WA_DeleteOnClose)
            gToolWindowInstance.show()
            return gToolWindowInstance
        else:
            return gToolWindowInstance
    else:
        uiwindow = MainWindow(parent=getMayaMainWindow())
        uiwindow.show()
        return uiwindow

def saveToShelf():
    shelf = mel.eval("$__tempShelf = $gShelfTopLevel")
    shelfTab = cmds.tabLayout(shelf, query=True, selectTab=True)

    dirPath = os.path.dirname(__file__)
    imgPath = os.path.join(dirPath, 'ui/image/vacuum-32x32.png')

    code = """import package_vacuum;package_vacuum.showToolWindow(True)"""
    cmds.shelfButton(
        commandRepeatable=True,
        image1=imgPath,
        label='Package Vacuum',
        # imageOverlayLabel='Package Vacuum',
        annotation='Start Package Vacuum',
        scaleIcon=True,
        command=code,
        sourceType='python',
        parent=shelfTab
    )