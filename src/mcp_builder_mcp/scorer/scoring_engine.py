"""Scoring engine for evaluating pattern buildability."""

from mcp_builder_mcp.models import Pattern, ScoredPattern, ScoreWeights


class ScoringEngine:
    """Engine for scoring patterns on buildability."""

    def __init__(self, weights: ScoreWeights | None = None):
        """Initialize scoring engine.

        Args:
            weights: Custom scoring weights. Uses defaults if not provided.
        """
        self.weights = weights or ScoreWeights()

    def score(self, pattern: Pattern) -> ScoredPattern:
        """Score a single pattern for buildability.

        Args:
            pattern: Pattern to score.

        Returns:
            ScoredPattern with individual scores and buildability.
        """
        scored = ScoredPattern(
            pattern=pattern,
            frequency=self._score_frequency(pattern),
            complexity=self._score_complexity(pattern),
            value=self._score_value(pattern),
            uniqueness=self._score_uniqueness(pattern),
            weights_used=self.weights,
        )

        scored.calculate_buildability(self.weights)
        return scored

    def rank(self, patterns: list[Pattern]) -> list[ScoredPattern]:
        """Score and rank patterns by buildability.

        Args:
            patterns: List of patterns to rank.

        Returns:
            List of ScoredPatterns sorted by buildability (descending).
        """
        scored = [self.score(p) for p in patterns]
        scored.sort(key=lambda s: s.buildability, reverse=True)
        return scored

    def recommend(
        self, patterns: list[Pattern], top_n: int = 3, threshold: float = 5.0
    ) -> list[ScoredPattern]:
        """Get top recommendations for building.

        Args:
            patterns: Patterns to evaluate.
            top_n: Maximum number of recommendations.
            threshold: Minimum buildability score to recommend.

        Returns:
            Top recommended patterns.
        """
        ranked = self.rank(patterns)
        recommendations = [s for s in ranked if s.buildability >= threshold]
        return recommendations[:top_n]

    def _score_frequency(self, pattern: Pattern) -> float:
        """Score based on how often the pattern appears.

        Score 1-5:
        - 5: Very common (>5 occurrences or strong indicators)
        - 4: Common (3-5 occurrences)
        - 3: Moderate (2-3 occurrences)
        - 2: Rare (1-2 occurrences)
        - 1: Very rare (single occurrence)
        """
        # Use confidence as a proxy for frequency in extracted patterns
        # Higher confidence often correlates with more complete/frequent patterns
        confidence = pattern.confidence

        # Also consider number of workflow steps (more steps = more comprehensive)
        step_count = len(pattern.workflow_steps)

        # And trigger count (more triggers = more ways to invoke = more common)
        trigger_count = len(pattern.triggers)

        # Weighted calculation
        base_score = confidence * 3  # 0-3 from confidence

        # Add step bonus (diminishing returns)
        if step_count > 0:
            base_score += min(1.0, step_count * 0.2)

        # Add trigger bonus
        if trigger_count > 0:
            base_score += min(1.0, trigger_count * 0.3)

        return min(5.0, max(1.0, base_score))

    def _score_complexity(self, pattern: Pattern) -> float:
        """Score implementation complexity (higher = more complex).

        Score 1-5:
        - 5: Very complex (external APIs, state management, async)
        - 4: Complex (multiple components, templates)
        - 3: Moderate (file operations, parsing)
        - 2: Simple (single operation, straightforward)
        - 1: Trivial (minimal code)
        """
        score = 1.0

        # More workflow steps = more complexity
        step_count = len(pattern.workflow_steps)
        score += min(2.0, step_count * 0.3)

        # More inputs = more complexity
        input_count = len(pattern.inputs)
        score += min(1.0, input_count * 0.2)

        # More outputs = more complexity
        output_count = len(pattern.outputs)
        score += min(0.5, output_count * 0.2)

        # Check for complexity indicators in workflow
        complex_actions = [
            "api",
            "external",
            "async",
            "database",
            "auth",
            "parse",
            "validate",
        ]
        for step in pattern.workflow_steps:
            action_lower = step.action.lower()
            if any(ca in action_lower for ca in complex_actions):
                score += 0.3

        return min(5.0, max(1.0, score))

    def _score_value(self, pattern: Pattern) -> float:
        """Score user benefit if automated.

        Score 1-5:
        - 5: High value (saves significant time, prevents errors)
        - 4: Good value (useful automation)
        - 3: Moderate value (nice to have)
        - 2: Low value (minimal benefit)
        - 1: Trivial value (almost no benefit)
        """
        score = 3.0  # Start with moderate value

        # Categories that tend to be high value
        high_value_categories = [
            "documentation",
            "testing",
            "validation",
            "git_workflow",
            "code_generation",
        ]
        if pattern.category in high_value_categories:
            score += 1.0

        # High value tags
        high_value_tags = [
            "automation",
            "validation",
            "documentation",
            "session",
            "handover",
        ]
        matching_tags = sum(1 for t in pattern.tags if t in high_value_tags)
        score += min(1.0, matching_tags * 0.3)

        # More outputs usually means more value delivered
        if len(pattern.outputs) > 0:
            score += min(0.5, len(pattern.outputs) * 0.2)

        # Patterns with clear triggers are more immediately usable
        if len(pattern.triggers) > 1:
            score += 0.5

        return min(5.0, max(1.0, score))

    def _score_uniqueness(self, pattern: Pattern) -> float:
        """Score how unique the pattern is (not covered by existing tools).

        Score 1-5:
        - 5: Completely unique
        - 4: Mostly unique (partial overlap)
        - 3: Moderately unique
        - 2: Significant overlap with existing
        - 1: Already covered by existing tools
        """
        # Known existing MCP tools (for overlap detection)
        existing_tools = {
            "smart-inventory": ["claude.md", "project analysis"],
            "next-conductor": ["next.md", "task tracking", "todo"],
            "paaf": ["audit", "project health", "debt"],
            "browser-mcp": ["browser", "screenshot", "click"],
            "content-extractor": ["ocr", "screenshot", "ui"],
            "research-agent": ["research", "sources", "citations"],
            "minna-memory": ["memory", "recall", "preferences"],
        }

        score = 5.0  # Start assuming unique

        # Check for overlaps
        pattern_text = " ".join(
            [
                pattern.name.lower(),
                pattern.description.lower(),
                pattern.category.lower(),
                " ".join(pattern.tags),
            ]
        )

        for _tool_name, keywords in existing_tools.items():
            overlap_count = sum(1 for kw in keywords if kw in pattern_text)
            if overlap_count > 0:
                # Each overlap reduces uniqueness
                score -= overlap_count * 0.5

        return min(5.0, max(1.0, score))
