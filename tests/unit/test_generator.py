"""Unit tests for GeneratorEngine."""

from pathlib import Path

from mcp_builder_mcp import GeneratorEngine, Input, Pattern, Step


class TestGeneratorEngine:
    """Tests for GeneratorEngine class."""

    def test_generate_creates_files(self, mock_pattern: Pattern, tmp_path: Path) -> None:
        """Test generate creates expected files."""
        generator = GeneratorEngine()
        result = generator.generate(mock_pattern, tmp_path)

        assert result.pattern_id == mock_pattern.id
        assert len(result.files) > 0

        # Check expected files
        paths = [f.path for f in result.files]
        assert any("server.py" in p for p in paths)
        assert any("pyproject.toml" in p for p in paths)

    def test_generate_preview(self, mock_pattern: Pattern) -> None:
        """Test preview returns file contents without writing."""
        generator = GeneratorEngine()
        preview = generator.generate_preview(mock_pattern)

        assert isinstance(preview, dict)
        assert len(preview) > 0
        assert all(isinstance(v, str) for v in preview.values())

    def test_write_files(self, mock_pattern: Pattern, tmp_path: Path) -> None:
        """Test files are written to disk."""
        generator = GeneratorEngine()
        result = generator.generate(mock_pattern, tmp_path)
        created = generator.write_files(result)

        assert len(created) > 0
        assert all(p.exists() for p in created)

    def test_package_name_generation(self) -> None:
        """Test package name is valid Python identifier."""
        generator = GeneratorEngine()

        pattern = Pattern(id="test", name="Session Handover Generator")
        name = generator._pattern_to_package_name(pattern)

        assert name == "session_handover_generator_mcp"
        assert name.isidentifier() or "_" in name

    def test_package_name_handles_special_chars(self) -> None:
        """Test package name handles special characters."""
        generator = GeneratorEngine()

        pattern = Pattern(id="test", name="Test-Pattern (v2.0)")
        name = generator._pattern_to_package_name(pattern)

        # Should be valid identifier without special chars
        assert "(" not in name
        assert ")" not in name
        assert "-" not in name
        assert "." not in name

    def test_tools_from_pattern(self, mock_pattern: Pattern) -> None:
        """Test tool extraction from pattern."""
        generator = GeneratorEngine()
        tools = generator._pattern_to_tools(mock_pattern)

        assert len(tools) >= 1
        assert tools[0].function

    def test_inputs_to_params(self) -> None:
        """Test input conversion to parameters."""
        generator = GeneratorEngine()

        inputs = [
            Input(name="file_path", type="path", required=True),
            Input(name="count", type="integer", required=False, default=10),
        ]
        params = generator._inputs_to_params(inputs)

        assert len(params) == 2
        assert params[0]["name"] == "file_path"
        assert params[0]["type"] == "str"
        assert params[1]["default"] == 10

    def test_infer_dependencies(self) -> None:
        """Test dependency inference from pattern."""
        generator = GeneratorEngine()

        pattern = Pattern(
            id="test",
            name="Test",
            workflow_steps=[
                Step(id="1", action="read_yaml"),
                Step(id="2", action="make_http_request"),
            ],
        )
        deps = generator._infer_dependencies(pattern)

        assert "pyyaml>=6.0" in deps
        assert "httpx>=0.27" in deps

    def test_template_rendering(self, mock_pattern: Pattern, tmp_path: Path) -> None:
        """Test templates render without errors."""
        generator = GeneratorEngine()
        result = generator.generate(mock_pattern, tmp_path)

        # All files should have content
        for file in result.files:
            assert len(file.content) > 0
            # Python files should have valid syntax
            if file.path.endswith(".py"):
                compile(file.content, file.path, "exec")

    def test_generate_without_tests(self, mock_pattern: Pattern, tmp_path: Path) -> None:
        """Test generation without test files."""
        generator = GeneratorEngine()
        result = generator.generate(mock_pattern, tmp_path, include_tests=False)

        paths = [f.path for f in result.files]
        assert not any("test_" in p for p in paths)

    def test_generate_without_docs(self, mock_pattern: Pattern, tmp_path: Path) -> None:
        """Test generation without documentation."""
        generator = GeneratorEngine()
        result = generator.generate(mock_pattern, tmp_path, include_docs=False)

        paths = [f.path for f in result.files]
        assert not any("README" in p for p in paths)
        assert not any("SKILL" in p for p in paths)


class TestSelfDescription:
    """Tests for MCP self-description generation."""

    def test_instructions_in_context(self, mock_pattern: Pattern) -> None:
        """Test instructions text is composed from pattern metadata."""
        generator = GeneratorEngine()
        tools = generator._pattern_to_tools(mock_pattern)
        pkg = generator._pattern_to_package_name(mock_pattern)
        context = generator._build_context(mock_pattern, pkg, tools)

        assert "instructions_text" in context
        assert mock_pattern.name in context["instructions_text"]
        assert mock_pattern.description in context["instructions_text"]

    def test_instructions_includes_tool_guide(self, mock_pattern: Pattern) -> None:
        """Test instructions text references tool functions."""
        generator = GeneratorEngine()
        tools = generator._pattern_to_tools(mock_pattern)
        pkg = generator._pattern_to_package_name(mock_pattern)
        context = generator._build_context(mock_pattern, pkg, tools)

        for tool in tools:
            assert tool.function in context["instructions_text"]

    def test_instructions_includes_triggers(self, mock_pattern: Pattern) -> None:
        """Test instructions text includes trigger phrases."""
        generator = GeneratorEngine()
        tools = generator._pattern_to_tools(mock_pattern)
        pkg = generator._pattern_to_package_name(mock_pattern)
        context = generator._build_context(mock_pattern, pkg, tools)

        for trigger in mock_pattern.triggers:
            assert trigger.phrase in context["instructions_text"]

    def test_instructions_includes_workflow(self, mock_pattern: Pattern) -> None:
        """Test instructions text includes workflow step actions."""
        generator = GeneratorEngine()
        tools = generator._pattern_to_tools(mock_pattern)
        pkg = generator._pattern_to_package_name(mock_pattern)
        context = generator._build_context(mock_pattern, pkg, tools)

        for step in mock_pattern.workflow_steps:
            assert step.action in context["instructions_text"]

    def test_resource_schema_in_context(self, mock_pattern: Pattern) -> None:
        """Test resource schema text is composed from tool specs."""
        generator = GeneratorEngine()
        tools = generator._pattern_to_tools(mock_pattern)
        pkg = generator._pattern_to_package_name(mock_pattern)
        context = generator._build_context(mock_pattern, pkg, tools)

        assert "resource_schema_text" in context
        for tool in tools:
            assert tool.function in context["resource_schema_text"]

    def test_prompts_in_context(self, mock_pattern: Pattern) -> None:
        """Test prompts are derived from workflow steps."""
        generator = GeneratorEngine()
        tools = generator._pattern_to_tools(mock_pattern)
        pkg = generator._pattern_to_package_name(mock_pattern)
        context = generator._build_context(mock_pattern, pkg, tools)

        assert "prompts" in context
        assert len(context["prompts"]) >= 1
        for prompt in context["prompts"]:
            assert "function" in prompt
            assert "description" in prompt
            assert "body" in prompt

    def test_no_prompts_without_steps(self) -> None:
        """Test no prompts generated for pattern without workflow steps."""
        generator = GeneratorEngine()
        pattern = Pattern(id="test", name="Simple Pattern", description="No steps here")
        tools = generator._pattern_to_tools(pattern)
        pkg = generator._pattern_to_package_name(pattern)
        context = generator._build_context(pattern, pkg, tools)

        assert context["prompts"] == []

    def test_generated_server_has_instructions(self, mock_pattern: Pattern, tmp_path: Path) -> None:
        """Test generated server.py contains instructions= parameter."""
        generator = GeneratorEngine()
        result = generator.generate(mock_pattern, tmp_path)

        server_file = next(f for f in result.files if f.path.endswith("server.py"))
        assert "instructions=" in server_file.content

    def test_generated_server_has_resource(self, mock_pattern: Pattern, tmp_path: Path) -> None:
        """Test generated server.py contains @mcp.resource()."""
        generator = GeneratorEngine()
        result = generator.generate(mock_pattern, tmp_path)

        server_file = next(f for f in result.files if f.path.endswith("server.py"))
        assert "@mcp.resource(" in server_file.content
        assert "resource_schema" in server_file.content

    def test_generated_server_has_prompt(self, mock_pattern: Pattern, tmp_path: Path) -> None:
        """Test generated server.py contains @mcp.prompt()."""
        generator = GeneratorEngine()
        result = generator.generate(mock_pattern, tmp_path)

        server_file = next(f for f in result.files if f.path.endswith("server.py"))
        assert "@mcp.prompt(" in server_file.content

    def test_no_guide_resource_without_docs(self, mock_pattern: Pattern, tmp_path: Path) -> None:
        """Test guide resource is omitted when include_docs=False."""
        generator = GeneratorEngine()
        result = generator.generate(mock_pattern, tmp_path, include_docs=False)

        server_file = next(f for f in result.files if f.path.endswith("server.py"))
        assert "resource_guide" not in server_file.content
        # Schema resource should still be present
        assert "resource_schema" in server_file.content


class TestToolSpec:
    """Tests for ToolSpec generation."""

    def test_tool_has_required_fields(self, mock_pattern: Pattern) -> None:
        """Test generated tools have required fields."""
        generator = GeneratorEngine()
        tools = generator._pattern_to_tools(mock_pattern)

        for tool in tools:
            assert tool.name
            assert tool.function
            assert tool.module
