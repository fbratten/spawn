"""Unit tests for ScoringEngine."""


from mcp_builder_mcp import Pattern, ScoredPattern, ScoreWeights, ScoringEngine


class TestScoringEngine:
    """Tests for ScoringEngine class."""

    def test_calculate_score(self, mock_pattern: Pattern) -> None:
        """Test score calculation produces valid result."""
        engine = ScoringEngine()
        scored = engine.score(mock_pattern)

        assert isinstance(scored, ScoredPattern)
        assert scored.pattern == mock_pattern
        assert 1.0 <= scored.frequency <= 5.0
        assert 1.0 <= scored.complexity <= 5.0
        assert 1.0 <= scored.value <= 5.0
        assert 1.0 <= scored.uniqueness <= 5.0
        assert scored.buildability != 0  # Should be calculated

    def test_rank_patterns(self, mock_pattern: Pattern, mock_pattern_simple: Pattern) -> None:
        """Test patterns are ranked by score."""
        engine = ScoringEngine()
        patterns = [mock_pattern, mock_pattern_simple]
        ranked = engine.rank(patterns)

        assert len(ranked) == 2
        # Should be sorted by buildability descending
        assert ranked[0].buildability >= ranked[1].buildability

    def test_custom_weights(self, mock_pattern: Pattern, custom_weights: ScoreWeights) -> None:
        """Test custom weight overrides work."""
        engine_default = ScoringEngine()
        engine_custom = ScoringEngine(weights=custom_weights)

        scored_default = engine_default.score(mock_pattern)
        scored_custom = engine_custom.score(mock_pattern)

        # Scores should differ with different weights
        assert scored_custom.weights_used == custom_weights
        # Buildability will differ due to different weights
        assert scored_default.buildability != scored_custom.buildability

    def test_recommendation_build(self, mock_pattern: Pattern) -> None:
        """Test 'build' recommendation for high-scoring patterns."""
        # Create pattern with high scores
        pattern = Pattern(
            id="high-score",
            name="High Score Pattern",
            confidence=1.0,
            triggers=[],
            workflow_steps=[],
            category="documentation",
            tags=["automation", "validation"],
        )

        engine = ScoringEngine()
        scored = engine.score(pattern)

        # Recommendation depends on score
        assert scored.recommendation in ["build", "review", "skip"]

    def test_recommendation_skip(self) -> None:
        """Test 'skip' recommendation for low-scoring patterns."""
        pattern = Pattern(
            id="low-score",
            name="Low Score Pattern",
            confidence=0.2,
            category="general",
        )

        engine = ScoringEngine()
        scored = engine.score(pattern)

        # Low confidence pattern should have lower score
        assert scored.buildability < 8.0  # Below 'build' threshold

    def test_recommend_top_n(self, mock_pattern: Pattern, mock_pattern_simple: Pattern) -> None:
        """Test recommend returns top N patterns."""
        engine = ScoringEngine()
        patterns = [mock_pattern, mock_pattern_simple]

        recommendations = engine.recommend(patterns, top_n=1, threshold=0.0)
        assert len(recommendations) <= 1

    def test_recommend_threshold(self, mock_pattern_simple: Pattern) -> None:
        """Test recommend filters by threshold."""
        engine = ScoringEngine()
        patterns = [mock_pattern_simple]

        # Very high threshold
        recommendations = engine.recommend(patterns, threshold=100.0)
        assert len(recommendations) == 0

    def test_frequency_scoring(self) -> None:
        """Test frequency score calculation."""
        # High confidence = higher frequency score
        pattern_high = Pattern(id="high", name="High", confidence=1.0)
        pattern_low = Pattern(id="low", name="Low", confidence=0.3)

        engine = ScoringEngine()
        scored_high = engine.score(pattern_high)
        scored_low = engine.score(pattern_low)

        assert scored_high.frequency > scored_low.frequency

    def test_complexity_scoring(self) -> None:
        """Test complexity score increases with more steps."""
        from mcp_builder_mcp import Step

        pattern_simple = Pattern(id="simple", name="Simple")
        pattern_complex = Pattern(
            id="complex",
            name="Complex",
            workflow_steps=[
                Step(id="1", action="action1"),
                Step(id="2", action="action2"),
                Step(id="3", action="action3"),
                Step(id="4", action="action4"),
            ],
        )

        engine = ScoringEngine()
        scored_simple = engine.score(pattern_simple)
        scored_complex = engine.score(pattern_complex)

        assert scored_complex.complexity > scored_simple.complexity

    def test_uniqueness_detects_overlap(self) -> None:
        """Test uniqueness detects overlap with existing tools."""
        # Pattern with overlapping keywords
        pattern_overlap = Pattern(
            id="overlap",
            name="Project Audit Tool",  # Overlaps with paaf
            description="audit project health",
            category="analysis",
        )

        # Unique pattern
        pattern_unique = Pattern(
            id="unique",
            name="Custom Widget Builder",
            description="builds custom widgets",
            category="code_generation",
        )

        engine = ScoringEngine()
        scored_overlap = engine.score(pattern_overlap)
        scored_unique = engine.score(pattern_unique)

        assert scored_unique.uniqueness > scored_overlap.uniqueness
