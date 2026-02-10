import os.path
import traceback
import math
from pathlib import Path
from collections import OrderedDict

import db
from ini import meta_ini, system_ini, spawn_ini
from treasure_manager import treasure_manager_ini, treasure_by_sid
from treasure_manager_ext import SpawnEntry, SpawnEntriesPool
from string_table import string_table
from spawn import get_spawn
from utils import print_warning, print_error

# ----------------------------------------------------------------

class SpawnEntriesCollector:
    def __init__(self):
        self.result = SpawnEntriesPool()

    def from_treasure_manager(self, levels=[]):
        """ Сборка вхождений с тайников из системы treasure_manager.
            @arg levels: list
                * Список локаций, по которым осуществляется сборка.
        """
        ini_tm = treasure_manager_ini()
        spawn = get_spawn()
        entries = SpawnEntriesPool()
        for treasure_section in ini_tm.sections():
            obj = spawn.story_object(treasure_section.get_number("target"))
            if obj._level in levels:
                entries.merge(obj._loot)
        self.result.merge(entries)

    def from_non_tm_inventories(self, levels=[]):
        """ Сборка вхождений с инвентарей:
                * inventory_box (O_INVBOX) вне системы тайников.
                * Мёртвые NPC (AI_STL_S) с предзаспавненным лутом.
                  Эта сборка не учитывает лут, определённый
                  системой death_manager и/или
                  полем supplies в характеристике NPC.
            @arg levels: list
                * Список локаций, по которым осуществляется сборка.
        """
        spawn = get_spawn()
        ini_spawn = spawn_ini()
        entries = SpawnEntriesPool()
        for obj in spawn.objects():
            if obj._level in levels:
                if obj._class == "O_INVBOX":
                    if treasure_by_sid(obj.story_id) is None:
                        entries.merge(obj._loot)
                elif obj._class == "AI_STL_S":
                    if ini_spawn.get_number(obj._id, "health") < 0.01:
                        if obj.custom_data.section_exist("dont_touch_old_loot"):
                            entries.merge(obj._loot)
        self.result.merge(entries)

    def from_drop_box_items(self, levels=[]):
        """ Сборка предметов из drop_box/items (xr_box).
            Эта сборка учитывает только детерминированный спавн,
              рандомизированный игнорируется.
            @arg levels: list
                * Список локаций, по которым осуществляется сборка.
        """
        spawn = get_spawn()
        entries = SpawnEntriesPool()
        for obj in spawn.objects():
            if obj._level in levels:
                if obj._class == "P_DSTRBL":  # physic_destroyable_object
                    if obj.custom_data.section_exist("drop_box"):
                        items = obj.custom_data.get_items("drop_box", "items", mandatory=False)
                        for item, count in items:
                            entries.add(SpawnEntry(item, str(count)))
        self.result.merge(entries)

    def from_level_items(self, levels=[]):
        """ Сборка предметов, лежащих в открытую на локации.
            В специфических случаях, когда состояние боеприпасов
              оружия невозможно описать синтаксисом вхождения,
              боеприпасы выносятся как отдельное вхождение,
              а оружие при этом считается разряженным.
            @arg levels: list
                * Список локаций, по которым осуществляется сборка.
        """
        ini_meta = meta_ini()
        ini_system = system_ini()
        ini_spawn = spawn_ini()
        spawn = get_spawn()
        entries = SpawnEntriesPool()
        for obj in spawn.objects():
            if obj._level in levels:
                _type = ini_meta.get_string("inv_class_to_type", obj._class, "")
                if len(_type) > 0:
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
                        cond = ini_spawn.get_number(obj._id, "condition")
                    if _type == "T_AMMO":
                        ammo_left = ini_spawn.get_uint(obj._id, "upd:ammo_left")
                        cfg_box_size = ini_system.get_uint(obj.section_name, "box_size")
                        if ammo_left < cfg_box_size:
                            box_size = ammo_left
                    if _type == "T_WPN":
                        ammo_elapsed = ini_spawn.get_uint(obj._id, "upd:ammo_elapsed")
                        if (ammo_elapsed == 0):
                            unload = True
                        else:
                            ammo_class = ini_system.get_strings(obj.section_name, "ammo_class")
                            ammo_type = ini_spawn.get_uint(obj._id, "upd:ammo_type")
                            if ammo_type >= len(ammo_class):
                                ammo_type = 0
                            ammo_mag_size = ini_system.get_uint(obj.section_name, "ammo_mag_size")
                            if (ammo_elapsed < ammo_mag_size) or (ammo_type != 0):
                                extra_ammo = (ammo_class[ammo_type], min(ammo_elapsed, ammo_mag_size))
                                unload = True
                        addon_flags = ini_spawn.get_uint(obj._id, "upd:addon_flags")
                        scope       = ((addon_flags & db.addon_flags.scope) != 0)
                        launcher    = ((addon_flags & db.addon_flags.launcher) != 0)
                        silencer    = ((addon_flags & db.addon_flags.silencer) != 0)
                    
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
                    entries.add(SpawnEntry(obj.section_name, params))
                    if extra_ammo is not None:
                        ammo_name, ammo_size = extra_ammo
                        entries.add(SpawnEntry(ammo_name, "1, box_size={}".format(ammo_size)))
        self.result.merge(entries)

# ----------------------------------------------------------------

def tm__extract_loot_each(fn, show_strings=False, show_visual=False):
    """ Вывести в файл содержимое каждого тайника.
        @arg show_strings: bool
            * также показать имя и описание тайника.
        @arg show_visual: bool
            * также показать используемый тайником визуал.
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
        else:
            # Сводка по наличию нужных строк
            for treasure_section in ini_tm.sections():
                treasure_id = treasure_section.id
                if not treasure_section.line_exist("name"):
                    print_warning(f"Treasure '{treasure_id}' doesn't have field 'name'")
                    continue
                if not treasure_section.line_exist("description"):
                    print_warning(f"Treasure '{treasure_id}' doesn't have field 'description'")
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
            obj = spawn.story_object(treasure_section.get_number("target"))
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


def tm__extract_position(fn):
    """ Вывести в файл позицию каждого тайника (для теста).
    """
    ini_tm = treasure_manager_ini()
    spawn = get_spawn()
    with open(fn, "w", encoding="utf-8") as file:
        for treasure_section in ini_tm.sections():
            obj = spawn.story_object(treasure_section.get_number("target"))
            str_pos = ",".join([str(p) for p in obj.position])
            file.write(f"{{\"{treasure_section.id}\", {{{str_pos}}}}},\n")


def tm__count_by_levels(fn):
    """ Подсчёт кол-ва тайников по каждой локации.
    """
    ini_tm = treasure_manager_ini()
    spawn = get_spawn()

    # counting
    cnt_by_lvl = {}
    for treasure_section in ini_tm.sections():
        obj = spawn.story_object(treasure_section.get_number("target"))
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


def tm__calculate_prob_w(fn):
    """ Подсчёт весов, используемых для определения,
          какой тайник выдать при обыске трупа.
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
        fp,
        include_treasure_manager=False,
        include_non_tm_inventories=False,
        include_drop_box_items=False,
        include_level_items=False,
        compress=False,
        show_unlisted_items=False,
        levels=[]
    ):
    """ Сводка по предметам в игре из разных источников на указанных локациях.
        Сводка осуществляется в формате т.н. вхождений (синтаксис секции [spawn]).
        Вхождения с одинаковыми параметрами агрегируются по кол-ву (складываются count).
        Вывод группируется по типу предметов (см. [inv_class_to_type] в мета-файле).
        В пределах каждого типа сохраняется порядок секций, как они встречаются в system.ltx.
        Также выводит метрику по всему собранному содержимому.
        
        @arg fp: str
            * Путь до файла для вывода.
        
        @arg include_treasure_manager: bool
            * Учесть предметы из тайников, зарегистрированных в системе treasure_manager.
        @arg include_non_tm_inventories: bool
            * Учесть предметы из хранилищ, не являющихся тайниками.
            * Также учитывает лут, вручную прописанный трупам NPC.
        @arg include_drop_box_items: bool
            * Учесть предметы из уничтожаемых ящиков, спавн которых детерминирован
              (указаны через items в секции [drop_box]; см. xr_box.script).
        @arg include_level_items: bool
            * Учесть предметы, которые лежат в открытую на локации,
              т.е. вне какого-либо инвентаря.
        
        @arg compress: bool
            * Более компактный вывод за счёт пост-обработки параметров вхождений.
            * Детальнее о принципе работы: см. SpawnEntriesPool::compress
            * Все метрики просчитываются до этой пост-обработки.
        @arg show_unlisted_items: bool
            * Отобразить те предметы, которые не встретились во всей сборке.
            * Такие предметы будут указаны с нулевым количеством (count).
            * Не будут отображены:
                - секции, перечисленные в [ignore_sections]
                - вспомогательные секции оружия для многоприцельности
        
        @arg levels: list
            * Список локаций, по которым осуществляется сводка.
    
        Примеры использования:
            * compress=True, show_unlisted_items=True
                * Аккуратная сводка по всем встречающимся и невстречающимся предметам
            * compress=False, show_unlisted_items=False
                * Отображение всех встреченных вхождений
                  (с агрегацией по количеству, где это возможно)
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
    metrics.append(("cost", round(entries.cost(trade=False))))
    metrics.append(("cost_trade", round(entries.cost(trade=True))))
    metrics.append(("game_objects_count", entries.game_objects_count(ignore_prob=False)))

    # Дополнение невстреченными предметами через их нулевое количество.
    if show_unlisted_items:
        _section_exists = {se.name: True for se in entries.pool.values()}
        for id, sect in ini_system.s.items():
            _type = ini_meta.get_string("inv_class_to_type", sect.get_string("class", ""), "")
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
                msgs_w.append("unable to insert '{}' with zero count ({})".format(id, str(e)))

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
            msgs_w.append("encountered section '{}' from [ignore_sections]".format(se.name))

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
        file.write("include_treasure_manager = {}\n".format(str(include_treasure_manager)))
        file.write("include_non_tm_inventories = {}\n".format(str(include_non_tm_inventories)))
        file.write("include_drop_box_items = {}\n".format(str(include_drop_box_items)))
        file.write("include_level_items = {}\n".format(str(include_level_items)))
        file.write("compress = {}\n".format(str(compress)))
        file.write("show_unlisted_items = {}\n".format(str(show_unlisted_items)))
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

def validate():
    try:
        ini_meta = meta_ini()
        ini_system = system_ini()
        ini_spawn = spawn_ini()
        ini_tm = treasure_manager_ini()
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
        return False
    return True
        
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

def _run_summary(dir_name, file_tag, kwargs):
    fn = "{}__{}.txt".format(dir_name, file_tag)
    fp = "{}/{}".format(dir_name, fn)
    summary(fp, **kwargs)

def run_summary(group_name, levels):
    dn = "{}__{}".format(summary.__name__, group_name)
    Path(dn).mkdir(exist_ok=True)
    try:
        _run_summary(dn, "01_TM", dict(
            include_treasure_manager=True, include_non_tm_inventories=False,
            include_drop_box_items=False, include_level_items=False,
            compress=(len(levels) > 1), show_unlisted_items=(len(levels) > 1),
            levels=levels
        ))
        _run_summary(dn, "02_NonTM", dict(
            include_treasure_manager=False, include_non_tm_inventories=True,
            include_drop_box_items=False, include_level_items=False,
            compress=(len(levels) > 1), show_unlisted_items=(len(levels) > 1),
            levels=levels
        ))
        _run_summary(dn, "03_DropBox", dict(
            include_treasure_manager=False, include_non_tm_inventories=False,
            include_drop_box_items=True, include_level_items=False,
            compress=(len(levels) > 1), show_unlisted_items=(len(levels) > 1),
            levels=levels
        ))
        _run_summary(dn, "04_NoParent", dict(
            include_treasure_manager=False, include_non_tm_inventories=False,
            include_drop_box_items=False, include_level_items=True,
            compress=(len(levels) > 1), show_unlisted_items=(len(levels) > 1),
            levels=levels
        ))
        _run_summary(dn, "05_All", dict(
            include_treasure_manager=True, include_non_tm_inventories=True,
            include_drop_box_items=True, include_level_items=True,
            compress=(len(levels) > 1), show_unlisted_items=(len(levels) > 1),
            levels=levels
        ))
        if len(levels) == 1:
            _run_summary(dn, "06_AllExt", dict(
                include_treasure_manager=True, include_non_tm_inventories=True,
                include_drop_box_items=True, include_level_items=True,
                compress=False, show_unlisted_items=True,
                levels=levels
            ))
            _run_summary(dn, "07_AllExtComp", dict(
                include_treasure_manager=True, include_non_tm_inventories=True,
                include_drop_box_items=True, include_level_items=True,
                compress=True, show_unlisted_items=True,
                levels=levels
            ))
    except Exception as e:
        print("")
        print("! {}".format(dn))
        print(traceback.format_exc())
        print("", flush=True)
    else:
        print("+ {}".format(dn), flush=True)

# ----------------------------------------------------------------

def main():
    if not validate():
        return

    # Summaries
    levels_all = [
        "l01_escape", "l02_garbage", "l03_agroprom", "l04_darkvalley",
        "l05_bar", "l06_rostok", "l07_military", "l08_yantar",
        "l08u_brainlab", "l10_radar", "l11_pripyat", "l12_stancia"
    ]
    run_summary("all", levels_all)
    run_summary(
        "all_but_l11_l12",
        [level for level in levels_all if level not in ["l11_pripyat", "l12_stancia"]]
    )
    run_summary(
        "custom",
        ["l01_escape", "l02_garbage", "l03_agroprom", "l04_darkvalley", "l05_bar", "l06_rostok",
        "l07_military", "l08_yantar", "l08u_brainlab"]
    )
    for level in levels_all:
        run_summary(level, [level])
    
    # Other
    run(tm__count_by_levels, "tm-counts")
    run(tm__extract_loot_each, "tm-each", dict(show_strings=True, show_visual=True))
    # run(tm__extract_position, "tm-position")
    run(tm__calculate_prob_w, "tm-prob_w")





if __name__ == "__main__":
    main()
