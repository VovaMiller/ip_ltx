import pytest
from pathlib import Path

from ip_ltx.generator_character_desc import form_characters


def _test(tmp_path, filename) -> None:
    root_path = Path(__file__).parent / Path(__file__).stem
    input_fn = f"{filename}.ltx"
    output_fn = f"{filename}.xml"

    input_path = root_path.joinpath("input", input_fn)
    assert input_path.is_file() == True

    expected_output_path = root_path.joinpath("output", output_fn)
    assert expected_output_path.is_file() == True
    expected_output = expected_output_path.read_text(encoding="utf-8")

    result_output_path = tmp_path / output_fn
    form_characters(
        fp_in=str(input_path),
        fp_out=str(result_output_path),
        independent_input=False,
        tab="\t"
    )
    assert result_output_path.is_file() == True
    result_output = result_output_path.read_text(encoding="utf-8")

    assert expected_output == result_output


def test_chrdsc_monolith(tmp_path):
    _test(tmp_path, "test_chrdsc_monolith")

def test_chrdsc_rnd(tmp_path):
    _test(tmp_path, "test_chrdsc_rnd")
