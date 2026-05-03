from .db import ADDON_FLAGS
from .ini import meta_ini, system_ini, spawn_ini
from .spawn import get_spawn
from .treasure_manager import treasure_manager_ini, treasure_by_sid
from .treasure_manager_ext import SpawnEntry, SpawnEntriesPool
from .utils_meta import ObjectType


class SpawnEntriesCollector:
    """Сборщик лута из разных источников.
    """
    result: SpawnEntriesPool

    def __init__(self):
        self.result = SpawnEntriesPool()

    def from_treasure_manager(self, levels: list[str] = []) -> None:
        """Сборка вхождений с тайников из системы treasure_manager.

        Учитывает список ``items`` из конфига тайника и предметы
        из секций ``[spawn]`` и ``[spawn_tm]`` из ``custom_data``
        соответствующего тайнику спавн-объекта.

        :param levels: Список локаций, по которым осуществляется сборка.
        """
        ini_meta = meta_ini()
        ini_tm = treasure_manager_ini()
        spawn = get_spawn()
        entries = SpawnEntriesPool()
        for treasure_section in ini_tm.sections():
            obj = spawn.story_object(treasure_section.get_uint("target"))
            if obj._level in levels:
                # all.spawn: [spawn] & [spawn_tm]
                entries.merge(obj._loot)
                # treasure_manager.ltx: items
                entries.merge(SpawnEntriesPool.from_items(treasure_section))
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
                if ini_spawn.get_float(obj._id, "health", 1.0) < 0.01:
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
                    entries.add(SpawnEntry(item, str(count), f"custom_data@{obj.name}"))
        self.result.merge(entries)

    def from_level_items(self, levels: list[str] = []) -> None:
        """Сборка предметов, лежащих в открытую на локации.

        В специфических случаях, когда состояние боеприпасов
        оружия невозможно описать синтаксисом вхождения,
        боеприпасы выносятся как отдельное вхождение,
        а оружие при этом считается разряженным.

        Предметы с `can_take = false` в конфиге секции игнорируются.
        
        :param levels: Список локаций, по которым осуществляется сборка.
        """
        ini_system = system_ini()
        ini_spawn = spawn_ini()
        spawn = get_spawn()
        entries = SpawnEntriesPool()
        for obj in spawn.objects():
            if obj._level not in levels:
                # Пропускаем ненужные локации.
                continue
            if not obj._type.is_item():
                # Пропускаем, если не инвентарный предмет.
                continue
            if not ini_system.get_bool(obj.section_name, "can_take", True):
                # Пропускаем предмет, если его нельзя подобрать
                continue
            
            # alias
            sname = obj.section_name

            # Параметры, по которым нужно собрать инфу
            cond = None
            box_size = None
            scope = False
            silencer = False
            launcher = False
            unload = False
            extra_ammo = None  # боеприпасы оружия как доп. вхождение
            
            # Сборка инфы спавна
            cond = obj.get_condition()
            if obj._type == ObjectType.ITEM_AMMO:
                ammo_left = ini_spawn.get_uint(obj._id, "upd:ammo_left")
                cfg_box_size = ini_system.get_uint(sname, "box_size")
                if ammo_left < cfg_box_size:
                    box_size = ammo_left
            if obj._type == ObjectType.ITEM_WEAPON:
                ammo_elapsed = ini_spawn.get_uint(obj._id, "upd:ammo_elapsed", 0)
                if (ammo_elapsed == 0):
                    unload = True
                else:
                    ammo_class = ini_system.get_strings(sname, "ammo_class")
                    ammo_type = ini_spawn.get_uint(obj._id, "upd:ammo_type", 0)
                    if ammo_type >= len(ammo_class):
                        ammo_type = 0
                    ammo_mag_size = ini_system.get_uint(sname, "ammo_mag_size")
                    if (ammo_elapsed < ammo_mag_size) or (ammo_type != 0):
                        extra_ammo = (
                            ammo_class[ammo_type],
                            min(ammo_elapsed, ammo_mag_size)
                        )
                        unload = True
                addon_flags = ini_spawn.get_uint(obj._id, "upd:addon_flags", 0)
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
            context = f"all.spawn@{obj.name}"
            entries.add(SpawnEntry(sname, params, context))
            if extra_ammo is not None:
                ammo_name, ammo_size = extra_ammo
                entries.add(SpawnEntry(ammo_name, f"1, box_size={ammo_size}", context))
        self.result.merge(entries)
