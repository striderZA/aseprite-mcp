import os
from typing import List
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
async def get_palette(filename: str) -> str:
    """Get the active sprite palette as a JSON array of hex colors."""
    if not os.path.exists(filename):
        return f"File {filename} not found"

    script = """
    local spr = app.activeSprite
    if not spr then print("No active sprite") return end

    local ok, pal = pcall(function() return spr.palettes[1] end)
    if not ok or not pal then print("No palette") return end

    local parts = {}
    local size = #pal
    table.insert(parts, "[")
    for i = 0, size - 1 do
        local c = pal:getColor(i)
        local hex = string.format("#%02X%02X%02X", c.red, c.green, c.blue)
        table.insert(parts, "\\"" .. hex .. "\\"")
        if i < size - 1 then
            table.insert(parts, ",")
        end
    end
    table.insert(parts, "]")
    print(table.concat(parts))
    """

    success, output = AsepriteCommand.execute_lua_script(script, filename)
    if success:
        return output
    return f"Failed to get palette: {output}"

@mcp.tool()
async def set_palette(filename: str, colors: List[str]) -> str:
    """Set the active sprite palette using a list of hex colors."""
    if not os.path.exists(filename):
        return f"File {filename} not found"
    if not colors:
        return "Colors list cannot be empty"

    rgb_list = []
    for color in colors:
        rgb = _parse_hex_color(color)
        if rgb is None:
            return "Colors must use #RRGGBB values"
        rgb_list.append(rgb)

    palette_entries = "\n".join(
        [f"    pal:setColor({i}, Color({r}, {g}, {b}))" for i, (r, g, b) in enumerate(rgb_list)]
    )

    script = f"""
    local spr = app.activeSprite
    if not spr then return "No active sprite" end

    local pal = Palette({len(rgb_list)})
{palette_entries}
    spr:setPalette(pal)
    spr:saveAs(spr.filename)
    return "Palette set"
    """

    success, output = AsepriteCommand.execute_lua_script(script, filename)
    if success:
        return f"Palette set with {len(colors)} colors in {filename}"
    return f"Failed to set palette: {output}"

@mcp.tool()
async def remap_colors_in_cel_range(
    filename: str,
    layer_name: str,
    start_frame: int,
    end_frame: int,
    mappings: List[dict],
    create_missing_cels: bool = False,
    source_frame_index: int | None = None
) -> str:
    """Remap colors in a layer across a frame range using explicit mappings."""
    if not os.path.exists(filename):
        return f"File {filename} not found"
    if not mappings:
        return "Mappings list cannot be empty"

    parsed = []
    for m in mappings:
        src = _parse_hex_color(m.get("from") or "")
        dst = _parse_hex_color(m.get("to") or "")
        if src is None or dst is None:
            return "Mappings must use #RRGGBB colors"
        sr, sg, sb = src
        dr, dg, db = dst
        parsed.append((sr, sg, sb, dr, dg, db))

    mapping_lua = ", ".join(
        [f"{{{sr},{sg},{sb},{dr},{dg},{db}}}" for sr, sg, sb, dr, dg, db in parsed]
    )
    create_flag = "true" if create_missing_cels else "false"
    source_idx = "nil" if source_frame_index is None else str(source_frame_index)
    safe_layer_name = lua_escape(layer_name)

    script = f"""
    local spr = app.activeSprite
    if not spr then return "No active sprite" end

    local start_idx = {start_frame}
    local end_idx = {end_frame}
    if start_idx < 1 or end_idx > #spr.frames or start_idx > end_idx then
        return "Frame range out of bounds"
    end

    local target = nil
    for _, layer in ipairs(spr.layers) do
        if layer.name == "{safe_layer_name}" then target = layer break end
    end
    if not target then return "Layer not found" end

    local source_frame = {source_idx}
    if source_frame == nil then
        source_frame = start_idx
    end
    if source_frame < 1 or source_frame > #spr.frames then
        return "Source frame out of range"
    end

    local map = {{ {mapping_lua} }}

    app.transaction(function()
        for fi = start_idx, end_idx do
            local frame = spr.frames[fi]
            local cel = target:cel(frame)
            if not cel and {create_flag} then
                local source_cel = target:cel(spr.frames[source_frame])
                if source_cel then
                    local img = source_cel.image:clone()
                    cel = spr:newCel(target, frame, img, source_cel.position)
                else
                    local img = Image(spr.width, spr.height, spr.colorMode)
                    cel = spr:newCel(target, frame, img, Point(0, 0))
                end
            end
            if cel then
                local img = cel.image
                for y = 0, img.height - 1 do
                    for x = 0, img.width - 1 do
                        local c = img:getPixel(x, y)
                        local r = app.pixelColor.rgbaR(c)
                        local g = app.pixelColor.rgbaG(c)
                        local b = app.pixelColor.rgbaB(c)
                        local a = app.pixelColor.rgbaA(c)
                        if a > 0 then
                            for _, m in ipairs(map) do
                                if r == m[1] and g == m[2] and b == m[3] then
                                    local nc = app.pixelColor.rgba(m[4], m[5], m[6], a)
                                    img:putPixel(x, y, nc)
                                    break
                                end
                            end
                        end
                    end
                end
            end
        end
    end)

    spr:saveAs(spr.filename)
    return "Colors remapped"
    """

    success, output = AsepriteCommand.execute_lua_script(script, filename)
    if success:
        return (
            f"Remapped colors on '{layer_name}' frames {start_frame}-{end_frame} in {filename}"
        )
    return f"Failed to remap colors: {output}"


@mcp.tool()
async def save_palette_to_file(filename: str, output_path: str) -> str:
    """Save the active sprite palette to a file (e.g. .gpl, .hex, .pal).

    Args:
        filename: Path to the .aseprite file
        output_path: Destination path for the palette file
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"

    err = reject_traversal(output_path)
    if err:
        return err

    script = f"""
    local spr = app.activeSprite
    if not spr then return "No active sprite" end

    local ok, pal = pcall(function() return spr.palettes[1] end)
    if not ok or not pal then return "No palette" end

    local save_ok, save_msg = pcall(function()
        pal:saveAs("{lua_escape(output_path)}")
    end)
    if not save_ok then return "Failed to save palette: " .. tostring(save_msg) end

    return "Palette saved"
    """

    success, output = AsepriteCommand.execute_lua_script(script, filename)
    if success:
        return f"Palette saved to {output_path}"
    return f"Failed to save palette: {output}"


@mcp.tool()
async def resize_palette(filename: str, count: int) -> str:
    """Resize the active sprite palette to the specified number of entries.

    Args:
        filename: Path to the .aseprite file
        count: Desired number of palette entries (must be at least 1)
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"
    if count < 1:
        return "Palette count must be at least 1"

    script = f"""
    local spr = app.activeSprite
    if not spr then return "No active sprite" end

    local ok, pal = pcall(function() return spr.palettes[1] end)
    if not ok or not pal then return "No palette" end

    pal:resize({count})
    spr:setPalette(pal)
    spr:saveAs(spr.filename)
    return "Palette resized"
    """

    success, output = AsepriteCommand.execute_lua_script(script, filename)
    if success:
        return f"Palette resized to {count} entries in {filename}"
    return f"Failed to resize palette: {output}"


@mcp.tool()
async def find_palette_color(filename: str, color_hex: str) -> str:
    """Find the palette index of a hex color using exact or best-match lookup.

    Args:
        filename: Path to the .aseprite file
        color_hex: Hex color string (e.g. "#FF8800")
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"
    rgb = _parse_hex_color(color_hex)
    if rgb is None:
        return "Color must use #RRGGBB format"
    r, g, b = rgb

    script = f"""
    local spr = app.activeSprite
    if not spr then return '{{"error":"No active sprite"}}' end

    local ok, pal = pcall(function() return spr.palettes[1] end)
    if not ok or not pal then return '{{"error":"No palette"}}' end

    local target = Color({r}, {g}, {b})

    local exact = pal:findExactMatch(target)
    if exact then
        return '{{"index":' .. exact .. ',"match":"exact"}}'
    end

    local best = pal:findBestMatch(target)
    if best then
        return '{{"index":' .. best .. ',"match":"best"}}'
    end

    return '{{"error":"No match found"}}'
    """

    success, output = AsepriteCommand.execute_lua_script(script, filename)
    if success:
        return output
    return f"Failed to find palette color: {output}"


@mcp.tool()
async def load_palette_from_file(filename: str, palette_path: str) -> str:
    """Load a palette from a file (.gpl/.hex/.pal) and apply it to the sprite.

    Args:
        filename: Path to the .aseprite file
        palette_path: Path to the palette file to load
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"
    err = reject_traversal(palette_path)
    if err:
        return err

    script = f"""
    local spr = app.activeSprite
    if not spr then return "No active sprite" end

    local ok, pal = pcall(function()
        return Palette{{ fromFile = "{lua_escape(palette_path)}" }}
    end)
    if not ok or not pal then return "Failed to load palette from file" end

    spr:setPalette(pal)
    spr:saveAs(spr.filename)
    return "Palette loaded"
    """

    success, output = AsepriteCommand.execute_lua_script(script, filename)
    if success:
        return f"Palette loaded from {palette_path} and applied to {filename}"
    return f"Failed to load palette: {output}"


@mcp.tool()
async def load_palette_from_resource(filename: str, resource_name: str) -> str:
    """Load a built-in palette resource (e.g. DB16, RPG, AAP-64) and apply it to the sprite.

    Args:
        filename: Path to the .aseprite file
        resource_name: Name of the built-in palette resource
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"

    safe_resource = lua_escape(resource_name)

    script = f"""
    local spr = app.activeSprite
    if not spr then return "No active sprite" end

    local ok, pal = pcall(function()
        return Palette{{ fromResource = "{safe_resource}" }}
    end)
    if not ok or not pal then return "Failed to load palette resource" end

    spr:setPalette(pal)
    spr:saveAs(spr.filename)
    return "Palette resource loaded"
    """

    success, output = AsepriteCommand.execute_lua_script(script, filename)
    if success:
        return f"Palette resource '{resource_name}' loaded and applied to {filename}"
    return f"Failed to load palette resource: {output}"
