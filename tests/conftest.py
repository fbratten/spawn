"""Shared test fixtures for pattern-mcp."""

from datetime import datetime
from pathlib import Path

import pytest

from mcp_builder_mcp import (
    Input,
    Output,
    Pattern,
    PatternStore,
    ScoreWeights,
    Session,
    Step,
    Trigger,
    Turn,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_log_content() -> str:
    """Small markdown log for testing."""
    return (
        "Human: Please create a session handover document\n\n"
        "Assistant: I'll create a session handover document for you.\n\n"
        "Let me first gather the git commits from today.\n\n"
        "I'll use the Bash tool to run git log.\n\n"
        "Now I'll read the relevant files that were modified.\n\n"
        "Using Read tool to check ai-memory/context.md\n\n"
        "Finally, I'll write the handover document.\n\n"
        "Using Write tool to create ai-memory/handover/2026-01-24-handover.md\n\n"
        "Done! The handover document has been created.\n\n"
        "Human: Thanks! Now please validate all links in the README\n\n"
        "Assistant: I'll validate the links in your README.\n\n"
        "Using Read to get README.md content.\n\n"
        "Using Bash to check each URL with curl.\n\n"
        "Found 2 broken links. Here's the report.\n"
    )


@pytest.fixture
def sample_log_file(tmp_path: Path, sample_log_content: str) -> Path:
    """Create a temporary log file."""
    log_file = tmp_path / "sample_log.md"
    log_file.write_text(sample_log_content)
    return log_file


@pytest.fixture
def empty_log_content() -> str:
    """Empty log for edge case testing."""
    return ""


@pytest.fixture
def mock_turn_user() -> Turn:
    """Mock user turn."""
    return Turn(
        role="user",
        content="Create a session handover document",
        tools_used=[],
        files_touched=[],
    )


@pytest.fixture
def mock_turn_assistant() -> Turn:
    """Mock assistant turn with tool usage."""
    return Turn(
        role="assistant",
        content="I'll create the handover document using git log and file operations.",
        tools_used=["Bash", "Read", "Write"],
        files_touched=[
            "/tmp/test-handover/doc.md",
        ],
    )


@pytest.fixture
def mock_session(mock_turn_user: Turn, mock_turn_assistant: Turn) -> Session:
    """Mock session with turns."""
    return Session(
        id="session-1",
        turns=[mock_turn_user, mock_turn_assistant],
        topic="Create handover document",
    )


@pytest.fixture
def mock_pattern() -> Pattern:
    """Pre-defined pattern for testing."""
    return Pattern(
        id="test-pattern-handover",
        name="Session Handover Generator",
        description="Generate a session handover document with commits, files, and context",
        version="1.0.0",
        extracted_from="test_log.md",
        extraction_date=datetime.now(),
        confidence=0.8,
        triggers=[
            Trigger(phrase="create handover"),
            Trigger(phrase="session handover"),
        ],
        inputs=[
            Input(name="project_path", type="path", required=True),
            Input(name="since_hours", type="integer", required=False, default=8),
        ],
        outputs=[
            Output(name="handover_document", type="file", format="markdown"),
        ],
        workflow_steps=[
            Step(id="step-1", action="Bash", description="Get git commits"),
            Step(id="step-2", action="Read", description="Read context files", depends_on=["step-1"]),
            Step(id="step-3", action="Write", description="Write handover", depends_on=["step-2"]),
        ],
        category="documentation",
        tags=["session", "handover", "git", "md"],
    )


@pytest.fixture
def mock_pattern_simple() -> Pattern:
    """Simple pattern with minimal fields."""
    return Pattern(
        id="test-pattern-simple",
        name="Simple Pattern",
        description="A simple test pattern",
        confidence=0.6,
        category="general",
    )


@pytest.fixture
def similar_patterns() -> list[Pattern]:
    """List of similar patterns for deduplication testing."""
    return [
        Pattern(
            id="pattern-1",
            name="Create Handover",
            triggers=[Trigger(phrase="create handover")],
            confidence=0.8,
        ),
        Pattern(
            id="pattern-2",
            name="Generate Handover",
            triggers=[Trigger(phrase="create handover")],  # Same trigger
            confidence=0.7,
        ),
        Pattern(
            id="pattern-3",
            name="Link Validator",
            triggers=[Trigger(phrase="validate links")],
            confidence=0.9,
        ),
    ]


@pytest.fixture
def custom_weights() -> ScoreWeights:
    """Custom scoring weights for testing."""
    return ScoreWeights(
        frequency=2.0,
        complexity=-1.0,
        value=2.0,
        uniqueness=1.0,
    )


@pytest.fixture
def temp_store(tmp_path: Path) -> PatternStore:
    """Temporary pattern store."""
    store_path = tmp_path / ".pattern-store"
    return PatternStore(store_path)


@pytest.fixture
def populated_store(temp_store: PatternStore, mock_pattern: Pattern, mock_pattern_simple: Pattern) -> PatternStore:
    """Store with test patterns."""
    temp_store.store(mock_pattern)
    temp_store.store(mock_pattern_simple)
    return temp_store


@pytest.fixture
def real_log_path() -> Path:
    """Path to actual project log (if exists)."""
    return Path("KB/note-2026-01-23.md")
