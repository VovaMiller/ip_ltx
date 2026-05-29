"""[string_table] из system.ltx."""

import xml.etree.ElementTree as ET

from ..ini import system_ini
from ..utils import SingletonBase, print_error
from ..utils_xml import print_warning_xml, read_xml


class StringTable(SingletonBase):
    """Набор текстов [string_table].
    """
    _data: dict[str, str]

    def __init__(self):
        ini_system = system_ini()
        if not ini_system.section_exist("string_table"):
            raise Exception("Section [string_table] doesn't exist")
        lang = ini_system.get_string("string_table", "language")
        xml_names = ini_system.get_strings("string_table", "files", mandatory=True)
        xml_paths = [f"text\\{lang}\\{fn}.xml" for fn in xml_names]

        # extracting strings
        self._data = {}
        for fp_from_config in xml_paths:
            try:
                root = ET.fromstringlist(
                    read_xml(
                        fp_from_config,
                        ini_system.gdm,
                        ini_system.gda
                    )
                )
            except Exception as e:
                print_error(f"[string_table] Ignoring '{fp_from_config}':\n  {e}")
                continue
            else:
                for elem in root.iterfind("string"):
                    if (id := elem.attrib.get("id", None)) is None:
                        continue
                    if (elem_text := elem.find("text")) is None:
                        continue
                    if id in self._data:
                        print_warning_xml(
                            f"[string_table] duplicate string with id=\"{id}\""
                        )
                    self._data[id] = str(elem_text.text)

    def __contains__(self, id: str) -> bool:
        return id in self._data

    def __iter__(self):
        return iter(self._data)

    def __getitem__(self, id: str) -> str | None:
        return self._data.get(id, None)

    def __len__(self):
        return len(self._data)

    def get[R](self, id: str, defval: R) -> str | R:
        return self._data.get(id, defval)
