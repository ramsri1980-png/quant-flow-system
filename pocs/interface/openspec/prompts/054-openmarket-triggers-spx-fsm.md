# 054 Open-market triggers and SPX crossing FSM
Epic: E5 | Depends: 014, 011 | Blockers: C9
Use: /opsx-propose @openspec/prompts/054-openmarket-triggers-spx-fsm.md
Capabilities: market-open-trigger, spx-crossing-fsm
Sources: SPEC V2 §19.3 spx_crossing_state_history; ARCH V1
Requirements:
1. Explicit FSM states/transitions; cooldown and rearm persisted as BIGINT epoch ms.
2. Deterministic given Clock.
3. Restart restores state.
Seed scenarios: cooldown boundary; rearm; restart mid-cooldown
Open questions (do not invent): C9 column types; FSM state list from DDL/docs only
Out of scope: alert content
