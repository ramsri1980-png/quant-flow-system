---
description: Stress-test one design/formula/fix decision (short)
agent: qf-doubt
---

@.opencode/playbooks/06-doubt-driven-development.md

Decision to examine: $ARGUMENTS

## Discipline for this command

- **Answer from the playbook and the cited rules first.** Do not explore.
- Only call a tool if you must quote a specific line from a source file.
- Hard cap: **2 tool calls total**. Prefer 0.
- Do not run `get_repo_skeleton`, `execute_and_capture`, or any directory listing.
- If the answer is complete from the playbook + AGENTS.md + constitution.md, answer directly.
