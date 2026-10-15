# 034 Dealer kernels (rewritten, C12)
Epic: E3 | Depends: 031 | Blockers: C12 approval; D.17-D.20 still heading-only
Use: /opsx-propose @openspec/prompts/034-dealer-hedging-kernels.md
Capabilities: dealer-sign-model, net-exposure, regime, gamma-flip-grid, levels-walls, vanna-charm-context
Sources: formulas-dealer-greeks.md F3–F6 (PROPOSED); ARCH V4 §D.15, D.16, D.21, D.23, D.24; SPEC V1 §2.11A; reference oracle tools/dealer_reference.py.
Requirements:
1. Dealer sign is an explicit parameter: model A OI_NAIVE (calls +1, puts −1 dealer), B SIGNED_FLOW, C PROVIDER; regime computed under two independent models; sign disagreement → sign_fragile → regime UNINFORMATIVE.
2. Net/Gross: R=|ΣGamma$|/Σ|Gamma$|; regime POSITIVE/NEGATIVE/UNINFORMATIVE (R<R_min, percentile per ticker/lane, fallback 0.10)/UNAVAILABLE (OI-coverage<DEALER_COVERAGE_MIN).
3. Flip (D.23): grid of FLIP_GRID_POINTS (41) spanning ±FLIP_GRID_HALF_MULT·m_daily (m_daily=IV/√252, D.15), reprice Γ at S' with σ_i,T fixed, zero crossing nearest spot by linear interpolation; none → NO_FLIP; flip_distance_pct=(S_flip−S)/S.
4. Levels/walls (D.24) per F5: signed per-strike net; roles PIN/SUPPORT/RESISTANCE/ACCELERATOR/AIR_POCKET with LEVEL_THETA, LEVEL_EPS, buffer b from D.14c; call/put wall = argmax unsigned Gamma$ above/below spot.
5. Events on refresh only (no minute-by-minute): REGIME_CHANGE, FLIP_DISAGREEMENT vs provider flip (FLIP_TOL_MULT·m_daily).
6. Persist regime per map in NEW append-only child table dealer_map_regime (DuckDB 051, 1:1 with dealer_level_maps; DDL in migrations/duckdb/051_dealer_map_regime.sql): sign models, map_basis (OI_PRIOR_DAY|PROVIDER_INTRADAY), regime, sign_fragile, net/gross gamma, net vanna/charm, coverage, r_min_used + source, kernel_version, constants_hash.
7. Charm = context only (morning brief, ≥1DTE); never in 0DTE pressure.
Seed scenarios: all-calls chain; R below R_MIN; models disagree; no zero crossing; flip exactly at a grid point; stale map; IV missing for large OI.
Open questions: BLOCKING approve F3–F5 constants (recommended values in ARCH V1 §AI.3 block); D.17 relevance, D.18 netting (cluster's own contribution), D.19 flip alignment, D.20 persistence still unspecified — draft or defer; provider schema for model C.
Schema decision (recommended, formulas F9): DuckDB 051 dealer_map_regime, component CORE, no dependency on 050; reuse existing quantflow_derived_gamma_flip / derived_flip_coverage columns for the flip. NON-BLOCKING once the operator accepts; coordinate with feature 010 manifest and the SPEC V2 vs ARCH V2 parity test.
Out of scope: alignment scoring (036), alerts, minute-level recomputation.
