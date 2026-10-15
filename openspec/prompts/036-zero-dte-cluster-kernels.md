# 036 0DTE cluster kernels (updated, C12)
Epic: E3 | Depends: 031, 034, 035 | Blockers: C12 approval
Use: /opsx-propose @openspec/prompts/036-zero-dte-cluster-kernels.md
Capabilities: cluster-grade, cluster-state, episode-state, gamma-align, vanna-align, confluence-score
Sources: SPEC V1 §2.20.7; ARCH V4 §D.14b–D.14d; formulas-dealer-greeks.md F7 (PROPOSED); SPEC V2 §19 (cluster snapshots).
Requirements:
1. Research-only: no route, size, ACTIONABLE_NOW. cluster_grade/cluster_state/episode_state disjoint; BASIC is a grade only; zero_dte_cluster_snapshots append-only.
2. GammaAlign ∈{0,0.5,1} per F7: 0 if regime UNINFORMATIVE/UNAVAILABLE/stale; NEGATIVE regime and no positive-gamma level between spot and target → 1; POSITIVE regime and target = nearest pin/resistance → 0.5; positive-gamma level between spot and target → 0. Support below spot feeds invalidation only.
3. VannaAlign per F7: ΔIV = ATM IV now − previous map refresh excluding the cluster window; θ_V = trailing 90th percentile of |H_V|/ADV$ (needs ZERO_DTE_PERCENTILE_MIN_DAYS else 0). Replaces fixed ZERO_DTE_VANNA_RELEVANCE_MIN.
4. D_c = (GammaAlign+VannaAlign)/2 in ConfluenceScore; HIGH gate (b) "confirmed" stays: either alignment = 1. Separation rule kept: price moves cannot change either alignment.
5. HIGH requires: fresh same-expiration map (≤ZERO_DTE_DEALER_MAP_FRESHNESS_S), coverage COMPLETE, not sign_fragile, not OI_NAIVE-only for 0DTE.
6. Shadow mode: alignments logged on all clusters even when feature flag off.
Seed scenarios: pin-above vs accelerator-above (different scores); regime flips between refreshes; ΔIV missing; stale map; cluster own flow excluded from ΔIV.
Open questions: BLOCKING approve F7 and θ_V rule; confluence weights 0.65/0.25/0.10 unfitted — keep, refit later from ledger.
Out of scope: trading decisions, minute-by-minute map refresh.
