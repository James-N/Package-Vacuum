import sys
import os
import os.path


MAYA_LOCATION = os.path.normpath(os.environ['MAYA_LOCATION'])
KEY_MODULE_PATH = '__file__'


class ModuleNotFoundException(Exception):
    pass


def isInternalModule(module):
    mpath = getattr(module, KEY_MODULE_PATH, None)
    if mpath is not None:
        return MAYA_LOCATION in mpath
    else:
        return True

def deregisterModule(name):
    try:
        del sys.modules[name]
    except KeyError:
        raise ModuleNotFoundException

def findModulesByQualifyName(name, ignoreInternal=False):
    def test(key, value):
        if key == name or key.startswith(name + '.'):
            if ignoreInternal:
                return not isInternalModule(value)
            else:
                return True
        else:
            return False

    names = [m[0] for m in sys.modules.items() if test(m[0], m[1])]
    names.sort(key=lambda n: len(n))

    return names

def filterModules(searchKey, ignoreInternal=False):
    def test(key, value):
        if searchKey in key:
            if ignoreInternal:
                return not isInternalModule(value)
            else:
                return True
        else:
            return False

    names = [m[0] for m in sys.modules.items() if test(m[0], m[1])]
    names.sort()
    return names

def hasModule(name):
    return name in sys.modules
