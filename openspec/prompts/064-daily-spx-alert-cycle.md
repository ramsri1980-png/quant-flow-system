# 064 Daily SPX alert cycle
Epic: E6 | Depends: 054, 060 | Blockers: C11
Use: /opsx-propose @openspec/prompts/064-daily-spx-alert-cycle.md
Capabilities: spx-daily-cycle
Sources: SPEC V1; ARCH V4; ARCH V3 §F
Requirements:
1. Cycle driven by 054 FSM and scheduler.
2. Timing variation (jitter) only if ADR-001 interpretation A allows.
Seed scenarios: missed trigger; restart
Open questions (do not invent): C11 jitter
Out of scope: capture mechanics
