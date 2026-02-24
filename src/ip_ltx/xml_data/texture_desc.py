"""[texture_desc] из system.ltx."""

import xml.etree.ElementTree as ET
from collections import OrderedDict
from dataclasses import dataclass

from ..ini import system_ini
from ..utils import cast_safe, print_error, print_warning, read_xml, SingletonBase


@dataclass(frozen=True)
class Texture:
    id: str
    x: int
    y: int
    width: int
    height: int
    file_name: str

class TextureDesc(SingletonBase):
    """Данные из xml-файлов, перечисленных в секции [texture_desc] из system.ltx.
    Порядок определения текстур сохранён.
    """
    _data: OrderedDict[str, Texture]

    def __init__(self):
        ini_system = system_ini()
        xml_names = ini_system.get_strings("texture_desc", "files", mandatory=True)
        xml_paths = [f"ui\\{fn}.xml" for fn in xml_names]
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

            # <file_name>
            elem_fn = root.find("file_name")
            file_name = elem_fn.text if elem_fn is not None else None
            if file_name is None:
                print_warning(f"[XML:{fp_from_config}] Can't find <file_name>")
                file_name = ""
            
            # <texture>
            for elem in root.iterfind("texture"):
                # id
                id = elem.attrib.get("id", None)
                if id is None:
                    continue
                if id in self._data:
                    print_warning((
                        f"[XML:{fp_from_config}] "
                        f"Duplicate <texture id=\"{id}\" ...>"
                    ))
                    continue

                # integer properties
                area = OrderedDict.fromkeys(["x", "y", "width", "height"], 0)
                missing, invalid = [], []
                for k in area.keys():
                    v = elem.attrib.get(k, None)
                    if v is None:
                        missing.append(k)
                        v = 0
                    else:
                        v = cast_safe(v, int, None)
                    if v is None:
                        invalid.append(k)
                        v = 0
                    area[k] = v
                if len(missing) > 0:
                    print_warning((
                        f"[XML:{fp_from_config}] "
                        f"Texture '{id}' has no attribute(s): "
                        f"{", ".join(missing)}"
                    ))
                if len(invalid) > 0:
                    print_warning((
                        f"[XML:{fp_from_config}] "
                        f"Texture '{id}' has invalid attribute(s): "
                        f"{", ".join(invalid)}"
                    ))

                self._data[id] = Texture(id, **area, file_name=file_name)

    def __contains__(self, id: str) -> bool:
        return id in self._data
    
    def __iter__(self):
        return iter(self._data)

    def __getitem__(self, id: str) -> Texture | None:
        return self._data.get(id, None)

    def __len__(self):
        return len(self._data)
