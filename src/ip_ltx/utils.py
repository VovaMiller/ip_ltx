import os
import sys
import traceback
from pathlib import Path
from typing import Any, Protocol

# ----------------------------------------------------------------

os.system("")  # enables colors for Windows consoles

class ANSI_COLOR_CODE:
    DEF = '\033[0m'
    BLACK   = '\033[90m'  # '\033[30m'
    RED     = '\033[91m'  # '\033[31m'
    GREEN   = '\033[92m'  # '\033[32m'
    YELLOW  = '\033[93m'  # '\033[33m'
    BLUE    = '\033[94m'  # '\033[34m'
    PURPLE  = '\033[95m'  # '\033[35m'
    CYAN    = '\033[96m'  # '\033[36m'
    WHITE   = '\033[97m'  # '\033[37m'

# ----------------------------------------------------------------

def print_warning(msg, prefix: bool = True, color: bool = True):
    msg_fmt = "{}{}{}{}".format(
        ANSI_COLOR_CODE.YELLOW if color else "",
        "~ " if prefix else "",
        msg,
        ANSI_COLOR_CODE.DEF if color else "",
    )
    print(msg_fmt, file=sys.stderr)

def print_error(msg, prefix: bool = True, color: bool = True):
    msg_fmt = "{}{}{}{}".format(
        ANSI_COLOR_CODE.RED if color else "",
        "! " if prefix else "",
        msg,
        ANSI_COLOR_CODE.DEF if color else "",
    )
    print(msg_fmt, file=sys.stderr)

# ----------------------------------------------------------------

def cast_safe(val, _type, defval=None):
    try:
        return _type(val)
    except (ValueError, TypeError):
        return defval

# ----------------------------------------------------------------

class Runnable(Protocol):
    def __call__(self, fn: str, *args: Any, **kwargs: Any) -> None:
        ...

def run(f: Runnable, tag: str, **kwargs: Any) -> None:
    """Обёртка для безопасного запуска функции, генерирующей текстовый файл с данными.

    * Формирует имя выходного файла, беря в качестве префикса имя исходного скрипта.
    * Перехватывает любые исключения и выводит информацию о них.

    :param f: Функция для запуска.
        Первым аргументом должна принимать имя выходного файла.
    :param tag: Суффикс выходного файла (без расширения).
    :param **kwargs: Остальные аргументы функции после имени выходного файла.
    """
    epp = Path(sys.argv[0])
    prefix = epp.stem if epp.is_file() else ""
    fn = f"{prefix}__{tag}.txt"
    try:
        f(fn, **kwargs)
    except Exception as e:
        print("")
        print((
            f"{ANSI_COLOR_CODE.RED}"
            f"! {fn}"
            f"{ANSI_COLOR_CODE.DEF}"
        ))
        # print("    {}".format(f.__name__))
        # print("    {}".format(repr(e)))
        print(traceback.format_exc())
        print("", flush=True)
    else:
        print(
            f"{ANSI_COLOR_CODE.GREEN}+{ANSI_COLOR_CODE.DEF}",
            fn,
            flush=True
        )

# ----------------------------------------------------------------
