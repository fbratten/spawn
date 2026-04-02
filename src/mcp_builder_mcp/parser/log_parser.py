"""Log parser for markdown dialogue logs."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Turn:
    """A single turn in a dialogue (user or assistant)."""

    role: str  # "user" or "assistant"
    content: str
    timestamp: str | None = None
    tools_used: list[str] = field(default_factory=list)
    files_touched: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "tools_used": self.tools_used,
            "files_touched": self.files_touched,
        }


@dataclass
class Session:
    """A logical session of related turns."""

    id: str
    turns: list[Turn] = field(default_factory=list)
    topic: str = ""
    start_marker: str | None = None
    end_marker: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "topic": self.topic,
            "turns": [t.to_dict() for t in self.turns],
            "start_marker": self.start_marker,
            "end_marker": self.end_marker,
        }


@dataclass
class DialogueLog:
    """Parsed dialogue log."""

    source_path: str
    raw_content: str
    turns: list[Turn] = field(default_factory=list)
    sessions: list[Session] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source_path": self.source_path,
            "turns_count": len(self.turns),
            "sessions_count": len(self.sessions),
            "metadata": self.metadata,
        }


class LogParser:
    """Parser for markdown dialogue logs."""

    # Patterns for detecting turns
    USER_PATTERNS = [
        r"^Human:\s*(.*)$",
        r"^User:\s*(.*)$",
        r"^>\s*Human:\s*(.*)$",
        r"^\*\*Human\*\*:\s*(.*)$",
        r"^\*\*User\*\*:\s*(.*)$",
        # Observation-style logs
        r"^❯\s*(.*)$",  # Prompt marker
        r"^>\s+(.*)$",  # Quote as user request
    ]

    ASSISTANT_PATTERNS = [
        r"^Assistant:\s*(.*)$",
        r"^Claude:\s*(.*)$",
        r"^AI:\s*(.*)$",
        r"^\*\*Assistant\*\*:\s*(.*)$",
        r"^\*\*Claude\*\*:\s*(.*)$",
        # Observation-style logs
        r"^●\s*(.*)$",  # Bullet marker for Claude actions
        r"^•\s*(.*)$",  # Alternative bullet
    ]

    # Patterns for detecting tool usage
    # Note: Group 1 should capture the tool name for all patterns
    TOOL_PATTERNS = [
        r"<invoke name=\"([^\"]+)\"",
        r"(mcp__[a-z_-]+__[a-z_]+)",
        # Observation-style tool mentions: "● Read(file)" or just "Read(file)"
        r"●?\s*(Bash)\([^)]+\)",
        r"●?\s*(Read)\([^)]+\)",
        r"●?\s*(Write)\([^)]+\)",
        r"●?\s*(Edit)\([^)]+\)",
        r"●?\s*(Glob)\([^)]+\)",
        r"●?\s*(Grep)\([^)]+\)",
        r"●?\s*(Task)\([^)]+\)",
        # Text descriptions of tool usage
        r"\b(git (?:status|push|pull|commit|add|log|diff))\b",
        r"\b(pytest|ruff|npm|pip|uv)\b",
    ]

    # Patterns for detecting file paths
    FILE_PATTERNS = [
        r"/mnt/[a-z]/[^\s\"\'\)\]]+",
        r"[A-Z]:\\[^\s\"\'\)\]]+",
        r"\./[^\s\"\'\)\]]+",
    ]

    # Session boundary markers
    SESSION_MARKERS = [
        r"^#{1,2}\s+Session",
        r"^---+$",
        r"^#{1,2}\s+\d{4}-\d{2}-\d{2}",
    ]

    def parse(self, log_path: Path | str) -> DialogueLog:
        """Parse a markdown log file into structured dialogue.

        Args:
            log_path: Path to the markdown log file.

        Returns:
            Parsed DialogueLog with turns and sessions.
        """
        path = Path(log_path)
        if not path.exists():
            raise FileNotFoundError(f"Log file not found: {path}")

        content = path.read_text(encoding="utf-8")
        return self.parse_content(content, str(path))

    def parse_content(self, content: str, source_path: str = "<string>") -> DialogueLog:
        """Parse log content directly.

        Args:
            content: The raw log content.
            source_path: Source identifier for the log.

        Returns:
            Parsed DialogueLog.
        """
        if not content.strip():
            return DialogueLog(source_path=source_path, raw_content=content)

        turns = self.extract_turns(content)
        sessions = self.identify_sessions(turns, content)

        return DialogueLog(
            source_path=source_path,
            raw_content=content,
            turns=turns,
            sessions=sessions,
            metadata={
                "total_turns": len(turns),
                "total_sessions": len(sessions),
                "content_length": len(content),
            },
        )

    def extract_turns(self, content: str) -> list[Turn]:
        """Extract user/assistant turns from log content.

        Args:
            content: Raw log content.

        Returns:
            List of extracted turns.
        """
        turns: list[Turn] = []
        lines = content.split("\n")

        current_role: str | None = None
        current_content: list[str] = []

        for line in lines:
            # Check for section separator - ends current turn
            if re.match(r"^---+\s*$", line):
                if current_role and current_content:
                    turns.append(self._create_turn(current_role, current_content))
                current_role = None
                current_content = []
                continue

            # Check for user turn start
            for pattern in self.USER_PATTERNS:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    # Save previous turn if exists
                    if current_role and current_content:
                        turns.append(self._create_turn(current_role, current_content))
                    current_role = "user"
                    current_content = [match.group(1)] if match.group(1) else []
                    break
            else:
                # Check for assistant turn start
                for pattern in self.ASSISTANT_PATTERNS:
                    match = re.match(pattern, line, re.IGNORECASE)
                    if match:
                        if current_role and current_content:
                            turns.append(self._create_turn(current_role, current_content))
                        current_role = "assistant"
                        current_content = [match.group(1)] if match.group(1) else []
                        break
                else:
                    # Continue current turn
                    if current_role is not None:
                        current_content.append(line)

        # Don't forget the last turn
        if current_role and current_content:
            turns.append(self._create_turn(current_role, current_content))

        return turns

    def _create_turn(self, role: str, content_lines: list[str]) -> Turn:
        """Create a Turn from accumulated content lines."""
        content = "\n".join(content_lines).strip()

        # Extract tools used
        tools_used = []
        for pattern in self.TOOL_PATTERNS:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, tuple):
                    tools_used.append("_".join(match))
                else:
                    tools_used.append(match)

        # Extract files touched
        files_touched = []
        for pattern in self.FILE_PATTERNS:
            matches = re.findall(pattern, content)
            files_touched.extend(matches)

        return Turn(
            role=role,
            content=content,
            tools_used=list(set(tools_used)),
            files_touched=list(set(files_touched)),
        )

    def identify_sessions(self, turns: list[Turn], content: str) -> list[Session]:
        """Group turns into logical sessions.

        Args:
            turns: List of extracted turns.
            content: Original content for session boundary detection.

        Returns:
            List of sessions.
        """
        if not turns:
            return []

        # For now, simple heuristic: group turns between session markers
        # or create one session for all turns if no markers found
        sessions: list[Session] = []

        # Check if content has explicit session markers
        has_markers = any(
            re.search(pattern, content, re.MULTILINE) for pattern in self.SESSION_MARKERS
        )

        if not has_markers:
            # Single session with all turns
            sessions.append(
                Session(
                    id="session-1",
                    turns=turns,
                    topic=self._infer_topic(turns),
                )
            )
        else:
            # Split by markers (simplified - can be enhanced)
            current_turns: list[Turn] = []
            session_count = 0

            for turn in turns:
                current_turns.append(turn)

                # Check if this turn's content suggests session end
                if "wrap up" in turn.content.lower() or "handover" in turn.content.lower():
                    session_count += 1
                    sessions.append(
                        Session(
                            id=f"session-{session_count}",
                            turns=current_turns.copy(),
                            topic=self._infer_topic(current_turns),
                        )
                    )
                    current_turns = []

            # Remaining turns form last session
            if current_turns:
                session_count += 1
                sessions.append(
                    Session(
                        id=f"session-{session_count}",
                        turns=current_turns,
                        topic=self._infer_topic(current_turns),
                    )
                )

        return sessions

    def _infer_topic(self, turns: list[Turn]) -> str:
        """Infer session topic from turns content."""
        if not turns:
            return ""

        # Get first user turn for topic hint
        for turn in turns:
            if turn.role == "user" and turn.content:
                # Take first 100 chars as topic hint
                topic = turn.content[:100].strip()
                if "\n" in topic:
                    topic = topic.split("\n")[0]
                return topic

        return ""
