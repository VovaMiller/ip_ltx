"""Извлечение разной информации по объектам, определённым в all.spawn"""

from dataclasses import dataclass

from .ini import meta_ini, spawn_ini
from .spawn import get_spawn
from .utils import print_warning, validate_data
from .utils_meta import ObjectType

# ----------------------------------------------------------------

def check_anomalies(
        fn: str,
        levels: list[str],
        level_for_details: str,
        sort_by_spawn_id: bool = True
) -> None:
    """Вывод разной информации по аномалиям.

    1. Список всех аномалий с указанным ``story_id``.
    2. Кол-во зон с ``restrictor_type = 2`` по каждой локации из ``levels``.
    3. Список аномалий с их позициями, которые невидимы для мутантов и NPC.
       Вывод только по локации, указанной в ``level_for_details``.

    :param fn: Путь/имя файла для вывода.
    :param levels: Список локаций, использующийся при выводе
        некоторой информации (см. список выше).
    :param level_for_details: Локация, по которой выводится
        некоторая информации (см. список выше).
    :param sort_by_spawn_id: Список выводимых аномалий будет отсортирован
        по возрастанию значения ``spawn_id``. Эта опция работает, только если
        в секции ``[features]`` установлен флаг ``universal_acdc``.
    """
    ini_meta = meta_ini()
    ini_spawn = spawn_ini()
    spawn = get_spawn()

    @dataclass(slots=True, frozen=True)
    class AnomalyInfo:
        name: str
        position: str
        spawn_id: int

    # Сборка инфы для level_for_details
    anomalies: list[AnomalyInfo] = []
    for obj in spawn.objects():
        if obj._level != level_for_details:
            continue
        if not ini_meta.line_exist("is_anomaly2", obj._class):
            continue
        if ini_spawn.get_int(obj._id, "restrictor_type", -1) == 2:
            continue
        anomalies.append(AnomalyInfo(
            name=obj.name,
            position=",".join(["{:.2f}".format(p) for p in obj.position]),
            spawn_id=obj.spawn_id
        ))
    if sort_by_spawn_id and ini_meta.get_bool("features", "universal_acdc", False):
        anomalies.sort(key=lambda x: x.spawn_id)

    with open(fn, "w", encoding="utf-8") as file:
        # Поиск аномалий с установленным story_id
        file.write("Anomalies with story_id:\n")
        for obj in spawn.objects():
            if obj._type == ObjectType.ANOMALY:
                if (obj.story_id is not None) and (obj.story_id != -1):
                    file.write("- {}\n".format(obj.name))

        # Кол-во зон, у которых restrictor_type = 2
        cnt_by_lvls = {}
        file.write("\n")
        file.write("Number of zones with restrictor_type = 2:\n")
        for obj in spawn.objects():
            if ini_spawn.get_int(obj._id, "restrictor_type", -1) == 2:
                cnt_by_lvls[obj._level] = cnt_by_lvls.get(obj._level, 0) + 1
        for lvl in levels:
            file.write("- {}: {}\n".format(lvl, cnt_by_lvls.get(lvl, 0)))
        
        # Список позиций аномалий на локации не с типом 2
        file.write("\n")
        file.write(f"Anomalies invisible by mobs ({level_for_details}):\n")
        for anomaly in anomalies:
            file.write(f"- {anomaly.name}: position={anomaly.position}\n")

def extract_mobs(
        fn: str,
        level: str,
        sort_by_spawn_id: bool = True
) -> None:
    """Вывод некоторой информации по всем мобам (мутанты и NPC) на указанной локации.
    
    :param fn: Путь/имя файла для вывода.
    :param level: Локация, по которой выводится информация.
    :param sort_by_spawn_id: Список выводимых мобов будет отсортирован
        по возрастанию значения ``spawn_id``. Эта опция работает, только если
        в секции ``[features]`` установлен флаг ``universal_acdc``.
    """
    ini_spawn = spawn_ini()
    spawn = get_spawn()

    @dataclass(slots=True, frozen=True)
    class MobInfo:
        spawn_id: int
        name: str
        object_flags: str
        g_team: int
        g_squad: int
        g_group: int
        profile: str
        spawner: str
        gulag: str

    # Сборка инфы
    info: dict[ObjectType, list[MobInfo]]
    info = {
        ObjectType.MONSTER: [],
        ObjectType.STALKER: [],
    }
    for obj in spawn.objects():
        if obj._level != level:
            continue
        section = ini_spawn.section(obj._id)
        if obj._type not in info:
            # Not a mob (maybe)
            check = [
                section.line_exist("g_team"),
                section.line_exist("g_squad"),
                section.line_exist("g_group"),
                section.line_exist("dynamic_out_restrictions"),
                section.line_exist("dynamic_in_restrictions"),
            ]
            if any(check) and (obj._class != "O_ACTOR") and (obj._class != "AI_CROW"):
                print_warning((
                    "Object '{}' with class '{}' seems like a creature, "
                    "but was not recognized as such"
                ).format(obj.name, obj._class))
            continue
        
        health = None
        g_team, g_squad, g_group = None, None, None
        try:
            health = section.get_float("health", 1.0)
            g_team = section.get_uint("g_team")
            g_squad = section.get_uint("g_squad")
            g_group = section.get_uint("g_group")
        except Exception as e:
            print_warning(f"Unable to process creature '{obj.name}' ({str(e)})")
            continue
        if health < 0.01:
            # ignoring corpses
            continue

        spawner = ""
        if obj.custom_data.section_exist("spawner"):
            if obj.custom_data.line_exist("spawner", "cond"):
                spawner = obj.custom_data.get_string("spawner", "cond")
            else:
                print_warning(
                    f"Creature '{obj.name}' has [spawner], but no 'cond' in it"
                )
                
        gulag = ""
        if obj.custom_data.section_exist("smart_terrains"):
            gulag = ", ".join(list(obj.custom_data.section("smart_terrains").lines()))
        
        info[obj._type].append(MobInfo(
            spawn_id=obj.spawn_id,
            name=obj.name,
            object_flags=section.get_string("object_flags", "0x????????"),
            g_team=g_team,
            g_squad=g_squad,
            g_group=g_group,
            profile=section.get_string("character_profile", obj.section_name),
            spawner=spawner,
            gulag=gulag
        ))
    if sort_by_spawn_id and meta_ini().get_bool("features", "universal_acdc", False):
        for ot in info.keys():
            info[ot].sort(key=lambda x: x.spawn_id)
    
    # writing down
    with open(fn, "w", encoding="utf-8") as file:
        file.write(f"# {level}\n")
        file.write("\n")
        for _caption, _type in [
            ("Monsters (alive only)", ObjectType.MONSTER),
            ("NPC (alive only)", ObjectType.STALKER)
        ]:
            file.write(f"## {_caption}\n")
            if len(info[_type]) == 0:
                file.write("\n")
                continue
            tab = 4 * (1 + max([len(mob.name) for mob in info[_type]]) // 4)
            for mob in info[_type]:
                str_spawner = (
                    f" {mob.spawner}"
                    if (len(mob.spawner) > 0)
                    else ""
                )
                str_gulag = (
                    f" ({mob.gulag})"
                    if (len(mob.gulag) > 0)
                    else ""
                )
                file.write("+ {}--[{}][t{}s{}g{}]{}{} {}\n".format(
                    mob.name.ljust(tab),
                    mob.object_flags,
                    mob.g_team, mob.g_squad, mob.g_group,
                    str_spawner, str_gulag,
                    mob.profile
                ))
            file.write("\n")

# ----------------------------------------------------------------

validate_data([
    meta_ini,
    spawn_ini,
    get_spawn,
])
