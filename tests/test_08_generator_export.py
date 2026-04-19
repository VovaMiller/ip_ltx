import pytest
from pathlib import Path

import ip_ltx.generator_export as ge

def _test(tmp_path, runnable, tag, **kwargs) -> None:
    FN = f"generator_export__{tag}.txt"
    fp_result = tmp_path / FN
    fp_expected = Path(__file__).parent / Path(__file__).stem / FN
    assert fp_expected.is_file() == True
    text_expected = fp_expected.read_text(encoding="utf-8")

    runnable(str(fp_result), **kwargs)
    text_result = fp_result.read_text(encoding="utf-8")

    assert text_result == text_expected

# ----------------------------------------------------------------

def test_ip_test_static_tables(tmp_path):
    _test(tmp_path, ge._ip_test_static_tables, "ip_test")

def test_acdc_tables(tmp_path):
    _test(tmp_path, ge._acdc_tables, "acdc")

def test_universal_acdc_tables(tmp_path):
    _test(tmp_path, ge._universal_acdc_tables, "universal_acdc")

# ----------------------------------------------------------------
