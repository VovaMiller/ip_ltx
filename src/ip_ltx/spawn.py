import os.path
from collections import OrderedDict

from .ip_ltx import Section, Ini
from .ini import meta_ini, system_ini, spawn_ini
from .treasure_manager_ext import SpawnEntry, SpawnEntriesPool
from .utils import print_error
from .utils_meta import Levels, CLSIDs, ObjectType

# ----------------------------------------------------------------

class SpawnObject:
    """Спавн-объект"""

    def __init__(self):
        self._errors: list[str] = []
        """Список сообщений об ошибках, возникших на этапе инициализации"""

        self._src: str = ""
        """Источник секции, по которой произведена инициализация"""

        self._id: str = ""
        """ID секции, по которой произведена инициализация"""

        self.spawn_id: int = -1
        """Порядковый номер объекта в общем списке all.spawn (Universal ACDC)"""

        self.section_name: str = ""
        """cse_abstract: section_name"""

        self.name: str = ""
        """cse_abstract: name"""

        self.position: tuple[float, float, float] = (0, 0, 0)
        """cse_abstract: position"""

        self.direction: tuple[float, float, float] = (0, 0, 0)
        """cse_abstract: direction"""

        self.game_vertex_id: int = -1
        """cse_alife_object: game_vertex_id"""

        self.level_vertex_id: int = -1
        """cse_alife_object: level_vertex_id"""

        self.object_flags: int = -1
        """cse_alife_object: object_flags"""

        self.custom_data: Ini = Ini(name="custom_data")
        """cse_alife_object: custom_data"""

        self.story_id: int = -1
        """cse_alife_object: story_id"""

        self._class: str = ""
        """Поле class из секции объекта"""

        self._type: ObjectType = ObjectType.UNDEFINED
        """Тип объекта"""

        self._level: str = ""
        """Имя локации объекта"""

        self._loot: SpawnEntriesPool = SpawnEntriesPool()
        """Лут [spawn] и/или [spawn_tm] из custom_data"""

    def init(self, section: Section):
        """Инициализация по секции

        :param section: Секция, по которой производится инициализация
        :raises Exception: при ошибке инициализации какого-либо поля
        """

        self._errors.clear()
        self._src = section._src
        self._id = section.id
        self.spawn_id = section.get_uint("spawn_id", -1)

        self.section_name = section.get_string("section_name", "")
        if len(self.section_name) == 0:
            self._errors.append("'section_name' is not specified")

        self.name = section.get_string("name", "")
        if len(self.name) == 0:
            self._errors.append("'name' is not specified")

        self.position = (0, 0, 0)
        try:
            tmp = section.get_floats("position")
        except Exception as e:
            self._errors.append(str(e))
        else:
            if len(tmp) == 3:
                self.position = (float(tmp[0]), float(tmp[1]), float(tmp[2]))
            else:
                self._errors.append((
                    f"'position': expected to get 3 numbers,"
                    f" but got {len(tmp)}"
                ))

        self.direction = (0, 0, 0)
        try:
            tmp = section.get_floats("direction")
        except Exception as e:
            self._errors.append(str(e))
        else:
            if len(tmp) == 3:
                self.direction = (float(tmp[0]), float(tmp[1]), float(tmp[2]))
            else:
                self._errors.append((
                    f"'direction': expected to get 3 numbers,"
                    f" but got {len(tmp)}"
                ))

        self.game_vertex_id = -1
        try:
            tmp = section.get_uint("game_vertex_id")
        except Exception as e:
            self._errors.append(str(e))
        else:
            self.game_vertex_id = tmp

        self.level_vertex_id = -1
        try:
            tmp = section.get_uint("level_vertex_id")
        except Exception as e:
            self._errors.append(str(e))
        else:
            self.level_vertex_id = tmp
        
        self.object_flags = -1
        try:
            tmp = int(section.get_string("object_flags"), 16)
        except Exception as e:
            self._errors.append(str(e))
        else:
            self.object_flags = tmp

        self.custom_data.clear()
        self.custom_data._name = (
            f"custom_data@{self.name}"
            if len(self.name) > 0
            else "custom_data"
        )
        try:
            self.custom_data.read_raw(section.get_string("custom_data", ""))
        except Exception as e:
            self.custom_data.clear()
            self._errors.append(str(e))

        self.story_id = -1
        try:
            tmp = section.get_int("story_id", -1)
        except Exception as e:
            self._errors.append(str(e))
        else:
            if type(tmp) == int:
                self.story_id = tmp
            else:
                self._errors.append("'story_id' is not an integer")

        self._class = ""
        if len(self.section_name) > 0:
            try:
                tmp = system_ini().get_string(self.section_name, "class", "")
            except Exception as e:
                self._errors.append(str(e))
            else:
                if len(tmp) > 0:
                    self._class = tmp
                else:
                    self._errors.append(
                        "unable to get class of this object"
                    )

        self._type = ObjectType.UNDEFINED
        if len(self._class) > 0:
            CLSIDS = CLSIDs()
            if self._class in CLSIDS:
                self._type = CLSIDS.get_object_type(self._class)
                if self._type == ObjectType.UNDEFINED:
                    self._errors.append(
                        "unable to get type of this object (dummy clsid)"
                    )
            else:
                self._errors.append(
                    "unable to get type of this object (unknown clsid)"
                )

        self._level = "";
        if self.game_vertex_id >= 0:
            try:
                tmp = Levels().get_lvl_by_gvid(self.game_vertex_id)
            except Exception as e:
                self._errors.append(str(e))
            else:
                if tmp is not None:
                    self._level = tmp
                else:
                    self._errors.append(
                        "unable to get location of this object"
                    )
        
        self._loot.clear()
        _success = True
        context = f"custom_data@{self.name}" if len(self.name) > 0 else ""
        for ssid in ["spawn", "spawn_tm"]:
            if self.custom_data.section_exist(ssid):
                for k, v in self.custom_data.section(ssid).fields():
                    try:
                        self._loot.add(SpawnEntry(k, v, context))
                    except Exception as e:
                        self._errors.append((
                            f"can't process loot entry"
                            f" '{k if v is None else f"{k} = {v}"}'"
                            f" ({e})"
                        ))
                        _success = False
        if not _success:
            self._loot.clear()
        
        # Валидация
        if len(self._errors) > 0:
            raise Exception("object {} is invalid".format(
                f"'{self.name}'" if (len(self.name) > 0) else f"[{self._id}]"
            ))

    def get_condition(self) -> float:
        """Получить состояние объекта.

        В первую очередь пытается считать поле ``upd:condition``.
        Если его нет, то пытается считать поле ``condition``.
        Если и его нет, то возращает значение по умолчанию - 0.

        На то, как будет считано поле ``upd:condition``, влияет флаг
        ``universal_acdc`` из секции ``[features]`` конфигурационного файла:

        * ``universal_acdc = False``: считывается как ``int`` от 0 до 255.
        * ``universal_acdc = True``: считывается как ``float`` от 0 до 1.

        :return: число с плавающей точкой (``float``) от 0 до 1.
        """
        ini_spawn = spawn_ini()
        if ini_spawn.line_exist(self._id, "upd:condition"):
            if meta_ini().get_bool("features", "universal_acdc", False):
                return ini_spawn.get_float(self._id, "upd:condition")
            else:
                return ini_spawn.get_uint(self._id, "upd:condition") / 255
        elif ini_spawn.line_exist(self._id, "condition"):
            return ini_spawn.get_float(self._id, "condition")
        else:
            return 0.0

# ----------------------------------------------------------------

class Spawn:
    """Хранилище всех спавн-объектов"""

    def __init__(self):
        self._so: OrderedDict[str, SpawnObject] = OrderedDict()
        """Основное хранилище. Не рекомендуется использовать напрямую"""
        
        self._id_by_sid: dict[int, str] = {}
        """Вспомогательная структура для быстрого поиска по story_id"""

    def init(self, silent: bool = False):
        """Инициализация всех спавн-объектов

        :param silent: Выводить ли сообщения об ошибках инициализации
        :raises Exception: если хотя бы один объект не удалось
            инициализировать полноценно; исключение можно проигнорировать,
            но тогда из хранилища будут исключены все проблемные объекты
        """
        self._so.clear()
        self._id_by_sid.clear()
        valid = True
        for s in spawn_ini().sections():
            try:
                so = SpawnObject()
                so.init(s)
            except Exception as e:
                valid = False
                if not silent:
                    print_error(e, prefix=False, color=True)
                    if len(so._errors) > 0:
                        for err in so._errors:
                            print_error(f"- {err}", prefix=False, color=False)
                    print_error("", prefix=False, color=False)
            else:
                self._so[s.id] = so
        self._id_by_sid = {
            so.story_id: so._id
            for so in self._so.values()
            if (so.story_id >= 0)
        }
        if not valid:
            raise Exception("spawn data was not initialized properly")

    def object(self, id: str) -> SpawnObject:
        """Получение спавн-объекта по его id

        :param id: ID спавн-объекта
        :raises Exception: если спавн-объекта с указанным ID
            не существует
        """
        if id not in self._so:
            raise Exception(f"spawn object [{id}] doesn't exist")
        return self._so[id]
    
    def story_object(self, sid: int) -> SpawnObject:
        """Получение спавн-объекта по его story_id

        :param sid: story_id спавн-объекта
        :raises Exception: если спавн-объекта с указанным story_id
            не существует
        """
        if sid not in self._id_by_sid:
            raise Exception(f"spawn object with story_id={sid} doesn't exist")
        return self._so[self._id_by_sid[sid]]
    
    def objects(self):
        """Получение всех спавн-объектов
        """
        return self._so.values()

# ----------------------------------------------------------------

_SPAWN = None

def get_spawn() -> Spawn:
    """Получить единый экземпляр класса Spawn
    """
    global _SPAWN
    if _SPAWN is None:
        _SPAWN = Spawn()
        _SPAWN.init(silent=False)
    return _SPAWN
