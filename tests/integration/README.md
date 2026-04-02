# integration

> Last updated: 2026-02-01

Integration tests validating multi-component workflows — 2 test files with 10 test functions.

## Contents

| File | About |
|------|-------|
| `test_analyze_pipeline.py` | Tests full Parser to Extractor to Scorer pipeline (5 tests) |
| `test_generate_pipeline.py` | Tests Pattern to Generate to Validate pipeline (5 tests) |

## Code Structure

### `test_analyze_pipeline.py`

| Type | Name | Description |
|------|------|-------------|
| function | `test_full_pipeline` | Validates end-to-end analysis from log to scored patterns |
| function | `test_full_pipeline_with_tool_markers` | Tests pipeline with tool usage markers in logs |
| function | `test_pipeline_with_store` | Verifies pipeline with PatternStore integration |
| function | `test_patterns_save_and_load` | Tests pattern persistence across pipeline runs |

### `test_generate_pipeline.py`

| Type | Name | Description |
|------|------|-------------|
| function | `test_full_generation_pipeline` | Validates end-to-end generation from pattern to MCP server |
| function | `test_generated_server_has_structure` | Verifies generated server directory structure |
| function | `test_generated_tests_structure` | Validates generated test file structure |
| function | `test_generated_python_syntax_valid` | Confirms all generated Python files have valid syntax |
| function | `test_pyproject_is_valid_toml` | Verifies generated pyproject.toml is valid TOML |
