---
title: Changelog
section: 05-appendix
order: 3
generated: 2026-04-03T01:21:31.201519
---
# Changelog

Track of changes and version history for this project.


## Recent Changes

See project commit history for recent changes.



## Version History

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- Project initialization
- Project registered as PROJ-CAHJG-BLHLI in Control Tower
- ai-memory structure with shared context
- Minna Memory configuration

### Derived Projects
- **8do-mcp v0.1.0** - Ralph Loop Orchestration MCP Server (27 tests)
  - Core loop engine with TaskQueue, CircuitBreaker, RalphLoop
  - 12 MCP tools: loop management, task inspection, configuration, observability
  - Evidence-based verification with Verdict gate (ACCEPT/REVISE/REJECT)
  - Whitelist-based Skills configuration with lanes
  - Based on: loop orchestration patterns and skills architecture

- **session-handover-mcp v0.4.0** - Multi-project handover support (138 tests)
  - Workspace-level handover tools
  - generate_workspace_handover, workspace_resume

- **manual-mcp v1.4.0** - Content Quality Enhancements (299 tests)
  - Phase 1: Content scoring foundation (priority propagation, relevance scores)
  - Phase 2: Smart fallbacks (FallbackContentGenerator, MetadataCollector)
  - Phase 3: Content mapping (ContentMapper for template variables)
  - Phase 4: Cross-reference links (CrossReferenceEngine)

## [0.0.0] - 2026-01-24

### Added
- Initial project scaffold
- KB materials from previous session analysis

---

## See Also

- [Getting Started](../01-user-guide/01-getting-started.md)
- [Installation](../01-user-guide/02-installation.md)
- [Quick Start](../01-user-guide/03-quick-start.md)
- [Worked Examples](../01-user-guide/04-worked-examples.md)
- [Overview](../02-api-reference/01-overview.md)

---

Previous: [FAQ](02-faq.md)