# 014 Scheduler and rate budgets
Epic: E1 | Depends: 005, 011 | Blockers: C11 for jitter semantics
Use: /opsx-propose @openspec/prompts/014-scheduler-rate-budgets.md
Capabilities: job-scheduler, rate-budget, session-limits
Sources: ARCH V1 (scheduler, human_rhythm_scheduler), ARCH V3 §F (limits); SPEC V1 §4.1.
Requirements:
1. Deterministic scheduler driven by injected Clock; missed-run policy explicit.
2. Per-provider rate budgets and sequential access per provider; pacing floor and session cap by named constants.
3. Budget exhaustion → defer, never burst.
4. Scheduler state persisted for restart.
Seed scenarios: clock jump; missed run after restart; budget exhausted; two jobs same provider.
Open questions: whether jitter in schedules is allowed (ADR-001, C11); constants not in §AI.3.
Out of scope: capture worker internals.
