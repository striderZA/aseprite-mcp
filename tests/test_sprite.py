"""Tests for the aseprite_mcp.tools.sprite module."""


class TestModuleImports:
    def test_module_importable(self):
        from aseprite_mcp.tools import sprite
        assert sprite is not None

    def test_tools_are_async_functions(self):
        from aseprite_mcp.tools.sprite import (
            save_copy_as,
            close_sprite,
            load_sprite_palette,
            convert_color_space,
            import_image_as_layer,
        )
        import asyncio
        assert asyncio.iscoroutinefunction(save_copy_as)
        assert asyncio.iscoroutinefunction(close_sprite)
        assert asyncio.iscoroutinefunction(load_sprite_palette)
        assert asyncio.iscoroutinefunction(convert_color_space)
        assert asyncio.iscoroutinefunction(import_image_as_layer)
