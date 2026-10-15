---
description: Review the current change against spec, units, purity and tests (read-only)
agent: qf-review
---
@.opencode/playbooks/05-code-review-and-quality.md
@.opencode/playbooks/06-doubt-driven-development.md

Scope: $ARGUMENTS (default: current change / git diff)

Diff: !`git diff --stat HEAD`

Review the change per the playbook. Read the change's specs/ and the touched files. Do not edit code. Output BLOCKER/MAJOR/MINOR list and a verdict; then say whether /opsx-verify and /opsx-archive can proceed.
