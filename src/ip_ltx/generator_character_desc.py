"""Генерация характеристик NPC"""

import re
import os.path
import traceback
import itertools
import random
from collections import Counter
from os import mkdir
from pathlib import Path, PureWindowsPath
from pathvalidate import is_valid_filename, is_valid_filepath
from typing import Callable, TextIO

from .ip_ltx import Ini, Section
from .ini import system_ini
from .xml_data.dialogs import Dialogs
from .xml_data.string_table import string_table
from .xml_data.texture_desc import TextureDesc
from .treasure_manager_ext import SpawnEntry
from .utils import (
    ANSI_COLOR_CODE,
    cast_safe,
    is_gamedata_dir,
    is_gamedata_file,
    preinit_singletons,
    print_error,
    print_warning,
    validate_data,
)

# ----------------------------------------------------------------

class CharacterDefaults:
    """Набор методов для получения параметров характеристики по умолчанию."""

    @staticmethod
    def get_name(community: str, rank: int) -> str:
        match community, rank:
            case "bandit", _:
                return "GENERATE_NAME_bandit"
            case "ecolog", _:
                return "GENERATE_NAME_science"
            case "military", r if r < 300:
                return "GENERATE_NAME_private"
            case "military", r if r < 600:
                return "GENERATE_NAME_sergeant"
            case "military", r if r < 900:
                return "GENERATE_NAME_lieutenant"
            case "military", _:
                return "GENERATE_NAME_captain"
            case _:
                return "GENERATE_NAME_stalker"
    
    @staticmethod
    def get_icon(community: str, visual: str) -> str:
        if community == "zombied":
            TD = TextureDesc()
            ICON_NONE = "ui_npc_u_none"
            if ICON_NONE in TD:
                return ICON_NONE
        return f"ui_npc_u_{Path(visual).stem}"

    @staticmethod
    def get_crouch_type(community: str) -> int:
        match community:
            case "stalker" | "monolith" | "zombied" | "killer" | "freedom" | "trader":
                return -1
            case "dolg" | "military" | "ipmil":
                return 0
            case "bandit" | "ecolog":
                return 1
        return -1

    @staticmethod
    def get_include_supplies() -> list[str]:
        return []

    @staticmethod
    def get_include() -> list[str]:
        return ["character_criticals", "character_dialogs"]

# ----------------------------------------------------------------

class Inspector:
    """Набор проверок указанных для характеристики данных на совместимость
    с ресурсами игры. Выявленные несоответствия лишь выводят предупреждение,
    причём не дублируют их при повторном вызове одной и той же проверки.
    """
    _name:          set[str] = set()
    _icon:          set[str] = set()
    _bio:           set[str] = set()
    _community:     set[str] = set()
    _terrain_sect:  set[str] = set()
    _visual:        set[str] = set()
    _snd_config:    set[str] = set()
    _include:       set[str] = set()
    _dialog:        set[str] = set()

    @staticmethod
    def name(v: str) -> None:
        if v not in Inspector._name:
            Inspector._name.add(v)
            GEN_PREFIX = "GENERATE_NAME_"
            if v.startswith(GEN_PREFIX):
                ini_system = system_ini()
                section_name = f"stalker_names_{v[len(GEN_PREFIX):]}"
                ok = False
                if ini_system.section_exist(section_name):
                    s = ini_system.section(section_name)
                    fn_cnt = cast_safe(s.get_string("name_cnt", ""), int, 0)
                    ln_cnt = cast_safe(s.get_string("last_name_cnt", ""), int, 0)
                    ok = (fn_cnt > 0) and (ln_cnt > 0)
                if not ok:
                    print_warning(f"<name> Generator '{v}' is not set up properly")
            else:
                ST = string_table()
                if v not in ST:
                    print_warning(f"<name> Not found: '{v}'")
    
    @staticmethod
    def icon(v: str) -> None:
        if v not in Inspector._icon:
            Inspector._icon.add(v)
            TD = TextureDesc()
            if v not in TD:
                print_warning(f"<icon> Not found: '{v}'")
    
    @staticmethod
    def bio(v: str | None) -> None:
        if (v is not None) and (v not in Inspector._bio):
            Inspector._bio.add(v)
            ST = string_table()
            if v not in ST:
                print_warning(f"<bio> Not found: '{v}'")

    @staticmethod
    def community(v: str) -> None:
        if v not in Inspector._community:
            Inspector._community.add(v)
            ini_system = system_ini()
            ok = False
            if ini_system.section_exist("game_relations"):
                cc = ini_system.get_strings(
                    "game_relations",
                    "communities",
                    mandatory=False
                )
                for i in range(0, len(cc), 2):
                    if cc[i] == v:
                        ok = True
                        break
            if not ok:
                print_warning(f"<community> Not found: '{v}'")

    @staticmethod
    def terrain_sect(v: str | None) -> None:
        if (v is not None) and (v not in Inspector._terrain_sect):
            Inspector._terrain_sect.add(v)
            if not system_ini().section_exist(v):
                print_warning(f"<terrain_sect> Not found: '{v}'")

    @staticmethod
    def visual(v: str) -> None:
        if v not in Inspector._visual:
            Inspector._visual.add(v)
            ini_system = system_ini()
            exists = is_gamedata_file(
                f"meshes\\{v}.ogf",
                gd_path_main=ini_system.gdp_m,
                gd_path_alt=ini_system.gdp_o
            )
            if not exists:
                print_warning(f"<visual> Not found: '{v}'")

    @staticmethod
    def snd_config(v: str | None) -> None:
        if (v is not None) and (v not in Inspector._snd_config):
            Inspector._snd_config.add(v)
            ini_system = system_ini()
            exists = is_gamedata_dir(
                f"sounds\\{v}",
                gd_path_main=ini_system.gdp_m,
                gd_path_alt=ini_system.gdp_o
            )
            if not exists:
                print_warning(f"<snd_config> Not found: '{v}'")

    @staticmethod
    def include(vv: list[str]) -> None:
        for v in vv:
            if v not in Inspector._include:
                Inspector._include.add(v)
                ini_system = system_ini()
                exists = is_gamedata_file(
                    f"config\\gameplay\\{v}.xml",
                    gd_path_main=ini_system.gdp_m,
                    gd_path_alt=ini_system.gdp_o
                )
                if not exists:
                    print_warning(f"#include: not found ({v})")
    
    @staticmethod
    def dialog(vv: list[str]) -> None:
        for v in vv:
            if v not in Inspector._dialog:
                Inspector._dialog.add(v)
                D = Dialogs()
                if v not in D:
                    print_warning(f"<*_dialog> Not found: '{v}'")

# ----------------------------------------------------------------

class Character:
    """Класс отдельной характеристики NPC."""

    _num:               int
    _unique:            bool
    name:               str
    icon:               str
    bio:                str | None
    cls:                str
    community:          str
    terrain_sect:       str | None
    rank:               int
    reputation:         int
    money_min:          int
    money_max:          int
    money_inf:          bool
    visual:             str
    snd_config:         str | None
    crouch_type:        int
    include_supplies:   list[str]
    include:            list[str]
    start_dialog:       list[str]
    actor_dialog:       list[str]
    spawn_items:        list[SpawnEntry]

    @staticmethod
    def get_id(unique: bool, cls: str, num: int) -> str:
        """Сформировать ID характеристики.

        :param unique: Является ли характеристика уникальной.
        :param cls: Класс характеристики.
        :param num: Порядковый номер характеристики.
        """
        if unique:
            return f"{cls}"
        else:
            return f"{cls}_default{num}"

    def write_xml(self, f: TextIO, tab: str = "\t") -> None:
        """Записать характеристику в файл в формате XML.

        :param f: Открытый для записи файл.
        :param tab: Отступ, используемый при выводе в файл.
        """
        id = Character.get_id(self._unique, self.cls, self._num)
        f.write((
            f"{tab*1}<specific_character id=\"{id}\" team_default=\"1\">\n"
        ))
        f.write(f"{tab*2}<name>{self.name}</name>\n")
        f.write(f"{tab*2}<icon>{self.icon}</icon>\n")
        if self.bio is not None:
            f.write(f"{tab*2}<bio>{self.bio}</bio>\n")
        f.write(f"{tab*2}<class>{self.cls}</class>\n")
        f.write(f"{tab*2}<community>{self.community}</community>")
        if (self.terrain_sect is None):
            f.write("\n")
        else:
            f.write(f" <terrain_sect>{self.terrain_sect}</terrain_sect>\n")
        if self.money_inf:
            f.write(
                f"{tab*2}<money min=\"100000\" max=\"110000\" infinitive=\"1\" />\n"
            )
        else:
            f.write((
                f"{tab*2}<money min=\"{self.money_min}\" max=\"{self.money_max}\""
                f" infinitive=\"0\" />\n"
            ))
        f.write(f"{tab*2}<rank>{self.rank}</rank>\n")
        f.write(f"{tab*2}<reputation>{self.reputation}</reputation>\n")
        f.write(f"{tab*2}<visual>{self.visual}</visual>\n")
        if self.snd_config is not None:
            f.write(f"{tab*2}<snd_config>{self.snd_config}</snd_config>\n")
        f.write(f"{tab*2}<crouch_type>{self.crouch_type}</crouch_type>\n")
        if (len(self.spawn_items) > 0) or (len(self.include_supplies) > 0):
            f.write(f"{tab*2}<supplies>\n")
            f.write(f"{tab*3}[spawn] \\n\n")
            for se in self.spawn_items:
                line = se.name
                params = se.get_params_str()
                if params != "1":
                    line = f"{se.name} = {params}"
                f.write(f"{tab*3}{line} \\n\n")
            for inc in self.include_supplies:
                f.write(f"#include \"gameplay\\{inc}.xml\"\n")
            f.write(f"{tab*2}</supplies>\n")
        for inc in self.include:
            f.write(f"#include \"gameplay\\{inc}.xml\"\n")
        if len(self.start_dialog) > 0:
            for dialog_id in self.start_dialog:
                f.write(f"{tab*2}<start_dialog>{dialog_id}</start_dialog>\n")
        if len(self.actor_dialog) > 0:
            for dialog_id in self.actor_dialog:
                f.write(f"{tab*2}<actor_dialog>{dialog_id}</actor_dialog>\n")
        f.write(f"{tab*1}</specific_character>\n")

# ----------------------------------------------------------------

class CharacterFactory:
    """Генератор характеристик(и) по заданной настройке.

    Описывается конфигурационной секцией в ltx-файле.
    Генерирует список экземпляров класса :class:`Character`.
    
    :param s: Секция, на базе которой осуществляется инициализация.
    :raises IncompleteError: если настройка неполная
        (например, когда не указан обязательный параметр).
    """

    class IncompleteError(Exception):
        """Вызывается при попытке инициализации по неполной или невалидной настройке."""
        pass
    class ItemsError(Exception):
        """Вызывается при ошибке считывания строки списка предметов."""
        pass
    class CharGenClsError(Exception):
        """Вызывается при ошибке генерации характеристики в связи с её классом."""
        pass
    class CharGenIdError(Exception):
        """Вызывается при ошибке генерации характеристики в связи с её ID."""
        pass

    chr_ids: set[str] = set()
    """Множество ID уже сгенерированных характеристик."""

    chr_cnt_by_cls: Counter[str] = Counter()
    """Кол-во уже сгенерированных характеристик по каждому классу."""

    gen_cnt_by_cls: Counter[str] = Counter()
    """Кол-во запущенных генераций по каждому классу."""

    unique_classes: set[str] = set()
    """Множество классов, занятых уникальной характеристикой."""

    _id:                str
    """ID секции с настройками, по которой была произведена инициализация."""

    builder:            Callable[[], list[Character]]
    """Функция-генератор характеристик."""

    name:               str | None
    icon:               str | None
    bio:                str | None
    cls:                str
    community:          str
    terrain_sect:       str | None
    rank:               tuple[int, int]
    reputation:         tuple[int, int]
    money:              tuple[int, int]
    money_inf:          bool
    visual:             str
    snd_config:         str | None
    crouch_type:        int | None
    w0:                 list[SpawnEntry | None]
    w1:                 list[SpawnEntry | None]
    w2:                 list[SpawnEntry | None]
    a0:                 list[SpawnEntry | None]
    a1:                 list[SpawnEntry | None]
    a2:                 list[SpawnEntry | None]
    items:              list[SpawnEntry | None]
    include_supplies:   list[str] | None
    include:            list[str] | None
    start_dialog:       list[str]
    actor_dialog:       list[str]

    def __init__(self, s: Section):
        def _err(msg: str) -> None:
            nonlocal _ok
            if _ok:
                print_error("", prefix=False, color=False)
                _ok = False
            print_error(f"[{s.id}] {msg}")
        
        def _read_range(
                tag: str,
                only_positive: bool,
                alias_parser: Callable[[str], tuple[int, int] | None]
        ) -> tuple[int, int] | None:
            """Вспомогательная функция для чтения поля, обозначающего
            целочисленные пределы "от" и "до". Такое поле состоит из одного
            или двух значений, являющихся или целым числом, или предопределённой
            строковой константой (alias).
            """
            try:
                rr_str = s.get_strings(tag, mandatory=True)
            except Section.Error as e:
                _err(f"<{tag}> {e.msg}")
                return None
            match len(rr_str):
                case 0:
                    _err(f"<{tag}> Empty field")
                    return None
                case 1:
                    rr_str = [rr_str[0], rr_str[0]]
                case 2:
                    rr_str = [rr_str[0], rr_str[1]]
                case _:
                    _err(f"<{tag}> Too many parameters")
                    return None
            rr_int: list[int] = [0, 0]
            for i in (0, 1):
                v = cast_safe(rr_str[i], int)
                if v is not None:
                    if not only_positive or (v >= 0):
                        rr_int[i] = v
                    else:
                        _err(f"<{tag}> Negative values are forbidden")
                        return None
                else:
                    lims = alias_parser(rr_str[i])
                    if lims is None:
                        _err(f"<{tag}> Unknown alias: '{rr_str[i]}'")
                        return None
                    rr_int[i] = lims[i]
            if rr_int[0] > rr_int[1]:
                _err(f"<{tag}> Typo or wrong order")
                return None
            return (rr_int[0], rr_int[1])

        _ok = True
        ini_system = system_ini()
        self._id = s.id

        # $GENMODE
        try:
            tmp = self._get_builder(s.get_string("$GENMODE"))
            if tmp is not None:
                self.builder = tmp
            else:
                _err("$GENMODE: Invalid value")
        except Section.Error:
            _err(f"$GENMODE: No value")

        # <name>, <icon>, <bio>, <snd_config>, <terrain_sect>
        # These are optional string fields
        for field in ["name", "icon", "bio", "snd_config", "terrain_sect"]:
            value = s._fields.get(field, None)
            if (value is None) or (len(value) > 0):
                setattr(self, field, value)
            else:
                _err(f"<{field}> Empty string")

        # <class>, <community>, <visual>
        # These are mandatory string fields
        to_attr = { "class": "cls" }
        for field in ["class", "community", "visual"]:
            try:
                tmp = s.get_string(field)
            except Section.Error as e:
                _err(f"<{field}> {e.msg}")
            else:
                if len(tmp) > 0:
                    setattr(self, to_attr.get(field, field), tmp)
                else:
                    _err(f"<{field}> Empty string")
        
        # Validating and uniforming: <visual>, <snd_config>
        if hasattr(self, "visual"):
            if is_valid_filepath(self.visual):
                self.visual = str(PureWindowsPath(self.visual)).removesuffix(".ogf")
            else:
                delattr(self, "visual")
                _err(f"<visual> Invalid filepath")
        if hasattr(self, "snd_config") and (self.snd_config is not None):
            if is_valid_filepath(self.snd_config):
                self.snd_config = f"{PureWindowsPath(self.snd_config)}\\"
            else:
                delattr(self, "snd_config")
                _err(f"<snd_config> Invalid filepath")
        
        # <rank>
        tmp = _read_range(
            tag="rank",
            only_positive=True,
            alias_parser=CharacterFactory._get_rank_lims
        )
        if tmp is not None:
            if (tmp[0] < 100) or (tmp[1] < 100):
                self._warn("Don't set rank below 100 to avoid NPC absurd accuracy bug")
            self.rank = tmp
        
        # <reputation>
        tmp = _read_range(
            tag="reputation",
            only_positive=False,
            alias_parser=CharacterFactory._get_reputation_lims
        )
        if tmp is not None:
            self.reputation = tmp

        # <money>
        if s.get_string("money", "").lower() in ["inf", "infinitive"]:
            self.money = (100000, 110000)
            self.money_inf = True
        else:
            try:
                money_list = s.get_uints("money", mandatory=True)
            except Section.Error as e:
                _err(f"<money> {e.msg}")
            else:
                match len(money_list):
                    case 0:
                        _err("<money> Empty field")
                    case 1:
                        self.money = (money_list[0], money_list[0])
                    case 2:
                        if money_list[0] <= money_list[1]:
                            self.money = (money_list[0], money_list[1])
                        else:
                            _err("<money> Typo or wrong order")
                    case _:
                        _err("<money> Too many parameters")
            self.money_inf = False
        if hasattr(self, "money"):
            if (self.money[0] == 0) or (self.money[1] == 0):
                self._warn("<money> min or max value is zero")

        # <crouch_type>
        self.crouch_type = None
        if s.line_exist_with_value("crouch_type"):
            try:
                tmp = s.get_int("crouch_type")
            except Section.Error as e:
                _err(f"<crouch_type> {e.msg}")
            else:
                if tmp in [-1, 0, 1]:
                    self.crouch_type = tmp
                else:
                    _err(f"<crouch_type> Invalid value")

        # <w0>, <w1>, <w2>, <items>
        self.w0, self.w1, self.w2 = [], [], []
        self.items = []
        for field in ["w0", "w1", "w2", "items"]:
            try:
                setattr(self, field, CharacterFactory._read_items(s, field))
            except CharacterFactory.ItemsError as e:
                _err(f"<{field}> {e}")
        
        # Checking <w0>, <w1>, <w2>
        # Проверка, что указано действительно оружие.
        for se in itertools.chain(self.w0, self.w1, self.w2):
            if (se is not None) and (se._type != "T_WPN"):
                self._warn(f"Not a weapon: '{se.name}'")
        
        # Checking <w1>, <w2>
        # Проверка, чтобы в одной характеристике не комбинировалось
        #  оружие, которое NPC использует в одном и том же слоте.
        for se in self.w1:
            if se is None:
                continue
            if ini_system.get_int(se.name, "ef_weapon_type", -1) not in [5]:
                self._warn(f"Unexpected ef_weapon_type in '{se.name}' from 'w1'")
        for se in self.w2:
            if se is None:
                continue
            if ini_system.get_int(se.name, "ef_weapon_type", -1) not in [6, 7, 8, 9]:
                self._warn(f"Unexpected ef_weapon_type in '{se.name}' from 'w2'")

        # Filling: <a0>, <a1>, <a2>
        self.a0, self.a1, self.a2 = [], [], []
        for w, a in zip([self.w0, self.w1, self.w2], [self.a0, self.a1, self.a2]):
            for wse in w:
                if wse is None:
                    a.append(None)
                else:
                    ammo_sections = ini_system.get_strings(
                        wse.name, "ammo_class", mandatory=False
                    )
                    if len(ammo_sections) > 0:
                        a.append(SpawnEntry(ammo_sections[0], "1"))
                    else:
                        self._warn(f"Can't get ammo for '{wse.name}'")
                        a.append(None)

        # <include_supplies>
        self.include_supplies = None
        if s.line_exist_with_value("include_supplies"):
            try:
                self.include_supplies = s.get_strings("include_supplies")
            except Section.Error as e:
                _err(f"<include_supplies> {e.msg}")

        # <include>
        self.include = None
        if s.line_exist_with_value("include"):
            try:
                self.include = s.get_strings("include")
            except Section.Error as e:
                _err(f"<include> {e.msg}")
        
        # <start_dialog>
        try:
            self.start_dialog = s.get_strings("start_dialog", mandatory=False)
            if len(self.start_dialog) > 1:
                self._warn("<start_dialog> More than one dialog")
        except Section.Error as e:
            _err(f"<start_dialog> {e.msg}")

        # <actor_dialog>
        try:
            self.actor_dialog = s.get_strings("actor_dialog", mandatory=False)
        except Section.Error as e:
            _err(f"<actor_dialog> {e.msg}")
        
        # Extra check for <start_dialog> and <actor_dialog>
        if hasattr(self, "start_dialog") and hasattr(self, "actor_dialog"):
            cnt_total = len(self.start_dialog) + len(self.actor_dialog)
            cnt_unique = len(set([*self.start_dialog, *self.actor_dialog]))
            if cnt_total != cnt_unique:
                self._warn("The same dialog is used twice")

        if not _ok:
            raise CharacterFactory.IncompleteError()
    
    def _warn(self, msg: str) -> None:
        print_warning(f"[{self._id}] {msg}")

    def _get_builder(self, v: str) -> Callable[[], list[Character]] | None:
        match v.lower():
            case "0" | "w0+w1*w2":
                return self._builder_mode_0
            case "1" | "unique":
                return self._builder_mode_1
            case "2" | "w0+w2":
                return self._builder_mode_2
        return None

    @staticmethod
    def _get_rank_lims(rank: str) -> tuple[int, int] | None:
        """Получение пары численных значений для данного идентификатора ранга.

        Ранг новичков начинается со 100 (а не с 0),
        чтобы избежать бага с завышенной точностью стрельбы
        (см. ``report_57``).
        
        :param rank: Идентификатор ранга.
        :return: Пара минимального и максимального численных значений для данного ранга.
            Возвращает None, если идентификатор не опознан.
        """
        match rank.lower():
            case "1n" | "novice":
                return (100, 299)
            case "2e" | "experienced":
                return (300, 599)
            case "3v" | "veteran":
                return (600, 899)
            case "4m" | "master":
                return (900, 999)
        return None

    @staticmethod
    def _get_reputation_lims(reputation: str) -> tuple[int, int] | None:
        """Получение пары численных значений для данного идентификатора репутации.
        
        :param rank: Идентификатор репутации.
        :return: Пара минимального и максимального численных значений
            для данной репутации. Возвращает None, если идентификатор не опознан.
        """
        match reputation.lower():
            case "terrible":
                return (-1500, -1001)
            case "very_bad":
                return (-1000, -151)
            case "bad":
                return (-150, -51)
            case "neutral":
                return (-50, 49)
            case "good":
                return (50, 149)
            case "very_good":
                return (150, 999)
            case "excellent":
                return (1000, 1500)
        return None

    @staticmethod
    def _read_items(section: Section, field: str) -> list[SpawnEntry | None]:
        """Прочитать строку с предметами из указанного поля данной секции.
        
        Пример строки: ``bread, vodka (2), wpn_pm (1, silencer)``
        
        :param section: Секция, из которой считывается поле.
        :param field: Поле, в котором записана строка с предметами.
        :raises ItemsError: при ошибке считывания.
        :return: Список экземпляров класса
            :class:`~ip_ltx.treasure_manager_ext.SpawnEntry`.

            Также в списке сохраняется как None:
            
            * Специальный элемент списка - нижнее подчёркивание (``_``)
            * Предмет с нулевым количеством
            * Предмет с нулевой вероятностью
        """
        Err = CharacterFactory.ItemsError
        line = section.get_string(field, "").strip()
        if len(line) == 0:
            return []
        if line.find("|") != -1:
            raise Err("wrong item list format")
        
        # Предобработка разделителей
        line_p = list(line)
        parenthesis = False
        for i in range(len(line_p)):
            if parenthesis:
                if line_p[i] == "(":
                    raise Err("wrong item list format")
                if line_p[i] == ")":
                    parenthesis = False
            else:
                if line_p[i] == ")":
                    raise Err("wrong item list format")
                if line_p[i] == "(":
                    parenthesis = True
                elif line_p[i] == ",":
                    line_p[i] = "|"
        line_p = "".join(line_p)
        
        # Считывание предметов
        items = []
        for i, s1 in enumerate(line_p.split("|")):
            s1 = s1.strip()
            if len(s1) == 0:
                raise Err(f"empty list element (#{i+1})")
            if s1 == "_":
                items.append(None)
                continue
            name, params = None, None
            tmp = re.match(r"^(\S+)\s*\(([^\)]+)\)$", s1)
            if tmp is not None:
                name = tmp.group(1)
                params = tmp.group(2).strip()
            else:
                tmp = re.match(r"^(\S+)$", s1)
                if tmp is None:
                    raise Err(f"wrong item list format (elem #{i+1})")
                name = tmp.group(1)
                params = "1"
            try:
                se = SpawnEntry(name, params)
            except Exception as e:
                raise Err(f"{e} (elem #{i+1})")
            else:
                if (se.count > 0) and (se.prob is None or se.prob > 0):
                    items.append(se)
                else:
                    items.append(None)
        
        return items
    
    @staticmethod
    def refresh():
        CharacterFactory.chr_ids.clear()
        CharacterFactory.chr_cnt_by_cls.clear()
        CharacterFactory.gen_cnt_by_cls.clear()
        CharacterFactory.unique_classes.clear()

    def _build_character(
            self,
            unique: bool,
            wpn: tuple[int | None, int | None, int | None]
    ) -> Character:
        """Генерация характеристики - экземпляра класса :class:`Character`.
        
        :param unique: Уникальная ли это характеристика.
        :param wpn: Выбор оружия из настроек характеристики.
        :raises CharGenClsError: если характеристика не была сгенерирована
            из-за её класса.
        :raises CharGenIdError: если характеристика не была сгенерирована
            из-за её идентификатора.
        :return: Экземпляр класса :class:`Character`.
        """
        if self.cls in CharacterFactory.unique_classes:
            raise CharacterFactory.CharGenClsError((
                f"class '{self.cls}' is already taken"
                " by some unique character"
            ))
        if unique and (CharacterFactory.chr_cnt_by_cls[self.cls] > 0):
            raise CharacterFactory.CharGenClsError((
                f"class '{self.cls}' is already taken"
                " and can't be used for a unique character"
            ))
        
        num = CharacterFactory.chr_cnt_by_cls[self.cls] + 1
        id = Character.get_id(unique, self.cls, num)
        if id in CharacterFactory.chr_ids:
            raise CharacterFactory.CharGenIdError(f"id '{id}' is already taken")

        ch = Character()
        CharacterFactory.chr_ids.add(id)
        CharacterFactory.chr_cnt_by_cls[self.cls] += 1
        if unique:
            CharacterFactory.unique_classes.add(self.cls)

        # base properties
        ch._num         = num
        ch._unique      = unique
        ch.cls          = self.cls
        ch.community    = self.community
        ch.visual       = self.visual
        ch.snd_config   = self.snd_config

        # range properties
        local_rnd = random.Random(id)
        ch.rank = local_rnd.randint(self.rank[0], self.rank[1])
        ch.reputation = local_rnd.randint(self.reputation[0], self.reputation[1])
        ch.money_min = self.money[0]
        ch.money_max = self.money[1]
        ch.money_inf = self.money_inf

        # autofill properties
        ch.name = (
            self.name
            if self.name is not None
            else CharacterDefaults.get_name(ch.community, ch.rank)
        )
        ch.icon = (
            self.icon
            if self.icon is not None
            else CharacterDefaults.get_icon(ch.community, ch.visual)
        )
        ch.crouch_type = (
            self.crouch_type
            if self.crouch_type is not None
            else CharacterDefaults.get_crouch_type(ch.community)
        )
        ch.include_supplies = (
            self.include_supplies
            if self.include_supplies is not None
            else CharacterDefaults.get_include_supplies()
        )
        ch.include = (
            self.include
            if self.include is not None
            else CharacterDefaults.get_include()
        )

        # optional properties
        ch.bio = self.bio
        ch.terrain_sect = self.terrain_sect
        ch.start_dialog = self.start_dialog
        ch.actor_dialog = self.actor_dialog

        # supplies
        ch.spawn_items = []
        for idx, ww, aa in zip(
            wpn,
            [self.w0, self.w1, self.w2],
            [self.a0, self.a1, self.a2]
        ):
            se_w = ww[idx] if idx is not None else None
            se_a = aa[idx] if idx is not None else None
            if se_w is not None:
                ch.spawn_items.append(se_w)
                if (se_a is not None):
                    ch.spawn_items.append(se_a)
        for se in self.items:
            if se is not None:
                ch.spawn_items.append(se)
        
        # Inspecting
        Inspector.name(ch.name)
        Inspector.icon(ch.icon)
        Inspector.bio(ch.bio)
        Inspector.community(ch.community)
        Inspector.terrain_sect(ch.terrain_sect)
        Inspector.visual(ch.visual)
        Inspector.snd_config(ch.snd_config)
        Inspector.include(ch.include_supplies)
        Inspector.include(ch.include)
        Inspector.dialog(ch.start_dialog)
        Inspector.dialog(ch.actor_dialog)

        return ch
    
    def _builder_mode_0(self) -> list[Character]:
        """``w0+w1*w2``"""
        characters = []
        count = len(self.w0) + len(self.w1)*len(self.w2)
        if count == 0:
            self._warn("Zero characters")
        for i in range(count):
            try:
                wpn = (
                    (i, None, None)
                    if i < len(self.w0)
                    else (
                        None,
                        (i - len(self.w0)) % len(self.w1),
                        (i - len(self.w0)) // len(self.w1)
                    )
                )
                characters.append(self._build_character(unique=False, wpn=wpn))
            except CharacterFactory.CharGenClsError as e:
                self._warn(f"Stopped: {e}")
                break
            except CharacterFactory.CharGenIdError as e:
                self._warn(f"Skipped character: {e}")
                continue
        CharacterFactory.gen_cnt_by_cls[self.cls] += 1
        return characters
    
    def _builder_mode_1(self) -> list[Character]:
        """``unique``"""
        characters = []
        count = len(self.w0) + len(self.w1)*len(self.w2)
        if count == 0:
            self._warn("Zero characters")
        if (count > 1):
            self._warn(f"Too many weapons choices for a unique character")
        if count > 0:
            try:
                wpn = (
                    (0, None, None)
                    if len(self.w0) > 0
                    else (None, 0, 0)
                )
                characters.append(self._build_character(unique=True, wpn=wpn))
            except CharacterFactory.CharGenClsError as e:
                self._warn(f"Stopped: {e}")
            except CharacterFactory.CharGenIdError as e:
                self._warn(f"Stopped: {e}")
        CharacterFactory.gen_cnt_by_cls[self.cls] += 1
        return characters
    
    def _builder_mode_2(self) -> list[Character]:
        """``w0+w2``"""
        characters = []
        count = len(self.w0) + len(self.w2)
        if count == 0:
            self._warn("Zero characters")
        for i in range(count):
            try:
                if i < len(self.w0):
                    wpn = (i, None, None)
                else:
                    if len(self.w1) > 0:
                        shift = CharacterFactory.gen_cnt_by_cls[self.cls]
                        pistol = (i - len(self.w0) + shift) % len(self.w1)
                    else:
                        pistol = None
                    wpn = (None, pistol, i - len(self.w0))
                characters.append(self._build_character(unique=False, wpn=wpn))
            except CharacterFactory.CharGenClsError as e:
                self._warn(f"Stopped: {e}")
                break
            except CharacterFactory.CharGenIdError as e:
                self._warn(f"Skipped character: {e}")
                continue
        CharacterFactory.gen_cnt_by_cls[self.cls] += 1
        return characters

# ----------------------------------------------------------------

def form_characters(
        fp_in: str,
        fp_out: str,
        independent_input: bool = False,
        tab: str = "\t"
) -> None:
    """Сгенерировать XML-файл с характеристиками по заданной конфигурации.

    :param fp_in: Путь до файла с конфигурационными секциями.
    :param fp_out: Путь до файла, куда выписываются сформированные характеристики.
        Директория этого файла должна быть подготовлена заранее.
    :param independent_input: Если True, то перед обработкой данного файла
        генератор забудет о всех ранее сгенерированных характеристиках
        в рамках текущей сессии.
    :param tab: Отступ, используемый при выводе в файл.
    :raises CharacterFactory.IncompleteError: при ошибке в конфигурации.
    """
    ini_cfg = Ini(_name=os.path.basename(fp_in))
    ini_cfg.read(fp_in, encoding=None)
    cf_list: list[CharacterFactory] = []
    ok = True
    for section in ini_cfg.sections():
        if not section.id.startswith("@"):
            try:
                cf_list.append(CharacterFactory(section))
            except CharacterFactory.IncompleteError:
                ok = False
    if not ok:
        raise CharacterFactory.IncompleteError("Invalid configuration file")
    if independent_input:
        CharacterFactory.refresh()
    with open(fp_out, "w", encoding="utf-8") as f:
        f.write("<?xml version='1.0' encoding=\"UTF-8\"?>\n")
        f.write((
            "<!-- This file was generated using"
            " \"ip_ltx.generator_character_desc\" -->\n"
            "<!-- https://github.com/VovaMiller/ip_ltx -->\n"
        ))
        f.write("<xml>\n")
        for cf in cf_list:
            for ch in cf.builder():
                ch.write_xml(f, tab=tab)
        f.write("</xml>\n")

# ----------------------------------------------------------------

def generate(
        fps: list[str],
        independent_input: bool = False,
        output_dir: str | None = None,
        tab: str = "\t"
) -> None:
    """Сгенерировать характеристики NPC по данным файлам.

    * Местный аналог функции-обёртки :func:`~ip_ltx.utils.run`.
    * Перехватывает любые исключения и выводит информацию о них.
    * Также предварительно валидирует все необходимые для работы синглтоны.

    :param fps: Список файлов с настройками характеристик.
    :param independent_input: Если True, то перед обработкой каждого нового файла
        генератор будет забывать о характеристиках, сгенерированных на основе
        предыдущего файла.
    :param output_dir: Существующая директория для выводимых файлов.
        Если None, то вывод осуществляется в текущую директорию.
    :param tab: Отступ, используемый при выводе в файлы.
    """
    def _construct_fp_out(fp_in: str) -> str:
        ifn = os.path.basename(fp_in)
        ifn, ife = os.path.splitext(ifn)
        if ife == ".xml":
            raise Exception("xml file input is not supported")
        if output_dir is None:
            return f"{ifn}.xml"
        odp = Path(output_dir)
        if not odp.is_dir():
            raise Exception("output directory doesn't exist")
        return str(odp.joinpath(f"{ifn}.xml"))
    
    if len(fps) == 0:
        print_warning("zero-length input provided")
        return
    
    try:
        validate_data([system_ini, string_table])
    except Exception:
        return
    preinit_singletons([Dialogs, TextureDesc])
    
    if (output_dir is not None) and not Path(output_dir).is_dir():
        print_error(f"Output directory doesn't exist: '{output_dir}'")
        return
    
    max_len_ifp = max([len(ifp) for ifp in fps])
    max_len_num = len(str(len(fps)))
    for i, ifp in enumerate(fps):
        try:
            ofp = _construct_fp_out(ifp)
            form_characters(ifp, ofp, independent_input, tab)
        except Exception:
            print("")
            print(
                f"{ANSI_COLOR_CODE.RED}-{ANSI_COLOR_CODE.DEF}",
                f"({i+1}/{len(fps)}) {ifp}"
            )
            print(traceback.format_exc())
            print("", flush=True)
        else:
            shift_before = max_len_num - len(str(i+1))
            shift_after = max_len_ifp - len(ifp)
            print(
                f"{ANSI_COLOR_CODE.GREEN}+{ANSI_COLOR_CODE.DEF}",
                f"({i+1}/{len(fps)})",
                f"{" "*shift_before}{ifp}{" "*shift_after} -> {ofp}",
                flush=True
            )
