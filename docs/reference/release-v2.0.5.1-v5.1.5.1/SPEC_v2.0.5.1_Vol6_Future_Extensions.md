# QUANT FLOW SYSTEM — SPECIFICATION v2.0.5.1
## VOLUME 6 — FUTURE EXTENSIONS & ML ROADMAP

Status: informational, non-normative. This volume describes
possible future work. Nothing in this volume is enforced at
v2.0.5.1. Binding contracts remain in Volumes 1–5 and in the
ARCH set. Sections not owned by this volume reference the
owning volume within the 10-file set by section number.

CHANGES FROM v2.0.5
- Header version bump to v2.0.5.1.
- P0-6: reserved shadow_basic_clusters table superseded by
  the snapshot_type = 'BASIC_SHADOW' mechanism on
  zero_dte_cluster_snapshots. §F.4.4 and §F.9 updated
  accordingly.

CHANGES FROM THIS REVIEW (F01)
- §F.9 forward-provisions paragraph rewritten: SQLite
  072–079 and DuckDB 046–049 reserved; SQLite 071 and
  DuckDB 050 are proposed core repairs (ARCH Vol 2 §C.3);
  DuckDB 043–045 remain independently adopted research
  modules. No reserved module is automatically enabled or
  marked applied.

CHANGES FROM v2.0.4
- New Volume 6 introduced at v2.0.5. No prior content.

AUTHORITY
  Nothing in this volume overrides any other volume.
  Where this volume conflicts with Volumes 1–5 or with
  ARCH Volumes 1–4, the other volume wins.
  Anti-detection remains authoritative in ARCH v5.1.5.1
  Vol 3 §F. This volume does not touch it.
  Decision precedence remains authoritative in SPEC v2.0.5.1
  Vol 3 §8.4. This volume does not touch it.

PRINCIPLES
  P1 The deterministic engine is the product. ML and LLM
     layers are optional convenience.
  P2 No model output may affect a decision, a route, a
     size, a target, a stop, or a probability visible to
     the operator, unless promoted through the active
     model manifest with a full audit record.
  P3 Every model is a challenger first.
  P4 Every narrative layer is optional and non-blocking.
  P5 No new infrastructure (feature store, vector DB,
     model server, LLM runtime) is required for v2.0.5.1.

CONTENTS
  F.1  Master Phased Roadmap Matrix
  F.2  Phase A — Deterministic Foundation (current)
  F.3  Phase B — Outcome Collection
  F.4  Phase C — Minimal ML Challenger (LOGISTIC_L2)
  F.5  Phase D — Promote Only on Demonstrated Improvement
  F.6  Phase E — Optional Local Narrative Service
  F.7  Phase F — More Complex ML (only if justified)
  F.8  Prohibitions
  F.9  Forward Provisions in v2.0.5.1
  F.10 Exit Conditions per Phase

================================================================================
F.1 MASTER PHASED ROADMAP MATRIX
================================================================================

  Phase               What you build              ML work              Qwen work
  ------------------  --------------------------  -------------------  ----------
  A: Deterministic    Complete known              None                 None
  foundation          formula/schema fixes;
  (Stages 0–3; now)   deterministic flow funnel,
                      canonical dedup, spread
                      netting, dealer/technical
                      maps, live quote gates;
                      immutable snapshots;
                      outcome storage.

  B: Outcome          Collect route P&L,          Existing score /     None
  collection          target/invalidation         calibrator remains
  (Early Stage 4)     outcomes, 0DTE markouts,    champion.
                      T+1 OI labels, rejected
                      shadow samples, and
                      market-regime context.

  C: ML               Add one local               Train L2 logistic    None
  challenger          ProbabilityModel            regression with
  (Stage 4, research  implementation and          10–12 structured
  only)               prediction audit records.   features; run
                                                  shadow-only.

  D: Validate and     Champion vs challenger      Promote only after   None
  promote             walk-forward comparison.    better Brier, log
  (Later Stage 4)                                 loss, calibration,
                                                  and precision at
                                                  same volume across
                                                  3 consecutive
                                                  chronological
                                                  windows.

  E: Optional local   Add optional                No direct            Morning
  Qwen                LocalNarrativeService       probability role.    explanation,
  (Stage 5)           after the immutable                              ad-hoc
                      snapshot.                                       explanation,
                                                                      report
                                                                      compression;
                                                                      post-close
                                                                      summaries.

  F: More complex     Add second challenger       Small gradient-      Possible
  ML only if          only after logistic         boosted tree;        structured
  justified           plateaus.                   shadow-first.        catalyst
  (future research)                                                   extraction.

  Avoid               No separate AI platform,    No neural network,   No Qwen-
  (all stages)        feature store, vector DB,   RL, per-ticker       generated
                      or real-time LLM service.   model, or online     buy/sell
                                                  self-modifying       decisions
                                                  model.               or confidence
                                                                       percentages.

================================================================================
F.2 PHASE A — DETERMINISTIC FOUNDATION (CURRENT)
================================================================================

What you build
  Complete the v2.0.5.1 / v5.1.5.1 corrections and the
  Stages 0–3 deliverables.

ML work
  None.

Qwen work
  None.

Exit condition
  AnalysisSnapshotBuilder passes §2.9.4 determinism tests.
  signal_outcomes reconstruct from raw_provider_events.
  zero_dte_cluster_outcomes populate on horizon close.
  Acceptance suite (Vol 4 §20, ARCH V3 §F.Q) passes.
  No feature leakage paths exist.

================================================================================
F.3 PHASE B — OUTCOME COLLECTION
================================================================================

What you build
  Sustained outcome collection across all live lanes.

ML work
  None. Existing deterministic score and calibrator remain
  the only model in the decision path.

Qwen work
  None.

Exit condition
  The chosen model scope key — (target, route, dte_lane,
  horizon, ruleset_version) — MUST itself satisfy
  N_scope >= max(300, 20 * p), where p is the number of
  fitted features (for p=12, N_scope >= 300; for p=25,
  N_scope >= 500). No cross-lane or cross-scope pooling is
  accepted for the activation gate. The chosen scope must
  also contain at least 75 positive and 75 negative
  outcomes. Per-scope arrival-rate implications remain per
  §14.19.8a; pooled counts may be reported for research
  purposes but never substitute for the per-scope gate.
  Route P&L, target/invalidation hits, 0DTE markouts, and
  T+1 OI labels stored. Rejected shadow samples captured
  per Vol 2 §7.4.

Note
  §14.19.8a documents that per-scope arrival rates are
  0.5–3 events/day for a single lane/route cell. Per-scope
  thresholds can take 3–18 months. The pooled count is a research reference only; activation requires the per-scope gate to pass;the
  max(300, 20p) formula scales with feature count.

================================================================================
F.4 PHASE C — MINIMAL ML CHALLENGER
================================================================================

F.4.1 Model configuration

    model_family: LOGISTIC_L2
    initial_feature_count: 10–12
    training: chronological walk-forward
    inference: pure local function
    role: CHALLENGER only

F.4.2 Suggested starting features

  Category             Feature                     Notes
  -------------------  --------------------------  -------------------
  Flow                 Flow Strength               Base intensity
  Flow                 Directional Share           Dominant side
  Flow                 Premium Percentile          Normalized premium
  Flow                 Delta Dollar Percentile     Normalized delta $
  Flow                 Independent Event Count     Unique prints
  Dealer / Price       Dealer Alignment            Level orientation
  Dealer / Price       Signed Hedge Pressure       Directional
  Dealer / Price       Distance to Gamma Flip      In sigma
                       in sigma
  Dealer / Price       Price vs VWAP / AVWAP       % variance
  Dealer / Price       Target/Invalidation         Reward/risk ratio
                       reward-risk
  Execution / Context  Chase Percentage            Aggressor momentum
  Execution / Context  Relative Quote Width        Spread thickness
  Execution / Context  Time Remaining              Until close
  Execution / Context  0DTE Line                   Boundary flag
  Execution / Context  Market Regime               Macro vol state

  Controlled interaction terms:
    X1 = FlowStrength × DealerAlignment
    X2 = DirectionalShare × PriceConfirmation
    X3 = DistanceToTarget /
         max(DistanceToInvalidation, ε)

  Prohibited in features:
    ticker identity, free-form text, raw provider name, or
    any Qwen-derived quantity.

F.4.3 Primary labels

  Workflow              Initial ML target
  --------------------  ----------------------------------------
  Normal option flow    Strategy profitable after spread,
                        fees, and modeled slippage over the
                        route horizon.
  0DTE cluster          Target reached before invalidation
                        before market close.
  Diagnostic only       Direction correct; opening confirmed;
                        flow-led vs price-led.

  For 0DTE, mathematical target:
    Y_0DTE = 1 if Target reached before Invalidation, else 0.

F.4.4 Database extensions

  The active_model_manifest gains a model_role column
  (CHAMPION / CHALLENGER / SHADOW). See ARCH Vol 2 §C.1.
  calibration_model gains model_family,
  feature_names_json, preprocessor_json, minority_class_n.
  See ARCH Vol 2 §C.2.

  Reserved DDL — model_predictions
    Not created at v2.0.5.1. Applied when the first
    challenger ships in Phase C.

    CREATE TABLE model_predictions (
        prediction_id TEXT PRIMARY KEY,
        analysis_snapshot_id TEXT NOT NULL,
        model_id TEXT NOT NULL,
        model_role TEXT NOT NULL
            CHECK(model_role IN ('CHAMPION','CHALLENGER','SHADOW')),
        target TEXT NOT NULL,
        p_raw DOUBLE,
        p_calibrated DOUBLE,
        p_lower DOUBLE,
        abstain_reason TEXT,
        model_features_hash TEXT NOT NULL,
        created_at BIGINT NOT NULL
    );
    CREATE INDEX idx_model_pred_snapshot
        ON model_predictions(analysis_snapshot_id);
    CREATE INDEX idx_model_pred_model
        ON model_predictions(model_id, created_at);

    Migration number reserved: duckdb 046 (within the
    046..049 RESERVED block). DuckDB 042 was reassigned
    to AH (exit_evaluations, ivr_history); 043–045 are
    reserved for SPEC Vol 7 (AE/AF/AG).

  BASIC cluster history
    Reserved DDL shadow_basic_clusters is superseded by
    P0-6: BASIC episodes now write a final snapshot to
    zero_dte_cluster_snapshots at expiry with
    snapshot_type = 'BASIC_SHADOW', alert_grade =
    'BASIC', and alert_ts = NULL. No separate shadow table
    is created. See SPEC
    Vol 2 §19.6 invariant Y and §19.3
    zero_dte_cluster_snapshots.

  Reserved note — narrative_annotations
    Optional future home for LocalNarrativeService output
    (see §F.6 and SPEC Vol 5 §O.16). Not required; the
    primary supported location remains
    report_runs.rendered_payload_json key "narrative".

  Infrastructure note
    No model server, distributed training environment, or
    new database engine is required.

F.4.5 Exit condition
  Challenger scores every candidate during shadow testing.
  Champion remains the sole decision source. No challenger
  output is visible in any notification, decision, or
  rendered report.

================================================================================
F.5 PHASE D — PROMOTE ONLY ON DEMONSTRATED IMPROVEMENT
================================================================================

Promotion requirements (all must hold during shadow
testing):

  Brier score           Better than current champion.
  Log loss              Better than current champion.
  Calibration error     No worse than current champion.
  Precision             Better at the exact same alert
                        volume/count.
  False positives       Lower or unchanged.
  Chronology            Measurable improvement in 3
                        consecutive walk-forward windows.
  Regime stability      No major failures in high-vol,
                        low-vol, or trend regimes.
  Feature ablation      Flow and dealer features show clear
                        incremental value.
  Replay integrity      Identical inputs + code version →
                        identical prediction.

State rule until promotion:
  production_decision = current_champion
  challenger_result   = stored_for_research_only

Promotion path
  Through existing active_model_manifest workflow with full
  audit record. Every promotion is auditable.

================================================================================
F.6 PHASE E — OPTIONAL LOCAL NARRATIVE SERVICE
================================================================================

Purpose
  Semantic narration of an immutable Analysis Snapshot.
  Plain-English summaries, explanations, structured text
  extraction. Never numeric.

Interface
  Declared in SPEC Vol 5 §O.16 (RESERVED, DISABLED).
  Config key: observability.narrative.enabled (default
  false). When false, the service is not invoked.

Approved use cases
  - Morning-report plain-English summaries.
  - Ad-hoc report explanations.
  - Compressing detailed evidence payloads before Muse
    receives them.
  - Post-close false-positive grouping.
  - Later, structured catalyst classification strictly in
    shadow mode.

Prohibited uses
  - Buy/sell decisions.
  - Trade probability calculations.
  - Gamma or vanna calculations.
  - Target or invalidation level assignments.
  - Route selection.
  - Position sizing calculations.
  - Upgrading WATCH alerts to ACTIONABLE_NOW.

Performance rule
  Real-time flow and 0DTE alerts never wait for or rely on
  narration.

Exit condition
  Narration failure never delays an alert and never changes
  decision, route, target, stop, size, or probability.

================================================================================
F.7 PHASE F — MORE COMPLEX ML (ONLY IF JUSTIFIED)
================================================================================

What you build
  A second challenger — small gradient-boosted tree — only
  after logistic-regression performance plateaus.

ML work
  Shadow-first. Same promotion rules as Phase D.

Qwen work
  Possible structured catalyst extraction in shadow mode.

Exit condition
  Demonstrated incremental holdout improvement over
  logistic regression, measured under the same promotion
  rules as Phase D.

================================================================================
F.8 PROHIBITIONS (ALL STAGES)
================================================================================

  No separate AI platform.
  No feature store.
  No vector database.
  No real-time LLM service in the decision path.
  No neural network.
  No reinforcement learning.
  No per-ticker model.
  No online self-modifying model.
  No Qwen-generated buy/sell decisions or confidence
  percentages.
  No challenger output reachable by any decision-path code.

================================================================================
F.9 FORWARD PROVISIONS IN v2.0.5.1
================================================================================

Reserved now (not active) so future work does not require
touching the decision path:

  1. Migration numbers 072-079 (SQLite) and 046-049
     (DuckDB) are reserved. SQLite 071 and DuckDB 050 are
     proposed core repairs in ARCH Vol 2 §C.3.
     SQLite 065-070 and DuckDB 038-042 retain their recorded
     core/AH roles. DuckDB 043-045 remain reserved for the
     independently adopted SPEC Vol 7 modules AE/AF/AG.
     No reserved module is automatically enabled or marked applied.
  2. active_model_manifest.model_role column
     (CHAMPION / CHALLENGER / SHADOW). See ARCH Vol 2
     §C.1 and ARCH Vol 1 §AI.17.
  3. calibration_model extended metadata (model_family,
     feature_names_json, preprocessor_json,
     minority_class_n). See ARCH Vol 2 §C.2 and SPEC Vol 2
     §19.3.
  4. model_predictions table reserved (DDL in §F.4.4;
     migration 046 reserved).
  5. BASIC_SHADOW snapshot_type reserved in
     zero_dte_cluster_snapshots (P0-6). See SPEC Vol 2
     §19.3 and §19.6 invariant Y.
  6. Invariants AI, AJ, AK, AM in SPEC Vol 2 §19.6.
  7. LocalNarrativeService interface stub in SPEC Vol 5
     §O.16.
  8. ZERO_DTE ticker scope realized through symbol_filter
     workflow_scope = 'ZERO_DTE_CLUSTER'. See SPEC Vol 1
     §7.6 and ARCH Vol 1 §AI.3.

Deferred (do NOT add now):
  - model_predictions table creation.
  - shadow_basic_clusters table (superseded by P0-6).
  - narrative_annotations table.
  - Feature store, vector DB, feature registry.
  - Any LLM runtime.
  - Second challenger or GBM scaffolding.
  - Any change to §8.4 (decision precedence) or §S.6
    (decision selector).
  - Any change to ARCH Vol 3 §F (frozen anti-detection)
    beyond the P0-8 authorization provision.

================================================================================
F.10 EXIT CONDITIONS PER PHASE
================================================================================

  Phase A   Determinism tests pass; outcomes reconstruct.
  Phase B   300 pooled usable outcomes; 75/75 class split
            for chosen scope.
  Phase C   Challenger shadow-scores every candidate;
            champion unchanged.
  Phase D   Promotion only after all F.5 criteria met and
            audit-recorded.
  Phase E   Narration never delays alerts; failure
            fail-opens.
  Phase F   Demonstrated incremental holdout improvement
            over logistic.

================================================================================
END OF SPEC Vol 6 v2.0.5.1
================================================================================