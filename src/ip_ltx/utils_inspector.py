"""Общие утилиты для ``meta_inspector.py`` и ``inspector.py``"""

import io
import traceback
from collections.abc import Callable
from contextlib import redirect_stderr
from dataclasses import dataclass
from enum import Enum

from .utils import ANSIColorCode


class InspectorError(Exception):
    """Вызывается на выходе из контекстного менеджера :class:`InspectorStep`
    при наличии ошибки.
    """
    pass


class InspectorStep:
    """Контекстный менеджер для отдельного шага общего процесса проверки.

    :param msg: Короткое описание шага проверки.
    :param raise_on_error: Если ``True`` (по умолчанию), то
        при наличии хотя бы одного сообщения об ошибке
        на выходе из контексного менеджера
        будет вызвано исключение :class:`InspectorError`.
    """

    LINE_WIDTH = 64

    class MessageLevel(Enum):
        INFO = 0
        WARNING = 1
        ERROR = 2

    @dataclass(frozen=True, slots=True)
    class Message:
        level: "InspectorStep.MessageLevel"
        text: str
        header: bool

    log: list[Message]
    intro_width: int

    def __init__(self, msg: str, raise_on_error: bool = True):
        self.log = []
        self.intro_width = len(msg) + 3
        print(msg, "...", sep="", end="")
        self.raise_on_error = raise_on_error

    def __enter__(self):
        return self

    def info(self, *msgs: str, header: bool = False):
        """Вывести серое сообщение с доп. информацией.

        Если ``header == True``, то сообщение отделится от предыдущих.
        """
        self.log.append(self.Message(
            level=self.MessageLevel.INFO,
            text="\n  ".join(msgs),
            header=header
        ))

    def warn(self, *msgs: str, header: bool = False):
        """Вывести жёлтое сообщение-предупреждение.

        Если ``header == True``, то сообщение отделится от предыдущих.
        """
        self.log.append(self.Message(
            level=self.MessageLevel.WARNING,
            text="\n  ".join(msgs),
            header=header
        ))

    def error(self, *msgs: str, header: bool = False):
        """Вывести красное сообщение об ошибке.

        При наличии хотя бы одного такого сообщения на выходе
        из контексного менеджера будет вызвано исключение,
        если ``raise_on_error == True``.

        В отличие прямого вызова исключения, позволяет вывести несколько ошибок сразу.

        Если ``header == True``, то сообщение отделится от предыдущих.
        """
        self.log.append(self.Message(
            level=self.MessageLevel.ERROR,
            text="\n  ".join(msgs),
            header=header
        ))

    def __exit__(self, exc_type, exc, tb):
        cnt_warning = len(
            [msg for msg in self.log if msg.level == self.MessageLevel.WARNING]
        )
        cnt_error = len(
            [msg for msg in self.log if msg.level == self.MessageLevel.ERROR]
        )
        res_clr = (
            ANSIColorCode.RED if (exc_type is not None) or (cnt_error > 0)
            else ANSIColorCode.YELLOW if (cnt_warning > 0)
            else ANSIColorCode.GREEN
        )
        res_txt = "OK" if (exc_type is None) and (cnt_error == 0) else "FAIL"
        dots = max(0, self.LINE_WIDTH - self.intro_width - len(res_txt))
        print(f"{"."*dots}{res_clr}{res_txt}{ANSIColorCode.DEF}")
        if (len(self.log) > 0) or (exc_type is not None):
            print("")
            for i, msg in enumerate(self.log):
                match msg.level:
                    case self.MessageLevel.INFO:
                        prefix = f"{ANSIColorCode.BLACK}* "
                    case self.MessageLevel.WARNING:
                        prefix = f"{ANSIColorCode.YELLOW}~ "
                    case self.MessageLevel.ERROR:
                        prefix = f"{ANSIColorCode.RED}! "
                    case _:
                        prefix = f"* {ANSIColorCode.WHITE}"
                if (i > 0) and msg.header:
                    print("")
                print(f"{prefix}{msg.text}{ANSIColorCode.DEF}")
            if exc_type is not None:
                print(f"{ANSIColorCode.RED}! {exc}{ANSIColorCode.DEF}")
            print("")
        if exc_type is not None:
            raise InspectorError() from exc
        if self.raise_on_error and (cnt_error > 0):
            raise InspectorError()


def run_inspection(
        pipeline: Callable[[], None] | list[Callable[[], None]],
        show_stderr: bool = False,
        show_traceback: bool = False
) -> None:
    """Обёртка для функции проверки/валидации,
    контролирующая вывод в ``stderr`` и исключения ``InspectorError``.

    :param pipeline: Функция со всеми проверками/валидациями.
        Также можно передать список таких функций,
        как бы разбивая все проверки на стадии;
        между каждой стадией будет выведена разделительная черта.
    :param show_stderr: Вывести ли сообщения из ``stderr``,
        собранные в процессе проверки.
    :param show_traceback: Выводить ли traceback исключения,
        которое может возникнуть в процессе проверки.
    """
    def _print_line():
        print("—" * InspectorStep.LINE_WIDTH)
    tb = ""

    # pipeline
    _print_line()
    stderr_buffer = io.StringIO()
    with redirect_stderr(stderr_buffer):
        try:
            if isinstance(pipeline, list):
                for i, stage in enumerate(pipeline, start=1):
                    stage()
                    if i < len(pipeline):
                        _print_line()
            else:
                pipeline()
        except InspectorError:
            tb = traceback.format_exc().strip()
    stderr_str = stderr_buffer.getvalue().strip()
    _print_line()

    # stderr
    if show_stderr and (len(stderr_str) > 0):
        print(stderr_str)
        _print_line()

    # traceback
    if show_traceback and (len(tb) > 0):
        print(tb)
        _print_line()
