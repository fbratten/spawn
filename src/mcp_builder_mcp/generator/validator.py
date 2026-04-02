"""Validator for generated MCP code."""

import ast
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mcp_builder_mcp.generator.generator_engine import GeneratedMCP

# Directories to exclude from recursive file scanning
_EXCLUDE_DIRS = {
    ".venv", "venv", "node_modules", "__pycache__", ".git", ".pytest_cache",
    ".ruff_cache", "build", "dist", ".eggs", ".tox", ".mypy_cache",
}


def _should_skip(file_path: Path, base_path: Path) -> bool:
    """Check if a file should be skipped based on directory exclusions."""
    rel = file_path.relative_to(base_path)
    return any(part in _EXCLUDE_DIRS for part in rel.parts)


@dataclass
class ValidationError:
    """A validation error."""

    file: str
    line: int | None
    message: str
    severity: str = "error"  # error, warning

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "file": self.file,
            "line": self.line,
            "message": self.message,
            "severity": self.severity,
        }


@dataclass
class ValidationResult:
    """Result of validation."""

    valid: bool
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationError] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "valid": self.valid,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
        }


class Validator:
    """Validator for generated MCP code."""

    def validate(self, generated: GeneratedMCP) -> ValidationResult:
        """Validate a generated MCP.

        Args:
            generated: Generated MCP to validate.

        Returns:
            ValidationResult with any errors or warnings.
        """
        errors: list[ValidationError] = []
        warnings: list[ValidationError] = []

        for file in generated.files:
            # Only validate Python files
            if file.path.endswith(".py"):
                file_errors, file_warnings = self._validate_python(
                    file.path, file.content
                )
                errors.extend(file_errors)
                warnings.extend(file_warnings)

            # Validate pyproject.toml
            elif file.path.endswith("pyproject.toml"):
                file_errors, file_warnings = self._validate_pyproject(
                    file.path, file.content
                )
                errors.extend(file_errors)
                warnings.extend(file_warnings)

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def validate_path(self, mcp_path: Path | str) -> ValidationResult:
        """Validate an MCP at a given path.

        Args:
            mcp_path: Path to MCP directory.

        Returns:
            ValidationResult.
        """
        path = Path(mcp_path)
        errors: list[ValidationError] = []
        warnings: list[ValidationError] = []

        if not path.exists():
            errors.append(
                ValidationError(
                    file=str(path),
                    line=None,
                    message=f"Directory does not exist: {path}",
                )
            )
            return ValidationResult(valid=False, errors=errors)

        # Find and validate all Python files (skip excluded dirs)
        for py_file in path.rglob("*.py"):
            if _should_skip(py_file, path):
                continue
            content = py_file.read_text(encoding="utf-8")
            rel_path = str(py_file.relative_to(path))
            file_errors, file_warnings = self._validate_python(rel_path, content)
            errors.extend(file_errors)
            warnings.extend(file_warnings)

        # Validate pyproject.toml if exists
        pyproject = path / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text(encoding="utf-8")
            file_errors, file_warnings = self._validate_pyproject(
                "pyproject.toml", content
            )
            errors.extend(file_errors)
            warnings.extend(file_warnings)

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def _validate_python(
        self, file_path: str, content: str
    ) -> tuple[list[ValidationError], list[ValidationError]]:
        """Validate Python syntax and basic structure."""
        errors: list[ValidationError] = []
        warnings: list[ValidationError] = []

        # Check syntax
        try:
            ast.parse(content)
        except SyntaxError as e:
            errors.append(
                ValidationError(
                    file=file_path,
                    line=e.lineno,
                    message=f"Syntax error: {e.msg}",
                )
            )
            return errors, warnings

        # Check for common issues
        tree = ast.parse(content)

        # Check for undefined names (basic check)
        defined_names = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef | ast.AsyncFunctionDef, ast.ClassDef)):
                defined_names.add(node.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name.split(".")[0]
                    defined_names.add(name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname or alias.name
                    defined_names.add(name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        defined_names.add(target.id)

        # Check imports are resolvable (basic check for standard library)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name.split(".")[0]
                    if not self._is_valid_import(module):
                        warnings.append(
                            ValidationError(
                                file=file_path,
                                line=node.lineno,
                                message=f"Import may not be resolvable: {alias.name}",
                                severity="warning",
                            )
                        )
            elif isinstance(node, ast.ImportFrom) and node.module:
                module = node.module.split(".")[0]
                if not self._is_valid_import(module):
                    warnings.append(
                        ValidationError(
                            file=file_path,
                            line=node.lineno,
                            message=f"Import may not be resolvable: {node.module}",
                            severity="warning",
                        )
                    )

        # Check MCP self-description features in server files
        warnings.extend(self._check_server_features(file_path, content))

        return errors, warnings

    def _check_server_features(
        self, file_path: str, content: str
    ) -> list[ValidationError]:
        """Check for MCP self-description features in server.py files."""
        warnings: list[ValidationError] = []

        if not file_path.endswith("server.py"):
            return warnings

        if "instructions=" not in content:
            warnings.append(
                ValidationError(
                    file=file_path,
                    line=None,
                    message="Server missing 'instructions=' on FastMCP() — AI agents won't know what this server does",
                    severity="warning",
                )
            )

        if "@mcp.resource(" not in content:
            warnings.append(
                ValidationError(
                    file=file_path,
                    line=None,
                    message="No @mcp.resource() defined — AI agents can't discover deep documentation on demand",
                    severity="warning",
                )
            )

        if "@mcp.prompt(" not in content:
            warnings.append(
                ValidationError(
                    file=file_path,
                    line=None,
                    message="No @mcp.prompt() defined — no pre-built workflow commands available",
                    severity="warning",
                )
            )

        return warnings

    def _validate_pyproject(
        self, file_path: str, content: str
    ) -> tuple[list[ValidationError], list[ValidationError]]:
        """Validate pyproject.toml structure."""
        errors: list[ValidationError] = []
        warnings: list[ValidationError] = []

        try:
            import tomllib

            data = tomllib.loads(content)

            # Check required sections
            if "project" not in data:
                errors.append(
                    ValidationError(
                        file=file_path,
                        line=None,
                        message="Missing [project] section",
                    )
                )
            else:
                project = data["project"]
                if "name" not in project:
                    errors.append(
                        ValidationError(
                            file=file_path,
                            line=None,
                            message="Missing project.name",
                        )
                    )
                if "version" not in project:
                    warnings.append(
                        ValidationError(
                            file=file_path,
                            line=None,
                            message="Missing project.version",
                            severity="warning",
                        )
                    )

            if "build-system" not in data:
                warnings.append(
                    ValidationError(
                        file=file_path,
                        line=None,
                        message="Missing [build-system] section",
                        severity="warning",
                    )
                )

        except Exception as e:
            errors.append(
                ValidationError(
                    file=file_path,
                    line=None,
                    message=f"Invalid TOML: {e}",
                )
            )

        return errors, warnings

    def _is_valid_import(self, module: str) -> bool:
        """Check if a module is likely valid."""
        # Standard library modules (partial list)
        stdlib = {
            "os",
            "sys",
            "re",
            "json",
            "pathlib",
            "typing",
            "dataclasses",
            "datetime",
            "collections",
            "functools",
            "itertools",
            "subprocess",
            "ast",
            "tomllib",
            "hashlib",
            "uuid",
        }

        # Known third-party modules
        known_third_party = {
            "mcp",
            "pytest",
            "jinja2",
            "yaml",
            "pyyaml",
            "httpx",
            "requests",
            "gitpython",
        }

        # Package-relative imports are allowed
        if module.startswith("."):
            return True

        return module in stdlib or module in known_third_party


def run_ruff(path: Path) -> ValidationResult:
    """Run ruff linter on generated code.

    Args:
        path: Path to code directory.

    Returns:
        ValidationResult from ruff.
    """
    errors: list[ValidationError] = []
    warnings: list[ValidationError] = []

    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", str(path), "--output-format=json"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.stdout:
            import json

            issues = json.loads(result.stdout)
            for issue in issues:
                severity = "error" if issue.get("fix") is None else "warning"
                err = ValidationError(
                    file=issue.get("filename", "unknown"),
                    line=issue.get("location", {}).get("row"),
                    message=issue.get("message", "Unknown issue"),
                    severity=severity,
                )
                if severity == "error":
                    errors.append(err)
                else:
                    warnings.append(err)

    except subprocess.TimeoutExpired:
        warnings.append(
            ValidationError(
                file=str(path),
                line=None,
                message="Ruff timed out",
                severity="warning",
            )
        )
    except FileNotFoundError:
        warnings.append(
            ValidationError(
                file=str(path),
                line=None,
                message="Ruff not installed",
                severity="warning",
            )
        )

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )
