# Aseprite MCP

> Model Context Protocol server for programmatic control of [Aseprite](https://www.aseprite.org) — create sprites, draw pixels, animate, and export, all from AI agents.

## Features

- **60+ MCP tools** covering the full Aseprite Lua scripting API
- **Drawing**: pixels, lines, rectangles, circles, polygons, paths, fills, gradients
- **Animation**: frame manipulation, cel tweens (position/opacity/scale with easing), oscillation, tags
- **Layers**: add/delete/reorder, blend modes, visibility, opacity, groups, flatten/merge
- **Selection**: select, deselect, add/subtract/intersect, move, query bounds
- **Image filters**: invert, noise, despeckle, sobel, oil, super pixel, HSL adjust, replace color, flood fill
- **Palette**: read/write, resize, find matches, load from file or built-in resource
- **Slices & tilesets**: create/delete/query, 9-slice, pivot, tilemap layers
- **Export**: PNG/GIF/JPG, sprite sheets with full layout control, duplicate, copy
- **Quality**: validate scene, audit overlaps, sanitize frame ranges
- **Canvas**: resize, crop, flip, rotate layers
- **Cross-platform**: macOS, Windows, Linux

## Quick Start

```bash
git clone https://github.com/striderZA/aseprite-mcp
cd aseprite-mcp
uv sync                        # install dependencies into .venv
ASEPRITE_PATH=/path/to/aseprite uv run -m aseprite_mcp
```

```powershell
git clone https://github.com/striderZA/aseprite-mcp
cd aseprite-mcp
uv sync                        # install dependencies into .venv
$env:ASEPRITE_PATH = "C:\Program Files\Aseprite\aseprite.exe"
uv run -m aseprite_mcp
```

### MCP Client Configuration

**OpenCode** — add to `opencode.json` in the project root:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "aseprite": {
      "type": "local",
      "command": ["uv", "--directory", "/path/to/aseprite-mcp", "run", "--no-sync", "-m", "aseprite_mcp"],
      "enabled": true,
      "environment": {
        "ASEPRITE_PATH": "/Applications/Aseprite.app/Contents/MacOS/aseprite"
      }
    }
  }
}
```

> `--no-sync` skips dependency checking on every launch (run `uv sync` after pulling changes).
> **Windows**: `"command": ["uv", "--directory", "C:\\path\\to\\aseprite-mcp", "run", "--no-sync", "-m", "aseprite_mcp"]`, `"ASEPRITE_PATH": "C:\\Program Files\\Aseprite\\aseprite.exe"`

**Claude Desktop / Cursor** — add to your MCP client config:

```json
{
  "mcpServers": {
    "aseprite": {
      "command": "uv",
      "args": ["--directory", "/path/to/aseprite-mcp", "run", "-m", "aseprite_mcp"]
    }
  }
}
```

## Tool Reference

### Canvas & Document

| Tool | Description |
|------|-------------|
| `create_canvas` | Create a new sprite with dimensions |
| `save_copy_as` | Save a copy without marking as saved |
| `close_sprite` | Close the sprite (destructive — warns) |
| `resize_canvas` | Scale canvas and content |
| `crop_canvas` | Crop to a rectangle |
| `convert_color_space` | Convert between sRGB/linear |
| `import_image_as_layer` | Import image as a new layer |

### Layers

| Tool | Description |
|------|-------------|
| `add_layer` | Add a new layer |
| `set_layer` | Set active layer by name |
| `delete_layer` | Delete a layer by name |
| `set_layer_blend_mode` | Set blend mode (normal, multiply, screen, etc.) |
| `reorder_layer` | Change layer stack index |
| `set_layer_visibility` | Show/hide layer |
| `set_layer_opacity` | Set 0-255 opacity |
| `set_layer_label_color` | Set layer tab color |
| `flatten_layers` | Flatten all layers |
| `merge_down_layer` | Merge layer into the one below |

### Drawing

| Tool | Description |
|------|-------------|
| `draw_pixels` / `draw_pixels_at` | Place individual pixels |
| `draw_line` / `draw_line_at` | Bresenham line with thickness |
| `draw_rectangle` / `draw_rectangle_at` | Rectangle (outline or filled) |
| `draw_circle` / `draw_circle_at` | Circle/ellipse (outline or filled) |
| `fill_area` / `fill_area_at` | Paint bucket fill |
| `draw_polygon` | Polygon with fill support |
| `draw_path` | Polyline path |
| `apply_gradient_rect` | Linear gradient fill |

### Image Filters

| Tool | Description |
|------|-------------|
| `invert_colors_at` | Invert all colors |
| `replace_color_at` | Swap one color for another |
| `flood_fill_at` | Flood fill with tolerance |
| `apply_noise_at` | Add noise |
| `apply_despeckle_at` | Remove noise |
| `apply_sobel_at` | Edge detection |
| `apply_oil_at` | Oil paint effect |
| `apply_super_pixel_at` | Pixelate |
| `adjust_hsl_at` | Hue/saturation/value/lightness |

### Animation

| Tool | Description |
|------|-------------|
| `add_frame` / `add_frames` | Add 1 or N frames |
| `set_frame_duration` | Per-frame duration |
| `set_frame_duration_all` | Set all frames duration |
| `duplicate_frame_range` | Duplicate and append |
| `copy_frame` | Copy all layers to another frame |
| `propagate_frame_to_range` | Copy one frame across a range |
| `propagate_cels` | Copy specific layers across range |
| `create_cel` | Create empty cel |
| `clear_cel` | Delete cel |
| `copy_cel` | Copy cel between frames |
| `set_cel_position` | Set cel position |
| `set_cel_zindex` | Set cel stacking order |
| `offset_cel_positions` | Offset by delta |
| `tween_cel_positions` | Linear position tween |
| `tween_cel_positions_eased` | Eased position tween |
| `tween_cel_opacity_eased` | Opacity fade with easing |
| `tween_cel_scale_eased` | Scale tween with easing |
| `oscillate_cel_positions` | Sine-wave oscillation |

### Selection

| Tool | Description |
|------|-------------|
| `select_rectangle` | Select/add/subtract/intersect a rectangle |
| `select_all` | Select entire canvas |
| `deselect` | Clear selection |
| `get_selection` | Query bounds and state as JSON |
| `move_selection` | Shift selection origin by delta |

### Palette

| Tool | Description |
|------|-------------|
| `get_palette` | Read palette as hex array |
| `set_palette` | Set palette from hex colors |
| `remap_colors_in_cel_range` | Remap specific colors across frames |
| `save_palette_to_file` | Export to .gpl/.hex/.pal |
| `resize_palette` | Change entry count |
| `find_palette_color` | Find index by exact or best match |
| `load_palette_from_file` | Load from .gpl/.hex/.pal |
| `load_palette_from_resource` | Load built-in (DB16, RPG, etc.) |

### Slices & Tilesets

| Tool | Description |
|------|-------------|
| `create_slice` | Create slice with bounds, 9-slice center, pivot |
| `delete_slice` | Delete by name |
| `get_slices` | List all slices as JSON |
| `set_slice_properties` | Update bounds/center/pivot/color/data |
| `create_tileset` | New tileset with tile dimensions |
| `delete_tileset` | Delete by name |
| `get_tilesets` | List all tilesets as JSON |
| `get_tilemap_layers` | List tilemap layers |

### Transform

| Tool | Description |
|------|-------------|
| `flip_layer` | Horizontal or vertical flip |
| `rotate_layer` | 90°/180°/270° clockwise |
| `resize_canvas` | Scale canvas |
| `crop_canvas` | Crop to rect |

### Export

| Tool | Description |
|------|-------------|
| `export_sprite` | Export to PNG/GIF/JPG |
| `export_sprite_sheet` | Full spritesheet with layout/padding/trim |
| `copy_sprite` | Duplicate .aseprite file |
| `duplicate_sprite` | Via Aseprite command |
| `flatten_layers` | Flatten before export |

### Scene & Quality

| Tool | Description |
|------|-------------|
| `copy_layers_between_sprites` | Copy specific layers between files |
| `ensure_layers_present` | Fill missing cels |
| `validate_scene` | Check layer/cel coverage |
| `audit_animation` | Overlap and range audit (JSON) |
| `animation_sanitize` | Auto-fix animation issues |

### Utilities

| Tool | Description |
|------|-------------|
| `undo_sprite` | Undo last action |
| `set_fg_color` / `set_bg_color` | Set global colors |
| `get_app_version` | Aseprite version as JSON |
| `open_sprite` | Open file |
| `set_onion_skin` | Configure onion skin prefs |
| `set_tag` | Create/update animation tag with direction |
| `start_preview_server` | HTTP preview server |
| `stop_preview_server` | Stop preview server |
| `animation_workflow_guide` | Workflow advice for common cases |

## Configuration

Set `ASEPRITE_PATH` to your Aseprite binary:

| OS | Typical Path |
|----|-------------|
| macOS | `/Applications/Aseprite.app/Contents/MacOS/aseprite` |
| Windows | `C:\Program Files\Aseprite\aseprite.exe` |
| Linux | `/usr/bin/aseprite` |

A `.env` file in the project root is loaded automatically.

## Development

```bash
uv sync                    # Install dependencies
uv run pytest tests/       # Run 114+ unit tests
uv run python -m aseprite_mcp  # Run the server (stdio)
```

## Project Structure

```
aseprite_mcp/
├── __init__.py          # FastMCP server setup
├── __main__.py          # Entry point
├── core/
│   └── commands.py      # Lua execution, path safety
└── tools/
    ├── animation.py     # Frame/cel/tween operations
    ├── app.py           # Undo, colors, version
    ├── canvas.py        # Create, layers, frames
    ├── drawing.py       # All drawing + image filters
    ├── export.py        # Export PNG, spritesheets
    ├── guide.py         # Workflow advice
    ├── palette.py       # Color palette operations
    ├── pixel_read.py    # Get pixel/region colors
    ├── preview.py       # HTTP preview server
    ├── quality.py       # Audit, sanitize, validate
    ├── scene.py         # Cross-sprite layer copy
    ├── selection.py     # Selection API
    ├── slice.py         # Slice create/delete/query
    ├── tileset.py       # Tileset & tilemap ops
    └── transform.py     # Flip, rotate, resize, crop
```

## License

MIT
