from keyword import iskeyword
from os import listdir
from os.path import dirname, join, isdir

from core.logger import Logger

basedir = dirname(__file__)

__all__ = []
for name in listdir(basedir):
    flow_dir_path = join(basedir, name)
    if isdir(flow_dir_path) and len(listdir(flow_dir_path)) > 0 and not name.startswith(
            '_') and name.isidentifier() and not iskeyword(name):
        try:
            __import__(__name__ + '.' + name)
        except Exception as e:
            Logger.warning('Ignoring exception while loading the \"{}\" flow. Exception: {}'.format(name, e))
        else:
            __all__.append(name)
__all__.sort()
