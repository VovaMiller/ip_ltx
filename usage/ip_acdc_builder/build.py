def main():
    from ip_ltx.acdc import ip_acdc_builder
    
    _ = ip_acdc_builder.build(
        input_dir="iP.ACDC/",
        output_dir="iP.ACDC/ACDC/",
        alife_list=[
            "alife_l01_escape.ltx",
            "alife_l02_garbage.ltx",
            "alife_l03_agroprom.ltx",
            "alife_l03u_agr_underground.ltx",
            "alife_l04_darkvalley.ltx",
            "alife_l04u_labx18.ltx",
            "alife_l05_bar.ltx",
            "alife_l06_rostok.ltx",
            "alife_l07_military.ltx",
            "alife_l08_yantar.ltx",
            "alife_l08u_brainlab.ltx",
            "alife_l10_radar.ltx",
            "alife_l10u_bunker.ltx",
            "alife_l11_pripyat.ltx",
            "alife_l12_stancia.ltx",
            "alife_l12_stancia_2.ltx",
            "alife_l12u_control_monolith.ltx",
            "alife_l12u_sarcofag.ltx",
        ],
        way_list=[
            "way_l01_escape.ltx",
            "way_l02_garbage.ltx",
            "way_l03_agroprom.ltx",
            "way_l03u_agr_underground.ltx",
            "way_l04_darkvalley.ltx",
            "way_l04u_labx18.ltx",
            "way_l05_bar.ltx",
            "way_l06_rostok.ltx",
            "way_l07_military.ltx",
            "way_l08_yantar.ltx",
            "way_l08u_brainlab.ltx",
            "way_l10_radar.ltx",
            "way_l10u_bunker.ltx",
            "way_l11_pripyat.ltx",
            "way_l12_stancia.ltx",
            "way_l12_stancia_2.ltx",
            "way_l12u_control_monolith.ltx",
            "way_l12u_sarcofag.ltx",
        ]
    ) and ip_acdc_builder.acdc_compile(
        acdc_dir="iP.ACDC/ACDC/",
        spawns_dir="./"
    )

# ----------------------------------------------------------------

if __name__ == "__main__":
    try:
        import sys
        import time
        import traceback
        t0 = time.perf_counter()
        main()
        t1 = time.perf_counter()
        print(f"Time elapsed: {t1-t0:.2f}s")
    except Exception:
        print("-"*80)
        traceback.print_exc()
        print("-"*80)
        input("CRITICAL ERROR: Press ENTER to close...")
        sys.exit(1)
    else:
        input("Press Enter to close...")
