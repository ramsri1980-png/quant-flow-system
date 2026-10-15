---
description: Implement a change with TDD + typing + errors + style playbooks
agent: qf-build
---
Playbooks for this phase:
@.opencode/playbooks/04-test-driven-development.md
@.opencode/playbooks/01-python-type-safety.md
@.opencode/playbooks/02-python-error-handling.md
@.opencode/playbooks/03-python-code-style.md

Existing modules (reuse first): @openspec/modules.md

Change / task scope: $ARGUMENTS

Run the OpenSpec apply workflow (as /opsx-apply; steps in .opencode/commands/opsx-apply.md): read tasks.md, do the next unchecked task group using the playbooks, check it off, run ruff + mypy --strict + pytest for touched code. Refuse to start if a BLOCKING open question is unresolved.
