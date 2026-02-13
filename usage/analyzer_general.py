META_FILEPATH = "_settings/meta.ltx"

def main():
    import ip_ltx.analyzer_general as ag
    from ip_ltx.analyzer_general import run
    from ip_ltx.ini import meta_ini

    run(ag.extract_fields, "all__class", dict(precond=ag.has_class, fields=["class"]))
    run(ag.extract_fields, "all__cost", dict(precond=ag.has_cost, fields=["cost"]))
    run(ag.extract_fields, "all__$spawn", dict(precond=ag.has_spawn_path, fields=["$spawn"]))
    
    run(ag.extract_fields, "INV__class", dict(precond=ag.is_inv_item__any2, fields=["class"]))
    run(ag.extract_fields, "INV__visual", dict(precond=ag.is_inv_item__any2, fields=["visual"]))
    
    run(ag.extract_fields, "mutant_parts", dict(
        precond=ag.is_mutant_part, fields=["cost", "inv_name"], fields_pp=[ag.to_uint, ag.translate_string]
    ))
    
    run(ag.extract_fields, "arts", dict(
        precond=ag.is_art, fields=["cost", "inv_name"], fields_pp=[ag.to_uint, ag.translate_string]
    ))
    
    run(ag.extract_fields, "outfit", dict(
        precond=ag.is_outfit,
        fields=["cost", "inv_name", "artefact_count"],
        fields_pp=[ag.to_uint, ag.translate_string, str]
    ))
    run(ag.extract_fields, "outfit__cost__sorted", dict(
        precond=ag.is_outfit, fields=["cost"], fields_pp=[ag.to_uint], sort=1
    ))
    # run(ag.extract_fields, "outfit__anomprots", dict(precond=ag.is_outfit, fields=[
        # "burn_protection", "shock_protection", "chemical_burn_protection"
    # ]))


    run(ag.extract_fields, "addon__cost", dict(
        precond=ag.is_addon,
        fields=["cost", "inv_name"],
        fields_pp=[ag.to_uint, ag.translate_string]
    ))
    run(ag.extract_fields, "addon__scopes", dict(
        precond=ag.is_addon_scope,
        fields=["cost", "inv_name", "scope_texture", "scope_zoom_factor", "scope_dynamic_zoom"],
        fields_pp=[ag.to_uint, ag.translate_string, ag.scope_type, str, str]
    ))
    run(ag.extract__addon_to_wpn, "addon__to_wpn")


    run(ag.extract_fields, "ammo", dict(
        precond=lambda s: ag.is_ammo(s) or ag.is_projectile(s) or ag.is_grenade(s),
        fields=["class", "inv_name", "cost", "box_size"],
        fields_pp=[lambda v: meta_ini().get_string("inv_class_to_type", v, "?"), ag.translate_string, str, str],
        sort=1
    ))
    run(ag.extract_fields, "ammo__k_hit", dict(precond=ag.is_ammo, fields=["k_hit"]))
    # run(ag.extract_fields, "ammo__cost", dict(precond=ag.is_ammo, fields=["cost", "box_size"]))
    run(ag.extract__ammo_to_wpn, "ammo__to_wpn")

    run(ag.extract_fields, "wpn", dict(
        precond=ag.is_wpn2, fields=["cost", "inv_name"], fields_pp=[ag.to_uint, ag.translate_string]
    ))
    run(ag.extract_fields, "wpn__desc", dict(
        precond=ag.is_wpn2, fields=["description"], fields_pp=[ag.translate_string], as_blocks=True
    ))
    run(ag.extract_fields, "wpn__cost__sorted", dict(
        precond=ag.is_wpn2, fields=["cost"], fields_pp=[ag.to_uint], sort=1
    ))
    # run(ag.extract_fields, "wpn__cam", dict(precond=ag.is_wpn2, fields=[
        # "cam_relax_speed",
        # "cam_dispersion", "cam_dispersion_inc", "cam_dispertion_frac",
        # "cam_max_angle", "cam_max_angle_horz",
        # "cam_step_angle_horz"
    # ]))
    # run(ag.extract_fields, "wpn__condition_shot_dec", dict(precond=ag.is_wpn2, fields=["condition_shot_dec"]))
    # run(ag.extract_fields, "wpn__fire_dispersion_condition_factor", dict(precond=ag.is_wpn2, fields=[
        # "fire_dispersion_condition_factor"
    # ]))
    # run(ag.extract_fields, "wpn__aim", dict(precond=ag.is_wpn2, fields=["use_aim_bullet", "time_to_aim"]))
    # run(ag.extract_fields, "wpn__Dispersion", dict(precond=ag.is_wpn2, fields=["fire_dispersion_base"]))
    run(ag.extract_fields, "wpn__Dispersion__sorted", dict(
        precond=ag.is_wpn2, fields=["fire_dispersion_base"], fields_pp=[ag.to_float], sort=1
    ))
    # run(ag.extract_fields, "wpn__hit_power", dict(precond=ag.is_wpn2, fields=["hit_power"]))
    # run(ag.extract_fields, "wpn__hit_impulse", dict(precond=ag.is_wpn2, fields=["hit_impulse"]))
    run(ag.extract_fields, "wpn__type", dict(precond=ag.is_wpn2, fields=[
        "ef_main_weapon_type", "ef_weapon_type", "animation_slot", "slot"
    ]))
    # run(ag.extract_fields, "wpn__slot", dict(precond=ag.is_wpn2, fields=["slot"]))
    # run(ag.extract_fields, "wpn__cam_relax_speed", dict(precond=ag.is_wpn2, fields=[
        # "cam_relax_speed", "cam_relax_speed_ai"
    # ]))
    # run(ag.extract_fields, "wpn__ammo_mag_size", dict(precond=ag.is_wpn2, fields=["ammo_mag_size"]))
    # run(ag.extract_fields, "wpn__fire_modes", dict(precond=ag.is_wpn2, fields=["fire_modes"]))
    # run(ag.extract_fields, "wpn__control_inertion_factor", dict(precond=ag.is_wpn2, fields=["control_inertion_factor"]))
    run(ag.extract_fields, "wpn__addon_scope", dict(precond=ag.is_wpn, fields=[
        "scope_status", "scope_name"
    ]))
    run(ag.extract_fields, "wpn__addon_silencer", dict(precond=ag.is_wpn2, fields=[
        "silencer_status", "silencer_name"
    ]))
    run(ag.extract_fields, "wpn__addon_launcher", dict(precond=ag.is_wpn2, fields=[
        "grenade_launcher_status", "grenade_launcher_name"
    ]))
    run(ag.extract_fields, "wpn__inv_weight", dict(
        precond=ag.is_wpn2, fields=["inv_weight"], fields_pp=[ag.to_float], sort=1
    ))
    
    # run(ag.extract_fields, "monsters", dict(precond=ag.is_monster, fields=[]))
    run(ag.extract_fields, "monsters__visual", dict(precond=ag.is_monster, fields=["visual"]))
    # run(ag.extract_fields, "monsters__health_hit_part", dict(precond=ag.is_monster, fields=["health_hit_part"]))
    run(ag.extract_monsters_health, "monsters__health", dict(hit_power_wound=2.5, hit_power_fire_wound=0.5))
    
    run(ag.extract_fields, "anomaly", dict(
        precond=ag.is_anomaly, fields=["can_be_deactivated"]
    ))

# ----------------------------------------------------------------

if __name__ == "__main__":
    try:
        import sys
        import traceback
        if "META_FILEPATH" in globals() and len(META_FILEPATH) > 0:
            from os import environ
            from pathlib import Path
            environ["META_FILEPATH"] = str(Path(META_FILEPATH).resolve())
        main()
    except Exception:
        print("-"*80)
        traceback.print_exc()
        print("-"*80)
        input("CRITICAL ERROR: Press ENTER to close...")
        sys.exit(1)
    else:
        input("Press Enter to close...")
