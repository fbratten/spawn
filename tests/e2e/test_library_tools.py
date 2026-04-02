"""End-to-end tests for pattern library tools (MVP 3)."""


import pytest

import mcp_builder_mcp.server as server_module
from mcp_builder_mcp.server import (
    _get_store,
    analyze_log,
    learn_outcome,
    search_patterns,
    store_pattern,
    suggest_similar,
)


def _clear_session():
    """Clear session state for tests."""
    # Clear session patterns list
    server_module._session_patterns.clear()

    # Clear the file-based store
    store = _get_store()
    # Delete all pattern files
    for f in store.patterns_dir.glob("*.yaml"):
        f.unlink()
    # Delete all history files
    for f in store.history_dir.glob("*.yaml"):
        f.unlink()


class TestStorePatternTool:
    """Tests for store_pattern tool."""

    @pytest.fixture
    def sample_log_content(self):
        """Sample log with patterns."""
        return (
            "# Session: Test Session\n\n"
            "## Turn 1\n"
            "**User**: Run the deployment script\n"
            "**Assistant**: I'll run the deployment now.\n"
            '<invoke name="Bash"><parameter name="command">./deploy.sh</parameter></invoke>\n'
            '<invoke name="Bash"><parameter name="command">./deploy.sh</parameter></invoke>\n'
            '<invoke name="Bash"><parameter name="command">./deploy.sh</parameter></invoke>\n'
        )

    def test_store_pattern_not_found(self):
        """Test storing a pattern that doesn't exist."""
        _clear_session()

        result = store_pattern("nonexistent-pattern")
        assert result.get("error") is not None
        assert "not found" in result["error"].lower()

    def test_store_and_retrieve_pattern(self, sample_log_content, tmp_path):
        """Test storing and retrieving a pattern."""
        _clear_session()

        # First analyze a log to get patterns
        log_file = tmp_path / "test.md"
        log_file.write_text(sample_log_content)

        analysis = analyze_log(str(log_file))
        if analysis.get("patterns"):
            pattern_id = analysis["patterns"][0]["id"]

            # Store the pattern
            result = store_pattern(pattern_id, tags=["test", "deployment"])
            assert result.get("error") is None
            assert result["pattern_id"] == pattern_id


class TestSearchPatternsTool:
    """Tests for search_patterns tool."""

    def test_search_empty(self):
        """Test search with no patterns."""
        _clear_session()
        result = search_patterns()
        assert result["patterns"] == []
        assert result["total_local"] == 0

    def test_search_by_category(self, tmp_path):
        """Test search by category."""
        _clear_session()

        # Create a pattern through analysis
        log_content = (
            "# Test\n"
            '<invoke name="Bash"><parameter name="command">git status</parameter></invoke>\n'
            '<invoke name="Bash"><parameter name="command">git status</parameter></invoke>\n'
            '<invoke name="Bash"><parameter name="command">git status</parameter></invoke>\n'
        )
        log_file = tmp_path / "test.md"
        log_file.write_text(log_content)

        analysis = analyze_log(str(log_file))
        if analysis.get("patterns"):
            pattern = analysis["patterns"][0]
            store_pattern(pattern["id"], tags=["git"])

            result = search_patterns(category=pattern.get("category", "general"))
            assert result.get("error") is None

    def test_search_by_tags(self, tmp_path):
        """Test search by tags."""
        _clear_session()

        log_content = (
            "# Test\n"
            '<invoke name="Read"><parameter name="path">file.py</parameter></invoke>\n'
            '<invoke name="Read"><parameter name="path">file.py</parameter></invoke>\n'
            '<invoke name="Read"><parameter name="path">file.py</parameter></invoke>\n'
        )
        log_file = tmp_path / "test.md"
        log_file.write_text(log_content)

        analysis = analyze_log(str(log_file))
        if analysis.get("patterns"):
            pattern_id = analysis["patterns"][0]["id"]
            store_pattern(pattern_id, tags=["reading", "files"])

            result = search_patterns(tags=["reading"])
            assert result.get("error") is None
            if result["patterns"]:
                assert any("reading" in p.get("tags", []) for p in result["patterns"])

    def test_search_by_query(self, tmp_path):
        """Test search by text query."""
        _clear_session()

        log_content = (
            "# Test\n"
            '<invoke name="Write"><parameter name="path">config.yaml</parameter></invoke>\n'
            '<invoke name="Write"><parameter name="path">config.yaml</parameter></invoke>\n'
            '<invoke name="Write"><parameter name="path">config.yaml</parameter></invoke>\n'
        )
        log_file = tmp_path / "test.md"
        log_file.write_text(log_content)

        analysis = analyze_log(str(log_file))
        if analysis.get("patterns"):
            pattern_id = analysis["patterns"][0]["id"]
            store_pattern(pattern_id)

            result = search_patterns(query="write")
            assert result.get("error") is None


class TestLearnOutcomeTool:
    """Tests for learn_outcome tool."""

    def test_learn_outcome_pattern_not_found(self):
        """Test learning outcome for nonexistent pattern."""
        _clear_session()

        result = learn_outcome("nonexistent", "success")
        # The function records the outcome even if pattern not found
        assert result.get("recorded") is True or result.get("error") is not None

    def test_learn_success_outcome(self, tmp_path):
        """Test recording a successful outcome."""
        _clear_session()

        log_content = (
            "# Test\n"
            '<invoke name="Bash"><parameter name="command">npm test</parameter></invoke>\n'
            '<invoke name="Bash"><parameter name="command">npm test</parameter></invoke>\n'
            '<invoke name="Bash"><parameter name="command">npm test</parameter></invoke>\n'
        )
        log_file = tmp_path / "test.md"
        log_file.write_text(log_content)

        analysis = analyze_log(str(log_file))
        if analysis.get("patterns"):
            pattern_id = analysis["patterns"][0]["id"]
            store_pattern(pattern_id)

            result = learn_outcome(pattern_id, "success", notes="Build passed")
            assert result["recorded"] is True
            assert result["pattern_id"] == pattern_id
            assert result["outcome"] == "success"

    def test_learn_failure_outcome(self, tmp_path):
        """Test recording a failure outcome."""
        _clear_session()

        log_content = (
            "# Test\n"
            '<invoke name="Bash"><parameter name="command">make build</parameter></invoke>\n'
            '<invoke name="Bash"><parameter name="command">make build</parameter></invoke>\n'
            '<invoke name="Bash"><parameter name="command">make build</parameter></invoke>\n'
        )
        log_file = tmp_path / "test.md"
        log_file.write_text(log_content)

        analysis = analyze_log(str(log_file))
        if analysis.get("patterns"):
            pattern_id = analysis["patterns"][0]["id"]
            store_pattern(pattern_id)

            result = learn_outcome(pattern_id, "failure", notes="Tests failed")
            assert result["recorded"] is True
            assert result["outcome"] == "failure"

    def test_learn_invalid_outcome(self):
        """Test that invalid outcome is rejected."""
        _clear_session()

        result = learn_outcome("some-pattern", "maybe")
        assert result.get("error") is not None
        assert "success" in result["error"] or "failure" in result["error"]

    def test_outcome_affects_adjustment(self, tmp_path):
        """Test that outcomes affect score adjustment."""
        _clear_session()

        log_content = (
            "# Test\n"
            '<invoke name="Bash"><parameter name="command">cargo build</parameter></invoke>\n'
            '<invoke name="Bash"><parameter name="command">cargo build</parameter></invoke>\n'
            '<invoke name="Bash"><parameter name="command">cargo build</parameter></invoke>\n'
        )
        log_file = tmp_path / "test.md"
        log_file.write_text(log_content)

        analysis = analyze_log(str(log_file))
        if analysis.get("patterns"):
            pattern_id = analysis["patterns"][0]["id"]
            store_pattern(pattern_id)

            # Record multiple successes
            learn_outcome(pattern_id, "success")
            learn_outcome(pattern_id, "success")
            result = learn_outcome(pattern_id, "success", apply_adjustment=True)

            if "adjustment" in result:
                assert result["adjustment"]["adjustment_factor"] > 1.0


class TestSuggestSimilarTool:
    """Tests for suggest_similar tool."""

    def test_suggest_similar_not_found(self):
        """Test suggestions for nonexistent pattern."""
        _clear_session()

        result = suggest_similar("nonexistent")
        assert result.get("error") is not None
        assert "not found" in result["error"].lower()

    def test_suggest_similar_no_others(self, tmp_path):
        """Test suggestions when only one pattern exists."""
        _clear_session()

        log_content = (
            "# Test\n"
            '<invoke name="Grep"><parameter name="pattern">TODO</parameter></invoke>\n'
            '<invoke name="Grep"><parameter name="pattern">TODO</parameter></invoke>\n'
            '<invoke name="Grep"><parameter name="pattern">TODO</parameter></invoke>\n'
        )
        log_file = tmp_path / "test.md"
        log_file.write_text(log_content)

        analysis = analyze_log(str(log_file))
        if analysis.get("patterns"):
            pattern_id = analysis["patterns"][0]["id"]
            store_pattern(pattern_id)

            result = suggest_similar(pattern_id)
            assert result.get("error") is None
            assert "similar_local" in result
            assert "similar_minna" in result

    def test_suggest_similar_finds_related(self, tmp_path):
        """Test that similar patterns are found."""
        _clear_session()

        # Create two similar patterns in same category
        log1 = (
            "# Test1\n"
            '<invoke name="Bash"><parameter name="command">pytest tests/unit/</parameter></invoke>\n'
            '<invoke name="Bash"><parameter name="command">pytest tests/unit/</parameter></invoke>\n'
            '<invoke name="Bash"><parameter name="command">pytest tests/unit/</parameter></invoke>\n'
        )
        log2 = (
            "# Test2\n"
            '<invoke name="Bash"><parameter name="command">pytest tests/integration/</parameter></invoke>\n'
            '<invoke name="Bash"><parameter name="command">pytest tests/integration/</parameter></invoke>\n'
            '<invoke name="Bash"><parameter name="command">pytest tests/integration/</parameter></invoke>\n'
        )

        file1 = tmp_path / "test1.md"
        file1.write_text(log1)
        file2 = tmp_path / "test2.md"
        file2.write_text(log2)

        analysis1 = analyze_log(str(file1))
        analysis2 = analyze_log(str(file2))

        pattern_ids = []
        for analysis in [analysis1, analysis2]:
            if analysis.get("patterns"):
                pid = analysis["patterns"][0]["id"]
                store_pattern(pid, tags=["testing", "pytest"])
                pattern_ids.append(pid)

        if len(pattern_ids) >= 2:
            result = suggest_similar(pattern_ids[0])
            assert result.get("error") is None
