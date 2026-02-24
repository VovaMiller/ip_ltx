"""Генерация конфигов, необходимых для заданий из task_manager"""

from .task_manager import TaskIterator
from .utils import run

# ----------------------------------------------------------------

def generate_tasks(
        fn: str,
        task_ids: list[str] | None = None,
        tab: str = "    "
) -> None:
    """Генерация конфига для ``game_tasks.xml``.
    
    :param fn: Путь/имя файла для вывода.
    :param task_ids: Список ID заданий из ``task_manager.ltx``,
        или None для генерации по всем заданиям.
    :param tab: Отступ, используемый при выводе в файл.
    """
    with open(fn, "w", encoding="utf-8") as file:
        for task_id, task_sect in TaskIterator(task_ids=task_ids, include_storyline=False):
            file.write(f"{tab*1}<game_task id=\"{task_id}\" prio=\"199\">\n")
            file.write(f"{tab*2}<title>{task_id}</title>\n")
            file.write(f"{tab*2}<objective>\n")
            file.write(f"{tab*3}<text>{task_id}</text>\n")
            file.write(f"{tab*3}<icon>ui_iconsTotal_{task_id}</icon>\n")
            file.write(f"{tab*3}<function_complete>task_manager.task_complete</function_complete>\n")
            file.write(f"{tab*3}<function_fail>task_manager.task_fail</function_fail>\n")
            file.write(f"{tab*2}</objective>\n")
            file.write(f"{tab*1}</game_task>\n")
        file.write("\n")

def generate_icons(
        fn: str,
        task_ids: list[str] | None = None,
        tab: str = "    "
) -> None:
    """Генерация конфига для ``ui_iconstotal.xml``.
    
    :param fn: Путь/имя файла для вывода.
    :param task_ids: Список ID заданий из ``task_manager.ltx``,
        или None для генерации по всем заданиям.
    :param tab: Отступ, используемый при выводе в файл.
    """
    OFFSET_BY_TYPE = {
        "artefact":         (0, 0),
        "monster_part":     (0, 47),
        "find_item":        (0, 94),
        "find_wpn":         (0, 141),
        "eliminate_lager":  (0, 188),
    }
    OFFSET_BY_VENDOR = {
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
        file.write(f"{tab*1}<file_name>ui\\ui_iconstotal_tm</file_name>\n")
        file.write("\n")
        file.write(f"{tab*1}<texture id=\"ui_icons_task_artefact\"        x=\"0\" y=\"0\" width=\"83\" height=\"47\"/>\n")
        file.write(f"{tab*1}<texture id=\"ui_icons_task_monster_part\"    x=\"0\" y=\"47\" width=\"83\" height=\"47\"/>\n")
        file.write(f"{tab*1}<texture id=\"ui_icons_task_find_item\"       x=\"0\" y=\"94\" width=\"83\" height=\"47\"/>\n")
        file.write(f"{tab*1}<texture id=\"ui_icons_task_find_wpn\"        x=\"0\" y=\"141\" width=\"83\" height=\"47\"/>\n")
        file.write(f"{tab*1}<texture id=\"ui_icons_task_eliminate_lager\" x=\"0\" y=\"188\" width=\"83\" height=\"47\"/>\n")
        file.write("\n")
        for task_id, task_sect in TaskIterator(task_ids=task_ids, include_storyline=False):
            task_type = task_sect._fields.get("type", None)
            parent = task_sect._fields.get("parent", None)

            # calculating icon position
            pos1 = OFFSET_BY_TYPE.get(task_type, None)
            if (pos1 is None):
                raise Exception(f"Unexpected task type ({task_type}) in \"{task_id}\"")
            pos2 = OFFSET_BY_VENDOR.get(parent, None)
            if (pos2 is None):
                raise Exception(f"Unexpected parent ({parent}) in \"{task_id}\"")
            pos = (pos1[0] + pos2[0], pos1[1] + pos2[1])

            file.write(f"{tab*1}<texture id=\"ui_iconsTotal_{task_id}\" x=\"{pos[0]}\" y=\"{pos[1]}\" width=\"83\" height=\"47\"/>\n")
        file.write("\n")
        file.write("</ui_texture>\n")

def generate_articles(
        fn: str,
        task_ids: list[str] | None = None,
        tab: str = "    "
) -> None:
    """Генерация конфига для ``storyline_info_to_diary.xml``.
    
    :param fn: Путь/имя файла для вывода.
    :param task_ids: Список ID заданий из ``task_manager.ltx``,
        или None для генерации по всем заданиям.
    :param tab: Отступ, используемый при выводе в файл.
    """
    with open(fn, "w", encoding="utf-8") as file:
        for task_id, task_sect in TaskIterator(task_ids=task_ids, include_storyline=False):
            task_article = task_sect._fields.get("article", None)
            task_text = task_sect._fields.get("text", None)
            task_type = task_sect._fields.get("type", None)
            if task_article is None:
                raise Exception(f"No article found in task \"{task_id}\"")
            if task_text is None:
                raise Exception(f"No text found in task \"{task_id}\"")
            if task_type is None:
                raise Exception(f"No type found in task \"{task_id}\"")
            file.write(f"<article id=\"{task_article}\" name=\"{task_type}\" article_type=\"task\">\n")
            file.write(f"{tab*1}<text>{task_text}</text>\n")
            file.write("</article>\n")
        file.write("\n")

def generate_strings(
        fn: str,
        task_ids: list[str] | None = None,
        tab: str = "    "
) -> None:
    """Генерация шаблонов для ``string_table``.
    
    :param fn: Путь/имя файла для вывода.
    :param task_ids: Список ID заданий из ``task_manager.ltx``,
        или None для генерации по всем заданиям.
    :param tab: Отступ, используемый при выводе в файл.
    """
    with open(fn, "w", encoding="utf-8") as file:
        file.write("<?xml version=\"1.0\" encoding=\"UTF-8\" ?>\n")
        file.write("<string_table>\n")
        for task_id, task_sect in TaskIterator(task_ids=task_ids, include_storyline=False):
            task_text = task_sect._fields.get("text", None)
            task_target = task_sect._fields.get("target", None)
            task_count = task_sect._fields.get("count", "")
            if task_text is None:
                raise Exception(f"No text found in task \"{task_id}\"")
            if task_target is None:
                raise Exception(f"No target found in task \"{task_id}\"")
            file.write(f"{tab*1}<string id=\"{task_id}\">  <!-- {task_target} - {task_count} -->\n")
            file.write(f"{tab*2}<text>TODO</text>\n")
            file.write(f"{tab*1}</string>\n")
            file.write(f"{tab*1}<string id=\"{task_text}\">\n")
            file.write(f"{tab*2}<text>TODO. {task_target} {task_count} ____</text>\n")
            file.write(f"{tab*1}</string>\n")
        file.write("</string_table>\n")

# ----------------------------------------------------------------

def generate(
        ids: list[str] | None,
        tab: str = "    "
) -> None:
    """Сгенерировать все необходимые конфиги для указанных второстепенных заданий.

    * :func:`generate_tasks`
    * :func:`generate_icons`
    * :func:`generate_articles`
    * :func:`generate_strings`

    :param ids: Список ID заданий из ``task_manager.ltx``,
        или None для генерации по всем заданиям.
    :param tab: Отступ, используемый при выводе в файлы.
    """
    if ids is None:
        print("> ALL")
    else:
        print(">", len(ids), "tasks:")
        for id in ids:
            print("> ", id)

    run(generate_tasks,     "task",     task_ids=ids, tab=tab)
    run(generate_icons,     "icon",     task_ids=ids, tab=tab)
    run(generate_articles,  "article",  task_ids=ids, tab=tab)
    run(generate_strings,   "string",   task_ids=ids, tab=tab)
