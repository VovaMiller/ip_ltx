import sys
import traceback
from pathlib import Path

from ini import system_ini
from utils import print_warning, print_error

# ----------------------------------------------------------------

def compare_sections(fn, s1, s2):
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

def read_input():
    ids = None
    if len(sys.argv) > 1:
        ids = sys.argv[1:]
    if ids is None:
        print("> ALL")
    else:
        print(">", len(ids), "tasks:")
        for id in ids:
            print("> ", id)
    return ids

def run(f, tag, kwargs={}):
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

def main():
    # reading arguments
    if len(sys.argv) < 3:
        print_error("Expected 2 arguments, got {len(sys.argv)-1}")
        return
    if len(sys.argv) > 3:
        print_warning("Ignoring all the arguments after the second one")
    s1_id, s2_id = sys.argv[1], sys.argv[2]

    # getting sections
    ini_system = system_ini()
    if ini_system.section_exist(s1_id):
        s1 = ini_system.section(s1_id)
    else:
        print_error(f"Section '{s1_id}' doesn't exist")
        return
    if ini_system.section_exist(s2_id):
        s2 = ini_system.section(s2_id)
    else:
        print_error(f"Section '{s2_id}' doesn't exist")
        return

    # compare
    run(compare_sections, f"{s1.id}__{s2.id}", dict(s1=s1, s2=s2))


if __name__ == "__main__":
    main()
