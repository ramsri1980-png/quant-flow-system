# 033 Scoring, calibration, EV (updated, C12)
Epic: E3 | Depends: 030, 031 | Blockers: H.1/H.4-H.6, I.1-I.9 headings only; C12
Use: /opsx-propose @openspec/prompts/033-scoring-calibration-ev.md
Capabilities: scoring, calibrator, ev-lower-bound, dealer-confidence, hedge-penalty-shadow
Sources: ARCH V4 §H, §I, §D.21, §L.5; SPEC V3 §8.4; SPEC V6 F.3; formulas-dealer-greeks.md F4 (confidence), F6 (hedge pressure).
Requirements:
1. Thresholds apply to calibrated lower bounds (p_lower, EV_lower); MEDIUM/HIGH_CONFLUENCE are evidence grades, not probabilities; no calibrator → no ACTIONABLE_NOW.
2. Dealer confidence (replaces H.2): c = clip((R−R_min)/(R_full−R_min),0,1)·coverage_oi_share·max(0,1−age_s/STALE_REF_S), R=|NetGamma$|/Gross; R_min/R_full = 20th/80th percentile of trailing R per (ticker, lane), fallback 0.10/0.50 labelled.
3. Hedge pressure H per F6 (dealer-signed exposures; ΔS in percent points; charm excluded for 0DTE; H>0 = dealers buy). H_signed unavailable if ADV$ missing.
4. EV_lower −= HEDGE_PENALTY_DEFAULT·|H_signed| applies once (L.5) ONLY when feature flag dealer_features_live=true; default false = SHADOW: compute and log H, alignments, regime on every alert, no effect on grade/EV.
5. Promotion rule: feature goes live only after per-scope N outcomes (SPEC V6 F.3) show markout lift; otherwise delete it.
Seed scenarios: shadow vs live flag; ADV missing; opposite-sign H; stale map (c→0); no calibrator.
Open questions: BLOCKING H.1, H.4–H.6, I.1–I.9 unspecified; p_BE and SAFETY_MARGIN source; approve DEALER_R_PCTL_*, DEALER_STALE_TTL_MULT; ADV$ source for index options (propose front ES notional).
Out of scope: ML challenger (084), sizing.
