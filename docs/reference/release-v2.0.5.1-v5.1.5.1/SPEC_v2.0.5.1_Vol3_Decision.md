# QUANT FLOW SYSTEM — SPECIFICATION v2.0.5.1
## VOLUME 3 — DECISION LOGIC

Status: self-contained for the sections this volume owns.
Sections not owned by this volume reference the owning
volume within the 10-file set by section number.

CHANGES FROM v2.0.5
- P0-1: §8.1a renamed from all_pass to signal_valid. The
  predicate concerns only signal validity, not portfolio,
  market hours, or live entry. §8.4 rewritten with the
  signal validity gate running before evaluated outcomes.

CHANGES FROM THIS REVIEW (S3-01 through S3-03)
- S3-01: §15.3 sizing now points at exact contractual
  endpoint/tail risk (ARCH Vol 4 §D.5) plus the D.6 cost
  allowance; scenario-grid minima and stops are explicitly
  excluded.
- S3-02: §15.5 exit readiness made concrete at route
  activation (frozen policy, active pointer, resolved
  deadlines, fill-identity, durable monitoring).
- S3-03: §15.6 fills bound to the corrected package-depth
  and execution identity in ARCH Vol 4 §AH.4.4; order
  acknowledgments are never fills.

CHANGES FROM v2.0.4
- §8.1a new: signal_valid composition explicit.
- §8.4 rewritten to use signal_valid.
- §9.6.5 SPX FSM: retreat hysteresis, intraday
  confirmation, evaluation cadence.
- §9.6.10 new constants.
- §14.7.1 measurement note added.
- §14.19.8 scope-aware recomputation.
- §15.9 sizing precedence explicit.

================================================================================
SECTION 8 — ACTIONABILITY CONTRACT
================================================================================

8.1 Actionability Contract (strict enforcement)

A route is ACTIONABLE_NOW only when ALL hold. Any false →
WATCH, VALIDATED_PENDING_ENTRY, ENTRY_UNAVAILABLE, or
PORTFOLIO_BLOCKED per the specific failure.

8.1.1 DQ grade A or B. Grade C watch-only regardless of
      score. Grades D and F prohibited from the decision
      path.
8.1.2 Coverage not UNKNOWN. PARTIAL caps confidence at 0.70.
      MANUAL_ONLY caps at 0.50. Cap applied inside the per-
      dimension weighted sum (§14.1).
8.1.3 A target-scoped calibrated probability exists. Fallback
      lookup per §14.19.4 permitted with confidence
      reduction (FALLBACK_CONFIDENCE_FACTOR = 0.7). If no
      calibrator (scoped or fallback) exists, decision →
      WATCH.
8.1.4 calibrated_probability_lower ≥ route threshold.
8.1.5 EV_lower > 0 after modeled costs. Until W/L/C are
      estimated, EV_net = null and EV_lower = null;
      actionability blocked.
8.1.6 All eligibility gates pass.
8.1.7 A supported route is selected with a declared exit
      handler (§15.5).
8.1.8 Current entry available (chase within lane limit).
8.1.9 Portfolio and assignment-risk gates pass.
8.1.10 Programmatic enforcement.
8.1.11 High raw score never overrides a failed gate.
8.1.12 Route selection is the OUTPUT of gate evaluation.
8.1.13 Favorable Dealer Level Map entry does not upgrade the
       decision state.
8.1.14 Every executable decision references a valid
       quote_snapshot_id and package_quote_observation_id
       (multi-leg).
8.1.15 Perp/proxy price never satisfies ACTIONABLE_NOW.
8.1.16 p_lower ≥ p_BE + SAFETY_MARGIN (default 0.05) in
       addition to §8.1.4. Binding constraint is
       p_lower ≥ max(route threshold, p_BE + SAFETY_MARGIN).
       SAFETY_MARGIN is a named constant in ARCH Vol 1 §AI.3.

8.1a signal_valid Definition (canonical)

  signal_valid ⇔ every gate below evaluates true. The
  predicate concerns ONLY whether a valid, actionable
  signal exists. It does NOT include portfolio capacity,
  market hours, or live entry availability — those are
  evaluated separately in §8.4.

      dq.grade ∈ {A, B}
   ∧  coverage.completeness ≠ UNKNOWN
   ∧  calibrator exists for scope (scoped or fallback)
   ∧  calibrated_probability_lower ≥ route_threshold
   ∧  p_lower ≥ p_BE + SAFETY_MARGIN
   ∧  EV_lower > 0
   ∧  eligibility gates pass
   ∧  supported route selected with declared exit handler

  Rationale: a signal that has not passed statistical
  validation returns WATCH regardless of portfolio or
  entry state. Prior formulations mixed signal validity
  with portfolio and entry gates into one flag, which
  (a) returned PORTFOLIO_BLOCKED for unvalidated theses
  and (b) made VALIDATED_PENDING_ENTRY unreachable when
  entry was unavailable during closed markets.

8.2 Calibrated Quantities

calibrated_probability           point estimate
calibrated_probability_lower     lower bound (80% CI)
expected_return_net_costs        point estimate
expected_return_lower            lower bound

8.3 Expected Value

EV_net   = p·W − (1−p)·L − C
EV_lower = p_lower·W_lower − (1−p_lower)·L_upper − C_upper
p_BE     = (L + C) / (W + L)

Binding of p, W, L, C in ARCH Vol 4 §D.12a. Summary:
  p = p_strategy_profitable_<horizon>.
  W = E[ gain | win ] over walk-forward sample.
  L = E[ loss | lose ].
  C = modeled costs (spread-crossing + fees + λ-stress).
  W_lower, L_upper, C_upper = empirical 20th / 80th / 80th
    percentile estimates.
  SAFETY_MARGIN = 0.05.

Actionable requires:
  p_lower ≥ max(route_threshold, p_BE + SAFETY_MARGIN)
  EV_lower > 0

Until route-specific W, L, C are estimated → null.

8.4 Decision State Selection

Order:

  1. External facts (unconditional precedence):
       RETRACTED > INVALIDATED > STAND_DOWN

  2. DQ gate:
       grade ∈ {C, D, F}       → WATCH
       coverage == UNKNOWN     → WATCH

  3. Signal validity gate (per §8.1a):
       not signal_valid        → WATCH

     Rationale: a thesis that has not passed statistical
     validation returns WATCH regardless of portfolio or
     entry state. Prior formulations mixed signal validity
     with portfolio and entry gates into one flag, which
     (a) returned PORTFOLIO_BLOCKED for unvalidated theses
     and (b) made VALIDATED_PENDING_ENTRY unreachable when
     entry was unavailable during closed markets.

  4. Evaluated outcomes (reached only when §3 passes):
       portfolio gates fail    → PORTFOLIO_BLOCKED
       market closed           → VALIDATED_PENDING_ENTRY
       market open + entry
         unavailable           → ENTRY_UNAVAILABLE
       else                    → ACTIONABLE_NOW

Terminal theses (EXPIRED / COMPLETED / RETRACTED) are never
routed through the decision function.

Precedence for conflict resolution:
  RETRACTED > INVALIDATED > STAND_DOWN > WATCH (from C/D/F or
  UNKNOWN) > WATCH (from signal_valid failure) >
  PORTFOLIO_BLOCKED > VALIDATED_PENDING_ENTRY >
  ENTRY_UNAVAILABLE > ACTIONABLE_NOW > CANDIDATE >
  NO_ACTIVE_FLOW_THESIS

Divergent case resolution: market closed + portfolio OK +
entry unavailable → falls through to VALIDATED_PENDING_ENTRY
(market closed takes precedence over entry availability).

8.5 Enrichment: immutable references only.
8.6 Dealer Exposure Snapshots: per pipeline.
8.7 Cadence: on material event, on rollover, on schedule.
8.8 Interpretation: dealer levels describe positioning, not
    trade direction.

================================================================================
SECTION 9 — CLASSIFICATION
================================================================================

9.1 Four Independent Questions: direction, structure,
    volatility, timing.
9.2 Aggressor: buy-side or sell-side per event.
9.3 Delta-Gamma-Theta-IV: decomposition kernel.
9.4 Opening Evidence: vol/oi, aggressor, mid-persistence,
    premium rise; clarification §9.4.2.
9.5 DTE Eligibility:
      9.5.1 Deterministic gate.
      9.5.2 Lane assignment per §2.20 / ARCH Vol 4 §AA.1.
      9.5.3 0DTE is research-only (two-tier cluster detection
            per §2.20.7).
      9.5.4 1DTE is research-only.
      9.5.5 Sub-1-DTE still collected for surface and regime.

9.6 SPX Crossing State Machine

9.6.1 Purpose: track SPX level crossings from Market Map
      levels using alert firings and spot.
9.6.2 States: FAR, APPROACHING, TESTING, CONFIRMED_BREAKOUT,
      CONFIRMED_REVERSAL, FALSE_CROSS, COOLDOWN, REARMED,
      INVALIDATED.
9.6.3 Inputs: OpenMarket alert firing, spot from
      LivePriceProviderAdapter, instrument-specific session
      close, Market Map levels.
9.6.4 Only Market Map levels trigger.

9.6.5 State transitions (complete):
      FAR → APPROACHING when |spot − level| / spot <
        SPX_APPROACHING_PCT (0.003).
      APPROACHING → FAR when |spot − level| / spot >
        SPX_APPROACHING_RETREAT_PCT (0.005). Hysteresis: the
        retreat threshold strictly exceeds the entry
        threshold.
      APPROACHING → TESTING when alert fires.
      TESTING → CONFIRMED_BREAKOUT intraday when:
        A 1-minute bar closes beyond the level by more
        than SPX_CONFIRMATION_BUFFER_PCT × spot, AND
        spot holds beyond the level for
        SPX_CONFIRMATION_HOLD_S (60 s) after that bar
        closes.
        Notification emitted immediately, intraday.
      TESTING → CONFIRMED_REVERSAL intraday when:
        A 1-minute bar closes on the origin side by more
        than SPX_CONFIRMATION_BUFFER_PCT × spot, AND
        spot holds on the origin side for
        SPX_CONFIRMATION_HOLD_S (60 s).
        Notification emitted immediately, intraday.
      TESTING → FALSE_CROSS intraday, before either
        confirmation fires, when spot returns to the
        origin side by more than
        SPX_FALSE_CROSS_TOLERANCE_PCT (0.0015) × spot
        beyond the level and holds there for
        SPX_FALSE_CROSS_HOLD_S (60 s).
      TESTING → COOLDOWN at instrument close when still
        TESTING (neither intraday confirmation nor
        false-cross fired). Reason recorded as
        CONFIRMATION_NOT_ACHIEVED_AT_CLOSE. No CONFIRMED
        notification. This resolves the strand case.
      FALSE_CROSS → COOLDOWN immediately; cooldown_until =
        now + SPX_COOLDOWN_S (600).
      CONFIRMED_BREAKOUT → COOLDOWN after notification
        emission.
      CONFIRMED_REVERSAL → COOLDOWN same.
      COOLDOWN → REARMED when now ≥ cooldown_until AND the
        level_id is still present in market_map_current.
      REARMED → FAR | APPROACHING per thresholds on next
        evaluation cycle.
      Any → INVALIDATED when market_map_current advances to a
        map_id that does not contain the level_id.

      Evaluation cadence: FSM evaluated on every accepted
      price tick, on every OpenMarket alert arrival, AND at
      least once every SPX_EVALUATION_CADENCE_S (30) while
      state ∉ { FAR, INVALIDATED }.

9.6.6 Effects: notifications per category map.
9.6.7 Storage: current pointer in SQLite; history in DuckDB.
9.6.8 Transition lock: while state ∈ {TESTING, COOLDOWN} for
      a level_id, inbound OpenMarket alerts for the same
      level_id are dropped (logged, not queued).
9.6.9 SPX_CASH_ONLY phase (16:00–16:15 ET):
      Block new ACTIONABLE_NOW for any thesis whose
        expiration_date == market_date. (Defense-in-depth:
        0DTE and 1DTE are research-only and cannot reach
        ACTIONABLE_NOW; the rule guards any future lane
        change.)
      Do not block existing position management.
      Do not block standard SPX/SPY/QQQ swing-lane signals.
9.6.10 Constants:
       SPX_FALSE_CROSS_TOLERANCE_PCT = 0.0015
       SPX_FALSE_CROSS_HOLD_S        = 60
       SPX_CONFIRMATION_BUFFER_PCT   = 0.0015
       SPX_CONFIRMATION_HOLD_S       = 60
       SPX_APPROACHING_RETREAT_PCT   = 0.005
       SPX_EVALUATION_CADENCE_S      = 30

9.7 Basis Discipline (canonical)

9.7.1 BASES_TOLERANCE_BPS default 15 for cash/index sources.
9.7.2 Reference priority: listed-option underlying, official
      index, other authorized.
9.7.3 Prior session close is not a basis reference.
9.7.4 Basis monitored continuously for the asset class in
      use.
9.7.5 Basis violation logged and flagged.
9.7.6 Basis used in decision path only when within
      tolerance.
9.7.7 Basis record kept per observation.

================================================================================
SECTION 10 — SPREAD DETECTION
================================================================================

10.1 Evidence Tiers 1–4.
10.2 Revaluation Controls: max interval 10 minutes, max
     spot move 1%, max staleness 15 minutes.
10.3 Normalization: similarity floor 0.80 (1:1).

10.4 Structure Types (canonical, single definition)

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

  25 entries. "partial fills" is not a structure — it is a
  fill state tracked on position_fills.

10.5 Tier assignment
      1 = CONFIRMED_SPREAD   full package-level evidence,
                             legs accounted for.
      2 = PROBABLE_SPREAD    package confidently inferred,
                             minor ambiguity.
      3 = POSSIBLE_SPREAD    relational cluster without a
                             confirmed package; standalone
                             legs are retained.
      4 = CONTEXT_ONLY       raw event retained for context;
                             no spread hypothesis.
      Tier is persisted on the thesis and referenced by
      scoring.
10.6 Cluster windows: RELATE events within 10 minutes if
     same structure signature.
10.7 Tier 3 Discipline: Tier 3 cannot suppress standalone
     legs.
10.8 Static Bars: cannot establish a spread.
10.9 Complex Auctions and Cross trades: recorded with
     appropriate confidence.

================================================================================
SECTION 13 — CAPTURE COMPLETENESS
================================================================================

13.1 COMPLETE, PARTIAL, MANUAL_ONLY, UNKNOWN.
13.2 PARTIAL cap 0.70 applied inside weighted sum (§14.1).
13.3 Coverage windows recorded on coverage_windows.
13.4 Coverage influences confidence but never promotes.

================================================================================
SECTION 14 — SCORING, CALIBRATION, CONFIDENCE
================================================================================

14.1 Per-Dimension Adjustments
  14.1.1 Raw score plus confidence per dimension.
  14.1.2 Adjusted = Σ(raw × conf × cov) − penalties.
  14.1.3 No global product.
  14.1.4 Bounded.
  14.1.5 cov is the coverage cap per ARCH Vol 4 §D.1a.

14.2 Global Confidence
  14.2.1 Weighted geometric mean.
  14.2.2 Reliability, not magnitude.
  14.2.3 C_final = min(C_global, C_coverage, C_DQ).
  14.2.4 Display-only. Not the score.

14.3 Separation: independent dimensions never multiplied as
     a global product.
14.4 Decision Sequence: see §8.4.
14.5 Dealer Confidence: per ARCH Vol 4 §H.2.
14.6 Regime Neutral Band: per ARCH Vol 4 §H.4.

14.7 Latency Budget

14.7.1 Print-to-alert latency budgeted per lane:
         TACTICAL_2DTE:       hard cutoff 3000 ms
         SHORT_TACTICAL:      hard cutoff 5000 ms
         SWING:               hard cutoff 10000 ms
         LONGER_HORIZON:      hard cutoff 30000 ms
         Measured from source_event_ts to alert_generated_ts.
         Events exceeding lane cutoff → quality-downgraded
         to C.

         Measurement note: these cutoffs are only meaningful
         once end-to-end latency is measured per provider and
         per channel. The browser-based capture path includes
         provider publication delay, provider UI refresh
         latency, and the humanized dwell/refresh cycle
         (ARCH Vol 3 §E.5–E.7). If measured end-to-end
         latency on the browser path cannot consistently
         beat the TACTICAL_2DTE cutoff, the operator must
         either (a) supply an authorized event/push channel
         for that source, or (b) accept that the
         TACTICAL_2DTE lane will see few passing events and
         document the resulting calibration impact (see
         §14.19.8a). Cutoffs must not be relaxed to hide a
         capture-channel limitation.

14.7.2 Confidence decays with age per ARCH Vol 4 §H.3,
       lane-parameterized.
14.7.3 Freshness thresholds per lane per ARCH Vol 4 §AA.2.

14.8 Composite Dimensions.
14.9 Calibration, §14.9.11 manifest-active.
14.10 Walk-Forward.
14.11 Weight Adjustment.
14.12 Internal Outputs.
14.13 Rules Registry.
14.14 Event Bucket.

14.15 Volatility Indices
  14.15.1 MVS = Model Variance Score. OVR = Option Variance
          Ratio.
  14.15.2 MAD normalization.
  14.15.3 Missing components → renormalize.
  14.15.4 Below MIN_VOL_INDEX_COVERAGE (0.60) → unavailable.

14.16 Model-Free Variance.
14.17 Dealer Hedging Pressure
  14.17.1 H_$ formula per ARCH Vol 4 §D.21.
  14.17.2 H_signed, H_magnitude.
  14.17.3 When hedge_direction opposes, subtract
          HEDGE_PENALTY_DEFAULT × H_magnitude from EV_lower.
          Single application (not also at portfolio gate).
  14.17.4 H_signed is consumed by portfolio gates only as a
          correlation-cluster proxy; it is not re-applied
          to EV_lower at the portfolio gate (single
          application per §14.17.3).
  14.17.5 H_signed changes are logged to the snapshot but do
          not by themselves transition a thesis state.

14.18 Cross-Asset Macro Regime (research, additive).

14.19 Cold-Start Calibration

  14.19.1 Cold-start stages: (A) no calibrator, (B) fallback
          available, (C) scoped calibrator trained.
  14.19.2 Pooled-lane and per-scope are distinct; the pooled
          case is a floor.
  14.19.3 Shadow sampling feeds the pooled case.
  14.19.4 Fallback lookup order: scoped → parent via _ANY →
          none.
  14.19.5 Fallback confidence reduction ×
          FALLBACK_CONFIDENCE_FACTOR (default 0.7).
  14.19.6 Promotion: scoped calibrator replaces fallback when
          MIN_CALIBRATION_N is met for the exact scope key.
  14.19.7 Long-lane proxy labeling: SWING and
          LONGER_HORIZON default to the 1d proxy label with
          a horizon-mismatch penalty until n-day markout
          labels are available.
  14.19.8 Cold-start duration estimate (recomputed per
          §14.19.8a).

  14.19.8a Scope-aware recomputation

     The prior "6–10 weeks for 200 samples" figure assumed a
     single pooled stream. Calibrators are scoped per
     (target, route, dte_lane, horizon, ruleset_version)
     with MIN_CALIBRATION_N = 200 per cell.

     Assume 5–15 raw alerts/day system-wide. After DQ
     filtering, FLOW_ALERT scope, lane restriction, and
     route restriction, the effective per-scope arrival rate
     is typically 0.5–3 events/day for a single active
     lane/route cell.

     Per-scope time to n = 200:
       3 events/day → ~67 trading days (~13 weeks / ~3 months)
       1 event/day  → ~200 trading days (~40 weeks / ~9 months)
       0.5 events/day → ~400 trading days (~18 months)

     EV W/L/C estimation typically adds 4–8 weeks after the
     200-sample threshold.

     Consequence: for a specific (lane, route) cell,
     ACTIONABLE_NOW may be disabled for ~3–18 months from
     first signal, not "2–4.5 months". The prior figure is
     retained only as a pooled-lane optimistic floor and
     must be labeled as such.

     Remediation options:
       - Shadow sampling feeds cold-start calibration as a
         labeled source.
       - Fallback calibrators (parent scope via _ANY) are
         visible under FALLBACK_CONFIDENCE_FACTOR.
       - The operator may extend the research-only posture
         for a lane until calibration is viable.

================================================================================
SECTION 15 — STRATEGY ROUTING, RISK, EXECUTION
================================================================================

15.1 Routes

  Long-call:      IV rank low, VRP low, contango, positive
                  vanna.
  Long-put:       IV rank low, VRP low, contango, negative
                  vanna; bearish direction required.
  Short-put:      IV rank high, VRP high, steep put skew,
                  strike below floor.
  Debit-spread:   pre-earnings.
  Spread-specific: when Tier 1 or Tier 2 structure detected.
  Until route defined: WATCH / NO TRADE.

15.2 Stand-Down: external facts trigger STAND_DOWN.

15.3 Sizing: exact contractual endpoint/tail risk per ARCH Vol 4
     D.5, plus its explicit risk-cost allowance and D.6 lane precedence.
     Never use a finite scenario-grid minimum or a stop-loss threshold
     as contractual maximum loss. Unsupported/unbounded risk blocks sizing.

15.4 Portfolio Risk: cluster caps, correlation, assignment.

15.5 Route-specific exits: ARCH Vol 4 AH is the binding contract.
     Before a route carries exposure, require a verified frozen policy,
     its operational active pointer, resolved absolute deadlines,
     executable fill-identity rules and durable monitoring readiness.
     A handler name alone cannot satisfy exit_handler_exists.
     Preserve premium/theta/IVR/gap seed values until a separately
     approved ruleset changes them. No autonomous order submission.

15.6 Actual fills are authoritative and deduplicated by the
     non-null source execution identity in ARCH Vol 4 AH.4.4.
     Paper fills use its ratio-normalized synchronized depth cap,
     conservative valuation and explicit PAPER namespace.
     An order acknowledgment is never a fill.

15.7 Execution Block: chase and entry rules per lane.

15.8 Dark-Pool Levels: separate structural context.

15.9 DTE Lane Interaction

  Full TACTICAL_2DTE lane contract:
    max_risk_pct_equity         0.005
    quote_freshness_s           15
    voland_freshness_s          900
    confirmation_delay_s        60
    latest_entry_time           15:30 ET
    hold_horizon_hours          6
    chase_max                   0.05
    mandatory_exit_before_0dte  true
    routes                      debit_spread, long_call, long_put
    calibrator_scope            TACTICAL_2DTE

  Sizing precedence: the lane contract's
  max_risk_pct_equity replaces the global BASE_RISK_PCT when
  defined. See ARCH Vol 4 §D.6.

  Snapshot transitions: one immutable append-only row per
  material 0DTE cluster transition (ALERT, MIXED, REVERSAL,
  RETRACTION, EXPIRY, BASIC_SHADOW) per invariant Y.
  Non-ALERT rows do not participate in outcome computation.
================================================================================
SECTION 17 — T+1 OI VERIFICATION
================================================================================

17.1 Fetch settled OI.
17.2 Confirm freshness.
17.3 Persist to chain_snapshots.
17.4 Job Order:
  1. Fetch settled OI.
  2. Confirm freshness. If not fresh: leave PENDING and
     schedule retry; do not persist partial data; do not run
     attribution. Exit.
  3. Persist to chain_snapshots.
  4. Run attribution.
  5. Mark DONE.
17.5 Idempotency: enforced by PRIMARY KEY
    (signal_id, signal_version, horizon, outcome_scope_id)
    on signal_outcomes (SPEC Vol 2 §19.3). DuckDB does not
    support partial unique indexes; the composite PK is the
    canonical idempotency mechanism.
17.6 Thesis Linkage: label update on flow_label.
17.7 FDI Retrospective: retrospective only.

================================================================================
END OF SPEC Vol 3 v2.0.5.1
================================================================================