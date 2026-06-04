"""Генератор данных для сторонних утилит."""

from dataclasses import dataclass
from pathlib import Path

from .ini import meta_ini, system_ini
from .utils import print_warning, run
from .utils_meta import CLSIDs, ObjectType
from .utils_system import is_multiscope_section

# ----------------------------------------------------------------

def _ip_cmd_static_tables(fn: str) -> None:
    @dataclass
    class SectionGroup:
        name: str
        sections: list[str]

    ini_meta = meta_ini()
    ini_system = system_ini()
    clsids = CLSIDs()
    group_by_type = {
        ObjectType.ITEM_ART:        SectionGroup("SECTIONS_INV_ART", []),
        ObjectType.ITEM_WEAPON:     SectionGroup("SECTIONS_INV_WPN", []),
        ObjectType.ITEM_AMMO:       SectionGroup("SECTIONS_INV_AMMO", []),
        ObjectType.ITEM_GRENADE:    SectionGroup("SECTIONS_INV_GREN", []),
        ObjectType.ITEM_ADDON:      SectionGroup("SECTIONS_INV_ADDON", []),
        ObjectType.ITEM_OUTFIT:     SectionGroup("SECTIONS_INV_OUTFIT", []),
        ObjectType.ITEM_OTHER:      SectionGroup("SECTIONS_INV_OTHER", []),
        ObjectType.STALKER:         SectionGroup("SECTIONS_STALKER", []),
        ObjectType.MONSTER:         SectionGroup("SECTIONS_MONSTER", []),
    }

    # filling in groups
    for sect in ini_system.sections():
        if ini_meta.line_exist("ignore_sections", sect.id):
            continue
        if is_multiscope_section(sect):
            # skipping auxiliary multi-scope sections
            continue
        _class = sect.get_string("class", "")
        if (len(_class) > 0) and (_class in clsids):
            _type = clsids.get_object_type(_class)
            if _type in group_by_type:
                group_by_type[_type].sections.append(sect.id)

    # writing
    with Path(fn).open("w", encoding="utf-8") as file:
        tab = 4
        for group in group_by_type.values():
            if len(group.sections) > 0:
                offset = ((
                    5 + max([len(sect_id) for sect_id in group.sections]) + (tab - 1)
                ) // tab) * tab
                file.write("\n{} = {{\n".format(group.name))
                for sect_id in group.sections:
                    file.write("{}[\"{}\"]{}= true,\n".format(
                        " "*tab,
                        sect_id,
                        " "*(offset - 4 - len(sect_id))
                    ))
                file.write("}}\n".format())
            else:
                file.write("\n{} = {{}}\n".format(group.name))


def _acdc_tables(fn: str) -> None:
    """Генерация таблицы ``section_to_class`` для **ACDC**.

    Работа генерации тестировалась на ACDC с последней правкой от 11.10.2007
    """
    ini_meta = meta_ini()
    clsids = CLSIDs()
    sn_ignore = "acdc@ignore"
    sn_conversion = "acdc@conversion"

    # Множество CLSID, которые будут проигнорированы
    ignore_clsid: set[str] = set()
    # 1. Кастомный набор
    if ini_meta.section_exist(sn_ignore):
        ignore_clsid.update(ini_meta.section(sn_ignore).lines())
    else:
        print_warning(f"Section [{sn_ignore}] doesn't exist")
    # 2. CLSID-заглушки
    ignore_clsid.update(
        clsid for clsid in clsids
        if clsids[clsid].object_type == ObjectType.UNDEFINED
    )

    # Словарь перевода имён серверных классов в имена пакетов ACDC.
    if ini_meta.section_exist(sn_conversion):
        cse_conversion = {
            cse_server: cse_package
            for cse_server, cse_package
            in ini_meta.section(sn_conversion).fields()
            if (cse_package is not None) and (len(cse_package) > 0)
        }
    else:
        cse_conversion = {}
        print_warning(f"Section [{sn_conversion}] doesn't exist")

    # Получение соответствий CLSID с серверным классом.
    # Считываем конфиг программы.
    clsid_to_cse: dict[str, str]
    clsid_to_cse = {
        clsid.clsid: clsid.server_class
        for clsid in clsids.data()
        if (clsid.clsid not in ignore_clsid) and (clsid.server_class is not None)
    }

    # Получение соответствий имён секций с CLSID.
    # Считываем конфиги игры.
    section_to_clsid = {}
    section_to_clsid_unk = {}
    for section in system_ini().sections():
        _class = section.get_string("class", "")
        if len(_class) == 0:
            continue
        if _class in ignore_clsid:
            continue
        if _class in clsid_to_cse:
            section_to_clsid[section.id] = _class
        else:
            section_to_clsid_unk[section.id] = _class

    # Вывод
    tab = 4
    with Path(fn).open("w", encoding="utf-8") as file:
        # header
        if len(section_to_clsid_unk) > 0:
            offset = ((
                2 + max([len(sect_id) for sect_id in section_to_clsid_unk]) + tab
            ) // tab) * tab
            file.write("# Unable to derive package for these sections:\n")
            for section, clsid in section_to_clsid_unk.items():
                shift = " "*(offset - len(section) - 2)
                file.write(f"#   '{section}'{shift}=> '__UNKNOWN__', # {clsid}\n")
            file.write("\n")
        file.write("# acdc.pl\n")

        # section_to_class
        offset = ((
            2 + max([len(sect_id) for sect_id in section_to_clsid]) + tab
        ) // tab) * tab
        file.write("use constant section_to_class => {\n")
        for section, clsid in section_to_clsid.items():
            cse_server = clsid_to_cse[clsid]
            cse_package = cse_conversion.get(cse_server, cse_server)
            shift = " "*(offset - len(section) - 2)
            file.write(f"\t'{section}'{shift}=> '{cse_package}', # {clsid}\n")
        file.write("};\n")


def _universal_acdc_tables(fn: str) -> None:
    """Генерация таблиц для **Universal ACDC**

    * ``section_to_clsid``
    * ``clsid_to_class``

    Работа генерации тестировалась на Universal ACDC v1.38
    """
    ini_meta = meta_ini()
    clsids = CLSIDs()
    sn_ignore = "universal_acdc@ignore"
    sn_conversion = "universal_acdc@conversion"

    # Множество CLSID, которые будут проигнорированы
    ignore_clsid: set[str] = set()
    # 1. Кастомный набор
    if ini_meta.section_exist(sn_ignore):
        ignore_clsid.update(ini_meta.section(sn_ignore).lines())
    else:
        print_warning(f"Section [{sn_ignore}] doesn't exist")
    # 2. CLSID-заглушки
    ignore_clsid.update(
        clsid for clsid in clsids
        if clsids[clsid].object_type == ObjectType.UNDEFINED
    )

    # Словарь перевода имён серверных классов в имена пакетов Universal ACDC.
    if ini_meta.section_exist(sn_conversion):
        cse_conversion = {
            cse_server: cse_package
            for cse_server, cse_package
            in ini_meta.section(sn_conversion).fields()
            if (cse_package is not None) and (len(cse_package) > 0)
        }
    else:
        cse_conversion = {}
        print_warning(f"Section [{sn_conversion}] doesn't exist")

    # Получение соответствий CLSID с серверным классом.
    # Считываем конфиг программы.
    clsid_to_cse: dict[str, str]
    clsid_to_cse = {
        clsid.clsid: clsid.server_class
        for clsid in clsids.data()
        if (clsid.clsid not in ignore_clsid) and (clsid.server_class is not None)
    }

    # Получение соответствий имён секций с CLSID.
    # Считываем конфиги игры.
    section_to_clsid = {}
    unknown_clsids = set()
    for section in system_ini().sections():
        _class = section.get_string("class", "")
        if len(_class) == 0:
            continue
        if _class in ignore_clsid:
            continue
        if _class in clsid_to_cse:
            section_to_clsid[section.id] = _class
        else:
            unknown_clsids.add(_class)

    # Вывод
    tab = 4
    with Path(fn).open("w", encoding="utf-8") as file:
        # header
        if len(unknown_clsids) > 0:
            file.write("# These unknown clsids were omitted in the tables below:\n")
            for clsid in unknown_clsids:
                file.write(f"#   {clsid}\n")
            file.write("\n")
        file.write("# scan.pm\n")

        # section_to_clsid
        offset = ((
            2 + max([len(sect_id) for sect_id in section_to_clsid]) + tab
        ) // tab) * tab
        file.write("use constant section_to_clsid => {\n")
        for section, clsid in section_to_clsid.items():
            shift = " "*(offset - len(section) - 2)
            file.write(f"\t'{section}'{shift}=> '{clsid}',\n")
        file.write("};\n")

        # clsid_to_class
        offset = ((
            max([len(sect_id) for sect_id in clsid_to_cse]) + tab
        ) // tab) * tab
        file.write("use constant clsid_to_class => {\n")
        for clsid, cse_server in clsid_to_cse.items():
            cse_package = cse_conversion.get(cse_server, cse_server)
            shift = " "*(offset - len(clsid))
            file.write(f"\t{clsid}{shift}=> '{cse_package}',\n")
        file.write("};\n")

# ----------------------------------------------------------------

def generate() -> None:
    """Основная функция для запуска всех генераций.

    Генерирует:

    * Статические таблицы для **ip_cmd** (``ip_cmd_db.script``)
    * Таблицу ``section_to_class`` для **ACDC**
    * Таблицы ``section_to_clsid`` и ``clsid_to_class`` для **Universal ACDC**
    """
    print("-"*80)
    ini_system = system_ini()
    print("MOD:", ini_system.gdm)
    print("ALT:", ini_system.gda or "--")
    print("-"*80)
    run(_ip_cmd_static_tables,  "ip_cmd")
    run(_acdc_tables,           "acdc")
    run(_universal_acdc_tables, "universal_acdc")
    print("-"*80)
