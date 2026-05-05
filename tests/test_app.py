from aseprite_mcp.tools.app import _parse_hex_color


class TestParseHexColor:
    def test_valid_hex(self):
        assert _parse_hex_color("#FF0000") == (255, 0, 0)

    def test_valid_hex_lowercase(self):
        assert _parse_hex_color("#00ff00") == (0, 255, 0)

    def test_valid_hex_mixed_case(self):
        assert _parse_hex_color("#AaBbCc") == (170, 187, 204)

    def test_returns_none_for_empty(self):
        assert _parse_hex_color("") is None

    def test_returns_none_for_none(self):
        assert _parse_hex_color(None) is None

    def test_returns_none_for_short_hex(self):
        assert _parse_hex_color("#FFF") is None

    def test_returns_none_for_invalid_chars(self):
        assert _parse_hex_color("#GGGGGG") is None

    def test_accepts_hex_without_hash(self):
        assert _parse_hex_color("FF0000") == (255, 0, 0)

    def test_works_without_hash_prefix(self):
        assert _parse_hex_color("FF0000") == (255, 0, 0)

    def test_black(self):
        assert _parse_hex_color("#000000") == (0, 0, 0)

    def test_white(self):
        assert _parse_hex_color("#FFFFFF") == (255, 255, 255)
