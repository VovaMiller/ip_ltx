import os
import re
from pathlib import Path

from .ip_ltx import Section
from .utils import SingletonBase, print_error, print_warning

# ----------------------------------------------------------------

class XMLOptions(SingletonBase):
    """Опции для работы с XML-файлами, устанавливаемые через переменные среды."""

    HIDE_XML_WARNINGS: bool
    """Спрятать сообщения о некритических ошибках при чтении xml-файлов.

    Значение по умолчанию: ``False``
    """

    def __init__(self) -> None:
        opt: str = os.environ.get("HIDE_XML_WARNINGS", "off")
        self.HIDE_XML_WARNINGS = (Section.cast_bool(opt) is True)

# ----------------------------------------------------------------

def print_warning_xml(msg: str) -> None:
    if not XMLOptions().HIDE_XML_WARNINGS:
        print_warning(msg)

# ----------------------------------------------------------------

class _XMLPatterns:
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
        gd_path_main: Path | None,
        gd_path_alt: Path | None
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
    * Удаляет заголовки, типа ``<?xml version="1.0" encoding="windows-1251" ?>``.
      Это необходимо, чтобы избежать ошибки при чтении, когда такой заголовок
      вставлен в какой-нибудь include-файл.

    :param fp: Путь до XML-файла относительно ``"gamedata/config/"``.
    :param gd_path_main: Путь до основной папки gamedata.
    :param gd_path_alt: Путь до вспомогательной папки gamedata.
        Например, до ресурсов оригинальной игры или распакованных db-архивов.
    :return: Список строк прочитанного файла.
        Может быть использован для передачи в ``xml.etree.ElementTree.fromstringlist``.
    """
    def _err(msg: str) -> None:
        print_error(f"[XML] ({fp_from_config}) {msg}")
    def _warn(msg: str) -> None:
        print_warning_xml(f"[XML] ({fp_from_config}) {msg}")

    def _process_line(line: str) -> str:
        # comments
        if _XMLPatterns.INVALID_COMMENT_LINE.search(line):
            _warn(f"Line {i+1}: 2+ hyphens inside a comment")
        line = _XMLPatterns.COMMENT.sub("", line)

        # invalid characters
        if _XMLPatterns.INVALID_CHARS.search(line):
            _warn(f"Line {i+1}: invalid character(s)")

        # unescaped ampersand
        if _XMLPatterns.UNESCAPED_AMPERSAND.search(line):
            _warn(f"Line {i+1}: unescaped ampersand(s)")
        line = _XMLPatterns.UNESCAPED_AMPERSAND.sub("", line)

        return line

    # Получаем реальный путь до файла
    for gd_path in [gd_path_main, gd_path_alt]:
        if gd_path is None:
            continue
        if (fp := gd_path.joinpath("config", fp_from_config)).is_file():
            break
    else:
        _err("Not found")
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
            with fp.open("r", encoding=encoding) as f:
                lines_input = f.readlines()
                break
        except UnicodeDecodeError:
            if decode_error_warn:
                _warn(f"Can't be read with encoding='{encoding}'")
            continue
        except OSError as e:
            _err(f"Skipping due to OSError: {e}")
            return []
    else:
        _err("Skipping: unexpected encoding")
        return []

    # Обработка строк и поддержка include-директив
    lines_output = []
    for i, line in enumerate(lines_input):
        if line.startswith("<?xml"):
            continue
        elif line.startswith("#include"):
            parts = line.split('"')
            if len(parts) > 1:
                if len(parts) != 3:
                    _warn(f"Strange #include syntax: line {i+1}")
                part_fp = parts[1].strip()
                lines_output.extend(read_xml(part_fp, gd_path_main, gd_path_alt))
            else:
                _warn(f"Invalid #include syntax: line {i+1}")
        else:
            lines_output.append(_process_line(line))

    return lines_output

# ----------------------------------------------------------------
