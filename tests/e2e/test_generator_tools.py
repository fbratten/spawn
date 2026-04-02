"""End-to-end tests for generation MCP tools."""

from pathlib import Path

import pytest

from mcp_builder_mcp import Input, Pattern, Step, Trigger
from mcp_builder_mcp.server import (
    generate_mcp,
    generate_preview,
    validate_mcp,
)


@pytest.fixture
def stored_pattern(tmp_path: Path) -> Pattern:
    """Create and store a pattern for testing."""
    from mcp_builder_mcp.store import PatternStore

    pattern = Pattern(
        id="test-gen-pattern",
        name="Test Generator Pattern",
        description="A pattern for testing generation",
        triggers=[Trigger(phrase="generate test")],
        inputs=[Input(name="path", type="path", required=True)],
        workflow_steps=[
            Step(id="1", action="read_file", description="Read input file"),
            Step(id="2", action="process", description="Process content"),
        ],
        category="testing",
    )

    store = PatternStore(tmp_path / ".pattern-store")
    store.store(pattern)

    return pattern


class TestGeneratePreviewTool:
    """E2E tests for generate_preview tool."""

    def test_preview_returns_files(self, stored_pattern: Pattern) -> None:
        """Test preview returns file list."""
        # Add to session
        from mcp_builder_mcp import server
        server._session_patterns = [stored_pattern]

        result = generate_preview(stored_pattern.id)

        assert "error" not in result
        assert "files" in result
        assert result["file_count"] > 0

    def test_preview_pattern_not_found(self) -> None:
        """Test preview handles missing pattern."""
        result = generate_preview("nonexistent-pattern")

        assert "error" in result
        assert "not found" in result["error"].lower()


class TestGenerateMCPTool:
    """E2E tests for generate_mcp tool."""

    def test_generate_creates_files(
        self, stored_pattern: Pattern, tmp_path: Path
    ) -> None:
        """Test generate creates files on disk."""
        from mcp_builder_mcp import server
        server._session_patterns = [stored_pattern]

        output_dir = tmp_path / "output"
        result = generate_mcp(stored_pattern.id, str(output_dir))

        assert "error" not in result
        assert result["file_count"] > 0
        assert output_dir.exists()
        assert len(list(output_dir.rglob("*"))) > 0

    def test_generate_includes_validation(
        self, stored_pattern: Pattern, tmp_path: Path
    ) -> None:
        """Test generate includes validation results."""
        from mcp_builder_mcp import server
        server._session_patterns = [stored_pattern]

        output_dir = tmp_path / "output"
        result = generate_mcp(stored_pattern.id, str(output_dir))

        assert "validation" in result
        assert "valid" in result["validation"]

    def test_generate_returns_next_steps(
        self, stored_pattern: Pattern, tmp_path: Path
    ) -> None:
        """Test generate returns helpful next steps."""
        from mcp_builder_mcp import server
        server._session_patterns = [stored_pattern]

        output_dir = tmp_path / "output"
        result = generate_mcp(stored_pattern.id, str(output_dir))

        assert "next_steps" in result
        assert len(result["next_steps"]) > 0

    def test_generate_without_tests(
        self, stored_pattern: Pattern, tmp_path: Path
    ) -> None:
        """Test generate without test files."""
        from mcp_builder_mcp import server
        server._session_patterns = [stored_pattern]

        output_dir = tmp_path / "output"
        result = generate_mcp(
            stored_pattern.id, str(output_dir), include_tests=False
        )

        assert "error" not in result
        # No test directory should be in the file paths
        test_dir_files = [f for f in result["files_created"] if "/tests/" in f]
        assert len(test_dir_files) == 0


class TestValidateMCPTool:
    """E2E tests for validate_mcp tool."""

    def test_validate_generated_server(
        self, stored_pattern: Pattern, tmp_path: Path
    ) -> None:
        """Test validation of generated server."""
        from mcp_builder_mcp import server
        server._session_patterns = [stored_pattern]

        # Generate first
        output_dir = tmp_path / "output"
        generate_mcp(stored_pattern.id, str(output_dir))

        # Then validate
        result = validate_mcp(str(output_dir))

        assert "error" not in result
        assert "valid" in result

    def test_validate_path_not_found(self, tmp_path: Path) -> None:
        """Test validation of non-existent path."""
        result = validate_mcp(str(tmp_path / "nonexistent"))

        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_validate_returns_counts(
        self, stored_pattern: Pattern, tmp_path: Path
    ) -> None:
        """Test validation returns error/warning counts."""
        from mcp_builder_mcp import server
        server._session_patterns = [stored_pattern]

        output_dir = tmp_path / "output"
        generate_mcp(stored_pattern.id, str(output_dir))

        result = validate_mcp(str(output_dir))

        assert "error_count" in result
        assert "warning_count" in result


class TestFullGenerationWorkflow:
    """E2E tests for full analyze → generate workflow."""

    def test_analyze_to_generate(self, sample_log_file: Path, tmp_path: Path) -> None:
        """Test full workflow from log analysis to generation."""
        # Analyze log
        from mcp_builder_mcp.server import analyze_log as analyze

        analyze_result = analyze(str(sample_log_file))

        if analyze_result.get("count", 0) > 0:
            pattern_id = analyze_result["patterns"][0]["id"]

            # Generate
            output_dir = tmp_path / "generated"
            gen_result = generate_mcp(pattern_id, str(output_dir))

            assert "error" not in gen_result
            assert output_dir.exists()
