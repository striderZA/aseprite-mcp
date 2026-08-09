import os
from ..core.commands import AsepriteCommand, lua_escape, reject_traversal
from .. import mcp


def _color_space_to_lua(name: str) -> str | None:
    mapping = {
        "srgb": "ColorSpace{sRGB=true}",
        "linear": "ColorSpace{linear=true}",
    }
    return mapping.get(name.lower())


@mcp.tool()
async def save_copy_as(filename: str, output_path: str) -> str:
    """Save a copy of the sprite without marking the original as saved.

    Args:
        filename: Path to the .aseprite file
        output_path: Destination path for the copy
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"

    err = reject_traversal(output_path)
    if err:
        return err

    safe_output = lua_escape(output_path.replace("\\", "/"))
    script = f"""
    local spr = app.activeSprite
    if not spr then return "No active sprite" end

    local ok, msg = pcall(function()
        spr:saveCopyAs("{safe_output}")
    end)
    if not ok then return "Failed to save copy: " .. tostring(msg) end

    return "Copy saved"
    """

    success, output = AsepriteCommand.execute_lua_script(script, filename)
    if success:
        return f"Copy saved to {output_path}"
    return f"Failed to save copy: {output}"


@mcp.tool()
async def close_sprite(filename: str) -> str:
    """Close the sprite without saving. WARNING: This is destructive -- all unsaved changes will be lost.

    Args:
        filename: Path to the .aseprite file to close
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"

    script = """
    local spr = app.activeSprite
    if not spr then return "No active sprite" end

    spr:close()
    return "Sprite closed"
    """

    success, output = AsepriteCommand.execute_lua_script(script, filename)
    if success:
        return f"Sprite {filename} closed"
    return f"Failed to close sprite: {output}"


@mcp.tool()
async def load_sprite_palette(filename: str, palette_path: str) -> str:
    """Load a palette from file and apply it to the sprite.

    Args:
        filename: Path to the .aseprite file
        palette_path: Path to the palette file (.gpl, .hex, .pal)
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"

    err = reject_traversal(palette_path)
    if err:
        return err

    safe_palette = lua_escape(palette_path.replace("\\", "/"))
    script = f"""
    local spr = app.activeSprite
    if not spr then return "No active sprite" end

    local ok, msg = pcall(function()
        spr:loadPalette("{safe_palette}")
    end)
    if not ok then return "Failed to load palette: " .. tostring(msg) end

    return "Palette loaded"
    """

    success, output = AsepriteCommand.execute_lua_script(script, filename)
    if success:
        return f"Palette loaded from {palette_path} into {filename}"
    return f"Failed to load palette: {output}"


@mcp.tool()
async def convert_color_space(filename: str, color_space_name: str) -> str:
    """Convert the sprite's pixels to a different color space.

    Args:
        filename: Path to the .aseprite file
        color_space_name: Target color space ("sRGB", "linear")
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"

    cs_lua = _color_space_to_lua(color_space_name)
    if not cs_lua:
        return f"Unsupported color space: {color_space_name}. Supported: sRGB, linear"

    script = f"""
    local spr = app.activeSprite
    if not spr then return "No active sprite" end

    local cs = {cs_lua}
    local ok, msg = pcall(function()
        spr:convertColorSpace(cs)
    end)
    if not ok then return "Color space conversion failed: " .. tostring(msg) end

    spr:saveAs(spr.filename)
    return "Color space converted"
    """

    success, output = AsepriteCommand.execute_lua_script(script, filename)
    if success:
        return f"Color space converted to {color_space_name} in {filename}"
    return f"Failed to convert color space: {output}"
