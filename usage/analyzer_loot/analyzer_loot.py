META_FILEPATH = "../_settings/meta.ltx"
HIDE_LTX_WARNINGS = True
HIDE_XML_WARNINGS = True
HIDE_EXTRA_WARNINGS = True

def main():
    import ip_ltx.analyzer_loot as al
    from ip_ltx.analyzer_loot import run_summary
    from ip_ltx.utils import run
    from ip_ltx.utils_meta import GameLevels

    al.validate_spawn_data()

    _levels_exclude: list[str] = [
        # "l03u_agr_underground",
        # "l04u_labx18",
        # "l10u_bunker",
        # "l12_stancia_2",
        # "l12u_control_monolith",
        # "l12u_sarcofag",
    ]

    # Summaries
    _levels_all = [lvl for lvl in GameLevels().as_list() if lvl not in _levels_exclude]
    run_summary(
        "all",
        _levels_all
    )
    for level in _levels_all:
        run_summary(level, [level])

    # Other
    run(al.tm__count_by_levels, "tm-counts")
    run(al.tm__extract_loot_each, "tm-each", show_strings=True, show_visual=True)
    # run(al.tm__extract_position, "tm-position")
    # run(al.tm__calculate_prob_w, "tm-prob_w")


# ----------------------------------------------------------------

if __name__ == "__main__":
    import sys
    import traceback
    try:
        from ip_ltx.utils import fill_environ
        fill_environ(globals())
        main()
    except Exception:
        print("-"*80)
        traceback.print_exc()
        print("-"*80)
        input("CRITICAL ERROR: Press ENTER to close...")
        sys.exit(1)
    else:
        input("Press Enter to close...")
