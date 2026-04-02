# tests

> Last updated: 2026-02-01

Root test directory containing shared test configuration, fixtures, and 156 tests organized across unit, integration, and end-to-end categories.

## Contents

| File | About |
|------|-------|
| `__init__.py` | Package initialization marker (empty) |
| `.gitkeep` | Git placeholder |
| `conftest.py` | Pytest shared fixtures and configuration — defines 12 fixtures for logs, patterns, sessions, stores, and weights |

## Code Structure

### `conftest.py`

| Type | Name | Description |
|------|------|-------------|
| function | `sample_log_path` | Fixture returning path to sample log file |
| function | `sample_pattern` | Fixture returning a pre-built Pattern instance |
| function | `sample_scored_pattern` | Fixture returning a ScoredPattern with scores |
| function | `tmp_store` | Fixture providing a temporary PatternStore |
| function | `score_weights` | Fixture returning default ScoreWeights |
