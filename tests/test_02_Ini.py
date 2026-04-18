import inspect
import math
import pytest
from pathlib import Path

from ip_ltx import Ini, Section
from ip_ltx.utils import cast_safe


@pytest.fixture(scope="module")
def sample_ini(tmp_path_factory):
    tmp_path_module = tmp_path_factory.mktemp(Path(__file__).stem)
    d = tmp_path_module / "sub"
    d.mkdir()
    f1 = tmp_path_module / "file_1.ltx"
    f2 = tmp_path_module / "file_2.ltx"
    f3 = tmp_path_module / "file_3.ltx"
    f4 = tmp_path_module / "file_4.ltx"
    f5 = d / "file_5.ltx"
    f6 = d / "file_6.ltx"

    f1.write_text(inspect.cleandoc(
    """; Main test file
        [test_1]
        field_str = word_1  ; this is a string
        field_float = 1.1   ; this is a float
        field_int = -1      ; this is an integer
        field_uint = 1      ; this is an unsigned integer
        field_bool = 1      ; this is a boolean

        #include "file_3.ltx"
        #include "file_2.ltx"

        [test_elems]
        strings_0 = 
        strings_1 = abc
        strings_2 = abc, def
        floats_0 = 
        floats_1 = 1.1
        floats_2 = 1.1, 2.2
        ints_0 = 
        ints_1 = -1
        ints_2 = -1, -2
        uints_0 = 
        uints_1 = 1
        utints_2 = 1, 2
        bools_0 = 
        bools_1 = True
        bools_2 = True, False

        [test_items]
        items_0 = 
        items_1 = item
        items_2 = item_1,10, item_2,20
        items_3 = q,w,2,e,r,t,-10,y

        [test_none]
        no_string
        no_strings
        no_float
        no_floats
        no_int
        no_ints
        no_uint
        no_uints
        no_bool
        no_bools
        no_items
    """))
    f2.write_text(inspect.cleandoc(
    """; Test #2
        [test_2]
        field_str = word_2
        field_float = 2.2
        field_int = -2
        field_uint = 2
        field_bool = 0
        field2_str = word_22
        field2_float = 22.2
        field2_int = -22
        field2_uint = 22
        field2_bool = 0

        #include "file_4.ltx"
    """))
    f3.write_text(inspect.cleandoc(
    """; Test #3
        [test_3]:test_1
        field_str = word_3  ; this is a string
        field_float = 3.3   ; this is a float
        field_int = -3      ; this is an integer
        field_uint = 3      ; this is an unsigned integer
        field_bool = 1      ; this is a boolean
        ;field_unknown
    """))
    f4.write_text(inspect.cleandoc(
    """; Test #4
        #include "sub/file_5.ltx"
        #include "sub/file_6.ltx"
    """))
    f5.write_text(inspect.cleandoc(
    """; Test #5
        [test_5]:test_2,test_1
        field_self_str = word_5
        field_self_float = 5.5
        field_self_int = -5
    """))
    f6.write_text(inspect.cleandoc(
    """; Test #6
        [test_6]:test_5
        ; comment line, please ignore
        field_self_str      =   word_6
        field_self_float    =   6.6
        field_self_int      =   -6
    """))

    ini = Ini(name="test")
    ini.read(str(f1), inside_gamedata=False)
    return ini


def test_sample_ini_sections(sample_ini):
    ini: Ini = sample_ini

    assert list(ini.ids()) == [
        "test_1", "test_3", "test_2", "test_5", "test_6",
        "test_elems", "test_items", "test_none",
    ]
    assert list([section.id for section in ini.sections()]) == [
        "test_1", "test_3", "test_2", "test_5", "test_6",
        "test_elems", "test_items", "test_none",
    ]
    assert ini.section_exist("test_1") == True
    assert ini.section_exist("test_2") == True
    assert ini.section_exist("test_3") == True
    assert ini.section_exist("test_4") == False
    assert ini.section_exist("test_5") == True
    assert ini.section_exist("test_6") == True
    assert ini.section_exist("test_7") == False
    assert ini.section_exist("test_8") == False
    assert ini.section_exist("test_elems") == True
    assert ini.section_exist("test_items") == True
    assert ini.section_exist("test_none") == True

    assert ini.get_section_index("test_1") == 0
    assert ini.get_section_index("test_2") == 2
    assert ini.get_section_index("test_3") == 1
    assert ini.get_section_index("test_4") == -1
    assert ini.get_section_index("test_5") == 3
    assert ini.get_section_index("test_6") == 4
    assert ini.get_section_index("test_7") == -1
    assert ini.get_section_index("test_8") == -1
    assert ini.get_section_index("test_elems") == 5
    assert ini.get_section_index("test_items") == 6
    assert ini.get_section_index("test_none") == 7


def test_sample_ini_fields(sample_ini):
    ini: Ini = sample_ini

    assert list(ini.section("test_1").lines()) == [
        "field_str", "field_float", "field_int", "field_uint", "field_bool",
    ]
    assert list(ini.section("test_2").lines()) == [
        "field_str", "field_float", "field_int", "field_uint", "field_bool",
        "field2_str", "field2_float", "field2_int", "field2_uint", "field2_bool",
    ]
    assert list(ini.section("test_3").lines()) == [
        "field_str", "field_float", "field_int", "field_uint", "field_bool",
    ]
    assert list(ini.section("test_5").lines()) == [
        "field_str", "field_float", "field_int", "field_uint", "field_bool",
        "field2_str", "field2_float", "field2_int", "field2_uint", "field2_bool",
        "field_self_str", "field_self_float", "field_self_int",
    ]
    assert list(ini.section("test_6").lines()) == [
        "field_str", "field_float", "field_int", "field_uint", "field_bool",
        "field2_str", "field2_float", "field2_int", "field2_uint", "field2_bool",
        "field_self_str", "field_self_float", "field_self_int",
    ]
    assert list(ini.section("test_elems").lines()) == [
        "strings_0", "strings_1", "strings_2",
        "floats_0", "floats_1", "floats_2",
        "ints_0", "ints_1", "ints_2",
        "uints_0", "uints_1", "utints_2",
        "bools_0", "bools_1", "bools_2",
    ]
    assert list(ini.section("test_items").lines()) == [
        "items_0", "items_1", "items_2", "items_3",
    ]
    assert list(ini.section("test_none").lines()) == [
        "no_string", "no_strings",
        "no_float", "no_floats",
        "no_int", "no_ints",
        "no_uint", "no_uints",
        "no_bool", "no_bools",
        "no_items",
    ]

    for section_id in ini.ids():
        for field in ini.section(section_id).lines():
            assert ini.line_exist(section_id, field) == True
    assert ini.line_exist("test_3", "field_unknown") == False
    with pytest.raises(Ini.Error):
        _ = ini.line_exist("unknown", "field_str")


def test_sample_ini_values(sample_ini):
    ini: Ini = sample_ini

    assert ini.get_string("test_1", "field_str") == "word_1"
    assert ini.get_float("test_1", "field_float") == pytest.approx(1.1, abs=1e-6)
    assert ini.get_int("test_1", "field_int") == -1
    assert ini.get_uint("test_1", "field_uint") == 1
    assert ini.get_bool("test_1", "field_bool") == True
    assert ini.get_string("test_2", "field_str") == "word_2"
    assert ini.get_float("test_2", "field_float") == pytest.approx(2.2, abs=1e-6)
    assert ini.get_int("test_2", "field_int") == -2
    assert ini.get_uint("test_2", "field_uint") == 2
    assert ini.get_bool("test_2", "field_bool") == False
    assert ini.get_string("test_2", "field2_str") == "word_22"
    assert ini.get_float("test_2", "field2_float") == pytest.approx(22.2, abs=1e-6)
    assert ini.get_int("test_2", "field2_int") == -22
    assert ini.get_uint("test_2", "field2_uint") == 22
    assert ini.get_bool("test_2", "field2_bool") == False
    assert ini.get_string("test_3", "field_str") == "word_3"
    assert ini.get_float("test_3", "field_float") == pytest.approx(3.3, abs=1e-6)
    assert ini.get_int("test_3", "field_int") == -3
    assert ini.get_uint("test_3", "field_uint") == 3
    assert ini.get_bool("test_3", "field_bool") == True
    assert ini.get_string("test_5", "field_str") == "word_1"
    assert ini.get_float("test_5", "field_float") == pytest.approx(1.1, abs=1e-6)
    assert ini.get_int("test_5", "field_int") == -1
    assert ini.get_uint("test_5", "field_uint") == 1
    assert ini.get_bool("test_5", "field_bool") == True
    assert ini.get_string("test_5", "field2_str") == "word_22"
    assert ini.get_float("test_5", "field2_float") == pytest.approx(22.2, abs=1e-6)
    assert ini.get_int("test_5", "field2_int") == -22
    assert ini.get_uint("test_5", "field2_uint") == 22
    assert ini.get_bool("test_5", "field2_bool") == False
    assert ini.get_string("test_5", "field_self_str") == "word_5"
    assert ini.get_float("test_5", "field_self_float") == pytest.approx(5.5, abs=1e-6)
    assert ini.get_int("test_5", "field_self_int") == -5
    assert ini.get_string("test_6", "field_str") == "word_1"
    assert ini.get_float("test_6", "field_float") == pytest.approx(1.1, abs=1e-6)
    assert ini.get_int("test_6", "field_int") == -1
    assert ini.get_uint("test_6", "field_uint") == 1
    assert ini.get_bool("test_6", "field_bool") == True
    assert ini.get_string("test_6", "field2_str") == "word_22"
    assert ini.get_float("test_6", "field2_float") == pytest.approx(22.2, abs=1e-6)
    assert ini.get_int("test_6", "field2_int") == -22
    assert ini.get_uint("test_6", "field2_uint") == 22
    assert ini.get_bool("test_6", "field2_bool") == False
    assert ini.get_string("test_6", "field_self_str") == "word_6"
    assert ini.get_float("test_6", "field_self_float") == pytest.approx(6.6, abs=1e-6)
    assert ini.get_int("test_6", "field_self_int") == -6

    assert ini.get_strings("test_elems", "strings_0") == []
    assert ini.get_strings("test_elems", "strings_1") == ["abc"]
    assert ini.get_strings("test_elems", "strings_2") == ["abc", "def"]
    assert ini.get_floats("test_elems", "floats_0") == []
    assert ini.get_floats("test_elems", "floats_1") == pytest.approx([1.1], abs=1e-6)
    assert ini.get_floats("test_elems", "floats_2") == pytest.approx([1.1, 2.2], abs=1e-6)
    assert ini.get_ints("test_elems", "ints_0") == []
    assert ini.get_ints("test_elems", "ints_1") == [-1]
    assert ini.get_ints("test_elems", "ints_2") == [-1, -2]
    assert ini.get_uints("test_elems", "uints_0") == []
    assert ini.get_uints("test_elems", "uints_1") == [1]
    assert ini.get_uints("test_elems", "utints_2") == [1, 2]
    assert ini.get_bools("test_elems", "bools_0") == []
    assert ini.get_bools("test_elems", "bools_1") == [True]
    assert ini.get_bools("test_elems", "bools_2") == [True, False]

    assert ini.get_items("test_items", "items_0") == []
    assert ini.get_items("test_items", "items_1") == [("item", 1)]
    assert ini.get_items("test_items", "items_2") == [("item_1", 10), ("item_2", 20)]
    assert ini.get_items("test_items", "items_3") == [
        ("q", 1), ("w", 2), ("e", 1), ("r", 1), ("t", -10), ("y", 1)
    ]


def test_sample_ini_access_nonexistent_sections(sample_ini):
    ini: Ini = sample_ini

    with pytest.raises(Ini.Error):
        _ = ini.get_string("unknown", "field_str")
    with pytest.raises(Ini.Error):
        _ = ini.get_float("unknown", "field_float")
    with pytest.raises(Ini.Error):
        _ = ini.get_int("unknown", "field_int")
    with pytest.raises(Ini.Error):
        _ = ini.get_uint("unknown", "field_uint")
    with pytest.raises(Ini.Error):
        _ = ini.get_bool("unknown", "field_bool")
    with pytest.raises(Ini.Error):
        _ = ini.get_strings("unknown", "strings")
    with pytest.raises(Ini.Error):
        _ = ini.get_floats("unknown", "floats")
    with pytest.raises(Ini.Error):
        _ = ini.get_ints("unknown", "ints")
    with pytest.raises(Ini.Error):
        _ = ini.get_uints("unknown", "uints")
    with pytest.raises(Ini.Error):
        _ = ini.get_bools("unknown", "bools")
    with pytest.raises(Ini.Error):
        _ = ini.get_items("unknown", "items")


def test_sample_ini_access_nonexistent_fields(sample_ini):
    ini: Ini = sample_ini

    with pytest.raises(Section.Error):
        _ = ini.get_string("test_1", "unknown_str")
    with pytest.raises(Section.Error):
        _ = ini.get_float("test_1", "unknown_float")
    with pytest.raises(Section.Error):
        _ = ini.get_int("test_1", "unknown_int")
    with pytest.raises(Section.Error):
        _ = ini.get_uint("test_1", "unknown_uint")
    with pytest.raises(Section.Error):
        _ = ini.get_bool("test_1", "unknown_bool")
    with pytest.raises(Section.Error):
        _ = ini.get_strings("test_elems", "unknown_strings")
    with pytest.raises(Section.Error):
        _ = ini.get_floats("test_elems", "unknown_floats")
    with pytest.raises(Section.Error):
        _ = ini.get_ints("test_elems", "unknown_ints")
    with pytest.raises(Section.Error):
        _ = ini.get_uints("test_elems", "unknown_uints")
    with pytest.raises(Section.Error):
        _ = ini.get_bools("test_elems", "unknown_bools")
    with pytest.raises(Section.Error):
        _ = ini.get_items("test_items", "unknown_items")

    assert ini.get_string("test_1", "unknown_str", defval="") == ""
    assert ini.get_float("test_1", "unknown_float", defval=0.0) == pytest.approx(0.0, abs=1e-6)
    assert ini.get_int("test_1", "unknown_int", defval=0) == 0
    assert ini.get_uint("test_1", "unknown_uint", defval=0) == 0
    assert ini.get_bool("test_1", "unknown_bool", defval=False) == False
    assert ini.get_strings("test_elems", "unknown_strings", mandatory=False) == []
    assert ini.get_floats("test_elems", "unknown_floats", mandatory=False) == []
    assert ini.get_ints("test_elems", "unknown_ints", mandatory=False) == []
    assert ini.get_uints("test_elems", "unknown_uints", mandatory=False) == []
    assert ini.get_bools("test_elems", "unknown_bools", mandatory=False) == []
    assert ini.get_items("test_items", "unknown_items", mandatory=False) == []


def test_sample_ini_access_fields_without_values(sample_ini):
    ini: Ini = sample_ini

    with pytest.raises(Section.Error):
        _ = ini.get_string("test_none", "no_string")
    with pytest.raises(Section.Error):
        _ = ini.get_strings("test_none", "no_strings")
    with pytest.raises(Section.Error):
        _ = ini.get_float("test_none", "no_float")
    with pytest.raises(Section.Error):
        _ = ini.get_floats("test_none", "no_floats")
    with pytest.raises(Section.Error):
        _ = ini.get_int("test_none", "no_int")
    with pytest.raises(Section.Error):
        _ = ini.get_ints("test_none", "no_ints")
    with pytest.raises(Section.Error):
        _ = ini.get_uint("test_none", "no_uint")
    with pytest.raises(Section.Error):
        _ = ini.get_uints("test_none", "no_uints")
    with pytest.raises(Section.Error):
        _ = ini.get_bool("test_none", "no_bool")
    with pytest.raises(Section.Error):
        _ = ini.get_bools("test_none", "no_bools")
    with pytest.raises(Section.Error):
        _ = ini.get_items("test_none", "no_items")

    assert ini.get_string("test_none", "no_string", defval="-") == "-"
    assert ini.get_strings("test_none", "no_strings", mandatory=False) == []
    assert ini.get_float("test_none", "no_float", defval=-1.0) == pytest.approx(-1.0, abs=1e-6)
    assert ini.get_floats("test_none", "no_floats", mandatory=False) == []
    assert ini.get_int("test_none", "no_int", defval=-1) == -1
    assert ini.get_ints("test_none", "no_ints", mandatory=False) == []
    assert ini.get_uint("test_none", "no_uint", defval=0) == 0
    assert ini.get_uints("test_none", "no_uints", mandatory=False) == []
    assert ini.get_bool("test_none", "no_bool", defval=True) == True
    assert ini.get_bools("test_none", "no_bools", mandatory=False) == []
    assert ini.get_items("test_none", "no_items", mandatory=False) == []


def test_sample_ini_write(sample_ini, tmp_path):
    ini: Ini = sample_ini
    tmp_file = tmp_path / "sample_ini.ltx"
    RESULT = "\n".join([
        "[test_1]",
        "field_str = word_1",
        "field_float = 1.1",
        "field_int = -1",
        "field_uint = 1",
        "field_bool = 1",
        "",
        "[test_3]",
        "field_str = word_3",
        "field_float = 3.3",
        "field_int = -3",
        "field_uint = 3",
        "field_bool = 1",
        "",
        "[test_2]",
        "field_str = word_2",
        "field_float = 2.2",
        "field_int = -2",
        "field_uint = 2",
        "field_bool = 0",
        "field2_str = word_22",
        "field2_float = 22.2",
        "field2_int = -22",
        "field2_uint = 22",
        "field2_bool = 0",
        "",
        "[test_5]",
        "field_str = word_1",
        "field_float = 1.1",
        "field_int = -1",
        "field_uint = 1",
        "field_bool = 1",
        "field2_str = word_22",
        "field2_float = 22.2",
        "field2_int = -22",
        "field2_uint = 22",
        "field2_bool = 0",
        "field_self_str = word_5",
        "field_self_float = 5.5",
        "field_self_int = -5",
        "",
        "[test_6]",
        "field_str = word_1",
        "field_float = 1.1",
        "field_int = -1",
        "field_uint = 1",
        "field_bool = 1",
        "field2_str = word_22",
        "field2_float = 22.2",
        "field2_int = -22",
        "field2_uint = 22",
        "field2_bool = 0",
        "field_self_str = word_6",
        "field_self_float = 6.6",
        "field_self_int = -6",
        "",
        "[test_elems]",
        "strings_0 = ",
        "strings_1 = abc",
        "strings_2 = abc,def",
        "floats_0 = ",
        "floats_1 = 1.1",
        "floats_2 = 1.1,2.2",
        "ints_0 = ",
        "ints_1 = -1",
        "ints_2 = -1,-2",
        "uints_0 = ",
        "uints_1 = 1",
        "utints_2 = 1,2",
        "bools_0 = ",
        "bools_1 = True",
        "bools_2 = True,False",
        "",
        "[test_items]",
        "items_0 = ",
        "items_1 = item",
        "items_2 = item_1,10,item_2,20",
        "items_3 = q,w,2,e,r,t,-10,y",
        "",
        "[test_none]",
        "no_string",
        "no_strings",
        "no_float",
        "no_floats",
        "no_int",
        "no_ints",
        "no_uint",
        "no_uints",
        "no_bool",
        "no_bools",
        "no_items",
        "",
        "",
    ])

    with open(tmp_file, "w", encoding="utf-8") as file:
        ini.write(file)

    assert tmp_file.read_text() == RESULT


def test_sample_ini_write_with_ids_mask(sample_ini, tmp_path):
    ini: Ini = sample_ini
    tmp_file = tmp_path / "sample_ini.ltx"
    IDS_MASK = "test_(3|6|items)"
    RESULT = "\n".join([
        "[test_3]",
        "field_str = word_3",
        "field_float = 3.3",
        "field_int = -3",
        "field_uint = 3",
        "field_bool = 1",
        "",
        "[test_6]",
        "field_str = word_1",
        "field_float = 1.1",
        "field_int = -1",
        "field_uint = 1",
        "field_bool = 1",
        "field2_str = word_22",
        "field2_float = 22.2",
        "field2_int = -22",
        "field2_uint = 22",
        "field2_bool = 0",
        "field_self_str = word_6",
        "field_self_float = 6.6",
        "field_self_int = -6",
        "",
        "[test_items]",
        "items_0 = ",
        "items_1 = item",
        "items_2 = item_1,10,item_2,20",
        "items_3 = q,w,2,e,r,t,-10,y",
        "",
        "",
    ])

    with open(tmp_file, "w", encoding="utf-8") as file:
        ini.write(file, ids_mask=IDS_MASK)

    assert tmp_file.read_text() == RESULT


def test_sample_ini_write_with_fields_mask(sample_ini, tmp_path):
    ini: Ini = sample_ini
    tmp_file = tmp_path / "sample_ini.ltx"
    FIELDS_MASK = ".*(float|bool).*"
    RESULT = "\n".join([
        "[test_1]",
        "field_float = 1.1",
        "field_bool = 1",
        "",
        "[test_3]",
        "field_float = 3.3",
        "field_bool = 1",
        "",
        "[test_2]",
        "field_float = 2.2",
        "field_bool = 0",
        "field2_float = 22.2",
        "field2_bool = 0",
        "",
        "[test_5]",
        "field_float = 1.1",
        "field_bool = 1",
        "field2_float = 22.2",
        "field2_bool = 0",
        "field_self_float = 5.5",
        "",
        "[test_6]",
        "field_float = 1.1",
        "field_bool = 1",
        "field2_float = 22.2",
        "field2_bool = 0",
        "field_self_float = 6.6",
        "",
        "[test_elems]",
        "floats_0 = ",
        "floats_1 = 1.1",
        "floats_2 = 1.1,2.2",
        "bools_0 = ",
        "bools_1 = True",
        "bools_2 = True,False",
        "",
        "[test_items]",
        "",
        "[test_none]",
        "no_float",
        "no_floats",
        "no_bool",
        "no_bools",
        "",
        "",
    ])

    with open(tmp_file, "w", encoding="utf-8") as file:
        ini.write(file, fields_mask=FIELDS_MASK)

    assert tmp_file.read_text() == RESULT


def test_sample_ini_write_with_first(sample_ini, tmp_path):
    ini: Ini = sample_ini
    tmp_file = tmp_path / "sample_ini.ltx"
    FIRST = [
        "field2_bool",
        "field2_uint",
        "field2_int",
        "field2_float",
        "field2_str",
    ]
    RESULT = "\n".join([
        "[test_1]",
        "field_str = word_1",
        "field_float = 1.1",
        "field_int = -1",
        "field_uint = 1",
        "field_bool = 1",
        "",
        "[test_3]",
        "field_str = word_3",
        "field_float = 3.3",
        "field_int = -3",
        "field_uint = 3",
        "field_bool = 1",
        "",
        "[test_2]",
        "field2_bool = 0",
        "field2_uint = 22",
        "field2_int = -22",
        "field2_float = 22.2",
        "field2_str = word_22",
        "field_str = word_2",
        "field_float = 2.2",
        "field_int = -2",
        "field_uint = 2",
        "field_bool = 0",
        "",
        "[test_5]",
        "field2_bool = 0",
        "field2_uint = 22",
        "field2_int = -22",
        "field2_float = 22.2",
        "field2_str = word_22",
        "field_str = word_1",
        "field_float = 1.1",
        "field_int = -1",
        "field_uint = 1",
        "field_bool = 1",
        "field_self_str = word_5",
        "field_self_float = 5.5",
        "field_self_int = -5",
        "",
        "[test_6]",
        "field2_bool = 0",
        "field2_uint = 22",
        "field2_int = -22",
        "field2_float = 22.2",
        "field2_str = word_22",
        "field_str = word_1",
        "field_float = 1.1",
        "field_int = -1",
        "field_uint = 1",
        "field_bool = 1",
        "field_self_str = word_6",
        "field_self_float = 6.6",
        "field_self_int = -6",
        "",
        "[test_elems]",
        "strings_0 = ",
        "strings_1 = abc",
        "strings_2 = abc,def",
        "floats_0 = ",
        "floats_1 = 1.1",
        "floats_2 = 1.1,2.2",
        "ints_0 = ",
        "ints_1 = -1",
        "ints_2 = -1,-2",
        "uints_0 = ",
        "uints_1 = 1",
        "utints_2 = 1,2",
        "bools_0 = ",
        "bools_1 = True",
        "bools_2 = True,False",
        "",
        "[test_items]",
        "items_0 = ",
        "items_1 = item",
        "items_2 = item_1,10,item_2,20",
        "items_3 = q,w,2,e,r,t,-10,y",
        "",
        "[test_none]",
        "no_string",
        "no_strings",
        "no_float",
        "no_floats",
        "no_int",
        "no_ints",
        "no_uint",
        "no_uints",
        "no_bool",
        "no_bools",
        "no_items",
        "",
        "",
    ])

    with open(tmp_file, "w", encoding="utf-8") as file:
        ini.write(file, first=FIRST)

    assert tmp_file.read_text() == RESULT


def test_sample_ini_write_with_value_getter(sample_ini, tmp_path):
    def _value_getter(section: Section, field: str) -> str | None:
        value = section.field(field)
        if value is None:  # No value
            return "None"
        if len(value) == 0:  # Empty value
            return "Zero"
        if (vf := cast_safe(value, float, None)) is not None:  # Number
            return f"{-vf:.2f}" if not math.isclose(vf, 0.0, abs_tol=1e-2) else "nil"
        if "," in value:  # List
            return ", ".join([item.strip().lower() for item in value.split(",")])
        return value.upper()

    ini: Ini = sample_ini
    tmp_file = tmp_path / "sample_ini.ltx"
    RESULT = "\n".join([
        "[test_1]",
        "field_str = WORD_1",
        "field_float = -1.10",
        "field_int = 1.00",
        "field_uint = -1.00",
        "field_bool = -1.00",
        "",
        "[test_3]",
        "field_str = WORD_3",
        "field_float = -3.30",
        "field_int = 3.00",
        "field_uint = -3.00",
        "field_bool = -1.00",
        "",
        "[test_2]",
        "field_str = WORD_2",
        "field_float = -2.20",
        "field_int = 2.00",
        "field_uint = -2.00",
        "field_bool = nil",
        "field2_str = WORD_22",
        "field2_float = -22.20",
        "field2_int = 22.00",
        "field2_uint = -22.00",
        "field2_bool = nil",
        "",
        "[test_5]",
        "field_str = WORD_1",
        "field_float = -1.10",
        "field_int = 1.00",
        "field_uint = -1.00",
        "field_bool = -1.00",
        "field2_str = WORD_22",
        "field2_float = -22.20",
        "field2_int = 22.00",
        "field2_uint = -22.00",
        "field2_bool = nil",
        "field_self_str = WORD_5",
        "field_self_float = -5.50",
        "field_self_int = 5.00",
        "",
        "[test_6]",
        "field_str = WORD_1",
        "field_float = -1.10",
        "field_int = 1.00",
        "field_uint = -1.00",
        "field_bool = -1.00",
        "field2_str = WORD_22",
        "field2_float = -22.20",
        "field2_int = 22.00",
        "field2_uint = -22.00",
        "field2_bool = nil",
        "field_self_str = WORD_6",
        "field_self_float = -6.60",
        "field_self_int = 6.00",
        "",
        "[test_elems]",
        "strings_0 = Zero",
        "strings_1 = ABC",
        "strings_2 = abc, def",
        "floats_0 = Zero",
        "floats_1 = -1.10",
        "floats_2 = 1.1, 2.2",
        "ints_0 = Zero",
        "ints_1 = 1.00",
        "ints_2 = -1, -2",
        "uints_0 = Zero",
        "uints_1 = -1.00",
        "utints_2 = 1, 2",
        "bools_0 = Zero",
        "bools_1 = TRUE",
        "bools_2 = true, false",
        "",
        "[test_items]",
        "items_0 = Zero",
        "items_1 = ITEM",
        "items_2 = item_1, 10, item_2, 20",
        "items_3 = q, w, 2, e, r, t, -10, y",
        "",
        "[test_none]",
        "no_string = None",
        "no_strings = None",
        "no_float = None",
        "no_floats = None",
        "no_int = None",
        "no_ints = None",
        "no_uint = None",
        "no_uints = None",
        "no_bool = None",
        "no_bools = None",
        "no_items = None",
        "",
        "",
    ])

    with open(tmp_file, "w", encoding="utf-8") as file:
        ini.write(file, value_getter=_value_getter)

    assert tmp_file.read_text() == RESULT


def test_sample_ini_write_with_all_params(sample_ini, tmp_path):
    def _value_getter(section: Section, field: str) -> str | None:
        value = section.field(field)
        if value is None:  # No value
            return "None"
        if len(value) == 0:  # Empty value
            return "Zero"
        if (vf := cast_safe(value, float, None)) is not None:  # Number
            return f"{-vf:.2f}" if not math.isclose(vf, 0.0, abs_tol=1e-2) else "nil"
        if "," in value:  # List
            return ", ".join([item.strip().lower() for item in value.split(",")])
        return value.upper()

    ini: Ini = sample_ini
    tmp_file = tmp_path / "sample_ini.ltx"
    IDS_MASK = "test_(3|elems|items|none)"
    FIELDS_MASK = r"(field_\w+|.*string.*|.*item.*)"
    FIRST = [
        "no_strings",
        "strings_1",
        "items_3", "items_2",
        "field_bool", "field_uint", "field_int", "field_float", "field_str"
    ]
    RESULT = "\n".join([
        "[test_3]",
        "field_bool = -1.00",
        "field_uint = -3.00",
        "field_int = 3.00",
        "field_float = -3.30",
        "field_str = WORD_3",
        "",
        "[test_elems]",
        "strings_1 = ABC",
        "strings_0 = Zero",
        "strings_2 = abc, def",
        "",
        "[test_items]",
        "items_3 = q, w, 2, e, r, t, -10, y",
        "items_2 = item_1, 10, item_2, 20",
        "items_0 = Zero",
        "items_1 = ITEM",
        "",
        "[test_none]",
        "no_strings = None",
        "no_string = None",
        "no_items = None",
        "",
        "",
    ])

    with open(tmp_file, "w", encoding="utf-8") as file:
        ini.write(
            file,
            ids_mask=IDS_MASK,
            fields_mask=FIELDS_MASK,
            first=FIRST,
            value_getter=_value_getter
        )

    assert tmp_file.read_text() == RESULT


def test_ini_read_several_equal_signs():
    """Разделение на поле и его значение производится по первому знаку равенства.
    """
    ini = Ini(name="test_ini")
    ini.read_raw("\n".join([
        "[test]",
        "f1=v1=v2",
        "f2=v1 = v2",
        "f3=v1 = v2 = v3",
    ]))
    assert ini.get_string("test", "f1") == "v1=v2"
    assert ini.get_string("test", "f2") == "v1=v2"
    assert ini.get_string("test", "f3") == "v1=v2=v3"

def test_ini_read_fields_with_whitespaces():
    """В имени поля пробельные символы убираются только по краям.
    """
    ini = Ini(name="test_ini")
    ini.read_raw("\n".join([
        "[test]",
        " \t \tf f\t \t = v1",
        "\t \t f\tf \t \t = v2",
        "f  f = v3",
        "f\t\tf = v4",
    ]))
    assert ini.get_string("test", "f f") == "v1"
    assert ini.get_string("test", "f\tf") == "v2"
    assert ini.get_string("test", "f  f") == "v3"
    assert ini.get_string("test", "f\t\tf") == "v4"

def test_ini_read_fields_with_empty_name():
    """Строчки с пустым именем поля игнорируются.
    """
    ini = Ini(name="test_ini")
    ini.read_raw("\n".join([
        "[test]",
        "=",
        "==",
        "= =",
        " =",
        "\t=",
        "=v1",
        " =v2",
        "\t=v3",
        "f = v4",
        " = v5",
        "=v6=v7",
    ]))
    assert ini.section_exist("") == False
    assert len(ini.section("test").lines()) == 1
    assert ini.get_string("test", "f") == "v4"

def test_ini_read_with_repeating_field_names():
    """Повторяющееся имя поля: порядок определения сохраняется, но значение обновляется.
    """
    ini = Ini(name="test_ini")
    ini.read_raw("\n".join([
        "[test]",
        "f1 = v1",
        "f2 = v2",
        "f3 = v3",
        "f2 = v4",
        "f3 = v5",
        "f4 = v6",
        "f1 = v7",
        "f3 = v8",
    ]))
    section = ini.section("test")
    assert list(section.lines()) == ["f1", "f2", "f3", "f4"]
    assert section.field("f1") == "v7"
    assert section.field("f2") == "v4"
    assert section.field("f3") == "v8"
    assert section.field("f4") == "v6"

def test_ini_read_with_various_field_names_cases():
    """Имя поля чувствительно к регистру.
    """
    ini = Ini(name="test_ini")
    ini.read_raw("\n".join([
        "[test]",
        "field = v1",
        "FIELD = v2",
        "FiElD = v3",
    ]))
    section = ini.section("test")
    assert section.field("field") == "v1"
    assert section.field("FIELD") == "v2"
    assert section.field("FiElD") == "v3"

def test_ini_read_various_values():
    """Фильтрация пробельных символов в значении поля и сохранение регистра.
    """
    ini = Ini(name="test_ini")
    ini.read_raw("\n".join([
        '[test]',
        'f1 = V1',
        'f2 =    v2    ',
        'f3 =\t\t\t\tv3\t\t\t\t',
        'f4 =  v  4  ',
        'f5 = \t\tv\t\t5\t\t',
        'f6 = 1 2 3 4 5',
        'f7 = "1 2" 3 "4 5"',
        'f8 =  1  " 2 3 "  4  5  " 6    ',
        'f9 = "1\t2\t3"',
    ]))
    assert ini.get_string("test", "f1") == 'V1'
    assert ini.get_string("test", "f2") == 'v2'
    assert ini.get_string("test", "f3") == 'v3'
    assert ini.get_string("test", "f4") == 'v4'
    assert ini.get_string("test", "f5") == 'v5'
    assert ini.get_string("test", "f6") == '12345'
    assert ini.get_string("test", "f7") == '"1 2"3"4 5"'
    assert ini.get_string("test", "f8") == '1" 2 3 "45" 6'
    assert ini.get_string("test", "f9") == '"1\t2\t3"'

def test_ini_read_values_with_whitespaces(tmp_path):
    """Чтение с сохранением пробельных символов.
    """
    f1 = tmp_path / "file_1.ltx"
    f2 = tmp_path / "file_2.ltx"
    f1.write_text("\n".join([
        '[test_1]',
        'f1 = V1',
        'f2 =    v2    ',
        'f3 =\t\t\t\tv3\t\t\t\t',
        'f4 =  v  4  ',
        'f5 = \t\tv\t\t5\t\t',
        'f6 = 1 2 3 4 5',
        'f7 = "1 2" 3 "4 5"',
        'f8 =  1  " 2 3 "  4  5  " 6    ',
        'f9 = "1\t2\t3"',
        '',
        '#include "file_2.ltx"',
    ]))
    f2.write_text("\n".join([
        '[test_2]',
        'f1 =    v1    ',
        'f2 =  v  2  ',
        'f3 = \t\tv\t\t3\t\t',
        'f4 = 1 2 3 4 5',
        'f5 =  1  " 2 3 "  4  5  " 6    ',
    ]))

    ini = Ini(name="test_ini")
    ini.read(str(f1), inside_gamedata=False, preserve_value_whitespaces=True)

    assert ini.get_string("test_1", "f1") == 'V1'
    assert ini.get_string("test_1", "f2") == 'v2'
    assert ini.get_string("test_1", "f3") == 'v3'
    assert ini.get_string("test_1", "f4") == 'v  4'
    assert ini.get_string("test_1", "f5") == 'v\t\t5'
    assert ini.get_string("test_1", "f6") == '1 2 3 4 5'
    assert ini.get_string("test_1", "f7") == '"1 2" 3 "4 5"'
    assert ini.get_string("test_1", "f8") == '1  " 2 3 "  4  5  " 6'
    assert ini.get_string("test_1", "f9") == '"1\t2\t3"'
    assert ini.get_string("test_2", "f1") == 'v1'
    assert ini.get_string("test_2", "f2") == 'v  2'
    assert ini.get_string("test_2", "f3") == 'v\t\t3'
    assert ini.get_string("test_2", "f4") == '1 2 3 4 5'
    assert ini.get_string("test_2", "f5") == '1  " 2 3 "  4  5  " 6'

def test_ini_read_with_comments():
    """Поддержка комментариев ``;`` и ``//``.

    C-style комментарий ``//`` не поддерживается,
    если до него встретился одиночный символ ``/``
    (баг *xrEngine*).
    """
    ini = Ini(name="test_ini")
    ini.read_raw("\n".join([
        "; Comment line with semicolon",
        "// Comment line in C-style",
        ";//;//;//",
        "//;//;//;//;",
        "; [innore_me]",
        "// [innore_me]",
        "[test]",
        "; Another comment line with semicolon",
        "// Another comment line in C-style",
        ";//;//;//;",
        "//;//;//;//",
        "f1 = v1 ; 1st value",
        "f2 = v2  // 2nd value",
        "f3 = v/3 // 3d value",
        "f4 =  \"v4    ; 4th value",
        "f5 =  \"v5    // 5th value",
    ]))
    assert list(ini.ids()) == ["test"]
    assert list(ini.section("test").lines()) == ["f1", "f2", "f3", "f4", "f5"]
    assert ini.get_string("test", "f1") == "v1"
    assert ini.get_string("test", "f2") == "v2"
    assert ini.get_string("test", "f3") == "v/3//3dvalue"
    assert ini.get_string("test", "f4") == "\"v4    "
    assert ini.get_string("test", "f5") == "\"v5    "

def test_ini_read_with_odd_section_ids():
    ini = Ini(name="test_ini")
    ini.read_raw("\n".join([
        "[ test ]",
        "f1 = v1",
        "[TEST]",
        "f2 = v2",
        "[]",
        "f3 = v3",
        "[[\taz@-_. ]",
        "f4 = v4",
        "[sect]don't]mind]me]абвгд]!@#$%^&*()_+]",
        "f5 = v5",
    ]))
    assert list(ini.ids()) == [" test ", "test", "", "[\taz@-_. ", "sect"]
    assert ini.get_string(" test ", "f1") == "v1"
    assert ini.get_string("test", "f2") == "v2"
    assert ini.get_string("", "f3") == "v3"
    assert ini.get_string("[\taz@-_. ", "f4") == "v4"
    assert ini.get_string("sect", "f5") == "v5"

def test_ini_read_with_odd_inheritance_1():
    """Пробельные символы и регистр при наследовании.
    """
    ini = Ini(name="test_ini")
    ini.read_raw("\n".join([
        "[test 1]",
        "field_1",
        "[test\t2]",
        "field_2",
        "[test_3]",
        "field_3",
        "[main]:    test 1    ,\t\ttest\t2\t\t, \tTEST_3 \t",
    ]))
    assert ini.line_exist("main", "field_1") == True
    assert ini.line_exist("main", "field_2") == True
    assert ini.line_exist("main", "field_3") == True

def test_ini_read_with_odd_inheritance_2():
    """Рассинхрон конца ID и начала списка наследования.
    """
    ini = Ini(name="test_ini")
    ini.read_raw("\n".join([
        "[test_1]",
        "field_1",
        "[main]wtf_is_this]:test_1",
    ]))
    assert ini.section_exist("main") == True
    assert ini.line_exist("main", "field_1") == True

def test_ini_read_with_odd_inheritance_3():
    """Лишние символы между ``]:`` убирают наследование.
    """
    ini = Ini(name="test_ini")
    ini.read_raw("\n".join([
        "[parent]",
        "field",
        "[child] :parent",
    ]))
    assert ini.section_exist("child") == True
    assert ini.line_exist("child", "field") == False

def test_ini_read_with_odd_inheritance_4():
    """Наследоваться от пустой секции нельзя.
    """
    ini = Ini(name="test_ini")
    with pytest.raises(Ini.Error):
        ini.read_raw("\n".join([
            "[]",
            "[p1]",
            "[p2]",
            "[test]:p1,,p2",
        ]))

def test_ini_read_with_odd_include_1(tmp_path):
    """Включение несуществующего файла - ERR.
    """
    file_path = tmp_path / "test.ltx"
    file_path.write_text("\n".join([
        '#include "unknown.ltx"'
    ]))
    ini = Ini(name="test_ini")
    assert file_path.is_file() == True
    with pytest.raises(Ini.Error):
        ini.read(str(file_path), inside_gamedata=False)

def test_ini_read_with_odd_include_2(tmp_path):
    """Строка include-директивы без кавычек - ERR.
    """
    file_path = tmp_path / "test.ltx"
    file_path.write_text("\n".join([
        '#include unknown.ltx'
    ]))
    ini = Ini(name="test_ini")
    assert file_path.is_file() == True
    with pytest.raises(Ini.Error):
        ini.read(str(file_path), inside_gamedata=False)

def test_ini_read_with_odd_include_3(tmp_path):
    """Строка include-директивы с одной кавычкой - OK.
    """
    f1_path = tmp_path / "f1.ltx"
    f1_path.write_text("\n".join([
        '#include "f2.ltx'
    ]))
    f2_path = tmp_path / "f2.ltx"
    f2_path.write_text("\n".join([
        '[test]',
    ]))
    ini = Ini(name="test_ini")
    ini.read(str(f1_path), inside_gamedata=False)
    assert ini.section_exist("test") == True

def test_ini_read_with_odd_include_4(tmp_path):
    """Строка include-директивы с пробельными символами вокруг пути - OK.
    """
    f1_path = tmp_path / "f1.ltx"
    f1_path.write_text("\n".join([
        '#include "\t \t f2.ltx\t\t  "'
    ]))
    f2_path = tmp_path / "f2.ltx"
    f2_path.write_text("\n".join([
        '[test]',
    ]))
    ini = Ini(name="test_ini")
    ini.read(str(f1_path), inside_gamedata=False)
    assert ini.section_exist("test") == True

def test_ini_read_with_odd_include_5(tmp_path):
    """Строка include-директивы с мусором вокруг кавычек - OK.
    """
    f1_path = tmp_path / "f1.ltx"
    f1_path.write_text("\n".join([
        '#includeАбВГд!@#$%^&*()_+"f2.ltx"Abcd"№;%:?*()-='
    ]))
    f2_path = tmp_path / "f2.ltx"
    f2_path.write_text("\n".join([
        '[test]',
    ]))
    ini = Ini(name="test_ini")
    ini.read(str(f1_path), inside_gamedata=False)
    assert ini.section_exist("test") == True


def test_ini_add():
    s1 = Section(id="s1")
    s1.add("f1", "s1v1")
    s1.add("f2", "s1v2")
    s2 = Section(id="s2")
    s2.add("f1", "s2v1")
    s2.add("f2", "s2v2")
    s3 = Section(id="s3")
    s3.add("f1", "s3v1")
    s3.add("f2", "s3v2")
    ini = Ini()

    ini.add(s1)
    ini.add(s2)
    ini.add(s3)

    assert list(ini.ids()) == ["s1", "s2", "s3"]
    assert list(ini.section("s1").fields()) == [("f1", "s1v1"), ("f2", "s1v2")]
    assert list(ini.section("s2").fields()) == [("f1", "s2v1"), ("f2", "s2v2")]
    assert list(ini.section("s3").fields()) == [("f1", "s3v1"), ("f2", "s3v2")]


def test_ini_add_without_reference():
    s1 = Section(id="s1")
    s1.add("f1", "v1")
    ini = Ini()

    ini.add(s1, by_reference=False)
    assert ini.section_exist("s1") == True
    assert ini.line_exist("s1", "f1") == True
    assert ini.get_string("s1", "f1") == "v1"

    s1.clear()
    assert ini.section_exist("s1") == True
    assert ini.line_exist("s1", "f1") == True
    assert ini.get_string("s1", "f1") == "v1"


def test_ini_add_by_reference():
    s1 = Section(id="s1")
    s1.add("f1", "v1")
    ini = Ini()

    ini.add(s1, by_reference=True)
    assert ini.section_exist("s1") == True
    assert ini.line_exist("s1", "f1") == True
    assert ini.get_string("s1", "f1") == "v1"

    s1.clear()
    assert ini.section_exist("s1") == True
    assert ini.line_exist("s1", "f1") == False


def test_ini_add_overwrite():
    s1 = Section(id="test")
    s1.add("f1", None)
    s2 = Section(id="test")
    s2.add("f2", None)
    ini = Ini()

    ini.add(s1)
    assert ini.line_exist("test", "f1") == True
    assert ini.line_exist("test", "f2") == False

    with pytest.raises(Ini.Error):
        ini.add(s2, overwrite=False)

    ini.add(s2, overwrite=True)
    assert ini.line_exist("test", "f1") == False
    assert ini.line_exist("test", "f2") == True


def test_ini_clear():
    ini = Ini()
    ini.add(Section(id="s1"))
    ini.add(Section(id="s2"))
    assert ini.section_exist("s1") == True
    assert ini.section_exist("s2") == True

    ini.clear()
    assert ini.section_exist("s1") == False
    assert ini.section_exist("s2") == False


def _test_ini_read_encoding(tmp_path, encoding):
    file_path = tmp_path / "test.ltx"
    file_path.write_text("\n".join([
        "[eng] ; Latin",
        "lower = qwertyuiopasdfghjklzxcvbnm",
        "UPPER = QWERTYUIOPASDFGHJKLZXCVBNM",
        "",
        "[symbols]",
        "; !@#$%^&*()-=_+[]{}|/:'<>,.?",
        "; \\",
        "; \"",
        "; \t",
        "; №",
        "",
        "[rus] ; Cyrillic",
        "lang = rus",
        "lower = йцукенгшщзхъфывапролджэячсмитьбю",
        "UPPER = ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ",
        "",
        "[numbers]",
        "digits = 1234567890",
    ]), encoding=encoding)

    ini = Ini()
    ini.read(str(file_path), inside_gamedata=False)

    assert ini.section_exist("eng") == True
    assert ini.section_exist("symbols") == True
    assert ini.section_exist("rus") == True
    assert ini.section_exist("numbers") == True

    assert ini.get_string("eng", "lower") == "qwertyuiopasdfghjklzxcvbnm"
    assert ini.get_string("eng", "UPPER") == "QWERTYUIOPASDFGHJKLZXCVBNM"
    assert ini.get_string("rus", "lower") == "йцукенгшщзхъфывапролджэячсмитьбю"
    assert ini.get_string("rus", "UPPER") == "ЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ"
    assert ini.get_string("numbers", "digits") == "1234567890"

def test_ini_read_encoding_utf8(tmp_path):
    _test_ini_read_encoding(tmp_path, "utf-8")

def test_ini_read_encoding_utf8bom(tmp_path):
    _test_ini_read_encoding(tmp_path, "utf-8-sig")

def test_ini_read_encoding_cp1251(tmp_path):
    _test_ini_read_encoding(tmp_path, "cp1251")

def test_ini_read_encoding_default(tmp_path):
    _test_ini_read_encoding(tmp_path, None)


def test_ini_read_inside_gamedata(tmp_path):
    # Setting up folders
    gd_mod_path = tmp_path / "gamedata-mod"
    gd_alt_path = tmp_path / "gamedata-alt"
    gd_mod_path.mkdir()
    gd_alt_path.mkdir()
    cfg_mod_path = gd_mod_path / "config"
    cfg_alt_path = gd_alt_path / "config"
    cfg_mod_path.mkdir()
    cfg_alt_path.mkdir()
    misc_alt_path = cfg_alt_path / "misc"
    misc_alt_path.mkdir()

    # Setting up files
    entry_mod = cfg_mod_path / "entry_mod.ltx"
    entry_alt = cfg_alt_path / "entry_alt.ltx"
    f_shared_mod = cfg_mod_path / "shared.ltx"
    f_shared_alt = cfg_alt_path / "shared.ltx"
    f_mod = cfg_mod_path / "mod.ltx"
    f_alt = misc_alt_path / "alt.ltx"

    # Setting up meta ini
    _ss = Section(id="settings")
    _ss.add("gamedata_path_mod", f'"{str(gd_mod_path)}"')
    _ss.add("gamedata_path_alt", f'"{str(gd_alt_path)}"')
    ini_meta = Ini(name="meta")
    ini_meta.add(_ss, by_reference=True)

    # Writing to files
    for entry_path in (entry_mod, entry_alt):
        entry_path.write_text("\n".join([
            r'#include "shared.ltx"',
            r'#include "mod.ltx"',
            r'#include "misc\alt.ltx"',
        ]))
    f_shared_mod.write_text("\n".join([
        "[section_shared]",
        "taken_from = mod",
    ]))
    f_shared_alt.write_text("\n".join([
        "[section_shared]",
        "taken_from = alt",
    ]))
    f_mod.write_text("\n".join([
        "[section_mod]",
        "taken_from = mod",
    ]))
    f_alt.write_text("\n".join([
        "[section_alt]",
        "taken_from = alt",
    ]))

    # Testing both entry points
    for entry_path in (entry_mod, entry_alt):
        ini = Ini(name=entry_path.stem, ini_meta=ini_meta)
        ini.read(f"config\\{entry_path.name}", inside_gamedata=True)

        assert ini.section_exist("section_shared") == True
        assert ini.section_exist("section_mod") == True
        assert ini.section_exist("section_alt") == True
        assert ini.get_string("section_shared", "taken_from") == "mod"
        assert ini.get_string("section_mod", "taken_from") == "mod"
        assert ini.get_string("section_alt", "taken_from") == "alt"


def test_ini_read_inside_gamedata_prefix_1(tmp_path):
    """Строка пути до ALT является префиксом строки пути до MOD.
    """
    # Setting up folders
    gd_mod_path = tmp_path / "gamedata-mod"
    gd_alt_path = tmp_path / "gamedata"
    gd_mod_path.mkdir()
    gd_alt_path.mkdir()

    # Setting up files
    mod_entry = gd_mod_path / "entry.ltx"
    mod_file = gd_mod_path / "file.ltx"

    # Setting up meta ini
    _ss = Section(id="settings")
    _ss.add("gamedata_path_mod", f'"{str(gd_mod_path)}"')
    _ss.add("gamedata_path_alt", f'"{str(gd_alt_path)}"')
    ini_meta = Ini(name="meta")
    ini_meta.add(_ss, by_reference=True)

    # Writing to files
    mod_entry.write_text("\n".join([
        r'#include "file.ltx"',
    ]))
    mod_file.write_text("\n".join([
        "[section_test]",
    ]))

    # Testing
    ini = Ini(name="entry", ini_meta=ini_meta)
    ini.read(mod_entry.name, inside_gamedata=True)
    assert ini.section_exist("section_test") == True

def test_ini_read_inside_gamedata_prefix_2(tmp_path):
    """Строка пути до MOD является префиксом строки пути до ALT.
    """
    # Setting up folders
    gd_mod_path = tmp_path / "gamedata"
    gd_alt_path = tmp_path / "gamedata-alt"
    gd_mod_path.mkdir()
    gd_alt_path.mkdir()

    # Setting up files
    alt_entry = gd_alt_path / "entry.ltx"
    alt_file = gd_alt_path / "file.ltx"
    mod_file = gd_mod_path / "file.ltx"

    # Setting up meta ini
    _ss = Section(id="settings")
    _ss.add("gamedata_path_mod", f'"{str(gd_mod_path)}"')
    _ss.add("gamedata_path_alt", f'"{str(gd_alt_path)}"')
    ini_meta = Ini(name="meta")
    ini_meta.add(_ss, by_reference=True)

    # Writing to files
    alt_entry.write_text("\n".join([
        r'#include "file.ltx"',
    ]))
    alt_file.write_text("\n".join([
        "[section_test]",
        "taken_from = alt",
    ]))
    mod_file.write_text("\n".join([
        "[section_test]",
        "taken_from = mod",
    ]))

    # Testing
    ini = Ini(name="entry", ini_meta=ini_meta)
    ini.read(alt_entry.name, inside_gamedata=True)
    assert ini.get_string("section_test", "taken_from") == "mod"


def test_ini_get_string_wb():
    ini = Ini(name="test_ini")
    ini.read_raw("\n".join([
        '[test]',
        'valid_1 = ',
        'valid_2 = ""',
        'valid_3 = "Text"',
        'valid_4  = "Long Text"',
        'no_value',
    ]))

    # valid format
    assert ini.get_string_wb("test", "valid_1") == ""
    assert ini.get_string_wb("test", "valid_2") == ""
    assert ini.get_string_wb("test", "valid_3") == "Text"
    assert ini.get_string_wb("test", "valid_4") == "Long Text"
    
    # valid format with defval
    assert ini.get_string_wb("test", "valid_1", defval="def") == ""
    assert ini.get_string_wb("test", "valid_2", defval="def") == ""
    assert ini.get_string_wb("test", "valid_3", defval="def") == "Text"
    assert ini.get_string_wb("test", "valid_4", defval="def") == "Long Text"

    # no value with defval
    assert ini.get_string_wb("test", "no_value", defval="def_1") == "def_1"
    assert ini.get_string_wb("test", "no_value", defval="def_2") == "def_2"

    # non-existent field with defval
    assert ini.get_string_wb("test", "unknown", defval="def_1") == "def_1"
    assert ini.get_string_wb("test", "unknown", defval="def_2") == "def_2"

    # no value
    with pytest.raises(Section.Error):
        _ = ini.get_string_wb("test", "no_value")

    # non-existent field
    with pytest.raises(Section.Error):
        _ = ini.get_string_wb("test", "unknown")

    # non-existent section
    with pytest.raises(Ini.Error):
        _ = ini.get_string_wb("unknown", "valid_1")
