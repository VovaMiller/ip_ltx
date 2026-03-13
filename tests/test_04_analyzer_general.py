import pytest
from pathlib import Path

import ip_ltx.analyzer_general as ag
from ip_ltx.ini import meta_ini


def _test(tmp_path, runnable, tag, **kwargs) -> None:
    FN = f"analyzer_general__{tag}.txt"
    fp_result = tmp_path / FN
    fp_expected = Path(__file__).parent / Path(__file__).stem / FN
    assert fp_expected.is_file() == True
    text_expected = fp_expected.read_text(encoding="utf-8")

    runnable(str(fp_result), **kwargs)
    text_result = fp_result.read_text(encoding="utf-8")

    assert text_result == text_expected


def test_addon_cost(tmp_path):
    _test(tmp_path,
        ag.extract_fields, "addon__cost",
        precond=ag.is_addon,
        fields=["cost", "inv_name"],
        fields_pp=[ag.to_uint, ag.translate_string]
    )

def test_addon_scopes(tmp_path):
    _test(tmp_path,
        ag.extract_fields, "addon__scopes",
        precond=ag.is_addon_scope,
        fields=[
            "cost", "inv_name",
            "scope_texture", "scope_zoom_factor", "scope_dynamic_zoom"
        ],
        fields_pp=[ag.to_uint, ag.translate_string, ag.scope_type, str, str]
    )

def test_addon_to_wpn(tmp_path):
    _test(tmp_path, ag.extract__addon_to_wpn, "addon__to_wpn")

def test_all_spawn(tmp_path):
    _test(tmp_path,
        ag.extract_fields, "all__$spawn",
        precond=ag.has_spawn_path,
        fields=["$spawn"],
        dont_ignore_sections=True
    )

def test_all_class(tmp_path):
    _test(tmp_path,
        ag.extract_fields, "all__class",
        precond=ag.has_class,
        fields=["class"],
        dont_ignore_sections=True
    )

def test_all_cost(tmp_path):
    _test(tmp_path,
        ag.extract_fields, "all__cost",
        precond=ag.has_cost2,
        fields=["cost"],
        dont_ignore_sections=True
    )

def test_ammo(tmp_path):
    _test(tmp_path,
        ag.extract_fields, "ammo",
        precond=lambda s: ag.is_ammo(s) or ag.is_projectile(s) or ag.is_grenade(s),
        fields=[
            "class",
            "inv_name",
            "cost",
            "box_size"
        ],
        fields_pp=[
            lambda v: meta_ini().get_string("inv_class_to_type", v, "?"),
            ag.translate_string,
            str,
            str
        ],
        sort=1
    )

def test_ammo_k_hit(tmp_path):
    _test(tmp_path,
        ag.extract_fields, "ammo__k_hit",
        precond=ag.is_ammo,
        fields=["k_hit"]
    )

def test_ammo_to_wpn(tmp_path):
    _test(tmp_path, ag.extract__ammo_to_wpn, "ammo__to_wpn")

def test_anomaly(tmp_path):
    _test(tmp_path,
        ag.extract_fields, "anomaly",
        precond=ag.is_anomaly,
        fields=["visible_by_detector"]
    )

def test_arts(tmp_path):
    _test(tmp_path,
        ag.extract_fields, "arts",
        precond=ag.is_art,
        fields=["cost", "inv_name"],
        fields_pp=[ag.to_uint, ag.translate_string]
    )

def test_inv_class(tmp_path):
    _test(tmp_path,
        ag.extract_fields, "INV__class",
        precond=ag.is_inv_item__old2,
        fields=["class"]
    )

def test_inv_visual(tmp_path):
    _test(tmp_path,
        ag.extract_fields, "INV__visual",
        precond=ag.is_inv_item__old2,
        fields=["visual"]
    )
    
def test_monsters_health(tmp_path):
    _test(tmp_path,
        ag.extract_monsters_health, "monsters__health",
        hit_power_wound=2.5,
        hit_power_fire_wound=0.5
    )

def test_monsters_visual(tmp_path):
    _test(tmp_path,
        ag.extract_fields, "monsters__visual",
        precond=ag.is_monster,
        fields=["visual"]
    )

def test_mutant_parts(tmp_path):
    _test(tmp_path,
        ag.extract_fields, "mutant_parts",
        precond=ag.is_mutant_part,
        fields=["cost", "inv_name"],
        fields_pp=[ag.to_uint, ag.translate_string]
    )

def test_outfit(tmp_path):
    _test(tmp_path,
        ag.extract_fields, "outfit",
        precond=ag.is_outfit,
        fields=["cost", "inv_name", "artefact_count"],
        fields_pp=[ag.to_uint, ag.translate_string, str]
    )

def test_outfit_anomaly_protections(tmp_path):
    _test(tmp_path,
        ag.extract_fields, "outfit__anomprots",
        precond=ag.is_outfit,
        fields=["burn_protection", "shock_protection", "chemical_burn_protection"]
    )

def test_outfit_cost_sorted(tmp_path):
    _test(tmp_path,
        ag.extract_fields, "outfit__cost__sorted",
        precond=ag.is_outfit,
        fields=["cost"],
        fields_pp=[ag.to_uint],
        sort=1
    )

def test_wpn(tmp_path):
    _test(tmp_path,
        ag.extract_fields, "wpn",
        precond=ag.is_wpn2,
        fields=["cost", "inv_name"],
        fields_pp=[ag.to_uint, ag.translate_string]
    )

def test_addon_launcher(tmp_path):
    _test(tmp_path,
        ag.extract_fields, "wpn__addon_launcher",
        precond=ag.is_wpn2,
        fields=["grenade_launcher_status", "grenade_launcher_name"]
    )

def test_addon_scope(tmp_path):
    _test(tmp_path,
        ag.extract_fields, "wpn__addon_scope",
        precond=ag.is_wpn,
        fields=["scope_status", "scope_name"]
    )

def test_addon_silencer(tmp_path):
    _test(tmp_path,
        ag.extract_fields, "wpn__addon_silencer",
        precond=ag.is_wpn2,
        fields=["silencer_status", "silencer_name"]
    )

def test_wpn_cost_sorted(tmp_path):
    _test(tmp_path,
        ag.extract_fields, "wpn__cost__sorted",
        precond=ag.is_wpn2,
        fields=["cost"],
        fields_pp=[ag.to_uint],
        sort=1
    )

def test_wpn_desc(tmp_path):
    _test(tmp_path,
        ag.extract_fields, "wpn__desc",
        precond=ag.is_wpn2,
        fields=["description"],
        fields_pp=[ag.translate_string],
        as_blocks=True
    )

def test_wpn_dispersion_sorted(tmp_path):
    _test(tmp_path,
        ag.extract_fields, "wpn__Dispersion__sorted",
        precond=ag.is_wpn2,
        fields=["fire_dispersion_base"],
        fields_pp=[ag.to_float],
        sort=1
    )

def test_inv_weight(tmp_path):
    _test(tmp_path,
        ag.extract_fields, "wpn__inv_weight",
        precond=ag.is_wpn2,
        fields=["inv_weight"],
        fields_pp=[ag.to_float],
        sort=1
    )

def test_wpn_type(tmp_path):
    _test(tmp_path,
        ag.extract_fields, "wpn__type",
        precond=ag.is_wpn2,
        fields=["ef_main_weapon_type", "ef_weapon_type", "animation_slot", "slot"]
    )
