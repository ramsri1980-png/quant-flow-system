# QUANT FLOW SYSTEM — TECHNICAL ARCHITECTURE v5.1.5.1
## VOLUME 4 — FORMULAS, SERVICES, WORKFLOWS

Status: self-contained for the sections this volume owns.
Sections not owned by this volume reference the owning
volume within the 10-file set by section number.

CHANGES FROM v5.1.5
- P0-1: §S.6 pseudo-code rewritten with separate signal_valid
  predicate; portfolio/market/entry evaluated after
  validation.
- P0-3: §D.14a and §D.14d use lifecycle-only cluster_state
  and deterministic episode_id (no |seq=N fallback).
- P0-5: §D.14c notes that all level comparisons are in
  _mills; spots remain in _micros.
- AH expanded in place: full route-specific exit contract
  (AH.0–AH.6). AH becomes operationally binding at Stage 4
  (Forward Paper). §AE/§AF/§AG now point to
  SPEC v2.0.5.1 Vol 7.

CHANGES FROM THIS REVIEW (A4-01 through A4-08)
- A4-01: D.5 rewritten as "Contractual Payoff Risk and
  Separate Scenario Grid"; exact endpoint/tail risk is
  authoritative, the finite grid is diagnostic only.
- A4-02: D.6 sizing uses exact contractual risk plus a
  separately declared cost allowance; no scenario extrema.
- A4-03: AH.3.1 replaced with durable theta intervals,
  fixed-point microcents accumulation, atomic SQLite
  transaction, and mid-gap rules.
- A4-04: AH.4.4 replaced with authoritative broker fill
  identity, ratio-normalized paper depth cap with
  persistent_idempotency reservation, and orphan rules.
- A4-05: AH.5.3 and AH.5.4 replaced with absolute UTC
  deadline bounds and clean separation of horizon clocks;
  AH.5.5 trigger priority renumbered with GAP added and
  first_trigger_at ordering.
- A4-06: AH.6.1–AH.6.4 replaced with the SQLite-first
  operational state, transaction scope, DuckDB mirror
  contract, and category mapping, without cross-engine
  transaction assumptions.
- A4-07: authority pointer to §15.5 corrected to SPEC Vol 3.
- A4-08: AH.6.6 rewritten to name proposed core repair
  migrations 071 (SQLite) and 050 (DuckDB) without
  touching applied 070/042.

CHANGES FROM v5.1.4
- §D.6 lane-parameterized sizing; TACTICAL_2DTE uses
  0.005.
- §D.14b package delta sums over legs; opposing share
  defined.
- §D.14c GammaAlign structural only; bullish rule corrected;
  vanna normalized by ADV window.
- §D.14d aligned with grade/state/episode split.
- §D.14e outcomes per alert grade.
- §S.6 aligned with SPEC Vol 3 §8.4 and §8.1a.
- §AA.2 lane property table unchanged in field names.
- §Z.1 category table unchanged.

CONTENTS
  D  Formulas & Worked Examples
  G  Notification & Email Delivery
  H  Confidence Propagation
  I  Calibration & Walk-Forward
  J  Spread Detection
  K  T+1 OI
  L  Sizing & Portfolio Risk
  O  Daily SPX Alert Cycle
  P  LivePriceProviderAdapter
  Q  Escalation Logic
  R  SymbolThesisService
  S  AnalysisSnapshotBuilder
  T  ProviderQueryPlanner
  U  DealerContextCache
  V  Morning Workflow
  W  Ad Hoc Workflow
  X  Thesis Merge/Split
  Y  Thesis-Ledger Reconciliation
  Z  Notification Mapping
  AA DTE Lanes
  AB MarketMapService + DealerLevelMapService + TechnicalLevelService
  AC ListedOptionQuoteAdapter
  AD SPX Crossing State Machine
  AE Closing FDI
  AF CFTC COT Ingestion
  AG Leveraged ETF Pressure
  AH Route-Specific Exits

================================================================================
D. FORMULAS & WORKED EXAMPLES
================================================================================

D.1 Per-Dimension Adjusted Score
  S_adjusted = Σ_i (raw_i × conf_i × cov_i) − penalties_i
  cov_i is the coverage cap per D.1a.

D.1a Coverage Cap Placement
  cov_i = 1.00 COMPLETE / 0.70 PARTIAL / 0.50 MANUAL_ONLY /
          0.00 UNKNOWN. Applied inside the weighted sum.

D.2 Global Confidence
  C_global = exp( Σ_i w_i ln(max(c_i, ε)) / Σ_i w_i )
  C_final  = min(C_global, C_coverage, C_DQ). Display-only.

D.3 Delta-Gamma-Theta-IV Decomposition

  Unit contract (declared, never inferred):

    option_price_dollars = option_price_cents / 100
    delta_spot_dollars   = delta_spot_micros / 1,000,000

    Delta:
      option dollars per $1 underlying move

    Gamma:
      option dollars per ($1 underlying move)^2

    Theta:
      option dollars per calendar day

    dt_days:
      elapsed calendar days, including fractional day

    Vega:
      option dollars per one volatility point

    delta_iv_vol_points:
      change in volatility points

  Δσ_impl,volpt = (
      ΔP$ − Δ·ΔS$ − ½·Γ·(ΔS$)² − Θ$/day · Δt_days
    ) / V$/volpt

  demand  = Δσ_impl − Δσ_surface
  MIN_VEGA = 0.005.

D.4 Opening and Closing Evidence
  vol_oi = print_volume / max(prior_oi, 1)
  opening_evidence_score = clip(
      0.45·min(vol_oi, 1)
    + 0.25·max(0, aggr)
    + 0.20·(mid_persist_5m > 0 ? 1 : 0)
    + 0.10·(premium_rising ? 1 : 0), 0, 1)

D.5 Contractual Payoff Risk and Separate Scenario Grid

  Authority: this section repairs contractual sizing. The finite
  scenario grid is not a proof of maximum loss or maximum profit.

  Supported exact-risk domain:
    Standard vanilla options on one nonnegative underlying, with
    the same expiration, settlement basis and verified deliverable.
    Route activation remains restricted by AH.1.2. Recognizing a
    structure does not enable its route. Calendar/diagonal,
    adjusted/nonstandard deliverable and unsupported packages
    return UNAVAILABLE until an exact route-specific risk model exists.

  Inputs for ONE package:
    signed integer leg ratio n_i (>0 long, <0 short);
    multiplier M_i > 0; right_i in {CALL, PUT};
    strike_mills_i; signed entry_cash_cents (credit positive,
    debit negative), already including every leg multiplier ONCE.
    Entry fees are excluded here and supplied separately as costs.

  Work in exact Decimal/rational values; never binary float for
  contractual cash risk. Let x be a hypothetical underlying price
  in mills, not an observed spot:
    intrinsic_mills_i(x) = max(x - K_i, 0) for a call,
                           max(K_i - x, 0) for a put.
    pnl_cents_exact(x) = entry_cash_cents
                        + SUM_i(n_i * M_i * intrinsic_mills_i(x) / 10).

  Because this terminal payoff is piecewise linear, evaluate it
  analytically at x=0 and every distinct leg strike. Let
    upper_tail_slope = SUM_call_legs(n_i * M_i).
  If upper_tail_slope < 0: maximum loss is UNBOUNDED; do not size.
  Otherwise:
    max_risk_per_package_cents = ceil(max(0, -min(endpoint_pnls))).
  If upper_tail_slope > 0: maximum profit is UNBOUNDED; encode
    max_profit_per_package_cents=NULL and profit_unbounded=true.
  Otherwise:
    max_profit_per_package_cents = floor(max(0, max(endpoint_pnls))).
  Use explicit status flags, never a finite substitute for infinity.

  Sanity formulas (valid, correctly oriented standard packages):
    long call/put:     maximum loss = debit paid;
    debit vertical:   maximum loss = net debit paid;
    credit vertical:  maximum loss = spread-width cash - net credit;
    cash-secured put: maximum loss = strike cash - net credit.
  Credit-vertical arithmetic is a test reference, not a newly enabled
  route. Assignment liquidity and orphan-leg risk are separate gates.
  Terminal package payoff does not guarantee a package can be closed
  at that loss intraday; costs, early assignment and legging risk
  remain explicit. Reject invalid/misaligned contract metadata.

  Sizing uses exact contractual risk plus a separately declared
  nonnegative risk_cost_allowance_cents per package. This allowance
  is not again subtracted from EV as a second copy of the same cost.
  For N packages:
    contractual_max_loss_cents = max_risk_per_package_cents * N.

  Scenario grid (diagnostic only):
    K_i_micros = strike_mills_i * 1000.
    S_min_micros = max(MIN_POSITIVE_SPOT_MICROS,
                      PAYOFF_KERNEL_GRID_MIN_FRAC * spot_micros).
    S_max_micros = max(max_i(K_i_micros), spot_micros)
                   * PAYOFF_KERNEL_GRID_MAX_MULT.
    Geometric step factor = 1.005; union all strikes and valid
    K_i_micros +/- epsilon_micros; retain only positive nodes.
    If S_min_micros >= S_max_micros or too many/invalid points,
    grid_status=UNAVAILABLE. This does not change exact endpoint risk.
    scenario_worst_loss_cents is explicitly truncated-range loss and
    MUST NOT feed contractual risk or sizing. Required scenario/EV
    consumers may still fail closed when their own grid is unavailable.
    The $10 positive grid floor never removes the analytical x=0 test.

  Golden example: short one standard $100 put, multiplier 100,
    entry credit $200, zero costs -> max loss $9,800 at x=0.
    The $8,800 loss at x=$10 is a scenario, not the maximum.

D.6 Position Sizing (lane-parameterized)

  The lane max_risk_pct_equity overrides BASE_RISK_PCT when declared.
  TACTICAL_2DTE uses 0.005; otherwise BASE_RISK_PCT=0.0075.
  risk_budget_cents = floor(Equity_cents * lane_max_risk_pct).
  risk_per_package_cents = max_risk_per_package_cents
                           + risk_cost_allowance_cents.
  Both risk inputs come from the frozen D.5 risk contract.
  Require risk_status=FINITE, max_risk_per_package_cents > 0,
  risk_cost_allowance_cents >= 0 and a positive denominator.
  Missing, unsupported, unbounded or zero-risk/anomalous package:
    no size and no executable route; do not divide or default.
  N = floor(risk_budget_cents / risk_per_package_cents).
  N=0 means no position. Subsequent portfolio and assignment-capacity
  constraints may reduce N but never increase it beyond this bound.
  Premium stops and scenario_worst_loss_cents never replace this risk.

D.7 Kelly (Shadow)
  kelly = max(0, (b·p − (1−p)) / b) × 0.25

D.8 Model-Free Variance (discrete CBOE form)
  σ²_fair = (2/T) · Σ_i (ΔK_i / K_i²) · e^{rT} · Q(K_i)
            − (1/T) · (F/K₀ − 1)²
  K₀ = first strike below F.

D.9 HAR-RV Forecast
  Standard HAR-RV log-linear forecast with daily, weekly,
  and monthly realized-variance regressors. Coefficients
  fit per ticker by OLS over the walk-forward window.
  Pinned model_version stored on volatility_snapshots.
  Consumed only as a VRP input; not decision-critical at
  v2.0.5.1.

D.10 VRP in Vol Points
  implied_vol = sqrt(sigma_fair)
  realized_vol_forecast = sqrt(rv_forecast)
  VRP_vol = implied_vol − realized_vol_forecast

D.11 T+1 OI Classification
  Classification of the T+1 change in open interest
  relative to observed volume: OPENING (OI up by ~volume),
  CLOSING (OI down by ~volume), ROLLING (OI flat),
  ANOMALOUS (unexplained). Feeds thesis.flow_label and the
  FDI retrospective (SPEC Vol 3 §17).

D.12 EV and Lower Bound
  EV_net   = p·W − (1−p)·L − C
  EV_lower = p_lower·W_lower − (1−p_lower)·L_upper − C_upper
  p_BE     = (L + C) / (W + L)
  Actionable requires:
    p_lower ≥ max(route_threshold, p_BE + SAFETY_MARGIN)
    EV_lower > 0

D.12a EV Subsystem
  Event space: route profitability over the lane's holding
  horizon.
  p binding:
    p = p_strategy_profitable_1d for TACTICAL_2DTE and
      SHORT_TACTICAL.
    p = p_strategy_profitable_<horizon> for SWING and
      LONGER_HORIZON.
    p_direction_correct_1h/1d are diagnostic-only.
  W, L, C: empirical from walk-forward sample.
  SAFETY_MARGIN default 0.05.
  Binding: p_lower ≥ max(route threshold, p_BE +
  SAFETY_MARGIN).

D.13 Chase (Debit and Credit)
  chase_debit  = max(0, (current_ask − event_debit) / event_debit)
  chase_credit = max(0, (event_credit − current_bid) / event_credit)
  Limits per AI.4.

D.14 DTE Lane Assignment
  calendar_dte = (expiration_date − today).days
  0       → 0DTE (research-only; two-tier cluster detection)
  1       → 1DTE (research)
  2       → TACTICAL_2DTE
  3..7    → SHORT_TACTICAL
  8..60   → SWING
  61+     → LONGER_HORIZON

--------------------------------------------------------------------------------
D.14a 0DTE Cluster Detection — Two-Tier Design
--------------------------------------------------------------------------------

Purpose: real-time tactical intelligence about same-day
expiry flow clusters. No route, size, or ACTIONABLE_NOW.

Inputs:
  - accepted canonical events tagged with
    expiration == today.
  - provider alert attributes (raw_color,
    normalized_meaning).
  - current session's Dealer Level Map.
  - current session's Market Map.
  - LivePriceProviderAdapter spot.

Basic cluster (silent):
  Same ticker + same-day expiration; ≥
  ZERO_DTE_CLUSTER_MIN_EVENTS (2) independent canonical
  events across ≥ ZERO_DTE_CLUSTER_MIN_STRIKES (2) distinct
  strikes within ZERO_DTE_CLUSTER_WINDOW_S (900 s), with at
  least one member of RAPIDFIRE_FAMILY or REPEATER_FAMILY in
  normalized_meaning. Failing tiers stored silently with
  cluster_grade = BASIC, cluster_state = ACTIVE,
  episode_state = FORMING.
  BASIC clusters write to zero_dte_cluster_current and
  zero_dte_cluster_member_history only; at expiry they write
  a zero_dte_cluster_snapshots row with
  snapshot_type = 'BASIC_SHADOW', alert_grade = 'BASIC',
  and alert_ts = NULL.

MEDIUM_CONFLUENCE tier:
  Requires ALL:
    1. DQ grade A/B, and:
         coverage = 'COMPLETE', OR
         coverage = 'PARTIAL' with
           provider_coverage_pct ≥
           ZERO_DTE_MEDIUM_MIN_COVERAGE_PCT (0.80).
       MANUAL_ONLY and UNKNOWN do not qualify for MEDIUM.
    2. No canceled or materially late member.
    3. Recognized provider status mapping.
    4. Tier 1/2 spread package legs counted as one event.
    5. Aggressor-adjusted direction unambiguous.
    6. OpposingShare = min(B,R)/(B+R) ≤ 0.25.
    7. Flow Strength F ≥ 0.70.
    8. Either ≥ 3 independent events across ≥ 3 strikes,
       OR premium/delta intensity ≥ 90th same-time
       percentile (per D.14b baseline).
    9. market_phase == REGULAR.
   10. last_qualifying_event_age ≤ ZERO_DTE_ALERT_MAX_AGE_S
       (300).
   11. every_counted_member member_latency_ms ≤
       ZERO_DTE_MEMBER_LATENCY_MAX_MS (3000).
   12. post-close reports audit-only.

  Effect: immediate Discord + email. Research-only.
  Dealer-derived fields shown where the current session's
  dealer map supports them; stale within 900 s → labeled;
  older → omitted with "dealer context unavailable".

HIGH_CONFLUENCE tier:
  Requires MEDIUM_CONFLUENCE plus ALL:
    1. Fresh same-session dealer map: age ≤
       ZERO_DTE_DEALER_MAP_FRESHNESS_S (300 s). No stale
       path for HIGH.
    1a. Coverage == COMPLETE.
    1b. Dealer map expiration scope matches cluster
        expiration.
    2. Gamma or vanna alignment confirmed (D.14c).
    3. Spot confirms activation by moving beyond it and
       holding per D.14c.
    4. ConfluenceScore ≥
       ZERO_DTE_HIGH_CONFLUENCE_MIN (0.80).
  Effect: immediate upgrade with revised target/support/
  invalidation and exact confirming evidence. If HIGH at
  first detection, send only HIGH.

--------------------------------------------------------------------------------
D.14b Flow, Directional Share, Flow Strength, Confluence
--------------------------------------------------------------------------------

Directional dollar delta per netted package k (sum over
legs j):

  S_{k,j,$} = underlying_price_micros_{k,j} / 1,000,000

  X_k = Σ_j aggr_{k,j} · Δ_{k,j} · Q_{k,j} · M_{k,j} · S_{k,j,$}

  where
    aggr = +1 if aggressor is buyer, -1 if seller.
    Δ    = signed option delta (positive for calls, negative
           for puts).
    Q    = contracts on leg j.
    M    = contract multiplier on leg j.
    S_{k,j,$} = underlying spot in dollars, computed as
                underlying_price_micros_{k,j} / 1,000,000
                before X_k evaluation. Never pass spot in
                _micros or _mills into X_k. X_k is in dollars.

This gives:
  call buy:    +Δ → bullish
  call sell:   -Δ → bearish
  put buy:     -Δ → bearish
  put sell:    +Δ → bullish

Aggregate:

  B = Σ_k max(X_k, 0)
  R = Σ_k max(-X_k, 0)

  OpposingShare               = min(B, R) / (B + R)
  DirectionalStrength         = 1 − 2·OpposingShare
                              = |B − R| / (B + R)
  SignedDirectionalImbalance  = (B − R) / (B + R)

Guard: B + R = 0 → no cluster.

Semantics:
  OpposingShare is the gate input (gate f, threshold 0.25).
  DirectionalStrength is the D_s input to Flow Strength.
    Zero for balanced flow; 0.5 at the gate boundary; 1
    for fully directional.
  SignedDirectionalImbalance is display-only. Its sign
    gives direction; its absolute value equals
    DirectionalStrength.

Flow Strength (all inputs normalized to [0, 1]):

  F = ZERO_DTE_FLOW_WEIGHT_DELTA   · P_Delta
    + ZERO_DTE_FLOW_WEIGHT_PREMIUM · P_premium
    + ZERO_DTE_FLOW_WEIGHT_DIRECTION · D_s
    + ZERO_DTE_FLOW_WEIGHT_EVENTS  · E_s
    + ZERO_DTE_FLOW_WEIGHT_STRIKES · K_s

  where
    P_Delta   = same-ticker 0DTE same-time percentile of
                gross delta dollars.
    P_premium = same-ticker 0DTE same-time percentile of
                premium.
    D_s       = DirectionalStrength
              = 1 − 2·OpposingShare
              = |B − R| / (B + R).
                Zero for balanced flow; 0.5 at the MEDIUM
                gate boundary (OpposingShare = 0.25); 1 for
                fully directional flow.
    E_s       = min(N_events / 5, 1).
    K_s       = min(N_strikes / 5, 1).

Percentile baseline (definitions):
  Percentile of current 0DTE aggregate vs same-ticker same-
  time-of-day trailing distribution.
  Baseline: trailing ZERO_DTE_PERCENTILE_WINDOW_D (20)
  trading days, same clock-minute bucket ±
  ZERO_DTE_PERCENTILE_BUCKET_S (600 s).
  Cold start (default fail closed): fewer than
  ZERO_DTE_PERCENTILE_MIN_DAYS (10) usable sessions →
  percentile gates do not pass; cluster retained at BASIC.
  Optional fallback (config flag, default false): labeled
  liquidity/sector-bucket fallback with
  ZERO_DTE_PERCENTILE_FALLBACK_PENALTY (0.15) applied to F;
  alert body carries "percentile baseline: fallback".

Dealer confirmation:
  D_c = max(GammaAlign, VannaAlign) in [0, 1].

Price confirmation:
  P_c = 1 only after the activation level is crossed or
  rejected in the thesis direction by the confirmation
  buffer b (D.14c) and held for
  ZERO_DTE_CONFIRMATION_HOLD_S (60 s). Else 0.

ConfluenceScore:
  ConfluenceScore = ZERO_DTE_CONFLUENCE_WEIGHT_FLOW   · F
                  + ZERO_DTE_CONFLUENCE_WEIGHT_DEALER · D_c
                  + ZERO_DTE_CONFLUENCE_WEIGHT_PRICE  · P_c
  Defaults: 0.65·F + 0.25·D_c + 0.10·P_c.

--------------------------------------------------------------------------------
D.14c Gamma/Vanna Confirmation, Target, Support, Invalidation
--------------------------------------------------------------------------------

Gamma confirmation (structural only):

  GammaAlign is derived ONLY from the current session's
  dealer map. It does NOT reference price crossings, holds,
  rejections, or any price-derived quantity. Price
  confirmation is P_c in D.14b.

  GammaAlign = 1 when a fresh, unexpired dealer-map level
  exists with orientation consistent with the flow direction:
    Bullish cluster:
      a POSITIVE_GAMMA_SUPPORT exists below spot;
      OR a POSITIVE_GAMMA_PIN exists above spot;
      OR a NEGATIVE_GAMMA_ACCELERATOR exists above spot;
      OR a confirmed structural gamma-flip state aligns
      (dealer map only; not price-derived).
    Bearish cluster: mirrored.

  GammaAlign = 0.5 when dealer levels are present but not
  unambiguously aligned.

  GammaAlign = 0 when no fresh dealer-map level exists, or
  the map contradicts the flow direction, or the map is
  stale beyond ZERO_DTE_DEALER_MAP_FRESHNESS_S.

  VannaAlign = 1 only when the sign of IV-movement-driven
  dealer hedge flow (H_V_ADV, below) matches the flow
  direction. IV-momentum only; no price reference.

  Separation rule: changing only price behavior cannot
  change GammaAlign or VannaAlign. Changing only dealer-map
  structure cannot change P_c.

Vanna confirmation (normalized):

  H_V = -Vanna_vol · ΔIV_vol

  Normalize by dollar-volume denominator:
    H_V_ADV = (-Vanna_vol · ΔIV_vol) / ADV_dollar_window
    ADV_dollar_window = trailing average dollar volume over
    the lane's lookback window (default same session's
    trailing 20 sessions same-time bucket).

  VannaAlign = 1 only when:
    - sign(H_V) matches flow direction,
    - |H_V_ADV| ≥ ZERO_DTE_VANNA_RELEVANCE_MIN (0.10),
    - IV timestamps aligned with the event window.
  Flat or missing IV → VannaAlign = 0 (context-only).

Confirmation buffer (all in _mills):
  S_mills       = round(S_micros / 1000)
  ATR_5m_mills  = round(ATR_5m_micros / 1000)
  b_mills = max(0.0015 · S_mills, 0.15 · ATR_5m_mills)

Confirmation rule: spot_mills must close beyond the
activation level by b_mills and hold for
ZERO_DTE_CONFIRMATION_HOLD_S (60 s).

Target and support/invalidation selection:
  All price levels (activation, target,
  support/resistance, invalidation) are stored and
  compared in _mills. Spot references remain in _micros.
  Eligible set E: fresh, unexpired, scenario-valid levels
  from the current session's dealer map and market map.
  Target = nearest eligible level in the direction of
  travel, priority:
    1. POSITIVE_GAMMA_PIN / RESISTANCE / SUPPORT, or native
       wall.
    2. Scenario-active VANNA_IV_UP_FLOW_LEVEL or
       VANNA_IV_DOWN_FLOW_LEVEL whose projected hedge flow
       aligns.
    3. Ranked confluence zone.
  NEGATIVE_GAMMA_ACCELERATOR in direction of travel is
  labeled "ACCELERATION TRIGGER". After the accelerator
  confirms, the next stabilizing gamma pin/wall or activated
  vanna level becomes the target.
  Support (bullish) / Resistance (bearish): nearest positive-
  gamma support/resistance, put/call wall, gamma-flip band,
  or dealer/AVWAP/VWAP confluence.
  Invalidation (all in _mills):
    Bullish: confirmed move below support_low − b_mills.
    Bearish: confirmed move above resistance_high + b_mills.
  Correction: the "next lower gamma strike" is not
  automatically support. If it is negative gamma, it is an
  acceleration or air-pocket risk and an invalidation
  warning.

--------------------------------------------------------------------------------
D.14d Episode Lifecycle and Delivery
--------------------------------------------------------------------------------

Episode identity:
  episode_id = sha256(
      ticker | expiration | direction |
      first_qualifying_canonical_event_id | ruleset_version
  )[:32]
  Deterministic across restarts. The first qualifying
  canonical event is persisted before the cluster is
  created, so restart produces the same ID. Two distinct
  same-day episodes for the same (ticker, expiration,
  direction) are distinguished by their different
  first_qualifying_canonical_event_id values. No manual
  |seq=N fallback exists.
  subject_key =
    "0dte:{ticker}:{direction}:{expiration_yyyymmdd}:{episode_id}:{state}"
  where the subject-key {state} token is a compact
  convention derived from (cluster_grade, cluster_state,
  episode_state):
    BASIC    → cluster_grade = BASIC, cluster_state = ACTIVE
    MEDIUM   → cluster_grade = MEDIUM_CONFLUENCE,
               cluster_state = ACTIVE
    HIGH     → cluster_grade = HIGH_CONFLUENCE,
               cluster_state = ACTIVE
    REVERSAL → cluster_state ∈ {BULLISH_REVERSAL,
               BEARISH_REVERSAL}
    MIXED    → cluster_state = MIXED
    RETRACTED→ cluster_state = RETRACTED
    EXPIRED  → cluster_state = EXPIRED

Push policy:
  Maximum normal pushes per episode: one MEDIUM + one HIGH
  upgrade. Additional same-direction members update silently
  unless the grade, target, invalidation, or lead/lag state
  changes materially.
  Separate immediate notifications allowed for:
    - reversal (category zero-dte-cluster-reversal).
    - retraction (category zero-dte-cluster-retraction).
    - new MIXED cluster.
  No arbitrary global daily cap on 0DTE cluster pushes.

Corrections:
  A canceled member is removed from
  zero_dte_cluster_members (removed_at set, removal_reason
  recorded) and mirrored to
  zero_dte_cluster_member_history. Cluster recomputed. If it
  no longer qualifies for its current grade, immediate
  retraction by Discord and email.

Expiry:
  Episode expires at instrument close. cluster_state =
  EXPIRED, episode_state = EXPIRED. Current row retired
  per invariant AA. For episodes with cluster_grade ∈
  {MEDIUM_CONFLUENCE, HIGH_CONFLUENCE}, the final snapshot
  is written to zero_dte_cluster_snapshots with
  snapshot_type = 'EXPIRY'. For BASIC episodes, the final
  snapshot is written with snapshot_type = 'BASIC_SHADOW',
  alert_grade = 'BASIC', and alert_ts = NULL. For all
  episodes, including
  BASIC, member history is retained in
  zero_dte_cluster_member_history. Next morning only in
  Prior-Day 0DTE Research Audit.

Delivery:
  Both MEDIUM and HIGH are immediate urgency. Discord and
  email dispatched in parallel. Email path: Resend primary,
  Mailgun fallback. Discord success does NOT suppress
  email. If both email providers fail, failed delivery
  retained and a delivery-channel-degraded notification is
  emitted.

--------------------------------------------------------------------------------
D.14e Lead/Lag and Markout Outcome Kernel
--------------------------------------------------------------------------------

Per cluster episode, computed after the relevant horizon
closes. Never fed back into alert-time snapshot.

d = +1 bullish, -1 bearish; S_0 = spot at detection.

  r_h    = d · (S_t_h − S_0) / S_0
  MFE_h  = max_{t ∈ (0, h]} ( d · (S_t − S_0) / S_0 )
  MAE_h  = max_{t ∈ (0, h]} ( d · (S_0 − S_t) / S_0 )

Store per (cluster_snapshot_id, horizon,
calculation_version):
  pre_5m_return, first_event_to_detection_return,
  post_1m_return, post_5m_return, post_15m_return,
  post_30m_return, to_close_return, MFE, MAE,
  target_hit_at, invalidation_hit_at,
  lead_lag_class ∈ {FLOW_LED, COINCIDENT, PRICE_LED,
  INDETERMINATE}.

Because MEDIUM and HIGH of the same episode produce separate
alert rows, they produce separate outcome rows.

--------------------------------------------------------------------------------
D.15 Dealer Cache Spot Threshold
--------------------------------------------------------------------------------
  m_daily = IV_30 / sqrt(252)
  TACTICAL_2DTE:  max(0.0035, 0.25·m_daily)
  SHORT_TACTICAL: 0.35·m_daily
  SWING:          0.50·m_daily
  LONGER_HORIZON: 0.75·m_daily

D.16 Vanna Scenario Hedge Flow
  Δ_dealer_delta_$ ≈ vanna_$/volpt × ΔIV
  Δ_hedge_$ ≈ −Δ_dealer_delta_$

D.17 Tactical Level Relevance
D.18 Paired Exposure Netting
D.19 Gamma Flip Alignment

D.20 Level Persistence and Rollover

D.21 Dealer Hedging Pressure (signed)
  H_$ = -( gamma_flow_$per1pct × ΔS_pct
         + vanna_flow_$pervolpt × ΔIV_volpt
         + charm_flow_$perday × Δt_days )
  H_signed    = H_$ / ADV_$
  H_magnitude = |H_signed|
  If sign(H_signed) opposes thesis direction:
    EV_lower -= HEDGE_PENALTY_DEFAULT × H_magnitude
  Single application.

D.22 Basis: canonical basis rule in SPEC Vol 3 §9.7.

D.23 Derived Gamma Flip (Grid Repricing)
D.24 Call Wall / Put Wall

D.25 FDI (Delta-Weighted)

  S_i is the underlying spot in dollars:
    S_i_dollars = S_i_micros / 1,000,000
  Every S in this formula is S_i_dollars. Never pass _micros
  or _mills into the formula.

  D_i = Σ_j s_ij · Δ_ij · Q_ij · M_ij · S_i_dollars
  q_i = event weight (default 1)
  FDI_t = Σ_i q_i·D_i / Σ_i q_i·|D_i|

D.26 Provider Query Budget (pool-based)
  Pools per (provider, market_date):
    FLOW_ALERT      60% of provider's daily ceiling.
                    SPX_INTRADAY debits this pool.
                    ZERO_DTE_CLUSTER debits this pool.
    MORNING_AD_HOC  40% shared.
    GLOBAL          separate ceiling.
  Borrowing: pre-market borrow ≤
  BUDGET_PREMARKET_BORROW_PCT restored at 09:30 ET.
  Intraday: FLOW_ALERT may draw unused MORNING_AD_HOC
  capacity only when that pool is ≥ 80% unspent.
  AD_HOC never draws beyond shared pool.

D.27 Calibrator Lookup and Fallback
  Lookup: scoped → parent via _ANY → none → WATCH.
  Only manifest-active calibrators visible.
  Fallback confidence × FALLBACK_CONFIDENCE_FACTOR.

================================================================================
G. NOTIFICATION & EMAIL DELIVERY
================================================================================

G.1 Notification Creation
  Idempotent on (category, provider, subject_key) within
  per-category cooldown:
    flow-alert-triggered            60
    flow-state-change               3600
    flow-retraction                 3600
    market-stand-down               3600
    plan-requires-open-revalidation 86400
    price-alert-triggered           120
    challenge-detected              3600
    fingerprint-incoherent          3600
    canary-drift                    86400
    behavioral-drift                2592000
    dealer-flip-disagreement        86400
    basis-tolerance-warning         86400
    external-signal                 86400
    zero-dte-flow-cluster           300
    zero-dte-dealer-confirmed       300
    zero-dte-cluster-reversal       300
    zero-dte-cluster-retraction     300
    zero-dte-cluster                86400
    scheduler-heartbeat-gap         3600
    (all others)                    3600

G.2 Delivery Dispatch

  if urgency == 'immediate':
    deliver_discord
    deliver_email      (parallel; Discord does not suppress
                        email)
  elif urgency == 'daily':
    enqueue_daily_summary
  else:
    log only

  The four 0DTE categories are immediate.

G.3 Discord Delivery
G.4 Email Delivery (Resend → Mailgun, 2 attempts each).
G.5 Retry After 15 Minutes.
G.6 Notification Format: [{urgency}] [{provider}]
     {short_title}; body full text + actions + one-line;
     resolve via quantctl.
G.7 OpenMarket Alert Trust: Pattern 1 (webhook we control,
     verify signature) or Pattern 2 (Discord message as
     untrusted wake-up; downstream revalidate). Default
     Pattern 2.
G.8 Categories (see SPEC Vol 4 §18.14 for authoritative
     table).

================================================================================
H. CONFIDENCE PROPAGATION
================================================================================

H.1 Stage Confidences.
H.2 Dealer Confidence Function
  c = 0.85 if index else 0.55
  c *= min(total_oi / 50000, 1.0)
  if days_to_event <= 3: c *= 0.6
  c *= max(0.3, 1.0 − greeks_age_hours / 24.0)
H.3 Latency Freshness (lane-parameterized)
  age_ms = now_ms − print_ts_ms
  F_s    = LANE_QUOTE_FRESHNESS_S[lane]
  T_half = F_s * 1000 * 0.5
  T_zero = F_s * 1000 * 4.0
  if age_ms >= T_zero: return 0.0
  if age_ms <= T_half: return 1.0
  frac = (age_ms − T_half) / (T_zero − T_half)
  return 1.0 − frac
H.4 Regime Neutral Band.
H.5 Flip Distance.
H.6 Dealer Level Map Interaction.

================================================================================
I. CALIBRATION & WALK-FORWARD
================================================================================

I.1 Calibrator Types.
I.2 Per-Target Calibrators.
I.3 Active Calibrator Enforcement.
I.4 EV/ES Models.
I.5 Lower Bound Estimation.
I.6 Walk-Forward.
I.7 Weight Clamp.
I.8 Beta Prior Shrinkage.
I.9 Cold Start + Fallback.

================================================================================
J. SPREAD DETECTION
================================================================================

J.1 Revaluation Formula.
J.2 Normalization.
J.3 Tier Assignment.

J.4 Structure Signatures (canonical; 25 entries):
  single
  vertical_call
  vertical_put
  calendar
  diagonal
  straddle
  strangle
  iron_condor
  ratio
  butterfly
  broken_wing_butterfly
  condor
  box
  conversion
  reversal
  risk_reversal
  collar
  covered_call
  buy_write
  synthetic_stock
  roll
  jelly_roll
  stock_option_combination
  complex_auction
  cross

  "partial fills" is not a structure — it is a fill state
  tracked on position_fills.

J.5 Cluster Windows.
J.6 Tier 3 Discipline.
J.7 Static Bars.

================================================================================
K. T+1 OI
================================================================================

K.1 Job Order.
K.2 Idempotency.
K.3 Label Update: thesis.flow_label.
K.4 FDI Retrospective only.

================================================================================
L. SIZING & PORTFOLIO RISK
================================================================================

L.1 Position Sizing (lane-parameterized; see D.6).
L.2 Portfolio Limits.
L.3 Entry Check.
L.4 Stop Checks.

L.5 Dealer Hedging Pressure Adjustment (single application):
  Hedge pressure (D.21) is applied once, at EV_lower
  computation. Not additionally subtracted at the portfolio
  gate. Portfolio gates consume H_signed only as a
  correlation-cluster proxy.

================================================================================
O. DAILY SPX ALERT CYCLE
================================================================================

O.1 Trigger Points.
O.2 Pre-Market Setup: scheduled_tasks row with run_at
     sampled from N(μ = 06:45 ET, σ = 15 min) constrained
     to [06:00, 07:00].
O.3 Intraday Firing.
O.4 Post-Close Cleanup: N(μ = 16:45 ET, σ = 15 min)
     constrained to [16:30, 17:30].
O.5 Browser Automation Pseudo-Code.
O.6 Failure Modes.
O.7 Scheduling.
O.8 Human Realism (operator_routine in
     behavioral_reference).
O.9 Cross-Day Reconciliation.
O.10 Thesis Interaction.

================================================================================
P. LIVEPRICEPROVIDERADAPTER
================================================================================

P.1 Purpose.
P.2 Interface.
P.3 Source Priority.
P.4 Quality and Actionability.
P.5 Instrument Mapping.
P.6 Health.
P.7 Storage.

================================================================================
Q. ESCALATION LOGIC
================================================================================

Q.1 Purpose.
Q.2 Gate Types (price, OI, alert).
Q.3 Significance Thresholds.
Q.4 Escalation Action.
Q.5 Rate Limiting.
Q.6 Logging.

================================================================================
R. SYMBOLTHESISSERVICE
================================================================================

R.1 Interface.
R.2 on_canonical_event (with opposite-thesis pre-check).
R.3 classify_relationship (5-value matrix with
    SUPPORTING_EVIDENCE).
R.4 expire_stale_theses.
R.5 Concurrency.
R.6 transition_thesis.
R.7 on_dealer_map_rollover.

================================================================================
S. ANALYSISSNAPSHOTBUILDER
================================================================================

S.1 Interface.
S.2 Invariants.
S.3 Determinism.
S.4 Idempotency.
S.5 Route Selection Order.
S.6 Decision State Selection

  def signal_valid(gates, dq, coverage, p_lower, ev_lower):
      return (
          dq.grade in ("A", "B")
          and coverage.completeness != "UNKNOWN"
          and not gates.calibrator_missing
          and p_lower is not None
          and p_lower >= gates.route_threshold
          and p_lower >= gates.p_BE + gates.safety_margin
          and ev_lower is not None and ev_lower > 0
          and gates.eligibility_gates_pass
          and gates.supported_route_exists
          and gates.exit_handler_exists
      )

  def select_decision_state(thesis, gates, dq, coverage,
                            p_lower, ev_lower, market_open):
      # 1. External facts — unconditional precedence.
      if gates.retracted: return RETRACTED
      if gates.invalidated: return INVALIDATED
      if gates.stand_down: return STAND_DOWN

      # 2. DQ gate.
      if dq.grade in ("C", "D", "F"): return WATCH
      if coverage.completeness == "UNKNOWN": return WATCH

      # 3. Signal validity gate.
      if not signal_valid(gates, dq, coverage, p_lower, ev_lower):
          return WATCH

      # 4. Evaluated outcomes.
      if not gates.portfolio_pass: return PORTFOLIO_BLOCKED
      if not market_open: return VALIDATED_PENDING_ENTRY
      if not gates.entry_available: return ENTRY_UNAVAILABLE
      return ACTIONABLE_NOW

S.7 Snapshot Fields.

================================================================================
T. PROVIDERQUERYPLANNER
================================================================================

T.1 Interface.
T.2 plan() (with pool resolution).
T.3 is_near_boundary.
T.4 No decorative queries.
T.5 Query types.
T.6 Budget partition.

================================================================================
U. DEALERCONTEXTCACHE
================================================================================
U.1–U.7: caching, TTLs per lane, invalidation, read-only for
detector, integration with 0DTE detector per AI.7.

================================================================================
V. MORNING WORKFLOW
================================================================================
V.1–V.9 with 0DTE cluster context added to §V.7 (Prior-Day
0DTE Research).

================================================================================
W. AD HOC WORKFLOW
================================================================================
W.1–W.7 with 0DTE cluster context added to §W.6
(dealer-context section E).

================================================================================
X. THESIS MERGE / SPLIT
================================================================================
X.1–X.4.

================================================================================
Y. THESIS-LEDGER RECONCILIATION
================================================================================
Y.1–Y.4.

================================================================================
Z. NOTIFICATION MAPPING
================================================================================

Z.1 Mapping Table (complete)

  decision state               category                        urgency
  ---------------------------  ------------------------------  ---------
  ACTIONABLE_NOW               flow-alert-triggered            immediate
  ENTRY_UNAVAILABLE            flow-state-change               immediate
  PORTFOLIO_BLOCKED            flow-state-change               immediate
  INVALIDATED                  flow-state-change               immediate
  RETRACTED                    flow-retraction                 immediate
  STAND_DOWN                   market-stand-down               immediate
  VALIDATED_PENDING_ENTRY      plan-requires-open-revalidation daily
  WATCH                        (silent)
  CANDIDATE                    (silent)
  EXPIRED                      (silent)
  COMPLETED                    (silent)
  NO_ACTIVE_FLOW_THESIS        (silent)

  Non-decision categories (domain per SPEC Vol 5 §O.2.4):
  dealer-flip-disagreement     (research)                      daily
  basis-tolerance-warning      (research)                      informational
  challenge-detected           (system)                        immediate
  canary-drift                 (research)                      daily
  fingerprint-incoherent       (system)                        immediate
  behavioral-drift             (research)                      informational
  external-signal              (research)                      daily
  zero-dte-flow-cluster        (tactical)                      immediate
  zero-dte-dealer-confirmed    (tactical)                      immediate
  zero-dte-cluster-reversal    (tactical)                      immediate
  zero-dte-cluster-retraction  (tactical)                      immediate
  manual-intervention-required (system)                        immediate
  session-blocked              (system)                        immediate
  login-failed                 (system)                        immediate
  schema-changed               (system)                        immediate
  refresh-failed               (system)                        immediate
  backup-drill-result          (research)                      daily
  data-quality-alarm           (system)                        immediate
  weekly-audit-result          (research)                      daily
  scheduler-heartbeat-gap      (system)                        immediate
  delivery-channel-degraded    (system)                        immediate
  price-alert-triggered        (tactical)                      immediate

Z.2 Subject Key
  flow-alert-triggered / flow-state-change:
    "flow:{thesis_id}:{state}:{version}"
  flow-retraction:
    "flow:{thesis_id}:retracted:{version}"
  0DTE cluster categories:
    "0dte:{ticker}:{direction}:{expiration_yyyymmdd}:{episode_id}:{state}"

Z.3 Idempotency per G.1.
Z.4 Body Template
  Body is composed per ARCH v5.1.5.1 Vol 4 §G.6 and
  SPEC v2.0.5.1 Vol 1 §2.19.4: full text + actions +
  one-line summary.

================================================================================
AA. DTE LANES
================================================================================

AA.1 Lane Assignment
  0       → 0DTE (research-only; cluster detection)
  1       → 1DTE (research)
  2       → TACTICAL_2DTE
  3..7    → SHORT_TACTICAL
  8..60   → SWING
  61+     → LONGER_HORIZON

AA.2 Lane Properties

  LANE_PROPERTIES = {
    "0DTE": {
      "directional_alerts": False,
      "research_only": True,
      "research_push": True,
      "cluster_detection": True,
      "hold_horizon_hours": 0,
      "quote_freshness_s": 5,
      "dealer_ttl_s": 300,
      "chase_max": 0,
    },
    "1DTE": {
      "directional_alerts": False,
      "research_only": True,
      "research_push": False,
      "hold_horizon_hours": 0,
      "quote_freshness_s": 5,
      "dealer_ttl_s": 300,
      "chase_max": 0.03,
    },
    "TACTICAL_2DTE": {
      "directional_alerts": True,
      "research_push": False,
      "hold_horizon_hours": 6,
      "quote_freshness_s": 15,
      "dealer_ttl_s": 900,
      "chase_max": 0.05,
      "paper_mode_required": True,
      "max_risk_pct_equity": 0.005,
      "voland_freshness_s": 900,
      "confirmation_delay_s": 60,
      "latest_entry_time": "15:30 ET",
      "mandatory_exit_before_0dte": True,
      "routes": ["debit_spread","long_call","long_put"],
      "calibrator_scope": "TACTICAL_2DTE",
    },
    "SHORT_TACTICAL": {
      "directional_alerts": True,
      "research_push": False,
      "hold_horizon_days": 3,
      "quote_freshness_s": 15,
      "dealer_ttl_s": 1800,
      "chase_max": 0.075,
    },
    "SWING": {
      "directional_alerts": True,
      "research_push": False,
      "hold_horizon_days": 15,
      "quote_freshness_s": 60,
      "dealer_ttl_s": 3600,
      "chase_max": 0.10,
    },
    "LONGER_HORIZON": {
      "directional_alerts": True,
      "research_push": False,
      "hold_horizon_days": 90,
      "quote_freshness_s": 300,
      "dealer_ttl_s": 7200,
      "chase_max": 0.15,
    },
  }

  The 0DTE lane emits research clusters at MEDIUM_CONFLUENCE
  or HIGH_CONFLUENCE. It never emits ACTIONABLE_NOW.

AA.3 calendar_dte vs trading_sessions_remaining.
AA.4 No Pooling.

================================================================================
AB. MARKETMAPSERVICE + DEALERLEVELMAPSERVICE + TECHLEVELSERVICE
================================================================================
AB.1 MarketMapService composes dealer_map_id +
     technical_snapshot_id + price_observation_id +
     volatility + event context into an immutable map_id
     per symbol per session. See SPEC Vol 1 §2.21.
AB.2 DealerLevelMapService produces dealer_map_id; roles
     and lifecycle in SPEC Vol 1 §2.11A.
AB.3 TechnicalLevelService produces
     technical_snapshot_id; field list in ARCH Vol 2 §C.2
     (technical_level_snapshots).
AB.4–AB.13 Detailed service contracts (input manifests,
     snapshot composition, rollover, cache interaction)
     are deferred. Canonical contracts are the DDL in
     ARCH Vol 2 §C.2 and the pipeline description in
     SPEC Vol 1 §2.4.
================================================================================
AC. LISTEDOPTIONQUOTEADAPTER
================================================================================
AC.1 Adapter provides executable option and package
     quotes. See SPEC Vol 1 §4.8.
AC.2 Candidate sources: operator-selected from authorized
     sources in source_authorization.
AC.3 Interface: get_quote(contract_id) and
     get_package_quote(legs) → immutable observation IDs.
AC.4 Quality rules: bid ≥ 0; ask ≥ bid; spread and
     freshness within lane limits.
AC.5 Fallback: VALIDATED_PENDING_ENTRY or WATCH.
AC.6 Current rows reference immutable observation IDs;
     history in DuckDB (option_quote_observations,
     package_quote_observations).
AC.7 Authentication: per source_authorization entry.

================================================================================
AD. SPX CROSSING STATE MACHINE
================================================================================
AD.1–AD.9 per SPEC Vol 3 §9.6 (including hysteresis,
intraday confirmation via 1-minute bars + 60 s hold,
close-of-day resolution for still-TESTING states,
cadence).

================================================================================
AE. CLOSING FDI
================================================================================
See SPEC v2.0.5.1 Vol 7 §AE for the full research contract.

================================================================================
AF. CFTC COT INGESTION
================================================================================
See SPEC v2.0.5.1 Vol 7 §AF for the full research contract.

================================================================================
AG. LEVERAGED ETF PRESSURE
================================================================================
See SPEC v2.0.5.1 Vol 7 §AG for the full research contract.

================================================================================
AH. ROUTE-SPECIFIC EXITS
================================================================================
AH.0 Authority and Activation

  AH.1–AH.6 are normative at v2.0.5.1. They become
  operationally binding when the first position-carrying
  lane opens a position at Stage 4 (Forward Paper). Until
  then, no positions exist and AH has no operational
  effect.

  AH does not alter:
    - the frozen anti-detection layer (ARCH Vol 3 §F);
    - decision precedence (SPEC Vol 3 §8.4);
    - the canonical DDL in SPEC Vol 2 §19;
    - existing constants in ARCH Vol 1 §AI.2/§AI.3.

  Any conflict between AH and SPEC Vol 3 §15.5 resolves in
  favor of AH until a versioned ruleset formally replaces
  it.

  Dependency: AH assumes RQ-005 (package_quote_observation_
  id at evidence boundaries) is resolved per the runbook
  deadline "Before 040/051". If unresolved at Stage 4
  start, AH.2 and AH.4 are blocked.

AH.1 Scope, Inherited Constants, Denominators

  AH.1.1 Preserve ARCH Vol 1 §AI.2 constants:
           PREMIUM_STOP_PCT       = 0.50
           THETA_BUDGET_PCT       = 0.30
           TIME_STOP_DAYS         = 45
           VOLATILITY_EXIT_IVR    = 60
           ROUTE_GAP_TRIGGER_PCT  = 0.015
         These are seeds, not proven-optimal stops.

  AH.1.2 Enabled routes:
           long_call, long_put, defined-risk debit_spread.
           cash-secured_short_put only outside
           TACTICAL_2DTE with explicit assignment capacity.
         Other routes remain disabled until a named
         handler exists.

  AH.1.3 Freeze policy JSON / policy_hash at entry.
         B0 = absolute actual net entry premium cash in
         cents, excluding fees, for the established
         position. B0 must be positive.
         - Debit route: B0 = debit paid.
         - Short-put route: B0 = credit received.
         B0 is NOT strike collateral.

  AH.1.4 Stop level never replaces PayoffKernel
         contractual maximum loss for sizing. Stops can
         be overrun.

AH.2 Premium Stop and Package P&L

  AH.2.1 Cash from fills:
           For every actual fill f,
             s_f = +1 BUY, -1 SELL
             cash_fills = SUM(-s_f * q_f * M_f * price_cents_f)
                          - SUM(fee_cents_f)

  AH.2.2 Remaining signed quantity n_i comes from the
         fill ledger.

  AH.2.3 Let V_close be conservative residual liquidation
         cash in cents (AH.4):
             PNL_liq = cash_fills + V_close
             loss_ratio = max(0, -PNL_liq) / B0

  AH.2.4 Trigger PREMIUM when loss_ratio >= 0.50,
         inclusive.

  AH.2.5 Freeze B0 after entry completion. Later scale-ins
         are new positions / lots.

  AH.2.6 Worked examples:
           Debit $400, closing proceeds $190, total costs
           $4 => PNL = -$214, loss_ratio = 53.5%,
           EXIT recommended.
           Short credit $200, close debit $310, costs $4
           => PNL = -$114, loss_ratio = 57%.
           With zero fees the short threshold is buyback
           $300 (= 1.5x credit), NOT "50% of collateral".

  AH.2.7 Include realized partial-close cash and residual
         risk; do not forget prior losses.

AH.3 Theta, IVR, Gap, Structure, Assignment

  AH.3.1 Theta budget and durable intervals.
         For [t0,t1), use remaining signed legs at t0 and the immutable
         spot/IV/rate/dividend/model inputs known at t0. Advance time only:
           loss_cents_exact = max(0, V_model_cents(t0) - V_model_cents(t1)).
         Split at every fill and policy activation. Positions no longer
         held contribute nothing to subsequent intervals. Overnight and
         weekend time advances even when the holding-horizon clock pauses.
         First-order theta is a diagnostic; production uses full repricing.

         Internal accumulation uses fixed-point microcents:
           delta_microcents = round_half_even(loss_cents_exact * 1000000).
           theta_ratio = theta_consumed_microcents / (B0_cents * 1000000).
         Compare using Decimal/integer arithmetic against THETA_BUDGET_PCT;
         never round each 5-second interval to a whole cent. Keep all
         executable quote/fill money in cents. Detect integer overflow.

         interval_id = SHA256(canonical JSON [position_id,
           policy_activation_id, t0, t1, quantity_revision, model_manifest_hash]).
         Before adding it, quantd checks interval_id is absent, t0 equals
         last_theta_interval_end_at, and no fill/policy boundary is skipped.
         In ONE SQLite transaction insert a THETA_INTERVAL event, advance
         theta_consumed_microcents and the cursor, then update state_revision.
         A repeated interval ID is a no-op; conflicting hashes are a fault.

         Seed the first cursor at the first validated fill/model boundary.
         If required earlier model data is missing, record EVALUATION_BLOCKED;
         do not advance the cursor over an unpriced gap or use later IV
         retrospectively. Catch-up may use only admissible original inputs.
         Preserve pending elapsed time until reconciled. Valid deadlines and
         already-latched triggers remain live throughout the gap.
         Before entry completes, B0-dependent ratios are NOT_EVALUATED;
         quantity, orphan/assignment checks and deadlines are already active.

  AH.3.2 IVR.
         IVR = 100 * (IV_now - min) / (max - min),
         where min/max are over PRIOR252 daily closes
         of consistent 30-day ATM IV. Clip to [0, 100].
         Fewer than 252 or zero range => NULL.
         Long call/put:
           IVR >= 60 for two completed 1m evaluations
             triggers VOLATILITY.
           IV_now <= 0.80 * entry_IV AND PNL_liq < 0,
             same observation, regardless of favorable
             IV changes.
         Never use an intraday return confirmation.
         Short put:
           IVR <= 60 AND PNL_liq >= 0 for two
             evaluations.
         Debit spread:
           IVR/crush only when entry net vega > 0;
           arm IVR-up only if entry IVR < 60.
           Otherwise the affected rule is disabled and
           declared.

  AH.3.3 Gap.
           g = open_today / previous_regular_close - 1
           on split-consistent underlying prices.
         Freeze thesis direction d = +1 bullish,
         -1 bearish.
             adverse_gap = max(0, -d * g)
         Trigger >= 0.015 after a valid opening
         observation.
         Never use an intraday return as an overnight gap.
         Corporate-action uncertainty => manual risk
         review.

  AH.3.4 Structure stop.
         Entry-frozen invalidation level; two completed
         1m closes beyond the level by
             b = max(0.0005 * spot, 0.10 * ATR_1m_14)
         where ATR is the mean true range of 14 prior
         completed 1m bars; all in mills.
         A missing required invalidation / model blocks
         new route activation.

  AH.3.5 Assignment controls.
         Actual assignment or orphan leg => immediate
         risk review.
         Short American option warning:
           ITM and extrinsic <= 2 * contract ticks, OR
           short call with next-session dividend
             >= extrinsic.
         Any assignment exposure > available cash is a
         hard breach.
         Assignment filters are conservative warnings,
         not predictions of exercise.
         Include known dividend/calendar data; unknown
         data cannot pass a required assignment gate.
         No assumed assignment protection from holding
         a long leg.
         Existing portfolio limits and mandatory
         deadlines outrank a favorable hold condition.
         0DTE clusters remain non-executable and have no
         position exits.

AH.4 Conservative Close Valuation and Partial Fills

  AH.4.1 Long residual leg:
             n * M * max(0, bid_cents - slip_cents)
         Short residual leg (n < 0):
             n * M * (ask_cents + slip_cents)
         Sum and subtract estimated close fees.
             slip = ceil_to_tick(max(one_tick,
                                     0.10 * (ask - bid)))
         Use exact multiplier and tick from contract
         master.

  AH.4.2 Seed fees = $0.65 per contract per side for
         paper fixtures ONLY. Real fee schedule must
         replace this before account-specific use.

  AH.4.3 Freshness <= min(lane limit, 60s). Leg
         timestamp skew <= 1s. Side depth positive.
         bid <= ask. Quotes/source/basis valid.
         Prefer a firm package quote for the requested
         signed leg vector and size.
         Leg sums are conservative synthetic estimates,
         not a guaranteed executable package.
         Zero bid / no depth: show lower bound but mark
         UNPRICED; no synthetic fill at zero or at last
         / mid.

  AH.4.4 Partial fills and execution identity.
         Actual broker/operator execution records are authoritative.
         Store a non-null broker, non-secret local account_ref, execution_id,
         stable execution_leg_key, position-local leg_number, side, effect,
         time, quantity, price and explicit fees. Contract multiplier comes
         from the frozen verified contract/entry manifest, never default 100.
         Deduplicate on (broker, account_ref, execution_id, execution_leg_key).
         execution_leg_key is the source execution-leg identity or an exact,
         documented contract-based source key, NOT the local ordinal that
         changes between positions. Normalize any session-scoped source ID
         into its documented session namespace; preserve the original ID.
         The same source fill cannot be assigned twice to different positions.
         Missing identity/fee information is unreconciled, never an invented
         broker fill. MANUAL/PAPER use explicitly labelled local namespaces
         and a persisted unique event ID. A venue is not a broker.

         Recompute signed residual n_i = SUM(buy quantities - sell quantities)
         after each accepted unique fill. Validate account and contract
         consistency and update quantity_revision in the same transaction.
         An order acknowledgment is not an execution. Balanced partial
         closure preserves ratios; unbalanced residuals imply ORPHAN_RISK.
         Never automatically remove protection while short risk remains.

         Paper-only synchronized depth cap:
           alpha = PAPER_DEPTH_PARTICIPATION_PCT = 0.25.
           d_i = bid_size for a SELL-to-close, ask_size for a
                 BUY-to-close.
           r_i = strictly positive contracts per package for leg i.
           capacity_i = floor(alpha * d_i / r_i).
           fillable_packages = min(remaining_packages, min_i(capacity_i)).
         Use integer floor division where possible: d_i // (4*r_i).
         Depth is contracts, not shares; multiplier does not enter capacity.
         Require a complete balanced package, valid quotes and all existing
         freshness/skew/price rules. Do not simulate fills from missing depth.
         Example: ratio 1:1, depth 100:100, remaining 30 -> 25 packages.
         Example: ratio 1:2, depth 100:100, remaining 30 -> 12 packages.

         Before a nonzero paper fill, atomically reserve each used
         (quote_observation_id, contract_id, executable_side) in
         persistent_idempotency and insert the deterministic PAPER fill rows.
         Conservative policy: one fill batch may consume each observation/
         side; a different position cannot reuse it. Do not reserve if zero
         packages fill. Retention must outlive quote eligibility and retries.
         Roll back all reservations if any side was already consumed.
         This models limited fills; it does not claim displayed depth is
         actually executable. Actual confirmed fills bypass the paper cap.
         CLOSED requires all real residuals zero and reconciliation passed.

AH.5 Exact Clock, Deadlines, Monitoring

  AH.5.1 Clock = UTC epoch ms. Calendars use
         America/New_York plus versioned contract
         last_trade_at, settlement, and broker cutoff.

  AH.5.2 TACTICAL_2DTE 6h means 21,600 scheduled
         regular-session seconds [P], pausing outside
         but NOT pausing for a halt inside a scheduled
         session.

  AH.5.3 Day horizons.
         A day horizon of h uses h trading sessions after the entry session,
         at the same elapsed regular-session time as entry. Clamp to a
         shortened target session's close. It is not h*24 wall-clock hours.
         TACTICAL_2DTE uses AH.5.2: 21,600 scheduled regular-session seconds;
         outside-session time pauses that clock, an intraday halt does not.
         Theta's calendar-time accumulation is independent of either clock.
         The lane horizon and its calendar version are frozen at entry.

  AH.5.4 Absolute deadlines, all in UTC epoch milliseconds.
         buffer_ms = POSITION_EXPIRY_EXIT_BUFFER_S * 1000 = 900000.
         For each leg use its verified last_trade_at, not merely expiry date.
         contract_bound_i = last_trade_at_i - buffer_ms.
         calendar_cap_at = entry_at + TIME_STOP_DAYS * 86400 * 1000.
         Where mandatory_exit_before_0dte=true:
           expiry_date = earliest leg expiration date;
           pre_0dte_exit_at = close of the last permitted REGULAR session
                             whose local session date < expiry_date,
                             minus buffer_ms.
         Otherwise pre_0dte_exit_at is NOT_APPLICABLE, not zero.

         Resolve broker/product/account/date-specific absolute cutoff values
         from verified registry metadata plus the frozen calendar. Persist
         each value and its source/version in deadline_manifest_json.
         A verified explicitly-absent broker bound is omitted. Unknown is
         different from absent and blocks entry. Do not invent a cutoff.
         The generic broker registry is only a default; exceptions must be
         explicitly resolved for all legs before approval.

         bounds_ms = [lane_horizon_at, calendar_cap_at,
                      every contract_bound_i,
                      pre_0dte_exit_at when applicable,
                      applicable verified broker_forced_cutoff_at].
         hard_deadline_at = min(bounds_ms).
         If outside allowed monitoring/trading sessions, map backward to the
         latest allowed instant at or before the bound, never forward.
         If deadline <= proposed_entry_at: reject entry.
         Persist absolute bounds before exposing a route as ready.
         Never mix the duration 15m directly into min(timestamps).
         Never relabel 0DTE/1DTE entries as TACTICAL_2DTE; both remain
         research-only and cannot create positions. An existing longer-DTE
         position ages normally but must obey its frozen pre-0DTE deadline.

  AH.5.5 Evaluation and simultaneous triggers.
         Evaluate on fills/assignment/corporate actions/accepted price or
         quote updates, plus every POSITION_EXIT_EVAL_INTERVAL_S=5 while
         carrying exposure. Deadline watchdog every 1 second.
         Evaluate required deadlines even when pricing inputs are absent.
         Persist clock-quality faults; a fault does not clear a known trigger.

         Priority (smallest first):
           1 ASSIGNMENT / ORPHAN_RISK / HARD_PORTFOLIO_BREACH
           2 MANDATORY_DEADLINE
           3 STRUCTURE
           4 GAP
           5 PREMIUM
           6 THETA
           7 VOLATILITY
         Record every true trigger and first_trigger_at. Primary = minimum
         (priority, first_trigger_at, stable trigger_code). Keep all latches
         until executed/reconciled or explicitly audited operator override.
         Recovery in price or loss of a quote never erases a latch.
         Deadline due + missing quote -> EXIT_DUE_UNPRICED.
         Halt/closed when due -> EXIT_DUE_PENDING_MARKET; exposure stays open.
         Deadline-300s reminder is optional once; emit one immediate material
         exit recommendation when due. Acknowledgment is not a fill.

AH.6 Persistence, Failure Policy, Acceptance

  AH.6.1 Active policy and durable operational state.
    position_exit_policies stays immutable with PK(position_id,policy_hash).
    position_exit_state has PK(position_id) and a composite FK to that
    policy. It is the only active-policy pointer; do not pick MAX(hash)
    or the newest policy row at read time. State includes activation ID,
    entry basis/completion, quantities/revision, absolute deadline and
    source manifest, theta accumulator/cursor, latches and exit progress.
    Initialize policy/state before risk can be carried. Entry-basis
    ratios remain unavailable until the first entry is completed.
    An approved policy amendment records a new immutable policy and
    activation event; transition atomically. Preserve accrued theta and
    latches; any exception requires a separately recorded operator action.
    Never retroactively re-price intervals under the new policy.

  AH.6.2 Fills and state transactions.
    Apply the AH.4.4 identity, side and package rules and the SPEC Vol 2
    position_fills DDL. Reject unknown identity before updating quantities.
    One quantd SQLite writer transaction performs each material update:
      verify event/idempotency key and expected state_revision;
      insert fill/interval evidence and append position_exit_events;
      update quantity/theta/cursors, latches and state_revision;
      insert material notifications and pending channel attempts;
      enqueue any analytical mirror in pending_exit_sync; commit.
    Duplicate event ID with identical hash is a no-op. Different payload
    for the same ID is a reconciliation fault. All SQL is parameterized.
    Event facts are immutable; current-state and retry rows are mutable.

  AH.6.3 Analytical history is a mirror, not exit authority.
    Define evaluation_id = SHA256(canonical JSON [position_id,
      policy_activation_id, prior_state_revision, position_revision,
      input_manifest_hash, evaluation_request_id]).
    evaluation_request_id includes an explicitly supplied as_of_ms;
    reuse the identical request on retry. Check its durable event before
    recomputing. Distinct exact times/inputs are not coalesced just
    because they share a one-second bucket.
    Commit the EVALUATION event, resulting state and notification first
    in SQLite. pending_exit_sync records its event ID and evaluation ID.
    Mirror into DuckDB exit_evaluations asynchronously with the SAME
    ID/payload hash, then delete the pending queue row only after success.
    Crash after DuckDB insertion but before queue ACK retries idempotently.
    No cross-engine transaction or fake cross-engine FK is assumed.
    If DuckDB is unavailable, monitoring/latches/deadlines continue from
    SQLite; do not clear a due exit. New entries retain existing gates.
    Delivery retries use persisted notifications and channel attempts;
    a stable notification ID/subject key prevents logical duplicates.
    External transports may still deliver duplicates after ambiguous
    network ACKs; do not promise end-to-end exactly-once email.

  AH.6.4 Safe failure and category mapping.
    Missing required market/model/calendar evidence -> explicit
    EVALUATION_BLOCKED or EXIT_DUE_UNPRICED, never assumed HOLD or fill.
    Preserve last valid observations with ages; do not label them live.
    Required quote/model gaps do not clear known risk/deadline triggers.
    Still-open short quantities retain collateral. If the SQLite write
    itself fails, stop new entries, preserve spooled evidence where
    possible and surface an operational fault; never claim a durable
    exit update committed when it did not.

    Normal exit recommendations use only:
      position-exit-required: TACTICAL, requires_ack=0, urgency=immediate;
      email and Discord independently; no system-health penalty.
    True monitoring failure, or valuation unavailable beyond 60s while
    exposure remains, uses exit-monitor-failure / valuation-unavailable:
      SYSTEM, requires_ack=1, urgency=immediate.
    Unknown category is a programming/config error, not default SYSTEM.
    Resolve all fields through SPEC Vol 5 O.10's category-policy function.
    One notification per position/policy-activation/trigger epoch;
    material severity/residual changes use a new explicit revision.
    An acknowledgment is not resolution, an execution or permission
    to erase a trigger. Do not add EXITING to position_status implicitly.

  AH.6.5 Acceptance and release gates.
         Golden tests:
           exactly 50% and below; credit-vs-debit
           denominator; actual multiplier; all fees;
           theta 30% with partial quantities;
           IVR = 60 boundary; flat history; IV crush;
           adverse/favorable 1.5% gap;
           two-trigger ordering;
           holiday/half-day/AM settlement;
           restart before deadline;
           zero bid/depth;
           ratio partial fill;
           orphan/assignment;
           duplicate execution;
           stale inputs;
           clock drift;
           manual override audit.
         Example alert:
           "EXIT REVIEW - TSLA debit spread.
            Net liquidation loss $214 / $400 basis
            = 53.5%, threshold 50%. 2 packages still
            open; quote age 2s. Primary STRUCTURE:
            premium also failed. Research estimate,
            not a fill."
         Sizing remains based on contractual loss.
         Run replay, fill-stress and chronological
         forward tests before any live
         decision-support promotion. None of these
         seeds implies a win.

  AH.6.6 Schema and migration ownership.
    Final target DDL lives in SPEC Vol 2 and is mirrored in ARCH Vol 2.
    Preserve applied SQLite 070 and DuckDB 042 unchanged.
    Proposed repair migrations: SQLite 071 (fill identity, exit state,
    events/retry queue) and DuckDB 050 (snapshot CHECK and exit mirror).
    Confirm both IDs remain unused before authoring real migration SQL.
    Schema changes affect only the appropriate store. Optional research
    migrations 043/044/045 remain independently disabled until adopted.

  AH.7 Pre-Implementation Checklist
        Before implementation: before activating a route, supply its
        numerical exit rules, trigger priority/handling, deadline
        calculation, gap/market-closed/stale-data behavior,
        partial-fill handling, and audit destination. Naming stop
        families alone does not define an executable handler.

================================================================================
END OF ARCH Vol 4 v5.1.5.1
================================================================================