"""Валидатор игровых ресурсов."""

import re
from inspect import getdoc
from pathlib import Path

import pygtrie

from .db import OBJECT_FLAGS
from .ini import game_ini, meta_ini, spawn_ini, system_ini
from .ip_ltx import Ini, Section
from .misc.task_manager import TaskManager
from .misc.trade import TradeBuy
from .misc.treasure_manager import TreasureManager
from .spawn import get_spawn
from .utils import cast_safe
from .utils_inspector import InspectorStep, run_inspection
from .utils_meta import Levels, ServerClasses, ObjectTypeDetector, CLSIDs, ObjectType
from .xml_data.dialogs import Dialogs
from .xml_data.info_portions import InfoPortions
from .xml_data.string_table import StringTable
from .xml_data.texture_desc import TextureDesc

# ----------------------------------------------------------------

def _require_feature(flag: str):
    """Декоратор для отдельных проверок.

    :param flag: Проверка запустится только если
        указанный флаг установлен в ``[features]``.
    """
    def decorator(func):
        func.require_feature = flag
        return func
    return decorator

def _run_all_from_class(cls) -> None:
    """Поочерёдно запускает все проверки, определённые как методы указанного класса.

    Запускаются только методы, удовлетворяющие всем следующим условиям:

    * Это статический метод.
    * Имя метода начинается на ``test_``.
    * Выполнено условие, определённое декоратором :func:`_require_feature`.
    """
    ini_meta = meta_ini()
    for name, attr in cls.__dict__.items():
        if isinstance(attr, staticmethod) and name.startswith("test_"):
            func = attr.__func__
            if hasattr(func, "require_feature"):
                if not ini_meta.get_bool("features", func.require_feature, False):
                    continue
            doc = getdoc(func)
            label = " ".join(doc.split("\n\n")[0].split()) if doc else name
            with InspectorStep(label, raise_on_error=False) as step:
                func(step)

# ----------------------------------------------------------------

class InspectionsGeneral:
    """Набор проверок, которые автоматически запускаются из ``_inspection_st2_general``.
    """

    @staticmethod
    def test_task_manager_unlisted(step: InspectorStep):
        """Поиск незарегистрированных заданий task_manager.
        """
        task_manager = TaskManager()
        for s in task_manager.ini.sections():
            task_type = s.get_string("type", "")
            if (len(task_type) > 0) and (s.id not in task_manager):
                if task_type == "storyline":
                    step.error(f"Storyline task '{s.id}' is unlisted")
                else:
                    step.error(f"Task '{s.id}' is unlisted")
    
    @staticmethod
    def test_treasure_manager_unlisted(step: InspectorStep):
        """Поиск незарегистрированных тайников treasure_manager.
        """
        treasure_manager = TreasureManager()
        for s in treasure_manager.ini.sections():
            if s.line_exist("target") and (s.id not in treasure_manager):
                step.error(f"Treasure '{s.id}' is unlisted")

    @staticmethod
    @_require_feature("iPv30")
    def test_treasure_manager_sections(step: InspectorStep):
        """Проверка секций treasure_manager.ltx.
        """
        for s in TreasureManager().ini.sections():
            if s.id not in ["list", "lvl_condlist", "lvl_adjacent"]:
                try:
                    _ = s.get_uint("target")
                except Section.Error:
                    step.error(f"Unrecognized section: [{s.id}]")

    @staticmethod
    def test_translations(step: InspectorStep):
        """Проверка наличия переводов некоторых строк.
        """
        ST = StringTable()

        # task_manager
        msgs = []
        for task in TaskManager().generic_tasks():
            if len(task.text) == 0:
                msgs.append(f"[{task._id}] Пустое поле 'text'")
            elif task.text not in ST:
                msgs.append(f"[{task._id}] Для строки '{task.text}' нет перевода")
        if len(msgs) > 0:
            step.info("task_manager", header=True)
            for msg in msgs:
                step.error(msg)
        
        # treasure_manager
        msgs = []
        for treasure in TreasureManager():
            if len(treasure.name) == 0:
                msgs.append(
                    f"[{treasure._id}] Пустое поле 'name'"
                )
            elif treasure.name not in ST:
                msgs.append(
                    f"[{treasure._id}] Для строки '{treasure.name}' нет перевода"
                )
            if len(treasure.description) == 0:
                msgs.append(
                    f"[{treasure._id}] Пустое поле 'description'"
                )
            elif treasure.description not in ST:
                msgs.append(
                    f"[{treasure._id}] Для строки '{treasure.description}' нет перевода"
                )
        if len(msgs) > 0:
            step.info("treasure_manager", header=True)
            for msg in msgs:
                step.error(msg)
        
        # inventory items
        ini_meta = meta_ini()
        CLSIDS = CLSIDs()
        FIELDS = ["inv_name", "inv_name_short", "inv_name_desc", "description"]
        NO_ST_PATTERN = re.compile('[ "а-яА-Я]')
        found_no_st: dict[str, list[str]] = {}
        found_no_tr: dict[str, list[str]] = {}
        for s in system_ini().sections():
            if ini_meta.line_exist("ignore_sections", s.id):
                continue
            _class = s.get_string("class", "")
            if (len(_class) > 0) and (_class in CLSIDS) and CLSIDS.is_item(_class):
                for field in FIELDS:
                    value = s.get_string(field, "")
                    if (len(value) > 0):
                        if re.search(NO_ST_PATTERN, value):
                            found_no_st.setdefault(s.id, []).append(field)
                        elif (value not in ST):
                            found_no_tr.setdefault(s.id, []).append(value)
        if len(found_no_st) > 0:
            step.info(
                "В указанных полях секций инвентарных предметов",
                "текст записан напрямую, без использования переводов string_table",
                header=True
            )
            for section_name, fields in found_no_st.items():
                step.error("[{}] {}".format(
                    section_name,
                    ", ".join(fields)
                ))
        if len(found_no_tr) > 0:
            step.info(
                "Указанные строки используются в секциях инвентарных предметов,",
                "но для них нет перевода в string_table",
                header=True
            )
            for section_name, strings in found_no_tr.items():
                step.error("[{}] {}".format(
                    section_name,
                    ", ".join([f'"{s}"' for s in dict.fromkeys(strings)])
                ))

    @staticmethod
    def test_generate_name(step: InspectorStep):
        """Проверка наличия имён GENERATE_NAME.
        """
        ST = StringTable()
        sections = [
            s
            for s in system_ini().sections()
            if s.id.startswith("stalker_names_")
        ]
        for s in sections:
            subset = s.id[len("stalker_names_"):]
            try:
                fname_cnt = s.get_uint("name_cnt")
                lname_cnt = s.get_uint("last_name_cnt")
            except Section.Error as e:
                step.error(str(e))
            else:
                ITERATION_DATA = [
                    ("name_cnt", fname_cnt, "name_"),
                    ("last_name_cnt", lname_cnt, "lname_"),
                ]
                for field, cnt, prefix in ITERATION_DATA:
                    if cnt == 0:
                        step.error(f"[{s.id}] {field} = 0")
                        continue
                    not_found = []
                    for i in range(cnt):
                        string_id = f"{prefix}{subset}_{i}"
                        if string_id not in ST:
                            not_found.append(string_id)
                    if len(not_found) > 0:
                        step.error("[{}] These strings were not found:\n  {}{}".format(
                            s.id,
                            "\n  ".join(not_found[:10]),
                            "\n  ..." if (len(not_found) > 10) else ""
                        ))
    
    @staticmethod
    @_require_feature("iPv30")
    def test_ph_capture_visuals(step: InspectorStep):
        """Поиск инвентарных предметов в [ph_capture_visuals].
        """
        ini_meta = meta_ini()
        ini_system = system_ini()
        CLSIDS = CLSIDs()
        ph_capture_visuals: set[Path] = {
            Path(line).with_suffix(".ogf")
            for line in ini_system.section("ph_capture_visuals").lines()
        }
        found_inv_visuals: list[tuple[str, Path]] = []
        for s in ini_system.sections():
            if ini_meta.line_exist("ignore_sections", s.id):
                continue
            _class = s.get_string("class", "")
            if (len(_class) > 0) and (_class in CLSIDS) and CLSIDS.is_item(_class):
                _visual = s.get_string("visual", "")
                if (len(_visual) > 0):
                    _visual_path = Path(_visual).with_suffix(".ogf")
                    if _visual_path in ph_capture_visuals:
                        found_inv_visuals.append((s.id, _visual_path))
        if len(found_inv_visuals) > 0:
            step.info("Визуалы инвентарных предметов обнаружены в [ph_capture_visuals]")
            step.info((
                "Это значит, что для предмета будет высвечена подсказка о\n"
                "  перетаскивании, хотя на деле таскать его будет невозможно."
            ))
            for section_name, visual_path in found_inv_visuals:
                step.error(f"[{section_name}] {visual_path}")

    @staticmethod
    @_require_feature("iPv30")
    def test_section_name_patterns(step: InspectorStep):
        """Проверка имён секций инвентарных предметов.
        """
        PATTERNS_BY_TYPE = {
            ObjectType.ITEM_ART:        r"^af_",
            ObjectType.ITEM_AMMO:       r"^ammo_",
            ObjectType.ITEM_GRENADE:    r"^grenade_",
            ObjectType.ITEM_ADDON:      r"^wpn_addon_",
            ObjectType.ITEM_WEAPON:     r"^wpn_",
            ObjectType.ITEM_OUTFIT:     r"_outfit$",
        }
        ini_meta = meta_ini()
        CLSIDS = CLSIDs()
        irregular_sections: list[tuple[str, ObjectType]] = []
        for s in system_ini().sections():
            if ini_meta.line_exist("ignore_sections", s.id):
                continue
            _class = s.get_string("class", "")
            if (len(_class) > 0) and (_class in CLSIDS):
                _type = CLSIDS.get_object_type(_class)
                if _type in PATTERNS_BY_TYPE:
                    if re.search(PATTERNS_BY_TYPE[_type], s.id) is None:
                        irregular_sections.append((s.id, _type))
        if len(irregular_sections) > 0:
            step.info("Обнаружены секции с неверным форматом имени")
            step.info((
                "Такие секции не будут распознаны как нужный\n"
                "  тип предмета в конфиге торговли"
            ))
            for section_name, _type in irregular_sections:
                step.error(f"[{section_name}] - {_type.name}")

    @staticmethod
    @_require_feature("iPv30")
    def test_inv_name_desc(step: InspectorStep):
        """Проверка сокращённых имён боеприпасов и аддонов.
        """
        ini_meta = meta_ini()
        ini_system = system_ini()
        CLSIDS = CLSIDs()
        sections_without_alias: list[str] = []
        for s in ini_system.sections():
            if ini_meta.line_exist("ignore_sections", s.id):
                continue
            _class = s.get_string("class", "")
            if (len(_class) > 0) and (_class in CLSIDS):
                if CLSIDS.is_ammo(_class) or CLSIDS.is_weapon_addon(_class):
                    if (
                        not s.line_exist_own("inv_name_desc")
                        or len(s.get_string("inv_name_desc")) == 0
                    ):
                        sections_without_alias.append(s.id)
        if len(sections_without_alias) > 0:
            step.info("Обнаружены секции беоприпасов/аддонов без `inv_name_desc`")
            step.info(
                "Эта строка используется при динамической генерации описания оружия"
            )
            for section_name in sections_without_alias:
                step.error(f"[{section_name}]")

# ----------------------------------------------------------------

class InspectionsSpawn:
    """Набор проверок, которые автоматически запускаются из ``_inspection_st3_spawn``.
    """

    @staticmethod
    def test_name_duplicates(step: InspectorStep):
        """Проверка на отсутствие дубликатов name.
        
        Если отключен флаг ``inspector_pedantic``,
        то ищет дубликаты только в рамках одной локации.
        """
        pedantic = meta_ini().get_bool("features", "inspector_pedantic", False)
        d: dict[tuple[str, str], list[str]] = {}
        for obj in get_spawn().objects():
            if re.match(r"^meshes\\brkbl#\d+\.ogf$", obj.name) is not None:
                # У breakable_object могут совпадать имена
                # Такой формат имени необходим для совместимости с X-Ray SDK
                continue
            level_key = obj._level if not pedantic else ""
            d.setdefault((level_key, obj.name), []).append(obj._id)
        d = {key: ids for key, ids in d.items() if len(ids) > 1}
        if len(d) > 0:
            if pedantic:
                step.info((
                    "Обнаружены дубликаты name\n"
                    "  при поиске по всем локациям."
                ))
                step.info((
                    "Дубликаты name могут приводить к нестабильным безлоговым\n"
                    "  вылетам при загрузке сохранения, в том числе\n"
                    "  при переходе на другую локацию."
                ))
                for key, ids in d.items():
                    _, name = key
                    step.error("name = {}{}{}".format(
                        name,
                        "".join([f"\n  [{id}]" for id in ids[:3]]),
                        "\n  ..." if (len(ids) > 3) else ""
                    ))
            else:
                step.info((
                    "Обнаружены дубликаты name\n"
                    "  при поиске по каждой отдельной локации."
                ))
                step.info((
                    "Дубликаты name могут приводить к нестабильным безлоговым\n"
                    "  вылетам при загрузке сохранения, в том числе\n"
                    "  при переходе на другую локацию."
                ))
                for key, ids in d.items():
                    level, name = key
                    step.error("{} | name = {}{}".format(
                        level, name,
                        "".join([f"\n  [{id}]" for id in ids])
                    ))

    @staticmethod
    def test_level_correspondence(step: InspectorStep):
        """Объекты прописаны в файлах соответствующих локаций.
        """
        for obj in get_spawn().objects():
            if (len(obj._src) > 0) and (obj._src.find(obj._level) < 0):
                step.error((
                    f"object '{obj.name}' is on level '{obj._level}',"
                    f"\n  but defined in '{obj._src}'"
                ))

    @staticmethod
    def test_upd_fields_consistency(step: InspectorStep):
        """Значения указанных полей state и update совпадают.
        
        ``health == upd:health``, ``position == upd:position``,
        ``g_team == upd:g_team``, ...

        Если в секции ``[features]`` не установлен флаг ``universal_acdc``,
        то значение поля ``upd:condition`` перед сравнением с ``condition``
        делится на 255 (для совместимости со старой версией ACDC).
        """
        upd_condition_f32 = meta_ini().get_bool("features", "universal_acdc", False)
        for section in spawn_ini().sections():
            lines = []
            for k, v in section.fields():
                if k.startswith("upd:"):
                    continue
                updk = "upd:" + k
                if section.line_exist(updk):
                    updv = section.field(updk)
                    unequal = False
                    if (k == "condition"):
                        vf = cast_safe(v, float, defval=None)
                        updvf = cast_safe(updv, float, defval=None)
                        if (vf is None) or (updvf is None):
                            unequal = True
                        else:
                            if not upd_condition_f32:
                                updvf = updvf / 255
                            unequal = (abs(vf - updvf) > 0.01)
                    else:
                        unequal = (v != updv)
                    if unequal:
                        lines.append("    {}{}".format(
                            k, " = {}".format(v) if (v is not None) else ""
                        ))
                        lines.append("{}{}".format(
                            updk, " = {}".format(updv) if (updv is not None) else ""
                        ))
            if len(lines) > 0:
                step.error("object [{}] ('{}'):\n  {}".format(
                    section.id,
                    section.get_string("name", "?"),
                    "\n  ".join(lines)
                ))

    @staticmethod
    def test_story_ids_miscellaneous(step: InspectorStep):
        """Различные проверки story_id.

        * Отсутствие дубликатов
        * Проверка адекватности значения (``0 < int < 65535``)
        * Проверка зарегистрированности в ``[story_ids]``
        """
        story_ids: set[int] = {
            int(sid) for sid in game_ini().section("story_ids").lines()
        }
        d = {}
        for obj in get_spawn().objects():
            if obj.story_id != -1:
                d.setdefault(obj.story_id, []).append(obj._id)
                if not (0 < obj.story_id < 65535):
                    step.error((
                        f"object [{obj._id}] ('{obj.name}'):"
                        f"\n  story_id = {obj.story_id}  ; strange value"
                    ))
                elif obj.story_id not in story_ids:
                    step.error((
                        f"object [{obj._id}] ('{obj.name}'):"
                        f"\n  story_id = {obj.story_id}  ; unregistered value"
                    ))
        for sid, ids in d.items():
            if len(ids) > 1:
                step.error("story_id '{}' is used more than once:{}".format(
                    sid,
                    "".join([f"\n  + [{id}]" for id in ids])
                ))

    @staticmethod
    @_require_feature("inspector_pedantic")
    def test_story_ids_unused(step: InspectorStep):
        """Поиск неиспользованных story_id.
        """
        used_sids: set[int] = {
            obj.story_id
            for obj in get_spawn().objects()
            if obj.story_id != -1
        }
        used_sids.add(65535)
        unused_sids: dict[int, str] = {
            int(story_id): (label or "")
            for story_id, label in game_ini().section("story_ids").fields()
            if int(story_id) not in used_sids
        }
        for sid, label in unused_sids.items():
            step.error(f"{sid} = {label}")

    @staticmethod
    def test_treasure_manager(step: InspectorStep):
        """Различные проверки treasure_manager.

        * Отсутствие тайников без соответствующего объекта в спавне
        * *(iP v2.0+)* Отсутствие тайников с пустым лутом
        * *(iP v2.0+)* Отсутствие тайников с потенциально пустым лутом:
          технически тайнику прописаны предметы,
          но если на всех них висит параметр prob,
          то возможна ситуация, что в игре тайник окажется пустым.
        * *(iP v3.0+)* [spawn] vs [spawn_tm]:
          подразумевается, что [spawn_tm] используется только тайниками,
          которые в свою очередь не используют [spawn].
        * *(iP v3.0+)* Все тайники должны использовать строго секцию inventory_box;
          иначе не будут срабатывать необходимые
          колбеки в ``bind_physic_object.script``.
        """
        iPv20 = meta_ini().get_bool("features", "iPv20", False)
        iPv30 = meta_ini().get_bool("features", "iPv30", False)
        TM = TreasureManager()
        found_treasures = {}
        for obj in get_spawn().objects():
            treasure = TM[obj.story_id] if (obj.story_id in TM) else None
            if treasure is not None:
                # registered in treasure_manager
                found_treasures[treasure._id] = True
                has_spawn = obj.custom_data.section_exist("spawn")
                has_spawn_tm = obj.custom_data.section_exist("spawn_tm")
                if not has_spawn and not has_spawn_tm:
                    if iPv20:
                        step.error(
                            f"treasure '{treasure._id}':",
                            "custom_data has neither [spawn] nor [spawn_tm]"
                        )
                else:
                    if has_spawn:
                        if iPv30:
                            step.error(
                                f"treasure '{treasure._id}':",
                                "custom_data has [spawn]; use [spawn_tm] instead"
                            )
                    if len(obj._loot) == 0:
                        if iPv20:
                            step.error(
                                f"treasure '{treasure._id}':",
                                "has no items"
                            )
                    else:
                        for se in obj._loot.entries():
                            g = True
                            g = g and (se.count > 0)
                            g = g and ((se.box_size is None) or (se.box_size > 0))
                            g = g and ((se.prob is None) or (se.prob == 100))
                            if g:
                                break
                        else:
                            step.error(
                                f"treasure '{treasure._id}':",
                                "can possibly have no items in it"
                            )

                # Проверка правильности используемой секции
                if iPv30:
                    if obj.section_name != "inventory_box":
                        step.error(
                            f"treasure '{treasure._id}':",
                            f"section_name = {obj.section_name}",
                            "use \"inventory_box\" instead"
                        )
            else:
                # non-treasure_manager object
                if obj.custom_data.section_exist("spawn_tm"):
                    if iPv30:
                        step.error(
                            f"object '{obj.name}':",
                            "not registered in treasure_manager, but has [spawn_tm]",
                            "use [spawn] instead"
                        )
        for treasure in TM:
            if treasure._id not in found_treasures:
                step.error(
                    f"treasure '{treasure._id}':",
                    "has no associated spawn object"
                )

    @staticmethod
    @_require_feature("inspector_pedantic")
    def test_storage_tips(step: InspectorStep):
        """Проверка надписей при наведении на хранилища.

        Правильная подсказка при наведении на ``inventory_box``:
        на обычном ``inventory_box``, который не является тайником,
        не должно быть подсказки "Обыскать тайник" (``st_search_treasure``);
        и наоборот, на тайниках должна быть только эта подсказка.

        Заодно проверяется наличие ``[logic]`` у тайников.
        """
        TM = TreasureManager()
        for obj in get_spawn().objects():
            if (obj.story_id != -1) and (obj.story_id in TM):
                # Проверка правильности подсказки ("Обыскать тайник")
                treasure = TM[obj.story_id]
                if obj.custom_data.section_exist("logic"):
                    if obj.custom_data.line_exist("logic", "cfg"):
                        cfg_obj = obj.custom_data.get_string("logic", "cfg")
                        cfg_std = "scripts\\treasure_inventory_box.ltx"
                        if cfg_obj != cfg_std:
                            step.error(
                                f"treasure '{treasure._id}':",
                                "for treasures use another cfg reference",
                                f"(\"{cfg_std}\")"
                            )
                    else:
                        for cd_sect in obj.custom_data.sections():
                            if cd_sect.get_string("tips", "") == "st_search_treasure":
                                break
                        else:
                            step.error(
                                f"treasure '{treasure._id}':",
                                "it doesn't seem to have a correct tip;",
                                "[logic] is expected to have this line:",
                                "tips = st_search_treasure"
                            )
                else:
                    step.error(
                        f"treasure '{treasure._id}':",
                        "custom_data has no [logic];",
                        "it should be provided at least for this:",
                        "tips = st_search_treasure"
                    )
            elif obj._class == "O_INVBOX":  # inventory_box
                # Проверка правильности подсказки ("Обыскать")
                if obj.custom_data.section_exist("logic"):
                    if obj.custom_data.line_exist("logic", "cfg"):
                        cfg_obj = obj.custom_data.get_string("logic", "cfg")
                        cfg_err = "scripts\\treasure_inventory_box.ltx"
                        cfg_std = "scripts\\treasure_inventory_box_notm.ltx"
                        if cfg_obj == cfg_err:
                            step.error(
                                f"object '{obj.name}':",
                                "for non-treasure storages use another cfg reference",
                                f"(\"{cfg_std}\")"
                            )
                    else:
                        for cd_sect in obj.custom_data.sections():
                            if cd_sect.get_string("tips", "") == "st_search_treasure":
                                step.error(
                                    f"object '{obj.name}':",
                                    "+ not a treasure",
                                    "+ seems to have treasure-specific tip on it"
                                )
                                break

    @staticmethod
    def test_known_info(step: InspectorStep):
        """Проверка [known_info] в custom_data объектов.

        В ``[known_info]`` нельзя использовать инфопоршни с ``<action>``,
        потому что укзанная функция может вызваться при попытке повторной выдачи
        инфопоршня, что иногда происходит, например, при перезаходе на локацию.
        Вместо ``<action>`` рекомендуется использовать кастомную скриптовую проверку
        (для ИП: ``ip_f.on_npc_corpse_used``).

        Если установлен флаг ``inspector_pedantic``, то запрещается
        использование секции ``[known_info]`` вообще.
        """
        pedantic = meta_ini().get_bool("features", "inspector_pedantic", False)
        if pedantic:
            having_any: list[tuple[str, str]] = []
            for obj in get_spawn().objects():
                if obj.custom_data.section_exist("known_info"):
                    having_any.append((obj._id, obj.name))
            if len(having_any) > 0:
                step.info(
                    "Не рекомендуется использовать секцию [known_info].",
                    "Ниже - список объектов, у которых она была обнаружена.",
                )
                for _id, _name in having_any:
                    step.error(f"object [{_id}] ('{_name}')")
        else:
            IP = InfoPortions()
            having_action: list[tuple[str, str, str]] = []
            for obj in get_spawn().objects():
                if obj.custom_data.section_exist("known_info"):
                    for info in obj.custom_data.section("known_info").lines():
                        if (info in IP) and (len(IP[info].action) > 0):
                            having_action.append((obj._id, obj.name, info))
            if len(having_action) > 0:
                step.info(
                    "Не рекомендуется прописывать infoportion с <action>",
                    "в секцию [known_info], т.к. укзанная функция может вызваться",
                    "при попытке повторной выдачи инфопоршня, что иногда происходит,",
                    "например, при перезаходе на локацию",
                )
                for _id, _name, _info in having_action:
                    step.error(
                        f"object [{_id}] ('{_name}')",
                        f"info_portion: '{_info}'"
                    )

    @staticmethod
    def test_space_restrictors(step: InspectorStep):
        """Проверка имён зон на "префиксность".

        Проверка имён: у объекта cse_alife_space_restrictor, у которого
        restrictor_type - 0 или 2, имя не должно являться префиксом имени
        другого объекта cse_alife_space_restrictor. Обратный расклад чреват
        засорением лога, а также игнорированием мутантами аномальных зон.
        Для деталей см. ``report_39``.

        Если не установлен флаг ``inspector_pedantic``, то
        под проверку попадают только аномальные зоны.
        """
        pedantic = meta_ini().get_bool("features", "inspector_pedantic", False)
        ini_spawn = spawn_ini()
        CLSIDS = CLSIDs()
        trie = pygtrie.CharTrie()  # префиксное дерево
        zones_all: list[tuple[str, str]] = []
        for obj in get_spawn().objects():
            if ini_spawn.line_exist(obj._id, "restrictor_type"):
                if pedantic or CLSIDS.is_anomaly(obj._class):
                    trie[obj.name] = True
                    rt = ini_spawn.get_uint(obj._id, "restrictor_type")
                    if (rt == 0) or (rt == 2):
                        zones_all.append((obj._id, obj.name))
        zones_prefixes = [
            (_id, _name) for _id, _name in zones_all if trie.has_subtrie(_name)
        ]
        if len(zones_prefixes) > 0:
            if pedantic:
                step.info(
                    "Обнаружены зоны (cse_alife_space_restrictor)",
                    "с типом 0 и/или 2 (restrictor_type),",
                    "имя которых является префиксом имени другой зоны."
                )
            else:
                step.info(
                    "Обнаружены аномальные зоны с типом 0 и/или 2 (restrictor_type),",
                    "имя которых является префиксом имени другой аномалии."
                )
            step.info(
                "Это чревато засорением лога,",
                "а также игнорированием мутантами аномалий."
            )
            for _id, _name in zones_prefixes:
                step.error(f"object [{_id}] ('{_name}')")

    @staticmethod
    @_require_feature("iPv30")
    def test_box_wood_01(step: InspectorStep):
        """Проверка наличия у деревянных коробок секции [drop_box].

        ``physics\\box\\box_wood_01``

        Без этой секции их уничтожение не прибавит
        счётчик в достижении "Крушитель" (ИП v3.0)
        """
        ini_spawn = spawn_ini()
        VISUAL_BOX_WOOD_01 = Path("physics\\box\\box_wood_01")
        found: list[tuple[str, str]] = []
        for obj in get_spawn().objects():
            if obj._class == "P_DSTRBL":  # physic_destroyable_object
                visual_name = ini_spawn.get_string(obj._id, "visual_name", "")
                visual_path = Path(visual_name).with_suffix("")
                if visual_path == VISUAL_BOX_WOOD_01:
                    if not obj.custom_data.section_exist("drop_box"):
                        found.append((obj._id, obj.name))
        if len(found) > 0:
            step.info("Обнаружены разрушаемые деревянные коробки без [drop_box]")
            step.info("Наличие этой секции необходимо для достижения 'ip_a_boxcrusher'")
            for _id, _name in found:
                step.error(f"object [{_id}] ('{_name}')")

    @staticmethod
    def test_offline_objects(step: InspectorStep):
        """Поиск объектов в оффлайне.
        """
        for obj in get_spawn().objects():
            if (obj.object_flags & OBJECT_FLAGS.flSwitchOnline) == 0:
                step.error(f"object [{obj._id}] ('{obj.name}') is offline")

    @staticmethod
    def test_inv_items_visual(step: InspectorStep):
        """Проверка visual_name у инвентарных предметов.
        """
        ini_system = system_ini()
        ini_spawn = spawn_ini()
        first_error: bool = True
        for obj in get_spawn().objects():
            if obj._type.is_item():
                visual_cfg = ini_system.get_string(obj.section_name, "visual", "")
                visual_spw = ini_spawn.get_string(obj._id, "visual_name", "")
                if (len(visual_cfg) > 0) and (len(visual_spw) > 0):
                    visual_cfg_path = Path(visual_cfg).with_suffix("")
                    visual_spw_path = Path(visual_spw).with_suffix("")
                    if visual_cfg_path != visual_spw_path:
                        if first_error:
                            step.info(
                                "Обнаружены инвентарные предметы, у которых",
                                "визуал из спавна не совпадает с визуалом из конфига."
                            )
                            first_error = False
                        step.error(
                            f"object [{obj._id}] ('{obj.name}'):",
                            f"section_name = {obj.section_name}",
                            f"visual (config): {visual_cfg_path}",
                            f"visual (spawn):  {visual_spw_path}"
                        )

    @staticmethod
    @_require_feature("iPv30")
    def test_invariant_names_as_prefixes(step: InspectorStep):
        """Запрет на префиксность имён любых объектов.
        
        Экспериментальный инвариант: имя любого объекта не должно
        являться префиксом имени другого объекта.
        
        Проверяемые имена:

        * **[1]** Имена изначально заспавненных объектов (all.spawn)
        * **[2]** Возможные имена заспавненных через скрипт объектов (section_name + id)

        Проверки:

        * [1]vs[1] - точная проверка
        * [1]vs[2] - проверка по избыточному условию
        * [2]vs[2] - не проверяется
        """
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
                step.error(
                    f"name '{name}' is a prefix of these names:",
                    *[f"+ '{k}'" for k in trie_n.iterkeys(prefix=name) if k != name]
                )
        # [1]vs[2] - 1/2
        for name in names:
            if trie_sn.has_subtrie(name) or trie_sn.has_key(name):
                step.error(
                    f"name '{name}' is a prefix:",
                    *[
                        f"+ section_name = {k}"
                        for k in trie_sn.iterkeys(prefix=name)
                    ]
                )
        # [1]vs[2] - 2/2
        for sname in snames:
            if trie_n.has_subtrie(sname):
                not_safe = [
                    k for k in trie_n.iterkeys(prefix=sname)
                    if str(k[len(sname):len(sname)+1]).isdecimal()
                ]
                if len(not_safe) > 0:
                    step.error(
                        f"names below are not safe for section name '{sname}':",
                        *[f"+ '{k}'" for k in not_safe]
                    )

    @staticmethod
    @_require_feature("iPv30")
    def test_cond_weapons_on_level(step: InspectorStep):
        """Проверка condition у оружия (ip_cleaner).
        
        Проверка наличия заспавненного на локации оружия,
        которое по умолчанию попадает под условия ``ip_cleaner``.
        """
        CLEANER_COND__WEAPONS = 0.899
        death_ini = Ini(name="death_generic.ltx", ini_meta=meta_ini())
        death_ini.read(
            "config\\misc\\death_generic.ltx",
            inside_gamedata=True
        )
        first_error: bool = True
        for obj in get_spawn().objects():
            # Объект должен быть оружием
            if obj._type != ObjectType.ITEM_WEAPON:
                continue
            # Объект не должен быть квестовым
            if death_ini.get_bool("keep_items", obj.section_name, False):
                continue
            # Объект не должен иметь story_id
            if (obj.story_id is not None) and (-1 < obj.story_id < 65535):
                continue
            # Объект должен быть достаточно сломан
            if obj.get_condition() > CLEANER_COND__WEAPONS:
                continue
            # Объект попадает под условия ip_cleaner
            if first_error:
                step.info(
                    "Обнаружено оружие вне хранилища, попадающее под условия ip_cleaner"
                )
                step.info((
                    "Необходимо добавить story_id"
                    f" или увеличить condition (>{CLEANER_COND__WEAPONS:.3f})"
                ))
                first_error = False
            step.error(f"object [{obj._id}] ('{obj.name}')")

# ----------------------------------------------------------------

def _inspection_st1_init() -> None:
    """Первая стадия валидации: инициализация данных."""
    with InspectorStep("Инициализация meta_ini") as step:
        ini_meta = meta_ini()
        ini_test = Ini(name="test_ini", ini_meta=ini_meta)
        step.info(f"MOD: {ini_test.gdm}")
        step.info(f"ALT: {ini_test.gda or "--"}")

    with InspectorStep("Инициализация game_ini") as step:
        ini_system = game_ini()

    with InspectorStep("Инициализация system_ini") as step:
        ini_system = system_ini()

    with InspectorStep("Инициализация данных о локациях") as step:
        LEVELS = Levels()

    with InspectorStep("Инициализация данных об игровых классах и CLSID") as step:
        SC = ServerClasses()
        OTD = ObjectTypeDetector()
        CLSIDS = CLSIDs()

    with InspectorStep("Инициализация XML-данных") as step:
        D = Dialogs()
        IP = InfoPortions()
        ST = StringTable()
        TD = TextureDesc()

    with InspectorStep("Инициализация данных task_manager") as step:
        task_manager = TaskManager()

    with InspectorStep("Инициализация данных о торговле") as step:
        trade = TradeBuy()

    with InspectorStep("Инициализация данных treasure_manager") as step:
        treasure_manager = TreasureManager()

    with InspectorStep("Инициализация данных all.spawn") as step:
        ini_spawn = spawn_ini()
        if len(ini_spawn.sections()) == 0:
            step.warn("[spawn] Нет данных о спавне")
        spawn = get_spawn()

def _inspection_st2_general() -> None:
    """Вторая стадия валидации: общие проверки."""
    _run_all_from_class(InspectionsGeneral)

def _inspection_st3_spawn() -> None:
    """Третья стадия валидации: ``all.spawn``."""
    with InspectorStep(
        "Старт валидации данных all.spawn",
        raise_on_error=False
    ) as step:
        if len(spawn_ini().sections()) == 0:
            step.error("Прервано, т.к. нет данных о спавне")
            return
    _run_all_from_class(InspectionsSpawn)

# ----------------------------------------------------------------

def inspect(show_stderr: bool = False, show_traceback: bool = False) -> None:
    """Основная функция для запуска проверки/валидации игровых ресурсов.

    :param show_stderr: Вывести ли сообщения из ``stderr``,
        собранные в процессе проверки.
    :param show_traceback: Выводить ли traceback исключения,
        которое может возникнуть в процессе проверки.
    """
    run_inspection(
        [
            _inspection_st1_init,
            _inspection_st2_general,
            _inspection_st3_spawn,
        ],
        show_stderr=show_stderr,
        show_traceback=show_traceback
    )
