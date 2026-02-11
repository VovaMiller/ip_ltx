import xml.etree.ElementTree as ET
import os.path
from pathlib import Path

from ip_ltx import Ini
from ini import meta_ini
from utils import print_warning


_STRING_TABLE = None

def _read_string_table():
    """ Считывает xml-файлы с string_table в словарь.
        TODO. Нужна поддержка #include внутри xml-файлов (см. string_table_includes)
    """
    ini_localization = Ini(_name="localization.ltx", ini_meta=meta_ini())
    if ini_localization.gdp_m is None:
        raise Exception(
            "Ini object for localization.ltx was not initialized properly"
        )
    ini_localization.read("config\\localization.ltx", inside_gamedata=True, encoding=None)
    st_sect = ini_localization.s.get("string_table", None)
    if st_sect is None:
        raise Exception(
            "section [string_table] was not found in localization.ltx"
        )
    xmls = st_sect._fields.get("files", None)
    xmls = [xml_name.strip() for xml_name in xmls.split(",")] if xmls is not None else []
    
    # reading xml-files' paths
    fns = []
    for path in xmls:
        fn = str(Path(ini_localization.gdp_m).joinpath(Path("config\\text\\rus\\{}.xml".format(path))))
        if os.path.isfile(fn):
            fns.append(fn)
        elif ini_localization.gdp_o is None:
            print_warning(f"string_table file '{path}' was not found!")
        else:
            fn = str(Path(ini_localization.gdp_o).joinpath(Path("config\\text\\rus\\{}.xml".format(path))))
            if os.path.isfile(fn):
                # print_warning(f"Using string_table file '{path}' from original gamedata")
                fns.append(fn)
            else:
                print_warning(f"string_table file '{path}' was not found!")

    # extracting strings
    st = {}
    for fn in fns:
        try:
            tree = ET.parse(fn)
        except Exception as e:
            raise Exception("[{}] {}".format(fn, repr(e)))
        else:
            root = tree.getroot()
            for elem in root:
                if elem.tag != "string":
                    continue
                id = elem.attrib.get("id", None)
                if id is None:
                    continue
                elem_text = elem.find("text")
                if elem_text is None:
                    continue
                if id in st:
                    msg = "localization: duplicate string with id=\"{}\"".format(id)
                    print_warning(msg)
                    # raise Exception(msg)
                st[id] = str(elem_text.text)
    return st

# ----------------------------------------------------------------

def string_table():
    global _STRING_TABLE
    if _STRING_TABLE is None:
        _STRING_TABLE = _read_string_table()
    return _STRING_TABLE
