"""Анализатор all.spawn

Извлечение разной информации по объектам с предварительным запуском инспектора
"""

import re
import os.path
import traceback
from collections import OrderedDict
from pathlib import Path

from .ip_ltx import Ini
from .ini import meta_ini, spawn_ini
from .level import get_lvl_by_gvid
from .spawn import get_spawn
from .utils import print_warning

# ----------------------------------------------------------------

def check_anomalies(fn):
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
        levels = [
            "l01_escape", "l02_garbage", "l03_agroprom", "l04_darkvalley",
            "l05_bar", "l06_rostok", "l07_military", "l08_yantar", "l08u_brainlab",
            "l10_radar", "l11_pripyat", "l12_stancia"
        ]
        cnt_by_lvls = {}
        file.write("\n")
        file.write("Number of zones with restrictor_type = 2:\n")
        for obj in spawn.objects():
            if ini_spawn.get_number(obj._id, "restrictor_type", -1) == 2:
                cnt_by_lvls[obj._level] = cnt_by_lvls.get(obj._level, 0) + 1
        for lvl in levels:
            file.write("- {}: {}\n".format(lvl, cnt_by_lvls.get(lvl, 0)))
        
        # Список позиций аномалий на локации не с типом 2
        level = "l03_agroprom"
        file.write("\n")
        file.write("Anomalies invisible by mobs ({}):\n".format(level))
        for obj in spawn.objects():
            if obj._level != level:
                continue
            if not ini_meta.get_bool("is_anomaly_class2", obj._class, False):
                continue
            if ini_spawn.get_number(obj._id, "restrictor_type", -1) == 2:
                continue
            file.write("- {}: position={}\n".format(obj.name, ",".join(["{:.2f}".format(p) for p in obj.position])))

def extract_mobs(fn, level):
    ini_meta = meta_ini()
    ini_spawn = spawn_ini()
    spawn = get_spawn()
    
    # Проверка типов
    for _class, _type in ini_meta.section("mob_class_to_type").fields():
        if (_type != "T_STALKER") and (_type != "T_MONSTER"):
            ini_meta._exception("section [mob_class_to_type] has unexpected mob type '{}'".format(_type))

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
            health = section.get_number("health")
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
                print_warning(f"Creature '{obj.name}' has [spawner], but no 'cond' in it")
                
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
        for _caption, _type in [("Monsters (alive only)", "T_MONSTER"), ("NPC (alive only)", "T_STALKER")]:
            file.write("## {}\n".format(_caption))
            tab = 4 * (1 + max([len(mob["name"]) for mob in info[_type]]) // 4)
            for mob in info[_type]:
                str_spawner = " {}".format(mob["spawner"]) if (len(mob["spawner"]) > 0) else ""
                str_gulag = " ({})".format(mob["gulag"]) if (len(mob["gulag"]) > 0) else ""
                file.write("+ {}--[{}][t{}s{}g{}]{}{} {}\n".format(
                    mob["name"].ljust(tab),
                    mob["object_flags"],
                    mob["g_team"], mob["g_squad"], mob["g_group"],
                    str_spawner, str_gulag,
                    mob["profile"]
                ))
            file.write("\n")

# ----------------------------------------------------------------

def run(f, tag, kwargs={}):
    fn = "{}__{}.txt".format(Path(__file__).stem, tag)
    try:
        f(fn, **kwargs)
    except Exception as e:
        print("")
        print("! {}".format(fn))
        # print("    {}".format(f.__name__))
        # print("    {}".format(repr(e)))
        print(traceback.format_exc())
        print("", flush=True)
    else:
        print("+ {}".format(fn), flush=True)

# ----------------------------------------------------------------

def _validation():
    try:
        ini_meta = meta_ini()
        ini_spawn = spawn_ini()
        spawn = get_spawn()
    except Exception as e:
        prefix = "[{}]".format(os.path.basename(__file__))
        tab = " "*len(prefix)
        print(prefix,   "Mandatory data validation failed:")
        print(tab,      "\"{}\"".format(str(e)))
        print(tab,      "Program will be stopped!")
        print(tab,      "See messages above.")
        print("")
        # print(traceback.format_exc())
        return 1
    return 0

if _validation():
    raise Exception("Mandatory data validation failed")
