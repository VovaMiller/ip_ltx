
import importlib.metadata

from .ip_ltx import Ini, Section

__all__ = [
    "Ini",
    "Section",
]

try:
    __version__ = importlib.metadata.version("ip_ltx")
except importlib.metadata.PackageNotFoundError:
    __version__ = "unknown"

__author__ = "Vova Miller"
__email__ = "vovamiller_97@mail.ru"
