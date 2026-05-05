import os
from ..core.commands import AsepriteCommand, lua_escape, reject_traversal
from .. import mcp


@mcp.tool()
async def create_tileset(filename: str, name: str, tile_width: int, tile_height: int) -> str:
    """Create a new tileset in the Aseprite file.

    Args:
        filename: Name of the Aseprite file to modify
        name: Name for the new tileset
        tile_width: Width of each tile in pixels
        tile_height: Height of each tile in pixels
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"
    if tile_width <= 0 or tile_height <= 0:
        return "Tile dimensions must be > 0"

    safe_name = lua_escape(name)

    script = f"""
    local spr = app.activeSprite
    if not spr then return "No active sprite" end

    local ts = spr:newTileset("{safe_name}", {tile_width}, {tile_height})
    if not ts then
        return "Failed to create tileset"
    end

    spr:saveAs(spr.filename)
    return "Tileset created successfully"
    """

    success, output = AsepriteCommand.execute_lua_script(script, filename)

    if success:
        return f"Tileset '{name}' ({tile_width}x{tile_height}) created in {filename}"
    return f"Failed to create tileset: {output}"


@mcp.tool()
async def delete_tileset(filename: str, name: str) -> str:
    """Delete a tileset by name from the Aseprite file.

    Args:
        filename: Name of the Aseprite file to modify
        name: Name of the tileset to delete
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"

    safe_name = lua_escape(name)

    script = f"""
    local spr = app.activeSprite
    if not spr then return "No active sprite" end

    local target = nil
    for _, ts in ipairs(spr.tilesets) do
        if ts.name == "{safe_name}" then
            target = ts
            break
        end
    end

    if not target then
        return "Tileset not found"
    end

    spr:deleteTileset(target)
    spr:saveAs(spr.filename)
    return "Tileset deleted"
    """

    success, output = AsepriteCommand.execute_lua_script(script, filename)

    if success:
        return f"Tileset '{name}' deleted from {filename}"
    return f"Failed to delete tileset: {output}"


@mcp.tool()
async def get_tilesets(filename: str) -> str:
    """List all tilesets in the Aseprite file as JSON.

    Args:
        filename: Name of the Aseprite file
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"

    script = """
    local spr = app.activeSprite
    if not spr then print("[]") return end

    local parts = {}
    table.insert(parts, "[")
    for i, ts in ipairs(spr.tilesets) do
        table.insert(parts, "{")
        table.insert(parts, "\\"name\\":\\"" .. ts.name .. "\\",")
        table.insert(parts, "\\"tileWidth\\":" .. ts.tileWidth .. ",")
        table.insert(parts, "\\"tileHeight\\":" .. ts.tileHeight .. ",")
        table.insert(parts, "\\"colorMode\\":" .. ts.colorMode)
        table.insert(parts, "}")
        if i < #spr.tilesets then
            table.insert(parts, ",")
        end
    end
    table.insert(parts, "]")
    print(table.concat(parts))
    """

    success, output = AsepriteCommand.execute_lua_script(script, filename)

    if success:
        return output
    return f"Failed to get tilesets: {output}"


@mcp.tool()
async def get_tilemap_layers(filename: str) -> str:
    """List all tilemap layers in the Aseprite file as JSON.

    Args:
        filename: Name of the Aseprite file
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"

    script = """
    local spr = app.activeSprite
    if not spr then print("[]") return end

    local parts = {}
    table.insert(parts, "[")
    local count = 0
    for i, layer in ipairs(spr.layers) do
        if layer.isTilemap then
            if count > 0 then
                table.insert(parts, ",")
            end
            table.insert(parts, "{")
            table.insert(parts, "\\"name\\":\\"" .. layer.name .. "\\",")
            table.insert(parts, "\\"isTilemap\\":true,")
            table.insert(parts, "\\"index\\":" .. i)
            table.insert(parts, "}")
            count = count + 1
        end
    end
    table.insert(parts, "]")
    print(table.concat(parts))
    """

    success, output = AsepriteCommand.execute_lua_script(script, filename)

    if success:
        return output
    return f"Failed to get tilemap layers: {output}"
