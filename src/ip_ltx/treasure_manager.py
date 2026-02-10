import os.path

from ip_ltx import Ini, Section
from ini import meta_ini

# ----------------------------------------------------------------

_INI = None
_ID_BY_SID = None

def _exception(msg):
    raise Exception("[{}] {}", os.path.basename(__file__), msg)

def _print(msg):
    print("[{}] {}".format(os.path.basename(__file__), msg))

def _initialize():
    tm_fp = "config\\misc\\treasure_manager.ltx"
    tm_fn = os.path.basename(tm_fp)
    ini_0 = Ini(_name="treasure_manager.ltx", ini_meta=meta_ini())
    ini_0.read(tm_fp, inside_gamedata=True)
    if not ini_0.section_exist("list"):
        _exception("Mandatory section [list] was not found!")
    
    # reading each treasure
    ini = Ini(_name="treasure_manager.ltx")
    id_by_sid = {}
    for treasure_id, _ in ini_0.section("list").fields():
        if not ini_0.section_exist(treasure_id):
            _exception("Treasure '{}' from [list] doesn't exist!".format(treasure_id))
        treasure_section = ini_0.section(treasure_id)
        sid = treasure_section.get_number("target")
        if (type(sid) != int) or (sid < 0):
            _exception("Treasure '{}' has invalid 'target' value ()!".format(
                treasure_id, treasure_section.get_string("target")
            ))
        if sid in id_by_sid:
            _exception("Target {} is used at least twice: see '{}' and '{}'".format(
                sid, id_by_sid[sid], treasure_id
            ))
        ini.s[treasure_id] = Section(id=treasure_id, init=treasure_section, _src=tm_fn)
        id_by_sid[sid] = treasure_id

    # warn about unlisted treasure sections
    for sect in ini_0.sections():
        if sect.id not in ["list", "lvl_condlist", "lvl_adjacent"]:
            try:
                target = sect.get_number("target")
            except:
                _print("Unrecognized section: '{}'".format(sect.id))
            else:
                if target not in id_by_sid:
                    _print("Treasure '{}' is unlisted!".format(sect.id))

    global _INI
    global _ID_BY_SID
    _INI = ini
    _ID_BY_SID = id_by_sid

# ----------------------------------------------------------------

def treasure_manager_ini() -> Ini:
    global _INI
    if _INI is None:
        _initialize()
    if _INI is None:
        raise Exception("_INI was not initialized properly")
    return _INI

def treasure_by_sid(sid: int) -> Section | None:
    global _INI
    global _ID_BY_SID
    if (_INI is None) or (_ID_BY_SID is None):
        _initialize()
    if _INI is None:
        raise Exception("_INI was not initialized properly")
    if _ID_BY_SID is None:
        raise Exception("_ID_BY_SID was not initialized properly")
    if sid not in _ID_BY_SID:
        return None
    return _INI.section(_ID_BY_SID[sid])
