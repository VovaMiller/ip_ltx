"""Инспектор данных all.spawn"""

import re
import os.path
import pygtrie
from collections import OrderedDict

from .db import OBJECT_FLAGS
from .ip_ltx import Ini
from .ini import meta_ini, system_ini, spawn_ini, game_ini
from .spawn import get_spawn
from .treasure_manager import treasure_manager_ini, treasure_by_sid
from .utils import ANSI_COLOR_CODE, cast_safe, validate_data

_OK = True

def _print1(msg):
    global _OK
    _OK = False
    print("[{}] {}".format(os.path.basename(__file__), msg))

def _print2(msg):
    global _OK
    _OK = False
    print("{} {}".format(" "*(2+len(os.path.basename(__file__))), msg))

# ----------------------------------------------------------------

def _check_name_duplicates() -> None:
    """Проверка на отсутствие дубликатов name.
    """
    d = OrderedDict()
    for obj in get_spawn().objects():
        if re.match(r"^meshes\\brkbl#\d+\.ogf$", obj.name) is not None:
            # У breakable_object могут совпадать имена
            # Такой формат имени необходим для совместимости с X-Ray SDK
            continue
        if obj.name in d:
            d[obj.name].append(obj._id)
        else:
            d[obj.name] = [obj._id]
    for name, ids in d.items():
        if len(ids) > 1:
            _print1("name '{}' is used more than once:".format(name))
            for id in ids:
                _print2("+ [{}]".format(id))

def _check_level_correspondence() -> None:
    """Объекты прописаны в файлах соответствующих локаций.
    """
    for obj in get_spawn().objects():
        if (len(obj._src) > 0) and (obj._src.find(obj._level) < 0):
            _print1("object '{}':".format(obj.name))
            _print2("+ on level '{}'".format(obj._level))
            _print2("+ defined in '{}'".format(obj._src))

def _check_upd_fields_consistency() -> None:
    """Значения указанных полей state и update совпадают.
    
    ``health == upd:health``, ``position == upd:position``,
    ``g_team == upd:g_team``, ...

    Также предусмотрен особый случай ``condition`` и ``upd:condition``,
    где значения должны не совпадать, а скорее корректно соотноситься.
    """
    for section in spawn_ini().sections():
        lines = []
        for k, v in section.fields():
            if k.startswith("upd:"):
                continue
            updk = "upd:" + k
            if section.line_exist(updk):
                updv = section.field(updk)
                unequal = False
                if k == "condition":
                    vf = cast_safe(v, float, defval=None)
                    updvf = cast_safe(updv, float, defval=None)
                    if (vf is None) or (updvf is None):
                        # TODO: по факту могут быть и равны, но здесь скорее
                        #       проблема неожиданных типов данных
                        unequal = True
                    else:
                        unequal = (abs(vf - (updvf / 255)) > 0.01)
                else:
                    unequal = (v != updv)
                if unequal:
                    lines.append("{}{}".format(
                        k, "     = {}".format(v) if (v is not None) else ""
                    ))
                    lines.append("{}{}".format(
                        updk, " = {}".format(updv) if (updv is not None) else ""
                    ))
        if len(lines) > 0:
            _print1("object '{}':".format(section.get_string("name")))
            _print2("; parameters inconsistency")
            for line in lines:
                _print2(line)

def _check_story_ids() -> None:
    """Ряд проверок story_id.

    * Отсутствие дубликатов
    * Проверка адекватности значения (0 < int < 65535)
    * Проверка зарегистрированности в [story_ids]
    * Отсутствие неиспользуемых story_id в [story_ids]
    """
    story_ids = {
        int(story_id): label
        for story_id, label in game_ini().section("story_ids").fields()
    }
    d = OrderedDict()
    for obj in get_spawn().objects():
        if obj.story_id != -1:
            if obj.story_id in d:
                d[obj.story_id].append(obj._id)
            else:
                d[obj.story_id] = [obj._id]
            if not (0 < obj.story_id < 65535):
                _print1("object '{}':".format(obj.name))
                _print2("; strange value")
                _print2("story_id = {}".format(obj.story_id))
            elif obj.story_id not in story_ids:
                _print1("object '{}':".format(obj.name))
                _print2("; unregistered value")
                _print2("story_id = {}".format(obj.story_id))
    for sid, ids in d.items():
        if len(ids) > 1:
            _print1("story_id '{}' is used more than once:".format(sid))
            for id in ids:
                _print2("+ [{}]".format(id))
    unused_sids = [
        sid
        for sid in story_ids.keys()
        if (sid not in d) and (sid != 65535)
    ]
    if len(unused_sids) > 0:
        _print1("unused story_id:")
        for sid in unused_sids:
            _print2("{} = \"{}\"".format(sid, story_ids[sid]))

def _check_treasure_manager() -> None:
    """Ряд проверок treasure_manager.

    * *(iP v3.0+)* [spawn] vs [spawn_tm]:
      подразумевается, что [spawn_tm] используется только тайниками,
      которые в свою очередь не используют [spawn].
    * Отсутствие тайников без соответствующего объекта в спавне
    * Отсутствие тайников без custom_data
    * *(iP v2.0+)* Отсутствие тайников с пустым лутом
    * *(iP v2.0+)* Отсутствие тайников с потенциально пустым лутом:
      технически тайнику прописаны предметы,
      но если на всех них висит параметр prob,
      то возможна ситуация, что в игре тайник окажется пустым.
    * Правильная подсказка при наведении на inventory_box:
      на обычном inventory_box, который не является тайником,
      не должно быть подсказки "Обыскать тайник" (``st_search_treasure``);
      и наоборот, на тайниках должна быть только эта подсказка.
    * *(iP v3.0+)* Все тайники должны использовать строго секцию inventory_box;
      иначе не будут срабатывать необходимые колбеки в ``bind_physic_object.script``.
    """
    iPv20 = meta_ini().get_bool("features", "iPv20", False)
    iPv30 = meta_ini().get_bool("features", "iPv30", False)
    found_treasures = {}
    for obj in get_spawn().objects():
        treasure_section = (
            treasure_by_sid(obj.story_id)
            if (obj.story_id != -1)
            else None
        )
        if treasure_section is not None:
            # registered in treasure_manager
            found_treasures[treasure_section.id] = True
            has_spawn = obj.custom_data.section_exist("spawn")
            has_spawn_tm = obj.custom_data.section_exist("spawn_tm")
            if not has_spawn and not has_spawn_tm:
                if iPv20:
                    _print1("treasure '{}':".format(treasure_section.id))
                    _print2("custom_data has neither [spawn] nor [spawn_tm]")
            else:
                if has_spawn:
                    if iPv30:
                        _print1("treasure '{}':".format(treasure_section.id))
                        _print2("+ custom_data has [spawn]")
                        _print2("; use [spawn_tm] instead")
                if len(obj._loot) == 0:
                    if iPv20:
                        _print1("treasure '{}':".format(treasure_section.id))
                        _print2("+ has no items")
                else:
                    for se in obj._loot.entries():
                        g = True
                        g = g and (se.count > 0)
                        g = g and ((se.box_size is None) or (se.box_size > 0))
                        g = g and ((se.prob is None) or (se.prob == 100))
                        if g:
                            break
                    else:
                        _print1("treasure '{}':".format(treasure_section.id))
                        _print2("+ can possibly have no items in it")

            # Проверка правильности подсказки ("Обыскать тайник")
            if obj.custom_data.section_exist("logic"):
                if obj.custom_data.line_exist("logic", "cfg"):
                    cfg_obj = obj.custom_data.get_string("logic", "cfg")
                    cfg_std = "scripts\\treasure_inventory_box.ltx"
                    if cfg_obj != cfg_std:
                        _print1("treasure '{}':".format(treasure_section.id))
                        _print2("for treasures use another cfg reference")
                        _print2("(\"{}\")".format(cfg_std))
                else:
                    for cd_sect in obj.custom_data.sections():
                        if cd_sect.get_string("tips", "") == "st_search_treasure":
                            break
                    else:
                        _print1("treasure '{}':".format(treasure_section.id))
                        _print2("it doesn't seem to have a correct tip;")
                        _print2("[logic] is expected to have this line:")
                        _print2("tips = st_search_treasure")
            else:
                _print1("treasure '{}':".format(treasure_section.id))
                _print2("+ custom_data has no [logic]")
                _print2("; it should be provided at least for this:")
                _print2("; tips = st_search_treasure")

            # Проверка правильности используемой секции
            if iPv30:
                if obj.section_name != "inventory_box":
                    _print1("treasure '{}':".format(treasure_section.id))
                    _print2("+ section_name = {}".format(obj.section_name))
                    _print2("; use \"inventory_box\" instead")
        else:
            # non-treasure_manager object
            if obj.custom_data.section_exist("spawn_tm"):
                if iPv30:
                    _print1("object '{}':".format(obj.name))
                    _print2("+ not registered in treasure_manager")
                    _print2("+ custom_data has [spawn_tm]")
                    _print2("; use [spawn] instead")
            if obj._class == "O_INVBOX":  # inventory_box
                # Проверка правильности подсказки ("Обыскать")
                if obj.custom_data.section_exist("logic"):
                    if obj.custom_data.line_exist("logic", "cfg"):
                        cfg_obj = obj.custom_data.get_string("logic", "cfg")
                        cfg_err = "scripts\\treasure_inventory_box.ltx"
                        cfg_std = "scripts\\treasure_inventory_box_notm.ltx"
                        if cfg_obj == cfg_err:
                            _print1("object '{}':".format(obj.name))
                            _print2(
                                "for non-treasure storages use another cfg reference"
                            )
                            _print2("(\"{}\")".format(cfg_std))
                    else:
                        for cd_sect in obj.custom_data.sections():
                            if cd_sect.get_string("tips", "") == "st_search_treasure":
                                _print1("object '{}':".format(obj.name))
                                _print2("+ not a treasure")
                                _print2("+ seems to have treasure-specific tip on it")
                                break
    for treasure_id in treasure_manager_ini().ids():
        if treasure_id not in found_treasures:
            _print1("treasure '{}':".format(treasure_id))
            _print2("+ has no associated spawn object")

def _check_known_info() -> None:
    """Запрет на использование [known_info] в custom_data.

    Связано с тем, что action, прописанный внутри указанного инфопоршня,
    может вызываться несколько раз. Вместо этого используй ``ip_f.on_npc_corpse_used``.
    """
    for obj in get_spawn().objects():
        if obj.custom_data.section_exist("known_info"):
            _print1("object '{}':".format(obj.name))
            _print2("+ custom_data has [known_info]")
            _print2("; avoid using it")

def _check_space_restrictors() -> None:
    """Проверка имён зон на "префиксность".

    Проверка имён: у объекта cse_alife_space_restrictor, у которого
    restrictor_type - 0 или 2, имя не должно являться префиксом имени
    другого объекта cse_alife_space_restrictor. Обратный расклад чреват
    засорением лога, а также игнорированием мутантами аномальных зон.
    Для деталей см. ``report_39``.
    """
    ini_spawn = spawn_ini()
    trie = pygtrie.CharTrie()  # префиксное дерево
    zones = OrderedDict()
    for obj in get_spawn().objects():
        if ini_spawn.line_exist(obj._id, "restrictor_type"):
            trie[obj.name] = True
            rt = ini_spawn.get_uint(obj._id, "restrictor_type")
            if (rt == 0) or (rt == 2):
                zones[obj.name] = rt
    for zone_name, rt in zones.items():
        if trie.has_subtrie(zone_name):
            _print1("object '{}':".format(zone_name))
            _print2("+ restrictor_type = {}".format(rt))
            _print2("+ its name is a prefix of another restrictor's name")

def _check_box_wood_01() -> None:
    """Проверка наличия у деревянных коробок
    (``physics\\box\\box_wood_01``)
    секции [drop_box].

    *iP v3.0+*

    В противном случае их уничтожение не прибавит
    счётчик в достижении "Крушитель" (ИП v3.0)
    """
    iPv30 = meta_ini().get_bool("features", "iPv30", False)
    if not iPv30:
        return
    ini_spawn = spawn_ini()
    for obj in get_spawn().objects():
        if obj._class == "P_DSTRBL":  # physic_destroyable_object
            visual_name = ini_spawn.get_string(obj._id, "visual_name", "")
            if visual_name == "physics\\box\\box_wood_01":
                if not obj.custom_data.section_exist("drop_box"):
                    _print1("object '{}':".format(obj.name))
                    _print2("+ is a destroyable wooden box")
                    _print2("+ custom_data doesn't have [drop_box]")
                    _print2("; required by 'ip_a_boxcrusher'")

def _check_offline() -> None:
    """Проверка, не находится ли объект в оффлайне.
    """
    for obj in get_spawn().objects():
        if (obj.object_flags & OBJECT_FLAGS.flSwitchOnline) == 0:
            _print1("object '{}' is offline".format(obj.name))

def _check_visual() -> None:
    """Проверка корректности visual_name для инвентарных предметов.
    """
    ini_system = system_ini()
    ini_spawn = spawn_ini()
    for obj in get_spawn().objects():
        if len(ini_system.get_string(obj.section_name, "inv_name", "")) > 0:
            visual = ini_system.get_string(obj.section_name, "visual", "")
            visual_name = ini_spawn.get_string(obj._id, "visual_name", "")
            if visual.endswith(".ogf"):
                visual = visual[:-4]
            if visual_name.endswith(".ogf"):
                visual_name = visual_name[:-4]
            if visual != visual_name:
                _print1("object '{}':".format(obj.name))
                _print2("visual = {}".format(visual))
                _print2("visual_name = {}".format(visual_name))

def _invariant_names_as_prefixes() -> None:
    """ Инвариант: имя любого объекта не должно
    являться префиксом имени другого объекта.

    *iP v3.0+*
    
    Проверяемые имена:

    * **[1]** Имена изначально заспавненных объектов (all.spawn)
    * **[2]** Возможные имена заспавненных через скрипт объектов (section_name + id)

    Проверки:

    * [1]vs[1] - точная проверка
    * [1]vs[2] - проверка по избыточному условию
    * [2]vs[2] - не проверяется
    
    Инвариант экспериментальный. Скорее всего, он всё же бесполезный.
    """
    iPv30 = meta_ini().get_bool("features", "iPv30", False)
    if not iPv30:
        return
    trie_n = pygtrie.CharTrie()  # префиксное дерево имён всех объектов all.spawn
    trie_sn = pygtrie.CharTrie()  # префиксное дерево имён всех секций system.ltx
    names = []
    snames = []
    for obj in get_spawn().objects():
        trie_n[obj.name] = True
        names.append(obj.name)
    for sect in system_ini().sections():
        trie_sn[sect.id] = True
        snames.append(sect.id)
    # [1]vs[1]
    for name in names:
        if trie_n.has_subtrie(name):
            _print1("name '{}' is a prefix:".format(name))
            for k in trie_n.iterkeys(prefix=name):
                if k != name:
                    _print2("+ '{}'".format(k))
    # [1]vs[2] - 1/2
    for name in names:
        if trie_sn.has_subtrie(name):
            _print1("name '{}' is a prefix:".format(name))
            for k in trie_sn.iterkeys(prefix=name):
                if k != name:
                    _print2("+ section_name = {}".format(k))
    # [1]vs[2] - 2/2
    for sname in snames:
        if trie_n.has_subtrie(sname):
            not_safe = []
            for k in trie_n.iterkeys(prefix=sname):
                if str(k[len(sname):len(sname)+1]).isdigit():
                    not_safe.append(k)
            if len(not_safe) > 0:
                _print1("names below are not safe for section name '{}'".format(sname))
                for k in not_safe:
                    _print2("+ '{}'".format(k))

def _check_weapons_on_level() -> None:
    """Проверка наличия заспавненного на локации оружия,
    которое по умолчанию попадает под условия ``ip_cleaner``.

    *iP v3.0+*
    """
    iPv30 = meta_ini().get_bool("features", "iPv30", False)
    if not iPv30:
        return
    cleaner_cond__weapons = 0.899
    ini_meta = meta_ini()
    ini_spawn = spawn_ini()
    death_ini = Ini(_name="death_generic.ltx", ini_meta=ini_meta)
    death_ini.read(
        "config\\misc\\death_generic.ltx",
        inside_gamedata=True, encoding=None
    )
    for obj in get_spawn().objects():
        # Объект должен быть оружием
        if ini_meta.get_string("inv_class_to_type", obj._class, "") != "T_WPN":
            continue
        # Объект не должен быть квестовым
        if death_ini.get_string("keep_items", obj.section_name, "false") == "true":
            continue
        # Объект не должен иметь story_id
        if (obj.story_id is not None) and (-1 < obj.story_id < 65535):
            continue
        # Объект должен быть достаточно сломан
        if ini_spawn.get_number(obj._id, "condition", None) > cleaner_cond__weapons:
            continue
        # Объект попадает под условия ip_cleaner
        _print1("object '{}':".format(obj.name))
        _print2("can be removed by ip_cleaner.script")
        _print2(f"add story_id or increase condition (>{cleaner_cond__weapons:.3f})")

# ----------------------------------------------------------------

def inspect_spawn() -> None:
    """Ряд проверок на адекватность, правильность,
    консистентность, целостность данных спавна.
    """
    global _OK
    try:
        validate_data([
            meta_ini,
            system_ini,
            spawn_ini,
            game_ini,
            get_spawn,
            treasure_manager_ini,
        ])
    except Exception as e:
        print((
            f"{ANSI_COLOR_CODE.RED}"
            f"Can't initiate spawn inspection!"
            f"{ANSI_COLOR_CODE.DEF}"
        ), end="\n\n")
        _OK = False
    else:
        _check_name_duplicates()
        _check_level_correspondence()
        _check_upd_fields_consistency()
        _check_story_ids()
        _check_treasure_manager()
        _check_known_info()
        _check_space_restrictors()
        _check_box_wood_01()
        _check_offline()
        _check_visual()
        _invariant_names_as_prefixes()
        _check_weapons_on_level()
    finally:
        if _OK:
            print((
                f"[{os.path.basename(__file__)}] "
                f"{ANSI_COLOR_CODE.GREEN}OK{ANSI_COLOR_CODE.DEF}"
            ))
        print("", end="", flush=True)
