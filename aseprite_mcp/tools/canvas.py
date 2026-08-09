import os
from ..core.commands import AsepriteCommand, lua_escape, reject_traversal
from ..core.lua import FIND_LAYER
from .. import mcp
from .drawing import _parse_hex_color


@mcp.tool()
async def create_canvas(width: int, height: int, filename: str = "canvas.aseprite") -> str:
    """Create a new Aseprite canvas with specified dimensions.

    Args:
        width: Width of the canvas in pixels
        height: Height of the canvas in pixels
        filename: Name of the output file (default: canvas.aseprite)
    """
    if width <= 0 or height <= 0:
        return "Width and height must be > 0"
    err = reject_traversal(filename)
    if err:
        return err

    safe_path = lua_escape(filename.replace("\\", "/"))
    script = f"""
    local spr = Sprite({width}, {height})
    spr:saveAs("{safe_path}")
    print("OK")
    """

    success, output = AsepriteCommand.execute_lua_script_checked(script)

    if success:
        return f"Canvas created successfully: {filename}"
    else:
        return f"Failed to create canvas: {output}"

@mcp.tool()
async def add_layer(filename: str, layer_name: str, group: str = "") -> str:
    """Add a new layer to the Aseprite file.

    Args:
        filename: Name of the Aseprite file to modify
        layer_name: Name of the new layer
        group: Optional group to place the new layer inside, by name or
            "group/subgroup" path (default: top level)
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"

    safe_layer_name = lua_escape(layer_name)
    safe_group = lua_escape(group)
    script = f"""
    {FIND_LAYER}
    local spr = app.activeSprite
    if not spr then print("ERROR:No active sprite") return end

    local parent = nil
    if "{safe_group}" ~= "" then
        parent = find_layer(spr, "{safe_group}")
        if not parent then print("ERROR:Group not found") return end
        if not parent.isGroup then print("ERROR:Target is not a group") return end
    end

    app.transaction(function()
        local lyr = spr:newLayer()
        lyr.name = "{safe_layer_name}"
        if parent then lyr.parent = parent end
    end)

    spr:saveAs(spr.filename)
    print("OK")
    """

    success, output = AsepriteCommand.execute_lua_script_checked(script, filename)

    if success:
        location = f" inside group '{group}'" if group else ""
        return f"Layer '{layer_name}' added{location} to {filename}"
    else:
        return f"Failed to add layer: {output}"

@mcp.tool()
async def add_group(filename: str, group_name: str, parent_group: str = "") -> str:
    """Add a new, empty group layer.

    Combine with add_layer(group=...) / duplicate_layer(group=...) to build a
    grouped layer structure.

    Args:
        filename: Name of the Aseprite file to modify
        group_name: Name of the new group
        parent_group: Optional existing group to nest the new group inside, by
            name or "group/subgroup" path (default: top level)
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"

    safe_group = lua_escape(group_name)
    safe_parent = lua_escape(parent_group)
    script = f"""
    {FIND_LAYER}
    local spr = app.activeSprite
    if not spr then print("ERROR:No active sprite") return end

    local parent = nil
    if "{safe_parent}" ~= "" then
        parent = find_layer(spr, "{safe_parent}")
        if not parent then print("ERROR:Parent group not found") return end
        if not parent.isGroup then print("ERROR:Target is not a group") return end
    end

    app.transaction(function()
        local grp = spr:newGroup()
        grp.name = "{safe_group}"
        if parent then grp.parent = parent end
    end)

    spr:saveAs(spr.filename)
    print("OK")
    """

    success, output = AsepriteCommand.execute_lua_script_checked(script, filename)

    if success:
        location = f" inside '{parent_group}'" if parent_group else ""
        return f"Group '{group_name}' created{location} in {filename}"
    return f"Failed to create group: {output}"

@mcp.tool()
async def add_frame(filename: str) -> str:
    """Add a new frame to the Aseprite file.

    Args:
        filename: Name of the Aseprite file to modify
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"
    
    script = """
    local spr = app.activeSprite
    if not spr then print("ERROR:No active sprite") return end

    app.transaction(function()
        spr:newFrame()
    end)

    spr:saveAs(spr.filename)
    print("OK")
    """

    success, output = AsepriteCommand.execute_lua_script_checked(script, filename)

    if success:
        return f"New frame added successfully to {filename}"
    else:
        return f"Failed to add frame: {output}"

@mcp.tool()
async def set_frame(filename: str, frame_index: int) -> str:
    """Set the active frame by index (1-based).

    Args:
        filename: Name of the Aseprite file to modify
        frame_index: Frame index starting at 1
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"

    script = f"""
    local spr = app.activeSprite
    if not spr then print("ERROR:No active sprite") return end

    local idx = {frame_index}
    if idx < 1 or idx > #spr.frames then
        print("ERROR:Frame index out of range") return
    end

    app.transaction(function()
        app.activeFrame = spr.frames[idx]
    end)

    spr:saveAs(spr.filename)
    print("OK")
    """

    success, output = AsepriteCommand.execute_lua_script_checked(script, filename)

    if success:
        return f"Active frame set to {frame_index} in {filename}"
    else:
        return f"Failed to set frame: {output}"

@mcp.tool()
async def set_frame_duration(filename: str, frame_index: int, duration_ms: int) -> str:
    """Set the duration of a frame in milliseconds.

    Args:
        filename: Name of the Aseprite file to modify
        frame_index: Frame index starting at 1
        duration_ms: Duration in milliseconds
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"
    if duration_ms <= 0:
        return "Duration must be > 0"

    script = f"""
    local spr = app.activeSprite
    if not spr then print("ERROR:No active sprite") return end

    local idx = {frame_index}
    if idx < 1 or idx > #spr.frames then
        print("ERROR:Frame index out of range") return
    end

    app.transaction(function()
        spr.frames[idx].duration = {duration_ms} / 1000.0
    end)

    spr:saveAs(spr.filename)
    print("OK")
    """

    success, output = AsepriteCommand.execute_lua_script_checked(script, filename)

    if success:
        return f"Frame {frame_index} duration set to {duration_ms}ms in {filename}"
    else:
        return f"Failed to set frame duration: {output}"

@mcp.tool()
async def set_layer(filename: str, layer_name: str, create_if_missing: bool = False) -> str:
    """Set the active layer by name.

    Args:
        filename: Name of the Aseprite file to modify
        layer_name: Layer name to activate
        create_if_missing: Create layer if it does not exist
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"

    create_flag = "true" if create_if_missing else "false"
    safe_layer_name = lua_escape(layer_name)

    script = f"""
    local spr = app.activeSprite
    if not spr then print("ERROR:No active sprite") return end

    {FIND_LAYER}
    local target = find_layer(spr, "{safe_layer_name}")

    app.transaction(function()
        if not target then
            if {create_flag} then
                target = spr:newLayer()
                target.name = "{safe_layer_name}"
            else
                return
            end
        end
        app.activeLayer = target
    end)

    spr:saveAs(spr.filename)
    print("OK")
    """

    success, output = AsepriteCommand.execute_lua_script_checked(script, filename)

    if success:
        return f"Active layer set to '{layer_name}' in {filename}"
    else:
        return f"Failed to set layer: {output}"


@mcp.tool()
async def flatten_layers(filename: str) -> str:
    """Flatten all layers into a single layer.

    Args:
        filename: Name of the Aseprite file to modify
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"

    script = """
    local spr = app.activeSprite
    if not spr then return "No active sprite" end

    app.transaction(function()
        spr:flatten()
    end)

    spr:saveAs(spr.filename)
    return "Layers flattened"
    """

    success, output = AsepriteCommand.execute_lua_script(script, filename)

    if success:
        return f"Layers flattened in {filename}"
    else:
        return f"Failed to flatten layers: {output}"


@mcp.tool()
async def merge_down_layer(filename: str, layer_name: str) -> str:
    """Merge a layer down with the layer below it.

    Args:
        filename: Name of the Aseprite file to modify
        layer_name: Name of the layer to merge down
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"

    safe_layer_name = lua_escape(layer_name)
    script = f"""
    local spr = app.activeSprite
    if not spr then return "No active sprite" end

    local target = nil
    for i, layer in ipairs(spr.layers) do
        if layer.name == "{safe_layer_name}" then
            target = layer
            break
        end
    end
    if not target then return "Layer not found" end

    app.transaction(function()
        app.activeLayer = target
        spr:mergeDown()
    end)

    spr:saveAs(spr.filename)
    return "Layer merged down"
    """

    success, output = AsepriteCommand.execute_lua_script(script, filename)

    if success:
        return f"Layer '{layer_name}' merged down in {filename}"
    else:
        return f"Failed to merge layer down: {output}"


@mcp.tool()
async def set_layer_label_color(filename: str, layer_name: str, color_hex: str) -> str:
    """Set the label color of a layer.

    Args:
        filename: Name of the Aseprite file to modify
        layer_name: Name of the layer to modify
        color_hex: Hex color code (e.g. "#FF0000" for red)
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"

    rgb = _parse_hex_color(color_hex)
    if rgb is None:
        return f"Invalid color value: {color_hex}"
    r, g, b = rgb

    safe_layer_name = lua_escape(layer_name)
    script = f"""
    local spr = app.activeSprite
    if not spr then return "No active sprite" end

    local target = nil
    for i, layer in ipairs(spr.layers) do
        if layer.name == "{safe_layer_name}" then
            target = layer
            break
        end
    end
    if not target then return "Layer not found" end

    app.transaction(function()
        target.color = Color({r}, {g}, {b})
    end)

    spr:saveAs(spr.filename)
    return "Layer label color set"
    """

    success, output = AsepriteCommand.execute_lua_script(script, filename)

    if success:
        return f"Label color of '{layer_name}' set to {color_hex} in {filename}"
    else:
        return f"Failed to set layer label color: {output}"


@mcp.tool()
async def set_cel_zindex(filename: str, layer_name: str, frame_index: int, z_index: int) -> str:
    """Set the z-index of a cel on a specific layer and frame.

    Args:
        filename: Name of the Aseprite file to modify
        layer_name: Name of the layer containing the cel
        frame_index: Frame index starting at 1
        z_index: Z-index value for cel stacking order
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"

    safe_layer_name = lua_escape(layer_name)
    script = f"""
    local spr = app.activeSprite
    if not spr then return "No active sprite" end

    local idx = {frame_index}
    if idx < 1 or idx > #spr.frames then return "Frame index out of range" end

    local target = nil
    for i, layer in ipairs(spr.layers) do
        if layer.name == "{safe_layer_name}" then
            target = layer
            break
        end
    end
    if not target then return "Layer not found" end

    local cel = target:cel(spr.frames[idx])
    if not cel then return "No cel found on that layer/frame" end

    app.transaction(function()
        cel.zIndex = {z_index}
    end)

    spr:saveAs(spr.filename)
    return "Cel z-index set"
    """

    success, output = AsepriteCommand.execute_lua_script(script, filename)

    if success:
        return f"Cel z-index set to {z_index} on '{layer_name}' frame {frame_index} in {filename}"
    else:
        return f"Failed to set cel z-index: {output}"
