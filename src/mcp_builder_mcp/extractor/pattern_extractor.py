"""Pattern extractor for identifying workflow patterns from parsed logs."""

import hashlib
import re
from datetime import datetime

from mcp_builder_mcp.models import Input, Output, Pattern, Step, Trigger
from mcp_builder_mcp.parser import DialogueLog, Session, Turn


class PatternExtractor:
    """Extracts workflow patterns from parsed dialogue logs."""

    # Known workflow indicators
    WORKFLOW_INDICATORS = [
        r"let me\s+(\w+)",
        r"I'll\s+(\w+)",
        r"first,?\s+I'll\s+(\w+)",
        r"next,?\s+I'll\s+(\w+)",
        r"then\s+I'll\s+(\w+)",
        r"finally,?\s+I'll\s+(\w+)",
    ]

    # Common trigger phrases
    TRIGGER_PHRASES = [
        r"(create|generate|build|make)\s+a?\s*(\w+)",
        r"(run|execute)\s+(\w+)",
        r"(analyze|review|check)\s+(\w+)",
        r"(update|modify|edit)\s+(\w+)",
        r"(commit|push|deploy)\s+(\w+)?",
        r"(summarize|extract|parse)\s+(\w+)",
    ]

    # Input extraction patterns
    INPUT_PATTERNS = [
        (r"file[:\s]+([^\s,]+)", "path"),
        (r"path[:\s]+([^\s,]+)", "path"),
        (r"directory[:\s]+([^\s,]+)", "path"),
        (r"(\d+)\s*(files?|items?)", "integer"),
        (r"\"([^\"]+)\"", "string"),
        (r"'([^']+)'", "string"),
    ]

    def __init__(self, min_confidence: float = 0.5):
        """Initialize extractor.

        Args:
            min_confidence: Minimum confidence threshold for pattern extraction.
        """
        self.min_confidence = min_confidence

    def extract(self, log: DialogueLog) -> list[Pattern]:
        """Extract patterns from a parsed dialogue log.

        Args:
            log: Parsed dialogue log.

        Returns:
            List of extracted patterns.
        """
        patterns: list[Pattern] = []

        # Extract from sessions if available
        if log.sessions:
            for session in log.sessions:
                session_patterns = self._extract_from_session(session, log.source_path)
                patterns.extend(session_patterns)
        elif log.turns:
            # Create single virtual session
            virtual_session = Session(id="virtual-1", turns=log.turns)
            patterns = self._extract_from_session(virtual_session, log.source_path)

        # Deduplicate patterns
        return self.deduplicate(patterns)

    def _extract_from_session(self, session: Session, source: str) -> list[Pattern]:
        """Extract patterns from a single session."""
        patterns: list[Pattern] = []

        # Get assistant turns with tool usage
        tool_sequences = self._find_tool_sequences(session.turns)

        for seq in tool_sequences:
            pattern = self._sequence_to_pattern(seq, session, source)
            if pattern and pattern.confidence >= self.min_confidence:
                patterns.append(pattern)

        return patterns

    def _find_tool_sequences(self, turns: list[Turn]) -> list[list[Turn]]:
        """Find sequences of turns that represent coherent workflows."""
        sequences: list[list[Turn]] = []
        current_seq: list[Turn] = []

        for turn in turns:
            if turn.role == "user":
                # User turn starts a new potential sequence
                if current_seq:
                    sequences.append(current_seq)
                current_seq = [turn]
            elif turn.role == "assistant" and current_seq:
                # Add assistant turn to current sequence
                current_seq.append(turn)

                # Check if this is a completion point
                if self._is_workflow_complete(turn):
                    sequences.append(current_seq)
                    current_seq = []

        # Don't forget the last sequence
        if current_seq:
            sequences.append(current_seq)

        # Filter out sequences without tool usage
        return [seq for seq in sequences if self._has_tool_usage(seq)]

    def _has_tool_usage(self, turns: list[Turn]) -> bool:
        """Check if any turn in sequence has tool usage."""
        return any(turn.tools_used for turn in turns)

    def _is_workflow_complete(self, turn: Turn) -> bool:
        """Check if a turn indicates workflow completion."""
        completion_indicators = [
            "done",
            "complete",
            "finished",
            "created",
            "generated",
            "saved",
            "committed",
        ]
        content_lower = turn.content.lower()
        return any(ind in content_lower for ind in completion_indicators)

    def _sequence_to_pattern(
        self, turns: list[Turn], session: Session, source: str
    ) -> Pattern | None:
        """Convert a turn sequence to a pattern."""
        if not turns:
            return None

        # Get user request (first user turn)
        user_turn = next((t for t in turns if t.role == "user"), None)
        if not user_turn:
            return None

        # Skip one-off specific instructions that aren't reusable patterns
        if self._is_specific_instruction(user_turn.content):
            return None

        # Extract triggers from user request
        triggers = self._extract_triggers(user_turn.content)

        # Get all assistant turns
        assistant_turns = [t for t in turns if t.role == "assistant"]

        # Extract workflow steps
        steps = self._extract_steps(assistant_turns)

        # Extract inputs and outputs
        inputs = self._extract_inputs(turns)
        outputs = self._extract_outputs(assistant_turns)

        # Calculate confidence based on completeness
        confidence = self._calculate_confidence(triggers, steps, inputs, outputs)

        # Generate pattern ID
        pattern_id = self._generate_id(user_turn.content)

        # Infer name from triggers or content
        name = self._infer_name(triggers, user_turn.content)

        return Pattern(
            id=pattern_id,
            name=name,
            description=user_turn.content[:200].strip(),
            extracted_from=source,
            extraction_date=datetime.now(),
            confidence=confidence,
            triggers=triggers,
            inputs=inputs,
            outputs=outputs,
            workflow_steps=steps,
            category=self._infer_category(steps),
            tags=self._extract_tags(turns),
            source_context=session.topic or "",
        )

    def _is_specific_instruction(self, content: str) -> bool:
        """Check if content is a specific one-off instruction vs. a reusable pattern.

        One-off instructions typically:
        - Reference specific URLs, paths, or projects
        - Contain multiple specific file names or commit hashes
        - Are very long and detailed
        - Don't follow generic action patterns
        """
        # Very long requests are usually specific instructions
        if len(content) > 200:
            return True

        # Contains URLs (likely project-specific)
        if re.search(r"https?://[^\s]+", content):
            return True

        # Contains multiple specific paths/files
        path_count = len(re.findall(r"[/\\][\w.-]+[/\\][\w.-]+", content))
        if path_count >= 2:
            return True

        # Contains commit hashes or specific references
        if re.search(r"\b[a-f0-9]{6,40}\b", content):
            return True

        # Starts with generic action verbs = likely a pattern
        generic_starts = [
            r"^check\s+(?:all|the)\s+",
            r"^run\s+(?:the\s+)?tests?",
            r"^create\s+(?:a\s+)?",
            r"^generate\s+",
            r"^update\s+(?:the\s+)?(?:documentation|docs|readme)",
            r"^deploy\s+",
            r"^fix\s+(?:the\s+)?(?:broken\s+)?",
            r"^review\s+",
            r"^analyze\s+",
        ]
        for pattern in generic_starts:
            if re.match(pattern, content.lower()):
                return False  # This looks like a generic pattern

        # If content mentions "this", "that", "those" at start, likely specific
        return bool(re.match(r"^(?:this|that|those|these)\s+", content.lower()))

    def _extract_triggers(self, content: str) -> list[Trigger]:
        """Extract trigger phrases from user content."""
        triggers: list[Trigger] = []

        for pattern in self.TRIGGER_PHRASES:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                phrase = " ".join(match).strip() if isinstance(match, tuple) else match.strip()
                if phrase:
                    triggers.append(Trigger(phrase=phrase))

        # If no triggers found, use first sentence as trigger
        if not triggers:
            first_sentence = content.split(".")[0].strip()[:100]
            if first_sentence:
                triggers.append(Trigger(phrase=first_sentence))

        return triggers

    def _extract_steps(self, assistant_turns: list[Turn]) -> list[Step]:
        """Extract workflow steps from assistant turns."""
        steps: list[Step] = []
        step_count = 0

        for turn in assistant_turns:
            # Each tool used becomes a step
            for tool in turn.tools_used:
                step_count += 1
                steps.append(
                    Step(
                        id=f"step-{step_count}",
                        action=tool,
                        description=self._infer_step_description(tool, turn.content),
                        depends_on=[f"step-{step_count - 1}"] if step_count > 1 else [],
                    )
                )

        return steps

    def _infer_step_description(self, tool: str, context: str) -> str:
        """Infer step description from tool name and context."""
        tool_descriptions = {
            "Read": "Read file contents",
            "Write": "Write file",
            "Edit": "Edit file",
            "Bash": "Execute shell command",
            "Glob": "Find files by pattern",
            "Grep": "Search file contents",
            "Task": "Spawn subagent",
        }

        # Check for known tool
        for known, desc in tool_descriptions.items():
            if known.lower() in tool.lower():
                return desc

        # Try to find relevant context
        lines = context.split("\n")[:5]
        for line in lines:
            if tool.lower() in line.lower():
                return line.strip()[:100]

        return f"Execute {tool}"

    def _extract_inputs(self, turns: list[Turn]) -> list[Input]:
        """Extract input parameters from turns."""
        inputs: list[Input] = []
        seen_names: set[str] = set()

        for turn in turns:
            # Extract from files touched
            for _file_path in turn.files_touched:
                name = "file_path"
                if name not in seen_names:
                    inputs.append(
                        Input(
                            name=name,
                            type="path",
                            required=True,
                            description="Path to input file",
                        )
                    )
                    seen_names.add(name)

            # Extract from content patterns
            for pattern, input_type in self.INPUT_PATTERNS:
                matches = re.findall(pattern, turn.content)
                if matches and input_type not in seen_names:
                    inputs.append(
                        Input(
                            name=f"input_{input_type}",
                            type=input_type,
                            required=False,
                        )
                    )
                    seen_names.add(input_type)

        return inputs

    def _extract_outputs(self, assistant_turns: list[Turn]) -> list[Output]:
        """Extract outputs from assistant turns."""
        outputs: list[Output] = []

        for turn in assistant_turns:
            # Files written are outputs
            for file_path in turn.files_touched:
                # Determine output type from extension
                if file_path.endswith(".md"):
                    outputs.append(
                        Output(name="markdown_file", type="file", format="markdown")
                    )
                elif file_path.endswith(".yaml") or file_path.endswith(".yml"):
                    outputs.append(Output(name="yaml_file", type="file", format="yaml"))
                elif file_path.endswith(".json"):
                    outputs.append(Output(name="json_file", type="file", format="json"))
                elif file_path.endswith(".py"):
                    outputs.append(
                        Output(name="python_file", type="file", format="python")
                    )

        # Deduplicate by name
        seen = set()
        unique_outputs = []
        for out in outputs:
            if out.name not in seen:
                unique_outputs.append(out)
                seen.add(out.name)

        return unique_outputs

    def _calculate_confidence(
        self,
        triggers: list[Trigger],
        steps: list[Step],
        inputs: list[Input],
        outputs: list[Output],
    ) -> float:
        """Calculate confidence score for a pattern."""
        score = 0.0

        # Triggers contribute 0.2
        if triggers:
            score += 0.2

        # Steps contribute 0.4 (more steps = more complete)
        if steps:
            score += min(0.4, len(steps) * 0.1)

        # Inputs contribute 0.2
        if inputs:
            score += 0.2

        # Outputs contribute 0.2
        if outputs:
            score += 0.2

        return min(1.0, score)

    def _generate_id(self, content: str) -> str:
        """Generate a unique pattern ID from content."""
        hash_input = content[:100].lower().strip()
        short_hash = hashlib.md5(hash_input.encode()).hexdigest()[:8]
        return f"pattern-{short_hash}"

    def _infer_name(self, triggers: list[Trigger], content: str) -> str:
        """Infer a human-readable pattern name."""
        # Try to extract a meaningful name from the action verb + object
        action_patterns = [
            # "check all links" -> "Link Checker"
            r"\b(check|verify|validate)\s+(?:all\s+)?(?:the\s+)?(\w+)",
            # "fix broken links" -> "Link Fixer"
            r"\b(fix|repair|correct)\s+(?:broken\s+|all\s+)?(?:the\s+)?(\w+)",
            # "create handover" -> "Handover Creator"
            r"\b(create|generate|build|make)\s+(?:a\s+)?(?:the\s+)?(\w+)",
            # "run tests" -> "Test Runner"
            r"\b(run|execute)\s+(?:the\s+)?(\w+)",
            # "update documentation" -> "Documentation Updater"
            r"\b(update|modify|edit)\s+(?:the\s+)?(\w+)",
            # "deploy to production" -> "Production Deployer"
            r"\b(deploy|push)\s+(?:to\s+)?(\w+)?",
            # "analyze logs" -> "Log Analyzer"
            r"\b(analyze|review|audit)\s+(?:the\s+)?(\w+)",
        ]

        action_to_suffix = {
            "check": "Checker",
            "verify": "Verifier",
            "validate": "Validator",
            "fix": "Fixer",
            "repair": "Fixer",
            "correct": "Fixer",
            "create": "Creator",
            "generate": "Generator",
            "build": "Builder",
            "make": "Maker",
            "run": "Runner",
            "execute": "Runner",
            "update": "Updater",
            "modify": "Modifier",
            "edit": "Editor",
            "deploy": "Deployer",
            "push": "Pusher",
            "analyze": "Analyzer",
            "review": "Reviewer",
            "audit": "Auditor",
        }

        # Search in content for action patterns
        search_text = content.lower()
        for pattern in action_patterns:
            match = re.search(pattern, search_text, re.IGNORECASE)
            if match:
                action = match.group(1).lower()
                obj = match.group(2) if len(match.groups()) > 1 and match.group(2) else ""
                suffix = action_to_suffix.get(action, "Handler")
                if obj:
                    # Singularize common plurals
                    if obj.endswith("s") and len(obj) > 3:
                        obj = obj[:-1]
                    return f"{obj.title()} {suffix}"
                return suffix

        # Fallback: look at tools used and infer from workflow
        if triggers and triggers[0].phrase:
            # Clean up trigger phrase
            phrase = triggers[0].phrase
            phrase = re.sub(r"[^\w\s]", "", phrase)
            words = [w for w in phrase.split() if len(w) > 2][:3]
            if words:
                return " ".join(words).title()

        # Last resort: generic name based on first meaningful words
        words = re.findall(r"\b[a-zA-Z]{3,}\b", content)
        meaningful = [w for w in words[:10] if w.lower() not in
                     {"the", "and", "for", "are", "that", "this", "with", "from", "have", "will"}]
        if meaningful:
            return " ".join(meaningful[:2]).title() + " Workflow"

        return "Unnamed Workflow"

    def _infer_category(self, steps: list[Step]) -> str:
        """Infer pattern category from steps."""
        categories = {
            "file_management": ["Read", "Write", "Edit", "Glob"],
            "code_generation": ["Write", "python", "javascript", "code"],
            "documentation": ["markdown", "readme", "docs"],
            "git_workflow": ["git", "commit", "push", "branch"],
            "analysis": ["Grep", "analyze", "search", "parse"],
            "testing": ["pytest", "test", "spec"],
        }

        step_actions = " ".join(s.action.lower() for s in steps)

        for category, keywords in categories.items():
            if any(kw.lower() in step_actions for kw in keywords):
                return category

        return "general"

    def _extract_tags(self, turns: list[Turn]) -> list[str]:
        """Extract relevant tags from turns."""
        tags: set[str] = set()

        for turn in turns:
            # Add tools as tags
            for tool in turn.tools_used:
                # Extract base tool name
                if "_" in tool:
                    tags.add(tool.split("_")[0].lower())
                else:
                    tags.add(tool.lower())

            # Add file extensions as tags
            for file_path in turn.files_touched:
                if "." in file_path:
                    ext = file_path.rsplit(".", 1)[-1].lower()
                    if len(ext) <= 4:
                        tags.add(ext)

        return list(tags)[:10]  # Limit to 10 tags

    def deduplicate(self, patterns: list[Pattern]) -> list[Pattern]:
        """Remove duplicate patterns based on similarity.

        Args:
            patterns: List of patterns to deduplicate.

        Returns:
            Deduplicated list of patterns.
        """
        if not patterns:
            return []

        unique: list[Pattern] = []
        seen_ids: set[str] = set()

        for pattern in patterns:
            if pattern.id not in seen_ids:
                # Check for similar patterns
                is_similar = False
                for existing in unique:
                    if self._are_similar(pattern, existing):
                        # Keep the one with higher confidence
                        if pattern.confidence > existing.confidence:
                            unique.remove(existing)
                            seen_ids.discard(existing.id)
                        else:
                            is_similar = True
                        break

                if not is_similar:
                    unique.append(pattern)
                    seen_ids.add(pattern.id)

        return unique

    def _are_similar(self, p1: Pattern, p2: Pattern, threshold: float = 0.7) -> bool:
        """Check if two patterns are similar based on their structure."""
        # Compare triggers
        t1_phrases = {t.phrase.lower() for t in p1.triggers}
        t2_phrases = {t.phrase.lower() for t in p2.triggers}
        if t1_phrases and t2_phrases:
            trigger_overlap = len(t1_phrases & t2_phrases) / max(
                len(t1_phrases), len(t2_phrases)
            )
            if trigger_overlap > threshold:
                return True

        # Compare steps
        s1_actions = [s.action for s in p1.workflow_steps]
        s2_actions = [s.action for s in p2.workflow_steps]
        return bool(s1_actions and s2_actions and s1_actions == s2_actions)
