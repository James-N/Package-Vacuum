import sys
import maya.OpenMaya as om


def install_pyside(module):
    sys.modules['PySide'] = module

def install_shiboken(module):
    sys.modules['shiboken'] = module

# initiation
if om.MGlobal.apiVersion() < 20250000:
    install_pyside(__import__('PySide2'))
    install_shiboken(__import__('shiboken2'))
else:
    install_pyside(__import__('PySide6'))
    install_shiboken(__import__('shiboken6'))

del install_pyside
del install_shiboken
