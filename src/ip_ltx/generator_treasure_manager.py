"""Генерация конфигов, необходимых для тайников из treasure_manager"""

from collections import OrderedDict

from .ini import game_ini
from .utils import print_warning, print_error, run

# ----------------------------------------------------------------

def generate_main(
        fn: str,
        data: OrderedDict[int, str]
) -> None:
    """Генерация конфига для ``treasure_manager.ltx``.
    
    :param fn: Путь/имя файла для вывода.
    :param data: Словарь тайников (ключ - story_id, значение - id тайника)
    """
    with open(fn, "w", encoding="utf-8") as file:
        file.write("[list]\n")
        file.write("\n".join(data.values()))
        file.write("\n")

        for target, id in data.items():
            file.write("\n")
            file.write(f"[{id}]\n")
            file.write(f"target = {target}\n")
            file.write(f"name = {id}_name\n")
            file.write(f"description = {id}_desc\n")

def generate_strings(
        fn: str,
        data: OrderedDict[int, str],
        tab: str = "    "
) -> None:
    """Генерация шаблонов для ``string_table``.
    
    :param fn: Путь/имя файла для вывода.
    :param data: Словарь тайников (ключ - story_id, значение - id тайника)
    :param tab: Отступ, используемый при выводе в файл.
    """
    with open(fn, "w", encoding="utf-8") as file:
        for id in data.values():
            for str_id in [f"{id}_name", f"{id}_desc"]:
                file.write(f"{tab*1}<string id=\"{str_id}\">\n")
                file.write(f"{tab*2}<text>__TODO__</text>\n")
                file.write(f"{tab*1}</string>\n")

# ----------------------------------------------------------------

def generate(
        ids: list[str],
        tab: str = "    "
) -> None:
    """Сгенерировать все необходимые конфиги для указанных тайников.

    *iP v3.0+*

    * :func:`generate_main`
    * :func:`generate_strings`
    
    :param ids: список ID тайников из [story_ids] (``game_story_ids.ltx``)
    :param tab: Отступ, используемый при выводе в файлы.
    """
    if len(ids) == 0:
        print_warning("zero-length input provided")
        return
    ini_game = game_ini()
    if not ini_game.section_exist("story_ids"):
        print_error("game.ltx doesn't have section [story_ids]")
        return
    requested: OrderedDict[str, bool] = OrderedDict(
        [(id, False) for id in ids]
    )
    data = OrderedDict()
    for _sid, _id in ini_game.section("story_ids").fields():
        if (
            not _sid.isdecimal() or
            (_id is None) or
            not _id.startswith('"') or
            not _id.endswith('"')
        ):
            print_warning((
                f"section [story_ids], unexpected line format"
                f" ({_sid if _id is None else f"{_sid} = {_id}"})"
            ))
            continue
        story_id = int(_sid)
        id = _id[1:-1]
        if id in requested:
            if requested[id]:
                print_warning(
                    f"section [story_ids]: duplicate id found (\"{id}\")"
                )
            else:
                requested[id] = True
                data[story_id] = id
    if len(requested) != len(data):
        print_error("some ids were not found")

    print("-"*80)
    for id, fl in requested.items():
        print("{} {}".format("+" if fl else "-", id))
    print("-"*80)

    if len(data) > 0:
        run(generate_main,      "main",     data=data)
        run(generate_strings,   "string",   data=data, tab=tab)
        print("-"*80)
