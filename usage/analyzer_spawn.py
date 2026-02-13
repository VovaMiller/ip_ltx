META_FILEPATH = "_settings/meta.ltx"

def main():
    import ip_ltx.analyzer_spawn as asp
    from ip_ltx.analyzer_spawn import run
    from ip_ltx.spawn_inspector import inspect_spawn

    print("-"*80)
    inspect_spawn()
    print("-"*80, flush=True)

    run(asp.check_anomalies, "anomalies")

    run(asp.extract_mobs, "mobs__l01_escape",       dict(level="l01_escape"))
    run(asp.extract_mobs, "mobs__l02_garbage",      dict(level="l02_garbage"))
    run(asp.extract_mobs, "mobs__l03_agroprom",     dict(level="l03_agroprom"))
    run(asp.extract_mobs, "mobs__l04_darkvalley",   dict(level="l04_darkvalley"))
    run(asp.extract_mobs, "mobs__l05_bar",          dict(level="l05_bar"))
    run(asp.extract_mobs, "mobs__l06_rostok",       dict(level="l06_rostok"))
    run(asp.extract_mobs, "mobs__l07_military",     dict(level="l07_military"))
    run(asp.extract_mobs, "mobs__l08_yantar",       dict(level="l08_yantar"))
    run(asp.extract_mobs, "mobs__l08u_brainlab",    dict(level="l08u_brainlab"))
    run(asp.extract_mobs, "mobs__l10_radar",        dict(level="l10_radar"))
    run(asp.extract_mobs, "mobs__l11_pripyat",      dict(level="l11_pripyat"))
    run(asp.extract_mobs, "mobs__l12_stancia",      dict(level="l12_stancia"))
    
    print("-"*80)

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
