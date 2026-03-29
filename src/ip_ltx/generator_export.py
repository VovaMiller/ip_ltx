"""Генератор данных для сторонних утилит."""

from collections import OrderedDict

from .ini import meta_ini, system_ini
from .utils import run

# ----------------------------------------------------------------

def _ip_test_static_tables(fn: str) -> None:
    class SectionGroup:
        def __init__(self, name):
            self.name = name
            self.sections = []

    ini_meta = meta_ini()
    ini_system = system_ini()
    group_by_type = OrderedDict([
        ("T_ART",       SectionGroup("SECTIONS_INV_ART")),
        ("T_WPN",       SectionGroup("SECTIONS_INV_WPN")),
        ("T_AMMO",      SectionGroup("SECTIONS_INV_AMMO")),
        ("T_GREN",      SectionGroup("SECTIONS_INV_GREN")),
        ("T_ADDON",     SectionGroup("SECTIONS_INV_ADDON")),
        ("T_OUTFIT",    SectionGroup("SECTIONS_INV_OUTFIT")),
        ("T_OTHER",     SectionGroup("SECTIONS_INV_OTHER")),
        ("T_STALKER",   SectionGroup("SECTIONS_STALKER")),
    ])

    # filling in groups (inventory items)
    for sect in ini_system.sections():
        if ini_meta.line_exist("ignore_sections", sect.id):
            continue
        if len(ini_system.get_string(sect.id, "scope_respawn", "")) > 0:
            # skipping auxiliary multi-scope sections
            continue
        _class = sect.get_string("class", "?")
        _type = ini_meta.get_string("inv_class_to_type", _class, "?")
        if _type in group_by_type:
            group_by_type[_type].sections.append(sect.id)

    # filling in groups (mobs)
    for sect in ini_system.sections():
        if ini_meta.line_exist("ignore_sections", sect.id):
            continue
        _class = sect.get_string("class", "?")
        _type = ini_meta.get_string("mob_class_to_type", _class, "?")
        if _type in group_by_type:
            group_by_type[_type].sections.append(sect.id)

    # writing
    with open(fn, "w", encoding="utf-8") as file:
        tab = 4
        for group in group_by_type.values():
            if len(group.sections) > 0:
                offset = ((
                    5 + max([len(sect_id) for sect_id in group.sections]) + (tab - 1)
                ) // tab) * tab
                file.write("\n{} = {{\n".format(group.name))
                for sect_id in group.sections:
                    file.write("{}[\"{}\"]{}= true,\n".format(
                        " "*tab,
                        sect_id,
                        " "*(offset - 4 - len(sect_id))
                    ))
                file.write("}}\n".format())
            else:
                file.write("\n{} = {{}}\n".format(group.name))

def _universal_acdc_section_to_clsid(fn: str) -> None:
    KNOWN_CLSID = {
        "O_ACTOR", "R_ACTOR", "W_MGUN", "W_RAIL", "W_ROCKET", "W_M134", "AI_HUMAN",
        "W_GROZA", "W_M134en", "AI_CROW", "AI_HEN", "AI_RAT", "AI_SOLD", "AI_ZOMBY",
        "EVENT", "W_AK74", "W_FN2000", "W_HPSA", "W_LR300", "C_NIVA", "O_DUMMY",
        "W_BINOC", "W_FORT", "W_PM", "O_HEALTH", "AF_MBALL", "AI_ZOM", "T_ASS",
        "T_CS", "T_CSBASE", "T_CSCASK", "W_SHOTGN", "SPECT", "AI_RAT_G", "AI_STL",
        "A_PM", "AI_CONTR", "AI_DOG", "AI_GRAPH", "AI_SOLDR", "AI_TRADE", "AR_BDROP",
        "AR_GRAVI", "AR_MAGNT", "AR_MBALL", "AR_RADIO", "D_SIMDET", "EQ_ASUIT",
        "EQ_CNT", "EQ_CNT_A", "EQ_CNT_B", "EQ_CPS", "EQ_CPS_G", "EQ_CSUIT", "EQ_DTC",
        "EQ_DTC_L", "EQ_DTC_S", "EQ_DTC_U", "EQ_LIFES", "EQ_MKT", "EQ_MKT_U",
        "EQ_PSI_P", "EQ_PSUIT", "EQ_RADIO", "EQ_TSUIT", "II_BOLT", "W_AK_CHR",
        "W_FN_CHR", "W_FR_CHR", "W_HP_CHR", "W_LR_CHR", "W_PM_CHR", "W_TZ_CHR",
        "W_SVD", "W_SVU", "Z_MBALD", "Z_MINCER", "AI_IDOL", "AMMO", "G_F1", "G_RGD5",
        "G_RPG7", "O_HLAMP", "W_RPG7", "D_TORCH", "O_PHYSIC", "W_USP45", "W_VAL",
        "W_VINT", "W_WALTHR", "LVLPOINT", "LVL_CHNG", "W_KNIFE", "AI_BLOOD", "AI_DOG_R",
        "AI_FLESH", "AI_FLE_G", "AI_HIMER", "AI_SPGRP", "ARTEFACT", "D_PDA", "G_FAKE",
        "Z_ACIDF", "Z_BFUZZ", "Z_DEAD", "Z_GALANT", "Z_RADIO", "Z_RUSTYH", "AI_BOAR",
        "EQU_EXO", "EQU_MLTR", "EQU_SCIE", "EQU_STLK", "II_ANTIR", "II_BREAD", "II_DOC",
        "II_MEDKI", "AF_BDROP", "AF_NEEDL", "D_AFMERG", "SCRIPTZN", "AF_BAST",
        "AF_BGRAV", "AF_DUMMY", "AF_EBALL", "AF_FBALL", "AF_GALAN", "AF_RHAIR",
        "AF_THORN", "AF_ZUDA", "AI_DOG_B", "W_SCOPE", "W_SILENC", "W_GLAUNC",
        "SCRPTOBJ", "O_SEARCH", "II_BOTTL", "II_FOOD", "C_HLCPTR", "II_ATTCH",
        "W_MOUNTD", "II_EXPLO", "O_BRKBL", "AI_BURER", "AI_GIANT", "Z_TEAMBS", "A_M209",
        "A_OG7B", "A_VOG25", "W_BM16", "AI_PHANT", "NW_ATTCH", "P_SKELET", "Z_TORRID",
        "AI_FRACT", "SPACE_RS", "AI_SNORK", "O_CLMBL", "SMRTTRRN", "AI_CAT", "II_BTTCH",
        "CLSID_Z_BFUZZ", "Z_AMEBA", "AI_STL_S", "P_DSTRBL", "O_SWITCH", "W_RG6",
        "SM_BLOOD", "SM_BOARW", "SM_BURER", "SM_CAT_S", "SM_CHIMS", "SM_CONTR",
        "SM_FLESH", "SM_GIANT", "SM_IZLOM", "SM_POLTR", "SM_P_DOG", "SM_SNORK",
        "SM_TUSHK", "SM_ZOMBI", "SCRPTART", "SCRPTCAR", "W_STMGUN", "II_BANDG",
        "ON_OFF_G", "RE_SPAWN", "SM_DOG_F", "SM_DOG_P", "Z_NOGRAV", "TORCH_S",
        "E_STLK", "WP_AK74", "WP_BINOC", "WP_BM16", "WP_GROZA", "WP_HPSA", "WP_KNIFE",
        "WP_LR300", "WP_PM", "WP_RG6", "WP_RPG7", "WP_SCOPE", "WP_SHOTG", "WP_SVD",
        "WP_SVU", "WP_USP45", "WP_VAL", "WP_VINT", "WP_WALTH", "ZS_BFUZZ", "ZS_GALAN",
        "ZS_MBALD", "ZS_MINCE", "Z_ZONE", "O_INVBOX", "C_HLCP_S", "O_PHYS_S",
        "SPC_RS_S", "AI_TRD_S", "AI_TRADE_S", "SFACTION", "Z_CFIRE", "D_ADVANC",
        "D_ELITE", "D_FLARE", "SMRT_C_S", "SM_DOG_S", "S_ACTOR", "AMMO_S", "DET_ADVA",
        "DET_ELIT", "DET_SCIE", "DET_SIMP", "E_HLMET", "G_F1_S", "G_RGD5_S", "O_DSTR_S",
        "ON_OFF_S", "SO_HLAMP", "S_ANTIR", "S_BANDG", "S_BOTTL", "S_EXPLO", "S_FOOD",
        "S_INVBOX", "S_MEDKI", "S_M209", "S_OG7B", "S_PDA", "S_VOG25", "WP_ASHTG",
        "WP_GLAUN", "WP_SILEN", "ZS_RADIO", "ZS_TORRD",
    }
    IGNORE_CLSID = {
        "EVENT", "MP_PLBAG",
    }

    # Считывание конфигов
    section_to_clsid = {}
    clsids = {}
    for section in system_ini().sections():
        _class = section.get_string("class", "")
        if len(_class) == 0:
            continue
        if _class in IGNORE_CLSID:
            continue
        section_to_clsid[section.id] = _class
        clsids[_class] = True

    # Сборка потенциально неизвестных clsid
    unknown_clsids = [
        clsid
        for clsid in clsids.keys()
        if clsid not in KNOWN_CLSID
    ]

    # Вывод
    TAB = 4
    OFFSET = ((
        2 + max([len(sect_id) for sect_id in section_to_clsid.keys()]) + TAB
    ) // TAB) * TAB
    with open(fn, "w", encoding="utf-8") as file:
        if len(unknown_clsids) > 0:
            file.write("# You may also need to add these clsids to clsid_to_class:\n")
            for clsid in unknown_clsids:
                file.write(f"#   {clsid}\n")
            file.write("\n")
        file.write("# scan.pm\n")
        file.write("use constant section_to_clsid => {\n")
        for section, clsid in section_to_clsid.items():
            shift = " "*(OFFSET - len(section) - 2)
            file.write(f"\t'{section}'{shift}=> '{clsid}',\n")
        file.write("};\n")

# ----------------------------------------------------------------

def generate() -> None:
    """Основная функция для запуска всех генераций.
    
    Генерирует:

    * Статические таблицы для **ip_test** (``ip_test_db.script``)
    * Таблицу ``section_to_clsid`` для **Universal ACDC**
    """
    print("-"*80)
    ini_system = system_ini()
    print("MOD:", ini_system.gdm)
    print("ALT:", ini_system.gda or "--")
    print("-"*80)
    run(_ip_test_static_tables,  "ip_test")
    run(_universal_acdc_section_to_clsid,  "universal_acdc")
    print("-"*80)
