import pytest
import re

from ip_ltx.ini import spawn_ini
from ip_ltx.utils_meta import (
    Levels, ServerClasses, ObjectType, ObjectTypeDetector, CLSIDs
)

# ----------------------------------------------------------------

def test_levels():
    LEVELS = Levels()
    for s in spawn_ini().sections():
        level_calculated = LEVELS.get_lvl_by_gvid(s.get_uint("game_vertex_id"))
        if (m := re.fullmatch(r"alife_(.*)\.ltx", s._src)):
            level_expected = m.group(1).lower()
        else:
            level_expected = "__ERROR__"
        assert level_calculated == level_expected

def test_levels_invalid_gvid():
    LEVELS = Levels()
    with pytest.raises(ValueError):
        _ = LEVELS.get_lvl_by_gvid(-1)

# ----------------------------------------------------------------

def test_server_classes_size():
    SC = ServerClasses()
    assert len(SC) == 83
    
def test_server_classes_existence():
    SC = ServerClasses()

    # existent
    assert "cse_visual" in SC
    assert "cse_abstract" in SC
    assert "cse_shape" in SC
    assert "cse_alife_object" in SC
    assert "cse_alife_dynamic_object" in SC
    assert "cse_alife_item" in SC
    assert "cse_alife_item_weapon_magazined" in SC
    assert "cse_alife_trader" in SC
    assert "cse_alife_custom_zone" in SC
    assert "cse_alife_group_template<cse_alife_monster_base>" in SC
    assert "se_artefact" in SC
    assert "se_monster" in SC
    assert "se_stalker" in SC
    
    # non-existent
    assert "" not in SC
    assert "cse" not in SC
    assert "cse_parabellum" not in SC
    assert "CSE_visual" not in SC
    assert "SE_STALKER" not in SC

def test_server_classes_issubclass():
    SC = ServerClasses()

    # actual subclasses
    assert SC.issubclass("se_weapon_magazined_w_gl", "se_weapon_magazined_w_gl")
    assert SC.issubclass("se_weapon_magazined_w_gl", "cse_alife_item_weapon_magazined_w_gl")
    assert SC.issubclass("se_weapon_magazined_w_gl", "cse_alife_item_weapon_magazined")
    assert SC.issubclass("se_weapon_magazined_w_gl", "cse_alife_item_weapon")
    assert SC.issubclass("se_weapon_magazined_w_gl", "cse_alife_item")
    assert SC.issubclass("se_weapon_magazined_w_gl", "cse_alife_dynamic_object_visual")
    assert SC.issubclass("se_weapon_magazined_w_gl", "cse_alife_inventory_item")
    assert SC.issubclass("se_weapon_magazined_w_gl", "cse_alife_dynamic_object")
    assert SC.issubclass("se_weapon_magazined_w_gl", "cse_visual")
    assert SC.issubclass("se_weapon_magazined_w_gl", "cse_abstract")

    # false subclasses: inversion
    assert not SC.issubclass("cse_alife_item_weapon_magazined_w_gl", "se_weapon_magazined_w_gl")
    assert not SC.issubclass("cse_alife_item_weapon_magazined", "se_weapon_magazined_w_gl")
    assert not SC.issubclass("cse_alife_item_weapon", "se_weapon_magazined_w_gl")
    assert not SC.issubclass("cse_alife_item", "se_weapon_magazined_w_gl")
    assert not SC.issubclass("cse_alife_dynamic_object_visual", "se_weapon_magazined_w_gl")
    assert not SC.issubclass("cse_alife_inventory_item", "se_weapon_magazined_w_gl")
    assert not SC.issubclass("cse_alife_dynamic_object", "se_weapon_magazined_w_gl")
    assert not SC.issubclass("cse_visual", "se_weapon_magazined_w_gl")
    assert not SC.issubclass("cse_abstract", "se_weapon_magazined_w_gl")

    # false subclasses: random
    assert not SC.issubclass("se_weapon_magazined_w_gl", "cse_motion")
    assert not SC.issubclass("se_weapon_magazined_w_gl", "cse_shape")
    assert not SC.issubclass("se_weapon_magazined_w_gl", "cse_alife_item_weapon_shotgun")

    # errors
    with pytest.raises(ValueError):
        _ = SC.issubclass("cse_abstract", "cse_wtf")
    with pytest.raises(ValueError):
        _ = SC.issubclass("cse_wtf", "cse_abstract")
    with pytest.raises(ValueError):
        _ = SC.issubclass("cse_wtf_1", "cse_wtf_2")
    with pytest.raises(ValueError):
        _ = SC.issubclass("cse_abstract", "")
    with pytest.raises(ValueError):
        _ = SC.issubclass("", "cse_abstract")
    with pytest.raises(ValueError):
        _ = SC.issubclass("", "")

# ----------------------------------------------------------------

def test_object_type_is_mob():
    assert ObjectType.MONSTER.is_mob() == True
    assert ObjectType.STALKER.is_mob() == True
    assert ObjectType.ANOMALY.is_mob() == False
    assert ObjectType.ITEM_ART.is_mob() == False
    assert ObjectType.ITEM_WEAPON.is_mob() == False
    assert ObjectType.ITEM_AMMO.is_mob() == False
    assert ObjectType.ITEM_GRENADE.is_mob() == False
    assert ObjectType.ITEM_ADDON.is_mob() == False
    assert ObjectType.ITEM_OUTFIT.is_mob() == False
    assert ObjectType.ITEM_OTHER.is_mob() == False
    assert ObjectType.OTHER.is_mob() == False
    assert ObjectType.UNDEFINED.is_mob() == False

def test_object_type_is_item():
    assert ObjectType.MONSTER.is_item() == False
    assert ObjectType.STALKER.is_item() == False
    assert ObjectType.ANOMALY.is_item() == False
    assert ObjectType.ITEM_ART.is_item() == True
    assert ObjectType.ITEM_WEAPON.is_item() == True
    assert ObjectType.ITEM_AMMO.is_item() == True
    assert ObjectType.ITEM_GRENADE.is_item() == True
    assert ObjectType.ITEM_ADDON.is_item() == True
    assert ObjectType.ITEM_OUTFIT.is_item() == True
    assert ObjectType.ITEM_OTHER.is_item() == True
    assert ObjectType.OTHER.is_item() == False
    assert ObjectType.UNDEFINED.is_item() == False

# ----------------------------------------------------------------

def test_object_type_detector_exact():
    OTD = ObjectTypeDetector()
    assert OTD.get_object_type(None, "se_monster") == ObjectType.MONSTER
    assert OTD.get_object_type(None, "se_stalker") == ObjectType.STALKER
    assert OTD.get_object_type(None, "cse_alife_anomalous_zone") == ObjectType.ANOMALY
    assert OTD.get_object_type(None, "cse_alife_torrid_zone") == ObjectType.ANOMALY
    assert OTD.get_object_type(None, "cse_alife_item") == ObjectType.ITEM_OTHER
    assert OTD.get_object_type(None, "cse_alife_item_artefact") == ObjectType.ITEM_ART
    assert OTD.get_object_type(None, "cse_alife_item_weapon") == ObjectType.ITEM_WEAPON
    assert OTD.get_object_type(None, "cse_alife_item_ammo") == ObjectType.ITEM_AMMO
    assert OTD.get_object_type(None, "cse_alife_item_grenade") == ObjectType.ITEM_GRENADE
    assert OTD.get_object_type("CScope", None) == ObjectType.ITEM_ADDON
    assert OTD.get_object_type("CSilencer", None) == ObjectType.ITEM_ADDON
    assert OTD.get_object_type("CGrenadeLauncher", None) == ObjectType.ITEM_ADDON
    assert OTD.get_object_type(None, "cse_alife_item_custom_outfit") == ObjectType.ITEM_OUTFIT

def test_object_type_detector_inheritance():
    OTD = ObjectTypeDetector()

    # cse_alife_anomalous_zone
    assert OTD.get_object_type(None, "cse_alife_zone_visual") == ObjectType.ANOMALY
    assert OTD.get_object_type(None, "se_zone_anom") == ObjectType.ANOMALY

    # cse_alife_item_artefact
    assert OTD.get_object_type(None, "se_artefact") == ObjectType.ITEM_ART

    # cse_alife_item_weapon
    assert OTD.get_object_type(None, "cse_alife_item_weapon_magazined") == ObjectType.ITEM_WEAPON
    assert OTD.get_object_type(None, "cse_alife_item_weapon_magazined_w_gl") == ObjectType.ITEM_WEAPON
    assert OTD.get_object_type(None, "cse_alife_item_weapon_shotgun") == ObjectType.ITEM_WEAPON
    assert OTD.get_object_type(None, "se_weapon") == ObjectType.ITEM_WEAPON
    assert OTD.get_object_type(None, "se_weapon_shotgun") == ObjectType.ITEM_WEAPON
    assert OTD.get_object_type(None, "se_weapon_magazined") == ObjectType.ITEM_WEAPON
    assert OTD.get_object_type(None, "se_weapon_magazined_w_gl") == ObjectType.ITEM_WEAPON

    # cse_alife_item_custom_outfit
    assert OTD.get_object_type(None, "se_outfit") == ObjectType.ITEM_OUTFIT

    # cse_alife_item (ITEM_OTHER)
    assert OTD.get_object_type(None, "cse_alife_item_torch") == ObjectType.ITEM_OTHER
    assert OTD.get_object_type(None, "cse_alife_item_detector") == ObjectType.ITEM_OTHER
    assert OTD.get_object_type(None, "cse_alife_item_pda") == ObjectType.ITEM_OTHER
    assert OTD.get_object_type(None, "cse_alife_item_document") == ObjectType.ITEM_OTHER
    assert OTD.get_object_type(None, "cse_alife_item_explosive") == ObjectType.ITEM_OTHER
    assert OTD.get_object_type(None, "cse_alife_item_bolt") == ObjectType.ITEM_OTHER
    assert OTD.get_object_type(None, "se_item") == ObjectType.ITEM_OTHER
    assert OTD.get_object_type(None, "se_item_torch") == ObjectType.ITEM_OTHER

def test_object_type_detector_others():
    OTD = ObjectTypeDetector()
    assert OTD.get_object_type("AbsoluteNonsense", None) == ObjectType.OTHER
    assert OTD.get_object_type("G_LEVEL", None) == ObjectType.OTHER
    assert OTD.get_object_type("O_ACTOR", "cse_alife_creature_actor") == ObjectType.OTHER
    assert OTD.get_object_type(None, "cse_abstract") == ObjectType.OTHER
    assert OTD.get_object_type(None, "cse_temporary") == ObjectType.OTHER
    assert OTD.get_object_type(None, "cse_alife_helicopter") == ObjectType.OTHER
    assert OTD.get_object_type(None, "cse_alife_car") == ObjectType.OTHER
    assert OTD.get_object_type(None, "cse_alife_object") == ObjectType.OTHER
    assert OTD.get_object_type(None, "cse_alife_level_changer") == ObjectType.OTHER
    assert OTD.get_object_type(None, "cse_alife_inventory_box") == ObjectType.OTHER
    assert OTD.get_object_type(None, "cse_alife_trader") == ObjectType.OTHER
    assert OTD.get_object_type(None, "cse_alife_monster_base") == ObjectType.OTHER
    assert OTD.get_object_type(None, "cse_alife_human_stalker") == ObjectType.OTHER
    assert OTD.get_object_type(None, "se_car") == ObjectType.OTHER
    assert OTD.get_object_type(None, "se_heli") == ObjectType.OTHER
    assert OTD.get_object_type(None, "se_trader") == ObjectType.OTHER
    assert OTD.get_object_type(None, "se_restrictor") == ObjectType.OTHER
    assert OTD.get_object_type(None, "se_smart_terrain") == ObjectType.OTHER

def test_object_type_detector_undefined():
    OTD = ObjectTypeDetector()
    assert OTD.get_object_type(None, None) == ObjectType.UNDEFINED

# ----------------------------------------------------------------

def test_clsids_size():
    CLSIDS = CLSIDs()
    assert len(CLSIDS) == 192

def test_clsids_existence():
    CLSIDS = CLSIDs()

    # existent
    assert "G_LEVEL" in CLSIDS
    assert "AI_GRAPH" in CLSIDS
    assert "O_ACTOR" in CLSIDS
    assert "AI_STL" in CLSIDS
    assert "C_HLCPTR" in CLSIDS
    assert "ARTEFACT" in CLSIDS
    assert "W_PM" in CLSIDS
    assert "AMMO" in CLSIDS
    assert "W_SCOPE" in CLSIDS
    assert "II_FOOD" in CLSIDS
    assert "EQU_STLK" in CLSIDS
    assert "G_F1" in CLSIDS
    assert "G_RPG7" in CLSIDS
    assert "MP_PLBAG" in CLSIDS
    assert "LVL_CHNG" in CLSIDS
    assert "D_SIMDET" in CLSIDS
    assert "D_PDA" in CLSIDS
    assert "O_SEARCH" in CLSIDS
    assert "O_HLAMP" in CLSIDS
    assert "O_INVBOX" in CLSIDS
    assert "MAIN_MNU" in CLSIDS
    assert "SMRTTRRN" in CLSIDS
    assert "RE_SPAWN" in CLSIDS
    assert "SM_P_DOG" in CLSIDS
    assert "TORCH_S" in CLSIDS
    assert "E_STLK" in CLSIDS
    assert "WP_SCOPE" in CLSIDS
    assert "WP_AK74" in CLSIDS
    assert "ZS_MBALD" in CLSIDS

    # non-existent
    assert "" not in CLSIDS
    assert "ammo" not in CLSIDS
    assert "wp_knife" not in CLSIDS
    assert "WP_SCAR" not in CLSIDS
    assert "WP_AK" not in CLSIDS
    assert "WP_AK74U" not in CLSIDS

def test_clsids_get_client_class():
    CLSIDS = CLSIDs()

    # existent client classes
    assert CLSIDS.get_client_class("G_LEVEL") == "CLevel"
    assert CLSIDS.get_client_class("O_ACTOR") == "CActor"
    assert CLSIDS.get_client_class("W_WMAGGL") == "CWeaponMagazinedWGrenade"

    # no client class
    assert CLSIDS.get_client_class("AI_FLE_G") is None
    assert CLSIDS.get_client_class("AI_GRAPH") is None
    assert CLSIDS.get_client_class("ON_OFF_G") is None

    # invalid clsid
    with pytest.raises(ValueError):
        _ = CLSIDS.get_client_class("")
    with pytest.raises(ValueError):
        _ = CLSIDS.get_client_class("G")
    with pytest.raises(ValueError):
        _ = CLSIDS.get_client_class("AI_FLE_H")

def test_clsids_get_server_class():
    CLSIDS = CLSIDs()

    # existent server classes
    assert CLSIDS.get_server_class("AI_GRAPH") == "cse_alife_graph_point"
    assert CLSIDS.get_server_class("O_ACTOR") == "cse_alife_creature_actor"
    assert CLSIDS.get_server_class("C_NIVA") == "cse_alife_car"

    # no server class
    assert CLSIDS.get_server_class("G_LEVEL") is None
    assert CLSIDS.get_server_class("UI_SINGL") is None
    assert CLSIDS.get_server_class("MAIN_MNU") is None

    # invalid clsid
    with pytest.raises(ValueError):
        _ = CLSIDS.get_server_class("")
    with pytest.raises(ValueError):
        _ = CLSIDS.get_server_class("W")
    with pytest.raises(ValueError):
        _ = CLSIDS.get_server_class("W_KATANA")

def test_clsids_get_object_type_legacy():
    CLSIDS = CLSIDs()

    # [mob_class_to_type] T_MONSTER
    assert CLSIDS.get_object_type("SM_BLOOD") == ObjectType.MONSTER
    assert CLSIDS.get_object_type("SM_BOARW") == ObjectType.MONSTER
    assert CLSIDS.get_object_type("SM_DOG_S") == ObjectType.MONSTER
    assert CLSIDS.get_object_type("SM_FLESH") == ObjectType.MONSTER
    assert CLSIDS.get_object_type("SM_P_DOG") == ObjectType.MONSTER
    assert CLSIDS.get_object_type("SM_BURER") == ObjectType.MONSTER
    assert CLSIDS.get_object_type("SM_CAT_S") == ObjectType.MONSTER
    assert CLSIDS.get_object_type("SM_CHIMS") == ObjectType.MONSTER
    assert CLSIDS.get_object_type("SM_CONTR") == ObjectType.MONSTER
    assert CLSIDS.get_object_type("SM_IZLOM") == ObjectType.MONSTER
    assert CLSIDS.get_object_type("SM_POLTR") == ObjectType.MONSTER
    assert CLSIDS.get_object_type("SM_GIANT") == ObjectType.MONSTER
    assert CLSIDS.get_object_type("SM_ZOMBI") == ObjectType.MONSTER
    assert CLSIDS.get_object_type("SM_SNORK") == ObjectType.MONSTER
    assert CLSIDS.get_object_type("SM_TUSHK") == ObjectType.MONSTER
    assert CLSIDS.get_object_type("SM_DOG_P") == ObjectType.MONSTER
    assert CLSIDS.get_object_type("SM_DOG_F") == ObjectType.MONSTER

    # [mob_class_to_type] T_STALKER
    assert CLSIDS.get_object_type("AI_STL_S") == ObjectType.STALKER

    # [is_anomaly_class]
    assert CLSIDS.get_object_type("Z_MBALD") == ObjectType.ANOMALY
    assert CLSIDS.get_object_type("Z_MINCER") == ObjectType.ANOMALY
    assert CLSIDS.get_object_type("Z_ACIDF") == ObjectType.ANOMALY
    assert CLSIDS.get_object_type("Z_GALANT") == ObjectType.ANOMALY
    assert CLSIDS.get_object_type("Z_RADIO") == ObjectType.ANOMALY
    assert CLSIDS.get_object_type("Z_BFUZZ") == ObjectType.ANOMALY
    assert CLSIDS.get_object_type("Z_RUSTYH") == ObjectType.ANOMALY
    assert CLSIDS.get_object_type("Z_AMEBA") == ObjectType.ANOMALY
    assert CLSIDS.get_object_type("Z_NOGRAV") == ObjectType.ANOMALY
    assert CLSIDS.get_object_type("Z_DEAD") == ObjectType.ANOMALY
    assert CLSIDS.get_object_type("Z_TORRID") == ObjectType.ANOMALY
    assert CLSIDS.get_object_type("ZS_BFUZZ") == ObjectType.ANOMALY
    assert CLSIDS.get_object_type("ZS_MBALD") == ObjectType.ANOMALY
    assert CLSIDS.get_object_type("ZS_GALAN") == ObjectType.ANOMALY
    assert CLSIDS.get_object_type("ZS_MINCE") == ObjectType.ANOMALY

    # [inv_class_to_type] T_ART
    assert CLSIDS.get_object_type("ARTEFACT") == ObjectType.ITEM_ART
    assert CLSIDS.get_object_type("SCRPTART") == ObjectType.ITEM_ART

    # [inv_class_to_type] T_WPN
    assert CLSIDS.get_object_type("WP_AK74") == ObjectType.ITEM_WEAPON
    assert CLSIDS.get_object_type("WP_BM16") == ObjectType.ITEM_WEAPON
    assert CLSIDS.get_object_type("WP_GROZA") == ObjectType.ITEM_WEAPON
    assert CLSIDS.get_object_type("WP_HPSA") == ObjectType.ITEM_WEAPON
    assert CLSIDS.get_object_type("WP_LR300") == ObjectType.ITEM_WEAPON
    assert CLSIDS.get_object_type("WP_PM") == ObjectType.ITEM_WEAPON
    assert CLSIDS.get_object_type("WP_RG6") == ObjectType.ITEM_WEAPON
    assert CLSIDS.get_object_type("WP_RPG7") == ObjectType.ITEM_WEAPON
    assert CLSIDS.get_object_type("WP_SHOTG") == ObjectType.ITEM_WEAPON
    assert CLSIDS.get_object_type("WP_SVD") == ObjectType.ITEM_WEAPON
    assert CLSIDS.get_object_type("WP_SVU") == ObjectType.ITEM_WEAPON
    assert CLSIDS.get_object_type("WP_USP45") == ObjectType.ITEM_WEAPON
    assert CLSIDS.get_object_type("WP_VAL") == ObjectType.ITEM_WEAPON
    assert CLSIDS.get_object_type("WP_VINT") == ObjectType.ITEM_WEAPON
    assert CLSIDS.get_object_type("WP_WALTH") == ObjectType.ITEM_WEAPON

    # [inv_class_to_type] T_AMMO
    assert CLSIDS.get_object_type("AMMO") == ObjectType.ITEM_AMMO
    assert CLSIDS.get_object_type("A_M209") == ObjectType.ITEM_AMMO
    assert CLSIDS.get_object_type("A_OG7B") == ObjectType.ITEM_AMMO
    assert CLSIDS.get_object_type("A_VOG25") == ObjectType.ITEM_AMMO

    # [inv_class_to_type] T_GREN
    assert CLSIDS.get_object_type("G_F1") == ObjectType.ITEM_GRENADE
    assert CLSIDS.get_object_type("G_RGD5") == ObjectType.ITEM_GRENADE

    # [inv_class_to_type] T_ADDON
    assert CLSIDS.get_object_type("W_GLAUNC") == ObjectType.ITEM_ADDON
    assert CLSIDS.get_object_type("WP_SCOPE") == ObjectType.ITEM_ADDON
    assert CLSIDS.get_object_type("W_SILENC") == ObjectType.ITEM_ADDON

    # [inv_class_to_type] T_OUTFIT
    assert CLSIDS.get_object_type("E_STLK") == ObjectType.ITEM_OUTFIT

    # [inv_class_to_type] T_OTHER
    assert CLSIDS.get_object_type("D_SIMDET") == ObjectType.ITEM_OTHER
    assert CLSIDS.get_object_type("II_ANTIR") == ObjectType.ITEM_OTHER
    assert CLSIDS.get_object_type("II_ATTCH") == ObjectType.ITEM_OTHER
    assert CLSIDS.get_object_type("II_BANDG") == ObjectType.ITEM_OTHER
    assert CLSIDS.get_object_type("II_BOTTL") == ObjectType.ITEM_OTHER
    assert CLSIDS.get_object_type("II_FOOD") == ObjectType.ITEM_OTHER
    assert CLSIDS.get_object_type("II_MEDKI") == ObjectType.ITEM_OTHER

def test_clsids_get_object_type_others_with_type():
    CLSIDS = CLSIDs()

    assert CLSIDS.get_object_type("AF_MBALL") == ObjectType.ITEM_ART
    assert CLSIDS.get_object_type("AF_BDROP") == ObjectType.ITEM_ART
    assert CLSIDS.get_object_type("AF_NEEDL") == ObjectType.ITEM_ART
    assert CLSIDS.get_object_type("AF_BAST") == ObjectType.ITEM_ART
    assert CLSIDS.get_object_type("AF_BGRAV") == ObjectType.ITEM_ART
    assert CLSIDS.get_object_type("AF_DUMMY") == ObjectType.ITEM_ART
    assert CLSIDS.get_object_type("AF_ZUDA") == ObjectType.ITEM_ART
    assert CLSIDS.get_object_type("AF_THORN") == ObjectType.ITEM_ART
    assert CLSIDS.get_object_type("AF_FBALL") == ObjectType.ITEM_ART
    assert CLSIDS.get_object_type("AF_EBALL") == ObjectType.ITEM_ART
    assert CLSIDS.get_object_type("AF_RHAIR") == ObjectType.ITEM_ART
    assert CLSIDS.get_object_type("AF_GALAN") == ObjectType.ITEM_ART
    assert CLSIDS.get_object_type("AF_GRAVI") == ObjectType.ITEM_ART

    assert CLSIDS.get_object_type("W_WMAGAZ") == ObjectType.ITEM_WEAPON
    assert CLSIDS.get_object_type("W_WMAGGL") == ObjectType.ITEM_WEAPON
    assert CLSIDS.get_object_type("W_FN2000") == ObjectType.ITEM_WEAPON
    assert CLSIDS.get_object_type("W_AK74") == ObjectType.ITEM_WEAPON
    assert CLSIDS.get_object_type("W_LR300") == ObjectType.ITEM_WEAPON
    assert CLSIDS.get_object_type("W_HPSA") == ObjectType.ITEM_WEAPON
    assert CLSIDS.get_object_type("W_PM") == ObjectType.ITEM_WEAPON
    assert CLSIDS.get_object_type("W_FORT") == ObjectType.ITEM_WEAPON
    assert CLSIDS.get_object_type("W_BINOC") == ObjectType.ITEM_WEAPON
    assert CLSIDS.get_object_type("W_SHOTGN") == ObjectType.ITEM_WEAPON
    assert CLSIDS.get_object_type("W_SVD") == ObjectType.ITEM_WEAPON
    assert CLSIDS.get_object_type("W_SVU") == ObjectType.ITEM_WEAPON
    assert CLSIDS.get_object_type("W_RPG7") == ObjectType.ITEM_WEAPON
    assert CLSIDS.get_object_type("W_VAL") == ObjectType.ITEM_WEAPON
    assert CLSIDS.get_object_type("W_VINT") == ObjectType.ITEM_WEAPON
    assert CLSIDS.get_object_type("W_WALTHR") == ObjectType.ITEM_WEAPON
    assert CLSIDS.get_object_type("W_USP45") == ObjectType.ITEM_WEAPON
    assert CLSIDS.get_object_type("W_GROZA") == ObjectType.ITEM_WEAPON
    assert CLSIDS.get_object_type("W_KNIFE") == ObjectType.ITEM_WEAPON
    assert CLSIDS.get_object_type("W_BM16") == ObjectType.ITEM_WEAPON
    assert CLSIDS.get_object_type("W_RG6") == ObjectType.ITEM_WEAPON
    assert CLSIDS.get_object_type("WP_BINOC") == ObjectType.ITEM_WEAPON
    assert CLSIDS.get_object_type("WP_KNIFE") == ObjectType.ITEM_WEAPON

    assert CLSIDS.get_object_type("W_SCOPE") == ObjectType.ITEM_ADDON

    assert CLSIDS.get_object_type("EQU_SCIE") == ObjectType.ITEM_OUTFIT
    assert CLSIDS.get_object_type("EQU_STLK") == ObjectType.ITEM_OUTFIT
    assert CLSIDS.get_object_type("EQU_MLTR") == ObjectType.ITEM_OUTFIT
    assert CLSIDS.get_object_type("EQU_EXO") == ObjectType.ITEM_OUTFIT

    assert CLSIDS.get_object_type("II_BOLT") == ObjectType.ITEM_OTHER
    assert CLSIDS.get_object_type("II_EXPLO") == ObjectType.ITEM_OTHER
    assert CLSIDS.get_object_type("II_DOC") == ObjectType.ITEM_OTHER
    assert CLSIDS.get_object_type("MP_PLBAG") == ObjectType.ITEM_OTHER
    assert CLSIDS.get_object_type("D_TORCH") == ObjectType.ITEM_OTHER
    assert CLSIDS.get_object_type("D_PDA") == ObjectType.ITEM_OTHER
    assert CLSIDS.get_object_type("TORCH_S") == ObjectType.ITEM_OTHER

def test_clsids_get_object_type_others_without_type():
    CLSIDS = CLSIDs()
    assert CLSIDS.get_object_type("G_LEVEL") == ObjectType.OTHER
    assert CLSIDS.get_object_type("G_PERSIS") == ObjectType.OTHER
    assert CLSIDS.get_object_type("HUD_MNGR") == ObjectType.OTHER
    assert CLSIDS.get_object_type("SV_SINGL") == ObjectType.OTHER
    assert CLSIDS.get_object_type("SV_DM") == ObjectType.OTHER
    assert CLSIDS.get_object_type("SV_TDM") == ObjectType.OTHER
    assert CLSIDS.get_object_type("SV_AHUNT") == ObjectType.OTHER
    assert CLSIDS.get_object_type("CL_SINGL") == ObjectType.OTHER
    assert CLSIDS.get_object_type("CL_DM") == ObjectType.OTHER
    assert CLSIDS.get_object_type("CL_TDM") == ObjectType.OTHER
    assert CLSIDS.get_object_type("CL_AHUNT") == ObjectType.OTHER
    assert CLSIDS.get_object_type("UI_SINGL") == ObjectType.OTHER
    assert CLSIDS.get_object_type("UI_DM") == ObjectType.OTHER
    assert CLSIDS.get_object_type("UI_TDM") == ObjectType.OTHER
    assert CLSIDS.get_object_type("UI_AHUNT") == ObjectType.OTHER
    assert CLSIDS.get_object_type("AI_FLE_G") == ObjectType.OTHER
    assert CLSIDS.get_object_type("AI_GRAPH") == ObjectType.OTHER
    assert CLSIDS.get_object_type("ON_OFF_G") == ObjectType.OTHER
    assert CLSIDS.get_object_type("O_ACTOR") == ObjectType.OTHER
    assert CLSIDS.get_object_type("SPECT") == ObjectType.OTHER
    assert CLSIDS.get_object_type("AI_FLESH") == ObjectType.OTHER
    assert CLSIDS.get_object_type("AI_HIMER") == ObjectType.OTHER
    assert CLSIDS.get_object_type("AI_DOG_R") == ObjectType.OTHER
    assert CLSIDS.get_object_type("AI_STL") == ObjectType.OTHER
    assert CLSIDS.get_object_type("AI_BLOOD") == ObjectType.OTHER
    assert CLSIDS.get_object_type("AI_BOAR") == ObjectType.OTHER
    assert CLSIDS.get_object_type("AI_DOG_B") == ObjectType.OTHER
    assert CLSIDS.get_object_type("AI_DOG_P") == ObjectType.OTHER
    assert CLSIDS.get_object_type("AI_DOG_F") == ObjectType.OTHER
    assert CLSIDS.get_object_type("AI_BURER") == ObjectType.OTHER
    assert CLSIDS.get_object_type("AI_GIANT") == ObjectType.OTHER
    assert CLSIDS.get_object_type("AI_CONTR") == ObjectType.OTHER
    assert CLSIDS.get_object_type("AI_POLTR") == ObjectType.OTHER
    assert CLSIDS.get_object_type("AI_ZOM") == ObjectType.OTHER
    assert CLSIDS.get_object_type("AI_FRACT") == ObjectType.OTHER
    assert CLSIDS.get_object_type("AI_SNORK") == ObjectType.OTHER
    assert CLSIDS.get_object_type("AI_CAT") == ObjectType.OTHER
    assert CLSIDS.get_object_type("AI_TUSH") == ObjectType.OTHER
    assert CLSIDS.get_object_type("AI_PHANT") == ObjectType.OTHER
    assert CLSIDS.get_object_type("AI_TRADE") == ObjectType.OTHER
    assert CLSIDS.get_object_type("AI_CROW") == ObjectType.OTHER
    assert CLSIDS.get_object_type("C_NIVA") == ObjectType.OTHER
    assert CLSIDS.get_object_type("C_HLCPTR") == ObjectType.OTHER
    assert CLSIDS.get_object_type("G_RPG7") == ObjectType.OTHER
    assert CLSIDS.get_object_type("G_FAKE") == ObjectType.OTHER
    assert CLSIDS.get_object_type("Z_ZONE") == ObjectType.OTHER
    assert CLSIDS.get_object_type("LVL_CHNG") == ObjectType.OTHER
    assert CLSIDS.get_object_type("SCRIPTZN") == ObjectType.OTHER
    assert CLSIDS.get_object_type("SMRTZONE") == ObjectType.OTHER
    assert CLSIDS.get_object_type("Z_TEAMBS") == ObjectType.OTHER
    assert CLSIDS.get_object_type("SPACE_RS") == ObjectType.OTHER
    assert CLSIDS.get_object_type("O_SEARCH") == ObjectType.OTHER
    assert CLSIDS.get_object_type("W_MOUNTD") == ObjectType.OTHER
    assert CLSIDS.get_object_type("W_STMGUN") == ObjectType.OTHER
    assert CLSIDS.get_object_type("O_HLAMP") == ObjectType.OTHER
    assert CLSIDS.get_object_type("O_PHYSIC") == ObjectType.OTHER
    assert CLSIDS.get_object_type("SCRPTOBJ") == ObjectType.OTHER
    assert CLSIDS.get_object_type("O_BRKBL") == ObjectType.OTHER
    assert CLSIDS.get_object_type("O_CLMBL") == ObjectType.OTHER
    assert CLSIDS.get_object_type("P_SKELET") == ObjectType.OTHER
    assert CLSIDS.get_object_type("P_DSTRBL") == ObjectType.OTHER
    assert CLSIDS.get_object_type("O_INVBOX") == ObjectType.OTHER
    assert CLSIDS.get_object_type("MAIN_MNU") == ObjectType.OTHER
    assert CLSIDS.get_object_type("SMRTTRRN") == ObjectType.OTHER
    assert CLSIDS.get_object_type("RE_SPAWN") == ObjectType.OTHER
    assert CLSIDS.get_object_type("O_SWITCH") == ObjectType.OTHER
    assert CLSIDS.get_object_type("AI_TRD_S") == ObjectType.OTHER
    assert CLSIDS.get_object_type("C_HLCP_S") == ObjectType.OTHER
    assert CLSIDS.get_object_type("SPC_RS_S") == ObjectType.OTHER
    assert CLSIDS.get_object_type("O_PHYS_S") == ObjectType.OTHER
    assert CLSIDS.get_object_type("SCRPTCAR") == ObjectType.OTHER

def test_clsids_get_object_type_undefined():
    CLSIDS = CLSIDs()
    assert CLSIDS.get_object_type("AI_RAT_G") == ObjectType.UNDEFINED
    assert CLSIDS.get_object_type("AI_RAT") == ObjectType.UNDEFINED
    assert CLSIDS.get_object_type("EVENT") == ObjectType.UNDEFINED
    assert CLSIDS.get_object_type("AI_SPGRP") == ObjectType.UNDEFINED
    assert CLSIDS.get_object_type("II_BTTCH") == ObjectType.UNDEFINED
    assert CLSIDS.get_object_type("NW_ATTCH") == ObjectType.UNDEFINED

def test_clsids_get_object_type_errors():
    CLSIDS = CLSIDs()
    with pytest.raises(ValueError):
        _ = CLSIDS.get_object_type("")
    with pytest.raises(ValueError):
        _ = CLSIDS.get_object_type("MAIN")
    with pytest.raises(ValueError):
        _ = CLSIDS.get_object_type("MNU")
    with pytest.raises(ValueError):
        _ = CLSIDS.get_object_type("d_pda")
    with pytest.raises(ValueError):
        _ = CLSIDS.get_object_type("O_O")

def test_clsids_is_monster():
    CLSIDS = CLSIDs()
    assert CLSIDS.is_monster("SM_BOARW") == True
    assert CLSIDS.is_monster("SM_CAT_S") == True
    assert CLSIDS.is_monster("SM_POLTR") == True
    assert CLSIDS.is_monster("SM_SNORK") == True
    assert CLSIDS.is_monster("Z_RADIO") == False
    assert CLSIDS.is_monster("SCRPTART") == False
    assert CLSIDS.is_monster("WP_LR300") == False
    assert CLSIDS.is_monster("A_M209") == False
    with pytest.raises(ValueError):
        _ = CLSIDS.is_monster("ERROR")

def test_clsids_is_stalker():
    CLSIDS = CLSIDs()
    assert CLSIDS.is_stalker("AI_STL_S") == True
    assert CLSIDS.is_stalker("SM_ZOMBI") == False
    assert CLSIDS.is_stalker("G_F1") == False
    assert CLSIDS.is_stalker("W_GLAUNC") == False
    assert CLSIDS.is_stalker("E_STLK") == False
    with pytest.raises(ValueError):
        _ = CLSIDS.is_stalker("ERROR")

def test_clsids_is_anomaly():
    CLSIDS = CLSIDs()
    assert CLSIDS.is_anomaly("Z_GALANT") == True
    assert CLSIDS.is_anomaly("Z_RUSTYH") == True
    assert CLSIDS.is_anomaly("Z_TORRID") == True
    assert CLSIDS.is_anomaly("ZS_MINCE") == True
    assert CLSIDS.is_anomaly("D_SIMDET") == False
    assert CLSIDS.is_anomaly("SM_BLOOD") == False
    assert CLSIDS.is_anomaly("ARTEFACT") == False
    assert CLSIDS.is_anomaly("G_RGD5") == False
    with pytest.raises(ValueError):
        _ = CLSIDS.is_anomaly("ERROR")

def test_clsids_is_artefact():
    CLSIDS = CLSIDs()
    assert CLSIDS.is_artefact("ARTEFACT") == True
    assert CLSIDS.is_artefact("SCRPTART") == True
    assert CLSIDS.is_artefact("A_VOG25") == False
    assert CLSIDS.is_artefact("G_F1") == False
    assert CLSIDS.is_artefact("II_ATTCH") == False
    assert CLSIDS.is_artefact("SM_BLOOD") == False
    with pytest.raises(ValueError):
        _ = CLSIDS.is_artefact("ERROR")

def test_clsids_is_weapon():
    CLSIDS = CLSIDs()
    assert CLSIDS.is_weapon("WP_AK74") == True
    assert CLSIDS.is_weapon("WP_BM16") == True
    assert CLSIDS.is_weapon("WP_PM") == True
    assert CLSIDS.is_weapon("WP_SVD") == True
    assert CLSIDS.is_weapon("AMMO") == False
    assert CLSIDS.is_weapon("A_OG7B") == False
    assert CLSIDS.is_weapon("G_F1") == False
    assert CLSIDS.is_weapon("W_SILENC") == False
    with pytest.raises(ValueError):
        _ = CLSIDS.is_weapon("ERROR")

def test_clsids_is_ammo():
    CLSIDS = CLSIDs()
    assert CLSIDS.is_ammo("AMMO") == True
    assert CLSIDS.is_ammo("A_M209") == True
    assert CLSIDS.is_ammo("A_OG7B") == True
    assert CLSIDS.is_ammo("A_VOG25") == True
    assert CLSIDS.is_ammo("G_RGD5") == False
    assert CLSIDS.is_ammo("W_GLAUNC") == False
    assert CLSIDS.is_ammo("II_ATTCH") == False
    assert CLSIDS.is_ammo("Z_NOGRAV") == False
    with pytest.raises(ValueError):
        _ = CLSIDS.is_ammo("ERROR")

def test_clsids_is_grenade():
    CLSIDS = CLSIDs()
    assert CLSIDS.is_grenade("G_F1") == True
    assert CLSIDS.is_grenade("G_RGD5") == True
    assert CLSIDS.is_grenade("A_M209") == False
    assert CLSIDS.is_grenade("A_OG7B") == False
    assert CLSIDS.is_grenade("A_VOG25") == False
    assert CLSIDS.is_grenade("AMMO") == False
    with pytest.raises(ValueError):
        _ = CLSIDS.is_grenade("ERROR")

def test_clsids_is_weapon_addon():
    CLSIDS = CLSIDs()
    assert CLSIDS.is_weapon_addon("W_GLAUNC") == True
    assert CLSIDS.is_weapon_addon("WP_SCOPE") == True
    assert CLSIDS.is_weapon_addon("W_SILENC") == True
    assert CLSIDS.is_weapon_addon("II_ATTCH") == False
    assert CLSIDS.is_weapon_addon("II_BOTTL") == False
    assert CLSIDS.is_weapon_addon("SCRPTART") == False
    assert CLSIDS.is_weapon_addon("SM_CAT_S") == False
    with pytest.raises(ValueError):
        _ = CLSIDS.is_weapon_addon("ERROR")

def test_clsids_is_outfit():
    CLSIDS = CLSIDs()
    assert CLSIDS.is_outfit("E_STLK") == True
    assert CLSIDS.is_outfit("SM_FLESH") == False
    assert CLSIDS.is_outfit("AI_STL_S") == False
    assert CLSIDS.is_outfit("ZS_BFUZZ") == False
    assert CLSIDS.is_outfit("W_SILENC") == False
    with pytest.raises(ValueError):
        _ = CLSIDS.is_outfit("ERROR")

def test_clsids_is_mob():
    CLSIDS = CLSIDs()
    assert CLSIDS.is_mob("ARTEFACT") == False
    assert CLSIDS.is_mob("WP_HPSA") == False
    assert CLSIDS.is_mob("A_VOG25") == False
    assert CLSIDS.is_mob("G_RGD5") == False
    assert CLSIDS.is_mob("WP_SCOPE") == False
    assert CLSIDS.is_mob("E_STLK") == False
    assert CLSIDS.is_mob("II_FOOD") == False
    assert CLSIDS.is_mob("SM_CHIMS") == True
    assert CLSIDS.is_mob("AI_TRADE") == False
    assert CLSIDS.is_mob("AI_STL_S") == True
    assert CLSIDS.is_mob("Z_RADIO") == False
    with pytest.raises(ValueError):
        _ = CLSIDS.is_mob("ERROR")

def test_clsids_is_item():
    CLSIDS = CLSIDs()
    assert CLSIDS.is_item("ARTEFACT") == True
    assert CLSIDS.is_item("WP_HPSA") == True
    assert CLSIDS.is_item("A_VOG25") == True
    assert CLSIDS.is_item("G_RGD5") == True
    assert CLSIDS.is_item("WP_SCOPE") == True
    assert CLSIDS.is_item("E_STLK") == True
    assert CLSIDS.is_item("II_FOOD") == True
    assert CLSIDS.is_item("SM_CHIMS") == False
    assert CLSIDS.is_item("SM_TUSHK") == False
    assert CLSIDS.is_item("AI_STL_S") == False
    assert CLSIDS.is_item("Z_RADIO") == False
    with pytest.raises(ValueError):
        _ = CLSIDS.is_item("ERROR")

# ----------------------------------------------------------------
