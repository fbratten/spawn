# mcp_builder_mcp

> Last updated: 2026-02-01

Core Python package implementing the pattern MCP builder server — a meta-MCP that analyzes logs for workflow patterns, scores them, and generates new MCP servers.

## Contents

| File | About |
|------|-------|
| `__init__.py` | Package initialization exporting 17 public classes/functions including PatternExtractor, GeneratorEngine, Validator, models, LogParser, ScoringEngine, PatternStore, MinnaSync, and LearningEngine |
| `server.py` | FastMCP server implementing 17 MCP tools for pattern analysis, generation, and library management (~1,500+ LOC) |

## Code Structure

### `__init__.py`

| Type | Name | Description |
|------|------|-------------|
| constant | `__version__` | Package version string ("0.1.0") |

### `server.py`

| Type | Name | Description |
|------|------|-------------|
| constant | `mcp` | FastMCP server instance ("pattern-mcp") |
| constant | `_session_patterns` | In-memory list of patterns for the current session |
| constant | `_session_store` | PatternStore instance for persistent storage |
| constant | `EXISTING_MCP_TOOLS` | Hardcoded list of 7 known MCP tools with keywords for comparison |
| function | `_get_store()` | Initialize or retrieve the PatternStore singleton |
| function | `analyze_log()` | [DEPRECATED] Mechanical pattern extraction from logs |
| function | `get_log_content()` | Parse log and return raw data for AI analysis |
| function | `find_recurring_themes()` | Frequency analysis of tools, actions, and files in logs |
| function | `define_pattern()` | Create a pattern from AI-identified workflow |
| function | `list_patterns()` | List all patterns in session or store |
| function | `score_patterns()` | Score patterns for buildability using ScoringEngine |
| function | `_recommendation_reason()` | Generate human-readable recommendation text |
| function | `get_pattern()` | Retrieve a single pattern by ID |
| function | `generate_preview()` | Preview generated MCP code without writing files |
| function | `generate_mcp()` | Generate complete MCP server from a pattern |
| function | `validate_mcp()` | Validate MCP server syntax and structure |
| function | `store_pattern()` | Save pattern to persistent library |
| function | `search_patterns()` | Search local store and Minna memory |
| function | `learn_outcome()` | Record and learn from build outcomes |
| function | `suggest_similar()` | Find similar patterns in the library |
| function | `_calculate_similarity()` | Calculate similarity score between two patterns |
| function | `run_pipeline()` | Full analyze-score-generate pipeline |
| function | `compare_existing()` | Compare pattern with known MCP ecosystem tools |
| function | `batch_analyze()` | Batch process multiple log files |
| function | `_merge_similar_patterns()` | Merge patterns exceeding similarity threshold |
| function | `main()` | Entry point to run the MCP server |
