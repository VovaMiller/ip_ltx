META_FILEPATH = "../_settings/meta.ltx"
HIDE_LTX_WARNINGS = True
HIDE_XML_WARNINGS = True
HIDE_EXTRA_WARNINGS = True

def main():
    from ip_ltx.generator_character_desc import generate

    generate(
        [
            "sample_chrdsc_monolith.ltx",
            "sample_chrdsc_rnd.ltx",
        ],
        independent_input=False,
        output_dir="output",
        tab="\t"
    )

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
