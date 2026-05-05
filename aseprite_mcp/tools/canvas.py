import os
from ..core.commands import AsepriteCommand, lua_escape, reject_traversal
from .. import mcp
from .drawing import _parse_hex_color

_BLEND_MODES: dict[str, str] = {
    "normal": "BlendMode.NORMAL",
    "multiply": "BlendMode.MULTIPLY",
    "screen": "BlendMode.SCREEN",
    "overlay": "BlendMode.OVERLAY",
    "darken": "BlendMode.DARKEN",
    "lighten": "BlendMode.LIGHTEN",
    "color_dodge": "BlendMode.COLOR_DODGE",
    "color_burn": "BlendMode.COLOR_BURN",
    "hard_light": "BlendMode.HARD_LIGHT",
    "soft_light": "BlendMode.SOFT_LIGHT",
    "difference": "BlendMode.DIFFERENCE",
    "exclusion": "BlendMode.EXCLUSION",
    "hsl_hue": "BlendMode.HSL_HUE",
    "hsl_saturation": "BlendMode.HSL_SATURATION",
    "hsl_color": "BlendMode.HSL_COLOR",
    "hsl_luminosity": "BlendMode.HSL_LUMINOSITY",
    "addition": "BlendMode.ADDITION",
    "subtract": "BlendMode.SUBTRACT",
    "divide": "BlendMode.DIVIDE",
}

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
    return "Canvas created successfully"
    """
    
    success, output = AsepriteCommand.execute_lua_script(script)
    
    if success:
        return f"Canvas created successfully: {filename}"
    else:
        return f"Failed to create canvas: {output}"

@mcp.tool()
async def add_layer(filename: str, layer_name: str) -> str:
    """Add a new layer to the Aseprite file.

    Args:
        filename: Name of the Aseprite file to modify
        layer_name: Name of the new layer
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"
    
    safe_layer_name = lua_escape(layer_name)
    script = f"""
    local spr = app.activeSprite
    if not spr then return "No active sprite" end

    app.transaction(function()
        spr:newLayer()
        app.activeLayer.name = "{safe_layer_name}"
    end)
    
    spr:saveAs(spr.filename)
    return "Layer added successfully"
    """
    
    success, output = AsepriteCommand.execute_lua_script(script, filename)
    
    if success:
        return f"Layer '{layer_name}' added successfully to {filename}"
    else:
        return f"Failed to add layer: {output}"

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
    if not spr then return "No active sprite" end
    
    app.transaction(function()
        spr:newFrame()
    end)
    
    spr:saveAs(spr.filename)
    return "Frame added successfully"
    """
    
    success, output = AsepriteCommand.execute_lua_script(script, filename)
    
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
    if not spr then return "No active sprite" end

    local idx = {frame_index}
    if idx < 1 or idx > #spr.frames then
        return "Frame index out of range"
    end

    app.transaction(function()
        app.activeFrame = spr.frames[idx]
    end)

    spr:saveAs(spr.filename)
    return "Active frame set"
    """

    success, output = AsepriteCommand.execute_lua_script(script, filename)

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
    if not spr then return "No active sprite" end

    local idx = {frame_index}
    if idx < 1 or idx > #spr.frames then
        return "Frame index out of range"
    end

    app.transaction(function()
        spr.frames[idx].duration = {duration_ms} / 1000.0
    end)

    spr:saveAs(spr.filename)
    return "Frame duration set"
    """

    success, output = AsepriteCommand.execute_lua_script(script, filename)

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
    if not spr then return "No active sprite" end

    local target = nil
    for i, layer in ipairs(spr.layers) do
        if layer.name == "{safe_layer_name}" then
            target = layer
            break
        end
    end

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
    return "Active layer set"
    """

    success, output = AsepriteCommand.execute_lua_script(script, filename)

    if success:
        return f"Active layer set to '{layer_name}' in {filename}"
    else:
        return f"Failed to set layer: {output}"


@mcp.tool()
async def delete_layer(filename: str, layer_name: str) -> str:
    """Delete a layer by name.

    Args:
        filename: Name of the Aseprite file to modify
        layer_name: Name of the layer to delete
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
        spr:deleteLayer(target)
    end)

    spr:saveAs(spr.filename)
    return "Layer deleted"
    """

    success, output = AsepriteCommand.execute_lua_script(script, filename)

    if success:
        return f"Layer '{layer_name}' deleted from {filename}"
    else:
        return f"Failed to delete layer: {output}"


@mcp.tool()
async def set_layer_blend_mode(filename: str, layer_name: str, mode: str) -> str:
    """Set the blend mode of a layer.

    Args:
        filename: Name of the Aseprite file to modify
        layer_name: Name of the layer to modify
        mode: Blend mode (normal, multiply, screen, overlay, darken, lighten,
              color_dodge, color_burn, hard_light, soft_light, difference,
              exclusion, hsl_hue, hsl_saturation, hsl_color, hsl_luminosity,
              addition, subtract, divide)
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"

    mode_lower = mode.strip().lower()
    blend_mode = _BLEND_MODES.get(mode_lower)
    if blend_mode is None:
        valid = ", ".join(_BLEND_MODES.keys())
        return f"Invalid blend mode '{mode}'. Valid modes: {valid}"

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
        target.blendMode = {blend_mode}
    end)

    spr:saveAs(spr.filename)
    return "Blend mode set"
    """

    success, output = AsepriteCommand.execute_lua_script(script, filename)

    if success:
        return f"Blend mode of '{layer_name}' set to {mode} in {filename}"
    else:
        return f"Failed to set blend mode: {output}"


@mcp.tool()
async def reorder_layer(filename: str, layer_name: str, new_index: int) -> str:
    """Reorder a layer by setting its stack index (1-based).

    Args:
        filename: Name of the Aseprite file to modify
        layer_name: Name of the layer to reorder
        new_index: New stack index (1 = bottom)
    """
    if not os.path.exists(filename):
        return f"File {filename} not found"
    if new_index < 1:
        return "new_index must be >= 1"

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

    local idx = {new_index}
    if idx > #spr.layers then return "Index out of range" end

    app.transaction(function()
        target.stackIndex = idx
    end)

    spr:saveAs(spr.filename)
    return "Layer reordered"
    """

    success, output = AsepriteCommand.execute_lua_script(script, filename)

    if success:
        return f"Layer '{layer_name}' reordered to index {new_index} in {filename}"
    else:
        return f"Failed to reorder layer: {output}"


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
