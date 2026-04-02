# e2e

> Last updated: 2026-02-01

End-to-end tests validating MCP tool interfaces and complete user workflows — 4 test files with 53 test functions.

## Contents

| File | About |
|------|-------|
| `test_mcp_tools.py` | Tests core MCP tools: analyze_log, list_patterns, score_patterns, get_pattern (11 tests) |
| `test_generator_tools.py` | Tests generation MCP tools: generate_preview, generate_mcp, validate_mcp (10 tests) |
| `test_library_tools.py` | Tests library MCP tools: store_pattern, search_patterns, learn_outcome, suggest_similar (14 tests) |
| `test_pipeline_tools.py` | Tests pipeline MCP tools: run_pipeline, compare_existing, batch_analyze (18 tests) |

## Code Structure

### `test_mcp_tools.py`

| Type | Name | Description |
|------|------|-------------|
| class | `TestAnalyzeLogTool` | Tests for the analyze_log MCP tool |
| function | `test_analyze_log_success` | Validates successful log analysis |
| function | `test_analyze_log_file_not_found` | Tests error handling for missing log files |
| function | `test_analyze_log_min_confidence` | Tests confidence threshold parameter |
| class | `TestListPatternsTool` | Tests for the list_patterns MCP tool |
| class | `TestScorePatternsTool` | Tests for the score_patterns MCP tool |
| class | `TestGetPatternTool` | Tests for the get_pattern MCP tool |
| class | `TestRealLogFile` | Tests using actual project log files |

### `test_generator_tools.py`

| Type | Name | Description |
|------|------|-------------|
| class | `TestGeneratePreviewTool` | Tests for generate_preview MCP tool |
| class | `TestGenerateMCPTool` | Tests for generate_mcp MCP tool |
| class | `TestValidateMCPTool` | Tests for validate_mcp MCP tool |
| class | `TestFullGenerationWorkflow` | End-to-end generation workflow from analysis to generation |

### `test_library_tools.py`

| Type | Name | Description |
|------|------|-------------|
| class | `TestStorePatternTool` | Tests for store_pattern MCP tool |
| class | `TestSearchPatternsTool` | Tests for search_patterns MCP tool |
| class | `TestLearnOutcomeTool` | Tests for learn_outcome MCP tool including score adjustments |
| class | `TestSuggestSimilarTool` | Tests for suggest_similar MCP tool |

### `test_pipeline_tools.py`

| Type | Name | Description |
|------|------|-------------|
| class | `TestRunPipelineTool` | Tests for run_pipeline MCP tool including auto-generate |
| class | `TestCompareExistingTool` | Tests for compare_existing MCP tool |
| class | `TestBatchAnalyzeTool` | Tests for batch_analyze including merge and dedup |
| class | `TestPipelineIntegration` | Full pipeline integration scenarios |
