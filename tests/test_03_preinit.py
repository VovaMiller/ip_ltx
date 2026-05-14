from ip_ltx.ini import game_ini, meta_ini, spawn_ini, system_ini
from ip_ltx.misc.task_manager import TaskManager
from ip_ltx.misc.trade import TradeBuy
from ip_ltx.misc.treasure_manager import TreasureManager
from ip_ltx.spawn import get_spawn
from ip_ltx.utils_meta import CLSIDs, GameLevels, ObjectTypeDetector, ServerClasses
from ip_ltx.xml_data.dialogs import Dialogs
from ip_ltx.xml_data.info_portions import InfoPortions
from ip_ltx.xml_data.string_table import StringTable
from ip_ltx.xml_data.texture_desc import TextureDesc

# Allowing variable assignment without using it
# ruff: noqa: F841

def test_meta_ini():
    ini_meta = meta_ini()

def test_game_ini():
    ini_game = game_ini()

def test_system_ini():
    ini_system = system_ini()

def test_spawn_ini():
    ini_spawn = spawn_ini()

def test_meta_levels():
    game_levels = GameLevels()

def test_meta_server_classes():
    server_classes = ServerClasses()

def test_meta_object_type_detector():
    object_type_detector = ObjectTypeDetector()

def test_meta_clsids():
    clsids = CLSIDs()

def test_spawn():
    spawn = get_spawn()

def test_task_manager():
    task_manager = TaskManager()

def test_trade():
    trade = TradeBuy()

def test_treasure_manager():
    treasure_manager = TreasureManager()

def test_xml_dialogs():
    dialogs = Dialogs()

def test_xml_info_portions():
    info_portions = InfoPortions()

def test_xml_string_table():
    string_table = StringTable()

def test_xml_texture_desc():
    texture_desc = TextureDesc()
