# 064 Daily SPX alert cycle

Epic: E6 | Depends: 054, 060 | Blockers: none after 054
Use: /qf-propose @openspec/prompts/064-daily-spx-alert-cycle.md
Capabilities: spx-daily-cycle
Sources: SPEC V1 §2.15, §2.16, §2.20; SPEC V4 §18.19; ARCH V3 §E.0, §F.K.1; ARCH V4 §O.1–O.10; ARCH V1 §AI.16

Requirements:
1. Cycle driven by 054 FSM and scheduler (§AI.16).
2. Pre-market setup window: run_at sampled from Gaussian(μ=06:45 ET, σ=15 min) constrained to [06:00, 07:00] via the truncated-sampling primitive (§E.0). Not a fixed time.
3. Post-close cleanup window: run_at sampled from Gaussian(μ=16:45 ET, σ=15 min) constrained to [16:30, 17:30] via the truncated-sampling primitive (§E.0).
4. Active-hours exemption (§AI.16): the OpenMarket cycle runs outside the 07:00–16:00 ET flow-capture pacing window.
5. Newsletter timeout clock: 900 s from ~06:00 ET publication; hard cutoff 06:15 ET; fail closed (skip the day, one daily notification).
6. Verification window: opens at setup_completed_at, closes at 07:30 ET. Cleanup deadline 17:30 ET.
7. Max 4 SPX alerts/day (2 upside + 2 downside, one may be a flip designation).
8. Behavioral reference: pre-market setup and post-close cleanup recorded in `behavioral_reference` as `reference_type = 'operator_routine'` per §F.K.1.
9. Half-days use the calendar's actual close; holidays produce no cycle row.

Seed scenarios: missed trigger; restart mid-cycle; newsletter late (skipped day); half-day; holiday; jitter distribution boundary-mass.

Open questions (do not invent): none.

Out of scope: capture mechanics, alert content interpretation.
