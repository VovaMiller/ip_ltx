"""
ip_ltx
=====

Базовые классы для работы с ltx-файлами.

Отличия от ``CInifile`` (X-Ray Engine):
---------------------------------------
* Сохранён порядок определения секций и их полей.
* Поле без значения и поле с пустым значением различаются между собой.
* Отличие местных методов получения значения ``get_*`` от движковых ``r_*``:

    - Позволяют читать из секции с пустым ID.
    - Не переводят в нижний регистр данный ID секции.
    - Позволяют задать значение по умолчанию (``defval``).
    - Более придирчивы к формату при преобразовании к другому типу
      (``float``, ``s32``, ``u32``, ``bool``).

* ...
"""

import itertools
import os
import re
from collections.abc import Callable
from pathlib import Path
from typing import Literal, NoReturn, Self, TextIO

from .utils import cast_safe, print_warning, read_file


class Section:
    """Класс одной секции ltx-файла.
    
    :param id: Идентификатор секции.
    :param init: Другая секция, по которой можно инициализировать поля.
    :param _src: Имя файла-источника (откуда будет считана секция).
        Используется при логировании и в сообщениях об ошибках.
    :raises ValueError: при попытке инициализации с невалидным ID.
    """
    id: str
    _fields: dict[str, str | None]
    _fields_own: set[str]
    _src: str

    def __init__(self, id: str, init: Self | None = None, _src: str = ""):
        if ("\n" in id) or ("\r" in id):
            raise ValueError("Invalid section ID: multi-line")
        if ("]" in id):
            raise ValueError("Invalid section ID: symbol ']' is forbidden")
        self.id = id
        if init is None:
            self._fields = {}
            self._fields_own = set()
            self._src = _src
        else:
            self._fields = init._fields.copy()
            self._fields_own = init._fields_own.copy()
            self._src = _src if (len(_src) > 0) else init._src


    class Error(Exception):
        """Исключение, вызываемое классом :class:`Section`.

        :param src: Источник, откуда была считана секция (например, имя файла).
        :param id: ID секции.
        :param msg: Тело сообщения об ошибке.
        """
        def __init__(self, src: str, id: str, msg: str):
            super().__init__(
                f"({src}) [{id}] {msg}"
                if len(src) > 0
                else f"[{id}] {msg}"
            )
            self.src = src
            self.id = id
            self.msg = msg

    def _raise(self, msg: str) -> NoReturn:
        raise Section.Error(self._src, self.id, msg)


    def write(
            self,
            file: TextIO,
            fields_mask: str | None = None,
            first: list[str] = [],
            value_getter: Callable[[Self, str], str | None] | None = None
    ) -> None:
        """Запись секции в файл.

        * Поддерживает вывод многострочных значений для поля с именем ``custom_data``.
          Таким образом, поддерживается совместимость с ltx-файлами,
          используемыми ACDC для компиляции all.spawn.

        :param file: Открытый файл для записи.
        :param fields_mask: Маска-фильтр, определяющая, поля с каким именем выводить.
            Задаётся регулярным выражением. Проверяется полное совпадение.
            Если None, то выводит все существующие поля секции.
        :param first: Список имён полей, которые нужно вывести в первую очередь.
            В остальном, поля выводятся в том порядке, в котором они
            изначально были записаны в секцию.
        :param value_getter: Функция, определяющая то, как по данной секции и
            имени её поля будет получено значение.

            * По умолчанию (если указано None) используется непосредственное значение,
              получаемое методом :param:`Section.field`.
            * Переопределение этого параметра может быть использовано
              для предобработки значений перед их выводом.
            * При любом вызове этой функции гарантируется,
              что указанное поле в указанной секции существует.
        """
        value_getter = value_getter or Section.field
        file.write(f"[{self.id}]\n")
        written_fields = set()
        for field in itertools.chain(first, self.lines()):
            # Нужно/можно ли выводить это поле
            if field in written_fields:
                continue
            if not self.line_exist(field):
                continue
            if ("\n" in field) or ("\r" in field):
                print_warning((
                    f"[{self.id}] "
                    "Skipped field with multiline name: "
                    f"'{"\\n".join(field.splitlines())}'"
                ))
                continue
            if (fields_mask is not None) and not re.fullmatch(fields_mask, field):
                continue

            # Выводим строчку (или строчки)
            value = value_getter(self, field)
            if value is None:
                file.write(f"{field}\n")
            elif ("\n" in value) or ("\r" in value):
                if field == "custom_data":
                    file.write((
                        "custom_data = <<END\n"
                        f"{value.replace("\r", "").removesuffix("\n")}\n"
                        "END\n"
                    ))
                else:
                    print_warning((
                        f"[{self.id}] "
                        f"Value of the field '{field}' is multiline,"
                        " so it was flattened"
                    ))
                    value_fmt = " ".join(value.splitlines()).strip()
                    file.write(f"{field} = {value_fmt}\n")
            else:
                value_fmt = value.strip()
                file.write(f"{field} = {value_fmt}\n")
            written_fields.add(field)
        file.write("\n")


    def field(self, k: str) -> str | None:
        """Получение значения существующего поля.

        :param k: Имя поля.
        :raises Section.Error: если указанного поля нет.
        :return: Значение поля или None, если оно без значения.
        """
        if k not in self._fields:
            self._raise(f"field '{k}' is absent")
        return self._fields[k]

    def lines(self):
        """Набор имён всех полей секции.
        Представлен в том порядке, в котором в секцию добавлялись поля.
        """
        return self._fields.keys()

    def fields(self):
        """Набор всех пар (поле, значение).
        Представлен в том порядке, в котором в секцию добавлялись поля.
        """
        return self._fields.items()


    def line_exist(self, k: str) -> bool:
        """Проверка на то, что поле с укзанным именем существует.
        """
        return (k in self._fields)

    def line_exist_with_value(self, k: str) -> bool:
        """Проверка на то, что поле с укзанным именем существует и имеет значение
        (то есть оно не None).
        """
        return (k in self._fields) and (self._fields[k] is not None)


    def clear(self) -> None:
        """Удаление всех полей из секции."""
        self._fields.clear()
        self._fields_own.clear()

    def add(
            self,
            field: str,
            value: str | None,
            overwrite: bool = False,
            preserve_value_whitespaces: bool = False
    ) -> None:
        """Добавить поле с указанным значение.

        :param field: Имя поля.
            Перед регистрацией пробельные символы с краю обрезаются.
        :param value: Значение поля.
            Перед присвоением полю пробельные символы будут отфильтрованы
            как при чтении ltx-файла. Исключение - поле ``custom_data``.
        :param overwrite: Можно ли перезаписать уже существующее поле.
        :param preserve_value_whitespaces: Не удалять из значения поля
            пробельные символы (кроме тех, что с краю).
            По умолчанию они удаляются, если не находятся между парой кавычек.
        :raises Section.Error: если поле уже существует, а ``overwrite == False``.
        :raises ValueError: если дан неверный формат имени поля или значения.
        """
        if type(field) != str:
            raise ValueError("Field must be string")
        if (type(value) != str) and (value is not None):
            raise ValueError("Field value must be string or None")
        field = field.strip()
        if not overwrite and self.line_exist(field):
            self._raise(f"Field '{field}' already exists")
        if len(field) == 0:
            raise ValueError("Field name can't be empty")
        if (";" in field) or ("//" in field):
            raise ValueError("Field name can't contain comments")
        if ("\n" in field) or ("\r" in field):
            raise ValueError("Field name can't be multi-line")
        if value is not None:
            if (";" in value) or ("//" in value):
                raise ValueError("Value can't contain comments")
            if field == "custom_data":
                self._fields[field] = value.strip()
            else:
                if (("\n" in value) or ("\r" in value)):
                    raise ValueError("Multi-line value is allowed only for custom_data")
                self._fields[field] = (
                    value.strip()
                    if preserve_value_whitespaces
                    else Section.fmt_value_whitespaces(value)
                )
        else:
            self._fields[field] = None
        self._fields_own.add(field)


    @staticmethod
    def fmt_value_whitespaces(v: str) -> str:
        """Фильтрация пробельных символов перед присвоением значения полю.
        Все пробельные символы удаляются, за исключением тех, что расположены
        между парой прямых двойных кавычек. Если последней кавычке не нашлось пары,
        то все пробельные символы после неё будут сохранены.
        """
        parts = v.split('"')
        for i in range(0, len(parts), 2):
            parts[i] = "".join(parts[i].split())
        return '"'.join(parts)

    @staticmethod
    def cast_string_wb(v: str) -> str:
        l = 1 if v.startswith('"') else 0
        r = (len(v) - 1) if v.endswith('"') else len(v)
        return v[l:r]

    @staticmethod
    def cast_float(v: str) -> float | None:
        return cast_safe(v, float, defval=None)
    
    @staticmethod
    def cast_int(v: str) -> int | None:
        return cast_safe(v, int, defval=None)

    @staticmethod
    def cast_uint(v: str) -> int | None:
        return int(v) if v.isdecimal() else None
    
    @staticmethod
    def cast_bool(v: str) -> bool | None:
        match v.strip().lower():
            case "on" | "yes" | "true" | "1":
                return True
            case "off" | "no" | "false" | "0":
                return False
        return None


    def get_elem[R](
            self,
            type_caster: Callable[[str], R | None],
            type_label: str,
            k: str,
            defval: R | None
    ) -> R:
        """Получить значение поля с нужным типом.

        Базовый метод для ряда других методов (``get_*``).

        :param type_caster: Функция для конвертации значения поля в нужный тип,
            возвращающая ``None`` в случае невозможности конвертации.
        :param type_label: Текстовое обозначения типа.
            Используется в сообщении исключения.
        :param k: Имя поля.
        :param defval: Значение по умолчанию.
            Определяет поведение функции в случае,
            когда указанного поля нет или оно без значения.
        
        :raises Section.Error: в двух случаях:
        
            1. Конвертация значения поля невозможна.
            2. ``defval is None`` и при этом указанного поля нет или оно без значения.

        :return: Преобразованное в нужный тип значение поля,
            либо ``defval``, если он не ``None``
            и указанного поля нет или оно без значения.
        """
        r = self._fields.get(k, None)
        if r is not None:
            r = type_caster(r)
            if r is not None:
                return r
            self._raise(f"field '{k}' can't be read as *{type_label}*")
        if defval is None:
            why = "None value" if (k in self._fields) else "non-existent"
            self._raise(f"field '{k}' can't be read as *{type_label}*: {why}")
        return defval

    def get_string(self, k: str, defval: str | None = None) -> str:
        """Получить значение поля k как обычную строку (str).
        О деталях работы, см. :func:`get_elem`.
        """
        return self.get_elem(str, "str", k, defval)

    def get_string_wb(self, k: str, defval: str | None = None) -> str:
        """Получить значение поля k как обычную строку (str),
        но с обрезанными по краям кавычками.
        О деталях работы, см. :func:`get_elem`.
        """
        return self.get_elem(Section.cast_string_wb, "string_wb", k, defval)

    def get_float(self, k: str, defval: float | None = None) -> float:
        """Получить значение поля k как число с плавающей точкой (float).
        О деталях работы, см. :func:`get_elem`.
        """
        return self.get_elem(Section.cast_float, "float", k, defval)

    def get_int(self, k: str, defval: int | None = None) -> int:
        """Получить значение поля k как целое число (int).
        О деталях работы, см. :func:`get_elem`.
        """
        return self.get_elem(Section.cast_int, "int", k, defval)
    
    def get_uint(self, k: str, defval: int | None = None) -> int:
        """Получить значение поля k как неотрицательное целое число.
        О деталях работы, см. :func:`get_elem`.
        """
        return self.get_elem(Section.cast_uint, "uint", k, defval)
    
    def get_bool(self, k: str, defval: bool | None = None) -> bool:
        """Получить значение поля k как bool.
        О деталях работы, см. :func:`get_elem`.
        """
        return self.get_elem(Section.cast_bool, "bool", k, defval)


    def get_elems[R](
            self,
            type_caster: Callable[[str], R | None],
            type_label: str,
            k: str,
            mandatory: bool
    ) -> list[R]:
        """Получить значение поля как список элементов нужного типа.
        Подразумевается, что элементы разделены запятой.

        Базовый метод для ряда других методов (``get_*s``).

        :param type_caster: Функция для конвертации элементов в нужный тип,
            возвращающая ``None`` в случае невозможности конвертации.
        :param type_label: Текстовое обозначения типа.
            Используется в сообщении исключения.
        :param k: Имя поля.
        :param mandatory: Обязательное ли это поле.
            Определяет поведение функции в случае,
            когда указанного поля нет или оно без значения.
        
        :raises Section.Error: в двух случаях:
        
            1. Конвертация значения хотя бы одного элемента невозможна.
            2. ``mandatory == True`` и при этом
               указанного поля нет или оно без значения.

        :return: Построенный по значению поля список элементов нужного типа,
            либо пустой список, если ``mandatory == False``
            и указанного поля нет или оно без значения.
        """
        v = self._fields.get(k, None)
        if v is not None:
            if len(v.strip()) == 0:
                return []
            r = []
            for i, rr in enumerate([type_caster(vv.strip()) for vv in v.split(",")]):
                if rr is None:
                    self._raise((
                        f"field '{k}' can't be read as *list[{type_label}]*"
                        f": value #{i+1} is invalid"
                    ))
                r.append(rr)
            return r
        if mandatory:
            why = "None value" if (k in self._fields) else "non-existent"
            self._raise(f"field '{k}' can't be read as *list[{type_label}]*: {why}")
        return []

    def get_strings(self, k: str, mandatory: bool = True) -> list[str]:
        """Получить значение поля k как список из обычных строк.
        О деталях работы, см. :func:`get_elems`.
        """
        return self.get_elems(str, "str", k, mandatory)

    def get_floats(self, k: str, mandatory: bool = True) -> list[float]:
        """Получить значение поля k как список из чисел с плавающей точкой.
        О деталях работы, см. :func:`get_elems`.
        """
        return self.get_elems(Section.cast_float, "float", k, mandatory)

    def get_ints(self, k: str, mandatory: bool = True) -> list[int]:
        """Получить значение поля k как список из целых чисел.
        О деталях работы, см. :func:`get_elems`.
        """
        return self.get_elems(Section.cast_int, "int", k, mandatory)

    def get_uints(self, k: str, mandatory: bool = True) -> list[int]:
        """Получить значение поля k как список из неотрицательных целых чисел.
        О деталях работы, см. :func:`get_elems`.
        """
        return self.get_elems(Section.cast_uint, "uint", k, mandatory)

    def get_bools(self, k: str, mandatory: bool = True) -> list[bool]:
        """Получить значение поля k как список из bool.
        О деталях работы, см. :func:`get_elems`.
        """
        return self.get_elems(Section.cast_bool, "bool", k, mandatory)


    def get_items(
            self,
            k: str,
            mandatory: bool = True,
            parsing_mode: Literal["comma", "vanilla", "vanilla_ext"] = "comma"
    ) -> list[tuple[str, int]]:
        """Парсит строку вида
        ``<section>,<count>,<section>,<section>,...``
        в список пар ``(<section>, <count>)``.

        Аналог LUA-функции ``xr_box.r_items``,
        но допускает только целые числа (в том числе отрицательные).

        :param k: Имя поля, значение которого нужно считать.
        :param mandatory: Определяет поведение функции в случае,
            когда поля нет или оно без значения:
            
            * ``mandatory=True``: выдаст исключение
            * ``mandatory=False``: вернёт пустой список
        
        :param parsing_mode: Как исходная строка будет преобразована в список:

            * ``comma`` - обычное разбиение по запятым.
            * ``vanilla`` - алгоритм, повторяющий LUA-функцию ``_g.parse_names``.
              Не поддерживает точки и дефисы в элементах списка.
              Не поддерживает отрицательные числа.
            * ``vanilla_ext`` - алгоритм, повторяющий альтернативную LUA-функцию
              ``parse_names``, использующуюся в скриптах ``se_respawn``,
              ``task_manager``, ``treasure_manager``, ``xr_box``.
              Поддерживает точки и дефисы внутри элементов списка.
              Не поддерживает отрицательные числа.

        :raises Section.Error: если поля нет или оно без значения,
            и при этом ``mandatory=True``.
        :return: Список пар ``(<section>, <count>)``.
        """
        r = self._fields.get(k, None)
        if r is not None:
            r = str(r)
            if len(r) == 0:
                return []
            match parsing_mode:
                case "comma":
                    t = [vv.strip() for vv in r.split(",")]
                case "vanilla":
                    t = re.findall(r"([\w\\]+)[^\w\s]*", r)
                case "vanilla_ext":
                    t = re.findall(r"([\w\-.\\]+)[^\w\s]*", r)
                case _:
                    self._raise(f"get_items: unknown parsing_mode ({parsing_mode})")
            r = []
            n = len(t)
            i = 0
            while i < n:
                _section, _count = "", 0
                _section = t[i]
                if (i + 1) < n:
                    p = cast_safe(t[i+1], int, None)
                    if p is not None:
                        _count = p
                        i += 2
                    else:
                        _count = 1
                        i += 1
                else:
                    _count = 1
                    i += 1
                r.append((_section, _count))
            return r
        if mandatory:
            why = "None value" if (k in self._fields) else "non-existent"
            self._raise(f"field '{k}' can't be read: {why}")
        return []


    def get_pair[R](
            self,
            type_caster: Callable[[str], R | None],
            type_label: str,
            k: str,
            sep: str
    ) -> tuple[R, R]:
        """Получить значение поля как пару элементов нужного типа.

        Базовый метод для ряда других методов (``get_pair_*``).

        :param type_caster: Функция для конвертации элементов в нужный тип,
            возвращающая ``None`` в случае невозможности конвертации.
        :param type_label: Текстовое обозначения типа.
            Используется в сообщении исключения.
        :param k: Имя поля.
        :param sep: Разделитель, по которому
            из строкового значения поля получается список.
        
        :raises Section.Error: в одном из трёх случаев:
        
            1. Указанного поля нет или оно без значения.
            2. Размер списка не равен двум.
            3. Конвертация значения хотя бы одного элемента невозможна.

        :return: Построенная по строковому значению поля пара элементов нужного типа.
        """
        def _err(why: str) -> NoReturn:
            self._raise(f"field '{k}' can't be read as a pair of *{type_label}*: {why}")
        
        v = self._fields.get(k, None)
        if v is None:
            _err("None value" if (k in self._fields) else "non-existent")
        
        v = v.strip()
        v = v.split(sep) if len(v) > 0 else []
        if len(v) != 2:
            _err(f"expected exactly 2 values, got {len(v)}")
        
        v = [type_caster(vv.strip()) for vv in v]
        if v[0] is None:
            _err("value #1 is invalid")
        if v[1] is None:
            _err("value #2 is invalid")

        return (v[0], v[1])

    def get_pair_str(self, k: str, sep: str = ",") -> tuple[str, str]:
        """Получить значение поля k как пару обычных строк (str).
        О деталях работы, см. :func:`get_pair`.
        """
        return self.get_pair(str, "str", k, sep)

    def get_pair_float(self, k: str, sep: str = ",") -> tuple[float, float]:
        """Получить значение поля k как пару чисел с плавающей точкой (float).
        О деталях работы, см. :func:`get_pair`.
        """
        return self.get_pair(Section.cast_float, "float", k, sep)

    def get_pair_int(self, k: str, sep: str = ",") -> tuple[int, int]:
        """Получить значение поля k как пару целых чисел (int).
        О деталях работы, см. :func:`get_pair`.
        """
        return self.get_pair(Section.cast_int, "int", k, sep)
    
    def get_pair_uint(self, k: str, sep: str = ",") -> tuple[int, int]:
        """Получить значение поля k как пару неотрицательных целых чисел.
        О деталях работы, см. :func:`get_pair`.
        """
        return self.get_pair(Section.cast_uint, "uint", k, sep)
    
    def get_pair_bool(self, k: str, sep: str = ",") -> tuple[bool, bool]:
        """Получить значение поля k как пару bool.
        О деталях работы, см. :func:`get_pair`.
        """
        return self.get_pair(Section.cast_bool, "bool", k, sep)


# ----------------------------------------------------------------


class Ini:
    """Класс, считывающий ltx-файл(ы).
    
    Аналог LUA-класса ``ini_file`` (``CScriptIniFile``) и движкового ``CInifile``.

    :param name: Имя экземпляра класса. Используется при выводе ошибок.
    
    :param ini_meta: Экземпляр этого же класса с настройками путей папок gamedata.
        Эти настройки полезны для последующего чтения файлов из gamedata.
        Пути указываются в секции ``[settings]``:

            * ``gamedata_path_mod`` - путь до основной папки gamedata;
              как правило, это просто папка gamedata мода;
              указывается обязательно.
            * ``gamedata_path_alt`` - путь до альтернативной папки gamedata;
              как правило, это разархивированные ``gamedata.db*``;
              указывать не обязательно, если в основной папке gamedata
              уже содержатся все ресурсы игры.

    :raises Ini.Error: при ошибке инициализации.
    """
    _s: dict[str, Section]
    _name: str

    gdm: Path | None
    """Объект пути до основной папки gamedata."""

    gda: Path | None
    """Объект пути до альтернативной папки gamedata."""

    show_ltx_warnings: bool
    """Отображаются ли warning-сообщения при считывании ltx-файлов.
    
    По умолчанию ``True``.

    Отображение отключается для ltx-файлов из gamedata при
    установке переменной окружения ``HIDE_GAMEDATA_LTX_WARNINGS``.
    """

    class Error(Exception):
        """Исключение, вызываемое классом :class:`Ini`."""
        pass

    def __init__(self, name: str = "", ini_meta: Self | None = None):
        self._s = {}
        self._name = name
        self.gdm = None
        self.gda = None
        self.show_ltx_warnings = True
        if ini_meta is not None:
            if not ini_meta.section_exist("settings"):
                raise Ini.Error("ini_meta doesn't have mandatory section [settings]")
            
            # gamedata_path_mod
            gdm_str = ini_meta.get_string_wb("settings", "gamedata_path_mod", "")
            if len(gdm_str) > 0:
                self.gdm = Path(gdm_str).resolve()
                if not self.gdm.is_dir():
                    raise Ini.Error((
                        "Directory provided in 'gamedata_path_mod' doesn't exist: "
                        f"{gdm_str}"
                    ))
            else:
                raise Ini.Error((
                    "ini_meta: 'gamedata_path_mod' must be provided"
                    " in section [settings]"
                ))

            # gamedata_path_alt
            gda_str = ini_meta.get_string_wb("settings", "gamedata_path_alt", "")
            if len(gda_str) > 0:
                self.gda = Path(gda_str).resolve()
                if not self.gda.is_dir():
                    raise Ini.Error((
                        "Directory provided in 'gamedata_path_alt' doesn't exist: "
                        f"{gda_str}"
                    ))
            
            # Доп. проверка путей
            if (self.gdm is not None) and (self.gda is not None):
                if self.gdm == self.gda:
                    raise Ini.Error("gamedata paths can't be equal")
                if (
                    self.gdm.is_relative_to(self.gda)
                    or self.gda.is_relative_to(self.gdm)
                ):
                    raise Ini.Error("gamedata paths can't be relative to each other")

            # Указанная ini_meta - критерий того, что мы оперируем файлами из gamedata
            str_opt = os.environ.get("HIDE_GAMEDATA_LTX_WARNINGS", "off")
            if Section.cast_bool(str_opt) is True:
                self.show_ltx_warnings = False


    def _raise(self, msg: str) -> NoReturn:
        raise Ini.Error(
            f"{self._name} | {msg}" if len(self._name) > 0 else msg
        )


    def _get_fptr(self, fp: str, line_num: int | None) -> str:
        suffix = f":{line_num}" if (line_num is not None) else ""
        file_path = Path(fp)
        if (self.gdm is not None) and file_path.is_relative_to(self.gdm):
            return f"MOD:{file_path.relative_to(self.gdm)}{suffix}"
        elif (self.gda is not None) and file_path.is_relative_to(self.gda):
            return f"ALT:{file_path.relative_to(self.gda)}{suffix}"
        else:
            return f"{file_path}{suffix}"

    def _reader_error(
            self,
            fp: str | None,
            ln: int | None,
            msg: str
    ):
        parts = []
        if len(self._name) > 0:
            parts.append(self._name)
        if (fp is not None) and (len(fp) > 0):
            parts.append(self._get_fptr(fp, ln))
        elif ln is not None:
            parts.append(f"_:{ln}")
        parts.append(msg)
        raise Ini.Error(" | ".join(parts))

    def _reader_warning(
            self,
            fp: str | None,
            ln: int | None,
            sid: str | None,
            msg: str
    ) -> None:
        if self.show_ltx_warnings:
            parts = []
            if len(self._name) > 0:
                parts.append(self._name)
            if (fp is not None) and (len(fp) > 0):
                parts.append(self._get_fptr(fp, ln))
            elif ln is not None:
                parts.append(f"_:{ln}")
            if sid is not None:
                parts.append(f"[{sid}]")
            parts.append(msg)
            print_warning(" | ".join(parts))

    def read_raw(
            self,
            raw: str,
            fp_src: str = "",
            _current_section: Section | None = None,
            preserve_value_whitespaces: bool = False
    ) -> None:
        """Считывание данных о секциях непосредственно со строки (str).

        * Поддерживает наследование (в т.ч. множественное).
        * Поддерживает include-директивы.
        * Для поля custom_data поддерживается формат многострочного значения.
          Синтаксис: ``custom_data = <<END (new lines) END`` (типа heredoc из Perl).
          Таким образом, поддерживается чтение ltx-файлов, полученных
          декомпиляцией all.spawn через ACDC.

        :param raw: Текст с данными.
        :param fp_src: Путь к файлу, откуда взят текст.
            Необходимо для поддержки ``#include``, а также ``Section._src``.
        :param _current_section: Указатель на объект секции,
            на которой остановилось чтение.
            Используется самой функцией; в остальном, можно оставлять None.
        :param preserve_value_whitespaces: При чтении значения поля сохранить
            все его пробельные символы (кроме тех, что с краю).
            По умолчанию они сохраняются только если находятся между парой кавычек.
        :raises Ini.Error: при ошибке считывания.
        """
        def _err(ln: int, msg: str):
            self._reader_error(fp_src, ln, msg)
        def _wrn(ln: int, sid: str | None, msg: str) -> None:
            self._reader_warning(fp_src, ln, sid, msg)
        
        custom_data_buffer: str | None = None
        for i, line in enumerate(raw.splitlines(), start=1):
            line = line.strip()

            # Cutting off comment part
            semi = line.find(";")
            semi_1 = line.find("/")
            if (
                semi_1 != -1
                and (semi_1 + 1) < len(line)
                and line[semi_1 + 1] == "/"
                and (semi == -1 or semi_1 < semi)
             ):
                semi = semi_1;
            if semi != -1:
                line = line[:semi]
            
            # Warning about C-style comment bug
            if line.find("//") != -1:
                _wrn(i, None, "C-style comment was not recognized due to xrEngine bug")

            # custom_data processing
            if custom_data_buffer is not None:
                assert _current_section is not None, (
                    "custom_data_buffer exists, but there is no current_section"
                )
                if (line.strip() == "END"):
                    _current_section._fields["custom_data"] = custom_data_buffer
                    custom_data_buffer = None
                else:
                    custom_data_buffer += f"{line}\n"
                continue

            # Ignore empty lines
            if len(line.strip()) == 0:
                continue

            # "#include" support
            if line.startswith("#include"):
                # Извлечение пути до файла.
                parts = line.split('"')
                if len(parts) == 1:
                    _err(i, "Invalid #include syntax")
                elif len(parts) != 3:
                    _wrn(i, None, "Strange #include syntax")
                part_fp = parts[1].strip()

                # Получение абсолютного пути базовой директории.
                if len(fp_src) == 0:
                    _err(i, "Can't process #include: unknown base path")
                dir_base = Path(fp_src).parent.resolve()

                # Объекты путей до gamedata
                gdm = self.gdm
                gda = self.gda

                # Если это внутри оригинальной gamedata,
                #  то нужно перепрыгнуть в gamedata мода.
                if (gdm is not None) and (gda is not None):
                    if dir_base.is_relative_to(gda):
                        dir_base = gdm.joinpath(dir_base.relative_to(gda))

                # Путь до файла, который нужно включить.
                p_inc = dir_base.joinpath(part_fp).resolve()

                # Если файла нет, а его путь внутри gamedata мода,
                #  то пробуем найти его в папке оригинальной gamedata.
                if not p_inc.is_file() and (gdm is not None) and (gda is not None):
                    if p_inc.is_relative_to(gdm):
                        p_inc = gda.joinpath(p_inc.relative_to(gdm))

                # Если файла всё равно нет, то приплыли.
                if not p_inc.is_file():
                    # Определяем, шёл ли путь в какую-либо gamedata.
                    if (gdm is not None) and p_inc.is_relative_to(gdm):
                        inside_gamedata = True
                        str_inc = str(p_inc.relative_to(gdm))
                    elif (gda is not None) and p_inc.is_relative_to(gda):
                        inside_gamedata = True
                        str_inc = str(p_inc.relative_to(gda))
                    else:
                        inside_gamedata = False
                        str_inc = str(p_inc)
                    if inside_gamedata:
                        _err(i, (
                            f"#include error: gamedata doesn't have this file"
                            f" (\"{str_inc}\")"
                        ))
                    else:
                        _err(i, (
                            f"#include error: file doesn't exist (\"{str_inc}\")"
                        ))
                
                str_inc = str(p_inc)
                self.read_raw(
                    raw=read_file(str_inc),
                    fp_src=str_inc,
                    _current_section=_current_section,
                    preserve_value_whitespaces=preserve_value_whitespaces
                )
                continue

            # New section
            if line.startswith("["):
                # Parsing line
                idx_cls = line.find("]")
                idx_inh = line.find("]:")
                if (idx_cls == -1):
                    _err(i, "Invalid section declaration")
                
                # Some warnings about strange declarations
                if idx_inh != -1:
                    if idx_cls != idx_inh:
                        _wrn(
                            i, None,
                            "Garbage text inside the section declaration line"
                        )
                else:
                    if idx_cls != (len(line.rstrip()) - 1):
                        _wrn(
                            i, None,
                            "Garbage text at the end of the section declaration line"
                        )
                
                # Initializing section
                _id = line[1:idx_cls].lower()
                if _id in self._s:
                    _err(i, f"Duplicate section [{_id}] found")
                if any(c.isspace() for c in _id):
                    _wrn(i, _id, "Unsafe section ID: whitespaces")
                if len(_id) == 0:
                    _wrn(i, _id, "Section with empty ID found")
                fn_src = Path(fp_src).name if (len(fp_src) > 0) else ""
                section = Section(_id, _src=fn_src)

                # Inheritance
                if (idx_inh != -1):
                    parents = [
                        part.strip().lower() for part in line[idx_inh+2:].split(",")
                    ]
                    if any(len(s) == 0 for s in parents):
                        _err(i, "Invalid inheritance")
                    for parent in parents:
                        psect = self._s.get(parent, None)
                        if psect is not None:
                            for k, v in psect._fields.items():
                                section._fields[k] = v
                        else:
                            _err(i, f"Inheritance from unknown section [{parent}]")

                # Registrating
                self._s[_id] = section
                _current_section = self._s[_id]
                continue

            # Section's field
            if _current_section is not None:
                _id = _current_section.id

                # Extracting field name and its value
                if (idx := line.find("=")) != -1:
                    lv = line[:idx].strip()
                    rv = line[idx+1:]
                    if len(lv) == 0:
                        _wrn(i, _id, "Ignoring line with empty field name")
                        continue
                    if (lv == "custom_data") and (rv.strip() == "<<END"):
                        custom_data_buffer = ""
                        field, value = lv, ""
                    elif preserve_value_whitespaces:
                        field, value = lv, rv.strip()
                    else:
                        field, value = lv, Section.fmt_value_whitespaces(rv)
                        # rvs = rv.strip() if (rv.count('"') % 2) == 0 else rv.lstrip()
                        # if len(value) != len(rvs):
                        #     _wrn(i, _id, "Value has redundant whitespaces")
                else:
                    field, value = line.strip(), None
                
                # Setting field's value
                if field in _current_section._fields_own:
                    _wrn(i, _id, f"Redeclaration of '{field}'")
                _current_section._fields[field] = value
                _current_section._fields_own.add(field)
            else:
                _wrn(i, None, "Ignoring redundant text")
                continue

    def read(
            self,
            fp0: str,
            inside_gamedata: bool = False,
            preserve_value_whitespaces: bool = False
    ) -> None:
        """Считать данные с файла.

        :param fp0: Путь до файла.
        :param inside_gamedata: Если True, то интерпретирует путь до файла
            как указанный относительно папки gamedata.
            В первую очередь ищет файл в gamedata мода;
            если его там нет, то пробует gamedata оригинала.
        :param preserve_value_whitespaces: При чтении значения поля сохранить
            все его пробельные символы (кроме тех, что с краю).
            По умолчанию они сохраняются только если находятся между парой кавычек.
        :raises Ini.Error: при ошибке считывания.
        """
        fp = None
        if inside_gamedata:
            if self.gdm is None:
                self._raise("gamedata path is not specified")
            p = self.gdm.joinpath(fp0).resolve()
            if p.is_file():
                fp = str(p)
            elif self.gda is not None:
                p = self.gda.joinpath(fp0).resolve()
                if p.is_file():
                    fp = str(p)
            if fp is None:
                self._raise(f"gamedata doesn't have this file (\"{fp0}\")")
        else:
            if Path(fp0).is_file():
                fp = fp0
            if fp is None:
                self._raise(f"FILE DOES NOT EXIST (\"{fp}\")")
        self.read_raw(
            raw=read_file(fp),
            fp_src=fp,
            preserve_value_whitespaces=preserve_value_whitespaces
        )


    def write(
            self,
            file: TextIO,
            ids_mask: str | None = None,
            fields_mask: str | None = None,
            first: list[str] = [],
            value_getter: Callable[[Section, str], str | None] | None = None
    ) -> None:
        """Запись всех секций в файл.

        О деталях работы, см. :func:`Section.write`.
        
        :param file: Открытый файл для записи.
        :param ids_mask: Маска-фильтр, определяющая, секции с каким ID выводить.
            Задаётся регулярным выражением. Проверяется полное совпадение.
            Если None, то выводит все существующие поля секции.
        :param fields_mask: Маска-фильтр, определяющая, поля с каким именем выводить.
        :param first: Список имён полей, которые нужно вывести в первую очередь.
        :param value_getter: Функция, определяющая то, как по данной секции и
            имени её поля будет получено значение.
        """
        for section in self.sections():
            if (ids_mask is not None) and not re.fullmatch(ids_mask, section.id):
                continue
            section.write(file, fields_mask, first, value_getter)


    def section(self, id: str) -> Section:
        """Получение объекта секции по её ID.

        :param id: ID секции.
        :raises Ini.Error: если секции с указанным ID не существует.
        :return: Объект секции.
        """
        if id not in self._s:
            self._raise(f"section [{id}] doesn't exist")
        return self._s[id]

    def ids(self):
        return self._s.keys()

    def sections(self):
        return self._s.values()
    
    def get_section_index(self, section_id: str) -> int:
        """Получить порядковый номер секции с указанным ID.
        Возвращает -1, если такой секции не существует.
        """
        return list(self._s.keys()).index(section_id) if (section_id in self._s) else -1


    def section_exist(self, id: str) -> bool:
        """Существует ли секция с указанным ID.
        """
        return (id in self._s)

    def line_exist(self, id: str, k: str) -> bool:
        """Проверка наличия поля в секции.

        :param id: ID секции.
        :param k: Имя поля.
        :raises Ini.Error: если секции с указанным ID не существует.
        :return: Существует ли поле в секции с указанным ID.
        """
        if id not in self._s:
            self._raise(f"section [{id}] doesn't exist")
        return (k in self._s[id]._fields)


    def clear(self):
        """Удаление всех секций."""
        self._s.clear()

    def add(
            self,
            section: Section,
            by_reference: bool = False,
            overwrite: bool = False
    ) -> None:
        """Добавить секцию.

        :param section: Объект секции.
        :param by_reference: Если True, то не будет создавать копию объекта секции
            перед добавлением во внутреннее хранилище.
        :param overwrite: Если секция с таким ID уже существует, то
            можно ли её перезаписать.
        :raises Ini.Error: если секция с таким ID уже существует,
            а ``overwrite == False``.
        """
        if not overwrite and self.section_exist(section.id):
            self._raise(f"Section [{section.id}] already exists")
        self._s[section.id] = (
            section
            if by_reference
            else Section(id=section.id, init=section)
        )


    def get_string(self, id: str, k: str, defval: str | None = None) -> str:
        """Получить значение поля k секции id как обычную строку (str).
        Кидает исключение, если указанной секции не существует.
        В остальном, см. :func:`Section.get_string`.
        """
        return self.section(id).get_string(k, defval)

    def get_string_wb(self, id: str, k: str, defval: str | None = None) -> str:
        """Получить значение поля k секции id как обычную строку (str),
        но с обрезанными по краям кавычками.
        Кидает исключение, если указанной секции не существует.
        В остальном, см. :func:`Section.get_string_wb`.
        """
        return self.section(id).get_string_wb(k, defval)

    def get_float(self, id: str, k: str, defval: float | None = None) -> float:
        """Получить значение поля k секции id как число c плавающей точкой (float).
        Кидает исключение, если указанной секции не существует.
        В остальном, см. :func:`Section.get_float`.
        """
        return self.section(id).get_float(k, defval)

    def get_int(self, id: str, k: str, defval: int | None = None) -> int:
        """Получить значение поля k секции id как целое число (int).
        Кидает исключение, если указанной секции не существует.
        В остальном, см. :func:`Section.get_int`.
        """
        return self.section(id).get_int(k, defval)

    def get_uint(self, id: str, k: str, defval: int | None = None) -> int:
        """Получить значение поля k секции id как неотрицательное целое число.
        Кидает исключение, если указанной секции не существует.
        В остальном, см. :func:`Section.get_uint`.
        """
        return self.section(id).get_uint(k, defval)

    def get_bool(self, id: str, k: str, defval: bool | None = None) -> bool:
        """Получить значение поля k секции id как bool.
        Кидает исключение, если указанной секции не существует.
        В остальном, см. :func:`Section.get_bool`.
        """
        return self.section(id).get_bool(k, defval)


    def get_strings(self, id: str, k: str, mandatory: bool = True) -> list[str]:
        """Получить значение поля k секции id как список из обычных строк.
        Кидает исключение, если указанной секции не существует.
        В остальном, см. :func:`Section.get_strings`.
        """
        return self.section(id).get_strings(k, mandatory)

    def get_floats(self, id: str, k: str, mandatory: bool = True) -> list[float]:
        """Получить значение поля k секции id как список из чисел с плавающей точкой.
        Кидает исключение, если указанной секции не существует.
        В остальном, см. :func:`Section.get_floats`.
        """
        return self.section(id).get_floats(k, mandatory)

    def get_ints(self, id: str, k: str, mandatory: bool = True) -> list[int]:
        """Получить значение поля k секции id как список из целых чисел.
        Кидает исключение, если указанной секции не существует.
        В остальном, см. :func:`Section.get_ints`.
        """
        return self.section(id).get_ints(k, mandatory)

    def get_uints(self, id: str, k: str, mandatory: bool = True) -> list[int]:
        """Получить значение поля k секции id как список из неотрицательных целых чисел.
        Кидает исключение, если указанной секции не существует.
        В остальном, см. :func:`Section.get_uints`.
        """
        return self.section(id).get_uints(k, mandatory)

    def get_bools(self, id: str, k: str, mandatory: bool = True) -> list[bool]:
        """Получить значение поля k секции id как список из bool.
        Кидает исключение, если указанной секции не существует.
        В остальном, см. :func:`Section.get_bools`.
        """
        return self.section(id).get_bools(k, mandatory)


    def get_items(
            self,
            id: str,
            k: str,
            mandatory: bool = True,
            parsing_mode: Literal["comma", "vanilla", "vanilla_ext"] = "comma"
    ) -> list[tuple[str, int]]:
        """Парсит строку вида
        ``<section>,<count>,<section>,<section>,...``
        в список пар ``(<section>, <count>)``.
        Кидает исключение, если указанной секции не существует.
        В остальном, см. :func:`Section.get_items`.
        """
        return self.section(id).get_items(k, mandatory, parsing_mode)
