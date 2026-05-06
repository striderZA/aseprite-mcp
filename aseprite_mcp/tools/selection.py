import os
import json
from typing import Literal
from ..core.commands import AsepriteCommand, lua_escape, reject_traversal
from .. import mcp


_OPERATION_MAP = {
    "replace": "select",
    "add": "add",
    "subtract": "subtract",
    "intersect": "intersect",
}

SelectionOp = Literal["replace", "add", "subtract", "intersect"]


@mcp.tool()
async def select_rectangle(
    filename: str,
    x: int,
    y: int,
    width: int,
    height: int,
    operation: SelectionOp = "replace",
) -> str:
    """Select, add, subtract, or intersect a rectangular region.

    Args:
        filename: Name of the Aseprite file to modify
        x: Rectangle top-left x coordinate
        y: Rectangle top-left y coordinate
        width: Rectangle width
        height: Rectangle height
        operation: Selection operation: "replace", "add", "subtract", or "intersect"
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"
    if width <= 0 or height <= 0:
        return "Width and height must be > 0"

    lua_method = _OPERATION_MAP.get(operation)
    if not lua_method:
        return f"Invalid operation '{operation}'. Use: replace, add, subtract, or intersect"

    script = f"""
    local spr = app.activeSprite
    if not spr then return "No active sprite" end

    local sel = spr.selection
    sel:{lua_method}(Rectangle({x}, {y}, {width}, {height}))

    spr:saveAs(spr.filename)
    return "Selection rectangle applied"
    """

    success, output = AsepriteCommand.execute_lua_script(script, filename)
    if success:
        return f"Selection {operation} applied at ({x}, {y}, {width}x{height}) in {filename}"
    return f"Failed to apply selection: {output}"


@mcp.tool()
async def select_all(filename: str) -> str:
    """Select the entire canvas.

    Args:
        filename: Name of the Aseprite file to modify
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"

    script = """
    local spr = app.activeSprite
    if not spr then return "No active sprite" end

    app.transaction(function()
        local sel = spr.selection
        sel:selectAll()
    end)

    spr:saveAs(spr.filename)
    return "All selected"
    """

    success, output = AsepriteCommand.execute_lua_script(script, filename)
    if success:
        return f"All selected in {filename}"
    return f"Failed to select all: {output}"


@mcp.tool()
async def deselect(filename: str) -> str:
    """Deselect (clear) the current selection.

    Args:
        filename: Name of the Aseprite file to modify
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"

    script = """
    local spr = app.activeSprite
    if not spr then return "No active sprite" end

    app.transaction(function()
        local sel = spr.selection
        sel:deselect()
    end)

    spr:saveAs(spr.filename)
    return "Selection cleared"
    """

    success, output = AsepriteCommand.execute_lua_script(script, filename)
    if success:
        return f"Selection cleared in {filename}"
    return f"Failed to deselect: {output}"


@mcp.tool()
async def get_selection(filename: str) -> str:
    """Get the current selection state as JSON.

    Args:
        filename: Name of the Aseprite file to read
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"

    script = """
    local spr = app.activeSprite
    if not spr then return '{"error":"No active sprite"}' end

    local sel = spr.selection
    local parts = {}

    table.insert(parts, '{"isEmpty":')
    if sel.isEmpty then
        table.insert(parts, 'true')
    else
        table.insert(parts, 'false')
    end

    local b = sel.bounds
    if b then
        local bs = string.format(',"bounds":{"x":%d,"y":%d,"w":%d,"h":%d}', b.x, b.y, b.w, b.h)
        table.insert(parts, bs)
    else
        table.insert(parts, ',"bounds":null')
    end

    local o = sel.origin
    if o then
        local os = string.format(',"origin":{"x":%d,"y":%d}', o.x, o.y)
        table.insert(parts, os)
    else
        table.insert(parts, ',"origin":null')
    end

    table.insert(parts, '}')
    return table.concat(parts)
    """

    success, output = AsepriteCommand.execute_lua_script(script, filename)
    if not success:
        return json.dumps({"error": output})
    try:
        json.loads(output)
        return output
    except json.JSONDecodeError:
        return json.dumps({"error": "Failed to parse selection data"})


@mcp.tool()
async def move_selection(filename: str, dx: int, dy: int) -> str:
    """Move (shift) the selection origin by a delta.

    Args:
        filename: Name of the Aseprite file to modify
        dx: Horizontal shift in pixels
        dy: Vertical shift in pixels
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"

    script = f"""
    local spr = app.activeSprite
    if not spr then return "No active sprite" end

    app.transaction(function()
        local sel = spr.selection
        sel.origin = Point(sel.origin.x + {dx}, sel.origin.y + {dy})
    end)

    spr:saveAs(spr.filename)
    return "Selection moved"
    """

    success, output = AsepriteCommand.execute_lua_script(script, filename)
    if success:
        return f"Selection moved by ({dx}, {dy}) in {filename}"
    return f"Failed to move selection: {output}"
