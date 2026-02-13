import sys
if sys.version_info < (3, 12):
    raise ImportError("ip_ltx requires Python 3.12+")

from .ip_ltx import Section, Ini

import importlib.metadata
try:
    __version__ = importlib.metadata.version("ip_ltx")
except importlib.metadata.PackageNotFoundError:
    __version__ = "unknown"

__author__ = "Vova Miller"
__email__ = "vovamiller_97@mail.ru"
