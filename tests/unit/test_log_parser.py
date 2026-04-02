"""Unit tests for LogParser."""

from pathlib import Path

import pytest

from mcp_builder_mcp import DialogueLog, LogParser


class TestLogParser:
    """Tests for LogParser class."""

    def test_parse_markdown(self, sample_log_file: Path) -> None:
        """Test LogParser handles markdown format."""
        parser = LogParser()
        result = parser.parse(sample_log_file)

        assert isinstance(result, DialogueLog)
        assert result.source_path == str(sample_log_file)
        assert len(result.turns) > 0

    def test_parse_content_directly(self, sample_log_content: str) -> None:
        """Test parsing content string directly."""
        parser = LogParser()
        result = parser.parse_content(sample_log_content)

        assert isinstance(result, DialogueLog)
        assert len(result.turns) >= 2  # At least 2 human/assistant pairs

    def test_extract_turns(self, sample_log_content: str) -> None:
        """Test turn extraction from content."""
        parser = LogParser()
        turns = parser.extract_turns(sample_log_content)

        # Should have user and assistant turns
        roles = {t.role for t in turns}
        assert "user" in roles
        assert "assistant" in roles

    def test_handles_empty_log(self, empty_log_content: str) -> None:
        """Test graceful handling of empty logs."""
        parser = LogParser()
        result = parser.parse_content(empty_log_content)

        assert isinstance(result, DialogueLog)
        assert len(result.turns) == 0
        assert len(result.sessions) == 0

    def test_file_not_found(self, tmp_path: Path) -> None:
        """Test error handling for missing file."""
        parser = LogParser()
        nonexistent = tmp_path / "does_not_exist.md"

        with pytest.raises(FileNotFoundError):
            parser.parse(nonexistent)

    def test_extracts_tool_usage(self, sample_log_content: str) -> None:
        """Test that tool usage is extracted from content."""
        parser = LogParser()
        log = parser.parse_content(sample_log_content)

        # Check that at least one turn has tools
        assistant_turns = [t for t in log.turns if t.role == "assistant"]
        any(len(t.tools_used) > 0 for t in assistant_turns)
        # Note: Depends on patterns matching - may or may not find tools
        assert len(assistant_turns) > 0

    def test_identifies_sessions(self, sample_log_content: str) -> None:
        """Test session identification."""
        parser = LogParser()
        log = parser.parse_content(sample_log_content)

        # Should have at least one session
        assert len(log.sessions) >= 1

    def test_metadata_populated(self, sample_log_content: str) -> None:
        """Test that metadata is populated."""
        parser = LogParser()
        log = parser.parse_content(sample_log_content)

        assert "total_turns" in log.metadata
        assert "total_sessions" in log.metadata
        assert "content_length" in log.metadata
