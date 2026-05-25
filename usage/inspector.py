META_FILEPATH = "_settings/meta.ltx"
HIDE_LTX_WARNINGS = False
HIDE_XML_WARNINGS = False
HIDE_EXTRA_WARNINGS = False

def main():
    import ip_ltx.inspector as inspector

    inspector.inspect(show_stderr=True, show_traceback=False)

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
