META_FILEPATH = "_settings/meta.ltx"
HIDE_GAMEDATA_LTX_WARNINGS = True

def main():
    import ip_ltx.analyzer_spawn as asp
    from ip_ltx.spawn_inspector import inspect_spawn
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

    print("-"*80)
    inspect_spawn()
    print("-"*80, flush=True)

    run(asp.check_anomalies, "anomalies",
        levels=LEVELS_ALL,
        level_for_details="l03_agroprom"
    )

    for level in LEVELS_ALL:
        run(asp.extract_mobs, f"mobs__{level}", level=level)
    
    print("-"*80)

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
