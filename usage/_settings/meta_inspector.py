META_FILEPATH = "meta.ltx"
HIDE_LTX_WARNINGS = True
HIDE_XML_WARNINGS = True
HIDE_EXTRA_WARNINGS = True

def main():
    import ip_ltx.meta_inspector as inspector

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
