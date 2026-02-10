import sys
import traceback
from pathlib import Path
from collections import OrderedDict

from ini import meta_ini, system_ini

# ----------------------------------------------------------------

class SectionGroup:
    def __init__(self, name):
        self.name = name
        self.sections = []

def generate_sections(fn):
    ini_meta = meta_ini()
    ini_system = system_ini()
    group_by_type = OrderedDict([
        ("T_ART",       SectionGroup("SECTIONS_INV_ART")),
        ("T_WPN",       SectionGroup("SECTIONS_INV_WPN")),
        ("T_AMMO",      SectionGroup("SECTIONS_INV_AMMO")),
        ("T_PROJ",      SectionGroup("SECTIONS_INV_PROJ")),
        ("T_GREN",      SectionGroup("SECTIONS_INV_GREN")),
        ("T_ADDON",     SectionGroup("SECTIONS_INV_ADDON")),
        ("T_OUTFIT",    SectionGroup("SECTIONS_INV_OUTFIT")),
        ("T_OTHER",     SectionGroup("SECTIONS_INV_OTHER")),
        ("T_STALKER",   SectionGroup("SECTIONS_STALKER")),
    ])

    # filling in groups (inventory items)
    for sect in ini_system.sections():
        if ini_meta.line_exist("ignore_sections", sect.id):
            continue
        if len(ini_system.get_string(sect.id, "scope_respawn", "")) > 0:
            # skipping auxiliary multi-scope sections
            continue
        _class = sect.get_string("class", "?")
        _type = ini_meta.get_string("inv_class_to_type", _class, "?")
        if _type in group_by_type:
            group_by_type[_type].sections.append(sect.id)

    # filling in groups (mobs)
    for sect in ini_system.sections():
        if ini_meta.line_exist("ignore_sections", sect.id):
            continue
        _class = sect.get_string("class", "?")
        _type = ini_meta.get_string("mob_class_to_type", _class, "?")
        if _type in group_by_type:
            group_by_type[_type].sections.append(sect.id)

    # writing
    with open(fn, "w", encoding="utf-8") as file:
        tab = 4
        for group in group_by_type.values():
            if len(group.sections) > 0:
                offset = ((5 + max([len(sect_id) for sect_id in group.sections]) + (tab - 1)) // tab) * tab
                file.write("\n{} = {{\n".format(group.name))
                for sect_id in group.sections:
                    file.write("{}[\"{}\"]{}= true,\n".format(" "*tab, sect_id, " "*(offset - 4 - len(sect_id))))
                file.write("}}\n".format())
            else:
                file.write("\n{} = {{}}\n".format(group.name))

# ----------------------------------------------------------------

def run(f, tag, kwargs={}):
    fn = "{}__{}.txt".format(Path(__file__).stem, tag)
    try:
        f(fn, **kwargs)
    except Exception as e:
        print("")
        print("! {}".format(fn))
        print(traceback.format_exc())
        print("", flush=True)
    else:
        print("+ {}".format(fn), flush=True)


def main():
    print("-"*64)
    ini_system = system_ini()
    print("mod:", ini_system.gdp_m)
    print("SoC:", ini_system.gdp_o or "--")
    print("-"*64)
    run(generate_sections,  "sections")
    print("-"*64)


if __name__ == "__main__":
    main()
