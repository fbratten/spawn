"""Scoring data models."""

from dataclasses import dataclass, field
from typing import Any

from mcp_builder_mcp.models.pattern import Pattern


@dataclass
class ScoreWeights:
    """Configurable weights for pattern scoring."""

    frequency: float = 1.0
    """Weight for frequency (how often pattern appears)."""

    complexity: float = -0.5
    """Weight for complexity (negative - higher complexity = lower score)."""

    value: float = 1.5
    """Weight for value (user benefit if automated)."""

    uniqueness: float = 0.5
    """Weight for uniqueness (not covered by existing tools)."""

    def to_dict(self) -> dict[str, float]:
        """Convert to dictionary."""
        return {
            "frequency": self.frequency,
            "complexity": self.complexity,
            "value": self.value,
            "uniqueness": self.uniqueness,
        }

    @classmethod
    def from_dict(cls, data: dict[str, float]) -> "ScoreWeights":
        """Create from dictionary."""
        return cls(
            frequency=data.get("frequency", 1.0),
            complexity=data.get("complexity", -0.5),
            value=data.get("value", 1.5),
            uniqueness=data.get("uniqueness", 0.5),
        )


@dataclass
class ScoredPattern:
    """A pattern with buildability scores."""

    pattern: Pattern
    """The underlying pattern."""

    # Individual scores (1-5 scale)
    frequency: float = 0.0
    """How often pattern appears in logs (1-5)."""

    complexity: float = 0.0
    """Implementation difficulty (1-5, higher = harder)."""

    value: float = 0.0
    """User benefit if automated (1-5)."""

    uniqueness: float = 0.0
    """Not covered by existing tools (1-5)."""

    # Calculated score
    buildability: float = 0.0
    """Final buildability score."""

    # Recommendation
    recommendation: str = "review"
    """One of: 'build', 'skip', 'review'."""

    # Metadata
    weights_used: ScoreWeights = field(default_factory=ScoreWeights)
    """Weights used for scoring."""

    def calculate_buildability(self, weights: ScoreWeights | None = None) -> float:
        """Calculate buildability score from individual scores."""
        w = weights or self.weights_used

        self.buildability = (
            (self.frequency * w.frequency)
            + (self.complexity * w.complexity)
            + (self.value * w.value)
            + (self.uniqueness * w.uniqueness)
        )

        # Determine recommendation based on score
        if self.buildability >= 8.0:
            self.recommendation = "build"
        elif self.buildability >= 5.0:
            self.recommendation = "review"
        else:
            self.recommendation = "skip"

        return self.buildability

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pattern_id": self.pattern.id,
            "pattern_name": self.pattern.name,
            "scores": {
                "frequency": self.frequency,
                "complexity": self.complexity,
                "value": self.value,
                "uniqueness": self.uniqueness,
            },
            "buildability": self.buildability,
            "recommendation": self.recommendation,
            "weights_used": self.weights_used.to_dict(),
        }
