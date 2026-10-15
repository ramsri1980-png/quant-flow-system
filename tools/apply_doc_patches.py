#!/usr/bin/env python3
"""Apply C12 dealer/greeks corrections to the SPEC/ARCH markdown volumes.
Usage: python3 apply_doc_patches.py --dir docs/reference/CURRENT [--dry-run]
Backs up each changed file to <file>.bak-c12, is idempotent (skips already-patched), and reports NOT FOUND
so you can edit by hand. Patches are marker-based (start line .. end line), no line numbers."""
import argparse, glob, os, re, shutil, sys

D21 = """D.21 Dealer Hedging Pressure (signed)   [C12: corrected]
  Exposures MUST be DEALER-signed (formulas-dealer-greeks.md F3). H > 0 means dealers BUY the underlying.
  dDelta_dealer_$ = NetGamma_$per1pct * dS_pct + NetVanna_$pervolpt * dIV_volpt + NetCharm_$perday * dt_days
  H_$ = -dDelta_dealer_$
  dS_pct is in PERCENT POINTS (1.0 = 1%), never a fraction.
  0DTE: the charm term is EXCLUDED (linear dt invalid near expiry). >=1DTE: charm term allowed.
  Large scenario moves: full reprice on the D.23 grid instead of the Taylor sum.
  H_signed    = H_$ / ADV_$   (index options: front ES notional ADV; ADV missing -> H unavailable)
  H_magnitude = |H_signed|
  If sign(H_signed) opposes thesis direction AND dealer_features_live = true:
    EV_lower -= HEDGE_PENALTY_DEFAULT * H_magnitude
  Default dealer_features_live = false (SHADOW: compute and log, no effect on grade or EV).
  Single application."""

GAMMA_ALIGN = """  GammaAlign in {0, 0.5, 1} is derived ONLY from the current session's dealer map regime and levels   [C12: replaced]
  (no price-derived input; price confirmation is P_c in D.14b). Bearish cluster mirrored.
    GammaAlign = 0   when regime is UNINFORMATIVE or UNAVAILABLE, or sign_fragile, or the map is stale beyond
                     ZERO_DTE_DEALER_MAP_FRESHNESS_S.
    GammaAlign = 1   when regime = NEGATIVE and no POSITIVE_GAMMA level (support/resistance/pin) lies
                     between spot and target.
    GammaAlign = 0.5 when regime = POSITIVE and the target IS the nearest PIN/POSITIVE_GAMMA_RESISTANCE
                     in the direction of travel (pull to pin, capped).
    GammaAlign = 0   when a POSITIVE_GAMMA level lies between spot and target (wall blocks), or otherwise.
  POSITIVE_GAMMA_SUPPORT below spot is used for invalidation only, not for alignment."""

VANNA_SENT = """  VannaAlign = 1 only when the sign of IV-movement-driven dealer hedge flow H_V (below) matches the
  flow direction, per the normalized rule below. IV-momentum only; no price reference."""

VANNA_BLOCK = """Vanna confirmation (normalized)   [C12: corrected]
  dIV_pts = ATM IV of the cluster's expiration now - ATM IV at the previous dealer-map refresh, measured with
  the cluster's own event window EXCLUDED (breaks flow->IV->vanna circularity). Missing or misaligned
  timestamps -> VannaAlign = 0.
  H_V = -(NetVanna_$pervolpt * dIV_pts)        (dealer-signed; H_V > 0 = dealers buy)
  H_V_ADV = H_V / ADV_dollar_window            (index options: front ES notional ADV)
  VannaAlign = 1 only when sign(H_V) matches flow direction AND |H_V_ADV| >= theta_V, where theta_V = trailing
  90th percentile of |H_V_ADV| for the lane (needs ZERO_DTE_PERCENTILE_MIN_DAYS sessions, else VannaAlign = 0).
  ZERO_DTE_VANNA_RELEVANCE_MIN (0.10 = 10% of ADV) is DEPRECATED: likely unreachable for liquid underlyings.
  Flat or missing IV -> VannaAlign = 0 (context-only)."""

DC = "  D_c = (GammaAlign + VannaAlign) / 2 in [0, 1].   [C12: was max(), which biases upward]"

H2 = """H.2 Dealer Confidence Function   [C12: replaced]
  R = |NetGamma_$| / Sum|Gamma_$|   (net-to-gross, in [0,1])
  R_min / R_full = DEALER_R_PCTL_MIN / DEALER_R_PCTL_FULL percentile of trailing R for (ticker, lane) over
  ZERO_DTE_PERCENTILE_WINDOW_D sessions; fewer than ZERO_DTE_PERCENTILE_MIN_DAYS -> DEALER_R_MIN_FALLBACK /
  DEALER_R_FULL_FALLBACK and the output is labelled "fallback".
  c = clip((R - R_min) / (R_full - R_min), 0, 1) * coverage_oi_share * max(0, 1 - age_s / STALE_REF_S)
  STALE_REF_S = ZERO_DTE_DEALER_MAP_STALE_MAX_S (0DTE) else DEALER_STALE_TTL_MULT * lane dealer_ttl_s.
  coverage_oi_share = OI-weighted share of options with valid greeks; < DEALER_COVERAGE_MIN -> dealer map UNAVAILABLE."""

D23 = """D.23 Derived Gamma Flip (Grid Repricing)
  m_daily = IV/sqrt(252) per D.15 (0DTE: IV of the 0DTE ATM). N = FLIP_GRID_POINTS (odd); half = (N-1)/2;
  h = FLIP_GRID_HALF_MULT * m_daily / half; grid S'_j = S*(1 + j*h), j = -half..+half.
  At each S'_j reprice gamma with each option's own sigma_i and T fixed;
  NetGamma_$(S') = sum over options of s_i * Gamma_i(S') * S'^2 * 0.01 * M * OI_i.
  Flip = zero crossing nearest spot, linear interpolation between adjacent grid points of opposite sign;
  none in range -> NO_FLIP. flip_distance_pct = (S_flip - S) / S.
  Computed on map refresh only. See D.26."""

D24 = """D.24 Call Wall / Put Wall
  Call wall = argmax over K >= S of unsigned call Gamma_$ at K; Put wall = argmax over K <= S of unsigned put Gamma_$.
  Signed level roles from Net_K = sum of dealer-signed Gamma_$ at strike K (see D.26.4)."""

D26 = """D.26 Greeks kernel, dealer sign and regime   [C12: new]
D.26.1 Inputs/guards. T = (expiry_ts - as_of_ts)/(365*86_400_000) calendar years; T = max(T, DEALER_T_MIN_S/(365*86_400)).
  sigma_i is the option's own IV; sigma_i <= GREEKS_SIGMA_MIN or > GREEKS_SIGMA_MAX, missing IV, T <= 0 or OI <= 0 -> option EXCLUDED
  (counted in coverage, never defaulted).
D.26.2 BSM with carry q: d1 = [ln(S/K) + (r - q + sigma^2/2)T] / (sigma*sqrt(T)); d2 = d1 - sigma*sqrt(T).
  Gamma = exp(-qT) * n(d1) / (S*sigma*sqrt(T))            (n = pdf)
  Vanna = dDelta/dsigma = -exp(-qT) * n(d1) * d2 / sigma   (same for call and put)
  Charm = dDelta/dt (calendar) = -dDelta/dT:
    core = -exp(-qT) * n(d1) * (2(r-q)T - d2*sigma*sqrt(T)) / (2*T*sigma*sqrt(T))
    call = core + q*exp(-qT)*N(d1);  put = core - q*exp(-qT)*N(-d1)
  Verified sign table (r=q=0): gamma > 0; vanna > 0 when d2 < 0; ITM call charm > 0, OTM call charm < 0; put charm = call charm.
  CI: analytic vs central finite difference and vs py_vollib/QuantLib (< 0.5%) on 10 spots x 5 vols x 4 tenors.
D.26.3 Dollar units (M = 100, OI in contracts, S in dollars):
  Gamma_$per1pct = Gamma * S^2 * 0.01 * M * OI;  Vanna_$pervolpt = Vanna * 0.01 * S * M * OI;
  Charm_$perday = (Charm/365) * S * M * OI;  Delta_$ = Delta * S * M * OI.
D.26.4 Dealer sign and regime. dealer exposure_i = s_i * exposure_i. Models: A OI_NAIVE (dealer long calls +1, short
  puts -1), B SIGNED_FLOW, C PROVIDER. Regime computed under two independent models; sign disagreement ->
  sign_fragile -> UNINFORMATIVE. R = |sum Gamma_$| / sum |Gamma_$|. regime = POSITIVE if net > 0, NEGATIVE if net < 0,
  UNINFORMATIVE if R < R_min (H.2), UNAVAILABLE if coverage < DEALER_COVERAGE_MIN. Levels: local max of Net_K >= LEVEL_THETA*max|Net_K|
  -> POSITIVE_GAMMA_SUPPORT (below spot-b) / PIN (within +-b) / RESISTANCE (above spot+b); local min <= -LEVEL_THETA*max|Net_K|
  -> NEGATIVE_GAMMA_ACCELERATOR; contiguous |Net_K| < LEVEL_EPS*max|Net_K| -> LOW_EXPOSURE_AIR_POCKET.
D.26.5 Cadence. No minute-by-minute recompute: refresh on cache TTL or event; every output carries map age.
  Events on refresh only: REGIME_CHANGE (sign(Net) changed), FLIP_DISAGREEMENT (|own - provider flip|/S > FLIP_TOL_MULT*m_daily).
  0DTE maps built on prior-day OI are labelled provider-estimated/OI-stale; never HIGH on model A alone.
"""

CONSTS = """  # --- C12 dealer/greeks constants [RECOMMENDED values; running the patch script = approval] ---
  DEALER_T_MIN_S                      300
  GREEKS_SIGMA_MIN                    0.01
  GREEKS_SIGMA_MAX                    5.00
  DEALER_COVERAGE_MIN                 0.80
  DEALER_R_PCTL_MIN                   20     # R_min = this percentile of trailing net/gross R, (ticker, lane)
  DEALER_R_PCTL_FULL                  80     # R_full = this percentile; window/min-days reuse ZERO_DTE_PERCENTILE_*
  DEALER_R_MIN_FALLBACK               0.10   # only until MIN_DAYS history exists; output labelled "fallback"
  DEALER_R_FULL_FALLBACK              0.50
  DEALER_STALE_TTL_MULT               3      # non-0DTE stale ref = this * lane dealer_ttl_s; 0DTE uses ZERO_DTE_DEALER_MAP_STALE_MAX_S
  FLIP_GRID_HALF_MULT                 3      # grid half-width = this * m_daily (ARCH V4 D.15)
  FLIP_GRID_POINTS                    41
  FLIP_TOL_MULT                       0.25   # FLIP_TOL = this * m_daily
  LEVEL_THETA                         0.50
  LEVEL_EPS                           0.10
  VANNA_THETA_PCTL                    90"""

def span(text, start, end):
    i = text.find(start)
    if i < 0: return None
    j = text.find(end, i)
    return None if j < 0 else (i, j + len(end))

def block(text, start, end, new, tag):
    if tag in text: return text, "already"
    s = span(text, start, end)
    if not s: return text, "NOT FOUND"
    return text[:s[0]] + new + text[s[1]:], "ok"

def line(text, old, new, tag):
    if tag in text: return text, "already"
    if old not in text: return text, "NOT FOUND"
    return text.replace(old, new, 1), "ok"

def patch_v4(t):
    # sequential application (each patch sees the previous result)
    r = []
    for name, fn in [
        ("D.21", lambda x: block(x, "D.21 Dealer Hedging Pressure (signed)", "  Single application.", D21, "[C12: corrected]")),
        ("GammaAlign", lambda x: block(x, "  GammaAlign = 1 when a fresh, unexpired dealer-map level", "  stale beyond ZERO_DTE_DEALER_MAP_FRESHNESS_S.", GAMMA_ALIGN, "[C12: replaced]")),
        ("VannaAlign sentence", lambda x: block(x, "  VannaAlign = 1 only when the sign of IV-movement-driven", "  direction. IV-momentum only; no price reference.", VANNA_SENT, "per the normalized rule below")),
        ("Vanna block", lambda x: block(x, "Vanna confirmation (normalized):", "  Flat or missing IV → VannaAlign = 0 (context-only).", VANNA_BLOCK, "[C12: corrected]\n  dIV_pts")),
        ("D_c", lambda x: line(x, "  D_c = max(GammaAlign, VannaAlign) in [0, 1].", DC, "was max(), which biases")),
        ("H.2", lambda x: block(x, "H.2 Dealer Confidence Function", "  c *= max(0.3, 1.0 − greeks_age_hours / 24.0)", H2, "H.2 Dealer Confidence Function   [C12")),
        ("D.23", lambda x: line(x, "D.23 Derived Gamma Flip (Grid Repricing)", D23, "Flip = zero crossing nearest spot")),
        ("D.24", lambda x: line(x, "D.24 Call Wall / Put Wall", D24, "Signed level roles from Net_K")),
        ("D.26 (new section)", lambda x: line(x, "D.25 FDI (Delta-Weighted)", D26 + "\nD.25 FDI (Delta-Weighted)", "D.26 Greeks kernel, dealer sign")),
    ]:
        t, st = fn(t); r.append((name, st))
    return t, r

def patch_v1_arch(t):
    r = []
    if "C12 dealer/greeks constants" in t: r.append(("AI.3 constants", "already"))
    else:
        m = re.search(r"^( *MIN_VEGA +0\.005)$", t, re.M)
        if m: t = t[:m.end()] + "\n" + CONSTS + t[m.end():]; r.append(("AI.3 constants", "ok"))
        else: r.append(("AI.3 constants", "NOT FOUND"))
    if "DEPRECATED (C12)" in t: r.append(("vanna const", "already"))
    else:
        m = re.search(r"^( *ZERO_DTE_VANNA_RELEVANCE_MIN +0\.10)$", t, re.M)
        if m: t = t[:m.end()] + "   # DEPRECATED (C12): replaced by VANNA_THETA_PCTL rule, ARCH V4 D.14c"+ t[m.end():]; r.append(("vanna const", "ok"))
        else: r.append(("vanna const", "NOT FOUND"))
    t, st = line(t, "  Dealer exposure:            per signed fixture",
        "  Dealer exposure:            dealer-signed per explicit model (OI_NAIVE | SIGNED_FLOW | PROVIDER), ARCH V4 D.26.4", "explicit model (OI_NAIVE"); r.append(("AI.18 sign", st))
    return t, r

def patch_v1_spec(t):
    r = []
    t, st = line(t, "  Dealer exposure per signed fixture.",
        "  Dealer exposure is dealer-signed by an explicit model (OI_NAIVE | SIGNED_FLOW | PROVIDER); see ARCH Vol 4 §D.26.4.\n  Gamma_$ per +1% = Gamma*S^2*0.01*M*OI; Vanna_$ per vol pt = Vanna*0.01*S*M*OI; Charm_$ per day = Charm/365*S*M*OI.",
        "explicit model (OI_NAIVE"); r.append(("22.2 sign", st))
    t, st = line(t, "              ZERO_DTE_HIGH_CONFLUENCE_MIN (0.80).",
        "              ZERO_DTE_HIGH_CONFLUENCE_MIN (0.80).\n          (e) Dealer regime is POSITIVE or NEGATIVE (not UNINFORMATIVE/UNAVAILABLE, not sign_fragile) and the map is\n              not built on model A alone for 0DTE (ARCH Vol 4 §D.26.4).  [C12]", "[C12]"); r.append(("2.20.7.4 (e)", st))
    return t, r

DDL = """CREATE TABLE dealer_map_regime (
    dealer_map_id TEXT PRIMARY KEY REFERENCES dealer_level_maps(dealer_map_id),
    sign_model_primary TEXT NOT NULL CHECK(sign_model_primary IN ('OI_NAIVE','SIGNED_FLOW','PROVIDER')),
    sign_model_secondary TEXT CHECK(sign_model_secondary IN ('OI_NAIVE','SIGNED_FLOW','PROVIDER')),
    map_basis TEXT NOT NULL CHECK(map_basis IN ('OI_PRIOR_DAY','PROVIDER_INTRADAY')),
    regime TEXT NOT NULL CHECK(regime IN ('POSITIVE','NEGATIVE','UNINFORMATIVE','UNAVAILABLE')),
    sign_fragile INTEGER NOT NULL CHECK(sign_fragile IN (0,1)),
    net_gamma_usd_per1pct DOUBLE, gross_gamma_usd_per1pct DOUBLE, net_gross_ratio DOUBLE,
    net_vanna_usd_per_volpt DOUBLE, net_charm_usd_per_day DOUBLE,
    coverage_oi_share DOUBLE,
    r_min_used DOUBLE,
    r_threshold_source TEXT CHECK(r_threshold_source IN ('PERCENTILE','FALLBACK')),
    kernel_version TEXT NOT NULL, constants_hash TEXT NOT NULL,
    created_at BIGINT NOT NULL
);
CREATE INDEX idx_dealer_map_regime_regime ON dealer_map_regime(regime, created_at);
"""

def patch_spec_v2(t):
    r = []
    if "CREATE TABLE dealer_map_regime" in t: r.append(("DDL dealer_map_regime", "already"))
    else:
        i = t.find("CREATE TABLE dealer_level_maps (")
        j = t.find("\n);\n", i) if i >= 0 else -1
        if j < 0: r.append(("DDL dealer_map_regime", "NOT FOUND"))
        else:
            k = j + len("\n);\n")
            t = t[:k] + "\n-- dealer_map_regime (DuckDB 051, PROPOSED CORE; C12; 1:1 child of dealer_level_maps, append-only)\n" + DDL + t[k:]
            r.append(("DDL dealer_map_regime", "ok"))
    t, st = line(t, "market_map_snapshots and dealer_level_maps append-only.",
                 "market_map_snapshots, dealer_level_maps and dealer_map_regime append-only.", "dealer_map_regime append-only"); r.append(("append-only list", st))
    return t, r

def patch_arch_v2(t):
    r = []
    t, st = line(t, "        -- Depends on core 040 and 042, NOT on research 043-045.",
        "        -- Depends on core 040 and 042, NOT on research 043-045.\n    051_dealer_map_regime.sql            (PROPOSED CORE, C12)\n        -- dealer_map_regime: 1:1 append-only child of dealer_level_maps (regime, net/gross, sign_fragile).\n        -- Depends on baseline dealer_level_maps only; NOT on 050 or research 043-045.", "051_dealer_map_regime.sql"); r.append(("migration list 051", st))
    t, st = line(t, "DuckDB 042 then 050. Reserved", "DuckDB 042, 050, then 051. Reserved", "042, 050, then 051"); r.append(("fresh order", st))
    return t, r

TARGETS = [("Vol2_Data_Canonical", patch_spec_v2), ("ARCH.*Vol2_DataModel", patch_arch_v2), ("Vol4_Services", patch_v4), ("ARCH*Vol1_Foundation", patch_v1_arch), ("SPEC*Vol1_Foundations", patch_v1_spec)]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dir", required=True); ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(); bad = 0
    for pat, fn in TARGETS:
        files = [f for f in glob.glob(os.path.join(a.dir, "*.md")) if re.search(pat.replace("*", ".*"), os.path.basename(f))]
        if not files: print(f"!! no file matches {pat} in {a.dir}"); bad += 1; continue
        for f in files:
            old = open(f, encoding="utf-8").read(); new, res = fn(old)
            print(os.path.basename(f))
            for n, s in res: print(f"   {s:9s} {n}"); bad += s == "NOT FOUND"
            if new != old and not a.dry_run:
                shutil.copy(f, f + ".bak-c12"); open(f, "w", encoding="utf-8").write(new); print("   written (backup .bak-c12)")
    print("\nNEXT (manual): write migrations/duckdb/051_dealer_map_regime.sql (copy of the DDL), add it to the migration manifest"
          "\n  (store=duckdb, id=051, component=CORE, enabled), re-run the SPEC V2 vs ARCH V2 parity hash test.")
    sys.exit(1 if bad else 0)

if __name__ == "__main__": main()
