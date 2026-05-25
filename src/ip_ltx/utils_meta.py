from collections.abc import Container
from dataclasses import dataclass
from enum import Enum, auto

import networkx as nx

from .ini import meta_ini
from .utils import SingletonBase, print_error, print_warning

# ----------------------------------------------------------------

class GameLevels(SingletonBase):
    """Класс, хранящий информацию об игровых локациях и ``game_vertex_id``.

    Определяется секцией ``[level_gvids]`` в meta-файле.
    """

    _level_gvids: dict[str, int]

    def __init__(self):
        s = meta_ini().section("level_gvids")
        self._level_gvids = {}
        for loc in s.lines():
            self._level_gvids[loc.lower()] = s.get_uint(loc)
        self._level_gvids = dict(
            sorted(self._level_gvids.items(), key=lambda x: -x[1])
        )

    def __contains__(self, lvl: str) -> bool:
        return (lvl.lower() in self._level_gvids)

    def __len__(self) -> int:
        return len(self._level_gvids)

    def as_list(self) -> list[str]:
        return list(reversed(self._level_gvids.keys()))

    def get_lvl_by_gvid(self, gvid: int) -> str:
        """Получить имя уровня по ``game_vertex_id``

        :param gvid: ``game_vertex_id``
        :raises ValueError: если дан невалидный ``game_vertex_id``
        :return: Идентификатор уровня
        """
        for lvl, gvid_threshold in self._level_gvids.items():
            if gvid >= gvid_threshold:
                return lvl
        raise ValueError(f"Invalid game_vertex_id ({gvid})")

# ----------------------------------------------------------------

class ServerClasses(SingletonBase):
    """Структура данных, хранящая информацию о серверных классах и их иерархии.

    Определяется секцией ``[server_classes]`` в meta-файле.
    """

    _graph: nx.DiGraph
    """Ориентированный граф,
    в котором ребро (U, V) означает,
    что класс U напрямую наследуется от класса V.
    Циклы не допускаются.
    """

    def __init__(self):
        sn = "server_classes"

        # Построение графа
        sc = meta_ini().section(sn)
        self._graph = nx.DiGraph()
        self._graph.add_nodes_from(sc.lines())
        for cse_child in sc.lines():
            for cse_parent in sc.get_strings(cse_child, mandatory=False):
                if len(cse_parent) > 0:
                    self._graph.add_edge(cse_child, cse_parent)
                else:
                    print_warning(
                        f"[{sn}] {cse_child} "
                        "is derived from a class with zero-lenth name (ignored)"
                    )

        # Проверка на циклы
        if not nx.is_directed_acyclic_graph(self._graph):
            cycles = nx.simple_cycles(self._graph)
            print_warning("[{}] Server classes' hierarchy has cycles:\n    {}".format(
                sn,
                "\n    ".join(
                    [f"{i}: {cycle}" for i, cycle in enumerate(cycles, start=1)]
                )
            ))

    def __contains__(self, cse: str) -> bool:
        return cse in self._graph

    def __len__(self):
        return len(self._graph)

    def issubclass(self, cse_subclass: str, cse_class: str) -> bool:
        """Проверка, является ли один серверный класс подклассом
        другого серверного класса.

        Класс A является подклассом класса B, если B содержится во множестве
        предков класса A или равен классу A.

        Повторяет логику встроенной в Python функции ``issubclass``.

        :raises ValueError: если хотя бы одного из указанных серверных классов
            не существует.
        """
        if cse_subclass not in self._graph:
            raise ValueError(f"{cse_subclass} is not a server class")
        if cse_class not in self._graph:
            raise ValueError(f"{cse_class} is not a server class")
        return nx.has_path(self._graph, cse_subclass, cse_class)

# ----------------------------------------------------------------

class ObjectType(Enum):
    MONSTER         = auto()
    STALKER         = auto()
    ANOMALY         = auto()
    ITEM_ART        = auto()
    ITEM_WEAPON     = auto()
    ITEM_AMMO       = auto()
    ITEM_GRENADE    = auto()
    ITEM_ADDON      = auto()
    ITEM_OUTFIT     = auto()
    ITEM_OTHER      = auto()
    OTHER           = auto()
    UNDEFINED       = auto()

    def is_mob(self) -> bool:
        return self in (
            ObjectType.MONSTER,
            ObjectType.STALKER,
        )

    def is_item(self) -> bool:
        return self in (
            ObjectType.ITEM_ART,
            ObjectType.ITEM_WEAPON,
            ObjectType.ITEM_AMMO,
            ObjectType.ITEM_GRENADE,
            ObjectType.ITEM_ADDON,
            ObjectType.ITEM_OUTFIT,
            ObjectType.ITEM_OTHER,
        )

class ObjectTypeDetector(SingletonBase):
    """Класс для определения типа объекта по его клиентскому и серверному классам.

    Определяется секцией ``[object_types]`` в meta-файле.

    Используется для инициализации :class:`CLSIDs`.
    """

    @dataclass(frozen=True)
    class ObjectTypeRule:
        client_cls: list[str]
        server_cls: list[str]

    _rules: dict[ObjectType, ObjectTypeRule]
    """Правила определения типа объекта. Задаётся для каждого типа, кроме ``OTHER``."""

    def __init__(self):
        sn = "object_types"
        server_classes = ServerClasses()
        fatal = False

        # Задание соответствий
        map: list[tuple[ObjectType, str]]
        map = [
            (ObjectType.MONSTER,        "is_monster"),
            (ObjectType.STALKER,        "is_stalker"),
            (ObjectType.ANOMALY,        "is_anomaly"),
            (ObjectType.ITEM_ART,       "is_item_art"),
            (ObjectType.ITEM_WEAPON,    "is_item_weapon"),
            (ObjectType.ITEM_AMMO,      "is_item_ammo"),
            (ObjectType.ITEM_GRENADE,   "is_item_grenade"),
            (ObjectType.ITEM_ADDON,     "is_item_addon"),
            (ObjectType.ITEM_OUTFIT,    "is_item_outfit"),
            (ObjectType.ITEM_OTHER,     "is_item"),
        ]

        # Считывание данных
        self._rules = {}
        sect = meta_ini().section(sn)
        for object_type, field in map:
            client_cls, server_cls = [], []
            for cls in sect.get_strings(field, mandatory=False):
                if len(cls) > 0:
                    if cls in server_classes:
                        server_cls.append(cls)
                    else:
                        client_cls.append(cls)
                else:
                    print_warning(f"[{sn}] '{field}' has zero-length element (ignored)")
            if (len(client_cls) == 0) and (len(server_cls) == 0):
                print_error(f"[{sn}] '{field}' is undefined")
                fatal = True
            self._rules[object_type] = self.ObjectTypeRule(
                client_cls=client_cls,
                server_cls=server_cls
            )

        if fatal:
            raise Exception(f"[{sn}] is not complete")

    def get(
            self,
            client_class: str | None,
            server_class: str | None
    ) -> ObjectType:
        """Получить тип объекта по его клиентскому и серверному классам.

        Проверок на корректность указанных в аргументах классов не производится.
        """
        if (client_class is None) and (server_class is None):
            return ObjectType.UNDEFINED
        server_classes = ServerClasses()
        for object_type, rules in self._rules.items():
            if (client_class is not None) and (client_class in rules.client_cls):
                return object_type
            if server_class is not None:
                for server_class_rule in rules.server_cls:
                    if server_classes.issubclass(server_class, server_class_rule):
                        return object_type
        return ObjectType.OTHER

# ----------------------------------------------------------------

class CLSIDs(SingletonBase):
    """Класс, хранящий информацию о зарегистрированных CLSID.

    Определяется секциями ``[clsid_to_classes]`` и ``[object_types]`` в meta-файле.
    """

    @dataclass(frozen=True)
    class CLSID:
        clsid: str
        client_class: str | None
        server_class: str | None
        object_type: ObjectType

    _clsids: dict[str, CLSID]

    def __init__(self):
        sn = "clsid_to_classes"
        server_classes = ServerClasses()
        object_type_detector = ObjectTypeDetector()
        fatal = False

        # Считывание данных
        sect = meta_ini().section(sn)
        self._clsids = {}
        for clsid in sect.lines():
            # Проверка: длина CLSID
            if len(clsid) > 8:
                print_warning(f"[{sn}] len('{clsid}') > 8")

            # Получение классов
            pair = sect.get_pair_str(clsid)
            client_class = pair[0] if len(pair[0]) > 0 else None
            server_class = pair[1] if len(pair[1]) > 0 else None

            # Валидация: указанный серверный класс зарегистрирован
            if (server_class is not None) and (server_class not in server_classes):
                print_error(
                    f"[{sn}] {clsid} is assigned "
                    f"to an unregistered server class '{server_class}'"
                )
                fatal = True
                continue

            # Валидация: указанный клиентский класс не является серверным
            if (client_class is not None) and (client_class in server_classes):
                print_error(
                    f"[{sn}] Client class of {clsid} "
                    f"('{client_class}') is registered as a server class"
                )
                fatal = True
                continue

            # Получение типа объекта
            object_type = object_type_detector.get(client_class, server_class)

            # Сохранение
            self._clsids[clsid] = self.CLSID(
                clsid=clsid,
                client_class=client_class,
                server_class=server_class,
                object_type=object_type
            )

        if fatal:
            raise Exception("CLSIDs data validation failed")

    def __contains__(self, clsid: str) -> bool:
        return clsid in self._clsids

    def __getitem__(self, clsid: str) -> CLSID:
        if clsid not in self._clsids:
            raise KeyError(f"clsid {clsid} doesn't exist")
        return self._clsids[clsid]

    def __iter__(self):
        return iter(self._clsids)

    def __len__(self):
        return len(self._clsids)

    def data(self):
        return self._clsids.values()

    def get_client_class(self, clsid: str) -> str | None:
        """Получить имя клиентского класса для данного CLSID.

        :raises ValueError: если указанного clsid не существует.
        """
        if clsid not in self._clsids:
            raise ValueError(f"clsid {clsid} doesn't exist")
        return self._clsids[clsid].client_class

    def get_server_class(self, clsid: str) -> str | None:
        """Получить имя серверного класса для данного CLSID.

        :raises ValueError: если указанного clsid не существует.
        """
        if clsid not in self._clsids:
            raise ValueError(f"clsid {clsid} doesn't exist")
        return self._clsids[clsid].server_class

    def get_object_type(self, clsid: str) -> ObjectType:
        """Получить тип объекта для данного CLSID.

        :raises ValueError: если указанного clsid не существует.
        """
        if clsid not in self._clsids:
            raise ValueError(f"clsid {clsid} doesn't exist")
        return self._clsids[clsid].object_type

    def _is_object_type(
            self,
            clsid: str,
            types: ObjectType | Container[ObjectType]
    ) -> bool:
        if clsid not in self._clsids:
            raise ValueError(f"clsid {clsid} doesn't exist")
        ot = self._clsids[clsid].object_type
        if isinstance(types, ObjectType):
            return (ot == types)
        else:
            return (ot in types)

    def is_monster(self, clsid: str) -> bool:
        return self._is_object_type(clsid, ObjectType.MONSTER)

    def is_stalker(self, clsid: str) -> bool:
        return self._is_object_type(clsid, ObjectType.STALKER)

    def is_anomaly(self, clsid: str) -> bool:
        return self._is_object_type(clsid, ObjectType.ANOMALY)

    def is_artefact(self, clsid: str) -> bool:
        return self._is_object_type(clsid, ObjectType.ITEM_ART)

    def is_weapon(self, clsid: str) -> bool:
        return self._is_object_type(clsid, ObjectType.ITEM_WEAPON)

    def is_ammo(self, clsid: str) -> bool:
        return self._is_object_type(clsid, ObjectType.ITEM_AMMO)

    def is_grenade(self, clsid: str) -> bool:
        return self._is_object_type(clsid, ObjectType.ITEM_GRENADE)

    def is_weapon_addon(self, clsid: str) -> bool:
        return self._is_object_type(clsid, ObjectType.ITEM_ADDON)

    def is_outfit(self, clsid: str) -> bool:
        return self._is_object_type(clsid, ObjectType.ITEM_OUTFIT)

    def is_mob(self, clsid: str) -> bool:
        return self._is_object_type(clsid, {
            ObjectType.MONSTER,
            ObjectType.STALKER,
        })

    def is_item(self, clsid: str) -> bool:
        return self._is_object_type(clsid, {
            ObjectType.ITEM_ART,
            ObjectType.ITEM_WEAPON,
            ObjectType.ITEM_AMMO,
            ObjectType.ITEM_GRENADE,
            ObjectType.ITEM_ADDON,
            ObjectType.ITEM_OUTFIT,
            ObjectType.ITEM_OTHER,
        })

# ----------------------------------------------------------------
