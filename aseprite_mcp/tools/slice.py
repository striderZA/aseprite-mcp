import os
import json
from typing import Optional
from ..core.commands import AsepriteCommand, lua_escape, reject_traversal
from .. import mcp


def _parse_hex_color(value: str | None) -> tuple[int, int, int] | None:
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


def _format_slice_data(slices_output: str) -> str:
    if not slices_output or slices_output.strip() == "":
        return "[]"
    return slices_output


@mcp.tool()
async def create_slice(
    filename: str,
    name: str,
    x: int,
    y: int,
    width: int,
    height: int,
    color: str = "",
    data: str = "",
    center_x: Optional[int] = None,
    center_y: Optional[int] = None,
    center_width: Optional[int] = None,
    center_height: Optional[int] = None,
    pivot_x: Optional[float] = None,
    pivot_y: Optional[float] = None,
) -> str:
    """Create a new slice with the specified bounds and properties.

    Args:
        filename: Name of the Aseprite file to modify
        name: Slice name
        x: Slice bounds x coordinate
        y: Slice bounds y coordinate
        width: Slice bounds width
        height: Slice bounds height
        color: Hex color for timeline label (e.g. "#FF0000")
        data: User-defined data string attached to the slice
        center_x: 9-slice center rectangle x
        center_y: 9-slice center rectangle y
        center_width: 9-slice center rectangle width
        center_height: 9-slice center rectangle height
        pivot_x: Pivot point x coordinate
        pivot_y: Pivot point y coordinate
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"
    if width <= 0 or height <= 0:
        return "Width and height must be > 0"

    safe_name = lua_escape(name)
    safe_data = lua_escape(data)
    color_r, color_g, color_b = None, None, None
    if color:
        rgb = _parse_hex_color(color)
        if rgb is None:
            return f"Invalid color value: {color}"
        color_r, color_g, color_b = rgb

    center_lua = "nil"
    if all(v is not None for v in (center_x, center_y, center_width, center_height)):
        center_lua = f"Rectangle({center_x}, {center_y}, {center_width}, {center_height})"

    pivot_lua = "nil"
    if pivot_x is not None and pivot_y is not None:
        pivot_lua = f"Point({pivot_x}, {pivot_y})"

    color_line = ""
    if color_r is not None:
        color_line = f"    slice.color = Color({color_r}, {color_g}, {color_b})"

    data_line = ""
    if data:
        data_line = f'    slice.data = "{safe_data}"'

    script = f"""
    local spr = app.activeSprite
    if not spr then return "No active sprite" end

    app.transaction(function()
        if #spr.layers == 0 then return "No layers in sprite" end
        local slice = spr:newSlice(spr.layers[1], spr.frames[1], "{safe_name}", Rectangle({x}, {y}, {width}, {height}))
        slice.center = {center_lua}
        slice.pivot = {pivot_lua}
        {color_line}
        {data_line}
    end)

    spr:saveAs(spr.filename)
    return "Slice created"
    """

    success, output = AsepriteCommand.execute_lua_script(script, filename)
    if success:
        return f"Slice '{name}' created in {filename}"
    return f"Failed to create slice: {output}"


@mcp.tool()
async def delete_slice(filename: str, name: str) -> str:
    """Delete a slice by name.

    Args:
        filename: Name of the Aseprite file to modify
        name: Name of the slice to delete
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"

    safe_name = lua_escape(name)

    script = f"""
    local spr = app.activeSprite
    if not spr then return "No active sprite" end

    local found = false
    app.transaction(function()
        for i, s in ipairs(spr.slices) do
            if s.name == "{safe_name}" then
                spr:deleteSlice(s)
                found = true
                break
            end
        end
    end)

    if not found then return "Slice not found" end
    spr:saveAs(spr.filename)
    return "Slice deleted"
    """

    success, output = AsepriteCommand.execute_lua_script(script, filename)
    if success:
        return f"Slice '{name}' deleted from {filename}"
    return f"Failed to delete slice: {output}"


@mcp.tool()
async def get_slices(filename: str) -> str:
    """Return all slices as a JSON string with their properties.

    Args:
        filename: Name of the Aseprite file to read
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"

    script = """
    local spr = app.activeSprite
    if not spr then return "[]" end

    local function esc(str)
        if not str then return "" end
        return str:gsub('\\\\', '\\\\\\\\'):gsub('"', '\\\\"'):gsub('\\n', '\\\\n')
    end

    local parts = {}
    for i, s in ipairs(spr.slices) do
        local cr = s.color and s.color.red or 0
        local cg = s.color and s.color.green or 0
        local cb = s.color and s.color.blue or 0
        local center = "null"
        if s.center then
            center = string.format('{"x":%d,"y":%d,"w":%d,"h":%d}', s.center.x, s.center.y, s.center.w, s.center.h)
        end
        local pivot = "null"
        if s.pivot then
            pivot = string.format('{"x":%g,"y":%g}', s.pivot.x, s.pivot.y)
        end
        local sd = ""
        if s.data then sd = esc(s.data) end
        local entry = string.format(
            '{"name":"%s","bounds":{"x":%d,"y":%d,"w":%d,"h":%d},"center":%s,"pivot":%s,"color":"#%02X%02X%02X","data":"%s"}',
            esc(s.name), s.bounds.x, s.bounds.y, s.bounds.w, s.bounds.h,
            center, pivot, cr, cg, cb, sd
        )
        table.insert(parts, entry)
    end
    return "[" .. table.concat(parts, ",") .. "]"
    """

    success, output = AsepriteCommand.execute_lua_script(script, filename)
    if not success:
        return f"[]"
    slices = _format_slice_data(output)
    try:
        json.loads(slices)
        return slices
    except json.JSONDecodeError:
        return f"[{{\"error\": \"Failed to parse slice data\"}}]"


@mcp.tool()
async def set_slice_properties(
    filename: str,
    name: str,
    x: int = 0,
    y: int = 0,
    width: int = 0,
    height: int = 0,
    color: str = "",
    data: str = "",
    center_x: int = 0,
    center_y: int = 0,
    center_width: int = 0,
    center_height: int = 0,
    pivot_x: float = 0.0,
    pivot_y: float = 0.0,
) -> str:
    """Update properties of an existing slice.

    Args:
        filename: Name of the Aseprite file to modify
        name: Name of the slice to update
        x: New bounds x (requires width > 0)
        y: New bounds y (requires width > 0)
        width: New bounds width (set > 0 to update bounds)
        height: New bounds height (requires width > 0)
        color: New hex color for timeline label (e.g. "#FF0000")
        data: New user-defined data string
        center_x: New 9-slice center x (requires center_width > 0)
        center_y: New 9-slice center y (requires center_width > 0)
        center_width: New 9-slice center width (set > 0 to update center)
        center_height: New 9-slice center height (requires center_width > 0)
        pivot_x: New pivot x (requires pivot_y to also be set)
        pivot_y: New pivot y (requires pivot_x to also be set)
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"

    safe_name = lua_escape(name)
    safe_data = lua_escape(data)

    color_r, color_g, color_b = None, None, None
    if color:
        rgb = _parse_hex_color(color)
        if rgb is None:
            return f"Invalid color value: {color}"
        color_r, color_g, color_b = rgb

    bounds_line = ""
    if width > 0 and height > 0:
        bounds_line = f"    s.bounds = Rectangle({x}, {y}, {width}, {height})"

    center_line = ""
    if center_width > 0 and center_height > 0:
        center_line = f"    s.center = Rectangle({center_x}, {center_y}, {center_width}, {center_height})"

    pivot_line = ""
    if pivot_x != 0.0 or pivot_y != 0.0:
        pivot_line = f"    s.pivot = Point({pivot_x}, {pivot_y})"

    color_line = ""
    if color_r is not None:
        color_line = f"    s.color = Color({color_r}, {color_g}, {color_b})"

    data_line = ""
    if data:
        data_line = f'    s.data = "{safe_data}"'

    script = f"""
    local spr = app.activeSprite
    if not spr then return "No active sprite" end

    local found = false
    app.transaction(function()
        for i, s in ipairs(spr.slices) do
            if s.name == "{safe_name}" then
                {bounds_line}
                {center_line}
                {pivot_line}
                {color_line}
                {data_line}
                found = true
                break
            end
        end
    end)

    if not found then return "Slice not found" end
    spr:saveAs(spr.filename)
    return "Slice updated"
    """

    success, output = AsepriteCommand.execute_lua_script(script, filename)
    if success:
        return f"Slice '{name}' updated in {filename}"
    return f"Failed to update slice: {output}"
