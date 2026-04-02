## spawn - Copilot Instructions

spawn is a meta-MCP server that analyzes session log patterns and generates new MCP servers.

### Key Files
- `src/mcp_builder_mcp/server.py` - FastMCP server (17 tools)
- `src/mcp_builder_mcp/parser/log_parser.py` - Multi-format log parsing
- `src/mcp_builder_mcp/scorer/scoring_engine.py` - 5-dimension pattern scoring
- `src/mcp_builder_mcp/generator/generator_engine.py` - Code generation from patterns
- `src/mcp_builder_mcp/store/pattern_store.py` - JSON-backed pattern library
- `tests/` - 14 files, 156 tests (unit + integration + e2e)

### Architecture
- AI-agnostic design (data + utilities, AI does semantic understanding)
- Dependencies: mcp>=1.0.0, pyyaml>=6.0, jinja2>=3.1
- Optional: Minna Memory integration (graceful degradation)
- Generated code uses Jinja2 templates in generator/templates/

### Testing
Run: `python -m pytest tests/ -v`
