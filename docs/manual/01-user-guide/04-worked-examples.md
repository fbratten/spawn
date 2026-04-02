---
title: Worked Examples
section: 01-user-guide
order: 4
generated: 2026-04-03T01:30:01.131634
---
# Worked Examples

Practical examples demonstrating common usage patterns.


## From README

### Example 1

```
Session logs / transcripts
        |
        v
  PARSE (log_parser)
  Extract tool calls, AI actions, user requests
        |
        v
  EXTRACT (pattern_extractor)
  Identify recurring sequences and themes
        |
        v
  SCORE (scoring_engine)
  Rate patterns for buildability (frequency, complexity, feasibility)
        |
        v
  GENERATE (generator_engine)
  Produce complete MCP server: server.py, tools, tests, pyproject.toml
        |
        v
  VALIDATE (validator)
  Verify generated code structure and imports
        |
        v
  LEARN (learning_engine)
  Record outcomes, refine scoring weights
```

### Example 2

```
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

### Example 3

```
User: "Analyze my last session log for patterns"
AI: calls get_log_content with the log file
AI: calls find_recurring_themes to identify candidates
AI: calls define_pattern for each promising pattern
AI: calls score_patterns to rank them
AI: calls generate_mcp for the top-scoring pattern
-> Complete MCP server generated: server.py, tests, pyproject.toml, README
```

### Example 4

```
spawn/
├── src/mcp_builder_mcp/
│   ├── server.py              # FastMCP server (17 tools)
│   ├── parser/                # Log parsing (multi-format)
│   │   └── log_parser.py
│   ├── extractor/             # Pattern extraction
│   │   └── pattern_extractor.py
│   ├── scorer/                # Buildability scoring
│   │   └── scoring_engine.py
│   ├── generator/             # Code generation
│   │   ├── generator_engine.py
│   │   ├── validator.py
│   │   └── templates/         # Jinja2 templates for generated code
│   ├── store/                 # Persistence
│   │   ├── pattern_store.py   # JSON-backed pattern library
│   │   ├── learning.py        # Outcome tracking + weight refinement
│   │   └── minna_sync.py      # Optional memory integration
│   └── models/                # Data models
│       ├── pattern.py
│       └── score.py
└── tests/                     # 156 tests (unit + integration + e2e)
```

### Example 5

```
python -m pytest tests/ -v          # All 156 tests
python -m pytest tests/unit/ -v     # Unit tests
python -m pytest tests/integration/ -v
python -m pytest tests/e2e/ -v
```

---

## See Also

- [Overview](../02-api-reference/01-overview.md)
- [System Overview](../03-architecture/01-system-overview.md)
- [Data Models](../03-architecture/02-data-models.md)
- [Configuration](../04-reference/01-configuration.md)
- [Error Handling](../04-reference/02-error-handling.md)

---

Previous: [Quick Start](03-quick-start.md)