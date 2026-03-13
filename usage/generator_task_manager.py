META_FILEPATH = "_settings/meta.ltx"
HIDE_GAMEDATA_LTX_WARNINGS = True

def main():
    from ip_ltx.generator_task_manager import generate

    generate([
        "frm09e",
    ], tab="    ")

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
