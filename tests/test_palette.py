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

    def test_shorthand_hex(self):
        assert _parse_hex_color("#FFF") == (255, 255, 255)

    def test_too_long(self):
        assert _parse_hex_color("#FF88000") is None

    def test_invalid_characters(self):
        assert _parse_hex_color("#GGGGGG") is None

    def test_none_value(self):
        assert _parse_hex_color(None) is None


"""Palette tools (palette.py)."""
import json

from conftest import ok, run

from aseprite_mcp.tools import palette


def test_list_palette_presets():
    presets = json.loads(run(palette.list_palette_presets()))
    assert "dawnbringer16" in presets
    assert len(presets["gameboy"]) == 4


def test_apply_palette_preset(sprite):
    result = ok(run(palette.apply_palette_preset(sprite, "dawnbringer16")))
    assert "16 colors" in result


def test_apply_palette_preset_rejects_unknown(sprite):
    result = run(palette.apply_palette_preset(sprite, "nonsense"))
    assert result.startswith("Unknown preset")


def test_quantize_to_palette(sprite):
    result = ok(run(palette.quantize_to_palette(sprite)))
    assert "Quantized" in result


def test_generate_color_ramp():
    ramp = json.loads(run(palette.generate_color_ramp("#D04648", 5)))
    assert len(ramp) == 5
    assert all(c.startswith("#") and len(c) == 7 for c in ramp)


def test_color_mode_roundtrip(sprite):
    ok(run(palette.set_color_mode(sprite, "indexed")))
    ok(run(palette.set_color_mode(sprite, "rgb")))
