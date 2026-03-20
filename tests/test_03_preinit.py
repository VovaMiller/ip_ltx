import pytest

from ip_ltx.ini import game_ini, meta_ini, spawn_ini, system_ini
from ip_ltx.level import get_lvl_by_gvid
from ip_ltx.spawn import get_spawn
from ip_ltx.task_manager import get_task_manager
from ip_ltx.trade import get_buy_k
from ip_ltx.treasure_manager import treasure_manager_ini
from ip_ltx.xml_data.dialogs import Dialogs
from ip_ltx.xml_data.string_table import StringTable
from ip_ltx.xml_data.texture_desc import TextureDesc


def test_meta_ini():
    _ = meta_ini()

def test_game_ini():
    _ = game_ini()

def test_system_ini():
    _ = system_ini()

def test_spawn_ini():
    _ = spawn_ini()

def test_level():
    _ = get_lvl_by_gvid(1)

def test_spawn():
    _ = get_spawn()

def test_task_manager():
    _ = get_task_manager()

def test_trade():
    _ = get_buy_k("bread")

def test_treasure_manager():
    _ = treasure_manager_ini()

def test_xml_dialogs():
    _ = Dialogs()

def test_xml_string_table():
    _ = StringTable()

def test_xml_texture_desc():
    _ = TextureDesc()
