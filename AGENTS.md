# Repository Guidelines

## Project Overview

`aseprite-mcp` is a Model Context Protocol (MCP) server that gives AI agents programmatic control of [Aseprite](https://www.aseprite.org) — create sprites, draw pixels, animate, and export. It is a Python 3.13 package (`aseprite_mcp/`, v0.1.0, MIT) that registers **80+ MCP tools** which translate agent calls into Aseprite's Lua scripting API and execute them via the Aseprite CLI in batch mode. There is no HTTP/JSON-RPC/websocket bridge to Aseprite — subprocess CLI is the only channel.

## Architecture & Data Flow

**Server setup (import-time singleton):**
- `aseprite_mcp/__init__.py` creates `mcp = FastMCP("aseprite")` at import time. All tool modules import this instance and register via `@mcp.tool()` decorators.
- `aseprite_mcp/__main__.py` is the entry point: `mcp.run(transport='stdio')`.
- `aseprite_mcp/tools/__init__.py` imports all tool modules for their registration side-effects — there is **no manual registration list**.

**Tool execution pipeline (same pattern for every tool):**
1. Async tool function validates inputs (early-return on failure — see Error Handling).
2. It builds a Lua script string against Aseprite's API (`app.activeSprite`, `app.transaction(function()...end)`, `app.useTool{...}`, `Sprite{fromFile=...}`, `spr:saveAs(...)`).
3. `AsepriteCommand.execute_lua_script(script, filename)` writes the script to a temp `.lua` file and runs `aseprite --batch [<filename>] --script <tmp>` via subprocess, then deletes the temp file.
4. The tool returns a human-readable success/failure string (never raises).

**Data flow:** MCP client (OpenCode / Claude Desktop / Cursor) → stdio → FastMCP tool → Lua script → Aseprite CLI batch mode → file mutated on disk → result string returned to the client.

## Key Directories

```
aseprite_mcp/
├── __init__.py          # FastMCP server singleton + version
├── __main__.py          # Entry point (stdio transport)
├── core/
│   └── commands.py      # Aseprite subprocess bridge, Lua escaping, path safety, .env loading
└── tools/               # One module per domain; every function decorated with @mcp.tool()
    ├── animation.py     # Frames, cels, tweens, tags, onion skin, propagation
    ├── app.py           # undo, colors, version, open
    ├── canvas.py        # Canvas + layer/frame management
    ├── drawing.py       # Primitives, *_at variants, image filters, hex color parsing
    ├── export.py        # PNG/GIF/JPG, sprite sheets, copy/duplicate
    ├── guide.py         # Text-only workflow guide (no Aseprite call)
    ├── palette.py       # Palette read/write/remap/load
    ├── pixel_read.py    # Get pixel/region colors
    ├── preview.py       # Detached HTTP preview server (PID-file managed)
    ├── quality.py       # Layer/cel validation, animation audit + sanitize
    ├── scene.py         # Cross-sprite layer copy
    ├── selection.py     # Rectangle select, select_all, move, query
    ├── slice.py         # Slice create/delete/query/update
    ├── sprite.py        # Save copy, close, palette, color space, image import
    ├── tileset.py       # Tileset + tilemap ops
    └── transform.py     # Flip, rotate, resize, crop
```

`tests/` holds the pytest suite (see Testing & QA).

## Development Commands

Project is managed with **uv** (Python 3.13 pinned in `.python-version`):

```bash
uv sync                                # Install runtime deps into .venv (uv.lock)
uv run pytest tests/                   # Run unit tests
uv run -m aseprite_mcp                 # Run the MCP server (stdio) for local testing
ASEPRITE_PATH=/path/to/aseprite uv run -m aseprite_mcp   # With Aseprite on the path
```

- No console scripts exist — always invoke via `python -m aseprite_mcp`.
- A `.env` file in the project root is auto-loaded (python-dotenv); `ASEPRITE_PATH` is the only documented variable. Copy `sample.env` for the per-OS path table.
- There is **no lint/format/CI configuration** in the repo. `requirements.txt` pins dev tools (pytest, black, flake8, typing_extensions) but is **not** part of `uv.lock`, so `uv sync` will not install them.

## Code Conventions & Common Patterns

**Tool pattern (mandatory, uniform across `tools/`):**
- One `@mcp.tool()` per async function; the registered name is the function name (snake_case, verb-first: `draw_line`, `set_layer`, `export_sprite`).
- The first parameter is almost always `filename: str` (the `.aseprite` file to operate on); domain-specific params follow.
- Docstrings describe behavior concisely; per the PR template they must include `Args:` and produce user-actionable errors.
- Return `str` describing success or failure — tools never raise. Typical failure shape: `f"Failed to ...: {output}"` using stderr from the failed subprocess.

**Error handling:**
- Early-return validation: `os.path.exists(filename)` check, invalid hex via `_parse_hex_color` (returns `None`), path traversal via `reject_traversal`, out-of-range count/index checks.
- `AsepriteCommand.run_command` catches `subprocess.CalledProcessError` and returns `(False, stderr)`.
- No retries, no timeouts on subprocesses.

**Security (binding — see PR checklist):**
- Every user-supplied string embedded in Lua MUST pass `lua_escape(s)` (escapes backslashes, quotes, newlines, null) before interpolation.
- Every user-supplied filename/path MUST pass `reject_traversal(path)`.
- These two helpers live in `aseprite_mcp/core/commands.py`; new tools that touch strings/paths must use them.

**Async:** tools are `async def` but perform **no real async I/O** — they wrap synchronous subprocess calls. There are no retries, semaphores, or async-specific concerns; do not introduce `asyncio` primitives without need.

**State:** minimal and global:
- Module-level `_env_loaded` flag caches `.env` loading in `core/commands.py`.
- Single shared `mcp` FastMCP singleton.
- `preview.py` keeps per-port PID files in the OS tempdir (`<tempdir>/aseprite_mcp_preview_<port>.pid`); Windows kill uses `taskkill`, POSIX uses SIGTERM.
- Otherwise each tool is stateless: every call re-invokes Aseprite from scratch. There is no session/cache state to thread through tools.

**Naming:** modules = one noun domain (`palette.py`), tools = `verb_noun[_at]` where `_at` variants target a specific layer+frame. Private helpers prefixed with `_` (`_parse_hex_color`, `_layout_to_lua`, `_parse_layer_frame_ranges`).

## Important Files

| File | Why it matters |
|------|----------------|
| `aseprite_mcp/__init__.py` | `FastMCP("aseprite")` singleton, `__version__` |
| `aseprite_mcp/__main__.py` | stdio server entry point |
| `aseprite_mcp/core/commands.py` | `AsepriteCommand.execute_lua_script` / `run_command`, `lua_escape`, `reject_traversal`, `.env` loader — the only Aseprite-facing code |
| `aseprite_mcp/tools/__init__.py` | Imports all tool modules (registration side-effects); new tool modules must be added here |
| `pyproject.toml` / `uv.lock` | uv dependency pins; runtime deps: `httpx`, `mcp[cli]>=1.6.0`, `python-dotenv` |
| `sample.env` | Documents the `ASEPRITE_PATH` env contract |
| `README.md` | Client configs (OpenCode/Claude Desktop/Cursor), tool reference tables, project structure |

## Runtime/Tooling Preferences

- **Runtime:** Python ≥ 3.13 (`.python-version` = 3.13, `requires-python = ">=3.13"`).
- **Package manager:** uv only — `uv sync` / `uv run`; `uv.lock` is the source of truth for runtime deps.
- **MCP framework:** FastMCP (`from mcp.server.fastmcp import FastMCP`) over stdio transport.
- **External requirement:** Aseprite must be installed locally, discoverable via `ASEPRITE_PATH` env var or PATH.
- Tests use pytest but pytest is not in `uv.lock`; install dev tools explicitly (`uv pip install -r requirements.txt`) when test tooling is missing.

## Testing & QA

- **Framework:** pytest, class-grouped style (`class TestXxx` / `def test_xxx`), plain `assert` statements.
- **No shared infrastructure:** no `conftest.py`, no fixtures, no parametrization, no mocks (`unittest.mock`/`monkeypatch`), no async runners (`pytest.mark.anyio`/`asyncio.run`). Async functions are only asserted as coroutines via `asyncio.iscoroutinefunction`.
- **Two test kinds:**
  1. Import/callability smoke tests per tool module — assert tools import cleanly and are callable/coroutine functions (no live Aseprite connection needed).
  2. Pure unit tests of private helpers: `_parse_hex_color`, `_layout_to_lua`, `_data_format_to_lua`, `_parse_layer_frame_ranges`, `_parse_overlap_pairs`, `lua_escape`, `reject_traversal`.
- **Coverage expectations:** tests must pass with `uv run pytest tests/`. There is no coverage threshold configured.
- Known warts to respect, not replicate: `_parse_hex_color` tests are copy-pasted across `test_slice.py`/`test_palette.py`/`test_drawing.py`/`test_app.py`, and `import pytest` appears unused in several files. Prefer adding tests to the module's existing test file in the same style.
- No integration tests exercise tools through a real MCP client or mock Aseprite; manual verification is done by running the server (`uv run -m aseprite_mcp`) against a real Aseprite install.
