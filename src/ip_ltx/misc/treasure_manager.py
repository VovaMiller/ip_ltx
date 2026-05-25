from dataclasses import dataclass
from pathlib import Path

from ..ini import meta_ini
from ..ip_ltx import Ini, Section
from ..utils import SingletonBase, print_error, print_warning


@dataclass(frozen=True, slots=True)
class Treasure:
    """Класс одного тайника.
    """
    _id: str
    target: int
    name: str
    description: str

class TreasureManager(SingletonBase):
    """Класс, хранящий данные о тайниках, зарегистрированных в ``treasure_manager``.

    Путь до конфига указывается в настройках (*meta.ltx*):
    секция ``[cfg_path]``, поле ``treasure_manager``.
    """
    _data_by_id: dict[str, Treasure]
    _data_by_sid: dict[int, Treasure]

    ini: Ini
    """Считанный файл конфига (*treasure_manager.ltx*)"""

    def __init__(self):
        ini_meta = meta_ini()
        self.ini = Ini(name="treasure_manager", ini_meta=ini_meta)
        self._data_by_id = {}
        self._data_by_sid = {}

        fp_str = ini_meta.get_string_wb("cfg_path", "treasure_manager", "")
        if len(fp_str) == 0:
            # print_warning("treasure_manager: no data")
            return
        fp = Path(fp_str)
        fn = fp.name
        self.ini._name = fn
        self.ini.read(str(fp), inside_gamedata=True)

        for _id in self.ini.section("list").lines():
            if not self.ini.section_exist(_id):
                print_error(f"({fn}) Treasure '{_id}' from [list] doesn't exist")
                continue
            s = self.ini.section(_id)
            try:
                treasure = Treasure(
                    _id=_id,
                    target=s.get_uint("target"),
                    name=s.get_string("name"),
                    description=s.get_string("description")
                )
            except Section.Error as e:
                print_error(str(e))
            else:
                if treasure.target in self._data_by_sid:
                    print_error(
                        f"({fn}) Skipping '{treasure._id}', "
                        f"as its target ({treasure.target}) has already been used "
                        f"('{self._data_by_sid[treasure.target]._id}')"
                    )
                else:
                    self._data_by_id[_id] = treasure
                    self._data_by_sid[treasure.target] = treasure

    def __contains__(self, treasure: str | int) -> bool:
        """Проверка существования тайника по его *id* (``str``) или *target* (``int``).
        """
        if isinstance(treasure, str):
            return treasure in self._data_by_id
        elif isinstance(treasure, int):
            return treasure in self._data_by_sid
        else:
            raise TypeError("Treasure can only be identified by either str or int")

    def __iter__(self):
        return iter(self._data_by_id.values())

    def __getitem__(self, treasure: str | int) -> Treasure:
        """Получение объекта тайника по его *id* (``str``) или *target* (``int``).
        """
        if isinstance(treasure, str):
            return self._data_by_id[treasure]
        elif isinstance(treasure, int):
            return self._data_by_sid[treasure]
        else:
            raise TypeError("Treasure can only be identified by either str or int")

    def __len__(self):
        return len(self._data_by_id)

    def get[T](self, treasure: str | int, defval: T) -> Treasure | T:
        if treasure in self:
            return self[treasure]
        return defval
