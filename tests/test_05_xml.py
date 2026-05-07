import pytest

from ip_ltx.xml_data.info_portions import InfoPortions

# ----------------------------------------------------------------

def test_info_portions_len():
    IP = InfoPortions()
    assert len(IP) == 1707

def test_info_portions_existence():
    IP = InfoPortions()

    # existent
    assert "tutorial_artefact_start" in IP
    assert "esc_kill_gunslinger" in IP
    assert "agr_rush_start" in IP
    assert "pri_kamaz_start" in IP
    assert "level_changer_icons" in IP

    # non-existent
    assert "tutorial_artefact" not in IP
    assert "tutorial_artefact_start2" not in IP
    assert "esc_kill_trader" not in IP

def test_info_portions_data_1():
    IP = InfoPortions()
    info = IP["esc_kill_gunslinger"]
    assert info.disable == []
    assert info.article == ["about_enciclopedia", "sl_beginning"]
    assert info.article_disable == []
    assert info.task == ["storyline_eliminate_gunslinger"]
    assert info.action == []

def test_info_portions_data_2():
    IP = InfoPortions()
    info = IP["agr_krot_band_done"]
    assert info.disable == ["agr_krot_band_start", "agr_can_ask_krot_about_gunslinger"]
    assert info.article == []
    assert info.article_disable == []
    assert info.task == []
    assert info.action == []

def test_info_portions_data_3():
    IP = InfoPortions()
    info = IP["mil_cook_map_spot"]
    assert info.disable == []
    assert info.article == []
    assert info.article_disable == []
    assert info.task == []
    assert info.action == ["mil_tasks.set_cook_mapspot"]

# ----------------------------------------------------------------
