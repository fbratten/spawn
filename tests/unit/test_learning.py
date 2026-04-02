"""Tests for learning engine."""

import pytest

from mcp_builder_mcp import LearningEngine, OutcomeStats, ScoreAdjustment, ScoredPattern
from mcp_builder_mcp.models import Pattern, Step, Trigger


class TestOutcomeStats:
    """Tests for OutcomeStats dataclass."""

    def test_default_values(self):
        """Test default values."""
        stats = OutcomeStats()
        assert stats.total_builds == 0
        assert stats.successes == 0
        assert stats.failures == 0
        assert stats.success_rate == 0.0

    def test_to_dict(self):
        """Test conversion to dict."""
        stats = OutcomeStats(
            total_builds=10,
            successes=7,
            failures=3,
            success_rate=0.7,
        )
        result = stats.to_dict()
        assert result["total_builds"] == 10
        assert result["successes"] == 7
        assert result["failures"] == 3
        assert result["success_rate"] == 0.7


class TestScoreAdjustment:
    """Tests for ScoreAdjustment dataclass."""

    def test_to_dict(self):
        """Test conversion to dict with rounding."""
        adj = ScoreAdjustment(
            pattern_id="test-pattern",
            original_buildability=0.7532,
            adjusted_buildability=0.8285,
            adjustment_factor=1.1,
            reason="Boosted by 3 successful builds",
        )
        result = adj.to_dict()
        assert result["pattern_id"] == "test-pattern"
        assert result["original_buildability"] == 0.75
        assert result["adjusted_buildability"] == 0.83
        assert result["adjustment_factor"] == 1.1
        assert "successful" in result["reason"]


class TestLearningEngine:
    """Tests for LearningEngine."""

    @pytest.fixture
    def engine(self):
        """Create learning engine."""
        return LearningEngine()

    @pytest.fixture
    def sample_pattern(self):
        """Create a sample pattern."""
        return Pattern(
            id="test-pattern-1",
            name="Test Pattern",
            description="A test pattern",
            triggers=[Trigger(phrase="test")],
            workflow_steps=[Step(id="step1", action="test")],
        )

    @pytest.fixture
    def sample_scored(self, sample_pattern):
        """Create a scored pattern."""
        return ScoredPattern(
            pattern=sample_pattern,
            frequency=0.5,
            complexity=0.3,
            value=0.7,
            uniqueness=0.4,
            buildability=0.6,
            recommendation="buildable",
        )

    def test_calculate_stats_empty(self, engine):
        """Test stats with no outcomes."""
        stats = engine.calculate_stats([])
        assert stats.total_builds == 0
        assert stats.success_rate == 0.0

    def test_calculate_stats_all_success(self, engine):
        """Test stats with all successes."""
        outcomes = [
            {"outcome": "success"},
            {"outcome": "success"},
            {"outcome": "success"},
        ]
        stats = engine.calculate_stats(outcomes)
        assert stats.total_builds == 3
        assert stats.successes == 3
        assert stats.failures == 0
        assert stats.success_rate == 1.0

    def test_calculate_stats_mixed(self, engine):
        """Test stats with mixed outcomes."""
        outcomes = [
            {"outcome": "success"},
            {"outcome": "failure"},
            {"value": "success"},  # Alternative field
            {"value": "failure"},
        ]
        stats = engine.calculate_stats(outcomes)
        assert stats.total_builds == 4
        assert stats.successes == 2
        assert stats.failures == 2
        assert stats.success_rate == 0.5

    def test_calculate_adjustment_no_outcomes(self, engine):
        """Test adjustment with no history."""
        factor, reason = engine.calculate_adjustment([])
        assert factor == 1.0
        assert "No build history" in reason

    def test_calculate_adjustment_success_boost(self, engine):
        """Test positive adjustment from successes."""
        outcomes = [{"outcome": "success"}, {"outcome": "success"}]
        factor, reason = engine.calculate_adjustment(outcomes)
        assert factor > 1.0
        assert "Boosted" in reason

    def test_calculate_adjustment_failure_penalty(self, engine):
        """Test negative adjustment from failures."""
        outcomes = [{"outcome": "failure"}, {"outcome": "failure"}]
        factor, reason = engine.calculate_adjustment(outcomes)
        assert factor < 1.0
        assert "Reduced" in reason

    def test_calculate_adjustment_decay(self, engine):
        """Test that older outcomes have less weight."""
        # Recent success should matter more than old failure
        outcomes = [
            {"outcome": "success"},  # Most recent
            {"outcome": "failure"},
            {"outcome": "failure"},
            {"outcome": "failure"},  # Oldest
        ]
        factor, _ = engine.calculate_adjustment(outcomes)
        # Recent success should somewhat offset old failures
        assert factor > 0.7

    def test_calculate_adjustment_clamped(self, engine):
        """Test adjustment is clamped to max."""
        # Many successes
        outcomes = [{"outcome": "success"} for _ in range(20)]
        factor, _ = engine.calculate_adjustment(outcomes)
        assert factor <= 1.0 + engine.MAX_ADJUSTMENT

        # Many failures
        outcomes = [{"outcome": "failure"} for _ in range(20)]
        factor, _ = engine.calculate_adjustment(outcomes)
        assert factor >= 1.0 - engine.MAX_ADJUSTMENT

    def test_adjust_score(self, engine, sample_scored):
        """Test score adjustment."""
        outcomes = [{"outcome": "success"}, {"outcome": "success"}]
        adjustment = engine.adjust_score(sample_scored, outcomes)

        assert adjustment.pattern_id == "test-pattern-1"
        assert adjustment.original_buildability == 0.6
        assert adjustment.adjusted_buildability > 0.6
        assert adjustment.adjustment_factor > 1.0

    def test_suggest_weight_adjustments_insufficient_data(self, engine):
        """Test weight suggestions with insufficient data."""
        from mcp_builder_mcp.models import ScoreWeights

        outcomes = [{"outcome": "success"}]  # Only 1 build
        weights = ScoreWeights()
        suggestions = engine.suggest_weight_adjustments(outcomes, weights)
        assert suggestions == {}

    def test_suggest_weight_adjustments_low_success(self, engine):
        """Test weight suggestions with low success rate."""
        from mcp_builder_mcp.models import ScoreWeights

        outcomes = [
            {"outcome": "failure"},
            {"outcome": "failure"},
            {"outcome": "success"},
            {"outcome": "failure"},
        ]
        weights = ScoreWeights(complexity=0.25)
        suggestions = engine.suggest_weight_adjustments(outcomes, weights)
        # Should suggest increasing complexity weight
        assert "complexity" in suggestions
        assert suggestions["complexity"] > weights.complexity

    def test_rank_with_learning(self, engine, sample_pattern):
        """Test ranking with learning adjustments."""
        # Create multiple scored patterns
        pattern2 = Pattern(
            id="test-pattern-2",
            name="Second Pattern",
            description="Another pattern",
            triggers=[Trigger(phrase="other")],
            workflow_steps=[Step(id="step1", action="other")],
        )

        scored1 = ScoredPattern(
            pattern=sample_pattern,
            frequency=0.5,
            complexity=0.3,
            value=0.7,
            uniqueness=0.4,
            buildability=0.6,
            recommendation="buildable",
        )
        scored2 = ScoredPattern(
            pattern=pattern2,
            frequency=0.6,
            complexity=0.4,
            value=0.8,
            uniqueness=0.5,
            buildability=0.7,
            recommendation="buildable",
        )

        outcomes_by_pattern = {
            "test-pattern-1": [{"outcome": "success"}, {"outcome": "success"}],
            "test-pattern-2": [{"outcome": "failure"}, {"outcome": "failure"}],
        }

        results = engine.rank_with_learning([scored1, scored2], outcomes_by_pattern)

        assert len(results) == 2
        # Pattern 1 should rank higher due to successes despite lower base score
        assert results[0][0].pattern.id == "test-pattern-1"
        assert results[1][0].pattern.id == "test-pattern-2"
