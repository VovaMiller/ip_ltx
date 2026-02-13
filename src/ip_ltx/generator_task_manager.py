import traceback
from pathlib import Path

from .task_manager import TaskIterator

# ----------------------------------------------------------------

def generate_tasks(fn, task_ids=None):
    tab = "    "
    with open(fn, "w", encoding="utf-8") as file:
        for task_id, task_sect in TaskIterator(task_ids=task_ids, include_storyline=False):
            file.write("{}<game_task id=\"{}\" prio=\"199\">\n".format(tab*1, task_id))
            file.write("{}<title>{}</title>\n".format(tab*2, task_id))
            file.write("{}<objective>\n".format(tab*2))
            file.write("{}<text>{}</text>\n".format(tab*3, task_id))
            file.write("{}<icon>ui_iconsTotal_{}</icon>\n".format(tab*3, task_id))
            file.write("{}<function_complete>task_manager.task_complete</function_complete>\n".format(tab*3))
            file.write("{}<function_fail>task_manager.task_fail</function_fail>\n".format(tab*3))
            file.write("{}</objective>\n".format(tab*2))
            file.write("{}</game_task>\n".format(tab*1))
        file.write("\n")


def generate_icons(fn, task_ids=None):
    tab = "    "
    offset_by_type = {
        "artefact":         (0, 0),
        "monster_part":     (0, 47),
        "find_item":        (0, 94),
        "find_wpn":         (0, 141),
        "eliminate_lager":  (0, 188),
    }
    offset_by_vendor = {
        # "DEFAULT":           (0, 0),
        "trader":           (83, 0),
        "hound":            (166, 0),
        "devil":            (249, 0),
        "barman":           (332, 0),
        "bariga":           (415, 0),
        "shugan":           (498, 0),
        "dolg":             (581, 0),
        "ecolog":           (664, 0),
        "freedom":          (747, 0),
        "wild":             (830, 0),
    }
    with open(fn, "w", encoding="utf-8") as file:
        file.write("<ui_texture>\n")
        file.write("{}<file_name>ui\\ui_iconstotal_tm</file_name>\n".format(tab*1))
        file.write("\n")
        file.write("{}<texture id=\"ui_icons_task_artefact\"        x=\"0\" y=\"0\" width=\"83\" height=\"47\"/>\n".format(tab*1))
        file.write("{}<texture id=\"ui_icons_task_monster_part\"    x=\"0\" y=\"47\" width=\"83\" height=\"47\"/>\n".format(tab*1))
        file.write("{}<texture id=\"ui_icons_task_find_item\"       x=\"0\" y=\"94\" width=\"83\" height=\"47\"/>\n".format(tab*1))
        file.write("{}<texture id=\"ui_icons_task_find_wpn\"        x=\"0\" y=\"141\" width=\"83\" height=\"47\"/>\n".format(tab*1))
        file.write("{}<texture id=\"ui_icons_task_eliminate_lager\" x=\"0\" y=\"188\" width=\"83\" height=\"47\"/>\n".format(tab*1))
        file.write("\n")
        for task_id, task_sect in TaskIterator(task_ids=task_ids, include_storyline=False):
            task_type = task_sect._fields.get("type", None)
            parent = task_sect._fields.get("parent", None)

            # calculating icon position
            pos1 = offset_by_type.get(task_type, None)
            if (pos1 is None):
                raise Exception("[FATAL ERROR] Unexpected task type ({}) in \"{}\"".format(task_type, task_id))
            pos2 = offset_by_vendor.get(parent, None)
            if (pos2 is None):
                raise Exception("[FATAL ERROR] Unexpected parent ({}) in \"{}\"".format(parent, task_id))
            pos = (pos1[0] + pos2[0], pos1[1] + pos2[1])

            file.write("{}<texture id=\"ui_iconsTotal_{}\" x=\"{}\" y=\"{}\" width=\"83\" height=\"47\"/>\n".format(tab*1, task_id, pos[0], pos[1]))
        file.write("\n")
        file.write("</ui_texture>\n")


def generate_articles(fn, task_ids=None):
    tab = "    "
    with open(fn, "w", encoding="utf-8") as file:
        for task_id, task_sect in TaskIterator(task_ids=task_ids, include_storyline=False):
            task_article = task_sect._fields.get("article", None)
            task_text = task_sect._fields.get("text", None)
            task_type = task_sect._fields.get("type", None)
            if task_article is None:
                raise Exception("[FATAL ERROR] No article found in task \"{}\"".format(task_id))
            if task_text is None:
                raise Exception("[FATAL ERROR] No text found in task \"{}\"".format(task_id))
            if task_type is None:
                raise Exception("[FATAL ERROR] No type found in task \"{}\"".format(task_id))
            file.write("<article id=\"{}\" name=\"{}\" article_type=\"task\">\n".format(task_article, task_type))
            file.write("{}<text>{}</text>\n".format(tab*1, task_text))
            file.write("</article>\n")
        file.write("\n")


def generate_strings(fn, task_ids=None):
    tab = "    "
    with open(fn, "w", encoding="utf-8") as file:
        file.write("<?xml version=\"1.0\" encoding=\"windows-1251\" ?>\n")
        file.write("<string_table>\n")
        for task_id, task_sect in TaskIterator(task_ids=task_ids, include_storyline=False):
            task_text = task_sect._fields.get("text", None)
            task_target = task_sect._fields.get("target", None)
            task_count = task_sect._fields.get("count", "")
            if task_text is None:
                raise Exception("[FATAL ERROR] No text found in task \"{}\"".format(task_id))
            if task_target is None:
                raise Exception("[FATAL ERROR] No target found in task \"{}\"".format(task_id))
            file.write("{}<string id=\"{}\">  <!-- {} - {} -->\n".format(tab*1, task_id, task_target, task_count))
            file.write("{}<text>TODO</text>\n".format(tab*2))
            file.write("{}</string>\n".format(tab*1))
            file.write("{}<string id=\"{}\">\n".format(tab*1, task_text))
            file.write("{}<text>TODO. {} {} ____</text>\n".format(tab*2, task_target, task_count))
            file.write("{}</string>\n".format(tab*1))
        file.write("</string_table>\n")

# ----------------------------------------------------------------

def _run(f, tag, kwargs={}):
    fn = "{}__{}.txt".format(Path(__file__).stem, tag)
    try:
        f(fn, **kwargs)
    except Exception as e:
        print("")
        print("! {}".format(fn))
        # print("    {}".format(f.__name__))
        # print("    {}".format(repr(e)))
        print(traceback.format_exc())
        print("", flush=True)
    else:
        print("+ {}".format(fn), flush=True)

# ----------------------------------------------------------------

def generate(ids: list[str] | None):
    """Сгенерировать все необходимые для указанных второстепенных заданий файлы.

    :param ids: список ID заданий из task_manager.ltx,
        или None для генерации по всем заданиям
    """
    if ids is None:
        print("> ALL")
    else:
        print(">", len(ids), "tasks:")
        for id in ids:
            print("> ", id)

    _run(generate_tasks,     "task",     dict(task_ids=ids))
    _run(generate_icons,     "icon",     dict(task_ids=ids))
    _run(generate_articles,  "article",  dict(task_ids=ids))
    _run(generate_strings,   "string",   dict(task_ids=ids))
