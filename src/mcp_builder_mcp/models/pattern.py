"""Pattern data models."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Trigger:
    """A trigger condition for a pattern."""

    phrase: str
    """User phrase that triggers the pattern."""

    condition: str | None = None
    """Optional context condition (e.g., 'session_ending')."""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {"phrase": self.phrase, "condition": self.condition}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Trigger":
        """Create from dictionary."""
        return cls(phrase=data["phrase"], condition=data.get("condition"))


@dataclass
class Input:
    """An input parameter for a pattern."""

    name: str
    type: str  # path, string, integer, list, etc.
    required: bool = True
    default: Any = None
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "type": self.type,
            "required": self.required,
            "default": self.default,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Input":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            type=data["type"],
            required=data.get("required", True),
            default=data.get("default"),
            description=data.get("description", ""),
        )


@dataclass
class Output:
    """An output produced by a pattern."""

    name: str
    type: str  # file, string, dict, etc.
    format: str | None = None  # markdown, yaml, json, etc.
    location: str | None = None  # where the output is stored

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "type": self.type,
            "format": self.format,
            "location": self.location,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Output":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            type=data["type"],
            format=data.get("format"),
            location=data.get("location"),
        )


@dataclass
class Step:
    """A workflow step in a pattern."""

    id: str
    action: str
    description: str = ""
    template: str | None = None
    depends_on: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "action": self.action,
            "description": self.description,
            "template": self.template,
            "depends_on": self.depends_on,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Step":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            action=data["action"],
            description=data.get("description", ""),
            template=data.get("template"),
            depends_on=data.get("depends_on", []),
        )


@dataclass
class Pattern:
    """A reproducible workflow pattern extracted from logs."""

    id: str
    name: str
    description: str = ""
    version: str = "1.0.0"

    # Extraction metadata
    extracted_from: str | None = None
    extraction_date: datetime | None = None
    confidence: float = 1.0

    # Pattern structure
    triggers: list[Trigger] = field(default_factory=list)
    inputs: list[Input] = field(default_factory=list)
    outputs: list[Output] = field(default_factory=list)
    workflow_steps: list[Step] = field(default_factory=list)

    # Categorization
    category: str = "general"
    tags: list[str] = field(default_factory=list)

    # Source context (for debugging/tracing)
    source_context: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for YAML serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "extracted_from": self.extracted_from,
            "extraction_date": (
                self.extraction_date.isoformat() if self.extraction_date else None
            ),
            "confidence": self.confidence,
            "triggers": [t.to_dict() for t in self.triggers],
            "inputs": [i.to_dict() for i in self.inputs],
            "outputs": [o.to_dict() for o in self.outputs],
            "workflow_steps": [s.to_dict() for s in self.workflow_steps],
            "category": self.category,
            "tags": self.tags,
            "source_context": self.source_context,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Pattern":
        """Create from dictionary."""
        extraction_date = None
        if data.get("extraction_date"):
            extraction_date = datetime.fromisoformat(data["extraction_date"])

        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            extracted_from=data.get("extracted_from"),
            extraction_date=extraction_date,
            confidence=data.get("confidence", 1.0),
            triggers=[Trigger.from_dict(t) for t in data.get("triggers", [])],
            inputs=[Input.from_dict(i) for i in data.get("inputs", [])],
            outputs=[Output.from_dict(o) for o in data.get("outputs", [])],
            workflow_steps=[Step.from_dict(s) for s in data.get("workflow_steps", [])],
            category=data.get("category", "general"),
            tags=data.get("tags", []),
            source_context=data.get("source_context", ""),
        )
