import re
import copy

from ini import meta_ini, system_ini
from trade import get_buy_k

"""
    * class SpawnEntry
    * class SpawnEntriesPool
"""


class SpawnEntry:
    """ Класс строки из секции спавна [spawn]
        Также поддерживает [spawn_tm] из iP v3.0
    """

    def __init__(self, name, params):
        """ Инициализация строки "name = params"
            Поддерживает нецелые count и box_size.

            @arg name <str>
                * Имя секции.
                * Оно же - key из строки секции спавна.
            @arg params <str>
                * Параметры спавна.
                * Оно же - value из строки секции спавна.
        """
        self.name = name
        self.count = 1
        self.prob = None    # percentage
        self.cond = None    # percentage
        self.box_size = None
        self.scope = False
        self.silencer = False
        self.launcher = False
        self.unload = False
        self._type = None

        # pulling data from system.ltx
        ini_meta = meta_ini()
        ini_system = system_ini()
        _section = ini_system.s.get(name, None)
        if _section is None:
            raise Exception("section '{}' doesn't exist".format(name))
        _class = _section._fields.get("class", None)
        if _class is None:
            raise Exception("section '{}' has no 'class' field".format(name))
        self._type = ini_meta.s["inv_class_to_type"]._fields.get(_class, None)
        if self._type is None:
            raise Exception("section '{}' has unexpected class ('{}')".format(name, _class))

        # parsing params
        params = str(params) if params is not None else ""
        comma, tmp = "", ""
        if len(params) > 0:
            comma = params.find(",")
            if comma < 0:
                # count
                if params.isdigit():
                    self.count = int(params)
                else:
                    try:
                        self.count = float(params)
                    except:
                        raise Exception("Invalid syntax")
            elif comma == 0:
                raise Exception("Invalid syntax")
            else:
                # count
                if params[:comma].isdigit():
                    self.count = int(params[:comma])
                else:
                    try:
                        self.count = float(params[:comma])
                    except:
                        raise Exception("Invalid syntax")
                params = params[comma+1:]

                # prob
                tmp = re.search(r"prob=([0-9\.]+)", params)
                if tmp is not None:
                    tmp = tmp.group(1)
                    self.prob = int(100*float(tmp) + 0.5)
                    if not (0 <= self.prob <= 100):
                        raise Exception("Invalid prob value")

                # cond
                tmp = re.search(r"cond=([0-9\.]+)", params)
                if tmp is not None:
                    tmp = tmp.group(1)
                    self.cond = int(100*float(tmp) + 0.5)
                    if not (0 <= self.cond <= 100):
                        raise Exception("Invalid cond value")

                # box_size
                tmp = re.search(r"box_size=([0-9\.]+)", params)
                if tmp is not None:
                    tmp = tmp.group(1)
                    if tmp.isdigit():
                        self.box_size = int(tmp)
                    else:
                        self.box_size = float(tmp)

                # weapon options
                self.scope      = (params.find("scope") >= 0)
                self.silencer   = (params.find("silencer") >= 0)
                self.launcher   = (params.find("launcher") >= 0)
                self.unload     = (params.find("unload") >= 0)

        # appropriateness of ammo-specific options
        if (self.box_size is not None) and (self._type != "T_AMMO"):
            raise Exception("option 'box_size' is used with non-ammo section")

        # appropriateness of weapon-specific options
        if (self._type != "T_WPN"):
            if self.scope:
                raise Exception("option 'scope' is used with non-weapon section")
            if self.silencer:
                raise Exception("option 'silencer' is used with non-weapon section")
            if self.launcher:
                raise Exception("option 'launcher' is used with non-weapon section")
            if self.unload:
                raise Exception("option 'unload' is used with non-weapon section")
        else:
            # Status check: scope
            if self.scope and (str(_section._fields.get("scope_status", "0")) != "2"):
                raise Exception("Scope is not attachable for this weapon")

            # Status check: silencer
            if self.silencer and (str(_section._fields.get("silencer_status", "0")) != "2"):
                raise Exception("Silencer is not attachable for this weapon")

            # Status check: launcher
            if self.launcher and (str(_section._fields.get("grenade_launcher_status", "0")) != "2"):
                raise Exception("Launcher is not attachable for this weapon")

            # Multiscope support
            if self.scope:
                # Disallow scope for base section
                scope_name = _section._fields.get("scope_name", None)
                if scope_name is None:
                    raise Exception("scope_name is not specified for this weapon")
                if (scope_name == "") or (scope_name == "wpn_addon_scope_dummy"):
                    raise Exception("Scope must not be attached to a base-section weapon")
            else:
                # Forced scope for multiscope section
                if len(_section.get_string("scope_respawn", "")) > 0:
                    raise Exception("Scope must be attached to a multiscope-section weapon")

        # Unifying some params
        if self.cond == 100:
            self.cond = None
        if self.prob == 100:
            self.prob = None

    def __str__(self):
        return "{} = {}".format(self.name, self.get_params_str())

    def get_params_str(self):
        str_count = str(self.count)
        if type(self.count) == float:
            str_count = "{:.2f}".format(self.count)
        params = []
        if self.prob is not None:
            params.append("prob={:.2f}".format(self.prob / 100.0))
        if self.cond is not None:
            params.append("cond={:.2f}".format(self.cond / 100.0))
        if self.box_size is not None:
            if type(self.box_size) == float:
                params.append("box_size={:.2f}".format(self.box_size))
            else:
                params.append("box_size={}".format(self.box_size))
        if self.scope:
            params.append("scope")
        if self.silencer:
            params.append("silencer")
        if self.launcher:
            params.append("launcher")
        if self.unload:
            params.append("unload")
        if len(params) > 0:
            params = "{}, {}".format(str_count, " ".join(params))
        else:
            params = str_count
        return params

    def signature(self):
        """
            Возвращает "сигнатуру" - строку,
            по которой можно определить одинаковость
            двух экземпляров этого класса с точностью
            до различных count.
        """
        parts = []
        parts.append(self.name)
        if self.prob is not None:
            parts.append("prob={}".format(self.prob))
        if self.cond is not None:
            parts.append("cond={}".format(self.cond))
        if self.box_size is not None:
            parts.append("box_size={}".format(self.box_size))
        if self.scope:
            parts.append("scope")
        if self.silencer:
            parts.append("silencer")
        if self.launcher:
            parts.append("launcher")
        if self.unload:
            parts.append("unload")
        return "|".join(parts)

    def cost(self, trade=False):
        """ Подсчёт стоимости вхождения
              с учётом кол-ва и всех параметров.
            Учитываются также неразряженные боеприпасы
              и прикреплённые к оружию аддоны.
            Результат - всегда float.

            @arg trade: bool
                * False: подсчёт исходной стоимости.
                * True: подсчёт стоимости продажи торговцам.
        """
        ini_system = system_ini()
        count = float(self.count)
        prob = 1.0 if (self.prob is None) else (self.prob / 100.0)
        cond = 1.0 if (self.cond is None) else (self.cond / 100.0)
        cond = (cond*0.9 + 0.1)**0.75  # condition_factor как в движке
        buy_k = 1.0 if not trade else get_buy_k(self.name)
        base_cost = ini_system.get_uint(self.name, "cost")
        if self._type == "T_AMMO":
            base_box_size = ini_system.get_uint(self.name, "box_size")
            box_size = self.box_size if (self.box_size is not None) else base_box_size
            return base_cost * ((count * box_size) / base_box_size) * prob * cond * buy_k
        elif self._type == "T_WPN":
            cost_sum = base_cost * count * prob * cond * buy_k
            addons = []
            if self.scope:
                addons.append(ini_system.get_string(self.name, "scope_name"))
            if self.silencer:
                addons.append(ini_system.get_string(self.name, "silencer_name"))
            if self.launcher:
                addons.append(ini_system.get_string(self.name, "grenade_launcher_name"))
            for addon_name in addons:
                addon_cost = ini_system.get_uint(addon_name, "cost")
                addon_buy_k = 1.0 if not trade else get_buy_k(addon_name)
                cost_sum += addon_cost * count * prob * addon_buy_k
            if not self.unload:
                ammo_class = ini_system.get_strings(self.name, "ammo_class")[0]
                ammo_mag_size = ini_system.get_uint(self.name, "ammo_mag_size")
                ammo_base_cost = ini_system.get_uint(ammo_class, "cost")
                ammo_base_box_size = ini_system.get_uint(ammo_class, "box_size")
                ammo_buy_k = 1.0 if not trade else get_buy_k(ammo_class)
                box_count = (count * ammo_mag_size) / ammo_base_box_size
                cost_sum += ammo_base_cost * box_count * prob * ammo_buy_k
            return cost_sum
        return base_cost * count * prob * cond * buy_k


# ----------------------------------------------------------------


class SpawnEntriesPool:
    """ Хранилище экземпляров класса SpawnEntry.
        Агрегирует по count вхождения с одинаковыми параметрами.
    """

    def __init__(self):
        self.pool = {}

    def add(self, se: "SpawnEntry"):
        s = se.signature()
        if s in self.pool:
            self.pool[s].count += se.count
        else:
            self.pool[s] = copy.deepcopy(se)

    def merge(self, entries: "SpawnEntriesPool"):
        for se in entries.pool.values():
            self.add(se)
    
    def entries(self):
        return self.pool.values()

    def clear(self):
        self.pool.clear()
    
    def __len__(self):
        return len(self.pool)

    def cost(self, trade=False):
        """ Подсчёт стоимости всех вхождений
              с учётом их количеств и всех параметров.
            Учитываются также неразряженные боеприпасы
              и прикреплённые к оружию аддоны.
            Рекомендуется подсчитывать до compress.
            Результат - всегда float.

            @arg trade: bool
                * False: подсчёт исходной стоимости.
                * True: подсчёт стоимости продажи торговцам.
        """
        return sum([se.cost(trade=trade) for se in self.pool.values()])
    
    def game_objects_count(self, ignore_prob=True):
        """ Подсчёт кол-ва игровых объектов (game_object)
              в сумме по всем вхождениям.
            Рекомендуется подсчитывать до compress.
            Возвращает:
              int, если ignore_prob=True;
              float, если ignore_prob=False.
            
            @arg ignore_prob: bool
                * True: параметр prob будет проигнорирован.
                * False: кол-во будет домножаться на параметр prob.
        """
        ini_system = system_ini()
        cnt = 0
        for se in self.pool.values():
            prob_factor = 1 if ignore_prob else (1.0 if (se.prob is None) else (se.prob / 100.0))
            if se.box_size is not None:
                base_box_size = ini_system.get_uint(se.name, "box_size")
                total_ammo = se.count * se.box_size
                box_count = total_ammo // base_box_size
                box_count += 1 if ((total_ammo % base_box_size) != 0) else 0
                cnt += box_count * prob_factor
            else:
                cnt += se.count * prob_factor
        return cnt

    def compress(self):
        """ Пост-обработка параметров спавна для более компактного вывода.

            * cond
                * флаг удаляется (его значение игнорируется)
            * prob
                * флаг удаляется, а его значение преобразуется в нецелый count
            * scope, silencer, launcher
                * флаги удаляются
                * аддон открепляется от оружия, становясь отдельным предметом
                * аддон наследует count и prob оружия
            * scope
                * вспомогательная секция многоприцельности оружия становится базовой
            * unload
                * флаг проставляется каждому оружию
                * при проставлении разряженные боеприпасы выносятся как отдельный предмет
                * разряженные боеприпасы наследуют count и prob оружия
            * box_size
                * кол-во любых патронов обозначается через box_size
                * при этом count всегда считается единицей
        """
        ini_meta = meta_ini()
        ini_system = system_ini()
        buffer = SpawnEntriesPool()
        buffer_ammo = SpawnEntriesPool()  # count as box_size for aggregation
        for se in self.pool.values():
            se.cond = None
            if se.prob is not None:
                se.count = float(se.count) * (se.prob / 100.0)
                se.prob = None
            if se.scope:
                addon_name = ini_system.get_string(se.name, "scope_name")
                buffer.add(SpawnEntry(addon_name, str(se.count)))
                se.scope = False
                scope_respawn = ini_system.get_string(se.name, "scope_respawn", "")
                if len(scope_respawn) > 0:
                    se.name = scope_respawn
            if se.silencer:
                addon_name = ini_system.get_string(se.name, "silencer_name")
                buffer.add(SpawnEntry(addon_name, str(se.count)))
                se.silencer = False
            if se.launcher:
                addon_name = ini_system.get_string(se.name, "grenade_launcher_name")
                buffer.add(SpawnEntry(addon_name, str(se.count)))
                se.launcher = False
            if not se.unload and (se._type == "T_WPN"):
                ammo_class = ini_system.get_strings(se.name, "ammo_class")[0]
                _ammo_type = ini_meta.get_string("inv_class_to_type", ini_system.get_string(ammo_class, "class"))
                ammo_mag_size = ini_system.get_uint(se.name, "ammo_mag_size")
                if _ammo_type == "T_AMMO":
                    buffer_ammo.add(SpawnEntry(ammo_class, str(ammo_mag_size * se.count)))
                else:
                    buffer.add(SpawnEntry(ammo_class, str(ammo_mag_size * se.count)))
                se.unload = True
            if se._type == "T_AMMO":
                box_size = se.box_size
                if box_size is None:
                    box_size = ini_system.get_uint(se.name, "box_size")
                se.count = se.count * box_size
                se.box_size = None
                buffer_ammo.add(se)
            else:
                buffer.add(se)
        for se in buffer_ammo.pool.values():
            se.box_size = se.count
            se.count = 1
        self.pool = buffer.pool
        self.merge(buffer_ammo)
