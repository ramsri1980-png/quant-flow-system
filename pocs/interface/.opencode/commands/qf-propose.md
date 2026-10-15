---
description: Propose a QuantFlow change from a feature brief (loads spec-authoring playbook only)
agent: qf-plan
---
Rules for this phase (read carefully, then follow):
@.opencode/playbooks/09-quantflow-spec-authoring.md

Constitution: @openspec/constitution.md
Open conflicts: @openspec/conflicts-and-gaps.md

Feature brief / request: $ARGUMENTS

Now run the OpenSpec propose workflow for this change (same steps as /opsx-propose: create the change, then proposal → specs → design → tasks). If you need the exact steps, run `openspec instructions proposal --help` or read .opencode/commands/opsx-propose.md. Stop after tasks and list BLOCKING open questions.
