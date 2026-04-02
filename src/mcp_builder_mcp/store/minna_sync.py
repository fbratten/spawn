"""Minna Memory synchronization for pattern storage."""

from typing import Any

from mcp_builder_mcp.models import Pattern, ScoredPattern


class MinnaSync:
    """Synchronize patterns with Minna Memory for cross-session persistence."""

    # Entity naming convention
    ENTITY_PREFIX = "pattern:pattern-mcp:"
    OUTCOME_ATTRIBUTE = "build_outcome"
    DEFINITION_ATTRIBUTE = "definition"
    SCORE_ATTRIBUTE = "score"

    def __init__(self, memory_client: Any | None = None):
        """Initialize Minna sync.

        Args:
            memory_client: Optional Minna memory client. Uses MCP calls if not provided.
        """
        self._client = memory_client
        self._available: bool | None = None

    def is_available(self) -> bool:
        """Check if Minna Memory is available."""
        if self._available is not None:
            return self._available

        try:
            # Try to get stats to verify connection
            self._call_minna("memory_stats", {})
            self._available = True
        except Exception:
            self._available = False

        return self._available

    def sync_pattern(self, pattern: Pattern) -> bool:
        """Sync a pattern to Minna Memory.

        Args:
            pattern: Pattern to sync.

        Returns:
            True if synced successfully.
        """
        if not self.is_available():
            return False

        try:
            entity = self._pattern_entity(pattern.id)

            # Store pattern definition
            self._call_minna(
                "memory_store",
                {
                    "entity": entity,
                    "attribute": self.DEFINITION_ATTRIBUTE,
                    "value": pattern.name,
                    "context": pattern.description[:200] if pattern.description else "",
                },
            )

            return True
        except Exception:
            return False

    def sync_scored(self, scored: ScoredPattern) -> bool:
        """Sync a scored pattern to Minna Memory.

        Args:
            scored: Scored pattern to sync.

        Returns:
            True if synced successfully.
        """
        if not self.is_available():
            return False

        try:
            entity = self._pattern_entity(scored.pattern.id)

            # Store score
            score_value = (
                f"buildability={scored.buildability:.2f}, "
                f"recommendation={scored.recommendation}"
            )
            self._call_minna(
                "memory_store",
                {
                    "entity": entity,
                    "attribute": self.SCORE_ATTRIBUTE,
                    "value": score_value,
                    "context": f"freq={scored.frequency:.1f}, val={scored.value:.1f}",
                },
            )

            return True
        except Exception:
            return False

    def record_outcome(
        self, pattern_id: str, outcome: str, notes: str | None = None
    ) -> bool:
        """Record a build outcome in Minna Memory.

        Args:
            pattern_id: Pattern that was built.
            outcome: "success" or "failure".
            notes: Optional notes.

        Returns:
            True if recorded successfully.
        """
        if not self.is_available():
            return False

        try:
            entity = self._pattern_entity(pattern_id)

            self._call_minna(
                "memory_store",
                {
                    "entity": entity,
                    "attribute": self.OUTCOME_ATTRIBUTE,
                    "value": outcome,
                    "context": notes or "",
                },
            )

            return True
        except Exception:
            return False

    def get_outcomes(self, pattern_id: str) -> list[dict[str, Any]]:
        """Get build outcomes from Minna Memory.

        Args:
            pattern_id: Pattern to get outcomes for.

        Returns:
            List of outcome records.
        """
        if not self.is_available():
            return []

        try:
            entity = self._pattern_entity(pattern_id)
            result = self._call_minna(
                "memory_recall",
                {
                    "entity": entity,
                    "attribute": self.OUTCOME_ATTRIBUTE,
                    "limit": 20,
                },
            )
            return result.get("memories", [])
        except Exception:
            return []

    def search_patterns(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search patterns in Minna Memory.

        Args:
            query: Search query.
            limit: Maximum results.

        Returns:
            List of matching memories.
        """
        if not self.is_available():
            return []

        try:
            result = self._call_minna(
                "memory_search",
                {"query": query, "limit": limit},
            )
            return result.get("memories", [])
        except Exception:
            return []

    def find_similar(self, pattern: Pattern) -> list[dict[str, Any]]:
        """Find similar patterns in Minna Memory.

        Args:
            pattern: Pattern to find similar to.

        Returns:
            List of similar pattern memories.
        """
        # Build search query from pattern attributes
        query_parts = [pattern.name]
        if pattern.description:
            query_parts.append(pattern.description[:50])
        query_parts.extend(pattern.tags[:3])

        query = " ".join(query_parts)
        return self.search_patterns(query, limit=5)

    def _pattern_entity(self, pattern_id: str) -> str:
        """Create entity name for pattern."""
        # Clean pattern ID for entity name
        clean_id = pattern_id.replace(" ", "-").lower()
        return f"{self.ENTITY_PREFIX}{clean_id}"

    def _call_minna(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        """Call Minna Memory method.

        This is a placeholder that should be replaced with actual MCP calls
        in the server context.
        """
        if self._client:
            return getattr(self._client, method)(params)

        # Fallback: raise to indicate unavailable
        raise RuntimeError("Minna Memory not configured")
