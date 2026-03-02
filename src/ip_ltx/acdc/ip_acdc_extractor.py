"""Утилита для извлечения необходимых данных из ``all.spawn``.
Для предварительной декомпиляции полагается на *Universal ACDC*.

Данная утилита в основном используется для импорта в свои конфиги ``alife_*.ltx``
спавн-объектов, расставленных через *X-Ray SDK Level Editor*.

1. Через *X-Ray SDK Level Editor* на локации расставляются спавн-объекты.
2. Через *aiwrapper* осуществляется сборка ``all.spawn``.
3. Через *ACDC Universal* декомпилируется полученный ``all.spawn``.
4. Через ***ip_acdc_extractor*** из секций объектов извлекаются нужные поля.
5. Результат переносится к себе с минимальными правками
   (например, подписать наследование) для дальнейшей сборки
   своего ``all.spawn`` при помощи ***ip_acdc_builder*** и *ACDC*.
"""

import os
import re
import shutil
import subprocess
import traceback
from pathlib import Path
from pathvalidate import is_valid_filename
from typing import TextIO

from ..ip_ltx import Ini, Section
from ..utils import ANSI_COLOR_CODE, print_error, print_warning


_ACDC_LABEL = f"{ANSI_COLOR_CODE.BLACK}ACDC/decompiler{ANSI_COLOR_CODE.DEF}"
_ACDC_CMD = [
    "perl", "universal_acdc.pl", "-d", "all.spawn", "-out", "acdc_decompile", "-nofatal"
]


class Printer:
    """Функции для вывода, используемые данным модулем."""
    _header_printed = False

    @staticmethod
    def line() -> None:
        print(ANSI_COLOR_CODE.BLACK, "-"*64, ANSI_COLOR_CODE.DEF, sep="")

    @staticmethod
    def header() -> None:
        if not Printer._header_printed:
            Printer.line()
            print(
                ANSI_COLOR_CODE.BLACK,
                f"# {Path(__file__).name}",
                ANSI_COLOR_CODE.DEF,
                sep="",
                flush=True
            )
            Printer.line()
            Printer._header_printed = True


def _ini_write(
        ini: Ini,
        file: TextIO,
        extraction_rules: dict[str, str],
        exceptions: set[str],
        exceptions_first_fields: list[str],
        exceptions_hide_fields: set[str],
        u_acdc: bool
) -> None:
    def _get_3v_rounded_to_zero(section: Section, field: str, defval: str | None):
        try:
            nums = section.get_floats(field)
        except Section.Error:
            return defval
        if len(nums) == 3:
            sep = ", " if u_acdc  else ","
            return sep.join([("0" if abs(v) < 0.01 else str(v)) for v in nums])
        return defval
    def _value_getter(section: Section, field: str) -> str | None:
        value = section.field(field)
        match field:
            case "position" | "upd:position" if not u_acdc:
                value = value and value.replace(" ", "")
            case "direction":
                value = _get_3v_rounded_to_zero(section, field, defval=value)
            case "shapes" if not u_acdc:
                value = value and (
                    ",".join([f"shape_{i}" for i in range(int(value))])
                    if value.isdecimal()
                    else value
                )
        return value

    HIDDEN_FIELDS = (
        exceptions_hide_fields | {"id", "version", "script_version", "spawn_id"}
        if not u_acdc
        else {*exceptions_hide_fields}
    )

    for base_section in ini.sections():
        if not base_section.line_exist("name"):
            print_warning(f"[{base_section.id}] Skipped: no 'name'")
            continue
        if not base_section.line_exist("section_name"):
            print_warning(f"[{base_section.id}] Skipped: no 'section_name'")
            continue
        name = base_section.get_string("name")
        section_name = base_section.get_string("section_name")

        section = Section(id=name)
        if section_name in exceptions:
            for field, value in base_section.fields():
                if field not in HIDDEN_FIELDS:
                    section._fields[field] = value
            section.write(
                file=file,
                first=exceptions_first_fields,
                value_getter=_value_getter
            )
        else:
            for field, mask in extraction_rules.items():
                if not base_section.line_exist(field):
                    continue
                if re.fullmatch(mask, section_name):
                    section._fields[field] = base_section.field(field)
            section.write(file=file, value_getter=_value_getter)


def acdc_decompile(all_spawn_fp: str, acdc_dir: str) -> bool:
    """Функция для запуска декомпиляции all.spawn утилитой Universal ACDC
    с предварительным копированием файла all.spawn в папку утилиты.

    :param all_spawn_fp: Путь до файла all.spawn, который нужно декомпилировать.
    :param acdc_dir: Рабочая директория утилиты Universal ACDC.

    :return: True, если декомпиляция прошла успешно.
    """
    Printer.header()
    init_path = Path.cwd()
    all_spawn_path, acdc_path = Path(all_spawn_fp), Path(acdc_dir)

    # Проверка вводных
    if not all_spawn_path.is_file():
        print_error(f"File doesn't exist: '{all_spawn_fp}'")
        Printer.line()
        return False
    if not acdc_path.is_dir():
        print_error(f"Directory doesn't exist: '{acdc_dir}'")
        Printer.line()
        return False

    # Копирование all.spawn в рабочую директорию ACDC
    try:
        shutil.copy2(
            all_spawn_path,
            acdc_path.joinpath("all.spawn")
        )
    except OSError as e:
        print_error(f"Can't copy all.spawn to ACDC directory: {e}")
        Printer.line()
        return False

    # Декомпиляция all.spawn (Universal ACDC)
    try:
        os.chdir(acdc_path)
        print(f"{_ACDC_LABEL}: begin", flush=True)
        subprocess.run(_ACDC_CMD, check=True)
        print(f"{_ACDC_LABEL}: end", flush=True)
        os.chdir(init_path)
    except OSError as e:
        print_error(f"Decompilation failed due to OSError: {e}")
        Printer.line()
        return False
    except subprocess.CalledProcessError as e:
        print_error(f"ACDC: Decompilation failed (code: {e.returncode})")
        Printer.line()
        return False
    
    Printer.line()
    return True

def extract(
        input_dir: str,
        output_dir: str,
        alife_list: list[str],
        extraction_rules: dict[str, str],
        exceptions: set[str],
        exceptions_first_fields: list[str],
        exceptions_hide_fields: set[str],
        keep_universal_acdc_format: bool
) -> bool:
    """Извлечение заданной информации из файлов ``alife_*.ltx``,
    полученных в результате декомпиляции all.spawn утилитой Universal ACDC.
    
    :param input_dir: Директория с файлами ``alife_*.ltx``.
    :param output_dir: Директория, куда сохраняются результаты извлечения.
        Должна отличаться от ``input_dir``.
    :param alife_list: Список имён файлов ``alife_*.ltx`` (с расширением).

    :param extraction_rules: Набор правил, определяющих, какие поля выводить
        для каждой секции должны быть выведены в зависимости от значения поля
        ``section_name``. Ключ - имя поля. Значение - маска (регулярное выражение)
        для ``section_name``, по которой проверяется полное совпадение.
    
    :param exceptions: При выводе секций с перечисленными в этом параметре
        ``section_name`` игнорируются правила, определённые через ``extraction_rules``.
        Вместо этого будут выведены все поля, кроме тех, что были исключены
        другими параметрами. Секции, поля которых выводятся подобным образом,
        далее обозначаются как "секции-исключения".
    :param exceptions_first_fields: Список полей секций-исключений,
        которые будут выведены в первую очередь.
    :param exceptions_hide_fields: Множество полей секций-исключений,
        которые не будут выведены.
    :param keep_universal_acdc_format: Сохранять ли формат Universal ACDC или же
        преобразовать набор полей и их значения в формат классического ACDC.
    
    :return: True, если извлечение прошло успешно.
    """
    Printer.header()
    successful_extract = True

    # Проверка директорий
    input_path, output_path = Path(input_dir), Path(output_dir)
    if not input_path.is_dir():
        print_error(f"Input directory doesn't exist: '{input_dir}'")
        Printer.line()
        return False
    if not output_path.is_dir():
        print_error(f"Output directory doesn't exist: '{output_dir}'")
        Printer.line()
        return False
    if input_path == output_path:
        print_error("Input and output directories can't be the same")
        Printer.line()
        return False
    
    # Проверка имён файлов
    filenames_ok = True
    for filename in alife_list:
        if not is_valid_filename(filename):
            print_error(f"Invalid file name: '{filename}'")
            filenames_ok = False
    if not filenames_ok:
        Printer.line()
        return False

    # Проверка файлов на входе
    all_files_exist = True
    for filename in alife_list:
        p = input_path.joinpath(filename)
        if not p.is_file():
            print_error(f"File doesn't exist: '{p}'")
            all_files_exist = False
    if not all_files_exist:
        Printer.line()
        return False
    
    # Извлечение информации из alife_*.ltx
    if len(alife_list) == 0:
        print_warning("No alife_*.ltx files")
    else:
        for i, fn in enumerate(alife_list):
            try:
                input_fp = str(input_path.joinpath(fn))
                output_fp = str(output_path.joinpath(f"_{fn}"))
                ini = Ini()
                ini.read(input_fp)
                with open(output_fp, "w", encoding="utf-8") as file:
                    _ini_write(
                        ini,
                        file,
                        extraction_rules,
                        exceptions,
                        exceptions_first_fields,
                        exceptions_hide_fields,
                        keep_universal_acdc_format
                    )
            except Exception:
                print("")
                print(
                    f"{ANSI_COLOR_CODE.RED}-{ANSI_COLOR_CODE.DEF}",
                    f"({i+1}/{len(alife_list)}) {fn}"
                )
                print(traceback.format_exc())
                print("", flush=True)
                successful_extract = False
            else:
                shift = len(str(len(alife_list))) - len(str(i+1))
                print(
                    f"{ANSI_COLOR_CODE.GREEN}+{ANSI_COLOR_CODE.DEF}",
                    f"{" "*shift}({i+1}/{len(alife_list)}) {fn}",
                    flush=True
                )
    Printer.line()

    return successful_extract
