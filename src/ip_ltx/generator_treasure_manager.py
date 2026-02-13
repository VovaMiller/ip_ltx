import traceback
from pathlib import Path
from collections import OrderedDict

from .ini import game_ini
from .utils import print_warning, print_error

# ----------------------------------------------------------------

def generate_main(fn, data):
    with open(fn, "w", encoding="utf-8") as file:
        file.write("[list]\n")
        file.write("\n".join(data.values()))
        file.write("\n")

        for target, id in data.items():
            file.write("\n")
            file.write("[{}]\n".format(id))
            file.write("target = {}\n".format(target))
            file.write("name = {}_name\n".format(id))
            file.write("description = {}_desc\n".format(id))

def generate_strings(fn, data):
    tab = "    "
    with open(fn, "w", encoding="utf-8") as file:
        for id in data.values():
            for str_id in ["{}_name".format(id), "{}_desc".format(id)]:
                file.write("{}<string id=\"{}\">\n".format(tab*1, str_id))
                file.write("{}<text>__TODO__</text>\n".format(tab*2))
                file.write("{}</string>\n".format(tab*1))

# ----------------------------------------------------------------

def _run(f, tag, kwargs={}):
    fn = "{}__{}.txt".format(Path(__file__).stem, tag)
    try:
        f(fn, **kwargs)
    except Exception as e:
        print("")
        print("! {}".format(fn))
        print(traceback.format_exc())
        print("", flush=True)
    else:
        print("+ {}".format(fn), flush=True)

# ----------------------------------------------------------------

def generate(ids: list[str]):
    """Сгенерировать все необходимые для указанных тайников файлы.

    :param ids: список ID тайников из [story_ids] (game_story_ids.ltx)
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
            not _sid.isdigit() or
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
        _run(generate_main,      "main",     dict(data=data))
        _run(generate_strings,   "string",   dict(data=data))
        print("-"*80)
