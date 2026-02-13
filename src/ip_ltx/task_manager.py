from collections import OrderedDict
from pathlib import Path

from .ip_ltx import Ini, Section
from .ini import meta_ini
from .utils import print_warning

# ----------------------------------------------------------------

_TASK_MANAGER = None

def _read_task_manager():
    ini = Ini(_name="task_manager.ltx", ini_meta=meta_ini())
    ini.read("config\\misc\\task_manager.ltx", inside_gamedata=True)

    # reading [list]
    tm_list = ini.s.get("list", None)
    if tm_list is None:
        raise Exception("Mandatory section [list] was not found!")
    tm_list = list(tm_list._fields.keys())

    # reading each task
    tm = OrderedDict()
    for task_id in tm_list:
        task_sect = ini.s.get(task_id, None)
        if task_sect is None:
            raise Exception("Task '{}' from [list] doesn't exist!".format(task_id))
        task_type = task_sect._fields.get("type", None)
        if task_type is None:
            raise Exception("Task '{}' doesn't have mandatory field 'type'".format(task_id))
        tm[task_id] = Section(id=task_id, init=task_sect)

    # warn about unlisted task sections
    for id, sect in ini.s.items():
        task_type = sect._fields.get("type", None)
        if task_type is None:
            continue
        if id not in tm:
            if task_type == "storyline":
                print_warning(f"Storyline task '{id}' is unlisted!")
            else:
                print_warning(f"Task '{id}' is unlisted!")

    return tm

# ----------------------------------------------------------------

def get_task_manager():
    """
        Словарь заданий из [list] в task_manager.ltx
        * key - <int> (task id)
        * value - <Section>
    """
    global _TASK_MANAGER
    if _TASK_MANAGER is None:
        _TASK_MANAGER = _read_task_manager()
    return _TASK_MANAGER


class TaskIterator:
    """
        Итератор заданий: task_id, task_sect.
    """
    
    def __init__(self, task_ids=None, include_storyline=True):
        """
            @arg task_ids <list>
                * Список id заданий для итерации.
                * Если None, то итерирует все задания.
            @arg include_storyline <bool>
                * Итерировать ли сюжетные задания.
        """
        self.tasks = get_task_manager()
        if task_ids is None:
            self.task_ids = [
                task_id
                for task_id in self.tasks.keys()
                if (include_storyline or (self.tasks[task_id]._fields.get("type", "") != "storyline"))
            ]
        else:
            self.task_ids = task_ids
        self.include_storyline = include_storyline
        self.i = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.i >= len(self.task_ids):
            raise StopIteration
        task_id = self.task_ids[self.i]
        task_sect = self.tasks.get(task_id, None)
        if task_sect is None:
            raise Exception("task with id '{}' doesn't exist".format(task_id))
        if not self.include_storyline and (task_sect._fields.get("type", "") == "storyline"):
            raise Exception("task with id '{}' is storyline".format(task_id))
        self.i += 1
        return task_id, task_sect
