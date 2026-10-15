# 080 Position exit handlers (AH)
Epic: E8 | Depends: 037 | Blockers: Stage 4
Use: /opsx-propose @openspec/prompts/080-position-exit-AH.md
Capabilities: route-exit-handlers
Sources: ARCH V4 §AH (binding over SPEC V3 §15.5)
Requirements:
1. Route-specific exits per ARCH V4 §AH; position_exit_events append-only.
2. Declared exit handler enables ACTIONABLE_NOW path.
Seed scenarios: no handler; handler change
Open questions (do not invent): AH parts unspecified
Out of scope: execution
