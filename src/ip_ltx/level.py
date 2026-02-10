from ini import meta_ini


_LEVEL_GVIDS = None

def _get_level_gvids():
    """
        Считывает структуру данных для распознавания локации по game_vertex_id.
        Необходимые для этого данные прописываются в мета-файле в секции [level_gvids].
    """
    global _LEVEL_GVIDS
    if _LEVEL_GVIDS is not None:
        return _LEVEL_GVIDS
    sect_db = meta_ini().s.get("level_gvids", None)
    if sect_db is None:
        raise Exception("meta-file doesn't have mandatory section [level_gvids]")
    _LEVEL_GVIDS = []
    for k, v in sect_db._fields.items():
        _LEVEL_GVIDS.append((str(k), int(v)))
    _LEVEL_GVIDS = sorted(_LEVEL_GVIDS, key=lambda x: -x[1])
    return _LEVEL_GVIDS

# ----------------------------------------------------------------

def get_lvl_by_gvid(gvid) -> str | None:
    """
        Получить имя уровня по game_vertex_id.
        Возвращает None, если получить имя не удалось.
    """
    level_gvids = _get_level_gvids()
    for elem in level_gvids:
        elem_lvl, elem_gvid = elem
        if gvid >= elem_gvid:
            return elem_lvl
    return None
