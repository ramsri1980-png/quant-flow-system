# 060 Flow alert workflow
Epic: E6 | Depends: 037, 040, 042 | Blockers: RQ-002, RQ-005
Use: /opsx-propose @openspec/prompts/060-flow-alert-workflow.md
Capabilities: flow-alert-workflow
Sources: SPEC V1 §1.3 workflows; ARCH V4 workflows
Requirements:
1. Alert → thesis → snapshot → market map → decision → delivery.
2. Renderer cannot upgrade decision.
3. No executable recommendation without live quote.
Seed scenarios: stale quote; DQ fail; duplicate alert
Open questions (do not invent): RQ-002/005 outcomes
Out of scope: orders
