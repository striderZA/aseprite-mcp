import os
import json
from ..core.commands import AsepriteCommand, lua_escape, reject_traversal
from .. import mcp


def _parse_hex_color(value: str) -> tuple[int, int, int] | None:
    if not value:
        return None
    hex_color = value.lstrip("#")
    if len(hex_color) != 6:
        return None
    try:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
    except ValueError:
        return None
    return r, g, b


@mcp.tool()
async def undo_sprite(filename: str) -> str:
    """Undo the last action on a sprite.

    Note: In batch mode, app.undo() is not available, so we use
    app.command.Undo{ui=false} instead. This may have limited
    functionality compared to interactive use.

    Args:
        filename: Name of the Aseprite file to undo on
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"

    script = """
    local spr = app.activeSprite
    if not spr then return "No active sprite" end

    app.command.Undo{ui=false}
    spr:saveAs(spr.filename)
    return "Undo completed"
    """

    success, output = AsepriteCommand.execute_lua_script(script, filename)

    if success:
        return f"Undo completed on {filename}"
    else:
        return f"Failed to undo: {output}"


@mcp.tool()
async def set_fg_color(filename: str, color_hex: str) -> str:
    """Set the foreground color.

    Args:
        filename: Name of the Aseprite file to open
        color_hex: Hex color code like "#FF0000"
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"

    rgb = _parse_hex_color(color_hex)
    if rgb is None:
        return f"Invalid color value: {color_hex}"
    r, g, b = rgb

    script = f"""
    local spr = app.activeSprite
    if not spr then return "No active sprite" end

    app.fgColor = Color({r}, {g}, {b}, 255)
    spr:saveAs(spr.filename)
    return "Foreground color set"
    """

    success, output = AsepriteCommand.execute_lua_script(script, filename)

    if success:
        return f"Foreground color set to {color_hex} in {filename}"
    else:
        return f"Failed to set foreground color: {output}"


@mcp.tool()
async def set_bg_color(filename: str, color_hex: str) -> str:
    """Set the background color.

    Args:
        filename: Name of the Aseprite file to open
        color_hex: Hex color code like "#FF0000"
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"

    rgb = _parse_hex_color(color_hex)
    if rgb is None:
        return f"Invalid color value: {color_hex}"
    r, g, b = rgb

    script = f"""
    local spr = app.activeSprite
    if not spr then return "No active sprite" end

    app.bgColor = Color({r}, {g}, {b}, 255)
    spr:saveAs(spr.filename)
    return "Background color set"
    """

    success, output = AsepriteCommand.execute_lua_script(script, filename)

    if success:
        return f"Background color set to {color_hex} in {filename}"
    else:
        return f"Failed to set background color: {output}"


@mcp.tool()
async def get_app_version() -> str:
    """Return the Aseprite version (major.minor.patch) as a JSON string.

    No filename needed — this queries the Aseprite engine directly.
    """
    script = """
    local v = app.version
    print(string.format('{"major":%d,"minor":%d,"patch":%d}', v.major, v.minor, v.patch))
    """

    success, output = AsepriteCommand.execute_lua_script(script)

    if success:
        return output.strip()
    else:
        return f"Failed to get app version: {output}"


@mcp.tool()
async def open_sprite(filepath: str) -> str:
    """Open an Aseprite file using Sprite{ fromFile=... }.

    Note: In batch mode, opening a file via script does not display
    a UI window. The file is loaded into memory for script access.

    Args:
        filepath: Path to the Aseprite file to open
    """
    if not os.path.exists(filepath):
        return f"File {filepath} not found"
    err = reject_traversal(filepath)
    if err:
        return err

    safe_path = lua_escape(filepath.replace("\\", "/"))

    script = f"""
    local spr = Sprite{{ fromFile="{safe_path}" }}
    if not spr then return "Failed to open sprite" end
    return "Sprite opened successfully"
    """

    success, output = AsepriteCommand.execute_lua_script(script)

    if success:
        return f"Sprite opened successfully: {filepath}"
    else:
        return f"Failed to open sprite: {output}"
