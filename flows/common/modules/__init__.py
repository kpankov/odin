from glob import glob
from keyword import iskeyword
from os.path import dirname, join, split, splitext

from core.logger import Logger

basedir = dirname(__file__)

__all__ = []
for name in glob(join(basedir, '*.py')):
    module = splitext(split(name)[-1])[0]
    if not module.startswith('_') and module.isidentifier() and not iskeyword(module):
        try:
            __import__(__name__ + '.' + module)
        except Exception as e:
            Logger.warning('Ignoring exception while loading the \"{}\" module. Exception: {}'.format(module, e))
        else:
            __all__.append(module)
__all__.sort()
