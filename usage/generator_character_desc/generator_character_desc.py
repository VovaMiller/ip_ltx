META_FILEPATH = "../_settings/meta.ltx"

def main():
    from ip_ltx.generator_character_desc import generate

    generate([
        "sample_chrdsc_monolith.txt",
        "sample_chrdsc_rnd.txt",
        "sample_chrdsc_test.txt",
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
