import os
import json
from typing import Literal
from ..core.commands import AsepriteCommand, lua_escape, reject_traversal
from ..core.lua import FIND_LAYER, NORMALIZE_CEL, PSET
from ..core.colors import parse_hex_color
from .. import mcp


def _parse_hex_color(value: str) -> tuple[int, int, int] | None:
    """RGB-only parse (alpha dropped); unified via core.colors.parse_hex_color."""
    rgba = parse_hex_color(value)
    return rgba[:3] if rgba else None


_OPERATION_MAP = {
    "replace": "select",
    "add": "add",
    "subtract": "subtract",
    "intersect": "intersect",
}

SelectionOp = Literal["replace", "add", "subtract", "intersect"]


@mcp.tool()
async def move_region(
    filename: str,
    layer_name: str,
    frame_index: int,
    x: int,
    y: int,
    width: int,
    height: int,
    dest_x: int,
    dest_y: int,
) -> str:
    """Cut a rectangular region of pixels and paste it at a new position.

    Coordinates are sprite-global. The source area is left transparent.
    Pixels moved outside the canvas are discarded. Fully transparent
    source pixels do not overwrite destination pixels.

    Args:
        filename: Aseprite file to modify
        layer_name: Layer to operate on
        frame_index: Frame index starting at 1
        x: Left edge of the source region
        y: Top edge of the source region
        width: Region width
        height: Region height
        dest_x: New left edge for the region
        dest_y: New top edge for the region
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"
    if width <= 0 or height <= 0:
        return "Width and height must be > 0"

    safe_layer = lua_escape(layer_name)
    script = f"""
    {FIND_LAYER}
    {NORMALIZE_CEL}
    {PSET}
    local spr = app.activeSprite
    if not spr then print("ERROR:No active sprite") return end

    local idx = {frame_index}
    if idx < 1 or idx > #spr.frames then print("ERROR:Frame index out of range") return end

    local target = find_layer(spr, "{safe_layer}")
    if not target then print("ERROR:Layer not found") return end

    app.transaction(function()
        local cel = normalize_cel(spr, target, spr.frames[idx], false)
        if not cel then print("ERROR:No cel at that layer/frame") return end
        local img = cel.image

        local buf = {{}}
        for ry = 0, {height} - 1 do
            buf[ry] = {{}}
            for rx = 0, {width} - 1 do
                local sx = {x} + rx
                local sy = {y} + ry
                if sx >= 0 and sy >= 0 and sx < img.width and sy < img.height then
                    buf[ry][rx] = img:getPixel(sx, sy)
                    img:putPixel(sx, sy, 0)
                else
                    buf[ry][rx] = 0
                end
            end
        end

        for ry = 0, {height} - 1 do
            for rx = 0, {width} - 1 do
                local v = buf[ry][rx]
                if app.pixelColor.rgbaA(v) > 0 then
                    pset(img, {dest_x} + rx, {dest_y} + ry, v)
                end
            end
        end
    end)

    spr:saveAs(spr.filename)
    print("OK")
    """

    success, output = AsepriteCommand.execute_lua_script_checked(script, filename)
    if success:
        return (
            f"Moved {width}x{height} region from ({x},{y}) to ({dest_x},{dest_y}) "
            f"on '{layer_name}' frame {frame_index} in {filename}"
        )
    return f"Failed to move region: {output}"


@mcp.tool()
async def copy_region(
    filename: str,
    layer_name: str,
    frame_index: int,
    x: int,
    y: int,
    width: int,
    height: int,
    dest_x: int,
    dest_y: int,
    target_layer_name: str = "",
    target_frame_index: int = 0,
) -> str:
    """Copy a rectangular region of pixels to another position, layer, or frame.

    Coordinates are sprite-global. Fully transparent source pixels do not
    overwrite destination pixels. The destination cel is created when missing.

    Args:
        filename: Aseprite file to modify
        layer_name: Source layer
        frame_index: Source frame index starting at 1
        x: Left edge of the source region
        y: Top edge of the source region
        width: Region width
        height: Region height
        dest_x: Left edge of the destination
        dest_y: Top edge of the destination
        target_layer_name: Destination layer (default: same as source)
        target_frame_index: Destination frame (default: same as source)
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"
    if width <= 0 or height <= 0:
        return "Width and height must be > 0"

    safe_layer = lua_escape(layer_name)
    safe_target_layer = lua_escape(target_layer_name or layer_name)
    target_frame = target_frame_index if target_frame_index >= 1 else frame_index

    script = f"""
    {FIND_LAYER}
    {NORMALIZE_CEL}
    {PSET}
    local spr = app.activeSprite
    if not spr then print("ERROR:No active sprite") return end

    local src_idx = {frame_index}
    local dst_idx = {target_frame}
    if src_idx < 1 or src_idx > #spr.frames then print("ERROR:Source frame index out of range") return end
    if dst_idx < 1 or dst_idx > #spr.frames then print("ERROR:Target frame index out of range") return end

    local src_layer = find_layer(spr, "{safe_layer}")
    if not src_layer then print("ERROR:Source layer not found") return end
    local dst_layer = find_layer(spr, "{safe_target_layer}")
    if not dst_layer then print("ERROR:Target layer not found") return end

    app.transaction(function()
        local src_cel = normalize_cel(spr, src_layer, spr.frames[src_idx], false)
        if not src_cel then print("ERROR:No cel at source layer/frame") return end
        local src_img = src_cel.image

        local buf = {{}}
        for ry = 0, {height} - 1 do
            buf[ry] = {{}}
            for rx = 0, {width} - 1 do
                local sx = {x} + rx
                local sy = {y} + ry
                if sx >= 0 and sy >= 0 and sx < src_img.width and sy < src_img.height then
                    buf[ry][rx] = src_img:getPixel(sx, sy)
                else
                    buf[ry][rx] = 0
                end
            end
        end

        local dst_cel = normalize_cel(spr, dst_layer, spr.frames[dst_idx], true)
        local dst_img = dst_cel.image
        for ry = 0, {height} - 1 do
            for rx = 0, {width} - 1 do
                local v = buf[ry][rx]
                if app.pixelColor.rgbaA(v) > 0 then
                    pset(dst_img, {dest_x} + rx, {dest_y} + ry, v)
                end
            end
        end
    end)

    spr:saveAs(spr.filename)
    print("OK")
    """

    success, output = AsepriteCommand.execute_lua_script_checked(script, filename)
    if success:
        return (
            f"Copied {width}x{height} region from ({x},{y}) to ({dest_x},{dest_y}) "
            f"in {filename}"
        )
    return f"Failed to copy region: {output}"


@mcp.tool()
async def erase_region(
    filename: str,
    layer_name: str,
    frame_index: int,
    x: int,
    y: int,
    width: int,
    height: int,
) -> str:
    """Erase (make transparent) a rectangular region of pixels.

    Coordinates are sprite-global.

    Args:
        filename: Aseprite file to modify
        layer_name: Layer to operate on
        frame_index: Frame index starting at 1
        x: Left edge of the region
        y: Top edge of the region
        width: Region width
        height: Region height
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"
    if width <= 0 or height <= 0:
        return "Width and height must be > 0"

    safe_layer = lua_escape(layer_name)
    script = f"""
    {FIND_LAYER}
    {NORMALIZE_CEL}
    local spr = app.activeSprite
    if not spr then print("ERROR:No active sprite") return end

    local idx = {frame_index}
    if idx < 1 or idx > #spr.frames then print("ERROR:Frame index out of range") return end

    local target = find_layer(spr, "{safe_layer}")
    if not target then print("ERROR:Layer not found") return end

    app.transaction(function()
        local cel = normalize_cel(spr, target, spr.frames[idx], false)
        if not cel then print("ERROR:No cel at that layer/frame") return end
        local img = cel.image
        for py = math.max(0, {y}), math.min(img.height - 1, {y} + {height} - 1) do
            for px = math.max(0, {x}), math.min(img.width - 1, {x} + {width} - 1) do
                img:putPixel(px, py, 0)
            end
        end
    end)

    spr:saveAs(spr.filename)
    print("OK")
    """

    success, output = AsepriteCommand.execute_lua_script_checked(script, filename)
    if success:
        return (
            f"Erased {width}x{height} region at ({x},{y}) on '{layer_name}' "
            f"frame {frame_index} in {filename}"
        )
    return f"Failed to erase region: {output}"


@mcp.tool()
async def erase_color(
    filename: str,
    layer_name: str,
    frame_index: int,
    color: str,
    tolerance: int = 0,
) -> str:
    """Make all pixels of a given color transparent (like a magic eraser).

    Args:
        filename: Aseprite file to modify
        layer_name: Layer to operate on
        frame_index: Frame index starting at 1
        color: Hex color to erase, e.g. "#FF00FF"
        tolerance: Per-channel tolerance 0-255 (default 0 = exact match)
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"

    rgb = _parse_hex_color(color)
    if rgb is None:
        return f"Invalid color value: {color}"
    r, g, b = rgb
    if tolerance < 0 or tolerance > 255:
        return "Tolerance must be between 0 and 255"

    safe_layer = lua_escape(layer_name)
    script = f"""
    {FIND_LAYER}
    local spr = app.activeSprite
    if not spr then print("ERROR:No active sprite") return end

    local idx = {frame_index}
    if idx < 1 or idx > #spr.frames then print("ERROR:Frame index out of range") return end

    local target = find_layer(spr, "{safe_layer}")
    if not target then print("ERROR:Layer not found") return end

    local cel = target:cel(spr.frames[idx])
    if not cel then print("ERROR:No cel at that layer/frame") return end

    local count = 0
    app.transaction(function()
        local img = cel.image
        for py = 0, img.height - 1 do
            for px = 0, img.width - 1 do
                local v = img:getPixel(px, py)
                if app.pixelColor.rgbaA(v) > 0 then
                    local dr = math.abs(app.pixelColor.rgbaR(v) - {r})
                    local dg = math.abs(app.pixelColor.rgbaG(v) - {g})
                    local db = math.abs(app.pixelColor.rgbaB(v) - {b})
                    if dr <= {tolerance} and dg <= {tolerance} and db <= {tolerance} then
                        img:putPixel(px, py, 0)
                        count = count + 1
                    end
                end
            end
        end
    end)

    spr:saveAs(spr.filename)
    print("COUNT:" .. count)
    """

    success, output = AsepriteCommand.execute_lua_script_checked(script, filename)
    if not success:
        return f"Failed to erase color: {output}"

    count = "?"
    for line in output.splitlines():
        if line.startswith("COUNT:"):
            count = line[len("COUNT:"):]
    return (
        f"Erased {count} pixels of {color} on '{layer_name}' "
        f"frame {frame_index} in {filename}"
    )

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
    if not spr then print('{"error":"No active sprite"}') return end

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
    print(table.concat(parts))
    """

    success, output = AsepriteCommand.execute_lua_script(script, filename)
    if not success:
        return json.dumps({"error": output})
    output = output.strip()
    if not output:
        return json.dumps({"isEmpty": True, "bounds": None, "origin": None})
    try:
        json.loads(output)
        return output
    except json.JSONDecodeError:
        return json.dumps({"error": "Failed to parse selection data", "raw": output})


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
