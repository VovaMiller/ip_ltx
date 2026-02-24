"""Сводка по разному типу лута в игре"""

import traceback
import math
from pathlib import Path
from collections import OrderedDict

from .db import ADDON_FLAGS
from .ini import meta_ini, system_ini, spawn_ini
from .treasure_manager import treasure_manager_ini, treasure_by_sid
from .treasure_manager_ext import SpawnEntry, SpawnEntriesPool
from .xml_data.string_table import string_table
from .spawn import get_spawn
from .utils import ANSI_COLOR_CODE, print_warning, print_error, validate_data

# ----------------------------------------------------------------

class SpawnEntriesCollector:
    """Сборщик лута из разных источников.
    """
    result: SpawnEntriesPool

    def __init__(self):
        self.result = SpawnEntriesPool()

    def from_treasure_manager(self, levels: list[str] = []) -> None:
        """Сборка вхождений с тайников из системы treasure_manager.

        :param levels: Список локаций, по которым осуществляется сборка.
        """
        ini_tm = treasure_manager_ini()
        spawn = get_spawn()
        entries = SpawnEntriesPool()
        for treasure_section in ini_tm.sections():
            obj = spawn.story_object(treasure_section.get_uint("target"))
            if obj._level in levels:
                entries.merge(obj._loot)
        self.result.merge(entries)

    def from_non_tm_inventories(self, levels: list[str] = []) -> None:
        """Сборка вхождений с некоторых инвентарей.

        1. inventory_box (``O_INVBOX``) вне системы тайников.
        2. Мёртвые NPC (``AI_STL_S``) с предзаспавненным лутом.
           Эта сборка не учитывает лут, определённый системой
           death_manager и/или полем supplies в характеристике NPC.
        
        :param levels: Список локаций, по которым осуществляется сборка.
        """
        spawn = get_spawn()
        ini_spawn = spawn_ini()
        entries = SpawnEntriesPool()
        for obj in spawn.objects():
            if obj._level not in levels:
                continue
            if obj._class == "O_INVBOX":
                if treasure_by_sid(obj.story_id) is None:
                    entries.merge(obj._loot)
            elif obj._class == "AI_STL_S":
                if ini_spawn.get_float(obj._id, "health") < 0.01:
                    if obj.custom_data.section_exist("dont_touch_old_loot"):
                        entries.merge(obj._loot)
        self.result.merge(entries)

    def from_drop_box_items(self, levels: list[str] = []) -> None:
        """Сборка предметов из drop_box/items (``xr_box``).

        Эта сборка учитывает только детерминированный спавн,
        рандомизированный игнорируется.

        :param levels: Список локаций, по которым осуществляется сборка.
        """
        spawn = get_spawn()
        entries = SpawnEntriesPool()
        for obj in spawn.objects():
            if obj._level not in levels:
                continue
            if obj._class != "P_DSTRBL":  # physic_destroyable_object
                continue
            if obj.custom_data.section_exist("drop_box"):
                items = obj.custom_data.get_items("drop_box", "items", mandatory=False)
                for item, count in items:
                    entries.add(SpawnEntry(item, str(count)))
        self.result.merge(entries)

    def from_level_items(self, levels: list[str] = []) -> None:
        """Сборка предметов, лежащих в открытую на локации.

        В специфических случаях, когда состояние боеприпасов
        оружия невозможно описать синтаксисом вхождения,
        боеприпасы выносятся как отдельное вхождение,
        а оружие при этом считается разряженным.
        
        :param levels: Список локаций, по которым осуществляется сборка.
        """
        ini_meta = meta_ini()
        ini_system = system_ini()
        ini_spawn = spawn_ini()
        spawn = get_spawn()
        entries = SpawnEntriesPool()
        for obj in spawn.objects():
            if obj._level not in levels:
                continue
            
            sname = obj.section_name
            _type = ini_meta.get_string("inv_class_to_type", obj._class, "")
            if len(_type) == 0:
                continue
            
            # Параметры, по которым нужно собрать инфу
            cond = None
            box_size = None
            scope = False
            silencer = False
            launcher = False
            unload = False
            extra_ammo = None  # боеприпасы оружия как доп. вхождение
            
            # Сборка инфы спавна
            if ini_spawn.line_exist(obj._id, "upd:condition"):
                cond = ini_spawn.get_uint(obj._id, "upd:condition")
                cond = cond / 255
            else:
                cond = ini_spawn.get_float(obj._id, "condition")
            if _type == "T_AMMO":
                ammo_left = ini_spawn.get_uint(obj._id, "upd:ammo_left")
                cfg_box_size = ini_system.get_uint(sname, "box_size")
                if ammo_left < cfg_box_size:
                    box_size = ammo_left
            if _type == "T_WPN":
                ammo_elapsed = ini_spawn.get_uint(obj._id, "upd:ammo_elapsed")
                if (ammo_elapsed == 0):
                    unload = True
                else:
                    ammo_class = ini_system.get_strings(sname, "ammo_class")
                    ammo_type = ini_spawn.get_uint(obj._id, "upd:ammo_type")
                    if ammo_type >= len(ammo_class):
                        ammo_type = 0
                    ammo_mag_size = ini_system.get_uint(sname, "ammo_mag_size")
                    if (ammo_elapsed < ammo_mag_size) or (ammo_type != 0):
                        extra_ammo = (
                            ammo_class[ammo_type],
                            min(ammo_elapsed, ammo_mag_size)
                        )
                        unload = True
                addon_flags = ini_spawn.get_uint(obj._id, "upd:addon_flags")
                scope       = ((addon_flags & ADDON_FLAGS.scope) != 0)
                launcher    = ((addon_flags & ADDON_FLAGS.launcher) != 0)
                silencer    = ((addon_flags & ADDON_FLAGS.silencer) != 0)
            
            # Запись собранной инфы
            params = "{}{}{}{}{}{}".format(
                "" if (cond is None) else " cond={:.2f}".format(cond),
                "" if (box_size is None) else " box_size={}".format(box_size),
                "" if not scope else " scope",
                "" if not silencer else " silencer",
                "" if not launcher else " launcher",
                "" if not unload else " unload"
            )
            params = "1" if (len(params) == 0) else "1," + params
            entries.add(SpawnEntry(sname, params))
            if extra_ammo is not None:
                ammo_name, ammo_size = extra_ammo
                entries.add(SpawnEntry(ammo_name, f"1, box_size={ammo_size}"))
        self.result.merge(entries)

# ----------------------------------------------------------------

def tm__extract_loot_each(
        fn: str,
        show_strings: bool = False,
        show_visual: bool = False
) -> None:
    """Вывести в файл содержимое каждого тайника.

    :param fn: Путь/имя файла для вывода.
    :param show_strings: Также показать имя и описание тайника.
    :param show_visual: Также показать используемый тайником визуал.
    """
    ini_tm = treasure_manager_ini()
    ini_spawn = spawn_ini()
    spawn = get_spawn()

    # Извлекаем имена и описания
    st = {}
    if show_strings:
        try:
            st = string_table()
        except Exception as e:
            print_error(f"Unable to retrieve string_table nodes:\n    {str(e)}")
            st = {}
        else:
            # Сводка по наличию нужных строк
            for treasure_section in ini_tm.sections():
                treasure_id = treasure_section.id
                if not treasure_section.line_exist("name"):
                    print_warning(
                        f"Treasure '{treasure_id}' doesn't have field 'name'"
                    )
                    continue
                if not treasure_section.line_exist("description"):
                    print_warning(
                        f"Treasure '{treasure_id}' doesn't have field 'description'"
                    )
                    continue
                name = treasure_section.get_string("name")
                desc = treasure_section.get_string("description")
                if len(st.get(name, "")) == 0:
                    print_warning(f"Can't translate string '{name}'")
                    continue
                if len(st.get(desc, "")) == 0:
                    print_warning(f"Can't translate string '{desc}'")
                    continue

    # Выписываем содержимое тайников.
    with open(fn, "w", encoding="utf-8") as file:
        for treasure_section in ini_tm.sections():
            treasure_id = treasure_section.id
            obj = spawn.story_object(treasure_section.get_uint("target"))
            if show_strings:
                name_id = treasure_section.get_string("name", "?")
                name_txt = st.get(name_id, name_id)
                desc_id = treasure_section.get_string("description", "?")
                desc_txt = st.get(desc_id, desc_id)
                file.write("; {}\n".format(name_txt))
                file.write("; {}\n".format(desc_txt))
            if show_visual:
                visual_name = ini_spawn.get_string(obj._id, "visual_name", "")
                file.write(";; {}\n".format(visual_name))
            file.write("[{}]  {};story_id = {}\n".format(
                treasure_id, " "*max(0, 32-len(treasure_id)), obj.story_id
            ))
            file.write("\n".join([str(e) for e in obj._loot.entries()]))
            file.write("\n\n")


def tm__extract_position(fn: str) -> None:
    """Вывести в файл позицию каждого тайника (для теста).

    :param fn: Путь/имя файла для вывода.
    """
    ini_tm = treasure_manager_ini()
    spawn = get_spawn()
    with open(fn, "w", encoding="utf-8") as file:
        for treasure_section in ini_tm.sections():
            obj = spawn.story_object(treasure_section.get_uint("target"))
            str_pos = ",".join([str(p) for p in obj.position])
            file.write(f"{{\"{treasure_section.id}\", {{{str_pos}}}}},\n")


def tm__count_by_levels(fn: str) -> None:
    """Подсчёт кол-ва тайников по каждой локации.
    
    :param fn: Путь/имя файла для вывода.
    """
    ini_tm = treasure_manager_ini()
    spawn = get_spawn()

    # counting
    cnt_by_lvl = {}
    for treasure_section in ini_tm.sections():
        obj = spawn.story_object(treasure_section.get_uint("target"))
        if obj._level not in cnt_by_lvl:
            cnt_by_lvl[obj._level] = 0
        cnt_by_lvl[obj._level] += 1

    # writing down
    with open(fn, "w", encoding="utf-8") as file:
        offset = ((max([len(lvl) for lvl in cnt_by_lvl.keys()]) // 4) + 1) * 4
        for lvl, cnt in sorted(cnt_by_lvl.items(), key=lambda x: x[0]):
            file.write("{}{}{}\n".format(lvl, " "*(offset - len(lvl)), cnt))
        file.write("{}\n".format("-"*(offset+2)))
        file.write("{}{}\n".format(" "*offset, sum(cnt_by_lvl.values())))


def tm__calculate_prob_w(fn: str) -> None:
    """Подсчёт весов, используемых в ``ИП v3.0``
    для определения, какой тайник выдать при обыске трупа.

    :param fn: Путь/имя файла для вывода.
    """
    ini_tm = treasure_manager_ini()
    spawn = get_spawn()
    d = OrderedDict()
    for ts in ini_tm.sections():
        obj = spawn.story_object(ts.get_uint("target"))
        cost = round(obj._loot.cost(trade=False))
        prob_w = 0 if (cost == 0) else math.ceil(1000000 / cost)
        d[ts.id] = prob_w
    offset_0 = ((max([len(k) for k in d.keys()]) // 4) + 1) * 4
    offset_1 = ((max([len(str(v)) for v in d.values()]) // 4) + 1) * 4
    with open(fn, "w", encoding="utf-8") as file:
        file.write("# treasure_id, prob_w\n")
        for tid, prob_w in d.items():
            file.write("{}{}{}{}\n".format(
                tid,
                " "*(offset_0 - len(tid)),
                " "*(offset_1 - len(str(prob_w))),
                prob_w
            ))


def summary(
        fp: str,
        include_treasure_manager: bool = False,
        include_non_tm_inventories: bool = False,
        include_drop_box_items: bool = False,
        include_level_items: bool = False,
        compress: bool = False,
        show_unlisted_items: bool = False,
        levels: list[str] = []
) -> None:
    """Сводка по предметам в игре из разных источников на указанных локациях.

    Сводка осуществляется в формате т.н. вхождений (синтаксис секции ``[spawn]``).
    Вхождения с одинаковыми параметрами агрегируются по кол-ву (складываются count).
    Вывод группируется по типу предметов (см. ``[inv_class_to_type]`` в мета-файле).
    В пределах каждого типа сохраняется порядок секций,
    как они встречаются в ``system.ltx``.
    Также выводится метрика по всему собранному содержимому.
    
    :param fp: Путь до файла для вывода.
    
    :param include_treasure_manager: Учесть предметы из тайников,
        зарегистрированных в системе treasure_manager.
    :param include_non_tm_inventories: Учесть предметы из хранилищ,
        не являющихся тайниками. Также учитывает лут, вручную прописанный трупам NPC.
    :param include_drop_box_items: Учесть предметы из уничтожаемых ящиков,
        спавн которых детерминирован (указаны через ``items`` в секции ``[drop_box]``;
        см. ``xr_box.script``).
    :param include_level_items: Учесть предметы, которые лежат в открытую на локации,
        т.е. вне какого-либо инвентаря.

    :param compress: Использовать более компактный вывод за счёт
        пост-обработки параметров вхождений. Детальнее о принципе работы
        см. :meth:`~ip_ltx.treasure_manager_ext.SpawnEntriesPool.compress`.
        Все метрики просчитываются до этой пост-обработки.
    :param show_unlisted_items: Отобразить те предметы, которые
        не встретились во всей сборке. Такие предметы будут указаны
        с нулевым количеством (count). Не будут отображены секции,
        перечисленные в ``[ignore_sections]``, а также вспомогательные
        секции оружия для многоприцельности.
    
    :param levels: Список локаций, по которым осуществляется сводка.

    **Примеры использования**:

        * ``compress=True, show_unlisted_items=True`` - аккуратная сводка
          по всем встречающимся и невстречающимся предметам.
        * ``compress=False, show_unlisted_items=False`` - отображение всех
          встреченных вхождений (с агрегацией по количеству, где это возможно).
    """
    ini_meta = meta_ini()
    ini_system = system_ini()
    _types = {}
    _sections = {}
    msgs_w, msgs_e = [], []
    metrics = []

    # meta verification
    if not ini_meta.section_exist("inv_class_to_type"):
        raise Exception("meta-file doesn't have mandatory section [inv_class_to_type]")
    if not ini_meta.section_exist("ignore_sections"):
        raise Exception("meta-file doesn't have mandatory section [ignore_sections]")

    # Запоминаем порядковые номера типов предметов для финальной сортировки
    for _class, _type in ini_meta.s["inv_class_to_type"]._fields.items():
        if _type not in _types:
            _types[_type] = len(_types)
    
    # Запоминаем порядковые номера секций предметов для финальной сортировки
    _sections = {id: i for i, id in enumerate(ini_system.s.keys())}

    # Сборка необходимых вхождений
    sec = SpawnEntriesCollector()
    pipeline = [
        (include_treasure_manager,      sec.from_treasure_manager),
        (include_non_tm_inventories,    sec.from_non_tm_inventories),
        (include_drop_box_items,        sec.from_drop_box_items),
        (include_level_items,           sec.from_level_items),
    ]
    for include, collector in pipeline:
        if include:
            collector(levels=levels)
    entries = sec.result
    
    # Подсчёт различных метрик.
    metrics.append((
        "cost", round(entries.cost(trade=False))
    ))
    metrics.append((
        "cost_trade", round(entries.cost(trade=True))
    ))
    metrics.append((
        "game_objects_count", entries.game_objects_count(ignore_prob=False)
    ))

    # Дополнение невстреченными предметами через их нулевое количество.
    if show_unlisted_items:
        _section_exists = {se.name: True for se in entries.pool.values()}
        for id, sect in ini_system.s.items():
            _class = sect.get_string("class", "")
            _type = ini_meta.get_string("inv_class_to_type", _class, "")
            if len(_type) == 0:
                # Пропускаем неинвентарные предметы.
                continue
            if _section_exists.get(id, False):
                # Пропускаем уже зафиксированные секции.
                continue
            if ini_meta.line_exist("ignore_sections", id):
                # Пропускаем игнорируемые секции.
                continue
            if (_type == "T_WPN") and (len(sect.get_string("scope_respawn", "")) > 0):
                # Пропускаем вспомогательные секции оружия для многоприцельности.
                continue
            try:
                entries.add(SpawnEntry(id, "0"))
            except Exception as e:
                msgs_w.append(f"unable to insert '{id}' with zero count ({e})")

    # Более компактный вывод за счёт пост-обработки параметров спавна.
    if compress:
        entries.compress()

    # Финальное преобразование: ряд сортировок
    entries = sorted(
        list(entries.pool.values()),
        key=lambda se: (
            _types[se._type],   # (1) по порядковому номеру типа инвентарного предмета
            _sections[se.name], # (2) по порядковому номеру секции
            se.signature()      # (3) по возрастанию сигнатур
        )
    )

    # Проверка, нет ли в собранном луте неожиданного предмета
    for se in entries:
        if ini_meta.line_exist("ignore_sections", se.name):
            msgs_w.append(f"encountered section '{se.name}' from [ignore_sections]")

    # Предподсчёт отступов по каждому типу предметов
    offset_by_type = {}
    for se in entries:
        if len(se.name) > offset_by_type.get(se._type, 0):
            offset_by_type[se._type] = len(se.name)
    for _type in offset_by_type.keys():
        offset_by_type[_type] = ((offset_by_type[_type] // 4) + 1) * 4

    # Вывод в файл
    with open(fp, "w", encoding="utf-8") as file:
        file.write("[options]\n")
        file.write(f"include_treasure_manager = {include_treasure_manager}\n")
        file.write(f"include_non_tm_inventories = {include_non_tm_inventories}\n")
        file.write(f"include_drop_box_items = {include_drop_box_items}\n")
        file.write(f"include_level_items = {include_level_items}\n")
        file.write(f"compress = {compress}\n")
        file.write(f"show_unlisted_items = {show_unlisted_items}\n")
        file.write("levels = {}\n".format(", ".join(levels)))
        file.write("\n")
        for msgs, label in [(msgs_e, "ERROR"), (msgs_w, "WARNING")]:
            if len(msgs) > 0:
                file.write("[{}]\n".format(label))
                for msg in msgs:
                    file.write("; {}\n".format(msg))
                file.write("\n")
        if len(metrics) > 0:
            file.write("[metrics]\n")
            for label, value in metrics:
                if type(value) == float:
                    file.write("{} = {:.1f}\n".format(label, value))
                else:
                    file.write("{} = {}\n".format(label, value))
            file.write("\n")
        file.write("[summary]\n")
        if len(entries) > 0:
            _prev_type = entries[0]._type
            for se in entries:
                if se._type != _prev_type:
                    file.write("\n")
                    _prev_type = se._type
                file.write("{}{}= {}\n".format(
                    se.name,
                    " "*(offset_by_type[se._type] - len(se.name)),
                    se.get_params_str()
                ))

# ----------------------------------------------------------------

def run_summary(group_name: str, levels: list[str]) -> None:
    """Функция для запуска ряда сводок по данном списку локаций.
    
    * Местный аналог функции-обёртки :func:`~ip_ltx.utils.run`.
    * Перехватывает любые исключения и выводит информацию о них.
    * Вывод всех сводок осуществляется в отдельную поддиректорию.
    
    :param group_name: Имя группы. Используется для наименования поддиректории.
    :param levels: Список локаций, по которым осуществляются сводки.
    """
    def _run_summary(dir_name, file_tag, **kwargs):
        fn = "{}__{}.txt".format(dir_name, file_tag)
        fp = "{}/{}".format(dir_name, fn)
        summary(fp, **kwargs)

    dn = f"{summary.__name__}__{group_name}"
    Path(dn).mkdir(exist_ok=True)
    try:
        _run_summary(dn, "01_TM",
            include_treasure_manager=True, include_non_tm_inventories=False,
            include_drop_box_items=False, include_level_items=False,
            compress=(len(levels) > 1), show_unlisted_items=(len(levels) > 1),
            levels=levels
        )
        _run_summary(dn, "02_NonTM",
            include_treasure_manager=False, include_non_tm_inventories=True,
            include_drop_box_items=False, include_level_items=False,
            compress=(len(levels) > 1), show_unlisted_items=(len(levels) > 1),
            levels=levels
        )
        _run_summary(dn, "03_DropBox",
            include_treasure_manager=False, include_non_tm_inventories=False,
            include_drop_box_items=True, include_level_items=False,
            compress=(len(levels) > 1), show_unlisted_items=(len(levels) > 1),
            levels=levels
        )
        _run_summary(dn, "04_NoParent",
            include_treasure_manager=False, include_non_tm_inventories=False,
            include_drop_box_items=False, include_level_items=True,
            compress=(len(levels) > 1), show_unlisted_items=(len(levels) > 1),
            levels=levels
        )
        _run_summary(dn, "05_All",
            include_treasure_manager=True, include_non_tm_inventories=True,
            include_drop_box_items=True, include_level_items=True,
            compress=(len(levels) > 1), show_unlisted_items=(len(levels) > 1),
            levels=levels
        )
        if len(levels) == 1:
            _run_summary(dn, "06_AllExt",
                include_treasure_manager=True, include_non_tm_inventories=True,
                include_drop_box_items=True, include_level_items=True,
                compress=False, show_unlisted_items=True,
                levels=levels
            )
            _run_summary(dn, "07_AllExtComp",
                include_treasure_manager=True, include_non_tm_inventories=True,
                include_drop_box_items=True, include_level_items=True,
                compress=True, show_unlisted_items=True,
                levels=levels
            )
    except Exception as e:
        print("")
        print((
            f"{ANSI_COLOR_CODE.RED}"
            f"! {dn}"
            f"{ANSI_COLOR_CODE.DEF}"
        ))
        print(traceback.format_exc())
        print("", flush=True)
    else:
        print(
            f"{ANSI_COLOR_CODE.GREEN}+{ANSI_COLOR_CODE.DEF}",
            dn,
            flush=True
        )

# ----------------------------------------------------------------

validate_data([
    meta_ini,
    system_ini,
    spawn_ini,
    treasure_manager_ini,
    get_spawn,
])
