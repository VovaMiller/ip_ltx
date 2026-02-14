"""Базовый инструментарий для извлечения кастомной информации из конфигов"""

import re
import math
from collections import OrderedDict
from collections.abc import Callable

from .ip_ltx import Section
from .ini import meta_ini, system_ini
from .string_table import string_table
from .utils import print_warning

# ----------------------------------------------------------------

# Preconds

def _is_ignored_id(section_id: str) -> bool:
    return meta_ini().line_exist("ignore_sections", section_id)

def _is_ignored(section: Section) -> bool:
    return _is_ignored_id(section.id)

def _is_multiscope(section: Section) -> bool:
    return len(section.get_string("scope_respawn", "")) > 0

def is_inv_item__old(section: Section) -> bool:
    """Является ли секция инвентарным предметом.
    Используется старый критерий: наличие у секции поля ``inv_name``.
    """
    return section.line_exist("inv_name")

def is_inv_item__old2(section: Section) -> bool:
    """Является ли секция инвентарным предметом.
    Используется старый критерий: наличие у секции поля ``inv_name``.
    Доп. исключение: вспомогательные секции оружия для многоприцельности.
    """
    return is_inv_item__old(section) and not _is_multiscope(section)

def is_inv_item(section: Section) -> bool:
    """Является ли секция инвентарным предметом.
    Используется проверка по классу (поле ``class``).
    """
    _class = section.get_string("class", "-")
    return (len(meta_ini().get_string("inv_class_to_type", _class, "")) > 0)

def is_inv_item2(section: Section) -> bool:
    """Является ли секция инвентарным предметом.
    Используется проверка по классу (поле ``class``).
    Доп. исключение: вспомогательные секции оружия для многоприцельности.
    """
    return is_inv_item(section) and not _is_multiscope(section)

def is_mutant_part(section: Section) -> bool:
    """Является ли секция предметом типа часть мутанта.
    Под критерий попадает любой инвентарный предмет, ID секции которого
    начинается на ``mutant_``.
    """
    return (
        is_inv_item__old2(section)
        and (re.match(r"^mutant_\w+$", section.id) is not None)
    )

def _is_inv_type(section: Section, _type: str) -> bool:
    _class = section.get_string("class", "-")
    return (meta_ini().get_string("inv_class_to_type", _class, "") == _type)

def is_art(section: Section) -> bool:
    """Является ли секция артефактом.
    Используется проверка по классу (поле ``class``).
    """
    return _is_inv_type(section, "T_ART")

def is_outfit(section: Section) -> bool:
    """Является ли секция броником.
    Используется проверка по классу (поле ``class``).
    """
    return _is_inv_type(section, "T_OUTFIT")

def is_wpn(section: Section) -> bool:
    """Является ли секция оружием.
    Используется проверка по классу (поле ``class``).
    """
    return _is_inv_type(section, "T_WPN")

def is_wpn2(section: Section) -> bool:
    """Является ли секция оружием.
    Используется проверка по классу (поле ``class``).
    Доп. исключение: вспомогательные секции оружия для многоприцельности.
    """
    return is_wpn(section) and not _is_multiscope(section)

def is_ammo(section: Section) -> bool:
    """Является ли секция патронами.
    Используется проверка по классу (поле ``class``).
    """
    return _is_inv_type(section, "T_AMMO")

def is_projectile(section: Section) -> bool:
    """Является ли секция снарядом.
    Используется проверка по классу (поле ``class``).
    """
    return _is_inv_type(section, "T_PROJ")

def is_grenade(section: Section) -> bool:
    """Является ли секция гранатой.
    Используется проверка по классу (поле ``class``).
    """
    return _is_inv_type(section, "T_GREN")

def is_addon(section: Section) -> bool:
    """Является ли секция аддоном для оружия.
    Используется проверка по классу (поле ``class``).
    """
    return _is_inv_type(section, "T_ADDON")

def is_addon_scope(section: Section) -> bool:
    """Является ли секция прицелом для оружия.
    Используется проверка по классу (поле ``class``).
    """
    return is_addon(section) and (section.get_string("class", "") == "WP_SCOPE")

def has_cost(section: Section) -> bool:
    """Является ли секция инвентарным предметом, имеющим поле ``cost``.
    """
    return is_inv_item__old(section) and section.line_exist("cost")

def has_cost2(section: Section) -> bool:
    """Является ли секция инвентарным предметом, имеющим поле ``cost``.
    Доп. исключение: вспомогательные секции оружия для многоприцельности.
    """
    return has_cost(section) and not _is_multiscope(section)

def has_class(section: Section) -> bool:
    """Имеет ли секция непустое поле ``class``.
    """
    return (len(section.get_string("class", "")) > 0)

def has_spawn_path(section: Section) -> bool:
    """Имеет ли секция непустое поле ``$spawn``.
    """
    return (len(section.get_string("$spawn", "")) > 0)

def is_monster(section: Section) -> bool:
    """Является ли секция мутантом.
    Используется проверка по классу (поле ``class``).
    """
    _class = section.get_string("class", "-")
    return (meta_ini().get_string("mob_class_to_type", _class, "") == "T_MONSTER")

def is_stalker(section: Section) -> bool:
    """Является ли секция сталкером/NPC.
    Используется проверка по классу (поле ``class``).
    """
    _class = section.get_string("class", "-")
    return (meta_ini().get_string("mob_class_to_type", _class, "") == "T_STALKER")

def is_anomaly(section: Section) -> bool:
    """Является ли секция аномалией.
    Используется проверка по классу (поле ``class``).
    В основе широкий критерий, под который попадает в т.ч. радиоактивная зона.
    """
    _class = section.get_string("class", "-")
    return meta_ini().get_bool("is_anomaly_class", _class, False)

def is_anomaly2(section: Section) -> bool:
    """Является ли секция аномалией.
    Используется проверка по классу (поле ``class``).
    По сравнению с :func:`is_anomaly` в основе более узкий критерий, который
    по идее эквивалентен проверке ``_g.IsAnomaly``.
    """
    _class = section.get_string("class", "-")
    return meta_ini().get_bool("is_anomaly_class2", _class, False)

# ----------------------------------------------------------------

# Fields Post Processing

def to_uint(v: str | None) -> int:
    """Преобразование значения поля в неотрицательное целое число.
    При невозможности преобразования выдаст ``-1``.
    """
    return int(v) if ((v is not None) and v.isdigit()) else -1

def to_int(v: str | None) -> int:
    """Преобразование значения поля в целое число.
    При невозможности преобразования выдаст ``-9999``.
    """
    v = v if v is not None else "invalid"
    try:
        r = int(v)
    except Exception:
        r = -9999
    return r

def to_float(v: str | None) -> float:
    """Преобразование значения поля в число с плавающей точкой.
    При невозможности преобразования выдаст ``-999.9``.
    """
    v = v if v is not None else "invalid"
    try:
        r = float(v)
    except:
        r = -999.9
    return r

def translate_string(v: str | None) -> str:
    """Перевод строки по таблице ``string_table``.
    """
    return string_table().get(v, v) if v is not None else "-"

def scope_type(v: str | None) -> str:
    """Определение типа прицела: коллиматор или оптика.
    Используется для преобразования значения поля ``scope_texture``.
    """
    return "collimator" if (v is None or len(v) == 0) else "optical"

# ----------------------------------------------------------------

def extract_fields(
        fn: str,
        precond: Callable[[Section], bool],
        fields: list[str],
        fields_pp: list[Callable[[str | None], str | int | float]] | None = None,
        sort: int | None = None,
        as_blocks: bool = False,
        dont_ignore_sections: bool = False
) -> None:
    """Итерация по всем секциям system.ltx и извлечение полей.
    
    :param fn: Путь/имя файла для вывода.
    :param precond: Функция-фильтр секций.
    :param fields: Список полей для извлечения.
    :param fields_pp: Список функций для постобработки значений соответствующих
        полей. Должен совпадать по размеру с fields.
    :param sort: Режим сортировки выводимых секций.
        None - без сортировки.
        0 - по имени секции.
        Больше 0 - по соответствующему полю.
    :param as_blocks: Режим вывода.
        True - вывести каждую секцию отдельными блоками.
        False - вывести в формате таблицы (одна секция - одна строка).
    :param dont_ignore_sections: Не игнорировать секции, перечисленные
        в мета-файле в [ignore_sections].
    """
    if (fields_pp is not None) and (len(fields) != len(fields_pp)):
        raise Exception("len of lists 'fields' and 'fields_pp' must be equal")
    ini_system = system_ini()
    
    # Extract data from system
    d = OrderedDict()
    for section in ini_system.sections():
        if not dont_ignore_sections and _is_ignored(section):
            continue
        if not precond(section):
            continue
        d[section.id] = OrderedDict()
        if fields_pp is None:
            for field in fields:
                d[section.id][field] = section._fields.get(field, "-")
        else:
            for i, field in enumerate(fields):
                d[section.id][field] = fields_pp[i](section._fields.get(field, None))
    if sort is not None:
        if sort == 0:
            d = OrderedDict(sorted(d.items(), key=lambda x: x[0]))
        elif 0 < sort <= len(fields):
            d = OrderedDict(sorted(d.items(), key=lambda x: x[1][fields[sort-1]]))
    
    with open(fn, "w", encoding="utf-8") as file:
        if as_blocks:
            # Header
            file.write(
                "{}\n".format(
                    "\n".join(["; {}".format(field) for field in fields])
                )
            )
            
            # Sections' blocks
            for k, v in d.items():
                file.write("\n")
                file.write("# {}\n".format(k))
                file.write("\n".join([v[field] for field in fields]))
                file.write("\n")
        else:
            # Calculate tab offsets
            tab_offset_0 = ((max([len(v) for v in d.keys()]) // 4) + 1) * 4
            max_lens = [
                max([len(field)] + [len(str(v[field])) for v in d.values()])
                for field in fields
            ]
            
            # Header
            column_0_name = "# id"
            file.write("{}{}".format(
                column_0_name,
                " "*(tab_offset_0 - len(column_0_name))
            ))
            for i, field in enumerate(fields):
                file.write("{}{}".format(" "*(2 + max_lens[i] - len(field)), field))
            file.write("\n")
            
            # Print
            for k, v in d.items():
                file.write("{}{}".format(k, " "*(tab_offset_0 - len(k))))
                for i, field in enumerate(fields):
                    file.write("{}{}".format(
                        " "*(2 + max_lens[i] - len(str(v[field]))),
                        v[field]
                    ))
                file.write("\n")


def extract__ammo_to_wpn(
        fn: str,
        dont_ignore_sections: bool = False
) -> None:
    """Для каждого типа патронов/боеприпасов извлечь список стволов его использующих.
    
    :param fn: Путь/имя файла для вывода.
    :param dont_ignore_sections: Не игнорировать секции, перечисленные
        в мета-файле в [ignore_sections].
    """
    ini_system = system_ini()
    da = OrderedDict()
    for section in ini_system.sections():
        if not dont_ignore_sections and _is_ignored(section):
            continue
        if not is_wpn2(section):
            continue
        ammo_classes = section.get_strings("ammo_class", False)
        for ammo in ammo_classes:
            if not dont_ignore_sections and _is_ignored_id(ammo):
                continue
            if da.get(ammo, None) is None:
                da[ammo] = []
            da[ammo].append(section.id)
    das = OrderedDict(sorted(da.items(), key=lambda x: x[0]))
    tab_offset = ((max([len(v) for v in das.keys()]) // 4) + 1) * 4
    with open(fn, "w", encoding="utf-8") as file:
        for ammo, wpns in das.items():
            file.write("{}{}= {}\n".format(
                ammo,
                " "*(tab_offset - len(ammo)),
                ", ".join(sorted(wpns))
            ))


def extract__addon_to_wpn(
        fn: str,
        dont_ignore_sections: bool = False
) -> None:
    """Для каждого аддона извлечь список стволов его использующих.
    
    :param fn: Путь/имя файла для вывода.
    :param dont_ignore_sections: Не игнорировать секции, перечисленные
        в мета-файле в [ignore_sections].
    """
    ini_system = system_ini()
    d = {}
    for section in ini_system.sections():
        if not dont_ignore_sections and _is_ignored(section):
            continue
        if is_addon(section):
            d[section.id] = []
    for section in ini_system.sections():
        if not dont_ignore_sections and _is_ignored(section):
            continue
        if not is_wpn(section):
            continue
        wpn_sect_id = section.id
        scope_respawn = section.get_string("scope_respawn", "")
        if len(scope_respawn) > 0:
            wpn_sect_id = scope_respawn
        addon_fields = [
            ("scope_status", "scope_name"),
            ("silencer_status", "silencer_name"),
            ("grenade_launcher_status", "grenade_launcher_name"),
        ]
        for _status, _name in addon_fields:
            addon_status = section.get_uint(_status, 0)
            addon_name = section.get_string(_name, "")
            if (addon_status == 2) and (len(addon_name) > 0):
                if addon_name not in d:
                    if not dont_ignore_sections and _is_ignored_id(addon_name):
                        continue
                    print_warning(f"Unexpected addon: '{addon_name}'")
                    d[addon_name] = []
                if wpn_sect_id not in d[addon_name]:
                    d[addon_name].append(wpn_sect_id)
    _class_last = ""
    with open(fn, "w", encoding="utf-8") as file:
        file.write("# <addon> = <weapons>\n")
        dsorted = sorted(d.items(), key=lambda x: ini_system.get_section_index(x[0]))
        for addon, wpns in dsorted:
            _class = ini_system.get_string(addon, "class", "")
            if _class != _class_last:
                file.write("\n")
                _class_last = _class
            file.write("{} = {}\n".format(addon, ", ".join(sorted(wpns))))


def extract_monsters_health(
        fn: str,
        hit_power_wound: float = 2.5,
        hit_power_fire_wound: float = 0.5,
        dont_ignore_sections: bool = False
) -> None:
    """Вывод информации о том, за сколько хитов/ударов/попаданий умирает мутант.
    
    Вывод осуществляется по каждому мутанту, по каждой перечисленной в его
    конфиге кости, по двум типам урона (``wound`` и ``fire_wound``).
    
    :param fn: Путь/имя файла для вывода.
    :param hit_power_wound: Величина урона типа ``wound``,
        используемая при расчётах фатального кол-ва ударов.
    :param hit_power_fire_wound: Величина урона типа ``fire_wound``,
        используемая при расчётах фатального кол-ва попаданий.
    :param dont_ignore_sections: Не игнорировать секции, перечисленные
        в мета-файле в [ignore_sections].
    """
    ini_system = system_ini()
    ceil = lambda f: math.ceil(round(f, 2))
    d = OrderedDict()
    for section in ini_system.sections():
        if not dont_ignore_sections and _is_ignored(section):
            continue
        if not is_monster(section):
            continue
        
        # Extracting health_hit_part.
        health_hit_part = section._fields.get("health_hit_part", None)
        if health_hit_part is None:
            print_warning(f"Skipping '{section.id}' as it has no 'health_hit_part'")
            continue
        health_hit_part = float(health_hit_part)
        
        # Extracting immunitiy.
        immu_sect_id = section._fields.get("immunities_sect", None)
        if immu_sect_id is None:
            print_warning(f"Skipping '{section.id}' as it has no 'immunities_sect'")
            continue
        immu_sect_id = immu_sect_id.lower()
        if not ini_system.section_exist(immu_sect_id):
            print_warning((
                f"Skipping '{section.id}': "
                f"immunities section '{immu_sect_id}' doesn't exist"
            ))
            continue
        immu_sect = ini_system.section(immu_sect_id)
        wound_immunity = immu_sect._fields.get("wound_immunity", None)
        fire_wound_immunity = immu_sect._fields.get("fire_wound_immunity", None)
        if wound_immunity is None:
            print_warning((
                f"Skipping '{section.id}': "
                f"immunities section '{immu_sect_id}' has no 'wound_immunity'"
            ))
            continue
        if fire_wound_immunity is None:
            print_warning((
                f"Skipping '{section.id}': "
                f"immunities section '{immu_sect_id}' has no 'fire_wound_immunity'"
            ))
            continue
        wound_immunity = float(wound_immunity)
        fire_wound_immunity = float(fire_wound_immunity)
        
        # Extracting damage (bones).
        dmg_sect_id = section._fields.get("damage", None)
        if dmg_sect_id is None:
            print_warning(f"Skipping '{section.id}' as it has no 'damage'")
            continue
        dmg_sect_id = dmg_sect_id.lower()
        if not ini_system.section_exist(dmg_sect_id):
            print_warning((
                f"Skipping '{section.id}': "
                f"bone damage section '{dmg_sect_id}' doesn't exist"
            ))
            continue
        dmg_sect = ini_system.section(dmg_sect_id)
        
        # Calculating.
        d[section.id] = OrderedDict()
        for k in dmg_sect.lines():
            try:
                values = [float(vv) for vv in dmg_sect.get_numbers(k, True)]
            except ValueError:
                del d[section.id]
                print_warning((
                    f"Skipping '{section.id}': "
                    f"bad format of bone values (section '{dmg_sect_id}', field '{k}')"
                ))
                break
            if (len(values) != 3) and (len(values) != 4):
                del d[section.id]
                print_warning((
                    f"Skipping '{section.id}': "
                    f"unexpected number of bone values"
                    f" (section '{dmg_sect_id}', field '{k}')"
                ))
                break
            d[section.id][k] = OrderedDict()
            d[section.id][k]["wound"] = ceil(1.0 / (
                hit_power_wound
                * wound_immunity
                * values[0]
                * health_hit_part
            ))
            d[section.id][k]["fire_wound"] = ceil(1.0 / (
                hit_power_fire_wound
                * fire_wound_immunity
                * values[0]
                * health_hit_part
            ))
            if len(values) == 4:
                d[section.id][k]["fire_wound_super"] = ceil(1.0 / (
                    hit_power_fire_wound
                    * fire_wound_immunity
                    * values[3]
                    * health_hit_part
                ))
    
    default_offset_1 = 16
    default_offset_2 = 8
    with open(fn, "w", encoding="utf-8") as file:
        file.write("# hit_power (wound) = {}\n".format(hit_power_wound))
        file.write("# hit_power (fire_wound) = {}\n".format(hit_power_fire_wound))
        file.write("# bone | wound | fire_wound (super fire_wound)\n")
        file.write("\n")
        for sect_id, dbones in d.items():
            file.write("; {}\n".format(sect_id))
            for bone, dv in dbones.items():
                wound = dv["wound"]
                fire_wound = dv["fire_wound"]
                fire_wound_super = dv.get("fire_wound_super", None)
                fire_wound_postfix = (
                    f" ({fire_wound_super})"
                    if fire_wound_super is not None
                    else ""
                )
                file.write("{}{}{}{}{}{}\n".format(
                    bone,
                    " "*(default_offset_1 - len(bone)),
                    wound,
                    " "*(default_offset_2 - len(str(wound))),
                    fire_wound,
                    fire_wound_postfix
                ))
            file.write("\n")

# ----------------------------------------------------------------
