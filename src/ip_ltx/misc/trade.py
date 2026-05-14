import re
from pathlib import Path

from ..ini import meta_ini
from ..ip_ltx import Ini, Section
from ..utils import SingletonBase, print_error


class TradeBuyImpl:
    """Класс, инкапсулирующий логику считывания секции
    с коэффициентами покупки торговцем товаров
    и логику определения этого коэффициента
    по данному имени секции предмета.

    Для совместимости с *OGSR Engine*,
    секция с коэффициентами также может содержать
    регулярные выражения - маску имени секции предмета,
    а не имя секции напрямую. Формат: ``/.../``.

    :param buy_section: секция из ltx-файла со всеми коэффициентами.
    """

    _buy_k: dict[str, float]
    """Коэффициенты по имени секции."""

    _buy_k_regex: dict[str, float]
    """Коэффициенты по маске имени секции (регулярному выражению)."""

    def __init__(self, buy_section: Section):
        self._buy_k = {}
        self._buy_k_regex = {}
        for k in buy_section.lines():
            if len(buy_section.get_string(k, "")) == 0:
                v = 0.0  # NO TRADE
            else:
                try:
                    v = sum(buy_section.get_pair_float(k)) / 2.0
                except Section.Error as e:
                    print_error(str(e))
                    v = 0.0  # assuming zero (NO TRADE)
            if (len(k) > 2) and k.startswith("/") and k.endswith("/"):
                self._buy_k_regex[k[1:-1]] = v
            else:
                self._buy_k[k] = v

    def get_buy_k(self, section_name: str) -> float:
        """Получить коэффициент покупки торговцем предмета.

        Отношение игрока к торговцу полагается нулевым
        (т.е. результат - полусумма двух указанных коэффициентов).

        Логика получения коэффициента воспроизводит работу
        LUA-функции ``ip_utils.get_buy_k`` (*ИП v3.0*).
        """
        # Прописана ли секция напрямую?
        if section_name in self._buy_k:
            return self._buy_k[section_name]

        # Проверяем по-очереди регулярки и выдаём первое соответствие.
        for pattern, value in self._buy_k_regex.items():
            if re.search(pattern, section_name) is not None:
                return value

        # Нет такой секции, возвращаем значение по умолчанию
        return 1.0


class TradeBuy(SingletonBase, TradeBuyImpl):
    """Класс, хранящий информацию о коэффициентах покупки торговцами предметов.

    Инициализация по этому классу всегда выдаёт единый экземпляр,
    инициализированный по секции, указанной в ``[trade]`` в meta-файле.
    """
    def __init__(self):
        ini_meta = meta_ini()
        file_path = ini_meta.get_string("trade", "file_path")
        buy_section = ini_meta.get_string("trade", "buy_section")
        ini_trade = Ini(name=Path(file_path).name, ini_meta=ini_meta)
        ini_trade.read(file_path, inside_gamedata=True)
        super().__init__(ini_trade.section(buy_section))
