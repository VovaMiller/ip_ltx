META_FILEPATH = "meta.ltx"

def main():
    import ip_ltx.meta_inspector as inspector

    inspector.inspect(show_stderr=False, show_traceback=False)

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
        os.environ["HIDE_GAMEDATA_LTX_WARNINGS"] = "1"
        main()
    except Exception:
        print("-"*80)
        traceback.print_exc()
        print("-"*80)
        input("CRITICAL ERROR: Press ENTER to close...")
        sys.exit(1)
    else:
        input("Press Enter to close...")
