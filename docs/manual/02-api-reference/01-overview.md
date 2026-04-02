---
title: Overview
section: 02-api-reference
order: 1
generated: 2026-04-03T01:21:31.066471
---
# API Overview

This section documents the available API endpoints and tools.




## Classes


### `PatternExtractor`

Extracts workflow patterns from parsed dialogue logs.


**Methods:**

| Method | Description |
|--------|-------------|
| `__init__` | Initialize extractor. |
| `extract` | Extract patterns from a parsed dialogue log. |
| `deduplicate` | Remove duplicate patterns based on similarity. |



### `ToolSpec`

Specification for a generated tool.




### `GeneratedFile`

A generated file.




### `GeneratedMCP`

Result of MCP generation.


**Methods:**

| Method | Description |
|--------|-------------|
| `to_dict` | Convert to dictionary. |



### `GeneratorEngine`

Engine for generating MCP servers from patterns.


**Methods:**

| Method | Description |
|--------|-------------|
| `__init__` | Initialize generator engine. |
| `generate` | Generate a complete MCP server from a pattern. |
| `generate_preview` | Generate a preview of files without writing to disk. |
| `write_files` | Write generated files to disk. |



### `ValidationError`

A validation error.


**Methods:**

| Method | Description |
|--------|-------------|
| `to_dict` | Convert to dictionary. |



### `ValidationResult`

Result of validation.


**Methods:**

| Method | Description |
|--------|-------------|
| `to_dict` | Convert to dictionary. |



### `Validator`

Validator for generated MCP code.


**Methods:**

| Method | Description |
|--------|-------------|
| `validate` | Validate a generated MCP. |
| `validate_path` | Validate an MCP at a given path. |



### `Trigger`

A trigger condition for a pattern.


**Methods:**

| Method | Description |
|--------|-------------|
| `to_dict` | Convert to dictionary. |
| `from_dict` | Create from dictionary. |



### `Input`

An input parameter for a pattern.


**Methods:**

| Method | Description |
|--------|-------------|
| `to_dict` | Convert to dictionary. |
| `from_dict` | Create from dictionary. |



### `Output`

An output produced by a pattern.


**Methods:**

| Method | Description |
|--------|-------------|
| `to_dict` | Convert to dictionary. |
| `from_dict` | Create from dictionary. |



### `Step`

A workflow step in a pattern.


**Methods:**

| Method | Description |
|--------|-------------|
| `to_dict` | Convert to dictionary. |
| `from_dict` | Create from dictionary. |



### `Pattern`

A reproducible workflow pattern extracted from logs.


**Methods:**

| Method | Description |
|--------|-------------|
| `to_dict` | Convert to dictionary for YAML serialization. |
| `from_dict` | Create from dictionary. |



### `ScoreWeights`

Configurable weights for pattern scoring.


**Methods:**

| Method | Description |
|--------|-------------|
| `to_dict` | Convert to dictionary. |
| `from_dict` | Create from dictionary. |



### `ScoredPattern`

A pattern with buildability scores.


**Methods:**

| Method | Description |
|--------|-------------|
| `calculate_buildability` | Calculate buildability score from individual scores. |
| `to_dict` | Convert to dictionary. |



### `Turn`

A single turn in a dialogue (user or assistant).


**Methods:**

| Method | Description |
|--------|-------------|
| `to_dict` | Convert to dictionary. |



### `Session`

A logical session of related turns.


**Methods:**

| Method | Description |
|--------|-------------|
| `to_dict` | Convert to dictionary. |



### `DialogueLog`

Parsed dialogue log.


**Methods:**

| Method | Description |
|--------|-------------|
| `to_dict` | Convert to dictionary. |



### `LogParser`

Parser for markdown dialogue logs.


**Methods:**

| Method | Description |
|--------|-------------|
| `parse` | Parse a markdown log file into structured dialogue. |
| `parse_content` | Parse log content directly. |
| `extract_turns` | Extract user/assistant turns from log content. |
| `identify_sessions` | Group turns into logical sessions. |



### `ScoringEngine`

Engine for scoring patterns on buildability.


**Methods:**

| Method | Description |
|--------|-------------|
| `__init__` | Initialize scoring engine. |
| `score` | Score a single pattern for buildability. |
| `rank` | Score and rank patterns by buildability. |
| `recommend` | Get top recommendations for building. |



### `OutcomeStats`

Statistics for build outcomes.


**Methods:**

| Method | Description |
|--------|-------------|
| `to_dict` | Convert to dictionary. |



### `ScoreAdjustment`

Adjustment to apply to a pattern score.


**Methods:**

| Method | Description |
|--------|-------------|
| `to_dict` | Convert to dictionary. |



### `LearningEngine`

Engine for learning from build outcomes and adjusting scores.


**Methods:**

| Method | Description |
|--------|-------------|
| `__init__` | Initialize learning engine. |
| `calculate_stats` | Calculate statistics from outcome history. |
| `calculate_adjustment` | Calculate score adjustment factor from outcomes. |
| `adjust_score` | Adjust a pattern's buildability score based on outcomes. |
| `suggest_weight_adjustments` | Suggest weight adjustments based on outcome patterns. |
| `rank_with_learning` | Rank patterns with learning adjustments applied. |



### `MinnaSync`

Synchronize patterns with Minna Memory for cross-session persistence.


**Methods:**

| Method | Description |
|--------|-------------|
| `__init__` | Initialize Minna sync. |
| `is_available` | Check if Minna Memory is available. |
| `sync_pattern` | Sync a pattern to Minna Memory. |
| `sync_scored` | Sync a scored pattern to Minna Memory. |
| `record_outcome` | Record a build outcome in Minna Memory. |
| `get_outcomes` | Get build outcomes from Minna Memory. |
| `search_patterns` | Search patterns in Minna Memory. |
| `find_similar` | Find similar patterns in Minna Memory. |



### `PatternStore`

File-based store for patterns using YAML.


**Methods:**

| Method | Description |
|--------|-------------|
| `__init__` | Initialize pattern store. |
| `store` | Store a pattern to disk. |
| `store_scored` | Store a scored pattern with its scores. |
| `get` | Get a pattern by ID. |
| `list_all` | List all stored patterns. |
| `search` | Search patterns by query, category, or tags. |
| `delete` | Delete a pattern. |
| `exists` | Check if a pattern exists. |
| `count` | Count stored patterns. |
| `record_outcome` | Record a build outcome for learning. |
| `get_outcomes` | Get build outcomes. |






## Functions

| Function | Description |
|----------|-------------|
| `analyze_log(log_path: str, min_confidence: float, focus_areas: list[str] | None) -> dict[str, Any]` | [DEPRECATED] Mechanical pattern extraction - use get_log_content + define_pattern instead. |
| `get_log_content(log_path: str, max_turns: int) -> dict[str, Any]` | Get raw parsed content from a log file for AI semantic analysis. |
| `find_recurring_themes(log_path: str, min_occurrences: int) -> dict[str, Any]` | Analyze a log for recurring themes that could become MCP tools. |
| `define_pattern(name: str, description: str, trigger: str, workflow_steps: list[str], category: str, tags: list[str] | None) -> dict[str, Any]` | Define a new pattern from AI semantic analysis. |
| `list_patterns(filter_by: str | None, sort_by: str, include_stored: bool) -> dict[str, Any]` | List identified patterns. |
| `score_patterns(pattern_ids: list[str] | None, threshold: float, weights: dict[str, float] | None) -> dict[str, Any]` | Score patterns for buildability. |
| `get_pattern(pattern_id: str) -> dict[str, Any]` | Get detailed information about a single pattern. |
| `generate_preview(pattern_id: str) -> dict[str, Any]` | Preview generated MCP code without writing to disk. |
| `generate_mcp(pattern_id: str, output_dir: str, include_tests: bool, include_docs: bool) -> dict[str, Any]` | Generate a complete MCP server from a pattern. |
| `validate_mcp(mcp_path: str) -> dict[str, Any]` | Validate a generated or existing MCP server. |
| `store_pattern(pattern_id: str, tags: list[str] | None, sync_to_minna: bool) -> dict[str, Any]` | Save a pattern to the persistent library. |
| `search_patterns(query: str | None, category: str | None, tags: list[str] | None, limit: int, include_minna: bool) -> dict[str, Any]` | Search the pattern library. |
| `learn_outcome(pattern_id: str, outcome: str, notes: str | None, apply_adjustment: bool) -> dict[str, Any]` | Record a build outcome for learning. |
| `suggest_similar(pattern_id: str) -> dict[str, Any]` | Find patterns similar to a given pattern. |
| `run_pipeline(log_path: str, output_dir: str | None, auto_generate: bool, min_score: float, top_n: int) -> dict[str, Any]` | Run the full pattern-to-MCP pipeline. |
| `compare_existing(pattern_id: str) -> dict[str, Any]` | Compare a pattern with existing MCP tools. |
| `batch_analyze(log_paths: list[str], merge_similar: bool, similarity_threshold: float) -> dict[str, Any]` | Analyze multiple logs in batch. |
| `main() -> None` | Run the MCP server. |
| `run_ruff(path: Path) -> ValidationResult` | Run ruff linter on generated code. |

---

## See Also

- [Getting Started](../01-user-guide/01-getting-started.md)
- [Installation](../01-user-guide/02-installation.md)
- [Quick Start](../01-user-guide/03-quick-start.md)
- [Worked Examples](../01-user-guide/04-worked-examples.md)
- [System Overview](../03-architecture/01-system-overview.md)