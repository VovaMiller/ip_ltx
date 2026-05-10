from dataclasses import dataclass
from collections.abc import Iterator

from ..ip_ltx import Ini, Section
from ..ini import meta_ini
from ..utils import print_error, print_warning, SingletonBase


@dataclass(frozen=True, slots=True)
class Task:
    _id: str
    _type: str

@dataclass(frozen=True, slots=True)
class TaskGeneric(Task):
    """Класс цикличного/второстепенного задания.

    Такое задание выдаётся по фразе "Мне нужна работа. Есть что на примете?"
    (если у него отдельно не настроена автоматическая выдача).
    """
    text: str
    article: str        # description
    parent: str
    target: str
    count: int | None   # кол-во необходимых предметов (ИП)

class TaskManager(SingletonBase):
    """Класс, хранящий данные об игровых заданиях,
    зарегистрированных в ``task_manager``.

    Включает в себя цикличные, второстепенные и сюжетные задания - все задания,
    перечисленные в ``[list]``.
    """
    _data: dict[str, Task]

    ini: Ini
    """Считанный файл task_manager.ltx"""

    def __init__(self):
        NAME = "task_manager.ltx"
        self.ini = Ini(name=NAME, ini_meta=meta_ini())
        self.ini.read("config\\misc\\task_manager.ltx", inside_gamedata=True)
        self._data = {}
        for task_id in list(self.ini.section("list").lines()):
            if not self.ini.section_exist(task_id):
                print_error(f"({NAME}) Task '{task_id}' from [list] doesn't exist")
                continue
            task_sect = self.ini.section(task_id)
            try:
                task_type = task_sect.get_string("type")
                if task_type == "storyline":
                    task = Task(
                        _id=task_id,
                        _type=task_type
                    )
                else:
                    task = TaskGeneric(
                        _id=task_id,
                        _type=task_type,
                        text=task_sect.get_string("text"),
                        article=(
                            task_sect.get_string("article")
                            if task_sect.line_exist("article")
                            else task_sect.get_string("description")
                        ),
                        parent=task_sect.get_string("parent"),
                        target=task_sect.get_string("target"),
                        count=(
                            task_sect.get_uint("count")
                            if task_sect.line_exist("count")
                            else None
                        )
                    )
            except Section.Error as e:
                print_error(str(e))
            else:
                self._data[task_id] = task
    
    def __contains__(self, id: str) -> bool:
        return id in self._data
    
    def __iter__(self):
        return iter(self._data)

    def __getitem__(self, id: str) -> Task:
        return self._data[id]

    def __len__(self):
        return len(self._data)
    
    def generic_task(self, task_id: str) -> TaskGeneric:
        """Получить объект цикличного/второстепенного задания.

        :param task_id: id задания.
        :raises KeyError: если указан id несуществующего задания.
        :raises ValueError: если указан id не второстепенного задания.
        """
        task = self._data[task_id]
        if isinstance(task, TaskGeneric):
            return task
        else:
            raise ValueError(f"Task '{task_id}' is not generic")

    def generic_tasks(self, ids: list[str] | None = None) -> Iterator[TaskGeneric]:
        """Итератор цикличных/второстепенных заданий.

        :param ids: Список id заданий, которые нужно проитерировать.
            Если ``None``, то итерирует все цикличные/второстепенные задания.
        :raises KeyError: если в списке указан id несуществующего задания.
        :raises ValueError: если в списке указан id не второстепенного задания.
        """
        if ids is None:
            for task in self._data.values():
                if isinstance(task, TaskGeneric):
                    yield task
        else:
            for task_id in ids:
                task = self._data[task_id]
                if isinstance(task, TaskGeneric):
                    yield task
                else:
                    raise ValueError(f"Task '{task_id}' is not generic")
