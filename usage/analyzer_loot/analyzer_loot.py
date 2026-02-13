META_FILEPATH = "../_settings/meta.ltx"

def main():
    import ip_ltx.analyzer_loot as al
    from ip_ltx.analyzer_loot import run, run_summary

    # Summaries
    levels_all = [
        "l01_escape", "l02_garbage", "l03_agroprom", "l04_darkvalley",
        "l05_bar", "l06_rostok", "l07_military", "l08_yantar",
        "l08u_brainlab", "l10_radar", "l11_pripyat", "l12_stancia"
    ]
    run_summary("all", levels_all)
    run_summary(
        "all_but_l11_l12",
        [level for level in levels_all if level not in ["l11_pripyat", "l12_stancia"]]
    )
    run_summary(
        "custom",
        ["l01_escape", "l02_garbage", "l03_agroprom", "l04_darkvalley", "l05_bar", "l06_rostok",
        "l07_military", "l08_yantar", "l08u_brainlab"]
    )
    for level in levels_all:
        run_summary(level, [level])
    
    # Other
    run(al.tm__count_by_levels, "tm-counts")
    run(al.tm__extract_loot_each, "tm-each", dict(show_strings=True, show_visual=True))
    # run(al.tm__extract_position, "tm-position")
    run(al.tm__calculate_prob_w, "tm-prob_w")

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
