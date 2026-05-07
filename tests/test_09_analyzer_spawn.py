import pytest
from pathlib import Path

import ip_ltx.analyzer_spawn as asp

def _test(tmp_path, runnable, tag, **kwargs) -> None:
    FN = f"analyzer_spawn__{tag}.txt"
    fp_result = tmp_path / FN
    fp_expected = Path(__file__).parent / Path(__file__).stem / FN
    assert fp_expected.is_file() == True
    text_expected = fp_expected.read_text(encoding="utf-8")

    runnable(str(fp_result), **kwargs)
    text_result = fp_result.read_text(encoding="utf-8")

    assert text_result == text_expected

# ----------------------------------------------------------------

def test_check_anomalies(tmp_path):
    _test(
        tmp_path, asp.check_anomalies, "anomalies",
        levels=[
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
        ],
        level_for_details="l03_agroprom"
    )

# ----------------------------------------------------------------

def _test_extract_mobs(tmp_path: Path, level: str) -> None:
    _test(tmp_path, asp.extract_mobs, f"mobs__{level}", level=level)


def test_extract_mobs_l01(tmp_path):
    _test_extract_mobs(tmp_path, "l01_escape")

def test_extract_mobs_l02(tmp_path):
    _test_extract_mobs(tmp_path, "l02_garbage")

def test_extract_mobs_l03(tmp_path):
    _test_extract_mobs(tmp_path, "l03_agroprom")

def test_extract_mobs_l03u(tmp_path):
    _test_extract_mobs(tmp_path, "l03u_agr_underground")

def test_extract_mobs_l04(tmp_path):
    _test_extract_mobs(tmp_path, "l04_darkvalley")

def test_extract_mobs_l04u(tmp_path):
    _test_extract_mobs(tmp_path, "l04u_labx18")

def test_extract_mobs_l05(tmp_path):
    _test_extract_mobs(tmp_path, "l05_bar")

def test_extract_mobs_l06(tmp_path):
    _test_extract_mobs(tmp_path, "l06_rostok")

def test_extract_mobs_l07(tmp_path):
    _test_extract_mobs(tmp_path, "l07_military")

def test_extract_mobs_l08(tmp_path):
    _test_extract_mobs(tmp_path, "l08_yantar")

def test_extract_mobs_l08u(tmp_path):
    _test_extract_mobs(tmp_path, "l08u_brainlab")

def test_extract_mobs_l10(tmp_path):
    _test_extract_mobs(tmp_path, "l10_radar")

def test_extract_mobs_l10u(tmp_path):
    _test_extract_mobs(tmp_path, "l10u_bunker")

def test_extract_mobs_l11(tmp_path):
    _test_extract_mobs(tmp_path, "l11_pripyat")

def test_extract_mobs_l12st1(tmp_path):
    _test_extract_mobs(tmp_path, "l12_stancia")

def test_extract_mobs_l12st2(tmp_path):
    _test_extract_mobs(tmp_path, "l12_stancia_2")

def test_extract_mobs_l12con(tmp_path):
    _test_extract_mobs(tmp_path, "l12u_control_monolith")

def test_extract_mobs_l12sar(tmp_path):
    _test_extract_mobs(tmp_path, "l12u_sarcofag")

# ----------------------------------------------------------------
