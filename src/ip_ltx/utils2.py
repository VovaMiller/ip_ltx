import os

from . import ip_ltx as _ip_ltx
from . import utils as _utils


def print_warning_extra(msg) -> None:
    """Сообщение о некритической ошибке, отображение которой
    регулируется переменной среды ``HIDE_EXTRA_WARNINGS``.
    """
    opt: str = os.environ.get("HIDE_EXTRA_WARNINGS", "off")
    if _ip_ltx.Section.cast_bool(opt) is not True:
        _utils.print_warning(msg)
