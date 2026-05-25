META_FILEPATH = "_settings/meta.ltx"
HIDE_LTX_WARNINGS = True
HIDE_XML_WARNINGS = True
HIDE_EXTRA_WARNINGS = True

def main():
    from ip_ltx.generator_task_manager import generate

    generate([
        "frm09e",
    ], tab="    ")

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
