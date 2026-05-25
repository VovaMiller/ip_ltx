import os
import sys
import traceback
from collections.abc import Callable, MutableMapping
from enum import StrEnum
from pathlib import Path
from typing import Any, ClassVar, Protocol

# ----------------------------------------------------------------

os.system("")  # enables colors for Windows consoles

class ANSIColorCode(StrEnum):
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

# Лишний пробел в конце необходим
#  для корректного распознавания строк
#  при изменении размера окна консоли.

def print_warning(msg, prefix: bool = True, color: bool = True):
    msg_fmt = "{}{}{}{} ".format(
        ANSIColorCode.YELLOW if color else "",
        "~ " if prefix else "",
        msg,
        ANSIColorCode.DEF if color else "",
    )
    print(msg_fmt, file=sys.stderr)

def print_error(msg, prefix: bool = True, color: bool = True):
    msg_fmt = "{}{}{}{} ".format(
        ANSIColorCode.RED if color else "",
        "! " if prefix else "",
        msg,
        ANSIColorCode.DEF if color else "",
    )
    print(msg_fmt, file=sys.stderr)

# ----------------------------------------------------------------

def cast_safe[R,D](
        val: Any,
        _type: Callable[[Any], R],
        defval: D = None
) -> R | D:
    try:
        return _type(val)
    except (ValueError, TypeError):
        return defval

# ----------------------------------------------------------------

class SingletonMeta(type):
    _instances: ClassVar[dict[Any, Any]] = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class SingletonBase(metaclass=SingletonMeta):
    pass

# ----------------------------------------------------------------

def validate_data(funcs: list[Callable[[], Any]]) -> None:
    """Вспомогательная функция для валидации данных,
    конструируемых посредством singleton-классов.

    :param funcs: Список функций, возвращающих экземпляр singleton-класса.
    :raises Exception: если валидация не пройдена.
    """
    if "sphinx" in sys.modules:
        # Ничего не валидировать, если модули подгружаются для документации.
        return
    try:
        for func in funcs:
            func_name = func.__name__
            func()
    except Exception as e:
        msg = f"Mandatory data validation failed ({func_name})"
        print("")
        print(
            f"{ANSIColorCode.RED}"
            f"! {msg}"
            f"{ANSIColorCode.DEF}"
        )
        print(traceback.format_exc())
        print("", flush=True)
        raise Exception(msg) from e

def preinit_singletons(singletons: list[type[SingletonBase]]) -> None:
    """Вспомогательная функция для предварительной инициализации singleton-классов.

    Может быть использована для предварительной валидации всех необходимых данных.

    :param singletons: Список классов, базирующихся на :class:`SingletonBase`.
    :raises Exception: если валидация не пройдена.
    """
    if "sphinx" in sys.modules:
        # Ничего не инициализировать, если модули подгружаются для документации.
        return
    try:
        for cls in singletons:
            cls_name = cls.__name__
            cls()
    except Exception:
        print_error(f"Mandatory data validation failed ({cls_name})")
        raise

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
    :param \\*\\*kwargs: Остальные аргументы функции после имени выходного файла.
    """
    epp = Path(sys.argv[0])
    prefix = epp.stem if epp.is_file() else ""
    fn = f"{prefix}__{tag}.txt"
    try:
        f(fn, **kwargs)
    except Exception:
        print("")
        print(
            f"{ANSIColorCode.RED}"
            f"! {fn}"
            f"{ANSIColorCode.DEF}"
        )
        print(traceback.format_exc())
        print("", flush=True)
    else:
        print(
            f"{ANSIColorCode.GREEN}+{ANSIColorCode.DEF}",
            fn,
            flush=True
        )

# ----------------------------------------------------------------

def is_gamedata_file(
        path: str,
        gd_path_main: Path | None,
        gd_path_alt: Path | None
) -> bool:
    """Проверка, существует ли файл в ресурсах игры (gamedata).

    :param path: Путь до файла относительно папки gamedata.
    :param gd_path_main: Путь до основной папки gamedata.
    :param gd_path_alt: Путь до вспомогательной папки gamedata.
        Например, до ресурсов оригинальной игры или распакованных db-архивов.
    :return: Был ли найден указанный файл хотя бы в одной из папок gamedata.
    """
    for gd_path in [gd_path_main, gd_path_alt]:
        if (gd_path is not None) and gd_path.joinpath(path).is_file():
            return True
    return False

def is_gamedata_dir(
        path: str,
        gd_path_main: Path | None,
        gd_path_alt: Path | None
) -> bool:
    """Проверка, существует ли папка в ресурсах игры (gamedata).

    :param path: Путь до папки относительно папки gamedata.
    :param gd_path_main: Путь до основной папки gamedata.
    :param gd_path_alt: Путь до вспомогательной папки gamedata.
        Например, до ресурсов оригинальной игры или распакованных db-архивов.
    :return: Была ли найдена указанная папка хотя бы в одной из папок gamedata.
    """
    for gd_path in [gd_path_main, gd_path_alt]:
        if (gd_path is not None) and gd_path.joinpath(path).is_dir():
            return True
    return False

# ----------------------------------------------------------------

def fill_environ(globalns: MutableMapping) -> None:
    """Заполнить переменные среды из глобальных перменных.

    * ``META_FILEPATH``: ``str``

        * Путь до основного конфигурационного файла.
        * Значение по умолчанию: файл ``meta.ltx`` в текущей рабочей директории.

    * ``HIDE_LTX_WARNINGS``: ``bool``

        * Спрятать сообщения о некритических ошибках при чтении/парсинге ltx-файлов.
        * Значение по умолчанию: ``False``

    * ``HIDE_XML_WARNINGS``: ``bool``
        * Спрятать сообщения о некритических ошибках при чтении/парсинге xml-файлов.
        * Значение по умолчанию: ``False``

    * ``HIDE_EXTRA_WARNINGS``: ``bool``
        * Спрятать сообщения о других некритических ошибках
          (например, при инициализации :class:`~ip_ltx.treasure_manager_ext.SpawnEntry`)
        * Значение по умолчанию: ``False``
    """
    gl = globalns

    opt: str = "META_FILEPATH"
    if (opt in gl) and isinstance(gl[opt], str) and (len(gl[opt]) > 0):
        os.environ[opt] = str(Path(gl[opt]).resolve())
    else:
        os.environ[opt] = str(Path.cwd().joinpath("meta.ltx"))

    opt: str = "HIDE_LTX_WARNINGS"
    if (opt in gl) and isinstance(gl[opt], bool):
        os.environ[opt] = str(int(gl[opt]))
    else:
        os.environ[opt] = "0"

    opt: str = "HIDE_XML_WARNINGS"
    if (opt in gl) and isinstance(gl[opt], bool):
        os.environ[opt] = str(int(gl[opt]))
    else:
        os.environ[opt] = "0"

    opt: str = "HIDE_EXTRA_WARNINGS"
    if (opt in gl) and isinstance(gl[opt], bool):
        os.environ[opt] = str(int(gl[opt]))
    else:
        os.environ[opt] = "0"

# ----------------------------------------------------------------
