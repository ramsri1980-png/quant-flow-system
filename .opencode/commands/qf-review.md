---
description: Review the current change against spec, units, purity and tests (read-only)
agent: qf-review
---
@.opencode/playbooks/05-code-review-and-quality.md
@.opencode/playbooks/06-doubt-driven-development.md

Scope: $ARGUMENTS (default: the change directory under openspec/changes/)


## How to review (no shell available)
- The `bash` tool is not available to this agent. Do not attempt to run `git diff`, `git status`, or any shell command.
- To see what changed, read these files directly with the `read` tool:
  - `openspec/changes/<change>/proposal.md`
  - `openspec/changes/<change>/design.md`
  - `openspec/changes/<change>/tasks.md`
  - every file listed in `tasks.md`
  - the relevant spec deltas under `openspec/changes/<change>/specs/`
- Compare the source files against the spec deltas. Cite file paths and line numbers in your findings.
- You must read at least one source file and one spec file before producing findings.
- Never output "BLOCKER: none. MAJOR: none." unless you have read the modified files. If you cannot find the change files, say so explicitly and list the paths you tried.

Output BLOCKER/MAJOR/MINOR list and a verdict; then say whether /opsx-verify and /opsx-archive can proceed.
