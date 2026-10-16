---
description: Propose a QuantFlow change from a feature brief (loads spec-authoring playbook only)
agent: qf-plan
---
## Tool budget
- Use `read`, `grep`, and `glob` for all file exploration. Do not use shell (`find`, `cat`, `head`, `grep -r`) for this.
- Use `execute_and_capture` only to run programs that produce structured output (tests, build, linter). Not for reading or searching files.
- Before any shell call, ask: "Can `read`, `grep`, or `glob` answer this?" If yes, use those.
- Do not run more than 3 shell commands in a single reasoning step.
- Stop after tasks and list BLOCKING open questions. Do not explore the repository further than the brief requires.

Rules for this phase (read carefully, then follow):
@.opencode/playbooks/09-quantflow-spec-authoring.md

Constitution: @openspec/constitution.md
Existing modules (reuse first): @openspec/modules.md
Dealer/greeks formulas (only if the brief is 031/033/034/035/036): read openspec/formulas-dealer-greeks.md
Open conflicts: @openspec/conflicts-and-gaps.md

Feature brief / request: $ARGUMENTS

Now run the OpenSpec propose workflow for this change (same steps as /opsx-propose: create the change, then proposal → specs → design → tasks). If you need the exact steps, run `openspec instructions proposal --help` or read .opencode/commands/opsx-propose.md. Stop after tasks and list BLOCKING open questions.

## Hard rules (override anything above)
1. First action: `openspec list --json`. If a change for this brief already exists, STOP: do not read sources. Report its name and task count, then ask: audit or regenerate.
2. Shell is for `openspec` only. Use read/grep/glob for files, never sed/grep/ls via shell.
3. Read only files and sections named in the brief. Max 6 source reads. If a section is missing, record it as an open question instead of searching.
4. Check CLI flags with `openspec <cmd> --help` once; do not guess flags.
5. Write artifacts with the openspec scaffolding; do not hand-build templates.
6. Read source ranges with Code Mode `harness-tools.rip_file_lines`; native read limit 120 lines; grep head_limit 20 or less.
