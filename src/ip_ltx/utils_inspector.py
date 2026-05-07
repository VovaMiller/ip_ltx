"""Общие утилиты для ``meta_inspector.py`` и ``inspector.py``"""

import io
import traceback
from collections.abc import Callable
from contextlib import redirect_stderr

from .utils import ANSI_COLOR_CODE


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

    log_info: list[str]
    log_warning: list[str]
    log_error: list[str]
    intro_width: int

    def __init__(self, msg: str, raise_on_error: bool = True):
        self.log_info = []
        self.log_warning = []
        self.log_error = []
        self.intro_width = len(msg) + 3
        print(msg, "...", sep="", end="")
        self.raise_on_error = raise_on_error

    def __enter__(self):
        return self
    
    def info(self, *msgs: str):
        """Вывести серое сообщение с доп. информацией."""
        self.log_info.append("\n  ".join(msgs))

    def warn(self, *msgs: str):
        """Вывести жёлтое сообщение-предупреждение."""
        self.log_warning.append("\n  ".join(msgs))
    
    def error(self, *msgs: str):
        """Вывести красное сообщение об ошибке.

        При наличии хотя бы одного такого сообщения на выходе
        из контексного менеджера будет вызвано исключение,
        если ``raise_on_error == True``.

        В отличие прямого вызова исключения, позволяет вывести несколько ошибок сразу.
        """
        self.log_error.append("\n  ".join(msgs))
    
    def __exit__(self, exc_type, exc, tb):
        res_clr = (
            ANSI_COLOR_CODE.RED if (exc_type is not None) or (len(self.log_error) > 0)
            else ANSI_COLOR_CODE.YELLOW if (len(self.log_warning) > 0)
            else ANSI_COLOR_CODE.GREEN
        )
        res_txt = "OK" if (exc_type is None) and (len(self.log_error) == 0) else "FAIL"
        dots = max(0, self.LINE_WIDTH - self.intro_width - len(res_txt))
        print(f"{"."*dots}{res_clr}{res_txt}{ANSI_COLOR_CODE.DEF}")
        if (
            (len(self.log_info) > 0)
            or (len(self.log_warning) > 0)
            or (len(self.log_error) > 0)
            or (exc_type is not None)
        ):
            print("")
            for msg in self.log_info:
                print(f"{ANSI_COLOR_CODE.BLACK}* {msg}{ANSI_COLOR_CODE.DEF}")
                # print(f"* {ANSI_COLOR_CODE.WHITE}{msg}{ANSI_COLOR_CODE.DEF}")
            for msg in self.log_warning:
                print(f"{ANSI_COLOR_CODE.YELLOW}~ {msg}{ANSI_COLOR_CODE.DEF}")
            for msg in self.log_error:
                print(f"{ANSI_COLOR_CODE.RED}! {msg}{ANSI_COLOR_CODE.DEF}")
            if exc_type is not None:
                print(f"{ANSI_COLOR_CODE.RED}! {exc}{ANSI_COLOR_CODE.DEF}")
            print("")
        if exc_type is not None:
            raise InspectorError() from exc
        if self.raise_on_error and (len(self.log_error) > 0):
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
