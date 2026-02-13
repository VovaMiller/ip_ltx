import re
import os.path

from .ip_ltx import Ini
from .ini import meta_ini


_BUY_K = None
_BUY_K_REGEX = None

def _init_buy_k():
    module_name = os.path.basename(__file__)

    # reading meta
    ini_meta = meta_ini()
    buy_k, buy_k_regex = {}, []
    if not ini_meta.section_exist("trade"):
        print((
            "! [{}] Unable to initialize data for 'get_buy_k' function: "
            "meta-file doesn't have section [trade]"
        ).format(module_name))
        return buy_k, buy_k_regex
    file_path = ini_meta.get_string("trade", "file_path", "")
    buy_section = ini_meta.get_string("trade", "buy_section", "")
    if (len(file_path) == 0) or (len(buy_section) == 0):
        print((
            "! [{}] Unable to initialize data for 'get_buy_k' function: "
            "both fields 'file_path' and 'buy_section' must be provided "
            "in meta-file section [trade]"
        ).format(module_name))
        return buy_k, buy_k_regex

    # reading file
    ini_trade = Ini(_name=os.path.basename(file_path), ini_meta=ini_meta)
    ini_trade.read(file_path, inside_gamedata=True)
    if not ini_trade.section_exist(buy_section):
        print((
            "! [{}] Unable to initialize data for 'get_buy_k' function: "
            "file '{}' doesn't have section [{}]"
        ).format(module_name, file_path, buy_section))
        return buy_k, buy_k_regex

    # reading data
    sect = ini_trade.s[buy_section]
    for k in sect._fields.keys():
        v = None
        try:
            nums = sect.get_numbers(k, mandatory=False)
        except:
            print((
                "! [{}] Wrong value format: '{} = {}' (file '{}', section [{}]). "
                "Assuming zero (NO TRADE)."
            ).format(module_name, k, sect._fields[k], file_path, buy_section))
            v = 0.0
        else:
            if len(nums) == 0:
                # NO TRADE
                v = 0.0
            elif len(nums) == 2:
                v = sum(nums) / 2.0
            else:
                print((
                    "! [{}] Unexpected count ({}) of numbers: '{} = {}' (file '{}', section [{}]). "
                    "Assuming zero (NO TRADE)."
                ).format(module_name, len(nums), k, sect._fields[k], file_path, buy_section))
                v = 0.0
        if (len(k) > 2) and k.startswith("/") and k.endswith("/"):
            buy_k_regex.append((k[1:-1], v))
        else:
            buy_k[k] = v

    return buy_k, buy_k_regex

# ----------------------------------------------------------------

def get_buy_k(section_name):
    """ Получить коэффициент покупки торговцам предмета секции section_name.
        Отношение игрока к торговцу полагается нулевым
          (т.е. результат - полусумма двух указанных коэффициентов).
        Секция с коэффициентами указывается в мета-файле в секции [trade].
        Секция с коэффициентами может содержать регулярные выражения
          (как в OGSR Engine).
        Копирует принцип работы LUA-функции ip_utils.get_buy_k
    """
    global _BUY_K
    global _BUY_K_REGEX
    if (_BUY_K is None) or (_BUY_K_REGEX is None):
        _BUY_K, _BUY_K_REGEX = _init_buy_k()

    # Прописана ли секция напрямую?
    v = _BUY_K.get(section_name, None)
    if v is not None:
        return v

    # Проверяем по-очереди регулярки и выдаём первое соответствие.
    for pattern, value in _BUY_K_REGEX:
        if re.search(pattern, section_name) is not None:
            return value

    # Нет такой секции, возвращаем значение по умолчанию
    return 1.0
