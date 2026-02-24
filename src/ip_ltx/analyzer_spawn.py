"""Извлечение разной информации по объектам, определённым в all.spawn"""

from .ini import meta_ini, spawn_ini
from .spawn import get_spawn
from .utils import print_warning, validate_data

# ----------------------------------------------------------------

def check_anomalies(
        fn: str,
        levels: list[str],
        level_for_details: str
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
    """
    ini_meta = meta_ini()
    ini_spawn = spawn_ini()
    spawn = get_spawn()
    with open(fn, "w", encoding="utf-8") as file:
        # Поиск аномалий с установленным story_id
        file.write("Anomalies with story_id:\n")
        for obj in spawn.objects():
            if ini_meta.get_bool("is_anomaly_class", obj._class, False):
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
        level = level_for_details
        file.write("\n")
        file.write("Anomalies invisible by mobs ({}):\n".format(level))
        for obj in spawn.objects():
            if obj._level != level:
                continue
            if not ini_meta.get_bool("is_anomaly_class2", obj._class, False):
                continue
            if ini_spawn.get_int(obj._id, "restrictor_type", -1) == 2:
                continue
            file.write("- {}: position={}\n".format(
                obj.name,
                ",".join(["{:.2f}".format(p) for p in obj.position])
            ))

def extract_mobs(fn: str, level: str) -> None:
    """Вывод некоторой информации по всем мобам (мутанты и NPC) на указанной локации.
    
    :param fn: Путь/имя файла для вывода.
    :param level: Локация, по которой выводится информация.
    """
    ini_meta = meta_ini()
    ini_spawn = spawn_ini()
    spawn = get_spawn()
    
    # Проверка типов
    for _class, _type in ini_meta.section("mob_class_to_type").fields():
        if (_type != "T_STALKER") and (_type != "T_MONSTER"):
            ini_meta._exception(
                f"section [mob_class_to_type] has unexpected mob type '{_type}'"
            )

    # Сборка инфы
    info = {}
    info["T_STALKER"] = []
    info["T_MONSTER"] = []
    for obj in spawn.objects():
        if obj._level != level:
            continue
        _type = ini_meta.get_string("mob_class_to_type", obj._class, "")
        section = ini_spawn.section(obj._id)
        if len(_type) == 0:
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
            health = section.get_float("health")
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
        
        info[_type].append({
            "name":         obj.name,
            "object_flags": section.get_string("object_flags", "0x????????"),
            "g_team":       g_team,
            "g_squad":      g_squad,
            "g_group":      g_group,
            "profile":      section.get_string("character_profile", obj.section_name),
            "spawner":      spawner,
            "gulag":        gulag,
        })
    
    # writing down
    with open(fn, "w", encoding="utf-8") as file:
        file.write("# {}\n".format(level))
        file.write("\n")
        for _caption, _type in [
            ("Monsters (alive only)", "T_MONSTER"),
            ("NPC (alive only)", "T_STALKER")
        ]:
            file.write("## {}\n".format(_caption))
            tab = 4 * (1 + max([len(mob["name"]) for mob in info[_type]]) // 4)
            for mob in info[_type]:
                str_spawner = (
                    " {}".format(mob["spawner"])
                    if (len(mob["spawner"]) > 0)
                    else ""
                )
                str_gulag = (
                    " ({})".format(mob["gulag"])
                    if (len(mob["gulag"]) > 0)
                    else ""
                )
                file.write("+ {}--[{}][t{}s{}g{}]{}{} {}\n".format(
                    mob["name"].ljust(tab),
                    mob["object_flags"],
                    mob["g_team"], mob["g_squad"], mob["g_group"],
                    str_spawner, str_gulag,
                    mob["profile"]
                ))
            file.write("\n")

# ----------------------------------------------------------------

validate_data([
    meta_ini,
    spawn_ini,
    get_spawn,
])
