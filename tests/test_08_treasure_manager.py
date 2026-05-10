import pytest

from ip_ltx.misc.treasure_manager import TreasureManager


def test_size():
    TM = TreasureManager()
    assert len(TM) == 215

def test_existence_by_id():
    TM = TreasureManager()
    assert "esc_secret_refuge" in TM
    assert "gar_secret_avoska" in TM
    assert "agr_secret_gray" in TM
    assert "agru_secret_mole_cave" in TM
    assert "val_secret_0032" in TM
    assert "mil_secret_0010" in TM
    assert "yan_secret_0002" in TM
    assert "x16_secret_0000" in TM
    assert "rad_secret_0001" in TM
    assert "pri_secret_0003" in TM
    assert "x18_secret_0000" in TM
    assert "bar_secret_0011" in TM
    assert "ros_secret_0012" in TM

def test_non_existence_by_id():
    TM = TreasureManager()
    assert "esc_secret" not in TM
    assert "esc_secret_refuge_2" not in TM
    assert "5000" not in TM

def test_existence_by_target():
    TM = TreasureManager()
    assert 5000 in TM
    assert 5101 in TM
    assert 5430 in TM
    assert 5469 in TM
    assert 5222 in TM
    assert 5255 in TM

def test_non_existence_by_target():
    TM = TreasureManager()
    assert -5000 not in TM
    assert -1 not in TM
    assert 0 not in TM
    assert 5093 not in TM
    assert 5256 not in TM
    assert 5300 not in TM

def test_getitem_by_id_error():
    TM = TreasureManager()
    with pytest.raises(KeyError):
        _ = TM["esc_grand_secret"]

def test_getitem_by_target_error():
    TM = TreasureManager()
    with pytest.raises(KeyError):
        _ = TM[4999]

def test_data_by_id():
    TM = TreasureManager()
    treasure = TM["val_secret_0029"]
    assert treasure._id == "val_secret_0029"
    assert treasure.target == 5429
    assert treasure.name == "val_secret_0029_name"
    assert treasure.description == "val_secret_0029_description"

def test_data_by_target():
    TM = TreasureManager()
    treasure = TM[5450]
    assert treasure._id == "bar_secret_0015"
    assert treasure.target == 5450
    assert treasure.name == "bar_secret_0015_name"
    assert treasure.description == "bar_secret_0015_description"

def test_data_by_id_and_by_target_equivalence():
    TM = TreasureManager()
    treasure_by_id = TM["mil_secret_0022"]
    treasure_by_target = TM[5222]
    assert treasure_by_id == treasure_by_target
