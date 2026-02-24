import xml.etree.ElementTree as ET

from ..ip_ltx import Ini
from ..ini import meta_ini
from ..utils import print_error, print_warning, read_xml


_STRING_TABLE = None

def _read_string_table() -> dict[str, str]:
    """ Считывает xml-файлы с string_table в словарь.
    """
    ini_localization = Ini(_name="localization.ltx", ini_meta=meta_ini())
    if ini_localization.gdp_m is None:
        raise Exception(
            "Ini object for localization.ltx was not initialized properly"
        )
    ini_localization.read("config\\localization.ltx", inside_gamedata=True, encoding=None)
    lang = ini_localization.get_string("string_table", "language")
    xml_names = ini_localization.get_strings("string_table", "files", mandatory=True)
    xml_paths = [f"text\\{lang}\\{fn}.xml" for fn in xml_names]

    # extracting strings
    st = {}
    for fp_from_config in xml_paths:
        try:
            root = ET.fromstringlist(
                read_xml(
                    fp_from_config,
                    ini_localization.gdp_m,
                    ini_localization.gdp_o
                )
            )
        except Exception:
            print_error(fp_from_config)
            raise
        else:
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
                    print_warning(f"localization: duplicate string with id=\"{id}\"")
                st[id] = str(elem_text.text)
    return st

# ----------------------------------------------------------------

def string_table():
    global _STRING_TABLE
    if _STRING_TABLE is None:
        _STRING_TABLE = _read_string_table()
    return _STRING_TABLE
