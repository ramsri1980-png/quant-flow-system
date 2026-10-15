# 033 Scoring, calibration, EV
Epic: E3 | Depends: 030, 031 | Blockers: H.1/H.4-H.6, I.5/I.8 gaps
Use: /opsx-propose @openspec/prompts/033-scoring-calibration-ev.md
Capabilities: scoring, calibrator, ev-lower-bound
Sources: ARCH V4 §H, §I; SPEC V3 §8.4; SPEC V6 (ML boundary)
Requirements:
1. Thresholds apply to calibrated lower bounds (p_lower, EV_lower), not raw scores.
2. MEDIUM/HIGH_CONFLUENCE are evidence grades, not probabilities.
3. No calibrator → no ACTIONABLE_NOW.
4. Versioned and auditable output.
Seed scenarios: no calibrator; p_lower at threshold; EV_lower ≤ 0; version change
Open questions (do not invent): BLOCKING H.1, H.4–H.6, I.1–I.9 mostly headings; p_BE and SAFETY_MARGIN source
Out of scope: ML challenger (084)
