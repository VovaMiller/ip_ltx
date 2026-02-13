"""Генерация характеристик NPC"""

import re
import os.path
import traceback
import itertools
from os import mkdir
from random import randint

from .ip_ltx import Ini
from .ini import system_ini
from .treasure_manager_ext import SpawnEntry
from .utils import print_warning, print_error


OUTPUT_FOLDER = "xml"

TAB = "\t"  # "    "
GENMODE_0 = ("0", "w0+w1*w2")
GENMODE_1 = ("1", "unique")
GENMODE_2 = ("2", "w0+w2")

RANK_NAME_TO_NUM = {
    """ UPD
        Ранг новичков проставлен не от нуля,
        чтобы избежать бага с завышенной точностью стрельбы
        (см. report_57).
    """
    "novice":       (100, 299),
    "experienced":  (300, 599),
    "veteran":      (600, 899),
    "master":       (900, 999),
    "1n":           (100, 299),
    "2e":           (300, 599),
    "3v":           (600, 899),
    "4m":           (900, 999)
}

COMMUNITY_TO_CROUCH_TYPE = {
    "stalker":  -1,
    "monolith": -1,
    "zombied":  -1,
    "killer":   -1,
    "freedom":  -1,
    "trader":   -1,
    "dolg":      0,
    "military":  0,
    "bandit":    1,
    "ecolog":    1,
    "ipmil":     0,
}

# ----------------------------------------------------------------

def read_items(section, field):
    """ Прочитать строку с предметами из секции (section) в поле (field).
        Пример строки: "bread, vodka (2), wpn_pm (1, silencer)".
        Возвращает список экземпляров класса SpawnEntry.
        В списке сохраняются как None:
            - Предметы без указанного id секции
            - Предметы с нулевым количеством или нулевой вероятностью.
    """
    line = section.get_string(field, "None").strip()
    if line == "None":
        return []
    if line.find("|") != -1:
        raise Exception("wrong item list format: \"{}\"".format(line))
    
    # Предобработка разделителей
    line_p = list(line)
    parenthesis = False
    for i in range(len(line_p)):
        if parenthesis:
            if line_p[i] == "(":
                raise Exception("wrong item list format: \"{}\"".format(line))
            if line_p[i] == ")":
                parenthesis = False
        else:
            if line_p[i] == ")":
                raise Exception("wrong item list format: \"{}\"".format(line))
            if line_p[i] == "(":
                parenthesis = True
            elif line_p[i] == ",":
                line_p[i] = "|"
    line_p = "".join(line_p)
    
    # Считывание предметов
    items = []
    for s1 in line_p.split("|"):
        s1 = s1.strip()
        if len(s1) == 0:
            items.append(None)
            continue
        name, params = None, None
        tmp = re.match(r"^(\S+)\s*\(([^\)]+)\)$", s1)
        if tmp is not None:
            name = tmp.group(1)
            params = tmp.group(2).strip()
        else:
            tmp = re.match(r"^(\S+)$", s1)
            if tmp is None:
                raise Exception("wrong item list format: \"{}\"".format(line))
            name = tmp.group(1)
            params = "1"
        try:
            se = SpawnEntry(name, params)
        except Exception as e:
            print_error(f"{str(e)} ('{s1}')")
            items.append(None)
        else:
            if (se.count > 0) and (se.prob is None or se.prob > 0):
                items.append(se)
            else:
                items.append(None)
    
    return items

# ----------------------------------------------------------------

class CharacterSettings:
    def __init__(self, s):
        # preinit
        self.genmode = None
        self.name = ""
        self.icon = ""
        self.cls = None
        self.community = ""
        self.terrain_sect = ""
        self.rank = None
        self.reputation = None
        self.money = None
        self.visual = ""
        self.snd_config = ""
        self.crouch_type = None
        self.w0, self.w1, self.w2 = [], [], []
        self.a0, self.a1, self.a2 = [], [], []
        self.items = []
        self.include_supplies = None
        self.include = None
        
        self.genmode = s._fields.get("_genmode", GENMODE_0[0])
        self.name = s._fields.get("name", "")
        self.icon = s._fields.get("icon", "")
        self.cls = s._fields.get("class", "")
        self.community = s._fields.get("community", "")
        self.terrain_sect = s._fields.get("terrain_sect", "")
        self.visual = s._fields.get("visual", "")
        self.snd_config = s._fields.get("snd_config", "")
        
        ini_system = system_ini()
        
        # Parsing <rank>
        self.rank = None
        rank = s._fields.get("rank", None)
        if (rank is not None):
            rank = rank.replace(" ", "").split(",")
            if (len(rank) == 1):
                if rank[0].isnumeric():
                    self.rank = (int(rank[0]), int(rank[0]))
                else:
                    self.rank = RANK_NAME_TO_NUM.get(rank[0], None)
                    assert self.rank is not None, "Unknown rank alias for \"{}\"".format(s.id)
            elif (len(rank) == 2):
                assert rank[0].isnumeric() and rank[1].isnumeric(), "Wrong rank format for \"{}\"".format(s.id)
                self.rank = (int(rank[0]), int(rank[1]))
                assert self.rank[0] <= self.rank[1], "<rank>: Typo or wrong order in [{}]".format(s.id)
            else:
                assert False, "Too many parameters for <rank> in \"{}\"".format(s.id)
        
        # Parsing <reputation>
        self.reputation = None
        reputation = s._fields.get("reputation", None)
        if (reputation is not None):
            reputation = reputation.replace(" ", "").split(",")
            if (len(reputation) == 1):
                try:
                    self.reputation = (int(reputation[0]), int(reputation[0]))
                except ValueError:
                    assert False, "Expected integer for <reputation> in \"{}\"".format(s.id)
            elif (len(reputation) == 2):
                try:
                    self.reputation = (int(reputation[0]), int(reputation[1]))
                except ValueError:
                    assert False, "Expected two integers for <reputation> in \"{}\"".format(s.id)
                assert self.reputation[0] <= self.reputation[1], "<reputation>: Typo or wrong order in [{}]".format(s.id)
            else:
                assert False, "Too many parameters for <reputation> in \"{}\"".format(s.id)
        
        # Parsing <money>
        self.money = None
        money = s._fields.get("money", None)
        if (money is not None):
            money = money.replace(" ", "").split(",")
            if (len(money) == 1):
                try:
                    self.money = (int(money[0]), int(money[0]))
                except ValueError:
                    assert False, "Expected integer for <money> in \"{}\"".format(s.id)
            elif (len(money) == 2):
                try:
                    self.money = (int(money[0]), int(money[1]))
                except ValueError:
                    assert False, "Expected two integers for <money> in \"{}\"".format(s.id)
                assert self.money[0] <= self.money[1], "<money>: Typo or wrong order in [{}]".format(s.id)
            else:
                assert False, "Too many parameters for <money> in \"{}\"".format(s.id)
        
        # Parsing <crouch_type>
        self.crouch_type = s._fields.get("crouch_type", None)
        if self.crouch_type is not None:
            try:
                self.crouch_type = int(self.crouch_type)
            except ValueError:
                assert False, "Expected integer for <crouch_type> in \"{}\"".format(s.id)
        
        # Parsing: <w0>, <w1>, <w2>
        self.w0 = read_items(s, "w0")
        self.w1 = read_items(s, "w1")
        self.w2 = read_items(s, "w2")
        
        # Checking <w0>, <w1>, <w2>
        # Проверка, что указано действительно оружие.
        for se in itertools.chain(self.w0, self.w1, self.w2):
            if (se is not None) and (se._type != "T_WPN"):
                print_warning(f"Section '{se.name}' is not a weapon")
        
        # Checking <w1>, <w2>
        # Проверка, чтобы в одной характеристике не комбинировалось
        #  оружие, которое NPC использует в одном и том же слоте.
        for se in self.w1:
            if (se is not None) and ini_system.get_number(se.name, "ef_weapon_type", -1) not in [5]:
                print_warning(f"Unexpected ef_weapon_type:\n    {s.id}, w1 = {se.name}")
        for se in self.w2:
            if (se is not None) and ini_system.get_number(se.name, "ef_weapon_type", -1) not in [6, 7, 8, 9]:
                print_warning(f"Unexpected ef_weapon_type:\n    {s.id}, w2 = {se.name}")

        # Filling: <a0>, <a1>, <a2>
        for w, a in zip([self.w0, self.w1, self.w2], [self.a0, self.a1, self.a2]):
            for wse in w:
                if wse is None:
                    a.append(None)
                else:
                    ammo_sections = ini_system.get_strings(wse.name, "ammo_class", mandatory=False)
                    if len(ammo_sections) > 0:
                        a.append(SpawnEntry(ammo_sections[0], "1"))
                    else:
                        print_warning(f"Can't get ammo for weapon '{wse.name}'")
                        a.append(None)

        # Parsing: <items>
        self.items = read_items(s, "items")

        # Parsing <include_supplies>
        self.include_supplies = s._fields.get("include_supplies", None)
        if self.include_supplies is not None:
            if self.include_supplies == "":
                self.include_supplies = []
            else:
                self.include_supplies = self.include_supplies.replace(" ", "").split(",")
        
        # Parsing <include>
        self.include = s._fields.get("include", None)
        if self.include is not None:
            if self.include == "":
                self.include = []
            else:
                self.include = self.include.replace(" ", "").split(",")


class Character:
    def __init__(self, cs, wpn):
        self.name = cs.name
        self.icon = cs.icon
        self.cls = cs.cls
        self.community = cs.community
        self.terrain_sect = cs.terrain_sect
        if (cs.rank is not None):
            self.rank = randint(cs.rank[0], cs.rank[1])
        else:
            self.rank = None
        if (cs.reputation is not None):
            self.reputation = randint(cs.reputation[0], cs.reputation[1])
        else:
            self.reputation = None
        if (cs.money is not None):
            if (cs.money[0] < 0) or (cs.money[1] < 0):
                self.money_min = -1
                self.money_max = -1
            else:
                self.money_min = cs.money[0]
                self.money_max = cs.money[1]
        else:
            self.money_min = None
            self.money_max = None
        self.visual = cs.visual
        self.snd_config = cs.snd_config
        self.crouch_type = cs.crouch_type
        self.include_supplies = cs.include_supplies
        self.include = cs.include
        self.spawn_items = []
        
        # Weapons & Ammo
        for idx, ww, aa in zip(wpn, [cs.w0, cs.w1, cs.w2], [cs.a0, cs.a1, cs.a2]):
            if (idx is not None) and (ww[idx] is not None):
                self.spawn_items.append(ww[idx])
                if (aa[idx] is not None):
                    self.spawn_items.append(aa[idx])

        # Extra items
        for se in cs.items:
            if se is not None:
                self.spawn_items.append(se)

    def autocomplete(self):
        """
            Автоматически заполняет некоторую незаполненную информацию.
        """
        if (self.name == ""):
            if (self.community == "bandit"):
                self.name = "GENERATE_NAME_bandit"
            elif (self.community == "ecolog"):
                self.name = "GENERATE_NAME_science"
            elif (self.community == "military"):
                if (self.rank is not None):
                    if (self.rank < 300):
                        self.name = "GENERATE_NAME_private"
                    elif (self.rank < 600):
                        self.name = "GENERATE_NAME_sergeant"
                    elif (self.rank < 900):
                        self.name = "GENERATE_NAME_lieutenant"
                    else:
                        self.name = "GENERATE_NAME_captain"
            else:
                self.name = "GENERATE_NAME_stalker"
        if (self.icon == ""):
            if (self.community == "zombied"):
                self.icon = "ui_npc_u_none"
            elif (self.visual != ""):
                self.icon = "ui_npc_u_{}".format(self.visual.split("\\")[-1])
        if (self.crouch_type is None):
            self.crouch_type = COMMUNITY_TO_CROUCH_TYPE.get(self.community, -1)
        if (self.include_supplies is None):
            self.include_supplies = []
        if (self.include is None):
            self.include = ["character_criticals", "character_dialogs"]
        
    def is_complete(self):
        """
            Проверяет полноту минимально необходимых данных характеристики.
            Если данных не хватает, то возвращает строку с именем незаполненного поля.
            Если данных хватает, то возвращает None.
        """
        if (self.cls is None):
            return "class"
        if (self.name == ""):
            return "name"
        if (self.icon == ""):
            return "icon"
        if (self.community == ""):
            return "community"
        if (self.rank is None):
            return "rank"
        if (self.reputation is None):
            return "reputation"
        if (self.money_min is None):
            return "money_min"
        if (self.money_max is None):
            return "money_max"
        if (self.visual == ""):
            return "visual"
        if (self.snd_config == ""):
            return "snd_config"
        if (self.crouch_type is None):
            return "crouch_type"
        if (self.include_supplies is None):
            return "include_supplies"
        if (self.include is None):
            return "include"
        return None
    
    def has_supplies(self):
        if (len(self.spawn_items) > 0):
            return True
        if (self.include_supplies is not None) and (len(self.include_supplies) > 0):
            return True
        return False
        

def write_character(f, ch, num):
    """
        f - файл для выписывания харктеристики.
        ch - экземляр Character с полной минимально необходимой информацией.
        num - номер характеристики для данного класса.
    """
    id_postfix = "_default{}".format(num) if num is not None else ""
    f.write("{}<specific_character id=\"{}{}\" team_default=\"1\">\n".format(TAB*1, ch.cls, id_postfix))
    f.write("{}<name>{}</name>\n".format(TAB*2, ch.name))
    f.write("{}<icon>{}</icon>\n".format(TAB*2, ch.icon))
    f.write("{}<class>{}</class>\n".format(TAB*2, ch.cls))
    f.write("{}<community>{}</community>".format(TAB*2, ch.community))
    if (ch.terrain_sect == ""):
        f.write("\n")
    else:
        f.write("<terrain_sect>{}</terrain_sect>\n".format(ch.terrain_sect))
    if (ch.money_min < 0) or (ch.money_max < 0):
        f.write("{}<money min=\"100000\" max=\"110000\" infinitive=\"1\"></money>\n".format(TAB*2))
    else:
        f.write("{}<money min=\"{}\" max=\"{}\" infinitive=\"0\"></money>\n".format(TAB*2, ch.money_min, ch.money_max))
    f.write("{}<rank>{}</rank>\n".format(TAB*2, ch.rank))
    f.write("{}<reputation>{}</reputation>\n".format(TAB*2, ch.reputation))
    f.write("{}<visual>{}</visual>\n".format(TAB*2, ch.visual))
    f.write("{}<snd_config>{}</snd_config>\n".format(TAB*2, ch.snd_config))
    f.write("{}<crouch_type>{}</crouch_type>\n".format(TAB*2, ch.crouch_type))
    if ch.has_supplies():
        f.write("{}<supplies>\n".format(TAB*2))
        f.write("{}[spawn] \\n\n".format(TAB*3))
        for se in ch.spawn_items:
            line = se.name
            params = se.get_params_str()
            if params != "1":
                line = "{} = {}".format(se.name, params)
            f.write("{}{} \\n\n".format(TAB*3, line))
        if (ch.include_supplies is not None):
            for inc in ch.include_supplies:
                f.write("#include \"gameplay\\{}.xml\"\n".format(inc))
        f.write("{}</supplies>\n".format(TAB*2))
    if (ch.include is not None):
        for inc in ch.include:
            f.write("#include \"gameplay\\{}.xml\"\n".format(inc))
    f.write("{}</specific_character>\n".format(TAB*1))


def form_characters(fp_in, fp_out):
    """
        fp_in - путь до файла с логикой формирования характеристик.
        fp_out - путь до файла, куда выписываются сформированные характеристики.
    """
    sys_ch = Ini(_name=os.path.basename(fp_in))
    sys_ch.read(fp_in, encoding=None)
    l_cs = []
    for section in sys_ch.s.values():
        if not section.id.startswith("_"):
            l_cs.append(CharacterSettings(section))
    d_cls_ch_num = {}
    d_cls_cs_num = {}
    
    with open(fp_out, "w", encoding=None) as f:
        f.write("<?xml version='1.0' encoding=\"windows-1251\"?>\n")
        f.write("<xml>\n")
        for cs in l_cs:
            if (cs.genmode == GENMODE_0[0]) or (cs.genmode == GENMODE_0[1]):
                count = len(cs.w0) + len(cs.w1)*len(cs.w2)
                for num in range(count):
                    wpn = (None, None, None)
                    if num < len(cs.w0):
                        wpn = (num, None, None)
                    else:
                        wpn = (None, (num - len(cs.w0)) % len(cs.w1), (num - len(cs.w0)) // len(cs.w1))
                    d_cls_ch_num[cs.cls] = d_cls_ch_num.get(cs.cls, 0) + 1
                    ch = Character(cs, wpn)
                    ch.autocomplete()
                    info = ch.is_complete()
                    assert info is None, "No <{}> info was found for character {}:{}".format(info, ch.cls, d_cls_ch_num[cs.cls])
                    write_character(f, ch, d_cls_ch_num[cs.cls])
            elif (cs.genmode == GENMODE_1[0]) or (cs.genmode == GENMODE_1[1]):
                count = len(cs.w0) + len(cs.w1)*len(cs.w2)
                assert (count <= 1), "Too many weapons choices for unique setting {}".format(cs.cls)
                assert (count == 1), "Expected exactly one characteristic for unique setting {}".format(cs.cls)
                assert (d_cls_ch_num.get(cs.cls, 0) == 0), "Too many characteristics for unique setting {}".format(cs.cls)
                wpn = (None, None, None)
                if len(cs.w0) > 0:
                    wpn = (0, None, None)
                else:
                    wpn = (None, 0, 0)
                d_cls_ch_num[cs.cls] = 1
                ch = Character(cs, wpn)
                ch.autocomplete()
                info = ch.is_complete()
                assert info is None, "No <{}> info was found for unique character {}".format(info, ch.cls)
                write_character(f, ch, None)
            elif (cs.genmode == GENMODE_2[0]) or (cs.genmode == GENMODE_2[1]):
                count = len(cs.w0) + len(cs.w2)
                for num in range(count):
                    wpn = (None, None, None)
                    if num < len(cs.w0):
                        wpn = (num, None, None)
                    else:
                        wpn = (
                            None,
                            ((num - len(cs.w0) + d_cls_cs_num.get(cs.cls, 0)) % len(cs.w1)) if len(cs.w1) > 0 else None,
                            num - len(cs.w0)
                        )
                    d_cls_ch_num[cs.cls] = d_cls_ch_num.get(cs.cls, 0) + 1
                    ch = Character(cs, wpn)
                    ch.autocomplete()
                    info = ch.is_complete()
                    assert info is None, "No <{}> info was found for character {}:{}".format(info, ch.cls, d_cls_ch_num[cs.cls])
                    write_character(f, ch, d_cls_ch_num[cs.cls])
            else:
                assert False, "Unexpected genmode ({}) for character settings with class {}".format(cs.genmode, cs.cls)
            d_cls_cs_num[cs.cls] = d_cls_cs_num.get(cs.cls, 0) + 1
        f.write("</xml>\n")


def construct_fp_out(fp_in):
    ifn = os.path.basename(fp_in)
    ifn, ife = os.path.splitext(ifn)
    if ife == ".xml":
        raise Exception("xml file input is not supported")
    return "{}/{}.xml".format(OUTPUT_FOLDER, ifn)

# ----------------------------------------------------------------

def generate(fps: list[str]):
    """Сгенерировать характеристики NPC по данным файлам.

    :param fps: Список файлов с настройками характеристик.
    """
    if len(fps) == 0:
        print_warning("zero-length input provided")
        return
    if not os.path.isdir(OUTPUT_FOLDER):
        mkdir(OUTPUT_FOLDER)
    max_len_fps = max([len(fp) for fp in fps])
    for i, ifp in enumerate(fps):
        try:
            ofp = construct_fp_out(ifp)
            form_characters(ifp, ofp)
        except Exception as e:
            print("")
            print("! ({}/{}) {}".format(i+1, len(fps), ifp))
            # print("    {}".format(repr(e)))
            print(traceback.format_exc())
            print("", flush=True)
        else:
            print(
                "+ ({}/{}) {}{} -> {}".format(i+1, len(fps), ifp, " "*(max_len_fps-len(ifp)), ofp),
                flush=True
            )
