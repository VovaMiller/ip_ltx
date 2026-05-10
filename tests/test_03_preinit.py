import pytest

from ip_ltx.ini import game_ini, meta_ini, spawn_ini, system_ini
from ip_ltx.misc.task_manager import TaskManager
from ip_ltx.misc.trade import TradeBuy
from ip_ltx.misc.treasure_manager import TreasureManager
from ip_ltx.spawn import get_spawn
from ip_ltx.utils_meta import Levels, ServerClasses, ObjectTypeDetector, CLSIDs
from ip_ltx.xml_data.dialogs import Dialogs
from ip_ltx.xml_data.info_portions import InfoPortions
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

def test_meta_levels():
    _ = Levels()

def test_meta_server_classes():
    _ = ServerClasses()

def test_meta_object_type_detector():
    _ = ObjectTypeDetector()

def test_meta_clsids():
    _ = CLSIDs()

def test_spawn():
    _ = get_spawn()

def test_task_manager():
    _ = TaskManager()

def test_trade():
    _ = TradeBuy()

def test_treasure_manager():
    _ = TreasureManager()

def test_xml_dialogs():
    _ = Dialogs()

def test_xml_info_portions():
    _ = InfoPortions()

def test_xml_string_table():
    _ = StringTable()

def test_xml_texture_desc():
    _ = TextureDesc()
