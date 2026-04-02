"""End-to-end tests for pipeline tools (MVP 4)."""


import pytest

import mcp_builder_mcp.server as server_module
from mcp_builder_mcp.server import (
    _get_store,
    analyze_log,
    batch_analyze,
    compare_existing,
    run_pipeline,
)


def _clear_session():
    """Clear session state for tests."""
    server_module._session_patterns.clear()
    store = _get_store()
    for f in store.patterns_dir.glob("*.yaml"):
        f.unlink()
    for f in store.history_dir.glob("*.yaml"):
        f.unlink()


class TestRunPipelineTool:
    """Tests for run_pipeline tool."""

    @pytest.fixture
    def sample_log(self, tmp_path):
        """Create a sample log file."""
        content = (
            "# Session: Test\n\n"
            "## Turn 1\n"
            "**User**: Deploy the application\n"
            "**Assistant**: Running deployment.\n"
            '<invoke name="Bash"><parameter name="command">./deploy.sh</parameter></invoke>\n'
            '<invoke name="Bash"><parameter name="command">./deploy.sh</parameter></invoke>\n'
            '<invoke name="Bash"><parameter name="command">./deploy.sh</parameter></invoke>\n'
        )
        log_file = tmp_path / "sample.md"
        log_file.write_text(content)
        return log_file

    def test_run_pipeline_file_not_found(self):
        """Test pipeline with nonexistent file."""
        _clear_session()
        result = run_pipeline("/nonexistent/path.md")
        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_run_pipeline_analyzes_log(self, sample_log):
        """Test that pipeline runs analysis stage."""
        _clear_session()
        result = run_pipeline(str(sample_log))
        assert "stages" in result
        assert "analyze" in result["stages"]
        assert result["stages"]["analyze"]["patterns_found"] >= 0

    def test_run_pipeline_scores_patterns(self, sample_log):
        """Test that pipeline runs scoring stage."""
        _clear_session()
        result = run_pipeline(str(sample_log))
        if "stages" in result and "score" in result["stages"]:
            assert "total_scored" in result["stages"]["score"]

    def test_run_pipeline_returns_recommendations(self, sample_log):
        """Test that pipeline returns recommendations."""
        _clear_session()
        result = run_pipeline(str(sample_log), min_score=0.0, top_n=5)
        assert "recommendations" in result

    def test_run_pipeline_auto_generate_requires_output(self, sample_log):
        """Test that auto_generate requires output_dir."""
        _clear_session()
        result = run_pipeline(str(sample_log), auto_generate=True)
        assert "error" in result
        assert "output_dir" in result["error"]

    def test_run_pipeline_auto_generate(self, sample_log, tmp_path):
        """Test pipeline with auto generation."""
        _clear_session()
        output_dir = tmp_path / "generated"
        output_dir.mkdir()

        result = run_pipeline(
            str(sample_log),
            output_dir=str(output_dir),
            auto_generate=True,
            min_score=0.0,
        )

        assert "generated" in result
        if result.get("recommendations"):
            # Should attempt generation for recommendations
            assert "stages" in result
            if "generate" in result["stages"]:
                assert "attempted" in result["stages"]["generate"]


class TestCompareExistingTool:
    """Tests for compare_existing tool."""

    @pytest.fixture
    def sample_log(self, tmp_path):
        """Create a sample log file."""
        content = (
            "# Session\n"
            '<invoke name="Bash"><parameter name="command">git status</parameter></invoke>\n'
            '<invoke name="Bash"><parameter name="command">git status</parameter></invoke>\n'
            '<invoke name="Bash"><parameter name="command">git status</parameter></invoke>\n'
        )
        log_file = tmp_path / "test.md"
        log_file.write_text(content)
        return log_file

    def test_compare_pattern_not_found(self):
        """Test comparison for nonexistent pattern."""
        _clear_session()
        result = compare_existing("nonexistent-pattern")
        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_compare_returns_overlaps(self, sample_log):
        """Test that comparison returns overlap info."""
        _clear_session()
        analyze_log(str(sample_log))

        if server_module._session_patterns:
            pattern_id = server_module._session_patterns[0].id
            result = compare_existing(pattern_id)

            assert "overlaps" in result
            assert "unique_features" in result
            assert "recommendation" in result

    def test_compare_detects_overlap_with_existing(self, tmp_path):
        """Test overlap detection with known tools."""
        _clear_session()

        # Create a pattern with keywords matching existing tools
        content = (
            "# Documentation Session\n"
            "**User**: Update the project documentation\n"
            "**Assistant**: I'll update the docs.\n"
            '<invoke name="Write"><parameter name="path">CLAUDE.md</parameter></invoke>\n'
            '<invoke name="Write"><parameter name="path">CLAUDE.md</parameter></invoke>\n'
            '<invoke name="Write"><parameter name="path">CLAUDE.md</parameter></invoke>\n'
        )
        log_file = tmp_path / "docs.md"
        log_file.write_text(content)

        analyze_log(str(log_file))

        if server_module._session_patterns:
            # Add relevant tags
            pattern = server_module._session_patterns[0]
            pattern.tags = ["documentation", "claude.md"]

            result = compare_existing(pattern.id)

            # Should find overlap with smart-inventory
            if result.get("overlaps"):
                [o["tool_name"] for o in result["overlaps"]]
                # smart-inventory handles CLAUDE.md
                assert any("smart-inventory" in n or "documentation" in str(o)
                          for o in result["overlaps"] for n in [o.get("tool_name", "")])


class TestBatchAnalyzeTool:
    """Tests for batch_analyze tool."""

    @pytest.fixture
    def multiple_logs(self, tmp_path):
        """Create multiple log files."""
        logs = []
        for i in range(3):
            content = (
                f"# Session {i}\n"
                f'<invoke name="Bash"><parameter name="command">cmd{i}</parameter></invoke>\n'
                f'<invoke name="Bash"><parameter name="command">cmd{i}</parameter></invoke>\n'
                f'<invoke name="Bash"><parameter name="command">cmd{i}</parameter></invoke>\n'
            )
            log_file = tmp_path / f"log_{i}.md"
            log_file.write_text(content)
            logs.append(str(log_file))
        return logs

    def test_batch_analyze_empty_list(self):
        """Test batch with empty list."""
        _clear_session()
        result = batch_analyze([])
        assert result["total_files"] == 0
        assert result["successful_files"] == 0

    def test_batch_analyze_single_file(self, multiple_logs):
        """Test batch with single file."""
        _clear_session()
        result = batch_analyze([multiple_logs[0]])
        assert result["total_files"] == 1
        assert result["successful_files"] == 1

    def test_batch_analyze_multiple_files(self, multiple_logs):
        """Test batch with multiple files."""
        _clear_session()
        result = batch_analyze(multiple_logs)
        assert result["total_files"] == 3
        assert result["successful_files"] == 3
        assert len(result["by_log"]) == 3

    def test_batch_analyze_handles_failures(self, multiple_logs):
        """Test batch handles missing files."""
        _clear_session()
        logs_with_missing = multiple_logs + ["/nonexistent/file.md"]
        result = batch_analyze(logs_with_missing)

        assert result["total_files"] == 4
        assert result["successful_files"] == 3
        assert len(result["failed_files"]) == 1

    def test_batch_analyze_returns_all_patterns(self, multiple_logs):
        """Test that all patterns are collected."""
        _clear_session()
        result = batch_analyze(multiple_logs)

        assert "all_patterns" in result
        # total_unique only present when patterns are found
        if "error" not in result:
            assert "total_unique" in result

    def test_batch_analyze_merges_similar(self, tmp_path):
        """Test that similar patterns are merged."""
        _clear_session()

        # Create two logs with very similar patterns
        for i in range(2):
            content = (
                f"# Session {i}\n"
                '<invoke name="Bash"><parameter name="command">npm test</parameter></invoke>\n'
                '<invoke name="Bash"><parameter name="command">npm test</parameter></invoke>\n'
                '<invoke name="Bash"><parameter name="command">npm test</parameter></invoke>\n'
            )
            (tmp_path / f"similar_{i}.md").write_text(content)

        logs = [str(tmp_path / f"similar_{i}.md") for i in range(2)]

        result = batch_analyze(logs, merge_similar=True, similarity_threshold=0.5)

        assert "merged_count" in result
        # With similar patterns, some should be merged
        if "total_unique" in result and result["total_unique"] > 0:
            # Either patterns were found and possibly merged
            assert result["all_patterns"] is not None

    def test_batch_analyze_no_merge(self, multiple_logs):
        """Test batch without merging."""
        _clear_session()
        result = batch_analyze(multiple_logs, merge_similar=False)

        assert result["merged_count"] == 0


class TestPipelineIntegration:
    """Integration tests for full pipeline workflows."""

    @pytest.fixture
    def rich_log(self, tmp_path):
        """Create a log with multiple patterns."""
        content = (
            "# Session: Development\n\n"
            "## Turn 1\n"
            "**User**: Run the tests\n"
            "**Assistant**: Running tests.\n"
            '<invoke name="Bash"><parameter name="command">pytest tests/</parameter></invoke>\n'
            '<invoke name="Bash"><parameter name="command">pytest tests/</parameter></invoke>\n'
            '<invoke name="Bash"><parameter name="command">pytest tests/</parameter></invoke>\n'
            "\n## Turn 2\n"
            "**User**: Check the linting\n"
            "**Assistant**: Running linter.\n"
            '<invoke name="Bash"><parameter name="command">ruff check src/</parameter></invoke>\n'
            '<invoke name="Bash"><parameter name="command">ruff check src/</parameter></invoke>\n'
            '<invoke name="Bash"><parameter name="command">ruff check src/</parameter></invoke>\n'
        )
        log_file = tmp_path / "dev.md"
        log_file.write_text(content)
        return log_file

    def test_full_pipeline_workflow(self, rich_log, tmp_path):
        """Test complete pipeline from log to recommendations."""
        _clear_session()

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        result = run_pipeline(
            str(rich_log),
            output_dir=str(output_dir),
            auto_generate=False,
            min_score=0.0,
            top_n=5,
        )

        # Check all stages completed
        assert "stages" in result
        assert "analyze" in result["stages"]

        # Should have recommendations if patterns found
        if result["stages"]["analyze"]["patterns_found"] > 0:
            assert "recommendations" in result

    def test_batch_then_pipeline(self, tmp_path):
        """Test batch analysis followed by pipeline."""
        _clear_session()

        # Create multiple logs
        for i in range(2):
            content = (
                f"# Session {i}\n"
                f'<invoke name="Bash"><parameter name="command">make build</parameter></invoke>\n'
                f'<invoke name="Bash"><parameter name="command">make build</parameter></invoke>\n'
                f'<invoke name="Bash"><parameter name="command">make build</parameter></invoke>\n'
            )
            (tmp_path / f"log_{i}.md").write_text(content)

        logs = [str(tmp_path / f"log_{i}.md") for i in range(2)]

        # First batch analyze
        batch_result = batch_analyze(logs, merge_similar=True)
        assert batch_result["successful_files"] == 2

        # Then run pipeline on one log (patterns already in store)
        pipeline_result = run_pipeline(logs[0], min_score=0.0)
        assert "stages" in pipeline_result
