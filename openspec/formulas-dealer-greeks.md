# Dealer / greeks formulas — proposed corrections (C12)
Status: RECOMMENDED. Constants below are my recommendations (not in SPEC/ARCH). Running tools/apply_doc_patches.py writes them into ARCH V1 §AI.3 and ARCH V4 §D; that is the approval step. Edit the values in the script first if you disagree. Reference oracle: tools/greeks_reference.py (self-test passes vs finite differences).
Cadence: NO minute-by-minute recompute. Maps refresh on cache TTL (ARCH V1 §AI.6) or on an event (flow alert, spot/IV move). Every output carries map age; stale → context only.

## F1 Greeks kernel (pure; fixes: none of this exists in the docs)
Inputs per option: S, K, r, q (carry/dividend), σ (that option's own IV, sticky-strike), T. T = (expiry_ts − as_of_ts)/(365·86 400 000) calendar years.
- Guards: T ← max(T, DEALER_T_MIN_S=300 s; maps refresh no faster than 120–300 s, and last-5-minute 0DTE greeks are noise); σ ≤ GREEKS_SIGMA_MIN (0.01) or > GREEKS_SIGMA_MAX (5.0) or missing IV or T≤0 → option EXCLUDED and counted in coverage (never defaulted).
- d1 = [ln(S/K) + (r − q + σ²/2)T] / (σ√T); d2 = d1 − σ√T; n(x)=e^(−x²/2)/√2π; N = normal CDF.
- Delta: call e^(−qT)N(d1); put e^(−qT)(N(d1) − 1)
- Gamma = e^(−qT)·n(d1)/(S σ √T)            (n = pdf, never N)
- Vanna = ∂Δ/∂σ = −e^(−qT)·n(d1)·d2/σ        (d2, not d1; same for call and put)
- Charm = ∂Δ/∂t (calendar, = −∂Δ/∂T): core = −e^(−qT) n(d1)[2(r−q)T − d2σ√T]/(2Tσ√T); call = core + q e^(−qT)N(d1); put = core − q e^(−qT)N(−d1)
Sign checks (r=q=0, verified): gamma>0 always; vanna>0 when d2<0 (OTM call side), <0 when d2>0; charm: call ITM(d2>0) >0, OTM <0; put charm equals call charm. If you see the opposite, the sign is wrong.
Tests (fail CI): 10 spots × 5 vols × 4 tenors × call/put × (r,q=0 and r,q>0): analytic vs central finite difference (rel err < 1e-3 gamma, 1e-4 vanna/charm) AND vs py_vollib/QuantLib (<0.5%). Do not hand-encode sign rules from any review; the FD test decides.

## F2 Dollar exposures (unit contract; position = OI contracts, M = multiplier 100)
- Gamma$ per +1% spot  = Γ · S² · 0.01 · M · OI      (= Δ$ change when spot moves 1%)
- Vanna$ per +1 vol pt = Vanna · 0.01 · S · M · OI
- Charm$ per calendar day = (Charm_per_year/365) · S · M · OI
- Delta$ = Δ · S · M · OI
Raw gamma/OI without S² makes low-price OTM strikes dominate: forbidden. In code S is dollars (÷1e6 from _micros at the boundary).

## F3 Dealer sign (the central assumption — explicit, switchable)
Dealer exposure_i = s_i · exposure_i, where s_i = dealer position sign.
- Model A OI_NAIVE [P default]: dealer long calls (+1), short puts (−1). B SIGNED_FLOW: s_i = −(aggressor-signed customer flow) for the cluster's contracts, OI_NAIVE elsewhere. C PROVIDER: use provider's signed map as-is (labelled provider-estimated).
- Compute regime under two INDEPENDENT models (A vs B, or A vs C). sign_fragile = sign of NetGamma$ at spot differs between them → regime = UNINFORMATIVE. Separately, a TEST (not a runtime flag): negating s_i must not leave any decision unchanged-by-accident, i.e. report which decisions flip under negation (measures how much rests on the assumption).
- 0DTE: prior-day OI misses same-day positions → label map "provider-estimated/OI-stale"; never HIGH-grade on OI_NAIVE alone.

## F4 Regime, flip, confidence (detection)
1. NetGamma$(S) = Σ dealer Gamma$; Gross = Σ |dealer Gamma$|; R = |Net|/Gross ∈[0,1].
2. regime = POSITIVE if Net>0 (dealers sell rallies/buy dips: damping), NEGATIVE if Net<0 (amplifying), UNINFORMATIVE if R < R_min or sign_fragile. R_min = DEALER_R_PCTL_MIN (20th) percentile of trailing R for (ticker, lane) over ZERO_DTE_PERCENTILE_WINDOW_D sessions (needs ZERO_DTE_PERCENTILE_MIN_DAYS, else fallback 0.10 and label 'fallback'). Net/gross scale differs by underlying, so no single fixed number.
3. Coverage gate: OI-weighted share of options with valid greeks ≥ DEALER_COVERAGE_MIN (0.80, same as ZERO_DTE_MEDIUM_MIN_COVERAGE_PCT), else dealer map UNAVAILABLE. HIGH grade still needs coverage COMPLETE.
4. Flip (D.23): m_daily = IV/√252 (D.15; 0DTE: 0DTE ATM IV). Grid S'_j = S·(1+j·h), j=−20..+20 (FLIP_GRID_POINTS=41), h = FLIP_GRID_HALF_MULT(3)·m_daily/20 — scale-free, reuses D.15; reprice Γ at each S' with σ_i, T fixed; NetGamma$(S'). Flip = zero crossing nearest spot, linear interpolation between adjacent grid points of opposite sign; none in range → NO_FLIP. flip_distance_pct = (S_flip − S)/S.
5. Events (on refresh only): REGIME_CHANGE if sign(Net) differs from previous map; FLIP_DISAGREEMENT if |S_flip_own − S_flip_provider|/S > FLIP_TOL_MULT(0.25)·m_daily (feeds existing dealer-flip-disagreement research alert).
6. Dealer confidence (replaces H.2): c = clip((R − R_min)/(R_full − R_min),0,1) · coverage_oi_share · max(0, 1 − age_s/STALE_REF_S); R_full = 80th percentile (fallback 0.50); STALE_REF_S = ZERO_DTE_DEALER_MAP_STALE_MAX_S (0DTE) else DEALER_STALE_TTL_MULT(3)·lane dealer_ttl_s.

## F5 Levels and walls (D.24 gap fill, signed per strike K) [P]
- Net_K = Σ dealer Gamma$ at strike K; Call wall = argmax_{K≥S} unsigned call Gamma$; Put wall = argmax_{K≤S} unsigned put Gamma$.
- Role: local max of Net_K with Net_K ≥ θ·max|Net| (LEVEL_THETA 0.50): below spot−b → POSITIVE_GAMMA_SUPPORT, above spot+b → RESISTANCE, within ±b → PIN. Local min with Net_K ≤ −θ·max|Net| → NEGATIVE_GAMMA_ACCELERATOR. Contiguous strikes with |Net_K| < ε·max|Net| → LOW_EXPOSURE_AIR_POCKET. b = confirmation buffer from D.14c.

## F6 Hedge pressure H (corrects D.21) 
- Exposures must be DEALER-signed. ΔDelta$_dealer ≈ NetGamma$_per1pct·ΔS_pct + NetVanna$_per_volpt·ΔIV_pts + NetCharm$_per_day·Δt_days; H = −ΔDelta$_dealer (H>0 = dealers buy underlying). ΔS_pct is in percent points (1.0 = 1%), NOT a fraction.
- 0DTE: H = −(gamma term + vanna term); charm EXCLUDED (linear Δt invalid near expiry). ≥1DTE: charm term allowed. Charm alone = "expected drift" context for morning brief, not a trigger.
- Large scenario moves: full reprice (F4 grid) instead of the Taylor sum. H_signed = H/ADV$. ADV$ single names = avg daily dollar volume; index options = front ES notional ADV [P]; denominator unavailable → H unavailable (fail closed).
- Penalty EV_lower −= HEDGE_PENALTY·|H_signed| stays SHADOW-ONLY until outcomes show H predicts markouts.

## F7 Alignment (corrects D.14c) [P]
- GammaAlign (bullish; bearish mirrored), values stay {0, 0.5, 1}:
  regime UNINFORMATIVE/stale/unavailable → 0. NEGATIVE regime and no POSITIVE_GAMMA resistance between spot and target → 1. POSITIVE regime and target is the nearest PIN/resistance → 0.5. POSITIVE_GAMMA resistance sits between spot and target → 0. Support below spot is used for invalidation only, not alignment. (Removes the OR that scored pin-above and accelerator-above equally.)
- VannaAlign: ΔIV = ATM IV of the cluster's expiration now − at previous map refresh, measured with the cluster's own window excluded (breaks circularity); missing/misaligned timestamps → 0. H_V = −NetVanna$_per_volpt·ΔIV_pts. VannaAlign = 1 iff sign(H_V) matches direction AND |H_V|/ADV$ ≥ θ_V, θ_V = trailing 90th percentile of |H_V|/ADV$ for that lane (needs ≥ MIN_DAYS else 0). The fixed 0.10 (10% of ADV) is likely unreachable (my order-of-magnitude: net vanna$ per vol pt is ~0.1–1% of ADV$ for liquid names — verify with data).
- D_c = (GammaAlign + VannaAlign)/2 in the score (was max, which biases upward). "Confirmed" for HIGH (b) stays: either equals 1.

## F9 Schema decision (DuckDB 051 dealer_map_regime)
Why not "compute at read time": the ledger must answer "what was the regime when this alert fired" for markout tests, and per-strike exposures are not stored. Why not ALTER dealer_level_maps: it is append-only. Decision: new 1:1 append-only child table, DuckDB only (shadow research data, not decision-critical; if regime ever enters the decision path, add a SQLite copy). ID 051 is free (050 = proposed core repair; 046–049 stay reserved). DDL: migrations/duckdb/051_dealer_map_regime.sql (also inserted into SPEC V2 §19 by the patch script). Existing dealer_level_maps columns reused: quantflow_derived_gamma_flip, derived_flip_coverage, coverage, sign_convention. Map age = created_at − provider_as_of (derived, not stored).

## F8 Rollout order (cheapest first)
1 F1+F2 kernel + FD/oracle tests → 2 F3 sign switch + sign_fragile → 3 F4 regime/flip/coverage → 4 shadow-log F5–F7 features on every alert (no effect on grade/EV) → 5 after ≥ per-scope N outcomes, test markouts, then promote or delete each feature.
