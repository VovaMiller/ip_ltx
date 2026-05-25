META_FILEPATH = "_settings/meta.ltx"
HIDE_LTX_WARNINGS = True
HIDE_XML_WARNINGS = True
HIDE_EXTRA_WARNINGS = True

def main():
    import ip_ltx.analyzer_spawn as asp
    from ip_ltx.utils import run
    from ip_ltx.utils_meta import GameLevels

    asp.validate_spawn_data()

    _levels_exclude: list[str] = [
        # "l03u_agr_underground",
        # "l04u_labx18",
        # "l10u_bunker",
        # "l12_stancia_2",
        # "l12u_control_monolith",
        # "l12u_sarcofag",
    ]
    _levels_all = [lvl for lvl in GameLevels().as_list() if lvl not in _levels_exclude]

    print("-"*80)

    run(asp.check_anomalies, "anomalies",
        levels=_levels_all,
        level_for_details="l03_agroprom"
    )

    for level in _levels_all:
        run(asp.extract_mobs, f"mobs__{level}", level=level)

    print("-"*80)

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
