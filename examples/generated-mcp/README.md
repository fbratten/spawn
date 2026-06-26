# Generated MCP example

This directory is a compact **golden sample** of the kind of output shape `spawn` is designed to produce from a recurring AI-agent workflow pattern.

It is intentionally small and readable. The point is not to be a full product, but to make the generated-output contract concrete for people scanning the repository.

## Source pattern

A repeated session-log workflow might look like this:

```text
Read issue text -> classify the issue -> create a triage checklist -> write a short report
```

## Generated shape

A generated MCP/FastMCP server should normally include:

```text
server.py          # MCP tool surface
pyproject.toml     # package/runtime metadata
README.md          # generated server documentation
MCP_INFO.md        # MCP metadata and integration notes
tests/             # test scaffolding in full generated outputs
```

## Example tools

The sample `server.py` exposes three small tools:

- `classify_issue` — classify an issue as bug, feature, security, or ops.
- `create_triage_checklist` — create a short checklist for the classification.
- `write_triage_report` — turn classification + checklist into a report.

## Why this example exists

Without an example, `spawn` can sound abstract: logs, patterns, scoring, generation. This folder shows the intended end state: a repeated agent workflow becomes a reusable MCP server boundary.
