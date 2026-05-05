# Aseprite MCP Tools

A Python module that serves as an MCP server for interacting with the Aseprite API

## Installation

### Prerequisites
- Python 3.13+
- `uv` package manager

### Installation:

Requires [Aseprite](https://www.aseprite.org) installed with `ASEPRITE_PATH` pointing to the binary.

**macOS:**
```json
{
  "mcpServers": {
    "aseprite": {
      "command": "/opt/homebrew/bin/uv",
      "args": ["--directory", "/path/to/repo", "run", "-m", "aseprite_mcp"]
    }
  }
}
```

**Windows:**
```json
{
  "mcpServers": {
    "aseprite": {
      "command": "uv",
      "args": ["--directory", "C:\\path\\to\\repo", "run", "-m", "aseprite_mcp"]
    }
  }
}
```

**Linux:**
```json
{
  "mcpServers": {
    "aseprite": {
      "command": "uv",
      "args": ["--directory", "/path/to/repo", "run", "-m", "aseprite_mcp"]
    }
  }
}
```
