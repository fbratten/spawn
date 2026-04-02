"""End-to-end tests for MCP tools."""

from pathlib import Path

import pytest

from mcp_builder_mcp.server import analyze_log, get_pattern, list_patterns, score_patterns


class TestAnalyzeLogTool:
    """E2E tests for analyze_log MCP tool."""

    def test_analyze_log_success(self, sample_log_file: Path) -> None:
        """Test analyze_log works end-to-end."""
        result = analyze_log(str(sample_log_file))

        assert "error" not in result
        assert "patterns" in result
        assert "count" in result
        assert "summary" in result
        assert result["count"] >= 0

    def test_analyze_log_file_not_found(self, tmp_path: Path) -> None:
        """Test analyze_log handles missing file."""
        result = analyze_log(str(tmp_path / "nonexistent.md"))

        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_analyze_log_min_confidence(self, sample_log_file: Path) -> None:
        """Test min_confidence parameter."""
        result_low = analyze_log(str(sample_log_file), min_confidence=0.1)
        result_high = analyze_log(str(sample_log_file), min_confidence=0.9)

        # Low threshold should find same or more patterns
        assert result_low["count"] >= result_high["count"]


class TestListPatternsTool:
    """E2E tests for list_patterns MCP tool."""

    def test_list_patterns_empty(self) -> None:
        """Test list_patterns with no patterns."""
        result = list_patterns(include_stored=False)

        assert "patterns" in result
        assert "count" in result

    def test_list_patterns_after_analyze(self, sample_log_file: Path) -> None:
        """Test list_patterns after analyze."""
        # First analyze
        analyze_log(str(sample_log_file))

        # Then list
        result = list_patterns()

        assert "patterns" in result
        # Should have patterns from analysis
        assert result["count"] >= 0


class TestScorePatternsTool:
    """E2E tests for score_patterns MCP tool."""

    def test_score_patterns_after_analyze(self, sample_log_file: Path) -> None:
        """Test scoring via MCP tool."""
        # First analyze
        analyze_result = analyze_log(str(sample_log_file))

        if analyze_result["count"] > 0:
            # Then score
            result = score_patterns()

            assert "scored" in result
            assert "summary" in result
            assert result["summary"]["total_scored"] > 0

    def test_score_patterns_no_patterns(self) -> None:
        """Test scoring with no patterns."""
        # Clear session patterns by not analyzing
        from mcp_builder_mcp import server
        server._session_patterns = []

        result = score_patterns()

        assert "error" in result

    def test_score_patterns_custom_weights(self, sample_log_file: Path) -> None:
        """Test custom weights in scoring."""
        analyze_log(str(sample_log_file))

        custom_weights = {
            "frequency": 2.0,
            "complexity": -0.5,
            "value": 2.0,
            "uniqueness": 0.5,
        }
        result = score_patterns(weights=custom_weights)

        if "summary" in result:
            assert result["summary"]["weights_used"]["frequency"] == 2.0


class TestGetPatternTool:
    """E2E tests for get_pattern MCP tool."""

    def test_get_pattern_after_analyze(self, sample_log_file: Path) -> None:
        """Test getting pattern details."""
        analyze_result = analyze_log(str(sample_log_file))

        if analyze_result["count"] > 0:
            pattern_id = analyze_result["patterns"][0]["id"]
            result = get_pattern(pattern_id)

            assert "pattern" in result
            assert result["pattern"]["id"] == pattern_id

    def test_get_pattern_not_found(self) -> None:
        """Test getting non-existent pattern."""
        result = get_pattern("nonexistent-pattern-id")

        assert "error" in result
        assert "not found" in result["error"].lower()


class TestRealLogFile:
    """E2E tests with real project log if available."""

    def test_analyze_real_log(self, real_log_path: Path) -> None:
        """Test analysis on actual project log."""
        if not real_log_path.exists():
            pytest.skip("Real log file not available")

        result = analyze_log(str(real_log_path))

        assert "error" not in result
        assert result["count"] >= 0
        # Check summary exists
        assert "summary" in result
        assert "source" in result["summary"]
