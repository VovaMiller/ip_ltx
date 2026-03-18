META_FILEPATH = "../_settings/meta.ltx"
HIDE_GAMEDATA_LTX_WARNINGS = True

def main():
    import ip_ltx.analyzer_loot as al
    from ip_ltx.analyzer_loot import run_summary
    from ip_ltx.utils import run

    LEVELS_ALL = [
        "l01_escape",
        "l02_garbage",
        "l03_agroprom",
        "l03u_agr_underground",
        "l04_darkvalley",
        "l04u_labx18",
        "l05_bar",
        "l06_rostok",
        "l07_military",
        "l08_yantar",
        "l08u_brainlab",
        "l10_radar",
        "l10u_bunker",
        "l11_pripyat",
        "l12_stancia",
        "l12_stancia_2",
        "l12u_control_monolith",
        "l12u_sarcofag",
    ]

    # Summaries: default
    run_summary(
        "all",
        LEVELS_ALL
    )
    for level in LEVELS_ALL:
        run_summary(level, [level])

    # Summaries: custom
    run_summary(
        "custom",
        [
            "l01_escape",
            "l02_garbage",
            "l03_agroprom",
            "l04_darkvalley",
            "l05_bar",
            "l06_rostok",
            "l07_military",
            "l08_yantar",
            "l08u_brainlab",
            "l10_radar",
            "l11_pripyat",
            "l12_stancia",
        ]
    )
    
    # Other
    run(al.tm__count_by_levels, "tm-counts")
    run(al.tm__extract_loot_each, "tm-each", show_strings=True, show_visual=True)
    # run(al.tm__extract_position, "tm-position")
    # run(al.tm__calculate_prob_w, "tm-prob_w")


# ----------------------------------------------------------------

if __name__ == "__main__":
    try:
        import os
        import sys
        import traceback
        from pathlib import Path
        if (
            "META_FILEPATH" in globals()
            and type(META_FILEPATH) == str
            and len(META_FILEPATH) > 0
        ):
            os.environ["META_FILEPATH"] = str(Path(META_FILEPATH).resolve())
        if (
            "HIDE_GAMEDATA_LTX_WARNINGS" in globals()
            and type(HIDE_GAMEDATA_LTX_WARNINGS) == bool
        ):
            os.environ["HIDE_GAMEDATA_LTX_WARNINGS"] = (
                str(int(HIDE_GAMEDATA_LTX_WARNINGS))
            )
        main()
    except Exception:
        print("-"*80)
        traceback.print_exc()
        print("-"*80)
        input("CRITICAL ERROR: Press ENTER to close...")
        sys.exit(1)
    else:
        input("Press Enter to close...")
