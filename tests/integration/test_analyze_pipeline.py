"""Integration tests for the analyze pipeline."""

from pathlib import Path

from mcp_builder_mcp import LogParser, PatternExtractor, PatternStore, ScoringEngine


class TestAnalyzePipeline:
    """Integration tests for Parser → Extractor → Scorer pipeline."""

    def test_full_pipeline(self, sample_log_file: Path, tmp_path: Path) -> None:
        """Test complete analyze pipeline."""
        # Parse
        parser = LogParser()
        log = parser.parse(sample_log_file)
        assert log.turns

        # Extract - patterns depend on tool detection
        extractor = PatternExtractor()
        patterns = extractor.extract(log)
        # May or may not find patterns in simple test content
        assert isinstance(patterns, list)

        # If patterns found, score them
        if patterns:
            engine = ScoringEngine()
            scored = engine.rank(patterns)
            assert len(scored) == len(patterns)
            assert all(s.buildability > 0 for s in scored)

    def test_full_pipeline_with_tool_markers(self, tmp_path: Path) -> None:
        """Test pipeline with content containing tool markers."""
        log_content = (
            "Human: Create a handover document\n\n"
            "Assistant: I'll create the handover.\n\n"
            "<invoke name=\"Bash\">\n"
            "<parameter name=\"command\">git log --oneline -5</parameter>\n"
            "</invoke>\n\n"
            "<invoke name=\"Write\">\n"
            "<parameter name=\"file_path\">/handover.md</parameter>\n"
            "</invoke>\n\n"
            "Handover complete.\n"
        )
        log_file = tmp_path / "log_with_tools.md"
        log_file.write_text(log_content)

        # Parse
        parser = LogParser()
        log = parser.parse(log_file)
        assert log.turns

        # Extract - should find patterns with tool markers
        extractor = PatternExtractor()
        patterns = extractor.extract(log)
        assert len(patterns) >= 1

        # Score
        engine = ScoringEngine()
        scored = engine.rank(patterns)
        assert len(scored) == len(patterns)

    def test_pipeline_with_store(self, sample_log_file: Path, tmp_path: Path) -> None:
        """Test pipeline with pattern storage."""
        store = PatternStore(tmp_path / ".pattern-store")

        # Parse and extract
        parser = LogParser()
        log = parser.parse(sample_log_file)
        extractor = PatternExtractor()
        patterns = extractor.extract(log)

        # Score and store
        engine = ScoringEngine()
        for pattern in patterns:
            scored = engine.score(pattern)
            store.store_scored(scored)

        # Verify stored
        assert store.count() == len(patterns)

        # Retrieve and verify
        stored = store.list_all()
        assert len(stored) == len(patterns)


class TestPatternStorage:
    """Integration tests for pattern storage."""

    def test_patterns_save_and_load(
        self, mock_pattern, tmp_path: Path
    ) -> None:
        """Test patterns persist correctly."""
        store = PatternStore(tmp_path / ".pattern-store")

        # Store
        store.store(mock_pattern)

        # Create new store instance (simulates restart)
        store2 = PatternStore(tmp_path / ".pattern-store")

        # Load
        loaded = store2.get(mock_pattern.id)

        assert loaded is not None
        assert loaded.id == mock_pattern.id
        assert loaded.name == mock_pattern.name
        assert len(loaded.triggers) == len(mock_pattern.triggers)
        assert len(loaded.workflow_steps) == len(mock_pattern.workflow_steps)

    def test_outcome_history_persists(
        self, mock_pattern, tmp_path: Path
    ) -> None:
        """Test build outcomes persist."""
        store = PatternStore(tmp_path / ".pattern-store")
        store.store(mock_pattern)
        store.record_outcome(mock_pattern.id, "success", "v1.0 working")

        # New store instance
        store2 = PatternStore(tmp_path / ".pattern-store")
        outcomes = store2.get_outcomes(mock_pattern.id)

        assert len(outcomes) == 1
        assert outcomes[0]["outcome"] == "success"
