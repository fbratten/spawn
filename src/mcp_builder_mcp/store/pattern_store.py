"""File-based pattern storage."""

from pathlib import Path
from typing import Any

import yaml

from mcp_builder_mcp.models import Pattern, ScoredPattern


class PatternStore:
    """File-based store for patterns using YAML."""

    DEFAULT_STORE_PATH = ".pattern-store"

    def __init__(self, store_path: Path | str | None = None):
        """Initialize pattern store.

        Args:
            store_path: Path to store directory. Uses default if not provided.
        """
        self.store_path = Path(store_path or self.DEFAULT_STORE_PATH)
        self.patterns_dir = self.store_path / "patterns"
        self.history_dir = self.store_path / "history"

        # Ensure directories exist
        self.patterns_dir.mkdir(parents=True, exist_ok=True)
        self.history_dir.mkdir(parents=True, exist_ok=True)

    def store(self, pattern: Pattern, scores: dict[str, float] | None = None) -> Path:
        """Store a pattern to disk.

        Args:
            pattern: Pattern to store.
            scores: Optional scores to include.

        Returns:
            Path to stored pattern file.
        """
        data = pattern.to_dict()

        # Add scores if provided
        if scores:
            data["scoring"] = scores

        # Generate filename from pattern ID
        filename = f"{self._safe_filename(pattern.id)}.yaml"
        filepath = self.patterns_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        return filepath

    def store_scored(self, scored: ScoredPattern) -> Path:
        """Store a scored pattern with its scores.

        Args:
            scored: Scored pattern to store.

        Returns:
            Path to stored pattern file.
        """
        scores = {
            "frequency": scored.frequency,
            "complexity": scored.complexity,
            "value": scored.value,
            "uniqueness": scored.uniqueness,
            "buildability": scored.buildability,
            "recommendation": scored.recommendation,
        }
        return self.store(scored.pattern, scores)

    def get(self, pattern_id: str) -> Pattern | None:
        """Get a pattern by ID.

        Args:
            pattern_id: Pattern identifier.

        Returns:
            Pattern if found, None otherwise.
        """
        filename = f"{self._safe_filename(pattern_id)}.yaml"
        filepath = self.patterns_dir / filename

        if not filepath.exists():
            return None

        with open(filepath, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return Pattern.from_dict(data)

    def list_all(self) -> list[Pattern]:
        """List all stored patterns.

        Returns:
            List of all patterns.
        """
        patterns = []

        for filepath in self.patterns_dir.glob("*.yaml"):
            with open(filepath, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if data:
                patterns.append(Pattern.from_dict(data))

        return patterns

    def search(
        self,
        query: str | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
        limit: int = 20,
    ) -> list[Pattern]:
        """Search patterns by query, category, or tags.

        Args:
            query: Text search in name and description.
            category: Filter by category.
            tags: Filter by tags (any match).
            limit: Maximum results.

        Returns:
            Matching patterns.
        """
        patterns = self.list_all()
        results = []

        for pattern in patterns:
            # Category filter
            if category and pattern.category != category:
                continue

            # Tag filter
            if tags and not any(t in pattern.tags for t in tags):
                continue

            # Text search
            if query:
                query_lower = query.lower()
                searchable = f"{pattern.name} {pattern.description}".lower()
                if query_lower not in searchable:
                    continue

            results.append(pattern)

            if len(results) >= limit:
                break

        return results

    def delete(self, pattern_id: str) -> bool:
        """Delete a pattern.

        Args:
            pattern_id: Pattern identifier.

        Returns:
            True if deleted, False if not found.
        """
        filename = f"{self._safe_filename(pattern_id)}.yaml"
        filepath = self.patterns_dir / filename

        if filepath.exists():
            filepath.unlink()
            return True
        return False

    def exists(self, pattern_id: str) -> bool:
        """Check if a pattern exists.

        Args:
            pattern_id: Pattern identifier.

        Returns:
            True if pattern exists.
        """
        filename = f"{self._safe_filename(pattern_id)}.yaml"
        filepath = self.patterns_dir / filename
        return filepath.exists()

    def count(self) -> int:
        """Count stored patterns.

        Returns:
            Number of patterns.
        """
        return len(list(self.patterns_dir.glob("*.yaml")))

    def record_outcome(
        self, pattern_id: str, outcome: str, notes: str | None = None
    ) -> None:
        """Record a build outcome for learning.

        Args:
            pattern_id: Pattern that was built.
            outcome: "success" or "failure".
            notes: Optional notes about the outcome.
        """
        from datetime import datetime

        history_file = self.history_dir / "builds.yaml"

        # Load existing history
        history: list[dict[str, Any]] = []
        if history_file.exists():
            with open(history_file, encoding="utf-8") as f:
                history = yaml.safe_load(f) or []

        # Add new entry
        history.append(
            {
                "pattern_id": pattern_id,
                "outcome": outcome,
                "date": datetime.now().isoformat(),
                "notes": notes,
            }
        )

        # Save history
        with open(history_file, "w", encoding="utf-8") as f:
            yaml.dump(history, f, default_flow_style=False)

    def get_outcomes(self, pattern_id: str | None = None) -> list[dict[str, Any]]:
        """Get build outcomes.

        Args:
            pattern_id: Filter by pattern. Returns all if not specified.

        Returns:
            List of outcome records.
        """
        history_file = self.history_dir / "builds.yaml"

        if not history_file.exists():
            return []

        with open(history_file, encoding="utf-8") as f:
            history: list[dict[str, Any]] = yaml.safe_load(f) or []

        if pattern_id:
            history = [h for h in history if h.get("pattern_id") == pattern_id]

        return history

    def _safe_filename(self, pattern_id: str) -> str:
        """Convert pattern ID to safe filename."""
        # Remove or replace unsafe characters
        safe = pattern_id.replace("/", "_").replace("\\", "_")
        safe = "".join(c for c in safe if c.isalnum() or c in "-_")
        return safe[:100]  # Limit length
