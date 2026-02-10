import re
import math
import traceback
from collections import OrderedDict
from pathlib import Path

from ini import meta_ini, system_ini
from string_table import string_table
from utils import print_warning

# ----------------------------------------------------------------

# Preconds

def is_inv_item__any(section):
    ini_meta = meta_ini()
    has_specific_field = (section._fields.get("inv_name", None) is not None)
    is_ignored = (section.id in ini_meta.s["ignore_sections"]._fields)
    return has_specific_field and not is_ignored

def is_inv_item__any2(section):
    # Доп. исключение: вспомогательные секции оружия для многоприцельности.
    return is_inv_item__any(section) and (len(section._fields.get("scope_respawn", "")) == 0)

def is_inv_item(section):
    ini_meta = meta_ini()
    _class = section._fields.get("class", "-")
    is_inv_class = (len(ini_meta.get_string("inv_class_to_type", _class, "")) > 0)
    is_ignored = (section.id in ini_meta.s["ignore_sections"]._fields)
    return is_inv_class and not is_ignored

def is_inv_item2(section):
    # Доп. исключение: вспомогательные секции оружия для многоприцельности.
    return is_inv_item(section) and (len(section._fields.get("scope_respawn", "")) == 0)

def is_mutant_part(section):
    return is_inv_item__any2(section) and (re.match(r"^mutant_\w+$", section.id) is not None)

def _is_inv_type(section, _type):
    ini_meta = meta_ini()
    _class = section._fields.get("class", "-")
    is_class_ok = (ini_meta.s["inv_class_to_type"]._fields.get(_class, "") == _type)
    is_ignored = (section.id in ini_meta.s["ignore_sections"]._fields)
    return is_class_ok and not is_ignored

def is_art(section):
    return _is_inv_type(section, "T_ART")

def is_outfit(section):
    return _is_inv_type(section, "T_OUTFIT")

def is_wpn(section):
    return _is_inv_type(section, "T_WPN")

def is_wpn2(section):
    # Доп. исключение: вспомогательные секции оружия для многоприцельности.
    return is_wpn(section) and (len(section._fields.get("scope_respawn", "")) == 0)

def is_ammo(section):
    return _is_inv_type(section, "T_AMMO")

def is_projectile(section):
    return _is_inv_type(section, "T_PROJ")

def is_grenade(section):
    return _is_inv_type(section, "T_GREN")

def is_addon(section):
    return _is_inv_type(section, "T_ADDON")

def is_addon_scope(section):
    return is_addon(section) and (section.get_string("class", "") == "WP_SCOPE")

def has_cost(section):
    return is_inv_item__any2(section) and (section._fields.get("cost", None) is not None)

def has_class(section):
    return (len(section._fields.get("class", "")) > 0)

def has_spawn_path(section):
    return (len(section._fields.get("$spawn", "")) > 0)

def is_monster(section):
    ini_meta = meta_ini()
    _class = section._fields.get("class", "-")
    is_class_ok = (ini_meta.s["mob_class_to_type"]._fields.get(_class, "") == "T_MONSTER")
    is_ignored = (section.id in ini_meta.s["ignore_sections"]._fields)
    return is_class_ok and not is_ignored

def is_stalker(section):
    ini_meta = meta_ini()
    _class = section._fields.get("class", "-")
    is_class_ok = (ini_meta.s["mob_class_to_type"]._fields.get(_class, "") == "T_STALKER")
    is_ignored = (section.id in ini_meta.s["ignore_sections"]._fields)
    return is_class_ok and not is_ignored

def is_anomaly(section):
    ini_meta = meta_ini()
    _class = section._fields.get("class", "-")
    is_class_ok = ini_meta.get_bool("is_anomaly_class", _class, False)
    is_ignored = (section.id in ini_meta.s["ignore_sections"]._fields)
    return is_class_ok and not is_ignored

def is_anomaly2(section):
    ini_meta = meta_ini()
    _class = section._fields.get("class", "-")
    is_class_ok = ini_meta.get_bool("is_anomaly_class2", _class, False)
    is_ignored = (section.id in ini_meta.s["ignore_sections"]._fields)
    return is_class_ok and not is_ignored

# ----------------------------------------------------------------

# Fields Post Processing

def to_uint(v):
    return int(v) if ((v is not None) and v.isdigit()) else -1

def to_int(v):
    r = None
    try:
        r = int(v)
    except:
        r = -1
    return r

def to_float(v):
    r = None
    try:
        r = float(v)
    except:
        r = -1
    return r

def translate_string(v):
    return string_table().get(v, v) if v is not None else "-"

def scope_type(v):
    return "collimator" if (len(v) == 0) else "optical"

# ----------------------------------------------------------------

def extract_fields(fn, precond, fields, fields_pp=None, sort=None, as_blocks=False):
    """
        Итерация по всем секциям system.ltx и извлечение полей.
        
        @arg fn <str>
            * Путь/имя файла для вывода.
        @arg precond <function>
            * Функция-фильтр секций.
        @arg fields <list[str]>
            * Список полей для извлечения.
        @arg fields_pp <list[function]>
            * Список функций для постобработки значений соотв. полей.
            * Должен совпадать по размеру с fields.
        @arg sort <int>
            * None: без сортировки.
            * 0: по имени секции.
            * больше 0: по соответствующему полю.
        @arg as_blocks <bool>
            * True: вывести каждую секцию отдельными блоками
            * False: вывести в формате таблицы (одна секция - одна строка)
    """
    if (fields_pp is not None) and (len(fields) != len(fields_pp)):
        raise Exception("len of lists 'fields' and 'fields_pp' must be equal")
    ini_system = system_ini()
    
    # Extract data from system
    d = OrderedDict()
    for section in ini_system.s.values():
        if not precond(section):
            continue
        d[section.id] = OrderedDict()
        if fields_pp is None:
            for field in fields:
                d[section.id][field] = section._fields.get(field, "-")
        else:
            for i, field in enumerate(fields):
                d[section.id][field] = fields_pp[i](section._fields.get(field, None))
    if sort is not None:
        if sort == 0:
            d = OrderedDict(sorted(d.items(), key=lambda x: x[0]))
        elif 0 < sort <= len(fields):
            d = OrderedDict(sorted(d.items(), key=lambda x: x[1][fields[sort-1]]))
    
    with open(fn, "w", encoding="utf-8") as file:
        if as_blocks:
            # Header
            file.write("{}\n".format("\n".join(["; {}".format(field) for field in fields])))
            
            # Sections' blocks
            for k, v in d.items():
                file.write("\n")
                file.write("# {}\n".format(k))
                file.write("\n".join([v[field] for field in fields]))
                file.write("\n")
        else:
            # Calculate tab offsets
            tab_offset_0 = ((max([len(v) for v in d.keys()]) // 4) + 1) * 4
            max_lens = [max([len(field)] + [len(str(v[field])) for v in d.values()]) for field in fields]
            
            # Header
            column_0_name = "# id"
            file.write("{}{}".format(column_0_name, " "*(tab_offset_0 - len(column_0_name))))
            for i, field in enumerate(fields):
                file.write("{}{}".format(" "*(2 + max_lens[i] - len(field)), field))
            file.write("\n")
            
            # Print
            for k, v in d.items():
                file.write("{}{}".format(k, " "*(tab_offset_0 - len(k))))
                for i, field in enumerate(fields):
                    file.write("{}{}".format(" "*(2 + max_lens[i] - len(str(v[field]))), v[field]))
                file.write("\n")


def extract__ammo_to_wpn(fn):
    ini_system = system_ini()
    da = OrderedDict()
    for section in ini_system.s.values():
        if is_wpn2(section):
            ammo_classes = section.get_strings("ammo_class", False)
            for ammo0 in ammo_classes:
                ammo = ammo0.strip()
                if da.get(ammo, None) is None:
                    da[ammo] = []
                da[ammo].append(section.id)
    das = OrderedDict(sorted(da.items(), key=lambda x: x[0]))
    tab_offset = ((max([len(v) for v in das.keys()]) // 4) + 1) * 4
    with open(fn, "w", encoding="utf-8") as file:
        for ammo, wpns in das.items():
            file.write("{}{}= {}\n".format(ammo, " "*(tab_offset - len(ammo)), ", ".join(sorted(wpns))))


def extract__addon_to_wpn(fn):
    ini_meta = meta_ini()
    ini_system = system_ini()
    d = {}
    for section in ini_system.sections():
        if is_addon(section):
            d[section.id] = []
    for section in ini_system.sections():
        if is_wpn(section):
            wpn_sect_id = section.id
            scope_respawn = section.get_string("scope_respawn", "")
            if len(scope_respawn) > 0:
                wpn_sect_id = scope_respawn
            addon_fields = [
                ("scope_status", "scope_name"),
                ("silencer_status", "silencer_name"),
                ("grenade_launcher_status", "grenade_launcher_name"),
            ]
            for _status, _name in addon_fields:
                addon_status = section.get_uint(_status, 0)
                addon_name = section.get_string(_name, "")
                if (addon_status == 2) and (len(addon_name) > 0):
                    if addon_name not in d:
                        if ini_meta.line_exist("ignore_sections", addon_name):
                            continue
                        print_warning(f"Unexpected addon: '{addon_name}'")
                        d[addon_name] = []
                    if wpn_sect_id not in d[addon_name]:
                        d[addon_name].append(wpn_sect_id)
    _class_last = ""
    with open(fn, "w", encoding="utf-8") as file:
        file.write("# <addon> = <weapons>\n")
        for addon, wpns in sorted(d.items(), key=lambda x: ini_system.get_section_index(x[0])):
            _class = ini_system.get_string(addon, "class", "")
            if _class != _class_last:
                file.write("\n")
                _class_last = _class
            file.write("{} = {}\n".format(addon, ", ".join(sorted(wpns))))


def extract_monsters_health(fn, hit_power_wound=2.5, hit_power_fire_wound=0.5):
    ini_system = system_ini()
    ceil = lambda f: math.ceil(round(f, 2))
    d = OrderedDict()
    for section in ini_system.s.values():
        if not is_monster(section):
            continue
        
        # Extracting health_hit_part.
        health_hit_part = section._fields.get("health_hit_part", None)
        if health_hit_part is None:
            print_warning(f"Skipping '{section.id}' as it has no 'health_hit_part'")
            continue
        health_hit_part = float(health_hit_part)
        
        # Extracting immunitiy.
        immu_sect_id = section._fields.get("immunities_sect", None)
        if immu_sect_id is None:
            print_warning(f"Skipping '{section.id}' as it has no 'immunities_sect'")
            continue
        immu_sect_id = immu_sect_id.lower()
        immu_sect = ini_system.s.get(immu_sect_id, None)
        if immu_sect is None:
            print_warning(f"Skipping '{section.id}': immunities section '{immu_sect_id}' doesn't exist")
            continue
        wound_immunity = immu_sect._fields.get("wound_immunity", None)
        fire_wound_immunity = immu_sect._fields.get("fire_wound_immunity", None)
        if wound_immunity is None:
            print_warning(f"Skipping '{section.id}': immunities section '{immu_sect_id}' has no 'wound_immunity'")
            continue
        if fire_wound_immunity is None:
            print_warning(f"Skipping '{section.id}': immunities section '{immu_sect_id}' has no 'fire_wound_immunity'")
            continue
        wound_immunity = float(wound_immunity)
        fire_wound_immunity = float(fire_wound_immunity)
        
        # Extracting damage (bones).
        dmg_sect_id = section._fields.get("damage", None)
        if dmg_sect_id is None:
            print_warning(f"Skipping '{section.id}' as it has no 'damage'")
            continue
        dmg_sect_id = dmg_sect_id.lower()
        dmg_sect = ini_system.s.get(dmg_sect_id, None)
        if dmg_sect is None:
            print_warning(f"Skipping '{section.id}': bone damage section '{dmg_sect_id}' doesn't exist")
            continue
        
        # Calculating.
        d[section.id] = OrderedDict()
        for k in dmg_sect.lines():
            try:
                values = [float(vv) for vv in dmg_sect.get_numbers(k, True)]
            except ValueError:
                del d[section.id]
                print_warning(f"Skipping '{section.id}': bad format of bone values (section '{dmg_sect_id}', field '{k}')")
                break
            if (len(values) != 3) and (len(values) != 4):
                del d[section.id]
                print_warning(f"Skipping '{section.id}': unexpected number of bone values (section '{dmg_sect_id}', field '{k}')")
                break
            hit = values[0]
            d[section.id][k] = OrderedDict()
            d[section.id][k]["wound"] = ceil(1.0 / (hit_power_wound * wound_immunity * hit * health_hit_part))
            d[section.id][k]["fire_wound"] = ceil(1.0 / (hit_power_fire_wound * fire_wound_immunity * hit * health_hit_part))
            if len(values) == 4:
                d[section.id][k]["fire_wound_super"] = ceil(1.0 / (hit_power_fire_wound * fire_wound_immunity * values[3] * health_hit_part))
    
    default_offset_1 = 16
    default_offset_2 = 8
    with open(fn, "w", encoding="utf-8") as file:
        file.write("# hit_power (wound) = {}\n".format(hit_power_wound))
        file.write("# hit_power (fire_wound) = {}\n".format(hit_power_fire_wound))
        file.write("# bone | wound | fire_wound (super fire_wound)\n")
        file.write("\n")
        for sect_id, dbones in d.items():
            file.write("; {}\n".format(sect_id))
            for bone, dv in dbones.items():
                wound = dv["wound"]
                fire_wound = dv["fire_wound"]
                fire_wound_super = dv.get("fire_wound_super", None)
                fire_wound_postfix = " ({})".format(fire_wound_super) if fire_wound_super is not None else ""
                file.write("{}{}{}{}{}{}\n".format(bone, " "*(default_offset_1 - len(bone)), wound, " "*(default_offset_2 - len(str(wound))), fire_wound, fire_wound_postfix))
            file.write("\n")

# ----------------------------------------------------------------

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

    run(extract_fields, "all__class", dict(precond=has_class, fields=["class"]))
    run(extract_fields, "all__cost", dict(precond=has_cost, fields=["cost"]))
    run(extract_fields, "all__$spawn", dict(precond=has_spawn_path, fields=["$spawn"]))
    
    run(extract_fields, "INV__class", dict(precond=is_inv_item__any2, fields=["class"]))
    run(extract_fields, "INV__visual", dict(precond=is_inv_item__any2, fields=["visual"]))
    
    run(extract_fields, "mutant_parts", dict(
        precond=is_mutant_part, fields=["cost", "inv_name"], fields_pp=[to_uint, translate_string]
    ))
    
    run(extract_fields, "arts", dict(
        precond=is_art, fields=["cost", "inv_name"], fields_pp=[to_uint, translate_string]
    ))
    
    run(extract_fields, "outfit", dict(
        precond=is_outfit,
        fields=["cost", "inv_name", "artefact_count"],
        fields_pp=[to_uint, translate_string, str]
    ))
    run(extract_fields, "outfit__cost__sorted", dict(
        precond=is_outfit, fields=["cost"], fields_pp=[to_uint], sort=1
    ))
    # run(extract_fields, "outfit__anomprots", dict(precond=is_outfit, fields=[
        # "burn_protection", "shock_protection", "chemical_burn_protection"
    # ]))


    run(extract_fields, "addon__cost", dict(
        precond=is_addon,
        fields=["cost", "inv_name"],
        fields_pp=[to_uint, translate_string]
    ))
    run(extract_fields, "addon__scopes", dict(
        precond=is_addon_scope,
        fields=["cost", "inv_name", "scope_texture", "scope_zoom_factor", "scope_dynamic_zoom"],
        fields_pp=[to_uint, translate_string, scope_type, str, str]
    ))
    run(extract__addon_to_wpn, "addon__to_wpn")


    run(extract_fields, "ammo", dict(
        precond=lambda s: is_ammo(s) or is_projectile(s) or is_grenade(s),
        fields=["class", "inv_name", "cost", "box_size"],
        fields_pp=[lambda v: meta_ini().get_string("inv_class_to_type", v, "?"), translate_string, str, str],
        sort=1
    ))
    run(extract_fields, "ammo__k_hit", dict(precond=is_ammo, fields=["k_hit"]))
    # run(extract_fields, "ammo__cost", dict(precond=is_ammo, fields=["cost", "box_size"]))
    run(extract__ammo_to_wpn, "ammo__to_wpn")

    run(extract_fields, "wpn", dict(
        precond=is_wpn2, fields=["cost", "inv_name"], fields_pp=[to_uint, translate_string]
    ))
    run(extract_fields, "wpn__desc", dict(
        precond=is_wpn2, fields=["description"], fields_pp=[translate_string], as_blocks=True
    ))
    run(extract_fields, "wpn__cost__sorted", dict(
        precond=is_wpn2, fields=["cost"], fields_pp=[to_uint], sort=1
    ))
    # run(extract_fields, "wpn__cam", dict(precond=is_wpn2, fields=[
        # "cam_relax_speed",
        # "cam_dispersion", "cam_dispersion_inc", "cam_dispertion_frac",
        # "cam_max_angle", "cam_max_angle_horz",
        # "cam_step_angle_horz"
    # ]))
    # run(extract_fields, "wpn__condition_shot_dec", dict(precond=is_wpn2, fields=["condition_shot_dec"]))
    # run(extract_fields, "wpn__fire_dispersion_condition_factor", dict(precond=is_wpn2, fields=[
        # "fire_dispersion_condition_factor"
    # ]))
    # run(extract_fields, "wpn__aim", dict(precond=is_wpn2, fields=["use_aim_bullet", "time_to_aim"]))
    # run(extract_fields, "wpn__Dispersion", dict(precond=is_wpn2, fields=["fire_dispersion_base"]))
    run(extract_fields, "wpn__Dispersion__sorted", dict(
        precond=is_wpn2, fields=["fire_dispersion_base"], fields_pp=[to_float], sort=1
    ))
    # run(extract_fields, "wpn__hit_power", dict(precond=is_wpn2, fields=["hit_power"]))
    # run(extract_fields, "wpn__hit_impulse", dict(precond=is_wpn2, fields=["hit_impulse"]))
    run(extract_fields, "wpn__type", dict(precond=is_wpn2, fields=[
        "ef_main_weapon_type", "ef_weapon_type", "animation_slot", "slot"
    ]))
    # run(extract_fields, "wpn__slot", dict(precond=is_wpn2, fields=["slot"]))
    # run(extract_fields, "wpn__cam_relax_speed", dict(precond=is_wpn2, fields=[
        # "cam_relax_speed", "cam_relax_speed_ai"
    # ]))
    # run(extract_fields, "wpn__ammo_mag_size", dict(precond=is_wpn2, fields=["ammo_mag_size"]))
    # run(extract_fields, "wpn__fire_modes", dict(precond=is_wpn2, fields=["fire_modes"]))
    # run(extract_fields, "wpn__control_inertion_factor", dict(precond=is_wpn2, fields=["control_inertion_factor"]))
    run(extract_fields, "wpn__addon_scope", dict(precond=is_wpn, fields=[
        "scope_status", "scope_name"
    ]))
    run(extract_fields, "wpn__addon_silencer", dict(precond=is_wpn2, fields=[
        "silencer_status", "silencer_name"
    ]))
    run(extract_fields, "wpn__addon_launcher", dict(precond=is_wpn2, fields=[
        "grenade_launcher_status", "grenade_launcher_name"
    ]))
    run(extract_fields, "wpn__inv_weight", dict(
        precond=is_wpn2, fields=["inv_weight"], fields_pp=[to_float], sort=1
    ))
    
    # run(extract_fields, "monsters", dict(precond=is_monster, fields=[]))
    run(extract_fields, "monsters__visual", dict(precond=is_monster, fields=["visual"]))
    # run(extract_fields, "monsters__health_hit_part", dict(precond=is_monster, fields=["health_hit_part"]))
    run(extract_monsters_health, "monsters__health", dict(hit_power_wound=2.5, hit_power_fire_wound=0.5))
    
    run(extract_fields, "anomaly", dict(
        precond=is_anomaly, fields=["can_be_deactivated"]
    ))


if __name__ == "__main__":
    main()
