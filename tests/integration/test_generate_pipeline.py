"""Integration tests for the generate pipeline."""

from pathlib import Path

import pytest

from mcp_builder_mcp import GeneratorEngine, Pattern, Validator


class TestGeneratePipeline:
    """Integration tests for Pattern → Generate → Validate pipeline."""

    def test_full_generation_pipeline(
        self, mock_pattern: Pattern, tmp_path: Path
    ) -> None:
        """Test complete generation pipeline."""
        output_dir = tmp_path / "generated"

        # Generate
        generator = GeneratorEngine()
        generated = generator.generate(mock_pattern, output_dir)

        assert len(generated.files) > 0

        # Write
        created = generator.write_files(generated)
        assert len(created) > 0
        assert all(p.exists() for p in created)

        # Validate
        validator = Validator()
        result = validator.validate(generated)

        assert result.valid

    def test_generated_server_has_structure(
        self, mock_pattern: Pattern, tmp_path: Path
    ) -> None:
        """Test generated server has correct structure."""
        output_dir = tmp_path / "generated"

        generator = GeneratorEngine()
        generated = generator.generate(mock_pattern, output_dir)
        generator.write_files(generated)

        # Check structure
        assert (output_dir / "pyproject.toml").exists()
        assert (output_dir / "README.md").exists()
        assert (output_dir / "SKILL.md").exists()

        # Check src directory
        src_dir = output_dir / "src" / generated.package_name
        assert src_dir.exists()
        assert (src_dir / "__init__.py").exists()
        assert (src_dir / "server.py").exists()
        assert (src_dir / "tools").exists()

    def test_generated_tests_structure(
        self, mock_pattern: Pattern, tmp_path: Path
    ) -> None:
        """Test generated tests have correct structure."""
        output_dir = tmp_path / "generated"

        generator = GeneratorEngine()
        generated = generator.generate(mock_pattern, output_dir, include_tests=True)
        generator.write_files(generated)

        # Check tests
        assert (output_dir / "tests").exists()
        assert (output_dir / "tests" / "conftest.py").exists()


class TestSelfDescriptionPipeline:
    """Integration tests for self-description in generated servers."""

    def test_self_description_compiles(
        self, mock_pattern: Pattern, tmp_path: Path
    ) -> None:
        """Test generated server with all self-description features compiles."""
        output_dir = tmp_path / "generated"

        generator = GeneratorEngine()
        generated = generator.generate(mock_pattern, output_dir)
        generator.write_files(generated)

        server_file = output_dir / "src" / generated.package_name / "server.py"
        content = server_file.read_text()

        # All four mechanisms present
        assert "instructions=" in content
        assert "@mcp.resource(" in content
        assert "@mcp.prompt(" in content
        assert "def resource_schema" in content

        # Still valid Python
        compile(content, str(server_file), "exec")

    def test_self_description_validates_clean(
        self, mock_pattern: Pattern, tmp_path: Path
    ) -> None:
        """Test generated server passes validation without self-description warnings."""
        output_dir = tmp_path / "generated"

        generator = GeneratorEngine()
        generated = generator.generate(mock_pattern, output_dir)

        validator = Validator()
        result = validator.validate(generated)
        assert result.valid

        # No self-description warnings for generated server
        desc_warnings = [
            w for w in result.warnings
            if "instructions=" in w.message
            or "@mcp.resource" in w.message
            or "@mcp.prompt" in w.message
        ]
        assert len(desc_warnings) == 0


class TestGeneratedServerRuns:
    """Integration tests for generated server execution."""

    def test_generated_python_syntax_valid(
        self, mock_pattern: Pattern, tmp_path: Path
    ) -> None:
        """Test all generated Python files have valid syntax."""
        output_dir = tmp_path / "generated"

        generator = GeneratorEngine()
        generated = generator.generate(mock_pattern, output_dir)
        generator.write_files(generated)

        # Check all Python files compile
        for py_file in output_dir.rglob("*.py"):
            content = py_file.read_text()
            try:
                compile(content, str(py_file), "exec")
            except SyntaxError as e:
                pytest.fail(f"Syntax error in {py_file}: {e}")

    def test_pyproject_is_valid_toml(
        self, mock_pattern: Pattern, tmp_path: Path
    ) -> None:
        """Test generated pyproject.toml is valid."""
        import tomllib

        output_dir = tmp_path / "generated"

        generator = GeneratorEngine()
        generated = generator.generate(mock_pattern, output_dir)
        generator.write_files(generated)

        pyproject = output_dir / "pyproject.toml"
        content = pyproject.read_text()

        # Should parse without error
        data = tomllib.loads(content)
        assert "project" in data
        assert "name" in data["project"]
