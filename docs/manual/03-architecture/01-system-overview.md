---
title: System Overview
section: 03-architecture
order: 1
generated: 2026-04-03T01:30:01.214714
---
# System Overview

This section describes the system architecture.


## Architecture

- AI-agnostic design (data + utilities, AI does semantic understanding)
- Dependencies: mcp>=1.0.0, pyyaml>=6.0, jinja2>=3.1
- Optional: Minna Memory integration (graceful degradation)
- Generated code uses Jinja2 templates in generator/templates/

---

## See Also

- [Getting Started](../01-user-guide/01-getting-started.md)
- [Installation](../01-user-guide/02-installation.md)
- [Quick Start](../01-user-guide/03-quick-start.md)
- [Worked Examples](../01-user-guide/04-worked-examples.md)
- [Overview](../02-api-reference/01-overview.md)

---

Next: [Data Models](02-data-models.md)