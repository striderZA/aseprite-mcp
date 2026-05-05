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
