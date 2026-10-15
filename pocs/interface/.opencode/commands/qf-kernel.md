---
description: Implement pure kernels/domain/snapshot-builder (units + purity + TDD + types)
agent: qf-build
---
@.opencode/playbooks/08-quantflow-units-purity.md
@.opencode/playbooks/04-test-driven-development.md
@.opencode/playbooks/01-python-type-safety.md

Change / task scope: $ARGUMENTS

Run the OpenSpec apply workflow (see .opencode/commands/opsx-apply.md) for kernel/domain tasks only. Add an AST test forbidding I/O, clock, randomness and fetch_*/get_current_*/read_pointer_* in the touched modules. Coverage ≥95% on kernels/** and domain/**.
