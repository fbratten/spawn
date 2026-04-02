"""Unit tests for PatternStore."""



from mcp_builder_mcp import Pattern, PatternStore, ScoredPattern


class TestPatternStore:
    """Tests for PatternStore class."""

    def test_store_pattern_creates_file(
        self, temp_store: PatternStore, mock_pattern: Pattern
    ) -> None:
        """Test storing pattern creates YAML file."""
        filepath = temp_store.store(mock_pattern)

        assert filepath.exists()
        assert filepath.suffix == ".yaml"

    def test_get_pattern(
        self, temp_store: PatternStore, mock_pattern: Pattern
    ) -> None:
        """Test retrieving stored pattern."""
        temp_store.store(mock_pattern)
        retrieved = temp_store.get(mock_pattern.id)

        assert retrieved is not None
        assert retrieved.id == mock_pattern.id
        assert retrieved.name == mock_pattern.name

    def test_get_nonexistent_returns_none(self, temp_store: PatternStore) -> None:
        """Test getting non-existent pattern returns None."""
        result = temp_store.get("nonexistent-pattern")
        assert result is None

    def test_list_all(self, populated_store: PatternStore) -> None:
        """Test listing all patterns."""
        patterns = populated_store.list_all()

        assert len(patterns) == 2

    def test_search_by_category(
        self, populated_store: PatternStore
    ) -> None:
        """Test searching by category."""
        results = populated_store.search(category="documentation")

        assert len(results) >= 1
        assert all(p.category == "documentation" for p in results)

    def test_search_by_query(self, populated_store: PatternStore) -> None:
        """Test text search in name/description."""
        results = populated_store.search(query="handover")

        assert len(results) >= 1
        assert any("handover" in p.name.lower() or "handover" in p.description.lower() for p in results)

    def test_search_by_tags(
        self, temp_store: PatternStore, mock_pattern: Pattern
    ) -> None:
        """Test filtering by tags."""
        temp_store.store(mock_pattern)
        results = temp_store.search(tags=["session"])

        assert len(results) >= 1

    def test_search_empty_results(self, populated_store: PatternStore) -> None:
        """Test search with no matches."""
        results = populated_store.search(query="xyznonexistent")
        assert len(results) == 0

    def test_delete_pattern(
        self, temp_store: PatternStore, mock_pattern: Pattern
    ) -> None:
        """Test deleting a pattern."""
        temp_store.store(mock_pattern)
        assert temp_store.exists(mock_pattern.id)

        deleted = temp_store.delete(mock_pattern.id)
        assert deleted is True
        assert not temp_store.exists(mock_pattern.id)

    def test_delete_nonexistent(self, temp_store: PatternStore) -> None:
        """Test deleting non-existent pattern returns False."""
        deleted = temp_store.delete("nonexistent")
        assert deleted is False

    def test_count(self, populated_store: PatternStore) -> None:
        """Test pattern count."""
        count = populated_store.count()
        assert count == 2

    def test_store_scored_pattern(
        self, temp_store: PatternStore, mock_pattern: Pattern
    ) -> None:
        """Test storing pattern with scores."""
        scored = ScoredPattern(
            pattern=mock_pattern,
            frequency=4.0,
            complexity=2.0,
            value=5.0,
            uniqueness=4.0,
            buildability=8.5,
            recommendation="build",
        )

        filepath = temp_store.store_scored(scored)
        assert filepath.exists()

    def test_record_outcome(
        self, temp_store: PatternStore, mock_pattern: Pattern
    ) -> None:
        """Test recording build outcome."""
        temp_store.store(mock_pattern)
        temp_store.record_outcome(
            mock_pattern.id, outcome="success", notes="Tests passing"
        )

        outcomes = temp_store.get_outcomes(mock_pattern.id)
        assert len(outcomes) == 1
        assert outcomes[0]["outcome"] == "success"

    def test_get_all_outcomes(
        self, temp_store: PatternStore, mock_pattern: Pattern
    ) -> None:
        """Test getting all outcomes."""
        temp_store.record_outcome(mock_pattern.id, "success")
        temp_store.record_outcome("other-pattern", "failure")

        all_outcomes = temp_store.get_outcomes()
        assert len(all_outcomes) == 2

    def test_safe_filename(self, temp_store: PatternStore) -> None:
        """Test filename sanitization."""
        pattern = Pattern(
            id="pattern/with\\special:chars",
            name="Test",
        )
        filepath = temp_store.store(pattern)

        # Should create valid file
        assert filepath.exists()
        assert "/" not in filepath.name
        assert "\\" not in filepath.name
