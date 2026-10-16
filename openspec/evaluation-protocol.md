# Evaluation protocol (pre-registered) — v1
Purpose: decide, with your own ledger, which dealer features earn promotion. Committed to git BEFORE collecting evaluation data; any change = new version + new commit; the commit hash is quoted in every report.
Values marked [P] are recommendations; edit before the first commit, then freeze.

## Rules
1. Unit of analysis = alert; unit of inference = trading DAY (alerts on one day are one cluster; use eval_stats.day_cluster_bootstrap_diff).
2. Registered tests = the H-list below. Count is fixed per version; Holm correction across them (eval_stats.holm). No unregistered test may justify a promotion.
3. Baseline = flow-only: rank by `flow_strength` (zero_dte_cluster_snapshots) or the score without dealer terms (signals). Compare dealer-aligned vs unaligned within the SAME stratum: time-of-day bucket (±ZERO_DTE_PERCENTILE_BUCKET_S), IV tercile, event-tag set (tools/event_tags.py).
4. Develop/test split by time: first 2/3 of sessions may tune thresholds (LEVEL_THETA, percentiles); last 1/3 is untouched until the single final run. No re-tuning after looking.
5. Minimum sample before any verdict [P]: ≥ 60 sessions and ≥ 100 alerts per group. Below that the report says INSUFFICIENT, never a direction.
6. Costs: tradable claims use signal_outcomes returns net of modeled_slippage_cents (option package marks). 0DTE cluster outcomes are underlying-only research: report gross, label "not tradable evidence".
7. Directional sign: returns are direction-adjusted (d·(S_h−S_0)/S_0 as in SPEC V1 §2.20.8).
8. Promotion: a feature goes live (flag dealer_features_live per feature) only if its H passes after Holm on the held-out third AND the effect has the pre-registered sign. Demotion: rolling 60-session lower CI < 0 → flag off, automatically proposed in the weekly report.

## Hypotheses (v1: 6 tests)
| ID | Claim | Metric (horizon) | Compare | Pass |
|---|---|---|---|---|
| H1 | Flow alerts in NEGATIVE regime continue more than in POSITIVE | post_15m_return, post_30m_return (use the 30m as primary) | regime NEGATIVE vs POSITIVE, sign_fragile=0 only | diff>0, Holm-adjusted p<0.05 |
| H2 | Pin targets hold | target_hit_at within CLOSE | target role PIN vs other targets | hit-rate diff>0 |
| H3 | Dealer terms add value over flow alone | post_30m_return | top quintile by confluence_score vs top quintile by flow_strength | diff>0 |
| H4 | VannaAlign=1 improves outcomes | post_30m_return | VannaAlign=1 vs 0 | diff>0 |
| H5 | Hedge pressure agreeing with thesis improves T+1/1h outcomes | signals: ret_pct at 1h/1D net of slippage | sign(H_signed) agrees vs opposes | diff>0 |
| H6 | Result not an artifact of the dealer-sign assumption | H1 and H3 repeated | model A vs model B maps | same sign in both |
Primary horizon per H is the bold choice stated above; others are descriptive only.

## Report (weekly job, read-only)
Per H: n alerts/days per group, diff, 95% CI, raw and Holm p, verdict PASS | FAIL | INSUFFICIENT; coverage and sign_fragile rates; share of alerts per event tag; operator ratings (USEFUL share by regime); protocol commit hash; data window. Output file only; the report never changes a flag (operator does via quantctl).
