---
title: Quick Start
section: 01-user-guide
order: 3
generated: 2026-04-03T01:21:31.021722
---
# Quick Start

```bash
# Install
pip install -e ".[dev]"

# Run as MCP server
python -m mcp_builder_mcp.server

# Add to .mcp.json
{
  "spawn": {
    "command": "bash",
    "args": ["-c", "cd /path/to/spawn && .venv/bin/python -m mcp_builder_mcp.server"]
  }
}
```

---

## See Also

- [Overview](../02-api-reference/01-overview.md)
- [System Overview](../03-architecture/01-system-overview.md)
- [Data Models](../03-architecture/02-data-models.md)
- [Configuration](../04-reference/01-configuration.md)
- [Error Handling](../04-reference/02-error-handling.md)

---

Previous: [Installation](02-installation.md) | Next: [Worked Examples](04-worked-examples.md)