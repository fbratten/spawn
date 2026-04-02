"""FastMCP server for Pattern MCP Builder.

Design: AI-agnostic. The MCP provides data and utilities.
The calling AI (Claude, Gemini, ChatGPT, etc.) does semantic understanding.

Primary Tools (AI-driven workflow):
- get_log_content: Parse log, return raw data for AI to analyze
- find_recurring_themes: Frequency analysis to surface potential patterns
- define_pattern: AI defines patterns it identifies from the content
- list_patterns: List defined patterns
- score_patterns: Score patterns for buildability
- get_pattern: Get single pattern details
- generate_preview: Preview generated code
- generate_mcp: Generate full MCP server from pattern
- validate_mcp: Validate generated server

Library Tools:
- store_pattern: Save pattern to library with tags
- search_patterns: Search pattern library
- learn_outcome: Record and learn from build outcomes
- suggest_similar: Find similar patterns

Pipeline Tools:
- run_pipeline: Full analyze -> score -> generate pipeline
- compare_existing: Compare pattern with existing MCP tools
- batch_analyze: Batch process multiple log files

Deprecated:
- analyze_log: Legacy mechanical extraction (use get_log_content + define_pattern instead)
"""

from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from mcp_builder_mcp.extractor import PatternExtractor
from mcp_builder_mcp.generator import GeneratorEngine, Validator
from mcp_builder_mcp.models import Pattern, ScoreWeights
from mcp_builder_mcp.parser import LogParser
from mcp_builder_mcp.scorer import ScoringEngine
from mcp_builder_mcp.store import LearningEngine, MinnaSync, PatternStore

# Initialize FastMCP server
mcp = FastMCP("pattern-mcp")

# Shared state for session
_session_patterns: list[Pattern] = []
_session_store: PatternStore | None = None


def _get_store() -> PatternStore:
    """Get or create pattern store."""
    global _session_store
    if _session_store is None:
        _session_store = PatternStore()
    return _session_store


@mcp.tool()
def analyze_log(
    log_path: str,
    min_confidence: float = 0.5,
    focus_areas: list[str] | None = None,
) -> dict[str, Any]:
    """[DEPRECATED] Mechanical pattern extraction - use get_log_content + define_pattern instead.

    This tool attempts mechanical pattern extraction via heuristics, which produces
    poor results. The recommended workflow is:
    1. Call get_log_content(log_path) to get raw parsed data
    2. AI analyzes the content semantically
    3. Call define_pattern() for each pattern identified

    Args:
        log_path: Path to markdown log file.
        min_confidence: Minimum confidence threshold for patterns (0.0-1.0).
        focus_areas: Optional filter for pattern categories.

    Returns:
        Dictionary with patterns (mechanically extracted - quality varies).
    """
    global _session_patterns

    path = Path(log_path)
    if not path.exists():
        return {"error": f"Log file not found: {log_path}"}

    try:
        # Parse log
        parser = LogParser()
        log = parser.parse(path)

        # Extract patterns
        extractor = PatternExtractor(min_confidence=min_confidence)
        patterns = extractor.extract(log)

        # Filter by focus areas if specified
        if focus_areas:
            patterns = [p for p in patterns if p.category in focus_areas]

        # Store in session
        _session_patterns = patterns

        # Also persist to store
        store = _get_store()
        for pattern in patterns:
            store.store(pattern)

        return {
            "patterns": [
                {
                    "id": p.id,
                    "name": p.name,
                    "category": p.category,
                    "confidence": p.confidence,
                    "triggers_count": len(p.triggers),
                    "steps_count": len(p.workflow_steps),
                }
                for p in patterns
            ],
            "count": len(patterns),
            "summary": {
                "source": str(path),
                "turns_parsed": log.metadata.get("total_turns", 0),
                "sessions_found": log.metadata.get("total_sessions", 0),
                "categories": list({p.category for p in patterns}),
            },
        }

    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def get_log_content(
    log_path: str,
    max_turns: int = 50,
) -> dict[str, Any]:
    """Get raw parsed content from a log file for AI semantic analysis.

    Unlike analyze_log which does mechanical pattern extraction,
    this returns the raw turns and sessions for the AI to analyze
    and identify patterns semantically.

    Args:
        log_path: Path to markdown log file.
        max_turns: Maximum number of turns to return (default 50).

    Returns:
        Dictionary with raw turns, sessions, and content summaries.
    """
    path = Path(log_path)
    if not path.exists():
        return {"error": f"Log file not found: {log_path}"}

    try:
        parser = LogParser()
        log = parser.parse(path)

        # Extract user requests and their outcomes
        interactions = []
        current_request = None

        for turn in log.turns[:max_turns]:
            if turn.role == "user":
                if current_request:
                    interactions.append(current_request)
                current_request = {
                    "request": turn.content[:300].strip(),
                    "outcomes": [],
                    "tools_used": [],
                }
            elif turn.role == "assistant" and current_request:
                current_request["outcomes"].append(turn.content[:200].strip())
                current_request["tools_used"].extend(turn.tools_used)

        if current_request:
            interactions.append(current_request)

        return {
            "source": str(path),
            "total_turns": len(log.turns),
            "total_sessions": len(log.sessions),
            "interactions": interactions,
            "summary": (
                f"Log contains {len(log.turns)} turns across {len(log.sessions)} sessions. "
                f"Found {len(interactions)} user requests with outcomes."
            ),
            "hint": (
                "Review the 'interactions' to identify repeatable patterns. "
                "Look for: similar requests, multi-step workflows, valuable automation opportunities. "
                "Use 'define_pattern' to create patterns you identify."
            ),
        }

    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def find_recurring_themes(
    log_path: str,
    min_occurrences: int = 2,
) -> dict[str, Any]:
    """Analyze a log for recurring themes that could become MCP tools.

    Performs frequency analysis to surface:
    - Tools used repeatedly (potential automation candidates)
    - Similar user requests (recurring needs)
    - Common action verbs (check, fix, create, update, deploy, etc.)
    - File types frequently touched

    The AI can then evaluate these themes and decide which are worth
    turning into MCP tools.

    Args:
        log_path: Path to markdown log file.
        min_occurrences: Minimum times something must appear to be reported (default 2).

    Returns:
        Dictionary with recurring themes, frequencies, and suggestions.
    """
    import re
    from collections import Counter

    path = Path(log_path)
    if not path.exists():
        return {"error": f"Log file not found: {log_path}"}

    try:
        parser = LogParser()
        log = parser.parse(path)

        # Collect all tools used
        all_tools: list[str] = []
        for turn in log.turns:
            all_tools.extend(turn.tools_used)

        # Collect all user requests
        user_requests: list[str] = []
        for turn in log.turns:
            if turn.role == "user":
                user_requests.append(turn.content.strip()[:150])

        # Collect file extensions touched
        file_extensions: list[str] = []
        for turn in log.turns:
            for file_path in turn.files_touched:
                if "." in file_path:
                    ext = file_path.rsplit(".", 1)[-1].lower()
                    if len(ext) <= 5:
                        file_extensions.append(ext)

        # Extract action verbs from user requests
        action_verbs: list[str] = []
        action_patterns = [
            r"\b(check|verify|validate|test)\b",
            r"\b(fix|repair|correct|update)\b",
            r"\b(create|generate|build|make)\b",
            r"\b(deploy|push|release|publish)\b",
            r"\b(analyze|review|audit|inspect)\b",
            r"\b(run|execute|start|stop)\b",
            r"\b(delete|remove|clean)\b",
            r"\b(migrate|convert|transform)\b",
        ]
        for request in user_requests:
            for pattern in action_patterns:
                matches = re.findall(pattern, request.lower())
                action_verbs.extend(matches)

        # Count frequencies
        tool_counts = Counter(all_tools)
        action_counts = Counter(action_verbs)
        ext_counts = Counter(file_extensions)

        # Filter by min_occurrences
        recurring_tools = {k: v for k, v in tool_counts.items() if v >= min_occurrences}
        recurring_actions = {k: v for k, v in action_counts.items() if v >= min_occurrences}
        recurring_extensions = {k: v for k, v in ext_counts.items() if v >= min_occurrences}

        # Generate theme suggestions
        themes = []

        # Tool-based themes
        for tool, count in sorted(recurring_tools.items(), key=lambda x: -x[1])[:5]:
            themes.append({
                "type": "tool_usage",
                "name": tool,
                "occurrences": count,
                "suggestion": f"'{tool}' used {count} times - potential automation candidate",
            })

        # Action-based themes
        for action, count in sorted(recurring_actions.items(), key=lambda x: -x[1])[:5]:
            themes.append({
                "type": "action_pattern",
                "name": action,
                "occurrences": count,
                "suggestion": f"'{action}' action appears {count} times - recurring workflow",
            })

        # File type themes
        for ext, count in sorted(recurring_extensions.items(), key=lambda x: -x[1])[:3]:
            themes.append({
                "type": "file_type",
                "name": f".{ext}",
                "occurrences": count,
                "suggestion": f"'.{ext}' files touched {count} times",
            })

        return {
            "source": str(path),
            "total_turns": len(log.turns),
            "total_user_requests": len(user_requests),
            "themes": themes,
            "recurring_tools": recurring_tools,
            "recurring_actions": recurring_actions,
            "recurring_file_types": recurring_extensions,
            "summary": (
                f"Found {len(themes)} recurring themes. "
                f"Top tools: {list(recurring_tools.keys())[:3]}. "
                f"Top actions: {list(recurring_actions.keys())[:3]}."
            ),
            "next_step": (
                "Review themes above. For valuable patterns, use define_pattern() to create them. "
                "Check if your existing tools already cover these themes before creating new MCPs."
            ),
        }

    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def define_pattern(
    name: str,
    description: str,
    trigger: str,
    workflow_steps: list[str],
    category: str = "general",
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """Define a new pattern from AI semantic analysis.

    Use this after reviewing log content with get_log_content
    to define patterns you've identified. This creates a properly
    structured pattern that can be scored and used for MCP generation.

    Args:
        name: Human-readable pattern name (e.g., "Link Checker and Fixer").
        description: What this pattern does and when to use it.
        trigger: What user request triggers this pattern (e.g., "check all links").
        workflow_steps: List of steps in the workflow (e.g., ["scan for links", "validate each", "fix broken"]).
        category: Pattern category (documentation, git_workflow, testing, deployment, etc.).
        tags: Optional tags for searchability.

    Returns:
        The created pattern with ID for scoring/generation.
    """
    global _session_patterns

    import hashlib
    from datetime import datetime

    from mcp_builder_mcp.models import Pattern, Step, Trigger

    # Generate ID
    hash_input = f"{name}:{trigger}".lower()
    pattern_id = f"pattern-{hashlib.md5(hash_input.encode()).hexdigest()[:8]}"

    # Create structured pattern
    pattern = Pattern(
        id=pattern_id,
        name=name,
        description=description,
        extracted_from="ai_defined",
        extraction_date=datetime.now(),
        confidence=1.0,  # AI-defined patterns have high confidence
        triggers=[Trigger(phrase=trigger)],
        inputs=[],
        outputs=[],
        workflow_steps=[
            Step(id=f"step-{i+1}", action=step, description=step)
            for i, step in enumerate(workflow_steps)
        ],
        category=category,
        tags=tags or [],
        source_context="Defined by AI semantic analysis",
    )

    # Add to session and store
    _session_patterns.append(pattern)
    store = _get_store()
    store.store(pattern)

    return {
        "pattern_id": pattern.id,
        "name": pattern.name,
        "description": pattern.description,
        "category": pattern.category,
        "steps_count": len(pattern.workflow_steps),
        "status": "created",
        "next_steps": [
            "Use score_patterns() to evaluate buildability",
            "Use compare_existing() to check for overlap with existing MCPs",
            "Use generate_preview() to see generated code",
        ],
    }


@mcp.tool()
def list_patterns(
    filter_by: str | None = None,
    sort_by: str = "confidence",
    include_stored: bool = True,
) -> dict[str, Any]:
    """List identified patterns.

    Returns patterns from the current session and optionally
    from the persistent store.

    Args:
        filter_by: Filter by category (e.g., "documentation", "git_workflow").
        sort_by: Sort field ("confidence", "name", "category"). Default: "confidence".
        include_stored: Include patterns from persistent store. Default: True.

    Returns:
        Dictionary with patterns list.
    """
    patterns = list(_session_patterns)

    # Add stored patterns if requested
    if include_stored:
        store = _get_store()
        stored = store.list_all()
        # Avoid duplicates by ID
        session_ids = {p.id for p in patterns}
        for p in stored:
            if p.id not in session_ids:
                patterns.append(p)

    # Filter by category
    if filter_by:
        patterns = [p for p in patterns if p.category == filter_by]

    # Sort
    if sort_by == "confidence":
        patterns.sort(key=lambda p: p.confidence, reverse=True)
    elif sort_by == "name":
        patterns.sort(key=lambda p: p.name)
    elif sort_by == "category":
        patterns.sort(key=lambda p: p.category)

    return {
        "patterns": [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description[:100] if p.description else "",
                "category": p.category,
                "confidence": p.confidence,
                "tags": p.tags,
                "triggers_count": len(p.triggers),
                "steps_count": len(p.workflow_steps),
            }
            for p in patterns
        ],
        "count": len(patterns),
    }


@mcp.tool()
def score_patterns(
    pattern_ids: list[str] | None = None,
    threshold: float = 3.0,
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Score patterns for buildability.

    Evaluates patterns on frequency, complexity, value, and uniqueness
    to determine which are most suitable for building into MCP servers.

    Args:
        pattern_ids: Specific pattern IDs to score. Scores all session patterns if not specified.
        threshold: Minimum buildability score to include. Default: 3.0.
        weights: Custom scoring weights. Keys: frequency, complexity, value, uniqueness.

    Returns:
        Dictionary with scored patterns and recommendations.
    """
    # Get patterns to score
    if pattern_ids:
        store = _get_store()
        patterns = []
        for pid in pattern_ids:
            p = store.get(pid)
            if p:
                patterns.append(p)
            else:
                # Check session patterns
                for sp in _session_patterns:
                    if sp.id == pid:
                        patterns.append(sp)
                        break
    else:
        patterns = list(_session_patterns)

    if not patterns:
        return {"error": "No patterns to score. Run analyze_log first."}

    # Create scoring engine with optional custom weights
    score_weights = None
    if weights:
        score_weights = ScoreWeights.from_dict(weights)

    engine = ScoringEngine(weights=score_weights)

    # Score and rank
    scored = engine.rank(patterns)

    # Filter by threshold
    above_threshold = [s for s in scored if s.buildability >= threshold]

    # Store scored patterns
    store = _get_store()
    for s in scored:
        store.store_scored(s)

    return {
        "scored": [
            {
                "pattern_id": s.pattern.id,
                "pattern_name": s.pattern.name,
                "scores": {
                    "frequency": round(s.frequency, 2),
                    "complexity": round(s.complexity, 2),
                    "value": round(s.value, 2),
                    "uniqueness": round(s.uniqueness, 2),
                },
                "buildability": round(s.buildability, 2),
                "recommendation": s.recommendation,
            }
            for s in scored
        ],
        "recommendations": [
            {
                "pattern_id": s.pattern.id,
                "pattern_name": s.pattern.name,
                "buildability": round(s.buildability, 2),
                "reason": _recommendation_reason(s),
            }
            for s in above_threshold
            if s.recommendation == "build"
        ],
        "summary": {
            "total_scored": len(scored),
            "above_threshold": len(above_threshold),
            "build_recommended": len(
                [s for s in above_threshold if s.recommendation == "build"]
            ),
            "weights_used": (
                score_weights.to_dict() if score_weights else ScoreWeights().to_dict()
            ),
        },
    }


def _recommendation_reason(scored: Any) -> str:
    """Generate human-readable reason for recommendation."""
    reasons = []

    if scored.frequency >= 4:
        reasons.append("frequently used pattern")
    if scored.value >= 4:
        reasons.append("high user value")
    if scored.complexity <= 2:
        reasons.append("low implementation complexity")
    if scored.uniqueness >= 4:
        reasons.append("not covered by existing tools")

    if reasons:
        return ", ".join(reasons).capitalize()
    return "Good overall buildability score"


@mcp.tool()
def get_pattern(pattern_id: str) -> dict[str, Any]:
    """Get detailed information about a single pattern.

    Returns the full pattern definition including triggers,
    inputs, outputs, and workflow steps.

    Args:
        pattern_id: The pattern identifier.

    Returns:
        Full pattern definition or error if not found.
    """
    # Check session patterns first
    for p in _session_patterns:
        if p.id == pattern_id:
            return {"pattern": p.to_dict()}

    # Check store
    store = _get_store()
    pattern = store.get(pattern_id)

    if pattern:
        return {"pattern": pattern.to_dict()}

    return {"error": f"Pattern not found: {pattern_id}"}


# =============================================================================
# MVP 2 Tools: Generation
# =============================================================================


@mcp.tool()
def generate_preview(pattern_id: str) -> dict[str, Any]:
    """Preview generated MCP code without writing to disk.

    Shows what files would be created and their contents
    before actually generating. Useful for review.

    Args:
        pattern_id: The pattern ID to generate preview for.

    Returns:
        Dictionary with file paths and preview content.
    """
    # Get pattern
    pattern = None
    for p in _session_patterns:
        if p.id == pattern_id:
            pattern = p
            break

    if pattern is None:
        store = _get_store()
        pattern = store.get(pattern_id)

    if pattern is None:
        return {"error": f"Pattern not found: {pattern_id}"}

    try:
        generator = GeneratorEngine()
        preview = generator.generate_preview(pattern)

        return {
            "pattern_id": pattern_id,
            "pattern_name": pattern.name,
            "files": [
                {
                    "path": path,
                    "size": len(content),
                    "preview": content[:500] + ("..." if len(content) > 500 else ""),
                }
                for path, content in preview.items()
            ],
            "file_count": len(preview),
        }

    except Exception as e:
        return {"error": f"Generation failed: {e}"}


@mcp.tool()
def generate_mcp(
    pattern_id: str,
    output_dir: str,
    include_tests: bool = True,
    include_docs: bool = True,
) -> dict[str, Any]:
    """Generate a complete MCP server from a pattern.

    Creates all necessary files including server code, tools,
    tests, and documentation based on the pattern definition.

    Args:
        pattern_id: The pattern ID to generate from.
        output_dir: Directory to write generated files.
        include_tests: Generate pytest test files. Default: True.
        include_docs: Generate README and SKILL.md. Default: True.

    Returns:
        Dictionary with created files and next steps.
    """
    # Get pattern
    pattern = None
    for p in _session_patterns:
        if p.id == pattern_id:
            pattern = p
            break

    if pattern is None:
        store = _get_store()
        pattern = store.get(pattern_id)

    if pattern is None:
        return {"error": f"Pattern not found: {pattern_id}"}

    output_path = Path(output_dir)

    try:
        generator = GeneratorEngine()
        generated = generator.generate(
            pattern,
            output_path,
            include_tests=include_tests,
            include_docs=include_docs,
        )

        # Write files
        created_files = generator.write_files(generated)

        # Validate
        validator = Validator()
        validation = validator.validate(generated)

        # Record outcome
        store = _get_store()
        store.record_outcome(
            pattern_id,
            outcome="success" if validation.valid else "warning",
            notes=f"Generated {len(created_files)} files",
        )

        return {
            "pattern_id": pattern_id,
            "pattern_name": pattern.name,
            "package_name": generated.package_name,
            "output_dir": str(output_path),
            "files_created": [str(f) for f in created_files],
            "file_count": len(created_files),
            "validation": validation.to_dict(),
            "next_steps": [
                f"cd {output_path}",
                "python -m venv .venv && source .venv/bin/activate",
                "uv pip install -e '.[dev]'",
                "pytest tests/ -v",
                "# Implement TODO items in tools/",
            ],
        }

    except Exception as e:
        # Record failure
        store = _get_store()
        store.record_outcome(pattern_id, outcome="failure", notes=str(e))
        return {"error": f"Generation failed: {e}"}


@mcp.tool()
def validate_mcp(mcp_path: str) -> dict[str, Any]:
    """Validate a generated or existing MCP server.

    Checks Python syntax, import resolution, and pyproject.toml
    structure. Optionally runs ruff for linting.

    Args:
        mcp_path: Path to the MCP directory to validate.

    Returns:
        Dictionary with validation results.
    """
    path = Path(mcp_path)

    if not path.exists():
        return {"error": f"Path not found: {mcp_path}"}

    try:
        validator = Validator()
        result = validator.validate_path(path)

        return {
            "path": str(path),
            "valid": result.valid,
            "errors": [e.to_dict() for e in result.errors],
            "warnings": [w.to_dict() for w in result.warnings],
            "error_count": len(result.errors),
            "warning_count": len(result.warnings),
        }

    except Exception as e:
        return {"error": f"Validation failed: {e}"}


# =============================================================================
# MVP 3 Tools: Pattern Library + Learning
# =============================================================================


@mcp.tool()
def store_pattern(
    pattern_id: str,
    tags: list[str] | None = None,
    sync_to_minna: bool = True,
) -> dict[str, Any]:
    """Save a pattern to the persistent library.

    Stores the pattern with optional tags for easier discovery.
    Optionally syncs to Minna Memory for cross-session persistence.

    Args:
        pattern_id: The pattern ID to store.
        tags: Additional tags to add to the pattern.
        sync_to_minna: Sync to Minna Memory. Default: True.

    Returns:
        Dictionary with storage confirmation.
    """
    # Get pattern
    pattern = None
    for p in _session_patterns:
        if p.id == pattern_id:
            pattern = p
            break

    if pattern is None:
        store = _get_store()
        pattern = store.get(pattern_id)

    if pattern is None:
        return {"error": f"Pattern not found: {pattern_id}"}

    # Add tags if provided
    if tags:
        existing_tags = set(pattern.tags)
        existing_tags.update(tags)
        pattern.tags = list(existing_tags)

    try:
        store = _get_store()
        filepath = store.store(pattern)

        result: dict[str, Any] = {
            "pattern_id": pattern_id,
            "pattern_name": pattern.name,
            "stored_path": str(filepath),
            "tags": pattern.tags,
        }

        # Sync to Minna if requested
        if sync_to_minna:
            minna = MinnaSync()
            synced = minna.sync_pattern(pattern)
            result["minna_synced"] = synced

        return result

    except Exception as e:
        return {"error": f"Storage failed: {e}"}


@mcp.tool()
def search_patterns(
    query: str | None = None,
    category: str | None = None,
    tags: list[str] | None = None,
    limit: int = 20,
    include_minna: bool = True,
) -> dict[str, Any]:
    """Search the pattern library.

    Search by text query, category, or tags. Can search both
    local store and Minna Memory.

    Args:
        query: Text search in name and description.
        category: Filter by category.
        tags: Filter by tags (any match).
        limit: Maximum results. Default: 20.
        include_minna: Also search Minna Memory. Default: True.

    Returns:
        Dictionary with matching patterns.
    """
    store = _get_store()
    results = store.search(query=query, category=category, tags=tags, limit=limit)

    # Add Minna results if requested
    minna_results: list[dict[str, Any]] = []
    if include_minna and query:
        minna = MinnaSync()
        minna_results = minna.search_patterns(query, limit=limit)

    return {
        "patterns": [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description[:100] if p.description else "",
                "category": p.category,
                "tags": p.tags,
                "source": "local",
            }
            for p in results
        ],
        "minna_matches": [
            {
                "entity": m.get("entity_name", ""),
                "value": m.get("value", ""),
                "context": m.get("context", ""),
                "source": "minna",
            }
            for m in minna_results
        ],
        "total_local": len(results),
        "total_minna": len(minna_results),
    }


@mcp.tool()
def learn_outcome(
    pattern_id: str,
    outcome: str,
    notes: str | None = None,
    apply_adjustment: bool = True,
) -> dict[str, Any]:
    """Record a build outcome for learning.

    Records whether a generated MCP succeeded or failed,
    and optionally adjusts the pattern's buildability score.

    Args:
        pattern_id: The pattern that was built.
        outcome: "success" or "failure".
        notes: Optional notes about the outcome.
        apply_adjustment: Apply score adjustment. Default: True.

    Returns:
        Dictionary with outcome recorded and any adjustments.
    """
    if outcome not in ("success", "failure"):
        return {"error": "Outcome must be 'success' or 'failure'"}

    store = _get_store()

    # Record outcome
    store.record_outcome(pattern_id, outcome, notes)

    # Also sync to Minna
    minna = MinnaSync()
    minna.record_outcome(pattern_id, outcome, notes)

    result: dict[str, Any] = {
        "pattern_id": pattern_id,
        "outcome": outcome,
        "recorded": True,
    }

    # Calculate and apply adjustment if requested
    if apply_adjustment:
        outcomes = store.get_outcomes(pattern_id)
        learning = LearningEngine()

        # Get current pattern and score
        pattern = store.get(pattern_id)
        if pattern:
            scorer = ScoringEngine()
            scored = scorer.score(pattern)

            adjustment = learning.adjust_score(scored, outcomes)
            result["adjustment"] = adjustment.to_dict()

            # Update stored pattern with adjusted recommendation
            if adjustment.adjusted_buildability >= 8.0:
                result["updated_recommendation"] = "build"
            elif adjustment.adjusted_buildability >= 5.0:
                result["updated_recommendation"] = "review"
            else:
                result["updated_recommendation"] = "skip"

        # Get stats
        stats = learning.calculate_stats(outcomes)
        result["stats"] = stats.to_dict()

    return result


@mcp.tool()
def suggest_similar(pattern_id: str) -> dict[str, Any]:
    """Find patterns similar to a given pattern.

    Searches both local store and Minna Memory for patterns
    with similar triggers, categories, or descriptions.

    Args:
        pattern_id: The pattern to find similar to.

    Returns:
        Dictionary with similar patterns.
    """
    # Get pattern
    pattern = None
    for p in _session_patterns:
        if p.id == pattern_id:
            pattern = p
            break

    if pattern is None:
        store = _get_store()
        pattern = store.get(pattern_id)

    if pattern is None:
        return {"error": f"Pattern not found: {pattern_id}"}

    similar_local: list[dict[str, Any]] = []
    similar_minna: list[dict[str, Any]] = []

    # Search local store by category and tags
    store = _get_store()
    candidates = store.search(category=pattern.category, limit=10)

    for candidate in candidates:
        if candidate.id == pattern_id:
            continue

        # Calculate similarity score
        similarity = _calculate_similarity(pattern, candidate)
        if similarity > 0.3:
            similar_local.append(
                {
                    "id": candidate.id,
                    "name": candidate.name,
                    "category": candidate.category,
                    "similarity": round(similarity, 2),
                }
            )

    # Search Minna
    minna = MinnaSync()
    minna_matches = minna.find_similar(pattern)
    for match in minna_matches:
        entity = match.get("entity_name", "")
        if pattern_id not in entity:
            similar_minna.append(
                {
                    "entity": entity,
                    "value": match.get("value", ""),
                }
            )

    return {
        "pattern_id": pattern_id,
        "pattern_name": pattern.name,
        "similar_local": sorted(
            similar_local, key=lambda x: x["similarity"], reverse=True
        )[:5],
        "similar_minna": similar_minna[:5],
    }


def _calculate_similarity(p1: Pattern, p2: Pattern) -> float:
    """Calculate similarity between two patterns."""
    score = 0.0

    # Category match
    if p1.category == p2.category:
        score += 0.3

    # Tag overlap
    if p1.tags and p2.tags:
        overlap = len(set(p1.tags) & set(p2.tags))
        max_tags = max(len(p1.tags), len(p2.tags))
        if max_tags > 0:
            score += 0.3 * (overlap / max_tags)

    # Trigger phrase overlap
    t1_phrases = {t.phrase.lower() for t in p1.triggers}
    t2_phrases = {t.phrase.lower() for t in p2.triggers}
    if t1_phrases and t2_phrases:
        overlap = len(t1_phrases & t2_phrases)
        max_triggers = max(len(t1_phrases), len(t2_phrases))
        if max_triggers > 0:
            score += 0.4 * (overlap / max_triggers)

    return score


# =============================================================================
# MVP 4 Tools: Full Pipeline + Polish
# =============================================================================


# Known MCP tools for comparison
EXISTING_MCP_TOOLS = [
    {
        "name": "smart-inventory",
        "purpose": "CLAUDE.md generation and project analysis",
        "keywords": ["documentation", "project", "inventory", "claude.md"],
    },
    {
        "name": "next-conductor",
        "purpose": "NEXT.md task tracking and management",
        "keywords": ["tasks", "next", "planning", "todo"],
    },
    {
        "name": "paaf",
        "purpose": "Project audits, documentation health, technical debt",
        "keywords": ["audit", "debt", "health", "requirements"],
    },
    {
        "name": "browser-mcp",
        "purpose": "Browser automation with Playwright",
        "keywords": ["browser", "web", "automation", "click"],
    },
    {
        "name": "research-agent-mcp",
        "purpose": "Academic and professional research workflows",
        "keywords": ["research", "sources", "citations", "synthesis"],
    },
    {
        "name": "minna-memory",
        "purpose": "Persistent memory across sessions",
        "keywords": ["memory", "entities", "recall", "preferences"],
    },
    {
        "name": "content-extractor-mcp",
        "purpose": "Screenshot analysis, OCR, UI region detection",
        "keywords": ["screenshot", "ocr", "ui", "image"],
    },
]


@mcp.tool()
def run_pipeline(
    log_path: str,
    output_dir: str | None = None,
    auto_generate: bool = False,
    min_score: float = 5.0,
    top_n: int = 3,
) -> dict[str, Any]:
    """Run the full pattern-to-MCP pipeline.

    Analyzes a log, scores patterns, and optionally generates
    MCP servers for top-scoring patterns.

    Args:
        log_path: Path to markdown log file.
        output_dir: Directory for generated MCPs. Required if auto_generate is True.
        auto_generate: Automatically generate MCPs for top patterns. Default: False.
        min_score: Minimum buildability score to consider. Default: 5.0.
        top_n: Number of top patterns to process. Default: 3.

    Returns:
        Dictionary with pipeline results and recommendations.
    """
    results: dict[str, Any] = {
        "stages": {},
        "recommendations": [],
        "generated": [],
    }

    # Stage 1: Analyze
    analysis = analyze_log(log_path)
    if "error" in analysis:
        return {"error": f"Analysis failed: {analysis['error']}"}

    results["stages"]["analyze"] = {
        "patterns_found": analysis["count"],
        "categories": analysis["summary"]["categories"],
    }

    if analysis["count"] == 0:
        return {
            "error": "No patterns found in log",
            "stages": results["stages"],
        }

    # Stage 2: Score
    scoring = score_patterns(threshold=min_score)
    if "error" in scoring:
        return {"error": f"Scoring failed: {scoring['error']}"}

    results["stages"]["score"] = {
        "total_scored": scoring["summary"]["total_scored"],
        "above_threshold": scoring["summary"]["above_threshold"],
    }

    # Get top N patterns
    top_patterns = [
        s for s in scoring["scored"]
        if s["buildability"] >= min_score
    ][:top_n]

    if not top_patterns:
        return {
            "message": "No patterns above threshold",
            "stages": results["stages"],
            "all_scored": scoring["scored"],
        }

    # Stage 3: Compare with existing tools
    for pattern in top_patterns:
        pattern_id = pattern["pattern_id"]
        comparison = compare_existing(pattern_id)

        recommendation = {
            "pattern_id": pattern_id,
            "pattern_name": pattern["pattern_name"],
            "buildability": pattern["buildability"],
            "recommendation": pattern["recommendation"],
            "overlaps_with": comparison.get("overlaps", []),
            "unique_features": comparison.get("unique_features", []),
        }
        results["recommendations"].append(recommendation)

    results["stages"]["compare"] = {
        "patterns_compared": len(top_patterns),
    }

    # Stage 4: Generate (if auto_generate)
    if auto_generate:
        if not output_dir:
            return {
                "error": "output_dir required when auto_generate is True",
                "stages": results["stages"],
                "recommendations": results["recommendations"],
            }

        output_path = Path(output_dir)

        for rec in results["recommendations"]:
            if rec["recommendation"] == "build":
                pattern_id = rec["pattern_id"]
                pattern_output = output_path / pattern_id

                gen_result = generate_mcp(
                    pattern_id=pattern_id,
                    output_dir=str(pattern_output),
                    include_tests=True,
                    include_docs=True,
                )

                if "error" not in gen_result:
                    results["generated"].append({
                        "pattern_id": pattern_id,
                        "output_dir": str(pattern_output),
                        "files_created": gen_result["file_count"],
                        "validation": gen_result["validation"],
                    })
                else:
                    results["generated"].append({
                        "pattern_id": pattern_id,
                        "error": gen_result["error"],
                    })

        results["stages"]["generate"] = {
            "attempted": len([r for r in results["recommendations"] if r["recommendation"] == "build"]),
            "succeeded": len([g for g in results["generated"] if "error" not in g]),
        }

    return results


@mcp.tool()
def compare_existing(pattern_id: str) -> dict[str, Any]:
    """Compare a pattern with existing MCP tools.

    Identifies overlaps with known MCP servers and highlights
    unique features of the pattern.

    Args:
        pattern_id: The pattern ID to compare.

    Returns:
        Dictionary with overlaps and unique features.
    """
    # Get pattern
    pattern = None
    for p in _session_patterns:
        if p.id == pattern_id:
            pattern = p
            break

    if pattern is None:
        store = _get_store()
        pattern = store.get(pattern_id)

    if pattern is None:
        return {"error": f"Pattern not found: {pattern_id}"}

    overlaps = []
    pattern_keywords = set()

    # Build keyword set from pattern
    pattern_keywords.add(pattern.name.lower())
    pattern_keywords.add(pattern.category.lower())
    pattern_keywords.update(t.lower() for t in pattern.tags)
    pattern_keywords.update(t.phrase.lower() for t in pattern.triggers)
    if pattern.description:
        # Add significant words from description
        desc_words = pattern.description.lower().split()
        pattern_keywords.update(
            w for w in desc_words if len(w) > 4 and w.isalpha()
        )

    # Compare with each existing tool
    for tool in EXISTING_MCP_TOOLS:
        tool_keywords = set(tool["keywords"])
        overlap_count = len(pattern_keywords & tool_keywords)

        if overlap_count > 0:
            overlap_score = overlap_count / max(len(tool_keywords), 1)
            if overlap_score >= 0.2:  # At least 20% keyword overlap
                overlaps.append({
                    "tool_name": tool["name"],
                    "purpose": tool["purpose"],
                    "overlap_score": round(overlap_score, 2),
                    "shared_keywords": list(pattern_keywords & tool_keywords),
                })

    # Identify unique features
    all_tool_keywords = set()
    for tool in EXISTING_MCP_TOOLS:
        all_tool_keywords.update(tool["keywords"])

    unique_keywords = pattern_keywords - all_tool_keywords
    unique_features = []

    # Generate feature descriptions from unique keywords
    for step in pattern.workflow_steps:
        step_words = step.action.lower().split("_")
        if any(w in unique_keywords for w in step_words):
            unique_features.append(f"Step: {step.action} - {step.description}")

    if pattern.outputs:
        for output in pattern.outputs:
            if output.format and output.format.lower() in unique_keywords:
                unique_features.append(f"Output: {output.name} ({output.format})")

    return {
        "pattern_id": pattern_id,
        "pattern_name": pattern.name,
        "overlaps": overlaps,
        "unique_features": unique_features[:5],  # Limit to top 5
        "recommendation": "build" if len(overlaps) == 0 else "review_overlaps",
    }


@mcp.tool()
def batch_analyze(
    log_paths: list[str],
    merge_similar: bool = True,
    similarity_threshold: float = 0.7,
) -> dict[str, Any]:
    """Analyze multiple logs in batch.

    Processes multiple log files and optionally merges
    similar patterns found across logs.

    Args:
        log_paths: List of paths to log files.
        merge_similar: Merge similar patterns across logs. Default: True.
        similarity_threshold: Threshold for merging. Default: 0.7.

    Returns:
        Dictionary with all patterns and per-log breakdown.
    """
    results: dict[str, Any] = {
        "by_log": {},
        "all_patterns": [],
        "merged_count": 0,
        "total_files": len(log_paths),
        "successful_files": 0,
        "failed_files": [],
    }

    all_patterns: list[Pattern] = []

    # Analyze each log
    for log_path in log_paths:
        analysis = analyze_log(log_path)

        if "error" in analysis:
            results["failed_files"].append({
                "path": log_path,
                "error": analysis["error"],
            })
            continue

        results["successful_files"] += 1
        results["by_log"][log_path] = {
            "patterns_found": analysis["count"],
            "pattern_ids": [p["id"] for p in analysis["patterns"]],
        }

        # Collect patterns
        for p in _session_patterns:
            all_patterns.append(p)

    if not all_patterns:
        return {
            "error": "No patterns found in any log",
            **results,
        }

    # Merge similar patterns if requested
    if merge_similar and len(all_patterns) > 1:
        merged = _merge_similar_patterns(all_patterns, similarity_threshold)
        results["merged_count"] = len(all_patterns) - len(merged)
        all_patterns = merged

    # Store merged patterns
    store = _get_store()
    for pattern in all_patterns:
        store.store(pattern)

    results["all_patterns"] = [
        {
            "id": p.id,
            "name": p.name,
            "category": p.category,
            "confidence": p.confidence,
        }
        for p in all_patterns
    ]
    results["total_unique"] = len(all_patterns)

    return results


def _merge_similar_patterns(
    patterns: list[Pattern], threshold: float
) -> list[Pattern]:
    """Merge similar patterns into representatives."""
    if not patterns:
        return []

    merged: list[Pattern] = []
    used: set[str] = set()

    for i, p1 in enumerate(patterns):
        if p1.id in used:
            continue

        # Find similar patterns
        similar_group = [p1]

        for _j, p2 in enumerate(patterns[i + 1 :], start=i + 1):
            if p2.id in used:
                continue

            similarity = _calculate_similarity(p1, p2)
            if similarity >= threshold:
                similar_group.append(p2)
                used.add(p2.id)

        # Create merged pattern (use highest confidence as representative)
        if len(similar_group) > 1:
            similar_group.sort(key=lambda p: p.confidence, reverse=True)
            representative = similar_group[0]

            # Merge tags from all similar patterns
            all_tags = set(representative.tags)
            for p in similar_group[1:]:
                all_tags.update(p.tags)
            representative.tags = list(all_tags)

            # Merge triggers
            all_triggers = {t.phrase: t for t in representative.triggers}
            for p in similar_group[1:]:
                for t in p.triggers:
                    if t.phrase not in all_triggers:
                        all_triggers[t.phrase] = t
            representative.triggers = list(all_triggers.values())

            merged.append(representative)
        else:
            merged.append(p1)

        used.add(p1.id)

    return merged


def main() -> None:
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
