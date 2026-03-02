"""Утилита для генерации конфигурационных файлов спавн-объектов - файлов
типа ``alife_*.ltx``, которые используются утилитой ACDC при компиляции ``all.spawn``.

Генерация происходит на основе ltx-файлов (условно говоря, файлов генерации).
Эти файлы можно воспринимать как по сути всё те же привычные ``alife_*.ltx``,
но с расширенным синтаксисом, позволяющим более удобно и гибко описывать спавн-объекты.

Особенности расширенного синтаксиса:

* Возможность использовать наследование как в обычных ltx-файлах.
* Возможность использовать include-директивы как в обычных ltx-файлах.
* Возможность определить т.н. "абстрактную" секцию. Это секции, ID которых
  начинается с символа @. По этим секциям напрямую не генерируется секция
  спавн-объекта - они используются только для наследования другими секциями.
* Если поле имеет значение __NONE__, то оно считается условно незаполненным:

    1. Такое значение позволяет осуществить автозаполнение:
       некоторые свойства upd-пакетов (поля ``upd:*``) при отсутствии своего значения
       позаимствуют его у одноимённого свойства state-пакета.
    2. При наличии такого значения у поля name, оно заменится на ID секции.
    3. Таким образом, используя значение __NONE__ в абстрактных секциях, можно
       избавиться  от необходимости повторяться при описании спавн-объекта.
       Но кроме этого, значение __NONE__ какого-нибдуь поля в абстрактной секции
       можно использовать как метку о том, что это поле обязательно для заполнения.
       Генерация выдаст ошибку, если какое-то поле имеет значение __NONE__ и
       для него нашлось замены в соответствии с пунктами 1 и 2.

Поскольку это **расширенный** синтаксис (а не какой-то принципиально иной),
то в качестве исходных файлов генерации можно использовать всё те же файлы
``alife_*.ltx``, полученные при декомпиляции ``all.spawn`` утилитой ACDC
(такие файлы генерации будут генерировать файлы по содержанию идентичные сами себе).
"""

import itertools
import os
import shutil
import subprocess
import traceback
from pathlib import Path
from pathvalidate import is_valid_filename
from typing import TextIO

from ..ip_ltx import Ini, Section
from ..utils import ANSI_COLOR_CODE, print_error, print_warning


_IDS_MASK = r"^[^@].*$"
_VNONE = "__NONE__"
_FIRST = [
    "section_name",
    "name",
    "position",
    "upd:position",
    "game_vertex_id",
    "level_vertex_id",
    "character_profile",
    "direction",
    "money",
    "object_flags",
    "custom_data",
    "story_id",
    "visual_name",
]
_OVERRIDE = {
    "upd:position": "position",
    "upd:g_team": "g_team",
    "upd:g_squad": "g_squad",
    "upd:g_group": "g_group",
    "upd:health": "health",
}
_OVERRIDE_ID = {
    "name"
}

_ACDC_LABEL = f"{ANSI_COLOR_CODE.BLACK}ACDC/compiler{ANSI_COLOR_CODE.DEF}"
_ACDC_CMD = ["perl", "acdc.pl", "-c", "all.ltx"]


def _ini_write(
        ini: Ini,
        file: TextIO,
        ids_mask: str | None,
        first: list[str],
        vnone: str,
        override: dict[str, str],
        override_id: set[str]
) -> None:
    """Запись всех секций в файл. То же, что и :func:`Ini.write`,
    но с предопределённым параметром-функцией ``value_getter``,
    поведение которой задаётся через ``vnone``, ``override``, ``override_id``.

    :param file: Открытый файл для записи.
    :param ids_mask: Маска-фильтр, определяющая, секции с каким ID выводить.
    :param first: Список имён полей, которые нужно вывести в первую очередь.

    :param vnone: Значение поля, при котором оно считается условно незаполненным.
        Попытка вывода поля с таким значением вызывает исключение,
        если для него не нашлось замены (см. ``override``, ``override_id``).
    :param override: Словарь, определяющий для поля (key),
        из какого другого поля (value) необходимо наследовать
        значение, если собственное - условно незаполненное.
        Наследование нерекурсивное.
    :param override_id: Множество полей, для которых их условно незаполненное значение
        заменится на ID секции. Перед такой заменой происходит попытка замены
        в соответствии с ``override``.

    :raises Exception: при попытке вывести поле с условно незаполненным значением,
        для которого не нашлось замены в соответствии с ``override`` и ``override_id``.
    """
    def _value_getter(section: Section, field: str) -> str | None:
        value = section.field(field)
        if (value == vnone) and (field in override):
            value = section._fields.get(override[field], value)
        if (value == vnone) and (field in override_id):
            value = section.id
        if value == vnone:
            raise Exception(
                f"[{section.id}] Field '{field}' has unresolvable none-value"
            )
        return value

    ini.write(file=file, ids_mask=ids_mask, first=first, value_getter=_value_getter)


def _print_line() -> None:
    """Функция для вывода разделительной линии, используемая функциями данного модуля.
    """
    print(ANSI_COLOR_CODE.BLACK, "-"*64, ANSI_COLOR_CODE.DEF, sep="")


def build(
        input_dir: str,
        output_dir: str,
        alife_list: list[str],
        way_list: list[str]
) -> bool:
    """Преобразование ltx-файлов спавна с раширенным синтаксисом
    в обычные ltx-файлы для считывания утилитой ACDC при компиляции all.spawn.

    * Преобразование осуществляется для файлов со спавн-объектами (``alife_*.ltx``).
    * Файлы с точками путей (``way_*.ltx``) пока копируются как есть.

    :param input_dir: Директория с файлами на вход.
        Эта директория должна содержать ltx-файлы двух типов.
        Во-первых, файлы описания спавн-объектов в расширенном синтаксисе
        (``alife_*.ltx``).
        Во-вторых, файлы с точками путей в классическом для ACDC формате
        (``way_*.ltx``).
    :param output_dir: Директория с файлами на выход.
        Как правило, это рабочая директория утилиты ACDC.
        Должна отличаться от ``input_dir``.
    :param alife_list: Список имён ltx-файлов (с расширением) со спавн-объектами.
    :param way_list: Список имён ltx-файлов (с расширением) с точками путей.

    :return: True, если преобразования и копирования полностью прошли успешно.
    """
    _print_line()
    print(
        ANSI_COLOR_CODE.BLACK,
        f"# {Path(__file__).name}",
        ANSI_COLOR_CODE.DEF,
        sep="",
        flush=True
    )
    successful_build = True
    _print_line()

    # Проверка директорий
    input_path, output_path = Path(input_dir), Path(output_dir)
    if not input_path.is_dir():
        print_error(f"Input directory doesn't exist: '{input_dir}'")
        _print_line()
        return False
    if not output_path.is_dir():
        print_error(f"Output directory doesn't exist: '{output_dir}'")
        _print_line()
        return False
    if input_path == output_path:
        print_error("Input and output directories can't be the same")
        _print_line()
        return False
    
    # Проверка имён файлов
    filenames_ok = True
    for filename in itertools.chain(alife_list, way_list):
        if not is_valid_filename(filename):
            print_error(f"Invalid file name: '{filename}'")
            filenames_ok = False
    if not filenames_ok:
        _print_line()
        return False

    # Проверка файлов на входе
    all_files_exist = True
    for filename in itertools.chain(alife_list, way_list):
        p = input_path.joinpath(filename)
        if not p.is_file():
            print_error(f"File doesn't exist: '{p}'")
            all_files_exist = False
    if not all_files_exist:
        _print_line()
        return False
    
    # Компиляция alife_*.ltx
    if len(alife_list) == 0:
        print_warning("No alife_*.ltx files")
    else:
        for i, fn in enumerate(alife_list):
            try:
                input_fp = str(input_path.joinpath(fn))
                output_fp = str(output_path.joinpath(fn))
                ini = Ini()
                ini.read(input_fp)
                with open(output_fp, "w", encoding="utf-8") as file:
                    _ini_write(
                        ini, file, _IDS_MASK, _FIRST, _VNONE, _OVERRIDE, _OVERRIDE_ID
                    )
            except Exception as e:
                print("")
                print(
                    f"{ANSI_COLOR_CODE.RED}-{ANSI_COLOR_CODE.DEF}",
                    f"({i+1}/{len(alife_list)}) {fn}"
                )
                print(traceback.format_exc())
                print("", flush=True)
                successful_build = False
            else:
                shift = len(str(len(alife_list))) - len(str(i+1))
                print(
                    f"{ANSI_COLOR_CODE.GREEN}+{ANSI_COLOR_CODE.DEF}",
                    f"{" "*shift}({i+1}/{len(alife_list)}) {fn}",
                    flush=True
                )
    _print_line()

    # Копирование way_*.ltx
    if len(way_list) == 0:
        print_warning("No way_*.ltx files")
    else:
        copied_counter = 0
        for i, fn in enumerate(way_list):
            try:
                shutil.copy2(input_path.joinpath(fn), output_path.joinpath(fn))
            except Exception as e:
                print(
                    f"{ANSI_COLOR_CODE.RED}-{ANSI_COLOR_CODE.DEF}",
                    f"{fn}:",
                    str(e)
                )
                successful_build = False
            else:
                copied_counter += 1
        else:
            if copied_counter > 0:
                prefix = (
                    f"{ANSI_COLOR_CODE.GREEN}+{ANSI_COLOR_CODE.DEF}"
                    if copied_counter == len(way_list)
                    else f"{ANSI_COLOR_CODE.YELLOW}+{ANSI_COLOR_CODE.DEF}"
                )
                postfix = (
                    f"({copied_counter})"
                    if copied_counter == len(way_list)
                    else f"({copied_counter}/{len(way_list)})"
                )
                print(prefix, "way_*.ltx", postfix, flush=True)
    _print_line()

    return successful_build


def acdc_compile(acdc_dir: str, spawns_dir: str) -> bool:
    """Функция для запуска компиляции all.spawn утилитой ACDC
    с переносом результата в нужную папку.

    :param acdc_dir: Рабочая директория утилиты ACDC.
    :param spawns_dir: Директория, в которую сохранится скомпилированный all.spawn.

    :return: True, если компиляция и сохранение прошли успешно.
    """
    init_path = Path.cwd()
    acdc_path, spawns_path = Path(acdc_dir), Path(spawns_dir)

    # Проверка директорий
    if not acdc_path.is_dir():
        print_error(f"ACDC directory doesn't exist: '{acdc_dir}'")
        _print_line()
        return False
    if not spawns_path.is_dir():
        print_error(f"Output directory for all.spawn doesn't exist: '{spawns_dir}'")
        _print_line()
        return False

    # Компиляция all.spawn (ACDC)
    try:
        os.chdir(acdc_path)
        print(f"{_ACDC_LABEL}: begin", flush=True)
        subprocess.run(_ACDC_CMD, check=True, capture_output=True, text=True)
        print(f"{_ACDC_LABEL}: end", flush=True)
        os.chdir(init_path)
    except OSError as e:
        print_error(f"Compilation failed due to OSError: {e}")
        _print_line()
        return False
    except subprocess.CalledProcessError as e:
        if len(e.stderr) > 0:
            print_error(f"ACDC: {e.stderr}".strip())
        else:
            print_error(f"ACDC: Compilation failed (code: {e.returncode})")
        _print_line()
        return False

    # Сохранение all.spawn
    try:
        shutil.copy2(
            acdc_path.joinpath("all.spawn.new"),
            spawns_path.joinpath("all.spawn")
        )
    except OSError as e:
        print_error(f"Can't save compiled all.spawn: {e}")
        _print_line()
        return False
    
    _print_line()
    return True
