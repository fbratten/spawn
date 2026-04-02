"""Learning engine for adjusting scores based on build outcomes."""

from dataclasses import dataclass
from typing import Any

from mcp_builder_mcp.models import ScoredPattern, ScoreWeights


@dataclass
class OutcomeStats:
    """Statistics for build outcomes."""

    total_builds: int = 0
    successes: int = 0
    failures: int = 0
    success_rate: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_builds": self.total_builds,
            "successes": self.successes,
            "failures": self.failures,
            "success_rate": self.success_rate,
        }


@dataclass
class ScoreAdjustment:
    """Adjustment to apply to a pattern score."""

    pattern_id: str
    original_buildability: float
    adjusted_buildability: float
    adjustment_factor: float
    reason: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pattern_id": self.pattern_id,
            "original_buildability": round(self.original_buildability, 2),
            "adjusted_buildability": round(self.adjusted_buildability, 2),
            "adjustment_factor": round(self.adjustment_factor, 3),
            "reason": self.reason,
        }


class LearningEngine:
    """Engine for learning from build outcomes and adjusting scores."""

    # Adjustment factors
    SUCCESS_BOOST = 0.10  # 10% boost per success
    FAILURE_PENALTY = 0.15  # 15% penalty per failure
    MAX_ADJUSTMENT = 0.50  # Maximum 50% adjustment either way
    DECAY_FACTOR = 0.9  # Older outcomes matter less

    def __init__(self):
        """Initialize learning engine."""
        pass

    def calculate_stats(self, outcomes: list[dict[str, Any]]) -> OutcomeStats:
        """Calculate statistics from outcome history.

        Args:
            outcomes: List of outcome records.

        Returns:
            OutcomeStats with calculated values.
        """
        stats = OutcomeStats()

        for outcome in outcomes:
            outcome_value = outcome.get("outcome") or outcome.get("value", "")
            if "success" in outcome_value.lower():
                stats.successes += 1
            elif "failure" in outcome_value.lower():
                stats.failures += 1

        stats.total_builds = stats.successes + stats.failures

        if stats.total_builds > 0:
            stats.success_rate = stats.successes / stats.total_builds

        return stats

    def calculate_adjustment(
        self, outcomes: list[dict[str, Any]]
    ) -> tuple[float, str]:
        """Calculate score adjustment factor from outcomes.

        Args:
            outcomes: List of outcome records, newest first.

        Returns:
            Tuple of (adjustment_factor, reason).
        """
        if not outcomes:
            return 1.0, "No build history"

        # Calculate weighted adjustment based on outcomes
        # More recent outcomes have more weight
        total_adjustment = 0.0
        total_weight = 0.0

        for i, outcome in enumerate(outcomes):
            weight = self.DECAY_FACTOR ** i  # Decay for older outcomes
            outcome_value = outcome.get("outcome") or outcome.get("value", "")

            if "success" in outcome_value.lower():
                total_adjustment += self.SUCCESS_BOOST * weight
            elif "failure" in outcome_value.lower():
                total_adjustment -= self.FAILURE_PENALTY * weight

            total_weight += weight

        normalized = total_adjustment / total_weight if total_weight > 0 else 0.0

        # Clamp adjustment
        adjustment = max(-self.MAX_ADJUSTMENT, min(self.MAX_ADJUSTMENT, normalized))

        # Generate reason
        stats = self.calculate_stats(outcomes)
        if adjustment > 0:
            reason = f"Boosted by {stats.successes} successful builds"
        elif adjustment < 0:
            reason = f"Reduced due to {stats.failures} failed builds"
        else:
            reason = "No adjustment needed"

        return 1.0 + adjustment, reason

    def adjust_score(
        self, scored: ScoredPattern, outcomes: list[dict[str, Any]]
    ) -> ScoreAdjustment:
        """Adjust a pattern's buildability score based on outcomes.

        Args:
            scored: Pattern with current scores.
            outcomes: Build outcome history.

        Returns:
            ScoreAdjustment with before/after values.
        """
        factor, reason = self.calculate_adjustment(outcomes)

        original = scored.buildability
        adjusted = original * factor

        return ScoreAdjustment(
            pattern_id=scored.pattern.id,
            original_buildability=original,
            adjusted_buildability=adjusted,
            adjustment_factor=factor,
            reason=reason,
        )

    def suggest_weight_adjustments(
        self, outcomes: list[dict[str, Any]], current_weights: ScoreWeights
    ) -> dict[str, float]:
        """Suggest weight adjustments based on outcome patterns.

        Analyzes which types of patterns tend to succeed or fail
        and suggests weight modifications.

        Args:
            outcomes: Build outcome history with pattern metadata.
            current_weights: Current scoring weights.

        Returns:
            Dictionary of suggested weight changes.
        """
        # This is a simplified version - real implementation would
        # analyze pattern features correlated with success/failure

        suggestions: dict[str, float] = {}
        stats = self.calculate_stats(outcomes)

        if stats.total_builds < 3:
            return suggestions  # Not enough data

        if stats.success_rate > 0.8:
            # High success rate - weights are working well
            pass
        elif stats.success_rate < 0.4:
            # Low success rate - suggest increasing complexity penalty
            suggestions["complexity"] = current_weights.complexity * 1.2

        return suggestions

    def rank_with_learning(
        self,
        scored_patterns: list[ScoredPattern],
        outcomes_by_pattern: dict[str, list[dict[str, Any]]],
    ) -> list[tuple[ScoredPattern, ScoreAdjustment]]:
        """Rank patterns with learning adjustments applied.

        Args:
            scored_patterns: List of scored patterns.
            outcomes_by_pattern: Outcomes keyed by pattern ID.

        Returns:
            List of (pattern, adjustment) tuples, sorted by adjusted score.
        """
        results = []

        for scored in scored_patterns:
            outcomes = outcomes_by_pattern.get(scored.pattern.id, [])
            adjustment = self.adjust_score(scored, outcomes)
            results.append((scored, adjustment))

        # Sort by adjusted buildability
        results.sort(key=lambda x: x[1].adjusted_buildability, reverse=True)

        return results
