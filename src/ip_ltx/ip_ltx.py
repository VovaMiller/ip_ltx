"""Базовые классы для работы с ltx-файлами.

* class Section
* class Ini
"""

import itertools
import re
from collections.abc import Callable
from pathlib import Path
from typing import Self, TextIO

from .utils import cast_safe, print_warning, read_file


class Section:
    """Класс одной секции ltx-файла.
    
    :param id: Идентификатор секции.
    :param init: Другая секция, по которой можно инициализировать поля.
    :param _src: Имя файла-источника (откуда будет считана секция).
        Используется при логировании и в сообщениях об ошибках.
    """
    id: str
    _fields: dict[str, str | None]
    _src: str

    def __init__(self, id: str, init: Self | None = None, _src: str = ""):
        self.id = id
        if init is None:
            self._fields = {}
            self._src = _src
        else:
            self._fields = init._fields.copy()
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

    def _raise(self, msg: str):
        raise Section.Error(self._src, self.id, msg)


    def overwrite(self, sect: Self) -> None:
        """Наследование полей от указанной секции с перезаписью собственных.
        """
        for k, v in sect._fields.items():
            self._fields[k] = v

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


    def add(
            self,
            field: str,
            value: str | None,
            overwrite: bool = False
    ) -> None:
        """Добавить поле с указанным значение.

        :param field: Имя поля.
        :param value: Значение поля.
        :param overwrite: Можно ли перезаписать уже существующее поле.
        :raises Section.Error: если поле уже существует, а ``overwrite == False``.
        :raises ValueError: если дан неверный формат имени поля или значения.
        """
        if type(field) != str:
            raise ValueError("Field must be string")
        if (type(value) != str) and (value is not None):
            raise ValueError("Field value must be string or None")
        if not overwrite and self.line_exist(field):
            self._raise(f"Field '{field}' already exists")
        if len(field) == 0:
            raise ValueError("Field name can't be empty")
        if ("\n" in field) or ("\r" in field):
            raise ValueError("Field name can't be multi-line")
        self._fields[field] = value


    @staticmethod
    def r_float(v: str) -> float | None:
        return cast_safe(v, float, defval=None)
    
    @staticmethod
    def r_int(v: str) -> int | None:
        return cast_safe(v, int, defval=None)

    @staticmethod
    def r_uint(v: str) -> int | None:
        return int(v) if v.isdecimal() else None
    
    @staticmethod
    def r_bool(v: str) -> bool | None:
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

    def get_float(self, k: str, defval: float | None = None) -> float:
        """Получить значение поля k как число с плавающей точкой (float).
        О деталях работы, см. :func:`get_elem`.
        """
        return self.get_elem(Section.r_float, "float", k, defval)

    def get_int(self, k: str, defval: int | None = None) -> int:
        """Получить значение поля k как целое число (int).
        О деталях работы, см. :func:`get_elem`.
        """
        return self.get_elem(Section.r_int, "int", k, defval)
    
    def get_uint(self, k: str, defval: int | None = None) -> int:
        """Получить значение поля k как неотрицательное целое число.
        О деталях работы, см. :func:`get_elem`.
        """
        return self.get_elem(Section.r_uint, "uint", k, defval)
    
    def get_bool(self, k: str, defval: bool | None = None) -> bool:
        """Получить значение поля k как bool.
        О деталях работы, см. :func:`get_elem`.
        """
        return self.get_elem(Section.r_bool, "bool", k, defval)


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
            либо пустоый список, если ``mandatory == False``
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
        return self.get_elems(Section.r_float, "float", k, mandatory)

    def get_ints(self, k: str, mandatory: bool = True) -> list[int]:
        """Получить значение поля k как список из целых чисел.
        О деталях работы, см. :func:`get_elems`.
        """
        return self.get_elems(Section.r_int, "int", k, mandatory)

    def get_uints(self, k: str, mandatory: bool = True) -> list[int]:
        """Получить значение поля k как список из неотрицательных целых чисел.
        О деталях работы, см. :func:`get_elems`.
        """
        return self.get_elems(Section.r_uint, "uint", k, mandatory)

    def get_bools(self, k: str, mandatory: bool = True) -> list[bool]:
        """Получить значение поля k как список из bool.
        О деталях работы, см. :func:`get_elems`.
        """
        return self.get_elems(Section.r_bool, "bool", k, mandatory)


    def get_items(
            self,
            k: str,
            mandatory: bool = True
    ) -> list[tuple[str, int]]:
        """Парсит строку вида
        ``<section>,<count>,<section>,<section>,...``
        в список пар ``(<section>, <count>)``.

        Аналог LUA-функции ``xr_box.r_items``.

        :param k: Имя поля, значение которого нужно считать.
        :param mandatory: Определяет поведение функции в случае,
            когда поля нет или оно без значения:
            
            * ``mandatory=True``: выдаст исключение
            * ``mandatory=False``: вернёт пустой список
        
        :raises Section.Error: если поля нет или оно без значения,
            и при этом ``mandatory=True``.
        :return: Список пар ``(<section>, <count>)``.
        """
        r = self._fields.get(k, None)
        if r is not None:
            r = str(r)
            if len(r) == 0:
                return []
            t = [vv.strip() for vv in r.split(",")]
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


# ----------------------------------------------------------------


class Ini:
    """Класс, считывающий ltx-файл(ы).
    
    Аналог LUA-класса ``ini_file`` (``CScriptIniFile``) и движкового ``CInifile``.

    Отличия от ``CInifile`` (X-Ray Engine):

    * Сохранён порядок определения секций и их полей.
    * Поле без значения и поле с пустым значением различаются между собой.

    :param ini_meta: Экземпляр этого же класса с настройками путей папок gamedata.
        Эти настройки полезны для последующего чтения файлов из gamedata.
        Пути указываются в секции ``[settings]``:

            * ``gamedata_path_mod`` - путь до папки gamedata мода.
            * ``gamedata_path_original`` - путь до папки gamedata
              с ресурсами оригинальной игры;
              необходимо, если не все используемые
              игрой файлы есть в gamedata мода.

    :param _name: Имя экземпляра класса. Используется при выводе ошибок.

    :raises Ini.Error: при ошибке инициализации.
    """
    _s: dict[str, Section]
    _name: str
    gdp_m: str | None
    gdp_o: str | None

    class Error(Exception):
        """Исключение, вызываемое классом :class:`Ini`."""
        pass

    def __init__(self, _name: str = "", ini_meta: Self | None = None):
        self._s = {}
        self._name = _name
        self.gdp_m = None
        self.gdp_o = None
        if ini_meta is not None:
            if not ini_meta.section_exist("settings"):
                raise Ini.Error("ini_meta doesn't have mandatory section [settings]")
            self.gdp_m = ini_meta.get_string("settings", "gamedata_path_mod", "")
            if len(self.gdp_m) > 0:
                self.gdp_m = str(Path(self.gdp_m).resolve())
            else:
                raise Ini.Error((
                    "ini_meta: 'gamedata_path_mod' must be provided"
                    " in section [settings]"
                ))
            self.gdp_o = ini_meta.get_string("settings", "gamedata_path_original", "")
            if len(self.gdp_o) > 0:
                self.gdp_o = str(Path(self.gdp_o).resolve())
            else:
                self.gdp_o = None

    def _raise(self, msg: str):
        raise Ini.Error(
            f"{self._name} | {msg}" if len(self._name) > 0 else msg
        )


    def read_raw(
            self,
            raw: str,
            fp_src: str = "",
            _current_section: Section | None = None
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
        :raises Ini.Error: при ошибке считывания.
        """
        custom_data_buffer: str | None = None
        for i, line0 in enumerate(raw.splitlines()):
            # Clearing the line.
            if (res := re.match(r"^([^;]*)", line0)):
                line = res.group(0).strip()
            else:
                self._raise(f"Error occurred while clearing the line ({fp_src}:{i+1})")

            # Custom data processing.
            if custom_data_buffer is not None:
                assert _current_section is not None, (
                    "custom_data_buffer exists, but there is no current_section"
                )
                if (line == "END"):
                    _current_section._fields["custom_data"] = custom_data_buffer
                    custom_data_buffer = None
                else:
                    custom_data_buffer += f"{line}\n"
                continue

            # Ignore empty lines.
            if len(line) == 0:
                continue

            # "#include" support
            if (res := re.match(r"\#include\s+\"([^\"]+)\"", line)):
                if len(fp_src) == 0:
                    self._raise(
                        "read_raw has found #include, but source file path is unknown!"
                    )

                # Получение абсолютного пути базовой директории.
                dir_base = str(Path(fp_src).parent.resolve())

                # Если это внутри оригинальной gamedata,
                #  то нужно перепрыгнуть в gamedata мода.
                if (self.gdp_o is not None) and (self.gdp_m is not None):
                    dir_gdo = str(Path(self.gdp_o).resolve())
                    if dir_base.startswith(dir_gdo):
                        dir_base = str(
                            Path(self.gdp_m).joinpath(Path(dir_base[len(dir_gdo)+1:]))
                        )

                # Путь до файла, который нужно включить.
                p_inc = Path(dir_base).joinpath(Path(res.group(1))).resolve()
                fp_inc = str(p_inc)

                # Если файла нет, а его путь внутри gamedata мода,
                #  то пробуем найти его в папке оригинальной gamedata.
                if (
                    not p_inc.is_file()
                    and (self.gdp_o is not None)
                    and (self.gdp_m is not None)
                ):
                    dir_gdm = str(Path(self.gdp_m).resolve())
                    if fp_inc.startswith(dir_gdm):
                        p_inc = (
                            Path(self.gdp_o)
                            .joinpath(Path(fp_inc[len(dir_gdm)+1:]))
                            .resolve()
                        )
                        fp_inc = str(p_inc)

                # Если файла всё равно нет, то приплыли.
                if not p_inc.is_file():
                    # Определяем, шёл ли путь в какую-либо gamedata.
                    inside_gamedata = False
                    fp_inc_fmt = fp_inc
                    if self.gdp_m is not None:
                        dir_gdm = str(Path(self.gdp_m).resolve())
                        if fp_inc.startswith(dir_gdm):
                            inside_gamedata = True
                            fp_inc_fmt = fp_inc[len(dir_gdm)+1:]
                    if self.gdp_o is not None:
                        dir_gdo = str(Path(self.gdp_o).resolve())
                        if fp_inc.startswith(dir_gdo):
                            inside_gamedata = True
                            fp_inc_fmt = fp_inc[len(dir_gdo)+1:]
                    if inside_gamedata:
                        self._raise((
                            f"#include error: gamedata doesn't have this file"
                            f" (\"{fp_inc_fmt}\")"
                        ))
                    else:
                        self._raise(
                            f"#include error: file doesn't exist (\"{fp_inc_fmt}\")"
                        )

                raw = read_file(fp_inc)
                self.read_raw(raw, fp_src=fp_inc, _current_section=_current_section)
                continue

            # Имя файла-иточника.
            fn_src = Path(fp_src).name if (len(fp_src) > 0) else ""

            # New section
            if (res := re.match(r"^\[([\w@.-]+)\]$", line)):
                id0 = res.group(1).lower()
                if id0 in self._s:
                    self._raise(f"Duplicate section id [{id0}] ({fp_src}:{i+1})")
                self._s[id0] = Section(id0, _src=fn_src)
                _current_section = self._s[id0]
                continue

            # New section with inheritance.
            if (res := re.match(r"^\[([\w@.-]+)\]:(.+)$", line)):
                id0 = res.group(1).lower()
                if id0 in self._s:
                    self._raise(f"Duplicate section id [{id0}] ({fp_src}:{i+1})")
                parents = [parent.strip().lower() for parent in res.group(2).split(",")]
                if len(parents) == 0:
                    self._raise(f"No parents specified [{id0}] ({fp_src}:{i+1})")
                sect0 = Section(id0, _src=fn_src)
                for parent in parents:
                    ps = self._s.get(parent, None)
                    if ps is None:
                        self._raise(f"Unknown section [{parent}] ({fp_src}:{i+1})")
                    sect0.overwrite(ps)
                self._s[id0] = sect0
                _current_section = self._s[id0]
                continue

            # Section fields.
            if _current_section is not None:
                if (res := re.match(r"^(\S*)\s*=\s*(.*)$", line)):
                    lv, rv = res.group(1), res.group(2)
                    if (lv == "custom_data") and (rv == "<<END"):
                        custom_data_buffer = ""
                        _current_section._fields[lv] = ""
                    else:
                        _current_section._fields[lv] = rv
                else:
                    _current_section._fields[line] = None
            else:
                self._raise(f"Redundant text [{fp_src}:{i+1}]")

    def read(
            self,
            fp0: str,
            inside_gamedata: bool = False
    ) -> None:
        """Считать данные с файла.

        :param fp0: Путь до файла.
        :param inside_gamedata: Если True, то интерпретирует путь до файла
            как указанный относительно папки gamedata.
            В первую очередь ищет файл в gamedata мода;
            если его там нет, то пробует gamedata оригинала.
        :raises Ini.Error: при ошибке считывания.
        """
        fp = None
        if inside_gamedata:
            if self.gdp_m is None:
                self._raise("gamedata path is not specified")
            p = Path(self.gdp_m).joinpath(fp0).resolve()
            if p.is_file():
                fp = str(p)
            elif self.gdp_o is not None:
                p = Path(self.gdp_o).joinpath(fp0).resolve()
                if p.is_file():
                    fp = str(p)
            if fp is None:
                self._raise(f"gamedata doesn't have this file (\"{fp0}\")")
        else:
            if Path(fp0).is_file():
                fp = fp0
            if fp is None:
                self._raise(f"FILE DOES NOT EXIST (\"{fp}\")")
        raw = read_file(fp)
        self.read_raw(raw, fp_src=fp)

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


    def clear(self):
        self._s.clear()

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
            mandatory: bool = True
    ) -> list[tuple[str, int]]:
        """Парсит строку вида
        ``<section>,<count>,<section>,<section>,...``
        в список пар ``(<section>, <count>)``.
        Кидает исключение, если указанной секции не существует.
        В остальном, см. :func:`Section.get_items`.
        """
        return self.section(id).get_items(k, mandatory)
