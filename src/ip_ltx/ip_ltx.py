import re
import os.path
from collections import OrderedDict
from pathlib import Path
from typing import Self

from utils import print_error, cast_safe


__VERSION__ = "2.1 (2026-02-01)"
# __VERSION__ = "2.0.1 (2025-06-22)"
# __VERSION__ = "2.0 (2025-06-18)"
# __VERSION__ = "1.4 (20250611)"
# __VERSION__ = "1.3.1 (20220124)"
# __VERSION__ = "1.2 (20210820)"

# ----------------------------------------------------------------

class Section:
    """ Класс одной секции ltx-файла.

        * Section::line_exist(field)
        * Section::get_string(field, defval=None)
        * Section::get_strings(field, mandatory=True)
        * Section::get_uint(field, defval=None)
        * Section::get_number(field, defval=None)
        * Section::get_numbers(field, mandatory=True)
        * Section::get_bool(field, defval=None)
        * Section::get_items(field, mandatory=True)
    """
    id: str
    _fields: OrderedDict[str, str | None]
    _src: str

    def __init__(self, id: str, init: Self | None = None, _src: str = ""):
        """ @arg id: str
                * id секции
            @arg init: Section
                * Если указан, то используется для инициализации полей.
            @arg _src: str
                * Имя файла-источника (откуда будет считана секция).
        """
        self.id = id
        if init is None:
            self._fields = OrderedDict()
            self._src = _src
        else:
            self._fields = init._fields.copy()
            self._src = _src if (len(_src) > 0) else init._src

    def _exception(self, msg: str):
        msg_ext = f"{self._src} | {msg}" if len(self._src) > 0 else msg
        # print_error(msg_ext)
        raise Exception(msg_ext)

    def overwrite(self, sect: Self):
        """ Записывает поверх поля секции sect.
        """
        for k, v in sect._fields.items():
            self._fields[k] = v


    def field(self, k: str) -> str | None:
        if k not in self._fields:
            self._exception("section [{}] doesn't have field '{}'".format(self.id, k))
        return self._fields[k]

    def lines(self):
        return self._fields.keys()

    def fields(self):
        return self._fields.items()


    def line_exist(self, k: str) -> bool:
        return (k in self._fields)

    def get_string(self, k: str, defval: str | None = None) -> str:
        """ Получить значение поля k как string.
            Если поля нет, или оно без значения, то:
                - defval is None: выдаст Exception
                - defval is not None: вернёт defval
        """
        r = self._fields.get(k, None)
        if r is not None:
            return str(r)
        if defval is None:
            reason = "None value" if (k in self._fields) else "non-existent field"
            self._exception("[{}]::{} can't be read as <string> ({})".format(self.id, k, reason))
        return defval

    def get_strings(self, k: str, mandatory: bool = True) -> list[str]:
        """ Получить значение поля k как список из string.
            Подразумевается, что каждая строка разделена запятой.
            Если поля нет, или оно без значения, то:
                - mandatory=True: выдаст Exception
                - mandatory=False: вернёт пустой список
        """
        r = self._fields.get(k, None)
        if r is not None:
            r = str(r)
            if len(r) == 0:
                return []
            return [vv.strip() for vv in r.split(",")]
        if mandatory:
            self._exception("[{}]::{} can't be read as a list of strings ({})".format(
                self.id, k,
                "None value" if (k in self._fields) else "non-existent field"
            ))
        return []

    def get_uint(self, k: str, defval: int | None = None) -> int:
        """ Получить значение поля k как неотрицательное целое число.
            Если поля нет, или оно без значения, то:
                - defval is None: выдаст Exception
                - defval is not None: вернёт defval
            Если конвертация значения невозможна, то выдаёт Exception.
        """
        r = self._fields.get(k, None)
        if r is not None:
            r = str(r)
            if r.isdigit():
                return int(r)
            self._exception("[{}]::{} can't be read as <uint>".format(self.id, k))
        if defval is None:
            reason = "None value" if (k in self._fields) else "non-existent field"
            self._exception("[{}]::{} can't be read as <uint> ({})".format(self.id, k, reason))
        return defval

    def get_number(self, k: str, defval: int | float | None = None) -> int | float:
        """ Получить значение поля k как число.
            Если указано целое число, то вернёт int.
            В противном случае вернёт float.
            Если конвертация значения невозможна, то выдаёт Exception.
            Если поля нет, или оно без значения, то:
                - defval is None: выдаст Exception
                - defval is not None: вернёт defval
        """
        r = self._fields.get(k, None)
        if r is not None:
            r = str(r)
            r = cast_safe(r, int, cast_safe(r, float))
            if r is not None:
                return r
            self._exception("[{}]::{} can't be read as a number".format(self.id, k))
        if defval is None:
            reason = "None value" if (k in self._fields) else "non-existent field"
            self._exception("[{}]::{} can't be read as a number ({})".format(self.id, k, reason))
        return defval

    def get_numbers(self, k: str, mandatory: bool = True) -> list[int | float]:
        """ Получить значение поля k как список из чисел.
            Каждое число - float (или int, где это возможно).
            Подразумевается, что числа разделены запятой.
            Если конвертация хотя бы одного числа невозможна,
              то выдаёт Exception.
            Если поля нет, или оно без значения, то:
                - mandatory=True: выдаст Exception
                - mandatory=False: вернёт пустой список
        """
        r = self._fields.get(k, None)
        if r is not None:
            r = str(r)
            nums = []
            if len(r) == 0:
                return nums
            for i, s in enumerate([vv.strip() for vv in r.split(",")]):
                num = cast_safe(s, int, cast_safe(s, float))
                if num is None:
                    self._exception("[{}]::{} can't be read as a list of numbers ({})".format(
                        self.id, k,
                        "value #{} is not a number".format(i+1)
                    ))
                nums.append(num)
            return nums
        if mandatory:
            self._exception("[{}]::{} can't be read as a list of numbers ({})".format(
                self.id, k,
                "None value" if (k in self._fields) else "non-existent field"
            ))
        return []

    def get_bool(self, k: str, defval: bool | None = None) -> bool:
        """ Получить значение поля k как boolean.
            Если конвертация значения невозможна, то выдаёт Exception.
            Если поля нет, или оно без значения, то:
                - defval is None: выдаст Exception
                - defval is not None: вернёт defval
        """
        r = self._fields.get(k, None)
        if r is not None:
            r = str(r).strip().lower()
            if r in ["on", "yes", "true", "1"]:
                return True
            if r in ["off", "no", "false", "0"]:
                return False
            self._exception("[{}]::{} can't be read as <bool>".format(self.id, k))
        if defval is None:
            reason = "None value" if (k in self._fields) else "non-existent field"
            self._exception("[{}]::{} can't be read as <bool> ({})".format(self.id, k, reason))
        return defval

    def get_items(self, k: str, mandatory: bool = True) -> list[tuple[str, int]]:
        """ Парсит строку вида "<section>,<count>,<section>,<section>,..."
              в список пар (<section>, <count>).
            Аналог LUA-функции xr_box.r_items
            Если поля нет, или оно без значения, то:
                - mandatory=True: выдаст Exception
                - mandatory=False: вернёт пустой список
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
            self._exception("[{}]::{} can't be read ({})".format(
                self.id, k,
                "None value" if (k in self._fields) else "non-existent field"
            ))
        return []


# ----------------------------------------------------------------


class Ini:
    """ Класс, считывающий ltx-файл.
        Аналог LUA-класса ini_file (CScriptIniFile).

        * Ini::section_exist(section)
        * Ini::line_exist(section, field)
        * Ini::get_string(section, field, defval=None)
        * Ini::get_strings(section, field, mandatory=True)
        * Ini::get_uint(section, field, defval=None)
        * Ini::get_number(section, field, defval=None)
        * Ini::get_numbers(section, field, mandatory=True)
        * Ini::get_bool(section, field, defval=None)
        * Ini::get_items(section, field, mandatory=True)
    """
    s: OrderedDict[str, Section]
    _name: str
    gdp_m: str | None
    gdp_o: str | None

    def __init__(self, _name: str = "", ini_meta: Self | None = None):
        """ Инициализация.

            @arg ini_meta: Ini
                * Экземпляр этого же класса с настройками путей папок gamedata.
                * Эти настройки полезны для последующего чтения ltx файлов из gamedata.
                * Пути указываются в секции [settings]
                    * gamedata_path_mod - путь до папки gamedata мода.
                    * gamedata_path_original - путь до папки gamedata с ресурсами оригинальной игры;
                      необходимо, если не все используемые игрой файлы есть в gamedata мода.
            @arg _name: str
                * Имя экземпляра класса.
                * Используется при выводе ошибок.
        """
        self.s = OrderedDict()
        self._name = _name
        self.gdp_m = None
        self.gdp_o = None
        if ini_meta is not None:
            if not ini_meta.section_exist("settings"):
                raise Exception("ini_meta doesn't have mandatory section [settings]")
            self.gdp_m = ini_meta.get_string("settings", "gamedata_path_mod", "")
            if len(self.gdp_m) > 0:
                self.gdp_m = str(Path(self.gdp_m).resolve())
            else:
                raise Exception("ini_meta: 'gamedata_path_mod' must be provided in section [settings]")
            self.gdp_o = ini_meta.get_string("settings", "gamedata_path_original", "")
            if len(self.gdp_o) > 0:
                self.gdp_o = str(Path(self.gdp_o).resolve())
            else:
                self.gdp_o = None


    def _exception(self, msg: str):
        msg_ext = f"{self._name} | {msg}" if len(self._name) > 0 else msg
        print_error(msg_ext)
        raise Exception(msg_ext)


    def read_raw(self, raw: str, fp_src: str = ""):
        """ Считать данные с текста.

            @arg raw: str
                * Текст с данными.
            @arg fp_src: str
                * Путь к файлу, откуда взят текст.
                * Необходимо для поддержки #include,
                  а также для поддержки Section::_src.
        """
        custom_data_buffer: str | None = None
        for i, line0 in enumerate(raw.splitlines()):
            # Clearing the line.
            res = re.match(r"^([^;]*)", line0)
            if res is None:
                self._exception("Error occurred while clearing the line [{}:{}]".format(fp_src, i+1))
            line = res.group(0).strip()

            # Custom data processing.
            if custom_data_buffer is not None:
                if (line == "END"):
                    next(reversed(self.s.values()))._fields["custom_data"] = custom_data_buffer
                    custom_data_buffer = None
                else:
                    custom_data_buffer += "{}\n".format(line)
                continue

            # Ignore empty lines.
            if len(line) == 0:
                continue

            # "#include" support
            res = re.match(r"\#include\s+\"([^\"]+)\"", line)
            if res is not None:
                if len(fp_src) == 0:
                    self._exception("read_raw has found #include, but source file path is unknown!")

                # Получение абсолютного пути базовой директории.
                dir_base = str(Path(fp_src).parent.resolve())

                # Если это внутри оригинальной gamedata, то нужно перепрыгнуть в gamedata мода.
                if (self.gdp_o is not None) and (self.gdp_m is not None):
                    dir_gdo = str(Path(self.gdp_o).resolve())
                    if dir_base.startswith(dir_gdo):
                        dir_base = str(Path(self.gdp_m).joinpath(Path(dir_base[len(dir_gdo)+1:])))

                # Путь до файла, который нужно включить.
                p_inc = Path(dir_base).joinpath(Path(res.group(1))).resolve()
                fp_inc = str(p_inc)

                # Если файла нет, а его путь внутри gamedata мода,
                #  то пробуем найти его в папке оригинальной gamedata.
                if not p_inc.is_file() and (self.gdp_o is not None) and (self.gdp_m is not None):
                    dir_gdm = str(Path(self.gdp_m).resolve())
                    if fp_inc.startswith(dir_gdm):
                        p_inc = Path(self.gdp_o).joinpath(Path(fp_inc[len(dir_gdm)+1:])).resolve()
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
                        self._exception((
                            "#include error: gamedata doesn't have this file (\"{}\")"
                        ).format(fp_inc_fmt))
                    else:
                        self._exception((
                            "#include error: file doesn't exist (\"{}\")"
                        ).format(fp_inc_fmt))

                raw = ""
                try:
                    with open(fp_inc, "r", encoding=None) as f:
                        raw = f.read()
                except UnicodeDecodeError:
                    with open(fp_inc, "r", encoding="utf-8") as f:
                        raw = f.read()
                self.read_raw(raw, fp_src=fp_inc)
                continue

            # Имя файла-иточника.
            fn_src = os.path.basename(fp_src) if (len(fp_src) > 0) else ""

            # New section
            res = re.match(r"^\[([\w@.-]+)\]$", line)
            if res is not None:
                id0 = res.group(1).lower()
                if self.s.get(id0, None) is not None:
                    self._exception("Duplicate section id ({}) found [{}:{}]".format(id0, fp_src, i+1))
                self.s[id0] = Section(id0, _src=fn_src)
                continue

            # New section with inheritance.
            res = re.match(r"^\[([\w@.-]+)\]:(.+)$", line)
            if res is not None:
                id0 = res.group(1).lower()
                if self.s.get(id0, None) is not None:
                    self._exception("Duplicate section id ({}) found [{}:{}]".format(id0, fp_src, i+1))
                parents = [parent.strip().lower() for parent in res.group(2).split(",")]
                if len(parents) == 0:
                    self._exception("No parents specified ({}) [{}:{}]".format(id0, fp_src, i+1))
                sect0 = Section(id0, _src=fn_src)
                for parent in parents:
                    ps = self.s.get(parent, None)
                    if ps is None:
                        self._exception("No section with id ({}) was found [{}:{}]".format(parent, fp_src, i+1))
                    sect0.overwrite(ps)
                self.s[id0] = sect0
                continue

            # Section fields.
            if len(self.s) == 0:
                self._exception("Redundant text [{}:{}]".format(fp_src, i+1))
            res = re.match(r"^(\S*)\s*=\s*(.*)$", line)
            if res is not None:
                lv, rv = res.group(1), res.group(2)
                if (lv == "custom_data") and (rv == "<<END"):
                    custom_data_buffer = ""
                    next(reversed(self.s.values()))._fields[lv] = ""
                else:
                    next(reversed(self.s.values()))._fields[lv] = rv
            else:
                next(reversed(self.s.values()))._fields[line] = None

    def read(self, fp0: str, inside_gamedata: bool = False, encoding: str | None = "utf-8"):
        """ Считать данные с файла.

            @arg fp0: str
                * Путь до файла.
            @arg inside_gamedata: bool
                * Если True, то интерпретирует путь до файла
                  как указанный относительно папки gamedata.
                * В первую очередь ищет файл в gamedata мода;
                  если его там нет, то пробует gamedata оригинала.
            @arg encoding: str
                * Кодировка файла.
                * Иногда для избежания ошибки при чтении
                  необходимо установить encoding=None.
        """
        fp = None
        if inside_gamedata:
            if self.gdp_m is None:
                self._exception("gamedata path is not specified")
            p = Path(self.gdp_m).joinpath(fp0).resolve()
            if p.is_file():
                fp = str(p)
            elif self.gdp_o is not None:
                p = Path(self.gdp_o).joinpath(fp0).resolve()
                if p.is_file():
                    fp = str(p)
            if fp is None:
                self._exception("gamedata doesn't have this file (\"{}\")".format(fp0))
        else:
            if os.path.exists(fp0):
                fp = fp0
            if fp is None:
                self._exception("FILE DOES NOT EXIST (\"{}\")".format(fp))
        raw = ""
        with open(fp, "r", encoding=encoding) as f:
            raw = f.read()
        self.read_raw(raw, fp_src=fp)

    def _write_field(self, file, sect, f, vnone, override, override_id):
        v = sect._fields.get(f, None)
        if v is None:
            return
        if (vnone is not None) and (v == vnone):
            v = sect._fields.get(override.get(f, f), v)
        if (vnone is not None) and (v == vnone):
            if override_id.get(f, None) is not None:
                v = sect.id
        if (vnone is not None) and (v == vnone):
            self._exception("None value in section [{}]".format(sect.id))
        if v is None:
            file.write("{}\n".format(f))
        elif f == "custom_data":
            file.write("custom_data = <<END\n")
            if (len(v) > 0) and (v[-1] == '\n'):
                file.write(v)
            else:
                file.write("{}\n".format(v))
            file.write("END\n")
        else:
            file.write("{} = {}\n".format(f, v))

    def _write_section(self, file, sect, order, vnone, override, override_id):
        # Header.
        file.write("[{}]\n".format(sect.id))

        # Writing the first fields.
        done_fields = {}  # remembering already written fields
        if order is not None:
            for f in order:
                self._write_field(file, sect, f, vnone, override, override_id)
                done_fields[f] = True

        # Writing the other fields.
        for f in sect._fields:
            if not done_fields.get(f, False):
                self._write_field(file, sect, f, vnone, override, override_id)
                done_fields[f] = True

        # Trailing newline.
        file.write("\n")

    def write(self, fp, mask=None, order=None, vnone=None, override=None, override_id=None):
        """
            fp
                Путь до файла для вывода секций.
            mask
                Маска имени секции для фильтрации множества выводимых секций.
                Если None, то выводятся все секции.
            order
                Список полей, которые будут выведены в первую очередь.
                Если None, то идентично пустому списку.
            vnone
                Значение поля, условно считающееся незаполненным.
                Поля выводимой секции не могут быть незаполненными.
                Если None, то любое поле считается заполненным.
            override
                Словарь замены значений.
                "f2": f1
                Если выписываемая секция имеет поля f1 и f2,
                  а поле f2 не заполнено (см. vnone),
                  то значение для f2 берётся из f1.
                Если None, то замен не производится.
            override_id
                Словарь замены значений.
                "f": whatever
                Если выписываемая секция имеет незаполненное поле f,
                  то её значением считается id секции.
                При коллизии с override сначала производит замену с ним.
                Если None, то замен не производится.
        """
        with open(fp, "w", encoding="utf-8") as file:
            for sect in self.s.values():
                # Filtering.
                if mask is not None:
                    if re.match(mask, sect.id) is None:
                        continue

                # Writing section.
                self._write_section(file, sect, order, vnone, override, override_id)

    def clear(self):
        self.s.clear()

    def section(self, id: str) -> Section:
        if id not in self.s:
            self._exception("section [{}] doesn't exist".format(id))
        return self.s[id]

    def ids(self):
        return self.s.keys()

    def sections(self):
        return self.s.values()
    
    def get_section_index(self, section_id: str) -> int:
        """ Получить порядковый номер секции с указанным id.
            Возвращает -1, если такой секции не существует.
        """
        return list(self.s.keys()).index(section_id) if (section_id in self.s) else -1


    def section_exist(self, id: str) -> bool:
        return (id in self.s)

    def line_exist(self, id: str, k: str) -> bool:
        if id not in self.s:
            self._exception("section '{}' doesn't exist".format(id))
        return (k in self.s[id]._fields)

    def get_string(self, id: str, k: str, defval: str | None = None) -> str:
        """ Получить значение поля k секции id как string.
            Выдаёт Exception, если указанной секции не существует.
            В остальном, см. описание Section::get_string
        """
        section = self.s.get(id, None)
        if section is None:
            self._exception("section '{}' doesn't exist".format(id))
        return section.get_string(k, defval)

    def get_strings(self, id: str, k: str, mandatory: bool = True) -> list[str]:
        """ Получить значение поля k секции id как список из string.
            Подразумевается, что каждая строка разделена запятой.
            Выдаёт Exception, если указанной секции не существует.
            В остальном, см. описание Section::get_strings
        """
        section = self.s.get(id, None)
        if section is None:
            self._exception("section '{}' doesn't exist".format(id))
        return section.get_strings(k, mandatory)

    def get_uint(self, id: str, k: str, defval: int | None = None) -> int:
        """ Получить значение поля k секции id как неотрицательное целое число.
            Выдаёт Exception, если указанной секции не существует.
            В остальном, см. описание Section::get_uint
        """
        section = self.s.get(id, None)
        if section is None:
            self._exception("section '{}' doesn't exist".format(id))
        return section.get_uint(k, defval)

    def get_number(self, id: str, k: str, defval: int | float | None = None) -> int | float:
        """ Получить значение поля k секции id как число.
            Выдаёт Exception, если указанной секции не существует.
            В остальном, см. описание Section::get_number
        """
        section = self.s.get(id, None)
        if section is None:
            self._exception("section '{}' doesn't exist".format(id))
        return section.get_number(k, defval)

    def get_numbers(self, id: str, k: str, mandatory: bool = True) -> list[int | float]:
        """ Получить значение поля k секции id как список из чисел.
            Каждое число - float (или int, где это возможно).
            Подразумевается, что числа разделены запятой.
            Выдаёт Exception, если указанной секции не существует.
            В остальном, см. описание Section::get_numbers
        """
        section = self.s.get(id, None)
        if section is None:
            self._exception("section '{}' doesn't exist".format(id))
        return section.get_numbers(k, mandatory)

    def get_bool(self, id: str, k: str, defval: bool | None = None) -> bool:
        """ Получить значение поля k секции id как boolean.
            Выдаёт Exception, если указанной секции не существует.
            В остальном, см. описание Section::get_bool
        """
        section = self.s.get(id, None)
        if section is None:
            self._exception("section '{}' doesn't exist".format(id))
        return section.get_bool(k, defval)

    def get_items(self, id: str, k: str, mandatory: bool = True) -> list[tuple[str, int]]:
        """ Парсит строку вида "<section>,<count>,<section>,<section>,..."
              в список пар (<section>, <count>).
            Выдаёт Exception, если указанной секции не существует.
            В остальном, см. описание Section::get_items
        """
        section = self.s.get(id, None)
        if section is None:
            self._exception("section '{}' doesn't exist".format(id))
        return section.get_items(k, mandatory)
