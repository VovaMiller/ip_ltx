import re

import pytest

from ip_ltx.ini import spawn_ini
from ip_ltx.utils_meta import (
    CLSIDs,
    GameLevels,
    ObjectType,
    ObjectTypeDetector,
    ServerClasses,
)

# ----------------------------------------------------------------

def test_levels():
    game_levels = GameLevels()
    for s in spawn_ini().sections():
        level_calculated = game_levels.get_lvl_by_gvid(s.get_uint("game_vertex_id"))
        if (m := re.fullmatch(r"alife_(.*)\.ltx", s._src)):
            level_expected = m.group(1).lower()
        else:
            level_expected = "__ERROR__"
        assert level_calculated == level_expected

def test_levels_invalid_gvid():
    game_levels = GameLevels()
    with pytest.raises(ValueError):
        _ = game_levels.get_lvl_by_gvid(-1)

# ----------------------------------------------------------------

def test_server_classes_size():
    server_classes = ServerClasses()
    assert len(server_classes) == 83

def test_server_classes_existence():
    server_classes = ServerClasses()

    # existent
    assert "cse_visual" in server_classes
    assert "cse_abstract" in server_classes
    assert "cse_shape" in server_classes
    assert "cse_alife_object" in server_classes
    assert "cse_alife_dynamic_object" in server_classes
    assert "cse_alife_item" in server_classes
    assert "cse_alife_item_weapon_magazined" in server_classes
    assert "cse_alife_trader" in server_classes
    assert "cse_alife_custom_zone" in server_classes
    assert "cse_alife_group_template<cse_alife_monster_base>" in server_classes
    assert "se_artefact" in server_classes
    assert "se_monster" in server_classes
    assert "se_stalker" in server_classes

    # non-existent
    assert "" not in server_classes
    assert "cse" not in server_classes
    assert "cse_parabellum" not in server_classes
    assert "CSE_visual" not in server_classes
    assert "SE_STALKER" not in server_classes

def test_server_classes_issubclass():
    server_classes = ServerClasses()

    # actual subclasses
    assert server_classes.issubclass("se_weapon_magazined_w_gl", "se_weapon_magazined_w_gl")
    assert server_classes.issubclass("se_weapon_magazined_w_gl", "cse_alife_item_weapon_magazined_w_gl")
    assert server_classes.issubclass("se_weapon_magazined_w_gl", "cse_alife_item_weapon_magazined")
    assert server_classes.issubclass("se_weapon_magazined_w_gl", "cse_alife_item_weapon")
    assert server_classes.issubclass("se_weapon_magazined_w_gl", "cse_alife_item")
    assert server_classes.issubclass("se_weapon_magazined_w_gl", "cse_alife_dynamic_object_visual")
    assert server_classes.issubclass("se_weapon_magazined_w_gl", "cse_alife_inventory_item")
    assert server_classes.issubclass("se_weapon_magazined_w_gl", "cse_alife_dynamic_object")
    assert server_classes.issubclass("se_weapon_magazined_w_gl", "cse_visual")
    assert server_classes.issubclass("se_weapon_magazined_w_gl", "cse_abstract")

    # false subclasses: inversion
    assert not server_classes.issubclass("cse_alife_item_weapon_magazined_w_gl", "se_weapon_magazined_w_gl")
    assert not server_classes.issubclass("cse_alife_item_weapon_magazined", "se_weapon_magazined_w_gl")
    assert not server_classes.issubclass("cse_alife_item_weapon", "se_weapon_magazined_w_gl")
    assert not server_classes.issubclass("cse_alife_item", "se_weapon_magazined_w_gl")
    assert not server_classes.issubclass("cse_alife_dynamic_object_visual", "se_weapon_magazined_w_gl")
    assert not server_classes.issubclass("cse_alife_inventory_item", "se_weapon_magazined_w_gl")
    assert not server_classes.issubclass("cse_alife_dynamic_object", "se_weapon_magazined_w_gl")
    assert not server_classes.issubclass("cse_visual", "se_weapon_magazined_w_gl")
    assert not server_classes.issubclass("cse_abstract", "se_weapon_magazined_w_gl")

    # false subclasses: random
    assert not server_classes.issubclass("se_weapon_magazined_w_gl", "cse_motion")
    assert not server_classes.issubclass("se_weapon_magazined_w_gl", "cse_shape")
    assert not server_classes.issubclass("se_weapon_magazined_w_gl", "cse_alife_item_weapon_shotgun")

    # errors
    with pytest.raises(ValueError):
        _ = server_classes.issubclass("cse_abstract", "cse_wtf")
    with pytest.raises(ValueError):
        _ = server_classes.issubclass("cse_wtf", "cse_abstract")
    with pytest.raises(ValueError):
        _ = server_classes.issubclass("cse_wtf_1", "cse_wtf_2")
    with pytest.raises(ValueError):
        _ = server_classes.issubclass("cse_abstract", "")
    with pytest.raises(ValueError):
        _ = server_classes.issubclass("", "cse_abstract")
    with pytest.raises(ValueError):
        _ = server_classes.issubclass("", "")

# ----------------------------------------------------------------

def test_object_type_is_mob():
    assert ObjectType.MONSTER.is_mob()          is True
    assert ObjectType.STALKER.is_mob()          is True
    assert ObjectType.ANOMALY.is_mob()          is False
    assert ObjectType.ITEM_ART.is_mob()         is False
    assert ObjectType.ITEM_WEAPON.is_mob()      is False
    assert ObjectType.ITEM_AMMO.is_mob()        is False
    assert ObjectType.ITEM_GRENADE.is_mob()     is False
    assert ObjectType.ITEM_ADDON.is_mob()       is False
    assert ObjectType.ITEM_OUTFIT.is_mob()      is False
    assert ObjectType.ITEM_OTHER.is_mob()       is False
    assert ObjectType.OTHER.is_mob()            is False
    assert ObjectType.UNDEFINED.is_mob()        is False

def test_object_type_is_item():
    assert ObjectType.MONSTER.is_item()         is False
    assert ObjectType.STALKER.is_item()         is False
    assert ObjectType.ANOMALY.is_item()         is False
    assert ObjectType.ITEM_ART.is_item()        is True
    assert ObjectType.ITEM_WEAPON.is_item()     is True
    assert ObjectType.ITEM_AMMO.is_item()       is True
    assert ObjectType.ITEM_GRENADE.is_item()    is True
    assert ObjectType.ITEM_ADDON.is_item()      is True
    assert ObjectType.ITEM_OUTFIT.is_item()     is True
    assert ObjectType.ITEM_OTHER.is_item()      is True
    assert ObjectType.OTHER.is_item()           is False
    assert ObjectType.UNDEFINED.is_item()       is False

# ----------------------------------------------------------------

def test_object_type_detector_exact():
    object_type_detector = ObjectTypeDetector()
    assert object_type_detector.get(None, "se_monster") == ObjectType.MONSTER
    assert object_type_detector.get(None, "se_stalker") == ObjectType.STALKER
    assert object_type_detector.get(None, "cse_alife_anomalous_zone") == ObjectType.ANOMALY
    assert object_type_detector.get(None, "cse_alife_torrid_zone") == ObjectType.ANOMALY
    assert object_type_detector.get(None, "cse_alife_item") == ObjectType.ITEM_OTHER
    assert object_type_detector.get(None, "cse_alife_item_artefact") == ObjectType.ITEM_ART
    assert object_type_detector.get(None, "cse_alife_item_weapon") == ObjectType.ITEM_WEAPON
    assert object_type_detector.get(None, "cse_alife_item_ammo") == ObjectType.ITEM_AMMO
    assert object_type_detector.get(None, "cse_alife_item_grenade") == ObjectType.ITEM_GRENADE
    assert object_type_detector.get("CScope", None) == ObjectType.ITEM_ADDON
    assert object_type_detector.get("CSilencer", None) == ObjectType.ITEM_ADDON
    assert object_type_detector.get("CGrenadeLauncher", None) == ObjectType.ITEM_ADDON
    assert object_type_detector.get(None, "cse_alife_item_custom_outfit") == ObjectType.ITEM_OUTFIT

def test_object_type_detector_inheritance():
    object_type_detector = ObjectTypeDetector()

    # cse_alife_anomalous_zone
    assert object_type_detector.get(None, "cse_alife_zone_visual") == ObjectType.ANOMALY
    assert object_type_detector.get(None, "se_zone_anom") == ObjectType.ANOMALY

    # cse_alife_item_artefact
    assert object_type_detector.get(None, "se_artefact") == ObjectType.ITEM_ART

    # cse_alife_item_weapon
    assert object_type_detector.get(None, "cse_alife_item_weapon_magazined") == ObjectType.ITEM_WEAPON
    assert object_type_detector.get(None, "cse_alife_item_weapon_magazined_w_gl") == ObjectType.ITEM_WEAPON
    assert object_type_detector.get(None, "cse_alife_item_weapon_shotgun") == ObjectType.ITEM_WEAPON
    assert object_type_detector.get(None, "se_weapon") == ObjectType.ITEM_WEAPON
    assert object_type_detector.get(None, "se_weapon_shotgun") == ObjectType.ITEM_WEAPON
    assert object_type_detector.get(None, "se_weapon_magazined") == ObjectType.ITEM_WEAPON
    assert object_type_detector.get(None, "se_weapon_magazined_w_gl") == ObjectType.ITEM_WEAPON

    # cse_alife_item_custom_outfit
    assert object_type_detector.get(None, "se_outfit") == ObjectType.ITEM_OUTFIT

    # cse_alife_item (ITEM_OTHER)
    assert object_type_detector.get(None, "cse_alife_item_torch") == ObjectType.ITEM_OTHER
    assert object_type_detector.get(None, "cse_alife_item_detector") == ObjectType.ITEM_OTHER
    assert object_type_detector.get(None, "cse_alife_item_pda") == ObjectType.ITEM_OTHER
    assert object_type_detector.get(None, "cse_alife_item_document") == ObjectType.ITEM_OTHER
    assert object_type_detector.get(None, "cse_alife_item_explosive") == ObjectType.ITEM_OTHER
    assert object_type_detector.get(None, "cse_alife_item_bolt") == ObjectType.ITEM_OTHER
    assert object_type_detector.get(None, "se_item") == ObjectType.ITEM_OTHER
    assert object_type_detector.get(None, "se_item_torch") == ObjectType.ITEM_OTHER

def test_object_type_detector_others():
    object_type_detector = ObjectTypeDetector()
    assert object_type_detector.get("AbsoluteNonsense", None) == ObjectType.OTHER
    assert object_type_detector.get("G_LEVEL", None) == ObjectType.OTHER
    assert object_type_detector.get("O_ACTOR", "cse_alife_creature_actor") == ObjectType.OTHER
    assert object_type_detector.get(None, "cse_abstract") == ObjectType.OTHER
    assert object_type_detector.get(None, "cse_temporary") == ObjectType.OTHER
    assert object_type_detector.get(None, "cse_alife_helicopter") == ObjectType.OTHER
    assert object_type_detector.get(None, "cse_alife_car") == ObjectType.OTHER
    assert object_type_detector.get(None, "cse_alife_object") == ObjectType.OTHER
    assert object_type_detector.get(None, "cse_alife_level_changer") == ObjectType.OTHER
    assert object_type_detector.get(None, "cse_alife_inventory_box") == ObjectType.OTHER
    assert object_type_detector.get(None, "cse_alife_trader") == ObjectType.OTHER
    assert object_type_detector.get(None, "cse_alife_monster_base") == ObjectType.OTHER
    assert object_type_detector.get(None, "cse_alife_human_stalker") == ObjectType.OTHER
    assert object_type_detector.get(None, "se_car") == ObjectType.OTHER
    assert object_type_detector.get(None, "se_heli") == ObjectType.OTHER
    assert object_type_detector.get(None, "se_trader") == ObjectType.OTHER
    assert object_type_detector.get(None, "se_restrictor") == ObjectType.OTHER
    assert object_type_detector.get(None, "se_smart_terrain") == ObjectType.OTHER

def test_object_type_detector_undefined():
    object_type_detector = ObjectTypeDetector()
    assert object_type_detector.get(None, None) == ObjectType.UNDEFINED

# ----------------------------------------------------------------

def test_clsids_size():
    clsids = CLSIDs()
    assert len(clsids) == 192

def test_clsids_existence():
    clsids = CLSIDs()

    # existent
    assert "G_LEVEL" in clsids
    assert "AI_GRAPH" in clsids
    assert "O_ACTOR" in clsids
    assert "AI_STL" in clsids
    assert "C_HLCPTR" in clsids
    assert "ARTEFACT" in clsids
    assert "W_PM" in clsids
    assert "AMMO" in clsids
    assert "W_SCOPE" in clsids
    assert "II_FOOD" in clsids
    assert "EQU_STLK" in clsids
    assert "G_F1" in clsids
    assert "G_RPG7" in clsids
    assert "MP_PLBAG" in clsids
    assert "LVL_CHNG" in clsids
    assert "D_SIMDET" in clsids
    assert "D_PDA" in clsids
    assert "O_SEARCH" in clsids
    assert "O_HLAMP" in clsids
    assert "O_INVBOX" in clsids
    assert "MAIN_MNU" in clsids
    assert "SMRTTRRN" in clsids
    assert "RE_SPAWN" in clsids
    assert "SM_P_DOG" in clsids
    assert "TORCH_S" in clsids
    assert "E_STLK" in clsids
    assert "WP_SCOPE" in clsids
    assert "WP_AK74" in clsids
    assert "ZS_MBALD" in clsids

    # non-existent
    assert "" not in clsids
    assert "ammo" not in clsids
    assert "wp_knife" not in clsids
    assert "WP_SCAR" not in clsids
    assert "WP_AK" not in clsids
    assert "WP_AK74U" not in clsids

def test_clsids_get_client_class():
    clsids = CLSIDs()

    # existent client classes
    assert clsids.get_client_class("G_LEVEL") == "CLevel"
    assert clsids.get_client_class("O_ACTOR") == "CActor"
    assert clsids.get_client_class("W_WMAGGL") == "CWeaponMagazinedWGrenade"

    # no client class
    assert clsids.get_client_class("AI_FLE_G") is None
    assert clsids.get_client_class("AI_GRAPH") is None
    assert clsids.get_client_class("ON_OFF_G") is None

    # invalid clsid
    with pytest.raises(ValueError):
        _ = clsids.get_client_class("")
    with pytest.raises(ValueError):
        _ = clsids.get_client_class("G")
    with pytest.raises(ValueError):
        _ = clsids.get_client_class("AI_FLE_H")

def test_clsids_get_server_class():
    clsids = CLSIDs()

    # existent server classes
    assert clsids.get_server_class("AI_GRAPH") == "cse_alife_graph_point"
    assert clsids.get_server_class("O_ACTOR") == "cse_alife_creature_actor"
    assert clsids.get_server_class("C_NIVA") == "cse_alife_car"

    # no server class
    assert clsids.get_server_class("G_LEVEL") is None
    assert clsids.get_server_class("UI_SINGL") is None
    assert clsids.get_server_class("MAIN_MNU") is None

    # invalid clsid
    with pytest.raises(ValueError):
        _ = clsids.get_server_class("")
    with pytest.raises(ValueError):
        _ = clsids.get_server_class("W")
    with pytest.raises(ValueError):
        _ = clsids.get_server_class("W_KATANA")

def test_clsids_get_object_type_legacy():
    clsids = CLSIDs()

    # [mob_class_to_type] T_MONSTER
    assert clsids.get_object_type("SM_BLOOD") == ObjectType.MONSTER
    assert clsids.get_object_type("SM_BOARW") == ObjectType.MONSTER
    assert clsids.get_object_type("SM_DOG_S") == ObjectType.MONSTER
    assert clsids.get_object_type("SM_FLESH") == ObjectType.MONSTER
    assert clsids.get_object_type("SM_P_DOG") == ObjectType.MONSTER
    assert clsids.get_object_type("SM_BURER") == ObjectType.MONSTER
    assert clsids.get_object_type("SM_CAT_S") == ObjectType.MONSTER
    assert clsids.get_object_type("SM_CHIMS") == ObjectType.MONSTER
    assert clsids.get_object_type("SM_CONTR") == ObjectType.MONSTER
    assert clsids.get_object_type("SM_IZLOM") == ObjectType.MONSTER
    assert clsids.get_object_type("SM_POLTR") == ObjectType.MONSTER
    assert clsids.get_object_type("SM_GIANT") == ObjectType.MONSTER
    assert clsids.get_object_type("SM_ZOMBI") == ObjectType.MONSTER
    assert clsids.get_object_type("SM_SNORK") == ObjectType.MONSTER
    assert clsids.get_object_type("SM_TUSHK") == ObjectType.MONSTER
    assert clsids.get_object_type("SM_DOG_P") == ObjectType.MONSTER
    assert clsids.get_object_type("SM_DOG_F") == ObjectType.MONSTER

    # [mob_class_to_type] T_STALKER
    assert clsids.get_object_type("AI_STL_S") == ObjectType.STALKER

    # [is_anomaly_class]
    assert clsids.get_object_type("Z_MBALD") == ObjectType.ANOMALY
    assert clsids.get_object_type("Z_MINCER") == ObjectType.ANOMALY
    assert clsids.get_object_type("Z_ACIDF") == ObjectType.ANOMALY
    assert clsids.get_object_type("Z_GALANT") == ObjectType.ANOMALY
    assert clsids.get_object_type("Z_RADIO") == ObjectType.ANOMALY
    assert clsids.get_object_type("Z_BFUZZ") == ObjectType.ANOMALY
    assert clsids.get_object_type("Z_RUSTYH") == ObjectType.ANOMALY
    assert clsids.get_object_type("Z_AMEBA") == ObjectType.ANOMALY
    assert clsids.get_object_type("Z_NOGRAV") == ObjectType.ANOMALY
    assert clsids.get_object_type("Z_DEAD") == ObjectType.ANOMALY
    assert clsids.get_object_type("Z_TORRID") == ObjectType.ANOMALY
    assert clsids.get_object_type("ZS_BFUZZ") == ObjectType.ANOMALY
    assert clsids.get_object_type("ZS_MBALD") == ObjectType.ANOMALY
    assert clsids.get_object_type("ZS_GALAN") == ObjectType.ANOMALY
    assert clsids.get_object_type("ZS_MINCE") == ObjectType.ANOMALY

    # [inv_class_to_type] T_ART
    assert clsids.get_object_type("ARTEFACT") == ObjectType.ITEM_ART
    assert clsids.get_object_type("SCRPTART") == ObjectType.ITEM_ART

    # [inv_class_to_type] T_WPN
    assert clsids.get_object_type("WP_AK74") == ObjectType.ITEM_WEAPON
    assert clsids.get_object_type("WP_BM16") == ObjectType.ITEM_WEAPON
    assert clsids.get_object_type("WP_GROZA") == ObjectType.ITEM_WEAPON
    assert clsids.get_object_type("WP_HPSA") == ObjectType.ITEM_WEAPON
    assert clsids.get_object_type("WP_LR300") == ObjectType.ITEM_WEAPON
    assert clsids.get_object_type("WP_PM") == ObjectType.ITEM_WEAPON
    assert clsids.get_object_type("WP_RG6") == ObjectType.ITEM_WEAPON
    assert clsids.get_object_type("WP_RPG7") == ObjectType.ITEM_WEAPON
    assert clsids.get_object_type("WP_SHOTG") == ObjectType.ITEM_WEAPON
    assert clsids.get_object_type("WP_SVD") == ObjectType.ITEM_WEAPON
    assert clsids.get_object_type("WP_SVU") == ObjectType.ITEM_WEAPON
    assert clsids.get_object_type("WP_USP45") == ObjectType.ITEM_WEAPON
    assert clsids.get_object_type("WP_VAL") == ObjectType.ITEM_WEAPON
    assert clsids.get_object_type("WP_VINT") == ObjectType.ITEM_WEAPON
    assert clsids.get_object_type("WP_WALTH") == ObjectType.ITEM_WEAPON

    # [inv_class_to_type] T_AMMO
    assert clsids.get_object_type("AMMO") == ObjectType.ITEM_AMMO
    assert clsids.get_object_type("A_M209") == ObjectType.ITEM_AMMO
    assert clsids.get_object_type("A_OG7B") == ObjectType.ITEM_AMMO
    assert clsids.get_object_type("A_VOG25") == ObjectType.ITEM_AMMO

    # [inv_class_to_type] T_GREN
    assert clsids.get_object_type("G_F1") == ObjectType.ITEM_GRENADE
    assert clsids.get_object_type("G_RGD5") == ObjectType.ITEM_GRENADE

    # [inv_class_to_type] T_ADDON
    assert clsids.get_object_type("W_GLAUNC") == ObjectType.ITEM_ADDON
    assert clsids.get_object_type("WP_SCOPE") == ObjectType.ITEM_ADDON
    assert clsids.get_object_type("W_SILENC") == ObjectType.ITEM_ADDON

    # [inv_class_to_type] T_OUTFIT
    assert clsids.get_object_type("E_STLK") == ObjectType.ITEM_OUTFIT

    # [inv_class_to_type] T_OTHER
    assert clsids.get_object_type("D_SIMDET") == ObjectType.ITEM_OTHER
    assert clsids.get_object_type("II_ANTIR") == ObjectType.ITEM_OTHER
    assert clsids.get_object_type("II_ATTCH") == ObjectType.ITEM_OTHER
    assert clsids.get_object_type("II_BANDG") == ObjectType.ITEM_OTHER
    assert clsids.get_object_type("II_BOTTL") == ObjectType.ITEM_OTHER
    assert clsids.get_object_type("II_FOOD") == ObjectType.ITEM_OTHER
    assert clsids.get_object_type("II_MEDKI") == ObjectType.ITEM_OTHER

def test_clsids_get_object_type_others_with_type():
    clsids = CLSIDs()

    assert clsids.get_object_type("AF_MBALL") == ObjectType.ITEM_ART
    assert clsids.get_object_type("AF_BDROP") == ObjectType.ITEM_ART
    assert clsids.get_object_type("AF_NEEDL") == ObjectType.ITEM_ART
    assert clsids.get_object_type("AF_BAST") == ObjectType.ITEM_ART
    assert clsids.get_object_type("AF_BGRAV") == ObjectType.ITEM_ART
    assert clsids.get_object_type("AF_DUMMY") == ObjectType.ITEM_ART
    assert clsids.get_object_type("AF_ZUDA") == ObjectType.ITEM_ART
    assert clsids.get_object_type("AF_THORN") == ObjectType.ITEM_ART
    assert clsids.get_object_type("AF_FBALL") == ObjectType.ITEM_ART
    assert clsids.get_object_type("AF_EBALL") == ObjectType.ITEM_ART
    assert clsids.get_object_type("AF_RHAIR") == ObjectType.ITEM_ART
    assert clsids.get_object_type("AF_GALAN") == ObjectType.ITEM_ART
    assert clsids.get_object_type("AF_GRAVI") == ObjectType.ITEM_ART

    assert clsids.get_object_type("W_WMAGAZ") == ObjectType.ITEM_WEAPON
    assert clsids.get_object_type("W_WMAGGL") == ObjectType.ITEM_WEAPON
    assert clsids.get_object_type("W_FN2000") == ObjectType.ITEM_WEAPON
    assert clsids.get_object_type("W_AK74") == ObjectType.ITEM_WEAPON
    assert clsids.get_object_type("W_LR300") == ObjectType.ITEM_WEAPON
    assert clsids.get_object_type("W_HPSA") == ObjectType.ITEM_WEAPON
    assert clsids.get_object_type("W_PM") == ObjectType.ITEM_WEAPON
    assert clsids.get_object_type("W_FORT") == ObjectType.ITEM_WEAPON
    assert clsids.get_object_type("W_BINOC") == ObjectType.ITEM_WEAPON
    assert clsids.get_object_type("W_SHOTGN") == ObjectType.ITEM_WEAPON
    assert clsids.get_object_type("W_SVD") == ObjectType.ITEM_WEAPON
    assert clsids.get_object_type("W_SVU") == ObjectType.ITEM_WEAPON
    assert clsids.get_object_type("W_RPG7") == ObjectType.ITEM_WEAPON
    assert clsids.get_object_type("W_VAL") == ObjectType.ITEM_WEAPON
    assert clsids.get_object_type("W_VINT") == ObjectType.ITEM_WEAPON
    assert clsids.get_object_type("W_WALTHR") == ObjectType.ITEM_WEAPON
    assert clsids.get_object_type("W_USP45") == ObjectType.ITEM_WEAPON
    assert clsids.get_object_type("W_GROZA") == ObjectType.ITEM_WEAPON
    assert clsids.get_object_type("W_KNIFE") == ObjectType.ITEM_WEAPON
    assert clsids.get_object_type("W_BM16") == ObjectType.ITEM_WEAPON
    assert clsids.get_object_type("W_RG6") == ObjectType.ITEM_WEAPON
    assert clsids.get_object_type("WP_BINOC") == ObjectType.ITEM_WEAPON
    assert clsids.get_object_type("WP_KNIFE") == ObjectType.ITEM_WEAPON

    assert clsids.get_object_type("W_SCOPE") == ObjectType.ITEM_ADDON

    assert clsids.get_object_type("EQU_SCIE") == ObjectType.ITEM_OUTFIT
    assert clsids.get_object_type("EQU_STLK") == ObjectType.ITEM_OUTFIT
    assert clsids.get_object_type("EQU_MLTR") == ObjectType.ITEM_OUTFIT
    assert clsids.get_object_type("EQU_EXO") == ObjectType.ITEM_OUTFIT

    assert clsids.get_object_type("II_BOLT") == ObjectType.ITEM_OTHER
    assert clsids.get_object_type("II_EXPLO") == ObjectType.ITEM_OTHER
    assert clsids.get_object_type("II_DOC") == ObjectType.ITEM_OTHER
    assert clsids.get_object_type("MP_PLBAG") == ObjectType.ITEM_OTHER
    assert clsids.get_object_type("D_TORCH") == ObjectType.ITEM_OTHER
    assert clsids.get_object_type("D_PDA") == ObjectType.ITEM_OTHER
    assert clsids.get_object_type("TORCH_S") == ObjectType.ITEM_OTHER

def test_clsids_get_object_type_others_without_type():
    clsids = CLSIDs()
    assert clsids.get_object_type("G_LEVEL") == ObjectType.OTHER
    assert clsids.get_object_type("G_PERSIS") == ObjectType.OTHER
    assert clsids.get_object_type("HUD_MNGR") == ObjectType.OTHER
    assert clsids.get_object_type("SV_SINGL") == ObjectType.OTHER
    assert clsids.get_object_type("SV_DM") == ObjectType.OTHER
    assert clsids.get_object_type("SV_TDM") == ObjectType.OTHER
    assert clsids.get_object_type("SV_AHUNT") == ObjectType.OTHER
    assert clsids.get_object_type("CL_SINGL") == ObjectType.OTHER
    assert clsids.get_object_type("CL_DM") == ObjectType.OTHER
    assert clsids.get_object_type("CL_TDM") == ObjectType.OTHER
    assert clsids.get_object_type("CL_AHUNT") == ObjectType.OTHER
    assert clsids.get_object_type("UI_SINGL") == ObjectType.OTHER
    assert clsids.get_object_type("UI_DM") == ObjectType.OTHER
    assert clsids.get_object_type("UI_TDM") == ObjectType.OTHER
    assert clsids.get_object_type("UI_AHUNT") == ObjectType.OTHER
    assert clsids.get_object_type("AI_FLE_G") == ObjectType.OTHER
    assert clsids.get_object_type("AI_GRAPH") == ObjectType.OTHER
    assert clsids.get_object_type("ON_OFF_G") == ObjectType.OTHER
    assert clsids.get_object_type("O_ACTOR") == ObjectType.OTHER
    assert clsids.get_object_type("SPECT") == ObjectType.OTHER
    assert clsids.get_object_type("AI_FLESH") == ObjectType.OTHER
    assert clsids.get_object_type("AI_HIMER") == ObjectType.OTHER
    assert clsids.get_object_type("AI_DOG_R") == ObjectType.OTHER
    assert clsids.get_object_type("AI_STL") == ObjectType.OTHER
    assert clsids.get_object_type("AI_BLOOD") == ObjectType.OTHER
    assert clsids.get_object_type("AI_BOAR") == ObjectType.OTHER
    assert clsids.get_object_type("AI_DOG_B") == ObjectType.OTHER
    assert clsids.get_object_type("AI_DOG_P") == ObjectType.OTHER
    assert clsids.get_object_type("AI_DOG_F") == ObjectType.OTHER
    assert clsids.get_object_type("AI_BURER") == ObjectType.OTHER
    assert clsids.get_object_type("AI_GIANT") == ObjectType.OTHER
    assert clsids.get_object_type("AI_CONTR") == ObjectType.OTHER
    assert clsids.get_object_type("AI_POLTR") == ObjectType.OTHER
    assert clsids.get_object_type("AI_ZOM") == ObjectType.OTHER
    assert clsids.get_object_type("AI_FRACT") == ObjectType.OTHER
    assert clsids.get_object_type("AI_SNORK") == ObjectType.OTHER
    assert clsids.get_object_type("AI_CAT") == ObjectType.OTHER
    assert clsids.get_object_type("AI_TUSH") == ObjectType.OTHER
    assert clsids.get_object_type("AI_PHANT") == ObjectType.OTHER
    assert clsids.get_object_type("AI_TRADE") == ObjectType.OTHER
    assert clsids.get_object_type("AI_CROW") == ObjectType.OTHER
    assert clsids.get_object_type("C_NIVA") == ObjectType.OTHER
    assert clsids.get_object_type("C_HLCPTR") == ObjectType.OTHER
    assert clsids.get_object_type("G_RPG7") == ObjectType.OTHER
    assert clsids.get_object_type("G_FAKE") == ObjectType.OTHER
    assert clsids.get_object_type("Z_ZONE") == ObjectType.OTHER
    assert clsids.get_object_type("LVL_CHNG") == ObjectType.OTHER
    assert clsids.get_object_type("SCRIPTZN") == ObjectType.OTHER
    assert clsids.get_object_type("SMRTZONE") == ObjectType.OTHER
    assert clsids.get_object_type("Z_TEAMBS") == ObjectType.OTHER
    assert clsids.get_object_type("SPACE_RS") == ObjectType.OTHER
    assert clsids.get_object_type("O_SEARCH") == ObjectType.OTHER
    assert clsids.get_object_type("W_MOUNTD") == ObjectType.OTHER
    assert clsids.get_object_type("W_STMGUN") == ObjectType.OTHER
    assert clsids.get_object_type("O_HLAMP") == ObjectType.OTHER
    assert clsids.get_object_type("O_PHYSIC") == ObjectType.OTHER
    assert clsids.get_object_type("SCRPTOBJ") == ObjectType.OTHER
    assert clsids.get_object_type("O_BRKBL") == ObjectType.OTHER
    assert clsids.get_object_type("O_CLMBL") == ObjectType.OTHER
    assert clsids.get_object_type("P_SKELET") == ObjectType.OTHER
    assert clsids.get_object_type("P_DSTRBL") == ObjectType.OTHER
    assert clsids.get_object_type("O_INVBOX") == ObjectType.OTHER
    assert clsids.get_object_type("MAIN_MNU") == ObjectType.OTHER
    assert clsids.get_object_type("SMRTTRRN") == ObjectType.OTHER
    assert clsids.get_object_type("RE_SPAWN") == ObjectType.OTHER
    assert clsids.get_object_type("O_SWITCH") == ObjectType.OTHER
    assert clsids.get_object_type("AI_TRD_S") == ObjectType.OTHER
    assert clsids.get_object_type("C_HLCP_S") == ObjectType.OTHER
    assert clsids.get_object_type("SPC_RS_S") == ObjectType.OTHER
    assert clsids.get_object_type("O_PHYS_S") == ObjectType.OTHER
    assert clsids.get_object_type("SCRPTCAR") == ObjectType.OTHER

def test_clsids_get_object_type_undefined():
    clsids = CLSIDs()
    assert clsids.get_object_type("AI_RAT_G") == ObjectType.UNDEFINED
    assert clsids.get_object_type("AI_RAT") == ObjectType.UNDEFINED
    assert clsids.get_object_type("EVENT") == ObjectType.UNDEFINED
    assert clsids.get_object_type("AI_SPGRP") == ObjectType.UNDEFINED
    assert clsids.get_object_type("II_BTTCH") == ObjectType.UNDEFINED
    assert clsids.get_object_type("NW_ATTCH") == ObjectType.UNDEFINED

def test_clsids_get_object_type_errors():
    clsids = CLSIDs()
    with pytest.raises(ValueError):
        _ = clsids.get_object_type("")
    with pytest.raises(ValueError):
        _ = clsids.get_object_type("MAIN")
    with pytest.raises(ValueError):
        _ = clsids.get_object_type("MNU")
    with pytest.raises(ValueError):
        _ = clsids.get_object_type("d_pda")
    with pytest.raises(ValueError):
        _ = clsids.get_object_type("O_O")

def test_clsids_is_monster():
    clsids = CLSIDs()
    assert clsids.is_monster("SM_BOARW")        is True
    assert clsids.is_monster("SM_CAT_S")        is True
    assert clsids.is_monster("SM_POLTR")        is True
    assert clsids.is_monster("SM_SNORK")        is True
    assert clsids.is_monster("Z_RADIO")         is False
    assert clsids.is_monster("SCRPTART")        is False
    assert clsids.is_monster("WP_LR300")        is False
    assert clsids.is_monster("A_M209")          is False
    with pytest.raises(ValueError):
        _ = clsids.is_monster("ERROR")

def test_clsids_is_stalker():
    clsids = CLSIDs()
    assert clsids.is_stalker("AI_STL_S")        is True
    assert clsids.is_stalker("SM_ZOMBI")        is False
    assert clsids.is_stalker("G_F1")            is False
    assert clsids.is_stalker("W_GLAUNC")        is False
    assert clsids.is_stalker("E_STLK")          is False
    with pytest.raises(ValueError):
        _ = clsids.is_stalker("ERROR")

def test_clsids_is_anomaly():
    clsids = CLSIDs()
    assert clsids.is_anomaly("Z_GALANT")        is True
    assert clsids.is_anomaly("Z_RUSTYH")        is True
    assert clsids.is_anomaly("Z_TORRID")        is True
    assert clsids.is_anomaly("ZS_MINCE")        is True
    assert clsids.is_anomaly("D_SIMDET")        is False
    assert clsids.is_anomaly("SM_BLOOD")        is False
    assert clsids.is_anomaly("ARTEFACT")        is False
    assert clsids.is_anomaly("G_RGD5")          is False
    with pytest.raises(ValueError):
        _ = clsids.is_anomaly("ERROR")

def test_clsids_is_artefact():
    clsids = CLSIDs()
    assert clsids.is_artefact("ARTEFACT")       is True
    assert clsids.is_artefact("SCRPTART")       is True
    assert clsids.is_artefact("A_VOG25")        is False
    assert clsids.is_artefact("G_F1")           is False
    assert clsids.is_artefact("II_ATTCH")       is False
    assert clsids.is_artefact("SM_BLOOD")       is False
    with pytest.raises(ValueError):
        _ = clsids.is_artefact("ERROR")

def test_clsids_is_weapon():
    clsids = CLSIDs()
    assert clsids.is_weapon("WP_AK74")          is True
    assert clsids.is_weapon("WP_BM16")          is True
    assert clsids.is_weapon("WP_PM")            is True
    assert clsids.is_weapon("WP_SVD")           is True
    assert clsids.is_weapon("AMMO")             is False
    assert clsids.is_weapon("A_OG7B")           is False
    assert clsids.is_weapon("G_F1")             is False
    assert clsids.is_weapon("W_SILENC")         is False
    with pytest.raises(ValueError):
        _ = clsids.is_weapon("ERROR")

def test_clsids_is_ammo():
    clsids = CLSIDs()
    assert clsids.is_ammo("AMMO")               is True
    assert clsids.is_ammo("A_M209")             is True
    assert clsids.is_ammo("A_OG7B")             is True
    assert clsids.is_ammo("A_VOG25")            is True
    assert clsids.is_ammo("G_RGD5")             is False
    assert clsids.is_ammo("W_GLAUNC")           is False
    assert clsids.is_ammo("II_ATTCH")           is False
    assert clsids.is_ammo("Z_NOGRAV")           is False
    with pytest.raises(ValueError):
        _ = clsids.is_ammo("ERROR")

def test_clsids_is_grenade():
    clsids = CLSIDs()
    assert clsids.is_grenade("G_F1")            is True
    assert clsids.is_grenade("G_RGD5")          is True
    assert clsids.is_grenade("A_M209")          is False
    assert clsids.is_grenade("A_OG7B")          is False
    assert clsids.is_grenade("A_VOG25")         is False
    assert clsids.is_grenade("AMMO")            is False
    with pytest.raises(ValueError):
        _ = clsids.is_grenade("ERROR")

def test_clsids_is_weapon_addon():
    clsids = CLSIDs()
    assert clsids.is_weapon_addon("W_GLAUNC")   is True
    assert clsids.is_weapon_addon("WP_SCOPE")   is True
    assert clsids.is_weapon_addon("W_SILENC")   is True
    assert clsids.is_weapon_addon("II_ATTCH")   is False
    assert clsids.is_weapon_addon("II_BOTTL")   is False
    assert clsids.is_weapon_addon("SCRPTART")   is False
    assert clsids.is_weapon_addon("SM_CAT_S")   is False
    with pytest.raises(ValueError):
        _ = clsids.is_weapon_addon("ERROR")

def test_clsids_is_outfit():
    clsids = CLSIDs()
    assert clsids.is_outfit("E_STLK")           is True
    assert clsids.is_outfit("SM_FLESH")         is False
    assert clsids.is_outfit("AI_STL_S")         is False
    assert clsids.is_outfit("ZS_BFUZZ")         is False
    assert clsids.is_outfit("W_SILENC")         is False
    with pytest.raises(ValueError):
        _ = clsids.is_outfit("ERROR")

def test_clsids_is_mob():
    clsids = CLSIDs()
    assert clsids.is_mob("ARTEFACT")            is False
    assert clsids.is_mob("WP_HPSA")             is False
    assert clsids.is_mob("A_VOG25")             is False
    assert clsids.is_mob("G_RGD5")              is False
    assert clsids.is_mob("WP_SCOPE")            is False
    assert clsids.is_mob("E_STLK")              is False
    assert clsids.is_mob("II_FOOD")             is False
    assert clsids.is_mob("SM_CHIMS")            is True
    assert clsids.is_mob("AI_TRADE")            is False
    assert clsids.is_mob("AI_STL_S")            is True
    assert clsids.is_mob("Z_RADIO")             is False
    with pytest.raises(ValueError):
        _ = clsids.is_mob("ERROR")

def test_clsids_is_item():
    clsids = CLSIDs()
    assert clsids.is_item("ARTEFACT")           is True
    assert clsids.is_item("WP_HPSA")            is True
    assert clsids.is_item("A_VOG25")            is True
    assert clsids.is_item("G_RGD5")             is True
    assert clsids.is_item("WP_SCOPE")           is True
    assert clsids.is_item("E_STLK")             is True
    assert clsids.is_item("II_FOOD")            is True
    assert clsids.is_item("SM_CHIMS")           is False
    assert clsids.is_item("SM_TUSHK")           is False
    assert clsids.is_item("AI_STL_S")           is False
    assert clsids.is_item("Z_RADIO")            is False
    with pytest.raises(ValueError):
        _ = clsids.is_item("ERROR")

# ----------------------------------------------------------------
