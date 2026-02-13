META_FILEPATH = "_settings/meta.ltx"

def main():
    from ip_ltx.generator_treasure_manager import generate

    generate([
        "mil_ipv30_secret_01",
        "mil_ipv30_secret_02",
        "mil_ipv30_secret_03",
        "mil_ipv30_secret_04",
        "mil_ipv30_secret_05",
        "mil_ipv30_secret_06",
    ])

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
