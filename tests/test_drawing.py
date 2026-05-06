import pytest
from aseprite_mcp.tools.drawing import _parse_hex_color


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


class TestFilterTools:
    def test_flood_fill_at_import(self):
        from aseprite_mcp.tools.drawing import flood_fill_at
        assert callable(flood_fill_at)

    def test_replace_color_at_import(self):
        from aseprite_mcp.tools.drawing import replace_color_at
        assert callable(replace_color_at)

    def test_invert_colors_at_import(self):
        from aseprite_mcp.tools.drawing import invert_colors_at
        assert callable(invert_colors_at)

    def test_apply_noise_at_import(self):
        from aseprite_mcp.tools.drawing import apply_noise_at
        assert callable(apply_noise_at)

    def test_apply_despeckle_at_import(self):
        from aseprite_mcp.tools.drawing import apply_despeckle_at
        assert callable(apply_despeckle_at)

    def test_apply_sobel_at_import(self):
        from aseprite_mcp.tools.drawing import apply_sobel_at
        assert callable(apply_sobel_at)

    def test_apply_oil_at_import(self):
        from aseprite_mcp.tools.drawing import apply_oil_at
        assert callable(apply_oil_at)

    def test_apply_super_pixel_at_import(self):
        from aseprite_mcp.tools.drawing import apply_super_pixel_at
        assert callable(apply_super_pixel_at)

    def test_adjust_hsl_at_import(self):
        from aseprite_mcp.tools.drawing import adjust_hsl_at
        assert callable(adjust_hsl_at)