import os
import re
import sys
import traceback
from collections.abc import Callable
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

class SingletonMeta(type):
    _instances = {}
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
        print((
            f"{ANSI_COLOR_CODE.RED}"
            f"! {msg}"
            f"{ANSI_COLOR_CODE.DEF}"
        ))
        print(traceback.format_exc())
        print("", flush=True)
        raise Exception(msg)

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

def is_gamedata_file(
        path: str,
        gd_path_main: str | None,
        gd_path_alt: str | None
) -> bool:
    """Проверка, существует ли файл в ресурсах игры (gamedata).

    :param path: Путь до файла относительно папки gamedata.
    :param gd_path_main: Путь до основной папки gamedata.
    :param gd_path_alt: Путь до вспомогательной папки gamedata.
        Например, до ресурсов оригинальной игры или распакованных db-архивов.
    :return: Был ли найден указанный файл хотя бы в одной из папок gamedata.
    """
    for gd_path in [gd_path_main, gd_path_alt]:
        if (gd_path is None) or (len(gd_path) == 0):
            continue
        if Path(gd_path).joinpath(Path(path)).is_file():
            return True
    return False

def is_gamedata_dir(
        path: str,
        gd_path_main: str | None,
        gd_path_alt: str | None
) -> bool:
    """Проверка, существует ли папка в ресурсах игры (gamedata).

    :param path: Путь до папки относительно папки gamedata.
    :param gd_path_main: Путь до основной папки gamedata.
    :param gd_path_alt: Путь до вспомогательной папки gamedata.
        Например, до ресурсов оригинальной игры или распакованных db-архивов.
    :return: Была ли найдена указанная папка хотя бы в одной из папок gamedata.
    """
    for gd_path in [gd_path_main, gd_path_alt]:
        if (gd_path is None) or (len(gd_path) == 0):
            continue
        if Path(gd_path).joinpath(Path(path)).is_dir():
            return True
    return False

# ----------------------------------------------------------------

class XML_PATTERNS:
    COMMENT = re.compile(r"<!--.*?-->")
    INVALID_COMMENT_LINE = re.compile(r"<!--.*--.*-->")
    INVALID_CHARS = re.compile(
        # Invalid character (XML 1.0)
        r"[^\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD\U00010000-\U0010FFFF]"
    )
    UNESCAPED_AMPERSAND = re.compile(
        r"&(?!(amp|lt|gt|apos|quot|#\d+|#x[a-fA-F0-9]+);)"
    )

def read_xml(
        fp_from_config: str,
        gd_path_main: str | None,
        gd_path_alt: str | None
) -> list[str]:
    """Основная функция для чтения XML файлов из ресурсов игры
    с поддержкой include-директив.

    Также перед парсингом функция:

    * Удаляет все комментарии. Это позволяет избежать ошибки из-за комментариев
      с двумя или более дефисами внутри (``--``). С точки зрения XML формата
      это невалидные комментарии, но в ресурсах игры они всё же нередко
      встречаются, и движок на них не ругается, а просто игнорирует.
    * Удаляет "голые" амперсанды (``&``). Это технический символ для XML формата,
      который нельзя использовать как обычный символ. Тем не менее, в ресурсах игры
      могут встретиться строки, использующие амперсанд как символ. Движок же на это
      не ругается, а символы просто удаляет.

    :param fp: Путь до XML-файла относительно ``"gamedata/config/"``.
    :param gd_path_main: Путь до основной папки gamedata.
    :param gd_path_alt: Путь до вспомогательной папки gamedata.
        Например, до ресурсов оригинальной игры или распакованных db-архивов.
    :return: Список строк прочитанного файла.
        Может быть использован для передачи в ``xml.etree.ElementTree.fromstringlist``.
    """
    def _warn(msg: str) -> None:
        print_warning(f"[XML] ({fp_from_config}) {msg}")
    
    def _process_line(line: str) -> str:
        # comments
        if XML_PATTERNS.INVALID_COMMENT_LINE.search(line):
            _warn(f"Line {i+1}: 2+ hyphens inside a comment")
        line = XML_PATTERNS.COMMENT.sub("", line)

        # invalid characters
        if XML_PATTERNS.INVALID_CHARS.search(line):
            _warn(f"Line {i+1}: invalid character(s)")

        # unescaped ampersand
        if XML_PATTERNS.UNESCAPED_AMPERSAND.search(line):
            _warn(f"Line {i+1}: unescaped ampersand(s)")
        line = XML_PATTERNS.UNESCAPED_AMPERSAND.sub("", line)

        return line

    # Получаем реальный путь до файла
    for gd_path in [gd_path_main, gd_path_alt]:
        if (gd_path is None) or (len(gd_path) == 0):
            continue
        path = Path(gd_path).joinpath(Path(f"config\\{fp_from_config}"))
        if path.is_file():
            fp = str(path)
            break
    else:
        _warn("Not found")
        return []
    
    # Читаем файл
    if Path(fp_from_config).is_relative_to("text\\rus\\"):
        encodings = ["cp1251", "utf-8-sig", None]
        decode_error_warn = True
    else:
        encodings = ["utf-8-sig", "cp1251", None]
        decode_error_warn = False
    for encoding in encodings:
        try:
            with open(fp, "r", encoding=encoding) as f:
                lines_input = f.readlines()
                break
        except UnicodeDecodeError:
            if decode_error_warn:
                _warn(f"Can't be read with encoding='{encoding}'")
            continue
        except OSError as e:
            _warn(f"Skipping due to OSError: {e}")
            return []
    else:
        _warn("Skipping: unexpected encoding")
        return []
    
    # Обработка строк и поддержка include-директив
    lines_output = []
    for i, line in enumerate(lines_input):
        if line.startswith("#include"):
            rr = re.match(r"#include\s*\"(.+?)\"", line)
            if rr is not None:
                lines_output.extend(read_xml(rr.group(1), gd_path_main, gd_path_alt))
            else:
                _warn(f"Ignoring odd #include on the line {i+1}")
        else:
            lines_output.append(_process_line(line))

    return lines_output

# ----------------------------------------------------------------
