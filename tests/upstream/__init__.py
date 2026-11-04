"""Original regression tests with only standalone import/path adaptation."""
import atexit
import inspect
import sys
import tempfile
import types

_profile = tempfile.TemporaryDirectory()
atexit.register(_profile.cleanup)
sys.modules.setdefault('globalVars', types.SimpleNamespace(
    appArgs=types.SimpleNamespace(configPath=_profile.name)))


def initTranslation():
    inspect.currentframe().f_back.f_globals['_'] = lambda message: message


sys.modules.setdefault('addonHandler', types.SimpleNamespace(initTranslation=initTranslation))
