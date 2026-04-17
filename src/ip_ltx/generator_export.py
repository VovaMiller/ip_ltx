"""Генератор данных для сторонних утилит."""

from collections import OrderedDict

from .ini import meta_ini, system_ini
from .utils import print_warning, run

# ----------------------------------------------------------------

def _ip_test_static_tables(fn: str) -> None:
    class SectionGroup:
        def __init__(self, name):
            self.name = name
            self.sections = []

    ini_meta = meta_ini()
    ini_system = system_ini()
    group_by_type = OrderedDict([
        ("T_ART",       SectionGroup("SECTIONS_INV_ART")),
        ("T_WPN",       SectionGroup("SECTIONS_INV_WPN")),
        ("T_AMMO",      SectionGroup("SECTIONS_INV_AMMO")),
        ("T_GREN",      SectionGroup("SECTIONS_INV_GREN")),
        ("T_ADDON",     SectionGroup("SECTIONS_INV_ADDON")),
        ("T_OUTFIT",    SectionGroup("SECTIONS_INV_OUTFIT")),
        ("T_OTHER",     SectionGroup("SECTIONS_INV_OTHER")),
        ("T_STALKER",   SectionGroup("SECTIONS_STALKER")),
    ])

    # filling in groups (inventory items)
    for sect in ini_system.sections():
        if ini_meta.line_exist("ignore_sections", sect.id):
            continue
        if len(ini_system.get_string(sect.id, "scope_respawn", "")) > 0:
            # skipping auxiliary multi-scope sections
            continue
        _class = sect.get_string("class", "?")
        _type = ini_meta.get_string("inv_class_to_type", _class, "?")
        if _type in group_by_type:
            group_by_type[_type].sections.append(sect.id)

    # filling in groups (mobs)
    for sect in ini_system.sections():
        if ini_meta.line_exist("ignore_sections", sect.id):
            continue
        _class = sect.get_string("class", "?")
        _type = ini_meta.get_string("mob_class_to_type", _class, "?")
        if _type in group_by_type:
            group_by_type[_type].sections.append(sect.id)

    # writing
    with open(fn, "w", encoding="utf-8") as file:
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

def _universal_acdc_tables(fn: str) -> None:
    """Генерация таблиц для **Universal ACDC**

    * ``section_to_clsid``
    * ``clsid_to_class``

    Работа генерации тестировалась на Universal ACDC v1.38
    """
    ini_meta = meta_ini()
    SECTION_IGNORE = "universal_acdc@ignore"
    SECTION_CONVERSION = "universal_acdc@conversion"

    # Множество CLSID, которые будут проигнорированы
    if ini_meta.section_exist(SECTION_IGNORE):
        ignore_clsid = set(ini_meta.section(SECTION_IGNORE).lines())
    else:
        ignore_clsid = set()
        print_warning(f"Section [{SECTION_IGNORE}] doesn't exist")

    # Словарь перевода имён серверных классов в имена пакетов Universal ACDC.
    if ini_meta.section_exist(SECTION_CONVERSION):
        cse_conversion = {
            cse_server: cse_package
            for cse_server, cse_package
            in ini_meta.section(SECTION_CONVERSION).fields()
            if (cse_package is not None) and (len(cse_package) > 0)
        }
    else:
        cse_conversion = {}
        print_warning(f"Section [{SECTION_CONVERSION}] doesn't exist")

    # Получение соответствий CLSID с серверным классом.
    # Считываем конфиг программы.
    clsid_to_classes = ini_meta.section("clsid_to_classes")
    clsid_to_cse = {}
    for clsid in clsid_to_classes.lines():
        if clsid in ignore_clsid:
            continue
        cse = clsid_to_classes.get_pair_str(clsid)[1]
        if len(cse) > 0:
            clsid_to_cse[clsid] = cse

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
    TAB = 4
    with open(fn, "w", encoding="utf-8") as file:
        # header
        if len(unknown_clsids) > 0:
            file.write("# These unknown clsids were omitted in the tables below:\n")
            for clsid in unknown_clsids:
                file.write(f"#   {clsid}\n")
            file.write("\n")
        file.write("# scan.pm\n")

        # section_to_clsid
        offset = ((
            2 + max([len(sect_id) for sect_id in section_to_clsid.keys()]) + TAB
        ) // TAB) * TAB
        file.write("use constant section_to_clsid => {\n")
        for section, clsid in section_to_clsid.items():
            shift = " "*(offset - len(section) - 2)
            file.write(f"\t'{section}'{shift}=> '{clsid}',\n")
        file.write("};\n")

        # clsid_to_class
        offset = ((
            max([len(sect_id) for sect_id in clsid_to_cse.keys()]) + TAB
        ) // TAB) * TAB
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

    * Статические таблицы для **ip_test** (``ip_test_db.script``)
    * Таблицы ``section_to_clsid`` и ``clsid_to_class`` для **Universal ACDC**
    """
    print("-"*80)
    ini_system = system_ini()
    print("MOD:", ini_system.gdm)
    print("ALT:", ini_system.gda or "--")
    print("-"*80)
    run(_ip_test_static_tables,  "ip_test")
    run(_universal_acdc_tables,  "universal_acdc")
    print("-"*80)
