import os
from typing import Optional
from ..core.commands import AsepriteCommand, lua_escape, reject_traversal
from .. import mcp


_LAYOUT_TYPES = {"horizontal", "vertical", "rows", "columns", "packed"}
_DATA_FORMATS = {"json_array", "json_hash"}


def _layout_to_lua(layout: str) -> str:
    return f"SpriteSheetType.{layout.upper()}"


def _data_format_to_lua(fmt: str) -> str:
    return f"SpriteSheetDataFormat.{fmt.upper()}"

@mcp.tool()
async def export_sprite(filename: str, output_filename: str, format: str = "png") -> str:
    """Export the Aseprite file to another format.

    Args:
        filename: Name of the Aseprite file to export
        output_filename: Name of the output file
        format: Output format (default: "png", can be "png", "gif", "jpg", etc.)
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"
    
    # Make sure format is lowercase
    format = format.lower()
    
    # Ensure output filename has the correct extension
    if not output_filename.lower().endswith(f".{format}"):
        output_filename = f"{output_filename}.{format}"
    
    # For animated exports
    if format == "gif":
        args = ["--batch", filename, "--save-as", output_filename]
        success, output = AsepriteCommand.run_command(args)
    else:
        # For still image exports
        args = ["--batch", filename, "--save-as", output_filename]
        success, output = AsepriteCommand.run_command(args)
    
    if success:
        return f"Sprite exported successfully to {output_filename}"
    else:
        return f"Failed to export sprite: {output}"

@mcp.tool()
async def copy_sprite(filename: str, output_filename: str, overwrite: bool = False) -> str:
    """Copy a sprite to a new Aseprite file.

    Args:
        filename: Name of the Aseprite file to copy
        output_filename: Name of the output .aseprite file
        overwrite: Whether to overwrite if output exists
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"

    if not output_filename.lower().endswith(".aseprite"):
        output_filename = f"{output_filename}.aseprite"

    err = reject_traversal(output_filename)
    if err:
        return err

    if os.path.exists(output_filename) and not overwrite:
        return f"Output file {output_filename} already exists"

    safe_path = lua_escape(output_filename.replace("\\", "/"))
    script = f"""
    local spr = app.activeSprite
    if not spr then return "No active sprite" end

    spr:saveAs("{safe_path}")
    return "Sprite copied"
    """

    success, output = AsepriteCommand.execute_lua_script(script, filename)
    if success:
        return f"Sprite copied to {output_filename}"
    return f"Failed to copy sprite: {output}"


@mcp.tool()
async def export_sprite_sheet(
    filename: str,
    output_texture: str,
    output_data: Optional[str] = None,
    data_format: str = "json_array",
    layout: str = "horizontal",
    border_padding: int = 0,
    shape_padding: int = 0,
    inner_padding: int = 0,
    trim: bool = False,
    trim_by_grid: bool = False,
    ignore_empty: bool = False,
    merge_duplicates: bool = False,
    split_layers: bool = False,
    split_tags: bool = False,
    list_slices: bool = False,
) -> str:
    """Export a sprite sheet from the Aseprite file.

    Generates a texture atlas (spritesheet) with optional JSON data file
    containing frame metadata.

    Args:
        filename: Name of the Aseprite file to export
        output_texture: Filename for the output spritesheet image (e.g. "sheet.png")
        output_data: Optional filename for the JSON metadata (e.g. "sheet.json")
        data_format: Data file format ("json_array" or "json_hash", default: "json_array")
        layout: Spritesheet layout type ("horizontal", "vertical", "rows", "columns", "packed", default: "horizontal")
        border_padding: Border padding in pixels (default: 0)
        shape_padding: Shape padding in pixels (default: 0)
        inner_padding: Inner padding in pixels (default: 0)
        trim: Trim transparent pixels from each frame (default: False)
        trim_by_grid: Trim sprite by grid cell (default: False)
        ignore_empty: Exclude empty frames from the sheet (default: False)
        merge_duplicates: Merge duplicate frames into a single reference (default: False)
        split_layers: Export each layer as a separate frame (default: False)
        split_tags: Export each tag as a separate spritesheet (default: False)
        list_slices: Export each slice as a separate frame (default: False)
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"

    err = reject_traversal(output_texture)
    if err:
        return err
    if output_data is not None:
        err = reject_traversal(output_data)
        if err:
            return err

    layout = layout.lower()
    if layout not in _LAYOUT_TYPES:
        return f"Invalid layout type '{layout}'. Must be one of: {', '.join(sorted(_LAYOUT_TYPES))}"

    data_format = data_format.lower()
    if data_format not in _DATA_FORMATS:
        return f"Invalid data format '{data_format}'. Must be one of: {', '.join(sorted(_DATA_FORMATS))}"

    safe_texture = lua_escape(output_texture.replace("\\", "/"))
    safe_data = lua_escape(output_data.replace("\\", "/")) if output_data else ""

    lua_lines = [
        "local spr = app.activeSprite",
        "if not spr then return \"No active sprite\" end",
        "",
        "app.command.ExportSpriteSheet{",
        "  ui=false,",
        f"  type={_layout_to_lua(layout)},",
        f"  textureFilename=\"{safe_texture}\",",
    ]

    if output_data:
        lua_lines.append(f'  dataFilename="{safe_data}",')
        lua_lines.append(f"  dataFormat={_data_format_to_lua(data_format)},")

    lua_lines.append(f"  borderPadding={border_padding},")
    lua_lines.append(f"  shapePadding={shape_padding},")
    lua_lines.append(f"  innerPadding={inner_padding},")
    lua_lines.append(f"  trim={'true' if trim else 'false'},")

    if trim_by_grid:
        lua_lines.append("  trimByGrid=true,")

    lua_lines.append(f"  ignoreEmpty={'true' if ignore_empty else 'false'},")
    lua_lines.append(f"  mergeDuplicates={'true' if merge_duplicates else 'false'},")
    lua_lines.append(f"  splitLayers={'true' if split_layers else 'false'},")
    lua_lines.append(f"  splitTags={'true' if split_tags else 'false'},")
    lua_lines.append(f"  listSlices={'true' if list_slices else 'false'},")
    lua_lines.append("}")
    lua_lines.append("")
    lua_lines.append('return "Sprite sheet exported"')

    script = "\n".join(lua_lines)
    success, output = AsepriteCommand.execute_lua_script(script, filename)

    if success:
        return f"Sprite sheet exported to {output_texture}"
    return f"Failed to export sprite sheet: {output}"


@mcp.tool()
async def duplicate_sprite(filename: str, output_filename: str) -> str:
    """Duplicate a sprite to a new Aseprite file.

    Uses app.command.DuplicateSprite to create a copy, then saves
    under a new name.

    Args:
        filename: Name of the Aseprite file to duplicate
        output_filename: Name for the duplicated file
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"

    err = reject_traversal(output_filename)
    if err:
        return err

    safe_path = lua_escape(output_filename.replace("\\", "/"))
    script = f"""
    local spr = app.activeSprite
    if not spr then return "No active sprite" end

    app.command.DuplicateSprite{{ui=false}}
    local dup = app.activeSprite
    if not dup then return "Failed to duplicate sprite" end

    dup:saveAs("{safe_path}")
    return "Sprite duplicated"
    """

    success, output = AsepriteCommand.execute_lua_script(script, filename)

    if success:
        return f"Sprite duplicated to {output_filename}"
    return f"Failed to duplicate sprite: {output}"


