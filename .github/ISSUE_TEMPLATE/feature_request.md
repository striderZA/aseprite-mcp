---
name: Feature request
about: Suggest a new tool or capability
title: ''
labels: enhancement
assignees: ''

---

**What Aseprite API feature should be exposed?**
Which Aseprite scripting API method or object should this tool wrap?
(e.g. `img:floodFill()`, `app.command.ExportSpriteSheet`, `sprite:close()`, slices)

**Proposed MCP tool signature**
```python
@mcp.tool()
async def my_new_tool(param1: str, param2: int = 42) -> str:
    """What this tool does."""
```

**Use case**
Describe when an AI agent would use this tool. What problem does it solve?

**Alternatives considered**
Any workarounds you've found using existing tools.

**Additional context**
Links to Aseprite API docs, related issues, or examples.
