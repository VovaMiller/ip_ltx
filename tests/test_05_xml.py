from ip_ltx.xml_data.info_portions import InfoPortions

# ----------------------------------------------------------------

def test_info_portions_len():
    info_portions = InfoPortions()
    assert len(info_portions) == 1707

def test_info_portions_existence():
    info_portions = InfoPortions()

    # existent
    assert "tutorial_artefact_start" in info_portions
    assert "esc_kill_gunslinger" in info_portions
    assert "agr_rush_start" in info_portions
    assert "pri_kamaz_start" in info_portions
    assert "level_changer_icons" in info_portions

    # non-existent
    assert "tutorial_artefact" not in info_portions
    assert "tutorial_artefact_start2" not in info_portions
    assert "esc_kill_trader" not in info_portions

def test_info_portions_data_1():
    info_portions = InfoPortions()
    info = info_portions["esc_kill_gunslinger"]
    assert info.disable == []
    assert info.article == ["about_enciclopedia", "sl_beginning"]
    assert info.article_disable == []
    assert info.task == ["storyline_eliminate_gunslinger"]
    assert info.action == []

def test_info_portions_data_2():
    info_portions = InfoPortions()
    info = info_portions["agr_krot_band_done"]
    assert info.disable == ["agr_krot_band_start", "agr_can_ask_krot_about_gunslinger"]
    assert info.article == []
    assert info.article_disable == []
    assert info.task == []
    assert info.action == []

def test_info_portions_data_3():
    info_portions = InfoPortions()
    info = info_portions["mil_cook_map_spot"]
    assert info.disable == []
    assert info.article == []
    assert info.article_disable == []
    assert info.task == []
    assert info.action == ["mil_tasks.set_cook_mapspot"]

# ----------------------------------------------------------------
