# unit

> Last updated: 2026-02-01

Unit tests for individual components in isolation — 8 test files with 93 test functions covering all core modules.

## Contents

| File | About |
|------|-------|
| `test_log_parser.py` | Tests LogParser markdown parsing and turn extraction (8 tests) |
| `test_pattern_extractor.py` | Tests pattern detection, deduplication, and trigger extraction (9 tests) |
| `test_scoring_engine.py` | Tests pattern scoring, ranking, and recommendations (10 tests) |
| `test_generator.py` | Tests MCP code generation and file creation (12 tests) |
| `test_validator.py` | Tests Python syntax and pyproject.toml validation (8 tests) |
| `test_pattern_store.py` | Tests pattern persistence, search, and retrieval (15 tests) |
| `test_learning.py` | Tests outcome tracking and score adjustment logic (15 tests) |
| `test_minna_sync.py` | Tests Minna Memory integration for pattern persistence (16 tests) |

## Code Structure

### `test_log_parser.py`

| Type | Name | Description |
|------|------|-------------|
| function | `test_parse_markdown` | Verifies markdown log files are parsed into structured data |
| function | `test_parse_content_directly` | Tests parsing from string content instead of file |
| function | `test_extract_turns` | Validates user/assistant turn extraction from dialogue |
| function | `test_handles_empty_log` | Ensures graceful handling of empty input |
| function | `test_file_not_found` | Tests error handling for missing files |
| function | `test_extracts_tool_usage` | Verifies tool invocation detection in logs |
| function | `test_identifies_sessions` | Tests session boundary detection |
| function | `test_metadata_populated` | Confirms metadata fields are populated after parsing |

### `test_pattern_extractor.py`

| Type | Name | Description |
|------|------|-------------|
| function | `test_find_patterns` | Validates pattern discovery from parsed log data |
| function | `test_find_patterns_with_tool_usage` | Tests pattern extraction when tool usage markers are present |
| function | `test_extract_triggers` | Verifies trigger condition extraction from patterns |
| function | `test_deduplicates` | Ensures duplicate patterns are merged |
| function | `test_min_confidence_filter` | Tests confidence threshold filtering |
| function | `test_pattern_has_workflow_steps` | Validates step extraction in discovered patterns |
| function | `test_pattern_id_generation` | Verifies unique ID generation for patterns |

### `test_scoring_engine.py`

| Type | Name | Description |
|------|------|-------------|
| function | `test_calculate_score` | Tests basic score calculation for a pattern |
| function | `test_rank_patterns` | Validates ranking of multiple patterns by score |
| function | `test_custom_weights` | Tests scoring with custom weight configurations |
| function | `test_recommendation_build` | Verifies "build" recommendation for high-scoring patterns |
| function | `test_recommendation_skip` | Verifies "skip" recommendation for low-scoring patterns |
| function | `test_recommend_top_n` | Tests top-N pattern selection |
| function | `test_recommend_threshold` | Tests minimum score threshold filtering |
| function | `test_frequency_scoring` | Validates frequency-based score component |

### `test_generator.py`

| Type | Name | Description |
|------|------|-------------|
| function | `test_generate_creates_files` | Verifies MCP server file creation |
| function | `test_generate_preview` | Tests preview mode without file writing |
| function | `test_write_files` | Validates file content writing to disk |
| function | `test_package_name_generation` | Tests Python package name derivation from pattern name |
| function | `test_package_name_handles_special_chars` | Ensures special characters are handled in naming |
| function | `test_tools_from_pattern` | Validates MCP tool generation from pattern steps |
| function | `test_inputs_to_params` | Tests input-to-parameter conversion for tool schemas |
| function | `test_infer_dependencies` | Verifies dependency inference from pattern content |

### `test_validator.py`

| Type | Name | Description |
|------|------|-------------|
| function | `test_valid_python_passes` | Confirms valid Python syntax passes validation |
| function | `test_invalid_syntax_fails` | Ensures invalid syntax is caught |
| function | `test_valid_pyproject_passes` | Tests pyproject.toml validation for correct format |
| function | `test_missing_project_name_fails` | Verifies missing required fields are detected |
| function | `test_validate_path` | Tests path-based validation |
| function | `test_validate_nonexistent_path` | Tests error handling for missing paths |

### `test_pattern_store.py`

| Type | Name | Description |
|------|------|-------------|
| function | `test_store_pattern_creates_file` | Verifies YAML file creation on store |
| function | `test_get_pattern` | Tests single pattern retrieval by ID |
| function | `test_get_nonexistent_returns_none` | Validates graceful handling of missing patterns |
| function | `test_list_all` | Tests listing all stored patterns |
| function | `test_search_by_category` | Validates category-based search |
| function | `test_search_by_query` | Tests text query search |
| function | `test_search_by_tags` | Validates tag-based filtering |
| function | `test_search_empty_results` | Tests empty result handling |
| function | `test_delete_pattern` | Verifies pattern deletion from store |
| function | `test_delete_nonexistent` | Tests deleting a non-existent pattern |
| function | `test_count` | Validates pattern count |
| function | `test_store_scored_pattern` | Tests storing patterns with scores |

### `test_learning.py`

| Type | Name | Description |
|------|------|-------------|
| function | `test_calculate_stats_empty` | Tests stats calculation with no outcomes |
| function | `test_calculate_stats_all_success` | Validates stats for all-success outcomes |
| function | `test_calculate_stats_mixed` | Tests mixed success/failure statistics |
| function | `test_calculate_adjustment_success_boost` | Verifies score boost for successful builds |
| function | `test_calculate_adjustment_failure_penalty` | Tests score penalty for failed builds |
| function | `test_calculate_adjustment_decay` | Validates time-based score decay |
| function | `test_calculate_adjustment_clamped` | Ensures adjustments stay within bounds |
| function | `test_adjust_score` | Tests end-to-end score adjustment |

### `test_minna_sync.py`

| Type | Name | Description |
|------|------|-------------|
| function | `test_is_available_with_client` | Tests Minna availability check with client present |
| function | `test_is_available_cached` | Validates caching of availability status |
| function | `test_is_available_without_client` | Tests fallback when client unavailable |
| function | `test_is_available_client_error` | Verifies graceful error handling |
| function | `test_sync_pattern` | Tests pattern synchronization to Minna |
| function | `test_sync_pattern_unavailable` | Tests sync when Minna is unavailable |
| function | `test_sync_scored` | Validates scored pattern synchronization |
| function | `test_record_outcome` | Tests build outcome recording in Minna |
