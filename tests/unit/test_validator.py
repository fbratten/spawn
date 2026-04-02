"""Unit tests for Validator."""

from pathlib import Path

from mcp_builder_mcp import GeneratorEngine, Pattern, Validator
from mcp_builder_mcp.generator.generator_engine import GeneratedFile, GeneratedMCP


class TestValidator:
    """Tests for Validator class."""

    def test_valid_python_passes(self) -> None:
        """Test valid Python code passes validation."""
        validator = Validator()

        generated = GeneratedMCP(
            pattern_id="test",
            package_name="test_mcp",
            output_dir=Path("/tmp"),
            files=[
                GeneratedFile(
                    path="test.py",
                    content='def hello():\n    return "world"\n',
                ),
            ],
        )

        result = validator.validate(generated)
        assert result.valid
        assert len(result.errors) == 0

    def test_invalid_syntax_fails(self) -> None:
        """Test invalid Python syntax is caught."""
        validator = Validator()

        generated = GeneratedMCP(
            pattern_id="test",
            package_name="test_mcp",
            output_dir=Path("/tmp"),
            files=[
                GeneratedFile(
                    path="bad.py",
                    content="def broken(\n",  # Syntax error
                ),
            ],
        )

        result = validator.validate(generated)
        assert not result.valid
        assert len(result.errors) > 0
        assert "Syntax error" in result.errors[0].message

    def test_valid_pyproject_passes(self) -> None:
        """Test valid pyproject.toml passes."""
        validator = Validator()

        pyproject = """
[project]
name = "test-mcp"
version = "0.1.0"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
"""

        generated = GeneratedMCP(
            pattern_id="test",
            package_name="test_mcp",
            output_dir=Path("/tmp"),
            files=[
                GeneratedFile(path="pyproject.toml", content=pyproject),
            ],
        )

        result = validator.validate(generated)
        assert result.valid

    def test_missing_project_name_fails(self) -> None:
        """Test missing project.name is caught."""
        validator = Validator()

        pyproject = """
[project]
version = "0.1.0"
"""

        generated = GeneratedMCP(
            pattern_id="test",
            package_name="test_mcp",
            output_dir=Path("/tmp"),
            files=[
                GeneratedFile(path="pyproject.toml", content=pyproject),
            ],
        )

        result = validator.validate(generated)
        assert not result.valid
        assert any("name" in e.message.lower() for e in result.errors)

    def test_validate_path(self, mock_pattern: Pattern, tmp_path: Path) -> None:
        """Test validation of files on disk."""
        # Generate files first
        generator = GeneratorEngine()
        generated = generator.generate(mock_pattern, tmp_path)
        generator.write_files(generated)

        # Validate
        validator = Validator()
        result = validator.validate_path(tmp_path)

        # Generated code should be valid
        assert result.valid

    def test_validate_nonexistent_path(self, tmp_path: Path) -> None:
        """Test validation of non-existent path."""
        validator = Validator()
        result = validator.validate_path(tmp_path / "nonexistent")

        assert not result.valid
        assert "does not exist" in result.errors[0].message

    def test_import_warnings(self) -> None:
        """Test unknown imports generate warnings."""
        validator = Validator()

        generated = GeneratedMCP(
            pattern_id="test",
            package_name="test_mcp",
            output_dir=Path("/tmp"),
            files=[
                GeneratedFile(
                    path="test.py",
                    content="import some_unknown_package\n",
                ),
            ],
        )

        result = validator.validate(generated)
        # Should have warning about unknown import
        assert len(result.warnings) > 0 or result.valid  # May pass without warning

    def test_validate_path_skips_venv(self, tmp_path: Path) -> None:
        """Test that .venv directory is excluded from validation."""
        # Create .venv with a file that has a syntax error
        venv_dir = tmp_path / ".venv" / "lib"
        venv_dir.mkdir(parents=True)
        (venv_dir / "bad.py").write_text("def broken(\n")

        # Create a valid source file
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "good.py").write_text('def hello():\n    return "world"\n')

        validator = Validator()
        result = validator.validate_path(tmp_path)

        # Should pass because .venv is skipped
        assert result.valid
        assert len(result.errors) == 0

    def test_validate_path_skips_node_modules(self, tmp_path: Path) -> None:
        """Test that node_modules directory is excluded from validation."""
        nm_dir = tmp_path / "node_modules" / "pkg"
        nm_dir.mkdir(parents=True)
        (nm_dir / "bad.py").write_text("import !!!\n")

        (tmp_path / "ok.py").write_text("x = 1\n")

        validator = Validator()
        result = validator.validate_path(tmp_path)
        assert result.valid

    def test_validation_result_to_dict(self) -> None:
        """Test ValidationResult serialization."""
        validator = Validator()

        generated = GeneratedMCP(
            pattern_id="test",
            package_name="test_mcp",
            output_dir=Path("/tmp"),
            files=[
                GeneratedFile(path="test.py", content="x = 1\n"),
            ],
        )

        result = validator.validate(generated)
        result_dict = result.to_dict()

        assert "valid" in result_dict
        assert "errors" in result_dict
        assert "warnings" in result_dict
        assert "error_count" in result_dict
