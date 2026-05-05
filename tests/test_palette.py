import pytest
from aseprite_mcp.tools.palette import _parse_hex_color


class TestParseHexColor:
    def test_valid_full_hex(self):
        assert _parse_hex_color("#FF8800") == (255, 136, 0)

    def test_valid_without_hash(self):
        assert _parse_hex_color("FF8800") == (255, 136, 0)

    def test_black(self):
        assert _parse_hex_color("#000000") == (0, 0, 0)

    def test_white(self):
        assert _parse_hex_color("#FFFFFF") == (255, 255, 255)

    def test_lowercase(self):
        assert _parse_hex_color("#aabbcc") == (170, 187, 204)

    def test_empty_string(self):
        assert _parse_hex_color("") is None

    def test_too_short(self):
        assert _parse_hex_color("#FFF") is None

    def test_too_long(self):
        assert _parse_hex_color("#FF88000") is None

    def test_invalid_characters(self):
        assert _parse_hex_color("#GGGGGG") is None

    def test_none_value(self):
        assert _parse_hex_color(None) is None
