"""Функции для сравнения секций"""

from .ini import system_ini
from .utils import run

# ----------------------------------------------------------------

def _compare_sections(fn: str, s1_id: str, s2_id: str) -> None:
    """Сравнение двух секций и вывод различий в текстовый файл.
    
    :param fn: Путь/имя файла для вывода.
    :param s1_id: ID первой секции.
    :param s2_id: ID второй секции.
    """
    # getting sections
    ini_system = system_ini()
    if not ini_system.section_exist(s1_id):
        raise Exception(f"Section '{s1_id}' doesn't exist")
    if not ini_system.section_exist(s2_id):
        raise Exception(f"Section '{s2_id}' doesn't exist")
    s1 = ini_system.section(s1_id)
    s2 = ini_system.section(s2_id)

    # collecting diff info
    fields_unique_1 = [k for k in s1._fields.keys() if k not in s2._fields]
    fields_unique_2 = [k for k in s2._fields.keys() if k not in s1._fields]
    fields_diff = []
    for k in s1._fields.keys():
        if k in s2._fields:
            v1, v2 = s1._fields[k], s2._fields[k]
            if v1 != v2:
                fields_diff.append(k)

    # writing down
    with open(fn, "w", encoding="utf-8") as file:
        file.write("# \"{}\" vs \"{}\"\n".format(s1.id, s2.id))
        file.write("\n")
        file.write("\n")
        
        iter_pack = [(s1.id, s1, fields_unique_1), (s2.id, s2, fields_unique_2)]
        for section_name, section, fields_unique in iter_pack:
            file.write("## Unique fields: \"{}\"\n".format(section_name))
            if len(fields_unique) > 0:
                for k in fields_unique:
                    v = section._fields[k]
                    if v is None:
                        file.write("{}\n".format(k))
                    else:
                        file.write("{} = {}\n".format(k, v))
            else:
                file.write("-\n")
            file.write("\n")
        file.write("\n")
        
        file.write("## Different values\n")
        if len(fields_diff) > 0:
            for k in fields_diff:
                file.write("\n")
                v1, v2 = s1._fields[k], s2._fields[k]
                line_1 = k if v1 is None else "{} = {}".format(k, v1)
                line_2 = k if v2 is None else "{} = {}".format(k, v2)
                offset = ((max(len(line_1), len(line_2)) // 4) + 1) * 4
                file.write("{}{}; {}\n".format(line_1, " "*(offset-len(line_1)), s1.id))
                file.write("{}{}; {}\n".format(line_2, " "*(offset-len(line_2)), s2.id))
        else:
            file.write("-\n")

# ----------------------------------------------------------------

def compare(s1_id: str, s2_id: str) -> None:
    """Обёртка для запуска функции ``_compare_sections``.
    
    * Безопасный запуск: все исключения будут перехвачены.
    * Имя выходного файла составляется из ID сравниваемых секций.
    
    :param s1_id: ID первой секции.
    :param s2_id: ID второй секции.
    """
    run(_compare_sections, f"{s1_id}__{s2_id}",
        s1_id=s1_id,
        s2_id=s2_id
    )
