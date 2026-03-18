import pytest
from pathlib import Path

import ip_ltx.analyzer_loot as al

def _test(tmp_path, runnable, tag, **kwargs) -> None:
    FN = f"analyzer_loot__{tag}.txt"
    fp_result = tmp_path / FN
    fp_expected = Path(__file__).parent / Path(__file__).stem / FN
    assert fp_expected.is_file() == True
    text_expected = fp_expected.read_text(encoding="utf-8")

    runnable(str(fp_result), **kwargs)
    text_result = fp_result.read_text(encoding="utf-8")

    assert text_result == text_expected

def _test_summary(
        tmp_path: Path,
        tag_levels: str,
        tag_options: str,
        levels: list[str],
        **kwargs
) -> None:
    DN = f"summary__{tag_levels}"
    FN = f"{DN}__{tag_options}.txt"

    exp_fp = Path(__file__).parent / Path(__file__).stem / DN / FN
    assert exp_fp.is_file() == True

    res_fp = tmp_path / FN
    al.summary(str(res_fp), **kwargs, levels=levels)
    assert res_fp.is_file() == True

    assert res_fp.read_text(encoding="utf-8") == exp_fp.read_text(encoding="utf-8")

# ----------------------------------------------------------------

def test_tm_each(tmp_path):
    _test(
        tmp_path,
        al.tm__extract_loot_each, "tm-each",
        show_strings=True, show_visual=True
    )

def test_tm_counts(tmp_path):
    _test(
        tmp_path,
        al.tm__count_by_levels, "tm-counts"
    )

# ----------------------------------------------------------------

KWARGS_SINGLE_01_TM = {
    "include_treasure_manager": True, "include_non_tm_inventories": False,
    "include_drop_box_items": False, "include_level_items": False,
    "compress": False, "show_unlisted_items": False,
}
KWARGS_SINGLE_02_NonTM = {
    "include_treasure_manager": False, "include_non_tm_inventories": True,
    "include_drop_box_items": False, "include_level_items": False,
    "compress": False, "show_unlisted_items": False,
}
KWARGS_SINGLE_03_DropBox = {
    "include_treasure_manager": False, "include_non_tm_inventories": False,
    "include_drop_box_items": True, "include_level_items": False,
    "compress": False, "show_unlisted_items": False,
}
KWARGS_SINGLE_04_NoParent = {
    "include_treasure_manager": False, "include_non_tm_inventories": False,
    "include_drop_box_items": False, "include_level_items": True,
    "compress": False, "show_unlisted_items": False,
}
KWARGS_SINGLE_05_All = {
    "include_treasure_manager": True, "include_non_tm_inventories": True,
    "include_drop_box_items": True, "include_level_items": True,
    "compress": False, "show_unlisted_items": False,
}
KWARGS_SINGLE_06_AllExt = {
    "include_treasure_manager": True, "include_non_tm_inventories": True,
    "include_drop_box_items": True, "include_level_items": True,
    "compress": False, "show_unlisted_items": True,
}
KWARGS_SINGLE_07_AllExtComp = {
    "include_treasure_manager": True, "include_non_tm_inventories": True,
    "include_drop_box_items": True, "include_level_items": True,
    "compress": True, "show_unlisted_items": True,
}

def _test_summary_single(tmp_path, level, tag_options):
    _test_summary(
        tmp_path,
        tag_levels=level,
        tag_options=tag_options,
        levels=[level],
        **globals()[f"KWARGS_SINGLE_{tag_options}"]
    )


def test_summary_l01_01_TM(tmp_path):
    _test_summary_single(tmp_path, "l01_escape", "01_TM")

def test_summary_l01_02_NonTM(tmp_path):
    _test_summary_single(tmp_path, "l01_escape", "02_NonTM")

def test_summary_l01_03_DropBox(tmp_path):
    _test_summary_single(tmp_path, "l01_escape", "03_DropBox")

def test_summary_l01_04_NoParent(tmp_path):
    _test_summary_single(tmp_path, "l01_escape", "04_NoParent")

def test_summary_l01_05_All(tmp_path):
    _test_summary_single(tmp_path, "l01_escape", "05_All")

def test_summary_l01_06_AllExt(tmp_path):
    _test_summary_single(tmp_path, "l01_escape", "06_AllExt")

def test_summary_l01_07_AllExtComp(tmp_path):
    _test_summary_single(tmp_path, "l01_escape", "07_AllExtComp")


def test_summary_l02_01_TM(tmp_path):
    _test_summary_single(tmp_path, "l02_garbage", "01_TM")

def test_summary_l02_02_NonTM(tmp_path):
    _test_summary_single(tmp_path, "l02_garbage", "02_NonTM")

def test_summary_l02_03_DropBox(tmp_path):
    _test_summary_single(tmp_path, "l02_garbage", "03_DropBox")

def test_summary_l02_04_NoParent(tmp_path):
    _test_summary_single(tmp_path, "l02_garbage", "04_NoParent")

def test_summary_l02_05_All(tmp_path):
    _test_summary_single(tmp_path, "l02_garbage", "05_All")

def test_summary_l02_06_AllExt(tmp_path):
    _test_summary_single(tmp_path, "l02_garbage", "06_AllExt")

def test_summary_l02_07_AllExtComp(tmp_path):
    _test_summary_single(tmp_path, "l02_garbage", "07_AllExtComp")


def test_summary_l03_01_TM(tmp_path):
    _test_summary_single(tmp_path, "l03_agroprom", "01_TM")

def test_summary_l03_02_NonTM(tmp_path):
    _test_summary_single(tmp_path, "l03_agroprom", "02_NonTM")

def test_summary_l03_03_DropBox(tmp_path):
    _test_summary_single(tmp_path, "l03_agroprom", "03_DropBox")

def test_summary_l03_04_NoParent(tmp_path):
    _test_summary_single(tmp_path, "l03_agroprom", "04_NoParent")

def test_summary_l03_05_All(tmp_path):
    _test_summary_single(tmp_path, "l03_agroprom", "05_All")

def test_summary_l03_06_AllExt(tmp_path):
    _test_summary_single(tmp_path, "l03_agroprom", "06_AllExt")

def test_summary_l03_07_AllExtComp(tmp_path):
    _test_summary_single(tmp_path, "l03_agroprom", "07_AllExtComp")


def test_summary_l03u_01_TM(tmp_path):
    _test_summary_single(tmp_path, "l03u_agr_underground", "01_TM")

def test_summary_l03u_02_NonTM(tmp_path):
    _test_summary_single(tmp_path, "l03u_agr_underground", "02_NonTM")

def test_summary_l03u_03_DropBox(tmp_path):
    _test_summary_single(tmp_path, "l03u_agr_underground", "03_DropBox")

def test_summary_l03u_04_NoParent(tmp_path):
    _test_summary_single(tmp_path, "l03u_agr_underground", "04_NoParent")

def test_summary_l03u_05_All(tmp_path):
    _test_summary_single(tmp_path, "l03u_agr_underground", "05_All")

def test_summary_l03u_06_AllExt(tmp_path):
    _test_summary_single(tmp_path, "l03u_agr_underground", "06_AllExt")

def test_summary_l03u_07_AllExtComp(tmp_path):
    _test_summary_single(tmp_path, "l03u_agr_underground", "07_AllExtComp")


def test_summary_l04_01_TM(tmp_path):
    _test_summary_single(tmp_path, "l04_darkvalley", "01_TM")

def test_summary_l04_02_NonTM(tmp_path):
    _test_summary_single(tmp_path, "l04_darkvalley", "02_NonTM")

def test_summary_l04_03_DropBox(tmp_path):
    _test_summary_single(tmp_path, "l04_darkvalley", "03_DropBox")

def test_summary_l04_04_NoParent(tmp_path):
    _test_summary_single(tmp_path, "l04_darkvalley", "04_NoParent")

def test_summary_l04_05_All(tmp_path):
    _test_summary_single(tmp_path, "l04_darkvalley", "05_All")

def test_summary_l04_06_AllExt(tmp_path):
    _test_summary_single(tmp_path, "l04_darkvalley", "06_AllExt")

def test_summary_l04_07_AllExtComp(tmp_path):
    _test_summary_single(tmp_path, "l04_darkvalley", "07_AllExtComp")


def test_summary_l04u_01_TM(tmp_path):
    _test_summary_single(tmp_path, "l04u_labx18", "01_TM")

def test_summary_l04u_02_NonTM(tmp_path):
    _test_summary_single(tmp_path, "l04u_labx18", "02_NonTM")

def test_summary_l04u_03_DropBox(tmp_path):
    _test_summary_single(tmp_path, "l04u_labx18", "03_DropBox")

def test_summary_l04u_04_NoParent(tmp_path):
    _test_summary_single(tmp_path, "l04u_labx18", "04_NoParent")

def test_summary_l04u_05_All(tmp_path):
    _test_summary_single(tmp_path, "l04u_labx18", "05_All")

def test_summary_l04u_06_AllExt(tmp_path):
    _test_summary_single(tmp_path, "l04u_labx18", "06_AllExt")

def test_summary_l04u_07_AllExtComp(tmp_path):
    _test_summary_single(tmp_path, "l04u_labx18", "07_AllExtComp")


def test_summary_l05_01_TM(tmp_path):
    _test_summary_single(tmp_path, "l05_bar", "01_TM")

def test_summary_l05_02_NonTM(tmp_path):
    _test_summary_single(tmp_path, "l05_bar", "02_NonTM")

def test_summary_l05_03_DropBox(tmp_path):
    _test_summary_single(tmp_path, "l05_bar", "03_DropBox")

def test_summary_l05_04_NoParent(tmp_path):
    _test_summary_single(tmp_path, "l05_bar", "04_NoParent")

def test_summary_l05_05_All(tmp_path):
    _test_summary_single(tmp_path, "l05_bar", "05_All")

def test_summary_l05_06_AllExt(tmp_path):
    _test_summary_single(tmp_path, "l05_bar", "06_AllExt")

def test_summary_l05_07_AllExtComp(tmp_path):
    _test_summary_single(tmp_path, "l05_bar", "07_AllExtComp")


def test_summary_l06_01_TM(tmp_path):
    _test_summary_single(tmp_path, "l06_rostok", "01_TM")

def test_summary_l06_02_NonTM(tmp_path):
    _test_summary_single(tmp_path, "l06_rostok", "02_NonTM")

def test_summary_l06_03_DropBox(tmp_path):
    _test_summary_single(tmp_path, "l06_rostok", "03_DropBox")

def test_summary_l06_04_NoParent(tmp_path):
    _test_summary_single(tmp_path, "l06_rostok", "04_NoParent")

def test_summary_l06_05_All(tmp_path):
    _test_summary_single(tmp_path, "l06_rostok", "05_All")

def test_summary_l06_06_AllExt(tmp_path):
    _test_summary_single(tmp_path, "l06_rostok", "06_AllExt")

def test_summary_l06_07_AllExtComp(tmp_path):
    _test_summary_single(tmp_path, "l06_rostok", "07_AllExtComp")


def test_summary_l07_01_TM(tmp_path):
    _test_summary_single(tmp_path, "l07_military", "01_TM")

def test_summary_l07_02_NonTM(tmp_path):
    _test_summary_single(tmp_path, "l07_military", "02_NonTM")

def test_summary_l07_03_DropBox(tmp_path):
    _test_summary_single(tmp_path, "l07_military", "03_DropBox")

def test_summary_l07_04_NoParent(tmp_path):
    _test_summary_single(tmp_path, "l07_military", "04_NoParent")

def test_summary_l07_05_All(tmp_path):
    _test_summary_single(tmp_path, "l07_military", "05_All")

def test_summary_l07_06_AllExt(tmp_path):
    _test_summary_single(tmp_path, "l07_military", "06_AllExt")

def test_summary_l07_07_AllExtComp(tmp_path):
    _test_summary_single(tmp_path, "l07_military", "07_AllExtComp")


def test_summary_l08_01_TM(tmp_path):
    _test_summary_single(tmp_path, "l08_yantar", "01_TM")

def test_summary_l08_02_NonTM(tmp_path):
    _test_summary_single(tmp_path, "l08_yantar", "02_NonTM")

def test_summary_l08_03_DropBox(tmp_path):
    _test_summary_single(tmp_path, "l08_yantar", "03_DropBox")

def test_summary_l08_04_NoParent(tmp_path):
    _test_summary_single(tmp_path, "l08_yantar", "04_NoParent")

def test_summary_l08_05_All(tmp_path):
    _test_summary_single(tmp_path, "l08_yantar", "05_All")

def test_summary_l08_06_AllExt(tmp_path):
    _test_summary_single(tmp_path, "l08_yantar", "06_AllExt")

def test_summary_l08_07_AllExtComp(tmp_path):
    _test_summary_single(tmp_path, "l08_yantar", "07_AllExtComp")


def test_summary_l08u_01_TM(tmp_path):
    _test_summary_single(tmp_path, "l08u_brainlab", "01_TM")

def test_summary_l08u_02_NonTM(tmp_path):
    _test_summary_single(tmp_path, "l08u_brainlab", "02_NonTM")

def test_summary_l08u_03_DropBox(tmp_path):
    _test_summary_single(tmp_path, "l08u_brainlab", "03_DropBox")

def test_summary_l08u_04_NoParent(tmp_path):
    _test_summary_single(tmp_path, "l08u_brainlab", "04_NoParent")

def test_summary_l08u_05_All(tmp_path):
    _test_summary_single(tmp_path, "l08u_brainlab", "05_All")

def test_summary_l08u_06_AllExt(tmp_path):
    _test_summary_single(tmp_path, "l08u_brainlab", "06_AllExt")

def test_summary_l08u_07_AllExtComp(tmp_path):
    _test_summary_single(tmp_path, "l08u_brainlab", "07_AllExtComp")


def test_summary_l10_01_TM(tmp_path):
    _test_summary_single(tmp_path, "l10_radar", "01_TM")

def test_summary_l10_02_NonTM(tmp_path):
    _test_summary_single(tmp_path, "l10_radar", "02_NonTM")

def test_summary_l10_03_DropBox(tmp_path):
    _test_summary_single(tmp_path, "l10_radar", "03_DropBox")

def test_summary_l10_04_NoParent(tmp_path):
    _test_summary_single(tmp_path, "l10_radar", "04_NoParent")

def test_summary_l10_05_All(tmp_path):
    _test_summary_single(tmp_path, "l10_radar", "05_All")

def test_summary_l10_06_AllExt(tmp_path):
    _test_summary_single(tmp_path, "l10_radar", "06_AllExt")

def test_summary_l10_07_AllExtComp(tmp_path):
    _test_summary_single(tmp_path, "l10_radar", "07_AllExtComp")


def test_summary_l10u_01_TM(tmp_path):
    _test_summary_single(tmp_path, "l10u_bunker", "01_TM")

def test_summary_l10u_02_NonTM(tmp_path):
    _test_summary_single(tmp_path, "l10u_bunker", "02_NonTM")

def test_summary_l10u_03_DropBox(tmp_path):
    _test_summary_single(tmp_path, "l10u_bunker", "03_DropBox")

def test_summary_l10u_04_NoParent(tmp_path):
    _test_summary_single(tmp_path, "l10u_bunker", "04_NoParent")

def test_summary_l10u_05_All(tmp_path):
    _test_summary_single(tmp_path, "l10u_bunker", "05_All")

def test_summary_l10u_06_AllExt(tmp_path):
    _test_summary_single(tmp_path, "l10u_bunker", "06_AllExt")

def test_summary_l10u_07_AllExtComp(tmp_path):
    _test_summary_single(tmp_path, "l10u_bunker", "07_AllExtComp")


def test_summary_l11_01_TM(tmp_path):
    _test_summary_single(tmp_path, "l11_pripyat", "01_TM")

def test_summary_l11_02_NonTM(tmp_path):
    _test_summary_single(tmp_path, "l11_pripyat", "02_NonTM")

def test_summary_l11_03_DropBox(tmp_path):
    _test_summary_single(tmp_path, "l11_pripyat", "03_DropBox")

def test_summary_l11_04_NoParent(tmp_path):
    _test_summary_single(tmp_path, "l11_pripyat", "04_NoParent")

def test_summary_l11_05_All(tmp_path):
    _test_summary_single(tmp_path, "l11_pripyat", "05_All")

def test_summary_l11_06_AllExt(tmp_path):
    _test_summary_single(tmp_path, "l11_pripyat", "06_AllExt")

def test_summary_l11_07_AllExtComp(tmp_path):
    _test_summary_single(tmp_path, "l11_pripyat", "07_AllExtComp")


def test_summary_l12st1_01_TM(tmp_path):
    _test_summary_single(tmp_path, "l12_stancia", "01_TM")

def test_summary_l12st1_02_NonTM(tmp_path):
    _test_summary_single(tmp_path, "l12_stancia", "02_NonTM")

def test_summary_l12st1_03_DropBox(tmp_path):
    _test_summary_single(tmp_path, "l12_stancia", "03_DropBox")

def test_summary_l12st1_04_NoParent(tmp_path):
    _test_summary_single(tmp_path, "l12_stancia", "04_NoParent")

def test_summary_l12st1_05_All(tmp_path):
    _test_summary_single(tmp_path, "l12_stancia", "05_All")

def test_summary_l12st1_06_AllExt(tmp_path):
    _test_summary_single(tmp_path, "l12_stancia", "06_AllExt")

def test_summary_l12st1_07_AllExtComp(tmp_path):
    _test_summary_single(tmp_path, "l12_stancia", "07_AllExtComp")


def test_summary_l12sar_01_TM(tmp_path):
    _test_summary_single(tmp_path, "l12u_sarcofag", "01_TM")

def test_summary_l12sar_02_NonTM(tmp_path):
    _test_summary_single(tmp_path, "l12u_sarcofag", "02_NonTM")

def test_summary_l12sar_03_DropBox(tmp_path):
    _test_summary_single(tmp_path, "l12u_sarcofag", "03_DropBox")

def test_summary_l12sar_04_NoParent(tmp_path):
    _test_summary_single(tmp_path, "l12u_sarcofag", "04_NoParent")

def test_summary_l12sar_05_All(tmp_path):
    _test_summary_single(tmp_path, "l12u_sarcofag", "05_All")

def test_summary_l12sar_06_AllExt(tmp_path):
    _test_summary_single(tmp_path, "l12u_sarcofag", "06_AllExt")

def test_summary_l12sar_07_AllExtComp(tmp_path):
    _test_summary_single(tmp_path, "l12u_sarcofag", "07_AllExtComp")


def test_summary_l12con_01_TM(tmp_path):
    _test_summary_single(tmp_path, "l12u_control_monolith", "01_TM")

def test_summary_l12con_02_NonTM(tmp_path):
    _test_summary_single(tmp_path, "l12u_control_monolith", "02_NonTM")

def test_summary_l12con_03_DropBox(tmp_path):
    _test_summary_single(tmp_path, "l12u_control_monolith", "03_DropBox")

def test_summary_l12con_04_NoParent(tmp_path):
    _test_summary_single(tmp_path, "l12u_control_monolith", "04_NoParent")

def test_summary_l12con_05_All(tmp_path):
    _test_summary_single(tmp_path, "l12u_control_monolith", "05_All")

def test_summary_l12con_06_AllExt(tmp_path):
    _test_summary_single(tmp_path, "l12u_control_monolith", "06_AllExt")

def test_summary_l12con_07_AllExtComp(tmp_path):
    _test_summary_single(tmp_path, "l12u_control_monolith", "07_AllExtComp")


def test_summary_l12st2_01_TM(tmp_path):
    _test_summary_single(tmp_path, "l12_stancia_2", "01_TM")

def test_summary_l12st2_02_NonTM(tmp_path):
    _test_summary_single(tmp_path, "l12_stancia_2", "02_NonTM")

def test_summary_l12st2_03_DropBox(tmp_path):
    _test_summary_single(tmp_path, "l12_stancia_2", "03_DropBox")

def test_summary_l12st2_04_NoParent(tmp_path):
    _test_summary_single(tmp_path, "l12_stancia_2", "04_NoParent")

def test_summary_l12st2_05_All(tmp_path):
    _test_summary_single(tmp_path, "l12_stancia_2", "05_All")

def test_summary_l12st2_06_AllExt(tmp_path):
    _test_summary_single(tmp_path, "l12_stancia_2", "06_AllExt")

def test_summary_l12st2_07_AllExtComp(tmp_path):
    _test_summary_single(tmp_path, "l12_stancia_2", "07_AllExtComp")

# ----------------------------------------------------------------

KWARGS_MULTIPLE_01_TM = {
    "include_treasure_manager": True, "include_non_tm_inventories": False,
    "include_drop_box_items": False, "include_level_items": False,
    "compress": True, "show_unlisted_items": True,
}
KWARGS_MULTIPLE_02_NonTM = {
    "include_treasure_manager": False, "include_non_tm_inventories": True,
    "include_drop_box_items": False, "include_level_items": False,
    "compress": True, "show_unlisted_items": True,
}
KWARGS_MULTIPLE_03_DropBox = {
    "include_treasure_manager": False, "include_non_tm_inventories": False,
    "include_drop_box_items": True, "include_level_items": False,
    "compress": True,"show_unlisted_items": True,
}
KWARGS_MULTIPLE_04_NoParent = {
    "include_treasure_manager": False, "include_non_tm_inventories": False,
    "include_drop_box_items": False, "include_level_items": True,
    "compress": True, "show_unlisted_items": True,
}
KWARGS_MULTIPLE_05_All = {
    "include_treasure_manager": True, "include_non_tm_inventories": True,
    "include_drop_box_items": True, "include_level_items": True,
    "compress": True, "show_unlisted_items": True,
}

LEVELS_ALL = [
    "l01_escape",
    "l02_garbage",
    "l03_agroprom",
    "l03u_agr_underground",
    "l04_darkvalley",
    "l04u_labx18",
    "l05_bar",
    "l06_rostok",
    "l07_military",
    "l08_yantar",
    "l08u_brainlab",
    "l10_radar",
    "l10u_bunker",
    "l11_pripyat",
    "l12_stancia",
    "l12_stancia_2",
    "l12u_control_monolith",
    "l12u_sarcofag",
]

LEVELS_CUSTOM = [
    "l01_escape",
    "l02_garbage",
    "l03_agroprom",
    "l04_darkvalley",
    "l05_bar",
    "l06_rostok",
    "l07_military",
    "l08_yantar",
    "l08u_brainlab",
    "l10_radar",
    "l11_pripyat",
    "l12_stancia",
]

def _test_summary_multiple(tmp_path, tag_levels, tag_options):
    _test_summary(
        tmp_path,
        tag_levels,
        tag_options,
        levels=globals()[f"LEVELS_{tag_levels.upper()}"],
        **globals()[f"KWARGS_MULTIPLE_{tag_options}"]
    )


def test_summary_all_01_TM(tmp_path):
    _test_summary_multiple(tmp_path, "all", "01_TM")

def test_summary_all_02_NonTM(tmp_path):
    _test_summary_multiple(tmp_path, "all", "02_NonTM")

def test_summary_all_03_DropBox(tmp_path):
    _test_summary_multiple(tmp_path, "all", "03_DropBox")

def test_summary_all_04_NoParent(tmp_path):
    _test_summary_multiple(tmp_path, "all", "04_NoParent")

def test_summary_all_05_All(tmp_path):
    _test_summary_multiple(tmp_path, "all", "05_All")


def test_summary_custom_01_TM(tmp_path):
    _test_summary_multiple(tmp_path, "custom", "01_TM")

def test_summary_custom_02_NonTM(tmp_path):
    _test_summary_multiple(tmp_path, "custom", "02_NonTM")

def test_summary_custom_03_DropBox(tmp_path):
    _test_summary_multiple(tmp_path, "custom", "03_DropBox")

def test_summary_custom_04_NoParent(tmp_path):
    _test_summary_multiple(tmp_path, "custom", "04_NoParent")

def test_summary_custom_05_All(tmp_path):
    _test_summary_multiple(tmp_path, "custom", "05_All")

# ----------------------------------------------------------------
