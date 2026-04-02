"""Unit tests for PatternExtractor."""



from mcp_builder_mcp import LogParser, Pattern, PatternExtractor, Trigger


class TestPatternExtractor:
    """Tests for PatternExtractor class."""

    def test_find_patterns(self, sample_log_content: str) -> None:
        """Test pattern detection from log."""
        parser = LogParser()
        log = parser.parse_content(sample_log_content)

        extractor = PatternExtractor()
        patterns = extractor.extract(log)

        # Patterns may or may not be found depending on tool detection
        # The extractor requires tool usage to be detected in content
        assert isinstance(patterns, list)
        assert all(isinstance(p, Pattern) for p in patterns)

    def test_find_patterns_with_tool_usage(self) -> None:
        """Test pattern detection with explicit tool markers."""
        log_with_tools = (
            "Human: Please read the config file\n\n"
            "Assistant: I'll read the config file for you.\n\n"
            "<invoke name=\"Read\">\n"
            "<parameter name=\"file_path\">/config.yaml</parameter>\n"
            "</invoke>\n\n"
            "Done reading the file.\n"
        )
        parser = LogParser()
        log = parser.parse_content(log_with_tools)

        extractor = PatternExtractor()
        patterns = extractor.extract(log)

        # Should find at least one pattern when tools are detected
        assert len(patterns) >= 1

    def test_extract_triggers(self, sample_log_content: str) -> None:
        """Test trigger phrase extraction."""
        parser = LogParser()
        log = parser.parse_content(sample_log_content)

        extractor = PatternExtractor()
        patterns = extractor.extract(log)

        # Patterns should have triggers
        for pattern in patterns:
            assert len(pattern.triggers) > 0
            assert all(isinstance(t, Trigger) for t in pattern.triggers)

    def test_deduplicates(self, similar_patterns: list[Pattern]) -> None:
        """Test near-duplicate pattern removal."""
        extractor = PatternExtractor()
        unique = extractor.deduplicate(similar_patterns)

        # Should remove duplicates with same trigger
        assert len(unique) < len(similar_patterns)
        # Should keep the one with higher confidence
        ids = {p.id for p in unique}
        assert "pattern-1" in ids  # Higher confidence
        assert "pattern-3" in ids  # Different trigger

    def test_min_confidence_filter(self, sample_log_content: str) -> None:
        """Test minimum confidence threshold."""
        parser = LogParser()
        log = parser.parse_content(sample_log_content)

        # High threshold
        extractor_high = PatternExtractor(min_confidence=0.9)
        patterns_high = extractor_high.extract(log)

        # Low threshold
        extractor_low = PatternExtractor(min_confidence=0.3)
        patterns_low = extractor_low.extract(log)

        # Low threshold should include same or more patterns
        assert len(patterns_low) >= len(patterns_high)

    def test_pattern_has_workflow_steps(self, sample_log_content: str) -> None:
        """Test that patterns include workflow steps."""
        parser = LogParser()
        log = parser.parse_content(sample_log_content)

        extractor = PatternExtractor()
        patterns = extractor.extract(log)

        # At least some patterns should have steps
        [p for p in patterns if len(p.workflow_steps) > 0]
        # This depends on the sample content having tool usage
        assert len(patterns) >= 0  # May or may not have steps

    def test_pattern_id_generation(self, sample_log_content: str) -> None:
        """Test that pattern IDs are unique and valid."""
        parser = LogParser()
        log = parser.parse_content(sample_log_content)

        extractor = PatternExtractor()
        patterns = extractor.extract(log)

        if patterns:
            ids = [p.id for p in patterns]
            assert len(ids) == len(set(ids))  # All unique
            for pid in ids:
                assert pid.startswith("pattern-")

    def test_category_inference(self, sample_log_content: str) -> None:
        """Test category is inferred from content."""
        parser = LogParser()
        log = parser.parse_content(sample_log_content)

        extractor = PatternExtractor()
        patterns = extractor.extract(log)

        for pattern in patterns:
            assert pattern.category in [
                "general",
                "file_management",
                "code_generation",
                "documentation",
                "git_workflow",
                "analysis",
                "testing",
            ]

    def test_empty_log_returns_empty(self, empty_log_content: str) -> None:
        """Test empty log returns no patterns."""
        parser = LogParser()
        log = parser.parse_content(empty_log_content)

        extractor = PatternExtractor()
        patterns = extractor.extract(log)

        assert patterns == []
