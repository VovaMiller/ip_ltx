import os
from pathlib import Path

from ip_ltx import Ini


_INI_META = None
_INI_SYSTEM = None
_INI_SPAWN = None
_INI_GAME = None

def _read_ini_meta():
    meta_fp = os.environ.get("META_FILEPATH", "")
    if len(meta_fp) == 0:
        meta_fp = str(Path(os.getcwd()).joinpath(Path("_meta.ltx")))
    if not os.path.isfile(meta_fp):
        raise FileNotFoundError(meta_fp)
    ini = Ini(_name=os.path.basename(meta_fp))
    ini.read(meta_fp)
    return ini

def _read_ini_system():
    ini = Ini(_name="system.ltx", ini_meta=meta_ini())
    ini.read("config\\system.ltx", inside_gamedata=True, encoding=None)
    return ini

def _read_ini_spawn():
    ini = Ini(_name="all.spawn", ini_meta=meta_ini())
    sect_db = meta_ini().s.get("spawn", None)
    if sect_db is None:
        raise Exception("meta-file doesn't have mandatory section [spawn]")
    for path in sect_db._fields.keys():
        ini.read(path, inside_gamedata=True)
    return ini

def _read_ini_game():
    ini = Ini(_name="game.ltx", ini_meta=meta_ini())
    ini.read("config\\game.ltx", inside_gamedata=True, encoding=None)
    return ini

# ----------------------------------------------------------------

def meta_ini() -> Ini:
    global _INI_META
    if _INI_META is None:
        _INI_META = _read_ini_meta()
    return _INI_META

def system_ini() -> Ini:
    global _INI_SYSTEM
    if _INI_SYSTEM is None:
        _INI_SYSTEM = _read_ini_system()
    return _INI_SYSTEM

def spawn_ini() -> Ini:
    global _INI_SPAWN
    if _INI_SPAWN is None:
        _INI_SPAWN = _read_ini_spawn()
    return _INI_SPAWN

def game_ini() -> Ini:
    global _INI_GAME
    if _INI_GAME is None:
        _INI_GAME = _read_ini_game()
    return _INI_GAME
