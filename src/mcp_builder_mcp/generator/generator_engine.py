"""Generator engine for producing MCP servers from patterns."""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from mcp_builder_mcp.models import Pattern


@dataclass
class ToolSpec:
    """Specification for a generated tool."""

    name: str
    function: str
    module: str
    description: str
    params: list[dict[str, Any]] = field(default_factory=list)
    steps: list[dict[str, str]] = field(default_factory=list)
    returns: str = "dict with result"
    imports: list[str] = field(default_factory=list)


@dataclass
class GeneratedFile:
    """A generated file."""

    path: str
    content: str


@dataclass
class GeneratedMCP:
    """Result of MCP generation."""

    pattern_id: str
    package_name: str
    output_dir: Path
    files: list[GeneratedFile] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pattern_id": self.pattern_id,
            "package_name": self.package_name,
            "output_dir": str(self.output_dir),
            "files": [{"path": f.path, "size": len(f.content)} for f in self.files],
            "file_count": len(self.files),
        }


class GeneratorEngine:
    """Engine for generating MCP servers from patterns."""

    TEMPLATES_DIR = Path(__file__).parent / "templates"

    def __init__(self, templates_dir: Path | None = None):
        """Initialize generator engine.

        Args:
            templates_dir: Custom templates directory. Uses default if not provided.
        """
        self.templates_dir = templates_dir or self.TEMPLATES_DIR

        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(default=False),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def generate(
        self,
        pattern: Pattern,
        output_dir: Path | str,
        include_tests: bool = True,
        include_docs: bool = True,
    ) -> GeneratedMCP:
        """Generate a complete MCP server from a pattern.

        Args:
            pattern: Pattern to generate from.
            output_dir: Directory to write generated files.
            include_tests: Generate test files.
            include_docs: Generate README and SKILL.md.

        Returns:
            GeneratedMCP with all generated files.
        """
        output_path = Path(output_dir)
        package_name = self._pattern_to_package_name(pattern)

        result = GeneratedMCP(
            pattern_id=pattern.id,
            package_name=package_name,
            output_dir=output_path,
        )

        # Generate tool specifications from pattern
        tools = self._pattern_to_tools(pattern)

        # Generate context for templates
        context = self._build_context(pattern, package_name, tools, include_docs=include_docs)

        # Generate server.py
        server_content = self._render_template("server.py.j2", context)
        result.files.append(
            GeneratedFile(
                path=f"src/{package_name}/server.py",
                content=server_content,
            )
        )

        # Generate __init__.py for package
        init_content = f'"""{ pattern.name } MCP Server."""\n\n__version__ = "0.1.0"\n'
        result.files.append(
            GeneratedFile(
                path=f"src/{package_name}/__init__.py",
                content=init_content,
            )
        )

        # Generate tools directory and implementations
        tools_init = '"""Tool implementations."""\n'
        result.files.append(
            GeneratedFile(
                path=f"src/{package_name}/tools/__init__.py",
                content=tools_init,
            )
        )

        for tool in tools:
            tool_context = {**context, "tool": tool.__dict__}
            tool_content = self._render_template("tool.py.j2", tool_context)
            result.files.append(
                GeneratedFile(
                    path=f"src/{package_name}/tools/{tool.module}.py",
                    content=tool_content,
                )
            )

        # Generate pyproject.toml
        pyproject_content = self._render_template("pyproject.toml.j2", context)
        result.files.append(
            GeneratedFile(
                path="pyproject.toml",
                content=pyproject_content,
            )
        )

        # Generate tests
        if include_tests:
            test_content = self._render_template("test.py.j2", context)
            result.files.append(
                GeneratedFile(
                    path=f"tests/test_{package_name}.py",
                    content=test_content,
                )
            )

            conftest_content = '"""Test fixtures."""\n\nimport pytest\n'
            result.files.append(
                GeneratedFile(
                    path="tests/conftest.py",
                    content=conftest_content,
                )
            )

        # Generate docs
        if include_docs:
            readme_content = self._render_template("readme.md.j2", context)
            result.files.append(
                GeneratedFile(
                    path="README.md",
                    content=readme_content,
                )
            )

            skill_content = self._render_template("skill.md.j2", context)
            result.files.append(
                GeneratedFile(
                    path="SKILL.md",
                    content=skill_content,
                )
            )

            # Generate MCP_INFO.md with comprehensive documentation
            mcp_info_content = self._render_template("mcp_info.md.j2", context)
            result.files.append(
                GeneratedFile(
                    path="MCP_INFO.md",
                    content=mcp_info_content,
                )
            )

        return result

    def generate_preview(self, pattern: Pattern) -> dict[str, str]:
        """Generate a preview of files without writing to disk.

        Args:
            pattern: Pattern to preview.

        Returns:
            Dictionary of file paths to content.
        """
        result = self.generate(pattern, Path("/preview"))
        return {f.path: f.content for f in result.files}

    def write_files(self, generated: GeneratedMCP) -> list[Path]:
        """Write generated files to disk.

        Args:
            generated: Generated MCP to write.

        Returns:
            List of created file paths.
        """
        created: list[Path] = []

        for file in generated.files:
            file_path = generated.output_dir / file.path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(file.content, encoding="utf-8")
            created.append(file_path)

        return created

    def _pattern_to_package_name(self, pattern: Pattern) -> str:
        """Convert pattern name to valid Python package name."""
        # Convert to lowercase, replace spaces with underscores
        name = pattern.name.lower().replace(" ", "_")
        # Remove invalid characters
        name = re.sub(r"[^a-z0-9_]", "", name)
        # Ensure starts with letter
        if name and not name[0].isalpha():
            name = "mcp_" + name
        # Add suffix
        if not name.endswith("_mcp"):
            name += "_mcp"
        return name or "generated_mcp"

    def _pattern_to_tools(self, pattern: Pattern) -> list[ToolSpec]:
        """Convert pattern workflow to tool specifications."""
        tools: list[ToolSpec] = []

        # Group workflow steps into logical tools
        # For now, create one main tool from the pattern
        if pattern.workflow_steps:
            # Create main tool from workflow
            main_tool = ToolSpec(
                name=pattern.name,
                function=self._to_function_name(pattern.name),
                module=self._to_function_name(pattern.name),
                description=pattern.description,
                params=self._inputs_to_params(pattern.inputs),
                steps=[
                    {"description": step.description, "action": step.action}
                    for step in pattern.workflow_steps
                ],
                returns="dict with result",
            )
            tools.append(main_tool)
        else:
            # Create placeholder tool
            tools.append(
                ToolSpec(
                    name=pattern.name,
                    function=self._to_function_name(pattern.name),
                    module=self._to_function_name(pattern.name),
                    description=pattern.description or "Generated tool",
                    params=self._inputs_to_params(pattern.inputs),
                )
            )

        return tools

    def _inputs_to_params(self, inputs: list) -> list[dict[str, Any]]:
        """Convert pattern inputs to tool parameters."""
        params = []
        for inp in inputs:
            param = {
                "name": inp.name,
                "type": self._map_type(inp.type),
                "required": inp.required,
                "default": inp.default,
                "description": inp.description or f"{inp.name} parameter",
                "test_value": self._get_test_value(inp.type, inp.default),
            }
            params.append(param)
        return params

    def _map_type(self, type_str: str) -> str:
        """Map pattern types to Python types."""
        type_map = {
            "path": "str",
            "string": "str",
            "integer": "int",
            "number": "float",
            "boolean": "bool",
            "list": "list",
            "dict": "dict",
        }
        return type_map.get(type_str.lower(), "str")

    def _get_test_value(self, type_str: str, default: Any) -> Any:
        """Get a test value for a parameter type."""
        if default is not None:
            return default

        test_values = {
            "path": "/tmp/test",
            "string": "test",
            "str": "test",
            "integer": 1,
            "int": 1,
            "number": 1.0,
            "float": 1.0,
            "boolean": True,
            "bool": True,
            "list": [],
            "dict": {},
        }
        return test_values.get(type_str.lower(), "test")

    def _to_function_name(self, name: str) -> str:
        """Convert name to valid Python function name."""
        # Lowercase and replace spaces
        func = name.lower().replace(" ", "_").replace("-", "_")
        # Remove invalid characters
        func = re.sub(r"[^a-z0-9_]", "", func)
        # Ensure starts with letter
        if func and not func[0].isalpha():
            func = "fn_" + func
        return func or "generated_function"

    def _compose_instructions(
        self, pattern: Pattern, package_name: str, tools: list[ToolSpec]
    ) -> str:
        """Compose the instructions= text for FastMCP from pattern metadata."""
        lines: list[str] = []

        # Server identity and purpose
        lines.append(f"{pattern.name}: {pattern.description}")
        lines.append("")

        # Tool selection guide
        if len(tools) > 1:
            lines.append("TOOL SELECTION GUIDE:")
            for tool in tools:
                summary = (tool.description[:80] + "...") if len(tool.description) > 80 else tool.description
                lines.append(f"- {tool.function} -- {summary}")
            lines.append("")
        elif tools:
            lines.append(f"PRIMARY TOOL: {tools[0].function} -- {tools[0].description}")
            lines.append("")

        # Workflow overview
        if pattern.workflow_steps:
            step_names = [s.action for s in pattern.workflow_steps]
            lines.append(f"TYPICAL WORKFLOW: {' -> '.join(step_names)}")
            lines.append("")

        # Trigger context
        if pattern.triggers:
            lines.append("USE WHEN:")
            for trigger in pattern.triggers:
                lines.append(f'- User says: "{trigger.phrase}"')
            lines.append("")

        # Discovery hints
        lines.append("RESOURCES: Use resources/list to discover tool schema reference and onboarding guide.")
        lines.append("PROMPTS: Use prompts/list to discover pre-built workflow commands.")

        return "\n".join(lines)

    def _compose_resource_schema(self, tools: list[ToolSpec]) -> str:
        """Compose the schema resource text from tool specifications."""
        lines = ["# Tool Schema Reference", ""]
        for tool in tools:
            lines.append(f"## {tool.function}")
            lines.append(f"Description: {tool.description}")
            lines.append("")
            if tool.params:
                lines.append("Parameters:")
                for p in tool.params:
                    req = "required" if p.get("required") else "optional"
                    default_str = f", default={p['default']}" if p.get("default") is not None else ""
                    lines.append(f"  - {p['name']}: {p['type']} ({req}{default_str}) -- {p.get('description', '')}")
                lines.append("")
            lines.append(f"Returns: {tool.returns}")
            lines.append("")
        return "\n".join(lines)

    def _compose_prompts(
        self, pattern: Pattern, tools: list[ToolSpec]
    ) -> list[dict[str, str]]:
        """Compose MCP prompt definitions from pattern workflow steps."""
        prompts: list[dict[str, str]] = []

        if not pattern.workflow_steps:
            return prompts

        # Main workflow prompt
        func_name = "run_" + self._to_function_name(pattern.name)

        # Build params from pattern inputs that map to str
        params_sig_parts: list[str] = []
        for inp in pattern.inputs:
            if inp.type in ("path", "string"):
                params_sig_parts.append(f"{inp.name}: str")

        # Build body with numbered steps
        body_lines = [f'Execute the "{pattern.name}" workflow. Follow these steps in order:']
        body_lines.append("")
        for i, step in enumerate(pattern.workflow_steps, 1):
            body_lines.append(f"Step {i}: {step.description}")
            body_lines.append(f"   Action: {step.action}")
            body_lines.append("")
        body_lines.append("Report the result of each step and summarize the overall outcome.")

        prompts.append({
            "function": func_name,
            "description": f"Step-by-step {pattern.name} workflow.",
            "params_signature": ", ".join(params_sig_parts),
            "body": "\n".join(body_lines),
        })

        return prompts

    def _build_context(
        self,
        pattern: Pattern,
        package_name: str,
        tools: list[ToolSpec],
        include_docs: bool = True,
    ) -> dict[str, Any]:
        """Build template rendering context."""
        instructions_text = self._compose_instructions(pattern, package_name, tools)
        resource_schema_text = self._compose_resource_schema(tools)
        prompts = self._compose_prompts(pattern, tools)

        return {
            "pattern": {
                "id": pattern.id,
                "name": pattern.name,
                "description": pattern.description,
                "version": pattern.version,
                "triggers": [t.__dict__ for t in pattern.triggers],
                "inputs": [i.__dict__ for i in pattern.inputs],
                "outputs": [o.__dict__ for o in pattern.outputs],
                "workflow_steps": [s.__dict__ for s in pattern.workflow_steps],
                "category": pattern.category,
                "tags": pattern.tags,
                # Metadata for MCP_INFO.md generation
                "extracted_from": pattern.extracted_from,
                "extraction_date": (
                    pattern.extraction_date.isoformat()
                    if pattern.extraction_date
                    else None
                ),
                "confidence": pattern.confidence,
            },
            "package_name": package_name,
            "server_name": package_name.replace("_", "-"),
            "version": "0.1.0",
            "tools": [t.__dict__ for t in tools],
            "dependencies": self._infer_dependencies(pattern),
            # MCP self-description mechanisms
            "instructions_text": instructions_text,
            "resource_schema_text": resource_schema_text,
            "include_guide_resource": include_docs,
            "prompts": prompts,
        }

    def _infer_dependencies(self, pattern: Pattern) -> list[str]:
        """Infer package dependencies from pattern."""
        deps = []

        # Check workflow steps for common tool patterns
        step_actions = " ".join(s.action.lower() for s in pattern.workflow_steps)

        if "yaml" in step_actions:
            deps.append("pyyaml>=6.0")
        if "json" in step_actions:
            pass  # json is built-in
        if "git" in step_actions:
            deps.append("gitpython>=3.1")
        if "http" in step_actions or "request" in step_actions:
            deps.append("httpx>=0.27")

        return deps

    def _render_template(self, template_name: str, context: dict[str, Any]) -> str:
        """Render a template with context."""
        template = self.env.get_template(template_name)
        return template.render(**context)
