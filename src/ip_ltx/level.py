from .ini import meta_ini
from .utils import print_warning


_LEVEL_GVIDS: list[tuple[str, int]] | None = None

def _get_level_gvids() -> list[tuple[str, int]]:
    """
    Считывает структуру данных для распознавания локации по game_vertex_id.

    Необходимые для этого данные прописываются в мета-файле
    в секции [level_gvids].
    """
    global _LEVEL_GVIDS
    if _LEVEL_GVIDS is not None:
        return _LEVEL_GVIDS
    
    ini_meta = meta_ini()
    sect_id = "level_gvids"
    if not ini_meta.section_exist(sect_id):
        raise Exception(
            f"meta-file doesn't have mandatory section [{sect_id}]"
        )
    sect = ini_meta.section(sect_id)

    _LEVEL_GVIDS = []
    for loc in sect.lines():
        try:
            gvid = sect.get_uint(loc)
        except Exception as e:
            print_warning(str(e))
        else:
            _LEVEL_GVIDS.append((loc, gvid))
    _LEVEL_GVIDS = sorted(_LEVEL_GVIDS, key=lambda x: -x[1])
    return _LEVEL_GVIDS

# ----------------------------------------------------------------

def get_lvl_by_gvid(gvid: int) -> str | None:
    """Получить имя уровня по game_vertex_id

    :param gvid: game_vertex_id
    :return: Имя уровня или None, если его не удалось получить
    """
    level_gvids = _get_level_gvids()
    for elem in level_gvids:
        elem_lvl, elem_gvid = elem
        if gvid >= elem_gvid:
            return elem_lvl
    return None
