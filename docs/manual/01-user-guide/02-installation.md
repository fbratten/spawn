---
title: Installation
section: 01-user-guide
order: 2
generated: 2026-04-03T01:30:01.109223
---
# Installation

## Install spawn

```bash
# Clone the repository
git clone <repository-url>
cd spawn

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```


## Requirements

| Package | Version |
|---------|---------|
| mcp | >= 1.0.0 |
| pyyaml | >= 6.0 |
| jinja2 | >= 3.1 |



## Quick Setup

```bash
uv venv .venv --python 3.12
uv pip install -e ".[dev]" --python .venv/bin/python
```

---

## See Also

- [Overview](../02-api-reference/01-overview.md)
- [System Overview](../03-architecture/01-system-overview.md)
- [Data Models](../03-architecture/02-data-models.md)
- [Configuration](../04-reference/01-configuration.md)
- [Error Handling](../04-reference/02-error-handling.md)

---

Previous: [Getting Started](01-getting-started.md) | Next: [Quick Start](03-quick-start.md)