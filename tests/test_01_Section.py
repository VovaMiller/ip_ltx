import io
import pytest

from ip_ltx import Section


def test_section_add_various_fields():
    section = Section(id="test")
    FIELDS = [
        "field",
        "FIELD",
        "FiElD",
        "a b",
        "a\tb",
        "\tabc\t",
        " def ",
        "\t \t fld\t \t ",
    ]
    for i, fld in enumerate(FIELDS):
        section.add(fld, str(i))
    
    assert list(section.lines()) == [fld.strip() for fld in FIELDS]
    for i, fld in enumerate(FIELDS):
        assert section.field(fld.strip()) == str(i)

def test_section_add_various_values():
    section = Section(id="test")

    section.add("field", None, overwrite=True)
    assert section.field("field") is None

    section.add("field", "", overwrite=True)
    assert section.field("field") == ""

    section.add("field", " ", overwrite=True)
    assert section.field("field") == ""

    section.add("field", "\t", overwrite=True)
    assert section.field("field") == ""

    section.add("field", "value", overwrite=True)
    assert section.field("field") == "value"

    section.add("field", "VALUE", overwrite=True)
    assert section.field("field") == "VALUE"

    section.add("field", " \tvalue \t", overwrite=True)
    assert section.field("field") == "value"

    section.add("field", '    "w1 w2"    ', overwrite=True)
    assert section.field("field") == '"w1 w2"'

    section.add("field", '    "w1\tw2\tw3"    ', overwrite=True)
    assert section.field("field") == '"w1\tw2\tw3"'

    section.add("field", ' "w1 w2" w3 w4 " w5 w6 " w7 ', overwrite=True)
    assert section.field("field") == '"w1 w2"w3w4" w5 w6 "w7'

    section.add("field", ' "w1 w2" w3 w4 " w5 w6    ', overwrite=True)
    assert section.field("field") == '"w1 w2"w3w4" w5 w6    '

def test_section_add_invalid_fields():
    section = Section(id="test")

    # empty field name
    with pytest.raises(ValueError):
        section.add("", "value")
    
    # multiline field name
    with pytest.raises(ValueError):
        section.add("line1\nline2", "value")
    
    # field name with comment sequence: semicolon
    with pytest.raises(ValueError):
        section.add("abc;def", "value")
    
    # field name with comment sequence: C-style
    with pytest.raises(ValueError):
        section.add("abc//def", "value")

def test_section_add_invalid_values():
    section = Section(id="test")

    # multiline value
    with pytest.raises(ValueError):
        section.add("field", "line1\nline2")

    # value with comment sequence: semicolon
    with pytest.raises(ValueError):
        section.add("field", "abc;def")

    # value with comment sequence: C-style
    with pytest.raises(ValueError):
        section.add("field", "abc//def")

def test_section_basics():
    section = Section(id="test")
    FIELDS = ["field_with_value", "field_with_empty_value", "field_without_value"]
    VALUES = ["value_1", "", None]
    for field, value in zip(FIELDS, VALUES):
        section.add(field, value)
    
    # start point check
    assert list(section.lines()) == FIELDS
    assert list(section.fields()) == list(zip(FIELDS, VALUES))

    assert section.line_exist("field_with_value") == True
    assert section.line_exist("field_with_empty_value") == True
    assert section.line_exist("field_without_value") == True
    assert section.line_exist("field_with_value_") == False
    assert section.line_exist("_field_with_value") == False
    assert section.line_exist("field") == False

    assert section.line_exist_with_value("field_with_value") == True
    assert section.line_exist_with_value("field_with_empty_value") == True
    assert section.line_exist_with_value("field_without_value") == False
    assert section.line_exist_with_value("field_with_value_") == False
    assert section.line_exist_with_value("_field_with_value") == False
    assert section.line_exist_with_value("field") == False

    assert section.field("field_with_value") == "value_1"
    assert section.field("field_with_empty_value") == ""
    assert section.field("field_without_value") is None
    with pytest.raises(Section.Error):
        _ = section.field("field")

    # updating value and changing back
    with pytest.raises(Section.Error):
        section.add("field_with_value", "value_2")
    section.add("field_with_value", "value_2", overwrite=True)
    assert section.field("field_with_value") == "value_2"
    section.add("field_with_value", None, overwrite=True)
    assert section.line_exist("field_with_value") == True
    assert section.line_exist_with_value("field_with_value") == False
    assert section.field("field_with_value") is None
    section.add("field_with_value", "value_1", overwrite=True)
    assert section.field("field_with_value") == "value_1"
    
    # equal to the start point
    assert list(section.lines()) == FIELDS
    assert list(section.fields()) == list(zip(FIELDS, VALUES))

def test_section_write_without_params():
    section = Section(id="test")
    section.add("field_one", "value_1")
    section.add("field_two", "")
    section.add("field_three", None)
    section.add("field_four", "    ")
    section.add("field_five", " 1, 2,  3,   4    ")
    section.add("custom_data", "line_1\nline_2")
    buffer = io.StringIO()
    RESULT = "\n".join([
        "[test]",
        "field_one = value_1",
        "field_two = ",
        "field_three",
        "field_four = ",
        "field_five = 1,2,3,4",
        "custom_data = <<END",
        "line_1",
        "line_2",
        "END",
        "",
        "",
    ])

    section.write(buffer)

    assert buffer.getvalue() == RESULT

def test_section_write_with_first():
    section = Section(id="test")
    section.add("field_one", "value_1")
    section.add("field_two", "")
    section.add("field_three", None)
    section.add("field_four", "value_4")
    section.add("field_five", None)
    section.add("field_six", "value_6")
    section.add("field_seven", None)
    buffer = io.StringIO()
    RESULT = "\n".join([
        "[test]",
        "field_three",
        "field_one = value_1",
        "field_four = value_4",
        "field_two = ",
        "field_five",
        "field_six = value_6",
        "field_seven",
        "",
        "",
    ])

    section.write(
        buffer,
        first=["field_three", "field_one", "field_eight", "field_four", "field_nine"]
    )

    assert buffer.getvalue() == RESULT

def test_section_write_with_filter():
    section = Section(id="test")
    section.add("field_one", "value_1")
    section.add("field_two", "")
    section.add("field_three", None)
    section.add("field_four", "value_4")
    section.add("field_five", None)
    section.add("field_six", "value_6")
    section.add("field_seven", None)
    buffer = io.StringIO()
    RESULT = "\n".join([
        "[test]",
        "field_two = ",
        "field_three",
        "field_six = value_6",
        "field_seven",
        "",
        "",
    ])

    section.write(buffer, fields_mask=r"field_(t|s)\w+")

    assert buffer.getvalue() == RESULT

def test_section_write_with_getter():
    def _value_getter(section: Section, field: str) -> str | None:
        value = section.field(field)
        match value:
            case None:
                return "None"
            case value if len(value) == 0:
                return None
            case _:
                return value.upper()
    
    section = Section(id="test")
    section.add("field_one", "value_1")
    section.add("field_two", "")
    section.add("field_three", None)
    section.add("field_four", "value_4")
    section.add("field_five", None)
    section.add("field_six", "value_6")
    section.add("field_seven", None)
    buffer = io.StringIO()
    RESULT = "\n".join([
        "[test]",
        "field_one = VALUE_1",
        "field_two",
        "field_three = None",
        "field_four = VALUE_4",
        "field_five = None",
        "field_six = VALUE_6",
        "field_seven = None",
        "",
        "",
    ])

    section.write(buffer, value_getter=_value_getter)

    assert buffer.getvalue() == RESULT

def test_section_write_with_all_params():
    def _value_getter(section: Section, field: str) -> str | None:
        value = section.field(field)
        match value:
            case None:
                return "None"
            case value if len(value) == 0:
                return None
            case _:
                return value.upper()
    
    section = Section(id="test")
    section.add("field_one", "value_1")
    section.add("field_two", "")
    section.add("field_three", None)
    section.add("field_four", "value_4")
    section.add("field_five", None)
    section.add("field_six", "value_6")
    section.add("field_seven", None)
    buffer = io.StringIO()
    RESULT = "\n".join([
        "[test]",
        "field_six = VALUE_6",
        "field_four = VALUE_4",
        "field_two",
        "field_three = None",
        "field_seven = None",
        "",
        "",
    ])

    section.write(
        buffer,
        fields_mask=r"field_(?!one|five)\w+",
        first=["field_six", "field_five", "field_four"],
        value_getter=_value_getter
    )

    assert buffer.getvalue() == RESULT

def test_section_casts():
    # string_wb
    assert Section.cast_string_wb('"inside quotes"') == 'inside quotes'
    assert Section.cast_string_wb('"test"') == 'test'
    assert Section.cast_string_wb('"test') == 'test'
    assert Section.cast_string_wb('test"') == 'test'
    assert Section.cast_string_wb('test') == 'test'
    assert Section.cast_string_wb('"A"') == 'A'
    assert Section.cast_string_wb('"A') == 'A'
    assert Section.cast_string_wb('A"') == 'A'
    assert Section.cast_string_wb('A') == 'A'
    assert Section.cast_string_wb('"""""') == '"""'
    assert Section.cast_string_wb('"""') == '"'
    assert Section.cast_string_wb('""') == ''
    assert Section.cast_string_wb('"') == ''

    # float: valid format
    assert Section.cast_float("0") == pytest.approx(0.0, abs=1e-6)
    assert Section.cast_float("-0") == pytest.approx(0.0, abs=1e-6)
    assert Section.cast_float("+0") == pytest.approx(0.0, abs=1e-6)
    assert Section.cast_float("0.0") == pytest.approx(0.0, abs=1e-6)
    assert Section.cast_float("+0.0") == pytest.approx(0.0, abs=1e-6)
    assert Section.cast_float("-0.0") == pytest.approx(0.0, abs=1e-6)
    assert Section.cast_float("0.0000") == pytest.approx(0.0, abs=1e-6)
    assert Section.cast_float("1") == pytest.approx(1.0, abs=1e-6)
    assert Section.cast_float("-1") == pytest.approx(-1.0, abs=1e-6)
    assert Section.cast_float("+1") == pytest.approx(1.0, abs=1e-6)
    assert Section.cast_float("1.0") == pytest.approx(1.0, abs=1e-6)
    assert Section.cast_float("-1.0") == pytest.approx(-1.0, abs=1e-6)
    assert Section.cast_float("+1.0") == pytest.approx(1.0, abs=1e-6)
    assert Section.cast_float("1.0000") == pytest.approx(1.0, abs=1e-6)
    assert Section.cast_float("3.14") == pytest.approx(3.14, abs=1e-6)
    assert Section.cast_float("-3.14") == pytest.approx(-3.14, abs=1e-6)
    assert Section.cast_float(".123") == pytest.approx(0.123, abs=1e-6)
    assert Section.cast_float("-.123") == pytest.approx(-0.123, abs=1e-6)
    assert Section.cast_float("+.123") == pytest.approx(0.123, abs=1e-6)
    assert Section.cast_float("1e-2") == pytest.approx(0.01, abs=1e-6)
    assert Section.cast_float("1E-2") == pytest.approx(0.01, abs=1e-6)
    assert Section.cast_float("+1e-2") == pytest.approx(0.01, abs=1e-6)
    assert Section.cast_float("+1E-2") == pytest.approx(0.01, abs=1e-6)
    assert Section.cast_float("-1e-2") == pytest.approx(-0.01, abs=1e-6)
    assert Section.cast_float("-1E-2") == pytest.approx(-0.01, abs=1e-6)
    assert Section.cast_float("00009") == pytest.approx(9.0, abs=1e-6)
    assert Section.cast_float("+00009") == pytest.approx(9.0, abs=1e-6)
    assert Section.cast_float("-00009") == pytest.approx(-9.0, abs=1e-6)

    # float: invalid format
    assert Section.cast_float("") is None  # 0.0
    assert Section.cast_float("a") is None  # 0.0
    assert Section.cast_float("123,456") is None  # 123.0
    assert Section.cast_float("123abc") is None  # 123.0
    assert Section.cast_float("+123e-3F") is None  # 0.123

    # s32: valid format
    assert Section.cast_int("0") == 0
    assert Section.cast_int("1") == 1
    assert Section.cast_int("+1") == 1
    assert Section.cast_int("-1") == -1
    assert Section.cast_int("12345") == 12345
    assert Section.cast_int("+12345") == 12345
    assert Section.cast_int("-12345") == -12345
    assert Section.cast_int("000123") == 123
    assert Section.cast_int("+000123") == 123
    assert Section.cast_int("-000123") == -123

    # s32: invalid format
    assert Section.cast_int("") is None  # 0
    assert Section.cast_int("a") is None  # 0
    assert Section.cast_int("123.456") is None  # 123
    assert Section.cast_int("123,456") is None  # 123
    assert Section.cast_int("123abc") is None  # 123
    assert Section.cast_int("zero") is None  # 0
    assert Section.cast_int("one") is None  # 0

    # u32
    assert Section.cast_uint("0") == 0
    assert Section.cast_uint("1") == 1
    assert Section.cast_uint("123456") == 123456
    assert Section.cast_uint("+0") is None  # 0
    assert Section.cast_uint("+1") is None  # 1
    assert Section.cast_uint("+123") is None  # 123
    assert Section.cast_uint("-0") is None  # ?
    assert Section.cast_uint("-1") is None  # ?
    assert Section.cast_uint("-123") is None  # ?
    assert Section.cast_uint("abc") is None  # 0
    assert Section.cast_uint("123abc") is None  # 123
    assert Section.cast_uint("123.456") is None  # 123

    # bool
    assert Section.cast_bool("on") == True
    assert Section.cast_bool("On") == True
    assert Section.cast_bool("ON") == True
    assert Section.cast_bool("yes") == True
    assert Section.cast_bool("Yes") == True
    assert Section.cast_bool("YES") == True
    assert Section.cast_bool("true") == True
    assert Section.cast_bool("True") == True
    assert Section.cast_bool("TRUE") == True
    assert Section.cast_bool("1") == True
    assert Section.cast_bool("off") == False
    assert Section.cast_bool("Off") == False
    assert Section.cast_bool("OFF") == False
    assert Section.cast_bool("no") == False
    assert Section.cast_bool("No") == False
    assert Section.cast_bool("NO") == False
    assert Section.cast_bool("false") == False
    assert Section.cast_bool("False") == False
    assert Section.cast_bool("FALSE") == False
    assert Section.cast_bool("0") == False
    assert Section.cast_bool("") is None
    assert Section.cast_bool("on_") is None
    assert Section.cast_bool("_on") is None
    assert Section.cast_bool("not") is None
    assert Section.cast_bool("00") is None
    assert Section.cast_bool("11") is None
    assert Section.cast_bool("2") is None

def test_section_get_string_wb():
    section = Section(id="test")
    section.add("valid_1", '')
    section.add("valid_2", '""')
    section.add("valid_3", 'Text')
    section.add("valid_4", '"Long Text"')
    section.add("no_value", None)
    
    # valid format
    assert section.get_string_wb("valid_1") == ""
    assert section.get_string_wb("valid_2") == ""
    assert section.get_string_wb("valid_3") == "Text"
    assert section.get_string_wb("valid_4") == "Long Text"
    
    # valid format with defval
    assert section.get_string_wb("valid_1", defval="def") == ""
    assert section.get_string_wb("valid_2", defval="def") == ""
    assert section.get_string_wb("valid_3", defval="def") == "Text"
    assert section.get_string_wb("valid_4", defval="def") == "Long Text"

    # no value with defval
    assert section.get_string_wb("no_value", defval="def_1") == "def_1"
    assert section.get_string_wb("no_value", defval="def_2") == "def_2"

    # non-existent with defval
    assert section.get_string_wb("unknown", defval="def_1") == "def_1"
    assert section.get_string_wb("unknown", defval="def_2") == "def_2"

    # no value
    with pytest.raises(Section.Error):
        _ = section.get_string_wb("no_value")

    # non-existent
    with pytest.raises(Section.Error):
        _ = section.get_string_wb("unknown")

def test_section_get_elem():
    section = Section(id="test")
    section.add("field_string_valid_1", "")
    section.add("field_string_valid_2", "123")
    section.add("field_string_valid_3", "Hello")
    section.add("field_string_invalid_1", None)
    section.add("field_float_valid_1", "1")
    section.add("field_float_valid_2", "1.23")
    section.add("field_float_valid_3", "-.123")
    section.add("field_float_invalid_1", None)
    section.add("field_float_invalid_2", "")
    section.add("field_float_invalid_3", "zero")
    section.add("field_float_invalid_4", "1,23")
    section.add("field_int_valid_1", "0")
    section.add("field_int_valid_2", "123")
    section.add("field_int_valid_3", "-123")
    section.add("field_int_invalid_1", None)
    section.add("field_int_invalid_2", "")
    section.add("field_int_invalid_3", "1.23")
    section.add("field_int_invalid_4", "zero")
    section.add("field_uint_valid_1", "0")
    section.add("field_uint_valid_2", "123")
    section.add("field_uint_invalid_1", None)
    section.add("field_uint_invalid_2", "")
    section.add("field_uint_invalid_3", "-123")
    section.add("field_uint_invalid_4", "zero")
    section.add("field_uint_invalid_5", "1.23")
    section.add("field_bool_valid_1", "on")
    section.add("field_bool_valid_2", "yes")
    section.add("field_bool_valid_3", "true")
    section.add("field_bool_valid_4", "1")
    section.add("field_bool_valid_5", "off")
    section.add("field_bool_valid_6", "no")
    section.add("field_bool_valid_7", "false")
    section.add("field_bool_valid_8", "0")
    section.add("field_bool_invalid_1", None)
    section.add("field_bool_invalid_2", "")
    section.add("field_bool_invalid_3", "not")
    
    # valid format
    assert section.get_string("field_string_valid_1") == ""
    assert section.get_string("field_string_valid_2") == "123"
    assert section.get_string("field_string_valid_3") == "Hello"
    assert section.get_float("field_float_valid_1") == pytest.approx(1.0, abs=1e-6)
    assert section.get_float("field_float_valid_2") == pytest.approx(1.23, abs=1e-6)
    assert section.get_float("field_float_valid_3") == pytest.approx(-0.123, abs=1e-6)
    assert section.get_int("field_int_valid_1") == 0
    assert section.get_int("field_int_valid_2") == 123
    assert section.get_int("field_int_valid_3") == -123
    assert section.get_uint("field_uint_valid_1") == 0
    assert section.get_uint("field_uint_valid_2") == 123
    assert section.get_bool("field_bool_valid_1") == True
    assert section.get_bool("field_bool_valid_2") == True
    assert section.get_bool("field_bool_valid_3") == True
    assert section.get_bool("field_bool_valid_4") == True
    assert section.get_bool("field_bool_valid_5") == False
    assert section.get_bool("field_bool_valid_6") == False
    assert section.get_bool("field_bool_valid_7") == False
    assert section.get_bool("field_bool_valid_8") == False
    
    # valid format with defval
    assert section.get_string("field_string_valid_1", defval="def") == ""
    assert section.get_string("field_string_valid_2", defval="def") == "123"
    assert section.get_string("field_string_valid_3", defval="def") == "Hello"
    assert section.get_float("field_float_valid_1", defval=3.14) == pytest.approx(1.0, abs=1e-6)
    assert section.get_float("field_float_valid_2", defval=3.14) == pytest.approx(1.23, abs=1e-6)
    assert section.get_float("field_float_valid_3", defval=3.14) == pytest.approx(-0.123, abs=1e-6)
    assert section.get_int("field_int_valid_1", defval=-999) == 0
    assert section.get_int("field_int_valid_2", defval=-999) == 123
    assert section.get_int("field_int_valid_3", defval=-999) == -123
    assert section.get_uint("field_uint_valid_1", defval=999) == 0
    assert section.get_uint("field_uint_valid_2", defval=999) == 123
    assert section.get_bool("field_bool_valid_1", defval=False) == True
    assert section.get_bool("field_bool_valid_2", defval=False) == True
    assert section.get_bool("field_bool_valid_3", defval=False) == True
    assert section.get_bool("field_bool_valid_4", defval=False) == True
    assert section.get_bool("field_bool_valid_5", defval=True) == False
    assert section.get_bool("field_bool_valid_6", defval=True) == False
    assert section.get_bool("field_bool_valid_7", defval=True) == False
    assert section.get_bool("field_bool_valid_8", defval=True) == False

    # no value with defval
    assert section.get_string("field_string_invalid_1", defval="def_1") == "def_1"
    assert section.get_string("field_string_invalid_1", defval="def_2") == "def_2"
    assert section.get_float("field_float_invalid_1", defval=3.14) == pytest.approx(3.14, abs=1e-6)
    assert section.get_float("field_float_invalid_1", defval=-3.14) == pytest.approx(-3.14, abs=1e-6)
    assert section.get_int("field_int_invalid_1", defval=999) == 999
    assert section.get_int("field_int_invalid_1", defval=-999) == -999
    assert section.get_uint("field_uint_invalid_1", defval=999) == 999
    assert section.get_uint("field_uint_invalid_1", defval=9999) == 9999
    assert section.get_bool("field_bool_invalid_1", defval=True) == True
    assert section.get_bool("field_bool_invalid_1", defval=False) == False

    # non-existent with defval
    assert section.get_string("field_string_unknown", defval="def_1") == "def_1"
    assert section.get_string("field_string_unknown", defval="def_2") == "def_2"
    assert section.get_float("field_float_unknown", defval=3.14) == pytest.approx(3.14, abs=1e-6)
    assert section.get_float("field_float_unknown", defval=-3.14) == pytest.approx(-3.14, abs=1e-6)
    assert section.get_int("field_int_unknown", defval=999) == 999
    assert section.get_int("field_int_unknown", defval=-999) == -999
    assert section.get_uint("field_uint_unknown", defval=999) == 999
    assert section.get_uint("field_uint_unknown", defval=9999) == 9999
    assert section.get_bool("field_bool_unknown", defval=True) == True
    assert section.get_bool("field_bool_unknown", defval=False) == False

    # invalid format OR no value
    with pytest.raises(Section.Error):
        _ = section.get_string("field_string_invalid_1")
    with pytest.raises(Section.Error):
        _ = section.get_float("field_float_invalid_1")
    with pytest.raises(Section.Error):
        _ = section.get_float("field_float_invalid_2")
    with pytest.raises(Section.Error):
        _ = section.get_float("field_float_invalid_3")
    with pytest.raises(Section.Error):
        _ = section.get_float("field_float_invalid_4")
    with pytest.raises(Section.Error):
        _ = section.get_int("field_int_invalid_1")
    with pytest.raises(Section.Error):
        _ = section.get_int("field_int_invalid_2")
    with pytest.raises(Section.Error):
        _ = section.get_int("field_int_invalid_3")
    with pytest.raises(Section.Error):
        _ = section.get_int("field_int_invalid_4")
    with pytest.raises(Section.Error):
        _ = section.get_uint("field_uint_invalid_1")
    with pytest.raises(Section.Error):
        _ = section.get_uint("field_uint_invalid_2")
    with pytest.raises(Section.Error):
        _ = section.get_uint("field_uint_invalid_3")
    with pytest.raises(Section.Error):
        _ = section.get_uint("field_uint_invalid_4")
    with pytest.raises(Section.Error):
        _ = section.get_uint("field_uint_invalid_5")
    with pytest.raises(Section.Error):
        _ = section.get_bool("field_bool_invalid_1")
    with pytest.raises(Section.Error):
        _ = section.get_bool("field_bool_invalid_2")
    with pytest.raises(Section.Error):
        _ = section.get_bool("field_bool_invalid_3")

    # non-existent
    with pytest.raises(Section.Error):
        _ = section.get_string("field_string_unknown")
    with pytest.raises(Section.Error):
        _ = section.get_float("field_float_unknown")
    with pytest.raises(Section.Error):
        _ = section.get_int("field_int_unknown")
    with pytest.raises(Section.Error):
        _ = section.get_uint("field_uint_unknown")
    with pytest.raises(Section.Error):
        _ = section.get_bool("field_bool_unknown")

def test_section_get_elems():
    section = Section(id="test")
    section.add("field_strings_valid_1", "")
    section.add("field_strings_valid_2", "123")
    section.add("field_strings_valid_3", "one,two, three,  four")
    section.add("field_strings_invalid_1", None)
    section.add("field_floats_valid_1", "")
    section.add("field_floats_valid_2", "1.1")
    section.add("field_floats_valid_3", "1.1, 2.22, 3.333")
    section.add("field_floats_invalid_1", None)
    section.add("field_floats_invalid_2", "1.1, zero, 3.3")
    section.add("field_ints_valid_1", "")
    section.add("field_ints_valid_2", "1")
    section.add("field_ints_valid_3", "-2,-1,0,1,2")
    section.add("field_ints_invalid_1", None)
    section.add("field_ints_invalid_2", "-2,-1,zero,1,2")
    section.add("field_uints_valid_1", "")
    section.add("field_uints_valid_2", "1")
    section.add("field_uints_valid_3", "0,1,2,3,4,5")
    section.add("field_uints_invalid_1", None)
    section.add("field_uints_invalid_2", "-2,-1,0,1,2")
    section.add("field_bools_valid_1", "")
    section.add("field_bools_valid_2", "on, yes, true, 1")
    section.add("field_bools_valid_3", "off, no, false, 0")
    section.add("field_bools_valid_4", "On, Off")
    section.add("field_bools_valid_5", "Yes, No")
    section.add("field_bools_valid_6", "True, False")
    section.add("field_bools_valid_7", "OFF, ON")
    section.add("field_bools_valid_8", "NO, YES")
    section.add("field_bools_valid_9", "FALSE, TRUE")
    section.add("field_bools_invalid_1", None)
    section.add("field_bools_invalid_2", "no, not")
    
    # valid format
    assert section.get_strings("field_strings_valid_1") == []
    assert section.get_strings("field_strings_valid_2") == ["123"]
    assert section.get_strings("field_strings_valid_3") == ["one", "two", "three", "four"]
    assert section.get_floats("field_floats_valid_1") == []
    assert section.get_floats("field_floats_valid_2") == pytest.approx([1.1], abs=1e-6)
    assert section.get_floats("field_floats_valid_3") == pytest.approx([1.1, 2.22, 3.333], abs=1e-6)
    assert section.get_ints("field_ints_valid_1") == []
    assert section.get_ints("field_ints_valid_2") == [1]
    assert section.get_ints("field_ints_valid_3") == [-2, -1, 0, 1, 2]
    assert section.get_uints("field_uints_valid_1") == []
    assert section.get_uints("field_uints_valid_2") == [1]
    assert section.get_uints("field_uints_valid_3") == [0, 1, 2, 3, 4, 5]
    assert section.get_bools("field_bools_valid_1") == []
    assert section.get_bools("field_bools_valid_2") == [True, True, True, True]
    assert section.get_bools("field_bools_valid_3") == [False, False, False, False]
    assert section.get_bools("field_bools_valid_4") == [True, False]
    assert section.get_bools("field_bools_valid_5") == [True, False]
    assert section.get_bools("field_bools_valid_6") == [True, False]
    assert section.get_bools("field_bools_valid_7") == [False, True]
    assert section.get_bools("field_bools_valid_8") == [False, True]
    assert section.get_bools("field_bools_valid_9") == [False, True]

    # no value AND not mandatory
    assert section.get_strings("field_strings_invalid_1", mandatory=False) == []
    assert section.get_floats("field_floats_invalid_1", mandatory=False) == []
    assert section.get_ints("field_ints_invalid_1", mandatory=False) == []
    assert section.get_uints("field_uints_invalid_1", mandatory=False) == []
    assert section.get_bools("field_bools_invalid_1", mandatory=False) == []

    # non-existent AND not mandatory
    assert section.get_strings("field_strings_unknown", mandatory=False) == []
    assert section.get_floats("field_floats_unknown", mandatory=False) == []
    assert section.get_ints("field_ints_unknown", mandatory=False) == []
    assert section.get_uints("field_uints_unknown", mandatory=False) == []
    assert section.get_bools("field_bools_unknown", mandatory=False) == []

    # invalid format OR no value
    with pytest.raises(Section.Error):
        _ = section.get_strings("field_strings_invalid_1")
    with pytest.raises(Section.Error):
        _ = section.get_floats("field_floats_invalid_1")
    with pytest.raises(Section.Error):
        _ = section.get_floats("field_floats_invalid_2")
    with pytest.raises(Section.Error):
        _ = section.get_ints("field_ints_invalid_1")
    with pytest.raises(Section.Error):
        _ = section.get_ints("field_ints_invalid_2")
    with pytest.raises(Section.Error):
        _ = section.get_uints("field_uints_invalid_1")
    with pytest.raises(Section.Error):
        _ = section.get_uints("field_uints_invalid_2")
    with pytest.raises(Section.Error):
        _ = section.get_bools("field_bools_invalid_1")
    with pytest.raises(Section.Error):
        _ = section.get_bools("field_bools_invalid_2")

    # non-existent
    with pytest.raises(Section.Error):
        _ = section.get_strings("field_strings_unknown")
    with pytest.raises(Section.Error):
        _ = section.get_floats("field_floats_unknown")
    with pytest.raises(Section.Error):
        _ = section.get_ints("field_ints_unknown")
    with pytest.raises(Section.Error):
        _ = section.get_uints("field_uints_unknown")
    with pytest.raises(Section.Error):
        _ = section.get_bools("field_bools_unknown")

def test_section_get_items():
    section = Section(id="test")
    section.add("items_valid_1", "")
    section.add("items_valid_2", "item")
    section.add("items_valid_3", "a,b,c")
    section.add("items_valid_4", "a,1, bb,2, ccc,3")
    section.add("items_valid_5", "aa,2,b,c,dddd,4,ee,2,f,ggg,3")
    section.add("items_valid_6", "1,2,3,4,5")
    section.add("items_valid_7", "-1,-2,-3,-4,-5")
    section.add("items_invalid_1", None)

    # valid format
    assert section.get_items("items_valid_1") == []
    assert section.get_items("items_valid_2") == [("item", 1)]
    assert section.get_items("items_valid_3") == [("a", 1), ("b", 1), ("c", 1)]
    assert section.get_items("items_valid_4") == [("a", 1), ("bb", 2), ("ccc", 3)]
    assert section.get_items("items_valid_5") == [("aa", 2), ("b", 1), ("c", 1), ("dddd", 4), ("ee", 2), ("f", 1), ("ggg", 3)]
    assert section.get_items("items_valid_6") == [("1", 2), ("3", 4), ("5", 1)]
    assert section.get_items("items_valid_7") == [("-1", -2), ("-3", -4), ("-5", 1)]

    # invalid format OR non-existent
    with pytest.raises(Section.Error):
        _ = section.get_items("items_invalid_1")
    with pytest.raises(Section.Error):
        _ = section.get_items("items_unknown")

    # invalid format OR non-existent AND not mandatory
    assert section.get_items("items_invalid_1", mandatory=False) == []
    assert section.get_items("items_unknown", mandatory=False) == []

def test_section_get_items_parsing_mode():
    section = Section(id="test")
    section.add("items_1", "")
    section.add("items_2", "medkit_army")
    section.add("items_3", "wpn_rg-6")
    section.add("items_4", "ammo_5.45x39_fmj")
    section.add("items_5", "config\\misc")
    section.add("items_6", "medkit_army, wpn_rg-6, ammo_5.45x39_fmj, config\\misc")
    section.add("items_7", "medkit_army,2, wpn_rg-6,1, ammo_5.45x39_fmj,30, config\\misc,-1")

    assert section.get_items("items_1", True, "comma") == []
    assert section.get_items("items_1", True, "vanilla") == []
    assert section.get_items("items_1", True, "vanilla_ext") == []

    assert section.get_items("items_2", True, "comma") == [("medkit_army", 1)]
    assert section.get_items("items_2", True, "vanilla") == [("medkit_army", 1)]
    assert section.get_items("items_2", True, "vanilla_ext") == [("medkit_army", 1)]

    assert section.get_items("items_3", True, "comma") == [("wpn_rg-6", 1)]
    assert section.get_items("items_3", True, "vanilla") == [("wpn_rg", 6)]
    assert section.get_items("items_3", True, "vanilla_ext") == [("wpn_rg-6", 1)]

    assert section.get_items("items_4", True, "comma") == [("ammo_5.45x39_fmj", 1)]
    assert section.get_items("items_4", True, "vanilla") == [("ammo_5", 1), ("45x39_fmj", 1)]
    assert section.get_items("items_4", True, "vanilla_ext") == [("ammo_5.45x39_fmj", 1)]

    assert section.get_items("items_5", True, "comma") == [("config\\misc", 1)]
    assert section.get_items("items_5", True, "vanilla") == [("config\\misc", 1)]
    assert section.get_items("items_5", True, "vanilla_ext") == [("config\\misc", 1)]

    assert section.get_items("items_6", True, "comma") == [
        ("medkit_army", 1), ("wpn_rg-6", 1), ("ammo_5.45x39_fmj", 1), ("config\\misc", 1)
    ]
    assert section.get_items("items_6", True, "vanilla") == [
        ("medkit_army", 1), ("wpn_rg", 6), ("ammo_5", 1), ("45x39_fmj", 1), ("config\\misc", 1)
    ]
    assert section.get_items("items_6", True, "vanilla_ext") == [
        ("medkit_army", 1), ("wpn_rg-6", 1), ("ammo_5.45x39_fmj", 1), ("config\\misc", 1)
    ]

    assert section.get_items("items_7", True, "comma") == [
        ("medkit_army", 2), ("wpn_rg-6", 1), ("ammo_5.45x39_fmj", 30), ("config\\misc", -1)
    ]
    assert section.get_items("items_7", True, "vanilla") == [
        ("medkit_army", 2), ("wpn_rg", 6), ("1", 1), ("ammo_5", 1), ("45x39_fmj", 30), ("config\\misc", 1)
    ]
    assert section.get_items("items_7", True, "vanilla_ext") == [
        ("medkit_army", 2), ("wpn_rg-6", 1), ("ammo_5.45x39_fmj", 30), ("config\\misc", 1)
    ]
    
def test_section_get_pair():
    section = Section(id="test")
    section.add("pair_str_1", "Hello, world!")
    section.add("pair_str_2", "One | Two")
    section.add("pair_float_1", "2.71828, 3.14159")
    section.add("pair_float_2", "-1.11 | 2.22")
    section.add("pair_int_1", "-10, 10")
    section.add("pair_int_2", "-111 | 111")
    section.add("pair_uint_1", "0, 10")
    section.add("pair_uint_2", "10 | 0")
    section.add("pair_bool_1", "False, True")
    section.add("pair_bool_2", "True | False")
    section.add("list_without_values", None)
    section.add("list_len_0", "")
    section.add("list_len_1", "1")
    section.add("list_len_3", "1,2,3")

    assert section.get_pair_str("pair_str_1") == ("Hello", "world!")
    assert section.get_pair_str("pair_str_2", sep="|") == ("One", "Two")
    assert section.get_pair_float("pair_float_1") == pytest.approx((2.71828, 3.14159), abs=1e-6)
    assert section.get_pair_float("pair_float_2", sep="|") == pytest.approx((-1.11, 2.22), abs=1e-6)
    assert section.get_pair_int("pair_int_1") == (-10, 10)
    assert section.get_pair_int("pair_int_2", sep="|") == (-111, 111)
    assert section.get_pair_uint("pair_uint_1") == (0, 10)
    assert section.get_pair_uint("pair_uint_2", sep="|") == (10, 0)
    assert section.get_pair_bool("pair_bool_1") == (False, True)
    assert section.get_pair_bool("pair_bool_2", sep="|") == (True, False)

    # Указанного поля нет или оно без значения
    with pytest.raises(Section.Error):
        _ = section.get_pair_str("unknown_field")
    with pytest.raises(Section.Error):
        _ = section.get_pair_str("list_without_values")
    
    # Размер списка не равен двум
    with pytest.raises(Section.Error):
        _ = section.get_pair_str("list_len_0")
    with pytest.raises(Section.Error):
        _ = section.get_pair_str("list_len_1")
    with pytest.raises(Section.Error):
        _ = section.get_pair_str("list_len_3")
    
    # Конвертация значения хотя бы одного элемента невозможна
    with pytest.raises(Section.Error):
        _ = section.get_pair_float("pair_str_1")
    with pytest.raises(Section.Error):
        _ = section.get_pair_uint("pair_int_1")
