"""Tests for the aseprite_mcp.tools.tileset module."""


class TestModuleImports:
    def test_module_importable(self):
        from aseprite_mcp.tools import tileset
        assert tileset is not None

    def test_tools_are_async_functions(self):
        from aseprite_mcp.tools.tileset import (
            create_tileset,
            delete_tileset,
            get_tilesets,
            get_tilemap_layers,
        )
        import asyncio
        assert asyncio.iscoroutinefunction(create_tileset)
        assert asyncio.iscoroutinefunction(delete_tileset)
        assert asyncio.iscoroutinefunction(get_tilesets)
        assert asyncio.iscoroutinefunction(get_tilemap_layers)
