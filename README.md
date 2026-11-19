# AB-hub

**Project Intelligence & Repository Control System**

> Every project has a history. AB-hub makes sure none of it gets lost.  
> **Know what you built. Control what you own.**

Version **0.1.0**

## Overview

AB-hub is a local-first, read-only CLI application that discovers, inventories, analyzes, classifies and monitors all GitHub repositories you have authorized access to (personal, private and organization repositories).

It acts as a central engineering archive so you never lose track of projects, technologies, activity history or abandoned work.

### Key Features

- Discover all accessible repositories (owner / collaborator / organization)
- Technology & dependency detection
- Commit & activity intelligence with explainable scoring
- Local SQLite persistence (works offline after first sync)
- Incremental scanning
- Filtering, search, comparison and export (JSON / CSV / Markdown)
- Fully modular and extensible architecture

## Requirements

- Python 3.12+
- A GitHub Personal Access Token with appropriate scopes:
  - `repo` (for private repositories)
  - `read:org` (for organization repositories)

## Installation

```bash
# Clone or extract the project
cd AB-hub

# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate   # Linux / macOS
# .venv\Scripts\activate    # Windows

# Install
pip install -e ".[dev]"
```

## Quick Start

```bash
# 1. Authenticate (interactive — paste your GitHub PAT)
ab-hub auth login

# Check connection
ab-hub auth status

# 2. Discover & analyze repositories
ab-hub scan

# Optional: include vulnerability scan
ab-hub scan --security

# 3. List repositories
ab-hub list

# 4. Inspect a specific project
ab-hub inspect <repo-name>

# 5. Activity & security
ab-hub activity
ab-hub abandoned
ab-hub security overview

# 6. Export
ab-hub export --format json
```

Running `ab-hub` with no arguments shows a friendly home screen with status and quick commands.

## CLI Commands

| Command | Description |
|---------|-------------|
| `ab-hub auth login` | Store GitHub token securely |
| `ab-hub auth status` | Check authentication status |
| `ab-hub auth logout` | Remove stored credentials |
| `ab-hub scan` | Discover & analyze repositories |
| `ab-hub scan --incremental` | Only process changes |
| `ab-hub list` | List repositories (with filters) |
| `ab-hub inspect <name>` | Detailed repository inspection |
| `ab-hub commits <name>` | Commit history |
| `ab-hub technologies` | Technology overview |
| `ab-hub activity <name>` | Activity score & classification |
| `ab-hub abandoned` | List potentially abandoned projects |
| `ab-hub compare <a> <b>` | Compare two repositories |
| `ab-hub report` | Generate summary report |
| `ab-hub export --format json\|csv\|markdown` | Export data |

## Architecture

```
AB-hub CLI
    └── Application Core
            ├── Discovery Engine
            ├── Intelligence Engine (Tech / Commits / Activity)
            ├── Control Engine
            └── Data Repository (SQLite)
```

## Security

- Tokens are never stored in the database or printed in logs.
- Prefer system keyring when available.
- Read-only by design — never modifies remote repositories.
- Minimal required permissions.


## Security Monitoring

AB-hub can scan dependencies against the [OSV](https://osv.dev) database:

```bash
# During a normal scan
ab-hub scan --security

# Dedicated security pass
ab-hub security scan
ab-hub security scan my-repo
ab-hub security overview
ab-hub security list my-repo
```

Findings are stored locally and included in reports. Severity levels: CRITICAL, HIGH, MEDIUM, LOW.

## Development

```bash
# Lint & format
ruff check .
ruff format .

# Type checking
mypy ab_hub

# Tests
pytest
```

## Project Structure

See the full modular layout under `ab_hub/`.


## CI/CD

GitHub Actions workflows are included:

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| **CI** | push / PR to main | Ruff lint + format, mypy, pytest (3.12 & 3.13), CLI smoke |
| **Release** | tag `v*` | Build wheel/sdist, GitHub Release, optional PyPI publish |
| **CodeQL** | push / weekly | Security static analysis |
| **Dependabot** | weekly | Dependency & Actions updates |

### Local parity

```bash
make install-dev
make ci          # lint + tests + smoke
make build       # sdist + wheel
```

### Release flow

```bash
git tag v0.1.0
git push origin v0.1.0
```

For PyPI trusted publishing, configure the repository as a trusted publisher on PyPI (project `ab-hub`, environment `pypi`).

## License

MIT (to be confirmed)

---

**AB-hub — Know what you built. Control what you own.**
