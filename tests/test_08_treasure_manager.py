import pytest

from ip_ltx.misc.treasure_manager import TreasureManager


def test_size():
    tm = TreasureManager()
    assert len(tm) == 215

def test_existence_by_id():
    tm = TreasureManager()
    assert "esc_secret_refuge" in tm
    assert "gar_secret_avoska" in tm
    assert "agr_secret_gray" in tm
    assert "agru_secret_mole_cave" in tm
    assert "val_secret_0032" in tm
    assert "mil_secret_0010" in tm
    assert "yan_secret_0002" in tm
    assert "x16_secret_0000" in tm
    assert "rad_secret_0001" in tm
    assert "pri_secret_0003" in tm
    assert "x18_secret_0000" in tm
    assert "bar_secret_0011" in tm
    assert "ros_secret_0012" in tm

def test_non_existence_by_id():
    tm = TreasureManager()
    assert "esc_secret" not in tm
    assert "esc_secret_refuge_2" not in tm
    assert "5000" not in tm

def test_existence_by_target():
    tm = TreasureManager()
    assert 5000 in tm
    assert 5101 in tm
    assert 5430 in tm
    assert 5469 in tm
    assert 5222 in tm
    assert 5255 in tm

def test_non_existence_by_target():
    tm = TreasureManager()
    assert -5000 not in tm
    assert -1 not in tm
    assert 0 not in tm
    assert 5093 not in tm
    assert 5256 not in tm
    assert 5300 not in tm

def test_getitem_by_id_error():
    tm = TreasureManager()
    with pytest.raises(KeyError):
        _ = tm["esc_grand_secret"]

def test_getitem_by_target_error():
    tm = TreasureManager()
    with pytest.raises(KeyError):
        _ = tm[4999]

def test_data_by_id():
    tm = TreasureManager()
    treasure = tm["val_secret_0029"]
    assert treasure._id == "val_secret_0029"
    assert treasure.target == 5429
    assert treasure.name == "val_secret_0029_name"
    assert treasure.description == "val_secret_0029_description"

def test_data_by_target():
    tm = TreasureManager()
    treasure = tm[5450]
    assert treasure._id == "bar_secret_0015"
    assert treasure.target == 5450
    assert treasure.name == "bar_secret_0015_name"
    assert treasure.description == "bar_secret_0015_description"

def test_data_by_id_and_by_target_equivalence():
    tm = TreasureManager()
    treasure_by_id = tm["mil_secret_0022"]
    treasure_by_target = tm[5222]
    assert treasure_by_id == treasure_by_target

def test_getter():
    tm = TreasureManager()
    assert tm.get("esc_secret_refuge", None) is tm["esc_secret_refuge"]
    assert tm.get(5000, None) is tm[5000]
    assert tm.get("dar_extra_secret", None) is None
    assert tm.get("dar_extra_secret", "-") == "-"
    assert tm.get(123, None) is None
    assert tm.get(123, "-") == "-"

def test_singleton():
    tm_1 = TreasureManager()
    tm_2 = TreasureManager()
    assert tm_1 is tm_2
