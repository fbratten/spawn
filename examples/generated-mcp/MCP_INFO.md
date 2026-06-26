# MCP_INFO

## Server

`issue-triage-mcp`

## Purpose

Demonstrates the end state of a generated MCP server: a repeated agent-session workflow has been codified into explicit tools that can be called again by an MCP-compatible AI client.

## Tools

| Tool | Purpose |
|------|---------|
| `classify_issue` | Classify an issue into a small triage category. |
| `create_triage_checklist` | Produce category-specific follow-up steps. |
| `write_triage_report` | Compose the classification and checklist into a Markdown report. |

## Integration note

This directory is a small repository sample, not a published package. Full generated outputs from `spawn` may include tests, richer README content, and project-specific tool implementations.
