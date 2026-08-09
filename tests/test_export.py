from aseprite_mcp.tools.export import (
    _layout_to_lua,
    _data_format_to_lua,
    _LAYOUT_TYPES,
    _DATA_FORMATS,
)


class TestLayoutToLua:
    def test_horizontal(self):
        assert _layout_to_lua("horizontal") == "SpriteSheetType.HORIZONTAL"

    def test_vertical(self):
        assert _layout_to_lua("vertical") == "SpriteSheetType.VERTICAL"

    def test_rows(self):
        assert _layout_to_lua("rows") == "SpriteSheetType.ROWS"

    def test_columns(self):
        assert _layout_to_lua("columns") == "SpriteSheetType.COLUMNS"

    def test_packed(self):
        assert _layout_to_lua("packed") == "SpriteSheetType.PACKED"


class TestDataFormatToLua:
    def test_json_array(self):
        assert _data_format_to_lua("json_array") == "SpriteSheetDataFormat.JSON_ARRAY"

    def test_json_hash(self):
        assert _data_format_to_lua("json_hash") == "SpriteSheetDataFormat.JSON_HASH"


class TestConstants:
    def test_layout_types(self):
        assert _LAYOUT_TYPES == {"horizontal", "vertical", "rows", "columns", "packed"}

    def test_data_formats(self):
        assert _DATA_FORMATS == {"json_array", "json_hash"}


"""Export and import tools (export.py)."""
import os
import struct

from conftest import BASE, ok, run

from aseprite_mcp.tools import animation, export


def png_size(path):
    with open(path, "rb") as f:
        data = f.read(24)
    return struct.unpack(">II", data[16:24])


def test_export_frame_scaled(sprite):
    out = f"{BASE}/frame1.png"
    ok(run(export.export_frame(sprite, 1, out, 8)))
    assert png_size(out) == (256, 256)


def test_export_spritesheet_with_data(sprite):
    ok(run(animation.add_frames(sprite, 3, 100)))
    out = f"{BASE}/sheet.png"
    data = f"{BASE}/sheet.json"
    ok(run(export.export_spritesheet(sprite, out, "horizontal", data, 2, 1)))
    assert os.path.exists(out) and os.path.exists(data)


def test_export_spritesheet_tag_filter(sprite):
    ok(run(animation.set_tag(sprite, "clip", 1, 2, "forward")))
    out = f"{BASE}/sheet_tag.png"
    ok(run(export.export_spritesheet(sprite, out, "horizontal", "", 1, 0, "clip")))
    w, h = png_size(out)
    assert (w, h) == (64, 32), "tag filter must export only the 2 tagged frames"


def test_export_layers(sprite):
    result = ok(run(export.export_layers(sprite, f"{BASE}/layers")))
    assert ".png" in result


def test_export_tag_gif(sprite):
    out = f"{BASE}/clip.gif"
    ok(run(export.export_tag(sprite, "clip", out, 4)))
    assert os.path.exists(out)


def test_import_image_as_layer(sprite):
    ok(run(export.import_image_as_layer(sprite, f"{BASE}/frame1.png", "ref", 1, 0, 0)))
