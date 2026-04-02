"""Tests for Minna Memory synchronization."""

from unittest.mock import MagicMock

import pytest

from mcp_builder_mcp import MinnaSync, Pattern, ScoredPattern
from mcp_builder_mcp.models import Step, Trigger


class TestMinnaSync:
    """Tests for MinnaSync."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock Minna Memory client."""
        client = MagicMock()
        client.memory_stats.return_value = {"entities": 10, "memories": 50}
        client.memory_store.return_value = {"id": 1}
        client.memory_recall.return_value = {"memories": []}
        client.memory_search.return_value = {"memories": []}
        return client

    @pytest.fixture
    def sync(self, mock_client):
        """Create MinnaSync with mock client."""
        return MinnaSync(memory_client=mock_client)

    @pytest.fixture
    def sync_no_client(self):
        """Create MinnaSync without client."""
        return MinnaSync(memory_client=None)

    @pytest.fixture
    def sample_pattern(self):
        """Create a sample pattern."""
        return Pattern(
            id="test-pattern-1",
            name="Test Pattern",
            description="A test pattern for testing",
            triggers=[Trigger(phrase="test"), Trigger(phrase="example")],
            workflow_steps=[Step(id="step1", action="test")],
            tags=["testing", "example"],
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

    def test_is_available_with_client(self, sync, mock_client):
        """Test availability check with working client."""
        assert sync.is_available() is True
        mock_client.memory_stats.assert_called_once()

    def test_is_available_cached(self, sync, mock_client):
        """Test availability is cached."""
        sync.is_available()
        sync.is_available()
        # Should only call once due to caching
        mock_client.memory_stats.assert_called_once()

    def test_is_available_without_client(self, sync_no_client):
        """Test availability without client."""
        assert sync_no_client.is_available() is False

    def test_is_available_client_error(self, mock_client):
        """Test availability when client raises error."""
        mock_client.memory_stats.side_effect = Exception("Connection failed")
        sync = MinnaSync(memory_client=mock_client)
        assert sync.is_available() is False

    def test_sync_pattern(self, sync, mock_client, sample_pattern):
        """Test syncing a pattern."""
        result = sync.sync_pattern(sample_pattern)
        assert result is True
        mock_client.memory_store.assert_called_once()

        call_args = mock_client.memory_store.call_args[0][0]
        assert "pattern:pattern-mcp:" in call_args["entity"]
        assert call_args["attribute"] == "definition"
        assert call_args["value"] == "Test Pattern"

    def test_sync_pattern_unavailable(self, sync_no_client, sample_pattern):
        """Test sync when unavailable."""
        result = sync_no_client.sync_pattern(sample_pattern)
        assert result is False

    def test_sync_scored(self, sync, mock_client, sample_scored):
        """Test syncing a scored pattern."""
        result = sync.sync_scored(sample_scored)
        assert result is True
        mock_client.memory_store.assert_called()

        call_args = mock_client.memory_store.call_args[0][0]
        assert call_args["attribute"] == "score"
        assert "buildability=0.60" in call_args["value"]
        assert "recommendation=buildable" in call_args["value"]

    def test_record_outcome(self, sync, mock_client):
        """Test recording build outcome."""
        result = sync.record_outcome("test-pattern-1", "success", "Build completed")
        assert result is True

        call_args = mock_client.memory_store.call_args[0][0]
        assert call_args["attribute"] == "build_outcome"
        assert call_args["value"] == "success"
        assert call_args["context"] == "Build completed"

    def test_record_outcome_no_notes(self, sync, mock_client):
        """Test recording outcome without notes."""
        result = sync.record_outcome("test-pattern-1", "failure")
        assert result is True

        call_args = mock_client.memory_store.call_args[0][0]
        assert call_args["context"] == ""

    def test_get_outcomes(self, sync, mock_client):
        """Test getting outcomes."""
        mock_client.memory_recall.return_value = {
            "memories": [
                {"value": "success", "context": "First build"},
                {"value": "failure", "context": "Second build"},
            ]
        }

        outcomes = sync.get_outcomes("test-pattern-1")
        assert len(outcomes) == 2
        assert outcomes[0]["value"] == "success"

    def test_get_outcomes_unavailable(self, sync_no_client):
        """Test getting outcomes when unavailable."""
        outcomes = sync_no_client.get_outcomes("test-pattern-1")
        assert outcomes == []

    def test_search_patterns(self, sync, mock_client):
        """Test searching patterns."""
        mock_client.memory_search.return_value = {
            "memories": [
                {"entity": "pattern:pattern-mcp:test", "value": "Test Pattern"},
            ]
        }

        results = sync.search_patterns("test", limit=5)
        assert len(results) == 1

        call_args = mock_client.memory_search.call_args[0][0]
        assert call_args["query"] == "test"
        assert call_args["limit"] == 5

    def test_search_patterns_unavailable(self, sync_no_client):
        """Test search when unavailable."""
        results = sync_no_client.search_patterns("test")
        assert results == []

    def test_find_similar(self, sync, mock_client, sample_pattern):
        """Test finding similar patterns."""
        mock_client.memory_search.return_value = {
            "memories": [
                {"entity": "pattern:pattern-mcp:similar", "value": "Similar Pattern"},
            ]
        }

        results = sync.find_similar(sample_pattern)
        assert len(results) == 1

        # Should search using pattern attributes
        call_args = mock_client.memory_search.call_args[0][0]
        assert "Test Pattern" in call_args["query"]
        assert call_args["limit"] == 5

    def test_pattern_entity_formatting(self, sync):
        """Test entity name formatting."""
        entity = sync._pattern_entity("Test Pattern ID")
        assert entity == "pattern:pattern-mcp:test-pattern-id"

        entity = sync._pattern_entity("UPPERCASE")
        assert entity == "pattern:pattern-mcp:uppercase"

    def test_call_minna_without_client(self, sync_no_client):
        """Test _call_minna raises without client."""
        with pytest.raises(RuntimeError, match="not configured"):
            sync_no_client._call_minna("memory_stats", {})
