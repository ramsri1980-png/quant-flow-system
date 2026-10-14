# ADR-003 — Python version

Status: Accepted
Date: 2026-10-13

## Context
The master runbook originally said Python 3.12. Python 3.14 is
the current stable release. No dependency in the frozen
SPEC/ARCH bundle binds the project to 3.12 specifically.

## Decision
Python 3.14 for all machines. Pinned in three places:
- `pyproject.toml`: `requires-python = ">=3.14"`
- `.python-version`: `3.14`
- tool configs: `ruff target-version = "py314"`,
  `mypy python_version = "3.14"`

## Consequences
- A Python version bump requires updating all three plus a full
  acceptance run.
- No downstream SPEC change is required; the version was a
  project convention, not a spec invariant.
