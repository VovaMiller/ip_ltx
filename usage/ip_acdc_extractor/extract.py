
def main():
    from ip_ltx.acdc import ip_acdc_extractor
    
    _ = ip_acdc_extractor.acdc_decompile(
        all_spawn_fp=r"C:\X-Ray SDK\gamedata\spawns\all.spawn",
        acdc_dir=r"C:\X-Ray SDK\_ACDC"
    ) and ip_acdc_extractor.extract(
        input_dir=r"C:\X-Ray SDK\_ACDC\acdc_decompile",
        output_dir="./",
        alife_list=[
            "alife_l01_escape.ltx",
            "alife_l02_garbage.ltx",
            "alife_l03_agroprom.ltx",
            "alife_l04_darkvalley.ltx",
            "alife_l05_bar.ltx",
            "alife_l06_rostok.ltx",
            "alife_l07_military.ltx",
            "alife_l08_yantar.ltx",
            "alife_l08u_brainlab.ltx",
            "alife_l10_radar.ltx",
            "alife_l11_pripyat.ltx",
            "alife_l12_stancia.ltx",
        ],
        extraction_rules={
            "position":         ".*",
            "game_vertex_id":   ".*",
            "level_vertex_id":  ".*",
            "direction":        ".*",
            "visual_name":      "(inventory_box|physic_object)",
        },
        exceptions={
            "space_restrictor",
            "zone_radioactive_weak",
            "zone_radioactive_average",
            "zone_radioactive_strong",
        },
        exceptions_first_fields=[
            "section_name",
            "name",
            "position",
            "game_vertex_id",
            "level_vertex_id",
            "direction",
        ],
        exceptions_hide_fields={
            # cse_alife_object
            "distance",

            # cse_alife_anomalous_zone
            "offline_interactive_radius",
            "artefact_spawn_count",
            "artefact_position_offset",
        },
        keep_universal_acdc_format=False
    )

# ----------------------------------------------------------------

if __name__ == "__main__":
    try:
        import sys
        import traceback
        main()
    except Exception:
        print("-"*80)
        traceback.print_exc()
        print("-"*80)
        input("CRITICAL ERROR: Press ENTER to close...")
        sys.exit(1)
    else:
        input("Press Enter to close...")
