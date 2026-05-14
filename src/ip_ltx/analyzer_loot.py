"""Сводка по разному типу лута в игре"""

import itertools
import math
import traceback
from collections import OrderedDict
from collections.abc import Collection
from pathlib import Path

from .ini import meta_ini, spawn_ini, system_ini
from .misc.treasure_manager import TreasureManager
from .spawn import get_spawn
from .spawn_entries_collector import SpawnEntriesCollector
from .treasure_manager_ext import SpawnEntriesPool, SpawnEntry
from .utils import (
    ANSIColorCode,
    preinit_singletons,
    print_error,
    validate_data,
)
from .utils_meta import CLSIDs
from .xml_data.string_table import StringTable

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
    tm = TreasureManager()
    ini_spawn = spawn_ini()
    spawn = get_spawn()
    st = StringTable() if show_strings else {}

    # Выписываем содержимое тайников.
    with Path(fn).open("w", encoding="utf-8") as file:
        for treasure in tm:
            obj = spawn.story_object(treasure.target)
            if show_strings:
                name_txt = st.get(treasure.name, treasure.name) or "?"
                desc_txt = st.get(treasure.description, treasure.description) or "?"
                file.write(f"; {name_txt}\n")
                file.write(f"; {desc_txt}\n")
            if show_visual:
                visual_name = ini_spawn.get_string(obj._id, "visual_name", "")
                file.write(f";; {visual_name}\n")
            file.write("[{}]  {};story_id = {}\n".format(
                treasure._id, " "*max(0, 32-len(treasure._id)), obj.story_id
            ))
            file.write("\n".join([
                str(e) for e in itertools.chain(
                    SpawnEntriesPool.from_items(tm.ini.section(treasure._id)).entries(),
                    obj._loot.entries()
                )
            ]))
            file.write("\n\n")


def tm__extract_position(fn: str) -> None:
    """Вывести в файл позицию каждого тайника (для теста).

    :param fn: Путь/имя файла для вывода.
    """
    tm = TreasureManager()
    spawn = get_spawn()
    with Path(fn).open("w", encoding="utf-8") as file:
        for treasure in tm:
            obj = spawn.story_object(treasure.target)
            str_pos = ",".join([str(p) for p in obj.position])
            file.write(f"{{\"{treasure._id}\", {{{str_pos}}}}},\n")


def tm__count_by_levels(fn: str) -> None:
    """Подсчёт кол-ва тайников по каждой локации.

    :param fn: Путь/имя файла для вывода.
    """
    tm = TreasureManager()
    spawn = get_spawn()

    # counting
    cnt_by_lvl = {}
    for treasure in tm:
        obj = spawn.story_object(treasure.target)
        if obj._level not in cnt_by_lvl:
            cnt_by_lvl[obj._level] = 0
        cnt_by_lvl[obj._level] += 1

    # writing down
    with Path(fn).open("w", encoding="utf-8") as file:
        offset = ((max([len(lvl) for lvl in cnt_by_lvl]) // 4) + 1) * 4
        for lvl, cnt in sorted(cnt_by_lvl.items(), key=lambda x: x[0]):
            file.write("{}{}{}\n".format(lvl, " "*(offset - len(lvl)), cnt))
        file.write("{}\n".format("-"*(offset+2)))
        file.write("{}{}\n".format(" "*offset, sum(cnt_by_lvl.values())))


def tm__calculate_prob_w(fn: str) -> None:
    """Подсчёт весов, используемых в ``ИП v3.0``
    для определения, какой тайник выдать при обыске трупа.

    :param fn: Путь/имя файла для вывода.
    """
    tm = TreasureManager()
    spawn = get_spawn()
    d = OrderedDict()
    for treasure in tm:
        obj = spawn.story_object(treasure.target)
        cost = round(obj._loot.cost(in_trade=False))
        prob_w = 0 if (cost == 0) else math.ceil(1000000 / cost)
        d[treasure._id] = prob_w
    offset_0 = ((max([len(k) for k in d]) // 4) + 1) * 4
    offset_1 = ((max([len(str(v)) for v in d.values()]) // 4) + 1) * 4
    with Path(fn).open("w", encoding="utf-8") as file:
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
        levels: Collection[str],
        include_treasure_manager: bool = False,
        include_non_tm_inventories: bool = False,
        include_drop_box_items: bool = False,
        include_level_items: bool = False,
        compress: bool = False,
        show_unlisted_items: bool = False
) -> None:
    """Сводка по предметам в игре из разных источников на указанных локациях.

    Сводка осуществляется в формате т.н. вхождений (синтаксис секции ``[spawn]``).
    Вхождения с одинаковыми параметрами агрегируются по кол-ву (складываются count).
    Вывод группируется по типу предметов (см. ``[object_types]`` в мета-файле).
    В пределах каждого типа сохраняется порядок секций,
    как они встречаются в ``system.ltx``.
    Также выводится метрика по всему собранному содержимому.

    :param fp: Путь до файла для вывода.
    :param levels: Набор локаций, по которым осуществляется сводка.

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

    **Примеры использования**:

        * ``compress=True, show_unlisted_items=True`` - аккуратная сводка
          по всем встречающимся и невстречающимся предметам.
        * ``compress=False, show_unlisted_items=False`` - отображение всех
          встреченных вхождений (с агрегацией по количеству, где это возможно).
    """
    ini_meta = meta_ini()
    ini_system = system_ini()
    clsids = CLSIDs()
    _sections = {}
    msgs_w, msgs_e = [], []
    metrics = []

    # meta verification
    if not ini_meta.section_exist("ignore_sections"):
        raise Exception("meta-file doesn't have mandatory section [ignore_sections]")

    # Запоминаем порядковые номера секций предметов для финальной сортировки
    _sections = {id: i for i, id in enumerate(ini_system._s.keys())}

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
        "cost", round(entries.cost(in_trade=False))
    ))
    metrics.append((
        "cost_trade", round(entries.cost(in_trade=True))
    ))
    metrics.append((
        "game_objects_count", entries.game_objects_count(ignore_prob=False)
    ))

    # Дополнение невстреченными предметами через их нулевое количество.
    if show_unlisted_items:
        _section_exists = {se.name: True for se in entries.pool.values()}
        for id, sect in ini_system._s.items():
            _class = sect.get_string("class", "")
            if (len(_class) == 0):
                # Пропускаем секции без поля class.
                continue
            if (_class not in clsids):
                # Пропускаем секции с невалидным значением поля class.
                continue
            if not clsids.is_item(_class):
                # Если не инвентарный предмет, то пропускаем.
                continue
            if _section_exists.get(id, False):
                # Пропускаем уже зафиксированные секции.
                continue
            if ini_meta.line_exist("ignore_sections", id):
                # Пропускаем игнорируемые секции.
                continue
            if (
                clsids.is_weapon(_class)
                and (len(sect.get_string("scope_respawn", "")) > 0)
            ):
                # Пропускаем вспомогательные секции оружия для многоприцельности.
                continue
            if not sect.get_bool("can_take", True):
                # Пропускаем предметы, которые нельзя подобрать.
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
        entries.pool.values(),
        key=lambda se: (
            se._type.value,     # (1) по порядковому номеру типа инвентарного предмета
            _sections[se.name], # (2) по порядковому номеру секции
            se.signature()      # (3) по возрастанию сигнатур
        )
    )

    # Проверка, нет ли в собранном луте неожиданного предмета
    for se in entries:
        if ini_meta.line_exist("ignore_sections", se.name):
            msgs_w.append(f"encountered section '{se.name}' from [ignore_sections]")
        if not ini_system.get_bool(se.name, "can_take", True):
            msgs_w.append(f"encountered section '{se.name}' with 'can_take = false'")

    # Предподсчёт отступов по каждому типу предметов
    offset_by_type = {}
    for se in entries:
        if len(se.name) > offset_by_type.get(se._type, 0):
            offset_by_type[se._type] = len(se.name)
    for _type in offset_by_type:
        offset_by_type[_type] = ((offset_by_type[_type] // 4) + 1) * 4

    # Вывод в файл
    with Path(fp).open("w", encoding="utf-8") as file:
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
                if isinstance(value, float):
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

def run_summary(group_name: str, levels: Collection[str]) -> None:
    """Функция для запуска ряда сводок по данном списку локаций.

    * Местный аналог функции-обёртки :func:`~ip_ltx.utils.run`.
    * Перехватывает любые исключения и выводит информацию о них.
    * Вывод всех сводок осуществляется в отдельную поддиректорию.

    :param group_name: Имя группы. Используется для наименования поддиректории.
    :param levels: Набор локаций, по которым осуществляются сводки.
    """
    def _run_summary(dir_name, file_tag, **kwargs):
        fn = "{}__{}.txt".format(dir_name, file_tag)
        fp = "{}/{}".format(dir_name, fn)
        summary(fp, levels, **kwargs)

    dn = f"{summary.__name__}__{group_name}"
    Path(dn).mkdir(exist_ok=True)
    try:
        _run_summary(dn, "01_TM",
            include_treasure_manager=True, include_non_tm_inventories=False,
            include_drop_box_items=False, include_level_items=False,
            compress=(len(levels) > 1), show_unlisted_items=(len(levels) > 1)
        )
        _run_summary(dn, "02_NonTM",
            include_treasure_manager=False, include_non_tm_inventories=True,
            include_drop_box_items=False, include_level_items=False,
            compress=(len(levels) > 1), show_unlisted_items=(len(levels) > 1)
        )
        _run_summary(dn, "03_DropBox",
            include_treasure_manager=False, include_non_tm_inventories=False,
            include_drop_box_items=True, include_level_items=False,
            compress=(len(levels) > 1), show_unlisted_items=(len(levels) > 1)
        )
        _run_summary(dn, "04_NoParent",
            include_treasure_manager=False, include_non_tm_inventories=False,
            include_drop_box_items=False, include_level_items=True,
            compress=(len(levels) > 1), show_unlisted_items=(len(levels) > 1)
        )
        _run_summary(dn, "05_All",
            include_treasure_manager=True, include_non_tm_inventories=True,
            include_drop_box_items=True, include_level_items=True,
            compress=(len(levels) > 1), show_unlisted_items=(len(levels) > 1)
        )
        if len(levels) == 1:
            _run_summary(dn, "06_AllExt",
                include_treasure_manager=True, include_non_tm_inventories=True,
                include_drop_box_items=True, include_level_items=True,
                compress=False, show_unlisted_items=True
            )
            _run_summary(dn, "07_AllExtComp",
                include_treasure_manager=True, include_non_tm_inventories=True,
                include_drop_box_items=True, include_level_items=True,
                compress=True, show_unlisted_items=True
            )
    except Exception:
        print("")
        print(
            f"{ANSIColorCode.RED}"
            f"! {dn}"
            f"{ANSIColorCode.DEF}"
        )
        print(traceback.format_exc())
        print("", flush=True)
    else:
        print(
            f"{ANSIColorCode.GREEN}+{ANSIColorCode.DEF}",
            dn,
            flush=True
        )

def validate_spawn_data():
    """Проверка наличия данных о спавне.

    :raises Exception: если данных о спавне нет.
    """
    if len(spawn_ini().sections()) == 0:
        print_error("Отсутствуют данные о спавне: см. секцию [spawn] в meta.ltx")
        raise Exception("Spawn data is not provided")

# ----------------------------------------------------------------

validate_data([
    meta_ini,
    system_ini,
    spawn_ini,
    get_spawn,
])

preinit_singletons([
    TreasureManager,
])
