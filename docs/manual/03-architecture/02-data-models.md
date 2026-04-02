---
title: Data Models
section: 03-architecture
order: 2
generated: 2026-04-03T01:30:01.225818
---
# Data Models

Key data structures and models used in the project.


## Classes from Pattern extractor for identifying workflow patterns from parsed logs.

### `PatternExtractor`

Extracts workflow patterns from parsed dialogue logs.

**Methods:**

- `__init__(self, min_confidence: float)`
  - Initialize extractor.
- `extract(self, log: DialogueLog) -> list[Pattern]`
  - Extract patterns from a parsed dialogue log.
- `deduplicate(self, patterns: list[Pattern]) -> list[Pattern]`
  - Remove duplicate patterns based on similarity.


## Classes from Generator engine for producing MCP servers from patterns.

### `ToolSpec`

Specification for a generated tool.


### `GeneratedFile`

A generated file.


### `GeneratedMCP`

Result of MCP generation.

**Methods:**

- `to_dict(self) -> dict[str, Any]`
  - Convert to dictionary.

### `GeneratorEngine`

Engine for generating MCP servers from patterns.

**Methods:**

- `__init__(self, templates_dir: Path | None)`
  - Initialize generator engine.
- `generate(self, pattern: Pattern, output_dir: Path | str, include_tests: bool, include_docs: bool) -> GeneratedMCP`
  - Generate a complete MCP server from a pattern.
- `generate_preview(self, pattern: Pattern) -> dict[str, str]`
  - Generate a preview of files without writing to disk.
- `write_files(self, generated: GeneratedMCP) -> list[Path]`
  - Write generated files to disk.


## Classes from Validator for generated MCP code.

### `ValidationError`

A validation error.

**Methods:**

- `to_dict(self) -> dict[str, Any]`
  - Convert to dictionary.

### `ValidationResult`

Result of validation.

**Methods:**

- `to_dict(self) -> dict[str, Any]`
  - Convert to dictionary.

### `Validator`

Validator for generated MCP code.

**Methods:**

- `validate(self, generated: GeneratedMCP) -> ValidationResult`
  - Validate a generated MCP.
- `validate_path(self, mcp_path: Path | str) -> ValidationResult`
  - Validate an MCP at a given path.


## Classes from Pattern data models.

### `Trigger`

A trigger condition for a pattern.

**Methods:**

- `to_dict(self) -> dict[str, Any]`
  - Convert to dictionary.
- `from_dict(cls, data: dict[str, Any]) -> 'Trigger'`
  - Create from dictionary.

### `Input`

An input parameter for a pattern.

**Methods:**

- `to_dict(self) -> dict[str, Any]`
  - Convert to dictionary.
- `from_dict(cls, data: dict[str, Any]) -> 'Input'`
  - Create from dictionary.

### `Output`

An output produced by a pattern.

**Methods:**

- `to_dict(self) -> dict[str, Any]`
  - Convert to dictionary.
- `from_dict(cls, data: dict[str, Any]) -> 'Output'`
  - Create from dictionary.

### `Step`

A workflow step in a pattern.

**Methods:**

- `to_dict(self) -> dict[str, Any]`
  - Convert to dictionary.
- `from_dict(cls, data: dict[str, Any]) -> 'Step'`
  - Create from dictionary.

### `Pattern`

A reproducible workflow pattern extracted from logs.

**Methods:**

- `to_dict(self) -> dict[str, Any]`
  - Convert to dictionary for YAML serialization.
- `from_dict(cls, data: dict[str, Any]) -> 'Pattern'`
  - Create from dictionary.


## Classes from Scoring data models.

### `ScoreWeights`

Configurable weights for pattern scoring.

**Methods:**

- `to_dict(self) -> dict[str, float]`
  - Convert to dictionary.
- `from_dict(cls, data: dict[str, float]) -> 'ScoreWeights'`
  - Create from dictionary.

### `ScoredPattern`

A pattern with buildability scores.

**Methods:**

- `calculate_buildability(self, weights: ScoreWeights | None) -> float`
  - Calculate buildability score from individual scores.
- `to_dict(self) -> dict[str, Any]`
  - Convert to dictionary.


## Classes from Log parser for markdown dialogue logs.

### `Turn`

A single turn in a dialogue (user or assistant).

**Methods:**

- `to_dict(self) -> dict[str, Any]`
  - Convert to dictionary.

### `Session`

A logical session of related turns.

**Methods:**

- `to_dict(self) -> dict[str, Any]`
  - Convert to dictionary.

### `DialogueLog`

Parsed dialogue log.

**Methods:**

- `to_dict(self) -> dict[str, Any]`
  - Convert to dictionary.

### `LogParser`

Parser for markdown dialogue logs.

**Methods:**

- `parse(self, log_path: Path | str) -> DialogueLog`
  - Parse a markdown log file into structured dialogue.
- `parse_content(self, content: str, source_path: str) -> DialogueLog`
  - Parse log content directly.
- `extract_turns(self, content: str) -> list[Turn]`
  - Extract user/assistant turns from log content.
- `identify_sessions(self, turns: list[Turn], content: str) -> list[Session]`
  - Group turns into logical sessions.


## Classes from Scoring engine for evaluating pattern buildability.

### `ScoringEngine`

Engine for scoring patterns on buildability.

**Methods:**

- `__init__(self, weights: ScoreWeights | None)`
  - Initialize scoring engine.
- `score(self, pattern: Pattern) -> ScoredPattern`
  - Score a single pattern for buildability.
- `rank(self, patterns: list[Pattern]) -> list[ScoredPattern]`
  - Score and rank patterns by buildability.
- `recommend(self, patterns: list[Pattern], top_n: int, threshold: float) -> list[ScoredPattern]`
  - Get top recommendations for building.


## Classes from Learning engine for adjusting scores based on build outcomes.

### `OutcomeStats`

Statistics for build outcomes.

**Methods:**

- `to_dict(self) -> dict[str, Any]`
  - Convert to dictionary.

### `ScoreAdjustment`

Adjustment to apply to a pattern score.

**Methods:**

- `to_dict(self) -> dict[str, Any]`
  - Convert to dictionary.

### `LearningEngine`

Engine for learning from build outcomes and adjusting scores.

**Methods:**

- `__init__(self)`
  - Initialize learning engine.
- `calculate_stats(self, outcomes: list[dict[str, Any]]) -> OutcomeStats`
  - Calculate statistics from outcome history.
- `calculate_adjustment(self, outcomes: list[dict[str, Any]]) -> tuple[float, str]`
  - Calculate score adjustment factor from outcomes.
- `adjust_score(self, scored: ScoredPattern, outcomes: list[dict[str, Any]]) -> ScoreAdjustment`
  - Adjust a pattern's buildability score based on outcomes.
- `suggest_weight_adjustments(self, outcomes: list[dict[str, Any]], current_weights: ScoreWeights) -> dict[str, float]`
  - Suggest weight adjustments based on outcome patterns.
- `rank_with_learning(self, scored_patterns: list[ScoredPattern], outcomes_by_pattern: dict[str, list[dict[str, Any]]]) -> list[tuple[ScoredPattern, ScoreAdjustment]]`
  - Rank patterns with learning adjustments applied.


## Classes from Minna Memory synchronization for pattern storage.

### `MinnaSync`

Synchronize patterns with Minna Memory for cross-session persistence.

**Methods:**

- `__init__(self, memory_client: Any | None)`
  - Initialize Minna sync.
- `is_available(self) -> bool`
  - Check if Minna Memory is available.
- `sync_pattern(self, pattern: Pattern) -> bool`
  - Sync a pattern to Minna Memory.
- `sync_scored(self, scored: ScoredPattern) -> bool`
  - Sync a scored pattern to Minna Memory.
- `record_outcome(self, pattern_id: str, outcome: str, notes: str | None) -> bool`
  - Record a build outcome in Minna Memory.
- `get_outcomes(self, pattern_id: str) -> list[dict[str, Any]]`
  - Get build outcomes from Minna Memory.
- `search_patterns(self, query: str, limit: int) -> list[dict[str, Any]]`
  - Search patterns in Minna Memory.
- `find_similar(self, pattern: Pattern) -> list[dict[str, Any]]`
  - Find similar patterns in Minna Memory.


## Classes from File-based pattern storage.

### `PatternStore`

File-based store for patterns using YAML.

**Methods:**

- `__init__(self, store_path: Path | str | None)`
  - Initialize pattern store.
- `store(self, pattern: Pattern, scores: dict[str, float] | None) -> Path`
  - Store a pattern to disk.
- `store_scored(self, scored: ScoredPattern) -> Path`
  - Store a scored pattern with its scores.
- `get(self, pattern_id: str) -> Pattern | None`
  - Get a pattern by ID.
- `list_all(self) -> list[Pattern]`
  - List all stored patterns.
- `search(self, query: str | None, category: str | None, tags: list[str] | None, limit: int) -> list[Pattern]`
  - Search patterns by query, category, or tags.
- `delete(self, pattern_id: str) -> bool`
  - Delete a pattern.
- `exists(self, pattern_id: str) -> bool`
  - Check if a pattern exists.
- `count(self) -> int`
  - Count stored patterns.
- `record_outcome(self, pattern_id: str, outcome: str, notes: str | None) -> None`
  - Record a build outcome for learning.
- `get_outcomes(self, pattern_id: str | None) -> list[dict[str, Any]]`
  - Get build outcomes.

---

## See Also

- [Getting Started](../01-user-guide/01-getting-started.md)
- [Installation](../01-user-guide/02-installation.md)
- [Quick Start](../01-user-guide/03-quick-start.md)
- [Worked Examples](../01-user-guide/04-worked-examples.md)
- [Overview](../02-api-reference/01-overview.md)

---

Previous: [System Overview](01-system-overview.md)