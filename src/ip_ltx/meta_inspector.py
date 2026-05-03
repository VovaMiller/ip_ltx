"""Помощник для настройки основного конфигурационного файла программы."""

import io
import re
import traceback
from collections.abc import Callable
from contextlib import redirect_stderr
from dataclasses import dataclass
from enum import auto, Enum

from .ini import game_ini, meta_ini, spawn_ini, system_ini
from .ip_ltx import Ini, Section
from .spawn import get_spawn
from .spawn_entries_collector import SpawnEntriesCollector
from .trade import get_buy_k
from .treasure_manager import treasure_manager_ini
from .utils import ANSI_COLOR_CODE
from .utils_meta import Levels, ServerClasses, ObjectTypeDetector, CLSIDs, ObjectType
from .xml_data.string_table import StringTable


class InspectorError(Exception):
    """Вызывается при критической ошибке в конфигурации."""
    pass

class InspectorStep:
    LINE_WIDTH = 64

    log_info: list[str]
    log_warning: list[str]
    log_error: list[str]
    intro_width: int

    def __init__(self, msg: str):
        self.log_info = []
        self.log_warning = []
        self.log_error = []
        self.intro_width = len(msg) + 3
        print(msg, "...", sep="", end="")

    def __enter__(self):
        return self
    
    def info(self, msg: str):
        """Вывести серое сообщение с доп. информацией."""
        self.log_info.append(msg)

    def warn(self, msg: str):
        """Вывести жёлтое сообщение-предупреждение."""
        self.log_warning.append(msg)
    
    def error(self, msg: str):
        """Вывести красное сообщение об ошибке.

        При наличии хотя бы одного такого сообщения на выходе
        из контексного менеджера будет вызвано исключение.

        В отличие прямого вызова исключения, позволяет вывести несколько ошибок сразу.
        """
        self.log_error.append(msg)
    
    def __exit__(self, exc_type, exc, tb):
        res_clr = (
            ANSI_COLOR_CODE.RED if (exc_type is not None) or (len(self.log_error) > 0)
            else ANSI_COLOR_CODE.YELLOW if (len(self.log_warning) > 0)
            else ANSI_COLOR_CODE.GREEN
        )
        res_txt = "OK" if (exc_type is None) and (len(self.log_error) == 0) else "FAIL"
        dots = max(0, self.LINE_WIDTH - self.intro_width - len(res_txt))
        print(f"{"."*dots}{res_clr}{res_txt}{ANSI_COLOR_CODE.DEF}")
        if (
            (len(self.log_info) > 0)
            or (len(self.log_warning) > 0)
            or (len(self.log_error) > 0)
            or (exc_type is not None)
        ):
            print("")
            for msg in self.log_info:
                print(f"{ANSI_COLOR_CODE.BLACK}* {msg}{ANSI_COLOR_CODE.DEF}")
                # print(f"* {ANSI_COLOR_CODE.WHITE}{msg}{ANSI_COLOR_CODE.DEF}")
            for msg in self.log_warning:
                print(f"{ANSI_COLOR_CODE.YELLOW}~ {msg}{ANSI_COLOR_CODE.DEF}")
            for msg in self.log_error:
                print(f"{ANSI_COLOR_CODE.RED}! {msg}{ANSI_COLOR_CODE.DEF}")
            if exc_type is not None:
                print(f"{ANSI_COLOR_CODE.RED}! {exc}{ANSI_COLOR_CODE.DEF}")
            print("")
        if exc_type is not None:
            raise InspectorError() from exc
        if len(self.log_error) > 0:
            raise InspectorError()


def _inspector_pipeline() -> None:
    """Полная проверка настройки основного конфигурационного файла (``meta.ltx``).

    :raises InspectorError: при критической ошибке в конфигурации.
    """
    with InspectorStep("Инициализация конфигурации (meta_ini)") as step:
        ini_meta = meta_ini()

    with InspectorStep("Проверка директорий игровых ресурсов") as step:
        # [settings]
        ini_test = Ini(name="test_ini", ini_meta=ini_meta)

        step.info(f"MOD: {ini_test.gdm}")
        step.info(f"ALT: {ini_test.gda or "--"}")

    with InspectorStep("Проверка базовых секций") as step:
        # [features]
        s = ini_meta.section("features")
        lines = ["iPv20", "iPv30", "universal_acdc"]
        for line in lines:
            if s.line_exist(line):
                _ = s.get_bool(line)
            else:
                step.warn(f"[{s.id}] Не хватает флага '{line}'")
        
        # [is_anomaly2]
        s = ini_meta.section("is_anomaly2")
        if len(s.lines()) == 0:
            step.warn(f"[{s.id}] Пустая секция")
        
        # [ignore_sections]
        s = ini_meta.section("ignore_sections")

        # [acdc@*]
        if not ini_meta.section_exist("acdc@ignore"):
            step.warn("Не найдена секция [acdc@ignore]")
        if not ini_meta.section_exist("acdc@conversion"):
            step.warn("Не найдена секция [acdc@conversion]")

        # [universal_acdc@*]
        if not ini_meta.section_exist("universal_acdc@ignore"):
            step.warn("Не найдена секция [universal_acdc@ignore]")
        if not ini_meta.section_exist("universal_acdc@ignore"):
            step.warn("Не найдена секция [universal_acdc@ignore]")

    with InspectorStep("Инициализация данных об игровых классах и CLSID") as step:
        SC = ServerClasses()
        OTD = ObjectTypeDetector()
        CLSIDS = CLSIDs()

    with InspectorStep("Инициализация system_ini") as step:
        ini_system = system_ini()

    with InspectorStep("Поиск незарегистрированных CLSID") as step:
        unregistered: dict[str, list[str]] = {}
        for section in ini_system.sections():
            _class = section.get_string("class", "")
            if (len(_class) > 0) and (_class not in CLSIDS):
                unregistered.setdefault(_class, []).append(section.id)
        for clsid, sections in unregistered.items():
            step.error("{}:{} {}{}".format(
                clsid,
                " "*(max(0, 8 - len(clsid))),
                ", ".join(sections[:3]),
                ", ..." if (len(sections) > 3) else ""
            ))

    with InspectorStep("Инициализация game_ini") as step:
        ini_game = game_ini()

    with InspectorStep("Инициализация таблицы переводов (string_table)") as step:
        ST = StringTable()

    with InspectorStep("Инициализация данных о локациях") as step:
        LEVELS = Levels()

    with InspectorStep("Инициализация данных о коэффициентах торговли") as step:
        _ = get_buy_k("bread")

    with InspectorStep("Инициализация данных о тайниках") as step:
        ini_treasure_manager = treasure_manager_ini()

    with InspectorStep("Инициализация данных о спавне (all.spawn)") as step:
        ini_spawn = spawn_ini()
        if len(ini_spawn.sections()) == 0:
            step.warn("[spawn] Нет данных о спавне")
        spawn = get_spawn()

    if len(ini_spawn.sections()) > 0:
        with InspectorStep("Проверка формата данных all.spawn") as step:
            class SpawnDataType(Enum):
                OLD_ACDC = auto()
                UNIVERSAL_ACDC = auto()
                AMBIGUOUS = auto()

            _type_flag = (
                SpawnDataType.UNIVERSAL_ACDC
                if ini_meta.get_bool("features", "universal_acdc", False)
                else SpawnDataType.OLD_ACDC
            )
            _type_global = None

            # upd:condition
            if _type_global != SpawnDataType.AMBIGUOUS:
                for s in ini_spawn.sections():
                    if s.line_exist_with_value("upd:condition"):
                        vs = s.get_string("upd:condition")
                        vi = Section.cast_int(vs)
                        vf = Section.cast_float(vs)
                        _type_local = (
                            SpawnDataType.UNIVERSAL_ACDC
                            if (vi is None) and (vf is not None)
                            else SpawnDataType.OLD_ACDC
                            if (vi is not None) and (vi > 10)
                            else None
                        )
                        if _type_local is not None:
                            if _type_global is None:
                                _type_global = _type_local
                            elif _type_global != _type_local:
                                _type_global = SpawnDataType.AMBIGUOUS
                                break

            # spawn_id
            if _type_global != SpawnDataType.AMBIGUOUS:
                for s in ini_spawn.sections():
                    _type_local = (
                        SpawnDataType.UNIVERSAL_ACDC
                        if s.line_exist("spawn_id")
                        else SpawnDataType.OLD_ACDC
                    )
                    if _type_global is None:
                        _type_global = _type_local
                    elif _type_global != _type_local:
                        _type_global = SpawnDataType.AMBIGUOUS
                        break

            if (_type_global is None) or (_type_global == SpawnDataType.AMBIGUOUS):
                step.warn("Не удалось определить формат данных all.spawn")
            elif _type_global != _type_flag:
                str_installed = (
                    "True "
                    if _type_flag == SpawnDataType.UNIVERSAL_ACDC
                    else "False"
                )
                std_determined = (
                    "True "
                    if _type_global == SpawnDataType.UNIVERSAL_ACDC
                    else "False"
                )
                step.warn((
                    "Определённый формат данных all.spawn не совпадает с установленным:"
                    f"\n  [features] universal_acdc = {str_installed} ; установленный"
                    f"\n  [features] universal_acdc = {std_determined} ; определённый"
                ))
    
    if len(ini_spawn.sections()) > 0:
        with InspectorStep("Проверка секций из [ignore_sections]") as step:
            class SectionSource(Enum):
                ALL_SPAWN           = "all.spawn"
                DROP_BOX            = "drop_box"
                TREASURE_MANAGER    = "treasure_manager"
                OTHER_INVENTORIES   = "инвентарь трупа или хранилища"

            ignored_src: dict[str, set[SectionSource]]
            ignored_src = {
                section_name: set()
                for section_name in ini_meta.section("ignore_sections").lines()
            }
            ALL_LEVELS = LEVELS.as_list()
            collector = SpawnEntriesCollector()

            # Объекты из all.spawn
            for obj in spawn.objects():
                if obj.section_name in ignored_src:
                    ignored_src[obj.section_name].add(SectionSource.ALL_SPAWN)
            
            # Предметы из разных источников
            pipeline: list[tuple[Callable[[list[str]], None], SectionSource]]
            pipeline = [
                (collector.from_drop_box_items, SectionSource.DROP_BOX),
                (collector.from_treasure_manager, SectionSource.TREASURE_MANAGER),
                (collector.from_non_tm_inventories, SectionSource.OTHER_INVENTORIES),
            ]
            for collect, src in pipeline:
                collect(ALL_LEVELS)
                for entry in collector.result.entries():
                    if entry.name in ignored_src:
                        ignored_src[entry.name].add(src)
                collector.result.clear()

            if any([(len(srcs) > 0) for srcs in ignored_src.values()]):
                step.info("Секции из [ignore_sections], которые встречаются в игре:")
                for section_name, srcs in ignored_src.items():
                    if len(srcs) > 0:
                        step.warn("{}: {}".format(
                            section_name,  
                            ", ".join([src.value for src in srcs])
                        ))

    with InspectorStep("Проверка заглушек для CLSID") as step:
        @dataclass(slots=True, frozen=True)
        class SectionWithDummyClass:
            section_name: str
            clsid: str
        
        dummy_sections: list[SectionWithDummyClass] = []
        dummy_clsids: set[str] = {
            clsid
            for clsid in CLSIDS
            if CLSIDS.get_object_type(clsid) == ObjectType.UNDEFINED
        }
        for s in ini_system.sections():
            clsid = s.get_string("class", "")
            if (len(clsid) > 0) and (clsid in dummy_clsids):
                if not ini_meta.line_exist("ignore_sections", s.id):
                    dummy_sections.append(SectionWithDummyClass(
                        section_name=s.id,
                        clsid=clsid
                    ))
        if len(dummy_sections) > 0:
            step.info(
                "Секции с CLSID-заглушкой рекомендуется прописать в [ignore_sections]:"
            )
            for data in dummy_sections:
                step.warn(f"{data.section_name} (class = {data.clsid})")

    with InspectorStep("Проверка правил определения типов объектов") as step:
        class InspectedType(Enum):
            MOBS            = ("MONSTER | STALKER", CLSIDS.is_mob)
            MONSTER         = ("MONSTER",           CLSIDS.is_monster)
            STALKER         = ("STALKER",           CLSIDS.is_stalker)
            ANOMALY         = ("ANOMALY",           CLSIDS.is_anomaly)
            ITEMS           = ("ITEM_*",            CLSIDS.is_item)
            ITEM_ART        = ("ITEM_ART",          CLSIDS.is_artefact)
            ITEM_WEAPON     = ("ITEM_WEAPON",       CLSIDS.is_weapon)
            ITEM_AMMO       = ("ITEM_AMMO",         CLSIDS.is_ammo)
            ITEM_GRENADE    = ("ITEM_GRENADE",      CLSIDS.is_grenade)
            ITEM_ADDON      = ("ITEM_ADDON",        CLSIDS.is_weapon_addon)
            ITEM_OUTFIT     = ("ITEM_OUTFIT",       CLSIDS.is_outfit)

            def __init__(self, type_label: str, type_checker: Callable[[str], bool]):
                self.type_label = type_label
                self.type_checker = type_checker
        
        INSPECTED_TYPES_DEPENDENCIES: dict[InspectedType, set[InspectedType]] = {
            InspectedType.MOBS: {
                InspectedType.MONSTER,
                InspectedType.STALKER,
            },
            InspectedType.ITEMS: {
                InspectedType.ITEM_ART,
                InspectedType.ITEM_WEAPON,
                InspectedType.ITEM_AMMO,
                InspectedType.ITEM_GRENADE,
                InspectedType.ITEM_ADDON,
                InspectedType.ITEM_OUTFIT,
            },
        }

        class DeviationReason(Enum):
            SPAWN_OBJECT_FIELDS     = "судя по объектам из all.spawn"
            SECTION_CONFIG_FIELDS   = "судя по полям конфига секции"
            SECTION_NAME            = "судя по имени секции"
            WEAPON_ADDON_SCOPE      = "встречается в scope_status"
            WEAPON_ADDON_SILENCER   = "встречается в silencer_status"
            WEAPON_ADDON_LAUNCHER   = "встречается в grenade_launcher_status"
            WEAPON_AMMO_CLASS       = "встречается в ammo_class"
            WEAPON_GRENADE_CLASS    = "встречается в grenade_class"

        @dataclass(slots=True)
        class SectionData:
            clsid: str
            deviations: set[tuple[InspectedType, DeviationReason]]

        # Сборка проверяемых секций
        sections_data: dict[str, SectionData] = {}
        for s in ini_system.sections():
            _class = s.get_string("class", "")
            if (
                (len(_class) > 0)
                and (_class in CLSIDS)
                and (CLSIDS.get_object_type(_class) != ObjectType.UNDEFINED)
                and not ini_meta.line_exist("ignore_sections", s.id)
            ):
                sections_data[s.id] = SectionData(
                    clsid=_class,
                    deviations=set()
                )

        # Поиск расхождений: оценка по полям объектов из all.spawn
        HEURISTIC: dict[InspectedType, list[str]] = {
            InspectedType.MOBS: [
                "base_out_restrictors",             # cse_alife_monster_abstract
                "base_in_restrictors",              # cse_alife_monster_abstract
                "upd:next_game_vertex_id",          # cse_alife_monster_abstract
                "upd:prev_game_vertex_id",          # cse_alife_monster_abstract
                "upd:distance_from_point",          # cse_alife_monster_abstract
                "upd:distance_to_point",            # cse_alife_monster_abstract
            ],
            InspectedType.STALKER: [
                "equipment_preferences",            # cse_alife_human_abstract (uACDC)
                "main_weapon_preferences",          # cse_alife_human_abstract (uACDC)
                "predicate5",                       # cse_alife_human_abstract (ACDC)
                "predicate4",                       # cse_alife_human_abstract (ACDC)
                "upd:start_dialog",                 # cse_alife_human_stalker
            ],
            InspectedType.ANOMALY: [
                "max_power",                        # cse_alife_custom_zone
                "enabled_time",                     # cse_alife_custom_zone
                "disabled_time",                    # cse_alife_custom_zone
                "start_time_shift",                 # cse_alife_custom_zone
            ],
            InspectedType.ITEMS: [
                "condition",                        # cse_alife_inventory_item
                "upd:quaternion",                   # cse_alife_inventory_item (uACDC)
                "upd:angular_velocity",             # cse_alife_inventory_item (uACDC)
                "upd:linear_velocity",              # cse_alife_inventory_item (uACDC)
                "upd:cse_alife_item__unk1_q8v4",    # cse_alife_inventory_item (ACDC)
                "upd:cse_alife_item__unk2_q8v3",    # cse_alife_inventory_item (ACDC)
                "upd:cse_alife_item__unk3_q8v3",    # cse_alife_inventory_item (ACDC)
            ],
            InspectedType.ITEM_WEAPON: [
                "ammo_current",                     # cse_alife_item_weapon
                "ammo_elapsed",                     # cse_alife_item_weapon
                "weapon_state",                     # cse_alife_item_weapon
                "addon_flags",                      # cse_alife_item_weapon
                "ammo_type",                        # cse_alife_item_weapon
                "upd:weapon_flags",                 # cse_alife_item_weapon
                "upd:ammo_elapsed",                 # cse_alife_item_weapon
                "upd:addon_flags",                  # cse_alife_item_weapon
                "upd:ammo_type",                    # cse_alife_item_weapon
                "upd:weapon_state",                 # cse_alife_item_weapon
                "upd:weapon_zoom",                  # cse_alife_item_weapon
            ],
            InspectedType.ITEM_AMMO: [
                "ammo_left",                        # cse_alife_item_ammo
                "upd:ammo_left",                    # cse_alife_item_ammo
            ],
        }
        for s in ini_spawn.sections():
            section_name = s.get_string("section_name", "")
            if (len(section_name) == 0) or (section_name not in sections_data):
                continue
            for _type, fields in HEURISTIC.items():
                if _type.type_checker(sections_data[section_name].clsid):
                    continue
                if any(s.line_exist(field) for field in fields):
                    sections_data[section_name].deviations.add(
                        (_type, DeviationReason.SPAWN_OBJECT_FIELDS)
                    )
        
        # Поиск расхождений: оценка по полям конфига секции
        HEURISTIC: dict[InspectedType, list[str]] = {
            InspectedType.MOBS: [
                # CCustomMonster
                "eye_fov", "eye_range",
                "critical_wound_threshold", "critical_wound_decrease_quant",
                "panic_threshold",
            ],
            InspectedType.MONSTER: [
                "attack_params", "max_hear_dist",
                "SoundThreshold", "DamagedThreshold",
                "RunAttack_PathDistance", "RunAttack_StartDistance",
                "DayTime_Begin", "DayTime_End",
                "distance_to_corpse", "satiety_threshold",
                "idle_sound_delay", "eat_sound_delay", "attack_sound_delay",
                "distant_idle_sound_delay", "distant_idle_sound_range",
                "eat_freq", "eat_slice", "eat_slice_weight",
            ],
            InspectedType.STALKER: [
                # CAI_Stalker
                "disp_walk_stand", "disp_walk_crouch",
                "disp_run_stand", "disp_run_crouch",
                "disp_stand_stand", "disp_stand_crouch",
                "disp_stand_stand_zoom", "disp_stand_crouch_zoom",
                "weapon_min_queue_size_far", "weapon_max_queue_size_far",
                "weapon_min_queue_interval_far", "weapon_max_queue_interval_far",
                "weapon_min_queue_size_medium", "weapon_max_queue_size_medium",
                "weapon_min_queue_interval_medium", "weapon_max_queue_interval_medium",
                "weapon_min_queue_size_close", "weapon_max_queue_size_close",
                "weapon_min_queue_interval_close", "weapon_max_queue_interval_close",
                "power_fx_factor",
            ],
            InspectedType.ANOMALY: [
                "disable_time", "disable_time_small", "disable_idle_time",
                "hit_impulse_scale", "effective_radius",
                "ignore_nonalive", "ignore_small", "ignore_artefacts",
                "visible_by_detector",
                "awaking_time", "blowout_time", "accamulate_time",
                "idle_sound", "accum_sound", "awake_sound",
                "blowout_sound", "hit_sound", "entrance_sound",
                "idle_particles", "blowout_particles",
                "accum_particles", "awake_particles",
                "entrance_small_particles", "entrance_big_particles",
                "hit_small_particles", "hit_big_particles",
                "idle_small_particles", "idle_big_particles",
                "postprocess",
                "blowout_particles_time", "blowout_light_time",
                "blowout_sound_time", "blowout_explosion_time",
                "blowout_wind", "blowout_light",
                "spawn_blowout_artefacts",
                "artefact_spawn_probability", "artefact_spawn_particles",
                "artefact_born_sound", "throw_out_power",
                "artefact_spawn_height", "artefacts",
                "ef_anomaly_type",
            ],
            InspectedType.ITEMS: [
                # CEatableItem
                "eat_health", "eat_power", "eat_satiety", "eat_radiation",
                "wounds_heal_perc",
                # CBottleItem
                "eat_alcohol",
                # CInventoryItem
                "slot", "description", "belt", "default_to_ruck",
                "can_take", "can_trade", "quest_item", "sprint_allowed",
            ],
            InspectedType.ITEM_ART: [
                # CArtefact
                "particles", "hit_absorbation_sect", "artefact_spawn_zones",
            ],
            InspectedType.ITEM_WEAPON: [
                # CWeapon
                "strap_position", "strap_orientation",
                "ammo_mag_size",
                "cam_relax_speed_ai",
                "PDM_disp_base", "PDM_disp_vel_factor", "PDM_disp_accel_factor",
                "PDM_disp_crouch", "PDM_disp_crouch_no_acc",
                "hand_dependence",
                "scope_status", "silencer_status", "grenade_launcher_status",
                "zoom_enabled",
                "scope_name", "silencer_name", "grenade_launcher_name",
            ],
            InspectedType.ITEM_AMMO: [
                # CWeaponAmmo
                "k_dist", "k_disp", "k_hit", "k_impulse",
                "k_pierce", "k_ap", "k_air_resistance",
                "tracer", "buck_shot", "impair", "box_size",
            ],
            InspectedType.ITEM_GRENADE: [
                # CGrenade
                "snd_checkout", "grenade_remove_time", "detonation_threshold_hit",
            ],
            InspectedType.ITEM_ADDON: [
                # CWeaponMagazined::ApplySilencerKoeffs
                "bullet_hit_power_k", "bullet_speed_k",
                "fire_dispersion_base_k", "cam_dispersion_k",
            ],
            InspectedType.ITEM_OUTFIT: [
                # CCustomOutfit
                "burn_protection", "strike_protection",
                "shock_protection", "wound_protection",
                "radiation_protection", "telepatic_protection",
                "chemical_burn_protection", "explosion_protection",
                "fire_wound_protection",
                "actor_visual", "ef_equipment_type", "power_loss",
            ],
        }
        for s in ini_system.sections():
            if s.id in sections_data:
                for _type, fields in HEURISTIC.items():
                    if _type.type_checker(sections_data[s.id].clsid):
                        continue
                    if any(s.line_exist(field) for field in fields):
                        sections_data[s.id].deviations.add(
                            (_type, DeviationReason.SECTION_CONFIG_FIELDS)
                        )
        
        # Поиск расхождений: оценка по имени секции
        HEURISTIC_SN: dict[InspectedType, re.Pattern] = {
            # InspectedType.ANOMALY:      re.compile(r"zone_.*|.*_zone"),
            InspectedType.ITEM_ART:     re.compile(r"af_.*"),
            InspectedType.ITEM_WEAPON:  re.compile(r"wpn_(?!.*(addon|missile)).*"),
            InspectedType.ITEM_AMMO:    re.compile(r"ammo_.*"),
            InspectedType.ITEM_GRENADE: re.compile(r"grenade_(?!.*fake).*"),
            InspectedType.ITEM_ADDON:   re.compile(r"wpn_addon_.*"),
            InspectedType.ITEM_OUTFIT:  re.compile(r"outfit_.*|.*_outfit"),
        }
        for s in ini_system.sections():
            if s.id in sections_data:
                for _type, pattern in HEURISTIC_SN.items():
                    if _type.type_checker(sections_data[s.id].clsid):
                        continue
                    if re.fullmatch(pattern, s.id):
                        sections_data[s.id].deviations.add(
                            (_type, DeviationReason.SECTION_NAME)
                        )

        # Поиск расхождений: проверка аддонов оружия
        WEAPON_ADDONS_CHECK : list[tuple[str, DeviationReason]] = [
            ("scope_name", DeviationReason.WEAPON_ADDON_SCOPE),
            ("silencer_name", DeviationReason.WEAPON_ADDON_SILENCER),
            ("grenade_launcher_name", DeviationReason.WEAPON_ADDON_LAUNCHER),
        ]
        for s in ini_system.sections():
            if (s.id in sections_data) and CLSIDS.is_weapon(sections_data[s.id].clsid):
                for field, reason in WEAPON_ADDONS_CHECK:
                    addon_sn = s.get_string(field, "")
                    if (
                        (len(addon_sn) > 0)
                        and (addon_sn in sections_data)
                        and not InspectedType.ITEM_ADDON.type_checker(
                            sections_data[addon_sn].clsid
                        )
                    ):
                        sections_data[addon_sn].deviations.add(
                            (InspectedType.ITEM_ADDON, reason)
                        )

        # Поиск расхождений: проверка боеприпасов оружия
        WEAPON_AMMO_CHECK : list[tuple[str, DeviationReason]] = [
            ("ammo_class", DeviationReason.WEAPON_AMMO_CLASS),
            ("grenade_class", DeviationReason.WEAPON_GRENADE_CLASS),
        ]
        for s in ini_system.sections():
            if (s.id in sections_data) and CLSIDS.is_weapon(sections_data[s.id].clsid):
                for field, reason in WEAPON_AMMO_CHECK:
                    for ammo_sn in s.get_strings(field, mandatory=False):
                        if (
                            (ammo_sn in sections_data)
                            and not InspectedType.ITEM_AMMO.type_checker(
                                sections_data[ammo_sn].clsid
                            )
                        ):
                            sections_data[ammo_sn].deviations.add(
                                (InspectedType.ITEM_AMMO, reason)
                            )
        
        # Фильтрация найденных расхождений:
        # 1. По одной и той же причине оставляем только более точные оценки типа
        for sdata in sections_data.values():
            dmap: dict[DeviationReason, list[InspectedType]] = {}
            for dtype, dreason in sdata.deviations:
                dmap.setdefault(dreason, []).append(dtype)
            for dreason, dtype_list in dmap.items():
                for dtype in dtype_list:
                    if (
                        (dtype in INSPECTED_TYPES_DEPENDENCIES)
                        and any(
                            (dtype2 in INSPECTED_TYPES_DEPENDENCIES[dtype])
                            for dtype2 in dtype_list
                        )
                    ):
                        sdata.deviations.remove((dtype, dreason))

        # Вывод найденных расхождений
        if any((len(sdata.deviations) > 0) for sdata in sections_data.values()):
            step.info(
                "Возможно, для некоторых секций неправильно определяется тип объекта..."
            )
            step.info("'имя секции': 'определённый тип' -> 'возможный тип' ('причина')")
            for sname, sdata in sections_data.items():
                for dtype, dreason in sdata.deviations:
                    step.warn("{}: {} -> {} ({})".format(
                        sname,
                        CLSIDS.get_object_type(sdata.clsid).name,
                        dtype.type_label,
                        dreason.value
                    ))


def inspect(show_stderr: bool = False, show_traceback: bool = False) -> None:
    """Основная функция для запуская полной проверки
    настройки конфигурационного файла (``meta.ltx``).

    :param show_stderr: Вывести ли сообщения из ``stderr``,
        собранные в процессе проверки.
    :param show_traceback: Выводить ли traceback исключения,
        которое может возникнуть в процессе проверки.
    """
    def _print_line():
        print("—" * InspectorStep.LINE_WIDTH)
    tb = ""

    # pipeline
    _print_line()
    stderr_buffer = io.StringIO()
    with redirect_stderr(stderr_buffer):
        try:
            _inspector_pipeline()
        except InspectorError:
            tb = traceback.format_exc().strip()
    stderr_str = stderr_buffer.getvalue().strip()
    _print_line()

    # stderr
    if show_stderr and (len(stderr_str) > 0):
        print(stderr_str)
        _print_line()
    
    # traceback
    if show_traceback and (len(tb) > 0):
        print(tb)
        _print_line()
