"""Диалоги с NPC"""

import xml.etree.ElementTree as ET
from collections import OrderedDict
from dataclasses import dataclass

from ..ini import system_ini
from ..utils import print_error, print_warning, read_xml, SingletonBase


@dataclass(frozen=True)
class Dialog:
    id: str

class Dialogs(SingletonBase):
    """Данные о диалогах из xml-файлов,
    перечисленных в секции [dialogs] из system.ltx.
    Порядок определения диалогов сохранён.

    Пока хранится лишь набор существующих диалогов
    без какой-либо детальной информации.
    """
    _data: OrderedDict[str, Dialog]

    def __init__(self):
        ini_system = system_ini()
        xml_names = ini_system.get_strings("dialogs", "files", mandatory=True)
        xml_paths = [f"gameplay\\{fn}.xml" for fn in xml_names]
        self._data = OrderedDict()
        for fp_from_config in xml_paths:
            try:
                root = ET.fromstringlist(
                    read_xml(
                        fp_from_config,
                        ini_system.gdp_m,
                        ini_system.gdp_o
                    )
                )
            except Exception:
                print_error(fp_from_config)
                raise

            # <dialog>
            for elem in root.iterfind("dialog"):
                # id
                id = elem.attrib.get("id", None)
                if id is None:
                    continue
                if id in self._data:
                    print_warning((
                        f"[XML:{fp_from_config}] "
                        f"Duplicate dialog id ('{id}')"
                    ))
                    continue

                self._data[id] = Dialog(id)

    def __contains__(self, id: str) -> bool:
        return id in self._data
    
    def __iter__(self):
        return iter(self._data)

    def __getitem__(self, id: str) -> Dialog | None:
        return self._data.get(id, None)

    def __len__(self):
        return len(self._data)
