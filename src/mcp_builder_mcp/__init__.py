"""Pattern MCP - Reproducible Pattern MCP Builder.

An MCP Server that analyzes AI dialogue logs for reproducible workflow patterns,
scores them for buildability, and generates MCP Servers from selected patterns.
"""

__version__ = "0.1.0"

from mcp_builder_mcp.extractor import PatternExtractor
from mcp_builder_mcp.generator import GeneratorEngine, Validator
from mcp_builder_mcp.models import (
    Input,
    Output,
    Pattern,
    ScoredPattern,
    ScoreWeights,
    Step,
    Trigger,
)
from mcp_builder_mcp.parser import DialogueLog, LogParser, Session, Turn
from mcp_builder_mcp.scorer import ScoringEngine
from mcp_builder_mcp.store import (
    LearningEngine,
    MinnaSync,
    OutcomeStats,
    PatternStore,
    ScoreAdjustment,
)

__all__ = [
    # Models
    "Pattern",
    "Trigger",
    "Step",
    "Input",
    "Output",
    "ScoredPattern",
    "ScoreWeights",
    # Parser
    "LogParser",
    "DialogueLog",
    "Turn",
    "Session",
    # Extractor
    "PatternExtractor",
    # Scorer
    "ScoringEngine",
    # Store
    "PatternStore",
    "MinnaSync",
    "LearningEngine",
    "OutcomeStats",
    "ScoreAdjustment",
    # Generator
    "GeneratorEngine",
    "Validator",
]
