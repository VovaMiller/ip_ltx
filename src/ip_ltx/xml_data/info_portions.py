"""Инфопоршни (``[info_portions]`` из ``system.ltx``)."""

import xml.etree.ElementTree as ET
from dataclasses import dataclass

from ..ini import system_ini
from ..utils import SingletonBase, print_error, print_warning, read_xml


@dataclass(frozen=True, slots=True)
class InfoPortion:
    id: str

    # CInfoPortion
    disable:            list[str]
    article:            list[str]
    article_disable:    list[str]
    task:               list[str]

    # CPhraseScript
    action:             list[str]

class InfoPortions(SingletonBase):
    """Класс, хранящий информацию о всех инфопоршнях в игре.

    Данные об инфопоршнях считываются из xml-файлов,
    перечисленных в секции ``[info_portions]`` из ``system.ltx``.
    """
    _data: dict[str, InfoPortion]

    def __init__(self):
        ini_system = system_ini()
        xml_names = ini_system.get_strings("info_portions", "files", mandatory=True)
        xml_paths = [f"gameplay\\{fn}.xml" for fn in xml_names]
        self._data = {}
        for fp_from_config in xml_paths:
            # Считывание текста
            xml_lines = read_xml(
                fp_from_config,
                ini_system.gdm,
                ini_system.gda
            )

            # Парсинг
            try:
                root = ET.fromstringlist(xml_lines)
            except ET.ParseError:
                root = None

            # Парсинг: режим совместимости
            if root is None:
                # Пустые файлы просто пропускаем
                if len(xml_lines) <= 1:
                    print_warning(f"[XML:{fp_from_config}] Empty file")
                    continue

                # Пробуем добавить закрывающий тег
                xml_lines.append("</game_information_portions>")
                try:
                    root = ET.fromstringlist(xml_lines)
                except ET.ParseError:
                    print_error(fp_from_config)
                    raise
                else:
                    print_warning(f"[XML:{fp_from_config}] Closing tag is missing")

            for elem in root.iterfind("info_portion"):
                # id
                id = elem.attrib.get("id", None)
                if id is None:
                    continue
                if id in self._data:
                    print_warning(
                        f"[XML:{fp_from_config}] "
                        f"Duplicate <info_portion id=\"{id}\" ...>"
                    )
                    continue
                self._data[id] = InfoPortion(
                    id=id,
                    disable=[
                        e.text for e in elem.iterfind("disable") if e.text
                    ],
                    article=[
                        e.text for e in elem.iterfind("article") if e.text
                    ],
                    article_disable=[
                        e.text for e in elem.iterfind("article_disable") if e.text
                    ],
                    task=[
                        e.text for e in elem.iterfind("task") if e.text
                    ],
                    action=[
                        e.text for e in elem.iterfind("action") if e.text
                    ]
                )

    def __contains__(self, id: str) -> bool:
        return id in self._data

    def __iter__(self):
        return iter(self._data)

    def __getitem__(self, id: str) -> InfoPortion:
        return self._data[id]

    def __len__(self):
        return len(self._data)
