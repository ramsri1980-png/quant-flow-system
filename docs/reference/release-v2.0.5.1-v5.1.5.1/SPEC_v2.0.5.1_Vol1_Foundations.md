# QUANT FLOW SYSTEM — SPECIFICATION v2.0.5.1
## VOLUME 1 — FOUNDATIONS

Status: self-contained for the sections this volume owns.
Sections not owned by this volume reference the owning
volume within the 10-file set by section number. Every
normative value and rule has a single home in the set;
references resolve within the set.

CHANGES FROM v2.0.5
- P0-1: §2.13.5 note added. signal_valid (SPEC Vol 3
  §8.1a) does not include portfolio, market hours, or
  live entry.
- P0-2: §7.6 rewritten. ZERO_DTE_CLUSTER workflow scope
  replaces the parallel ticker allowlist. symbol_filter
  is the single enforcement point.
- P0-3: §2.20.7.2 and §22.3 use lifecycle-only
  cluster_state. BASIC is a grade, never a state.
- P0-3: episode_id uses first_qualifying_canonical_event_id
  and ruleset_version; no |seq=N fallback.
- P0-6: BASIC episodes write a BASIC_SHADOW snapshot at
  expiry (no push).
- P0-7: §22.4 manifest deduplicated; §22.6 reference
  qualification rule added.
- AH integrated into ARCH V4; AE/AF/AG moved to
  SPEC Vol 7 (Research Addenda). Document map and
  manifest updated to 11-file set.

CHANGES FROM THIS REVIEW (S1-01, S1-02, S1-03)
- §2.20.7.2 and §2.20.7.8 BASIC_SHADOW instructions now
  carry alert_grade = 'BASIC' and alert_ts = NULL so that
  the SQL CHECK and the invariant Y prose agree.
- Invariant Y rewritten: ALERT rows require non-null
  alert_grade and non-null alert_ts; BASIC_SHADOW requires
  alert_grade='BASIC' and alert_ts=NULL; MIXED/REVERSAL/
  RETRACTION/EXPIRY require both NULL; transition_ts and
  snapshot_type remain NOT NULL.

CHANGES FROM v2.0.4
- All §-level content restated inline; no "per prior" placeholders.
- 0DTE cluster tier hardened: HIGH_CONFLUENCE requires dealer
  map age ≤ 300 s; MEDIUM may use ≤ 900 s with stale label.
- OpposingShare defined as min(B,R)/(B+R).
- Percentile baseline and cold-start policy defined.
- Market-phase, max-age and per-member latency gates added.
- RAPIDFIRE_FAMILY / REPEATER_FAMILY aliases defined.
- Default symbol_filter rows pinned.
- 0DTE grade/state/episode separated in schema.
- Cluster member history table added.
- Notification state enum lowercase canonical.
- DQ residuals (HTTP/3 unknown, provider telemetry unknown)
  reclassified as standing status lines, not alarms.

================================================================================
SECTION 1 — VISION, SCOPE, PRINCIPLES
================================================================================

1.1 Vision

A local, single-operator options flow research system that
observes pre-filtered flow signals, validates them against
dealer positioning, market structure, and market regime,
classifies them probabilistically, and delivers decisions
through three workflows — a real-time flow alert, a morning
action brief, and an ad hoc symbol report — all derived from
one shared thesis, one deterministic analysis snapshot, and
one market map. The system presents itself as a human
operator to sources that expect human interaction. Runs
entirely on one Linux machine.

Cost posture: zero recurring cost beyond data subscriptions
and the notification/backup infrastructure (Resend, Mailgun,
Cloudflare, encrypted offsite backup). Free sources cover
price and technical context; paid sources are queried only
when triggered.

Flow signal source: the pre-filtered Alerts view of the flow
providers. Not raw flow tapes, heat maps, or OI tables.

0DTE posture: same-day expiry clusters produce real-time
tactical intelligence at two immediate-delivery tiers
(MEDIUM_CONFLUENCE, HIGH_CONFLUENCE). They do not produce a
route, size, or ACTIONABLE_NOW state.

1.2 Scope

1.2.1 Observe flow signals from authorized sources' Alerts
      views.
1.2.2 Derive a canonical event representation from any
      source's native format.
1.2.3 Aggregate independent events into a Symbol Thesis.
1.2.4 Build one immutable Analysis Snapshot per decision
      moment.
1.2.5 Build one immutable Market Map per symbol per market
      session.
1.2.6 Classify each thesis into four independent
      probabilistic dimensions.
1.2.7 Detect when multiple events belong to a single multi-
      leg structure.
1.2.8 Score with per-dimension confidence propagation;
      calibrate to probabilities over time.
1.2.9 Route through strategy eligibility and portfolio risk
      gates at position level, not leg level.
1.2.10 Deliver decisions through three renderers sharing one
       decision.
1.2.11 Snapshot chains, greeks, OHLCV daily into a durable
       store.
1.2.12 Verify next-day OI and record as learning labels.
1.2.13 Present itself as a human at every network, protocol,
       and behavioral layer.
1.2.14 Isolate capture activity from analytical.
1.2.15 Use free price sources and native alert triggers to
       reduce paid-source calls.
1.2.16 Maintain a scope-separated Dealer Level Map.
1.2.17 Expose a documented operator control plane with audit
       trail.
1.2.18 Maintain basis discipline.
1.2.19 Maintain a Technical Level Map.
1.2.20 Restrict automated access to authorized sources.
1.2.21 Detect same-symbol multi-strike 0DTE clusters at
       real-time tactical intelligence tiers, without route
       selection or ACTIONABLE_NOW.

1.3 Non-Goals

1.3.1  Place orders or execute autonomously.
1.3.2  Redistribute provider data.
1.3.3  Multi-tenant.
1.3.4  LLM between raw observations and decisions.
1.3.5  Probability before calibration.
1.3.6  Generic market recap in morning brief.
1.3.7  Invent a flow thesis from dealer/chart context.
1.3.8  Query undocumented provider interfaces.
1.3.9  Autonomously replace UI-session acquisition with
       undocumented APIs.
1.3.10 Use a real-time perp price as if it were spot without
       a basis check.
1.3.11 Automate any source whose terms do not permit it.
1.3.12 Automate CAPTCHA or challenge solving.
1.3.13 Ingest full raw flow tapes, heat maps, or OI tables.
1.3.14 Select a route, size, or issue an order instruction
       for a 0DTE cluster.

1.4 Governing Principles

1.4.1  Correctness of a number outranks every other concern.
1.4.2  Observed facts, inferences, and decisions are never
       conflated.
1.4.3  Confidence propagates per-dimension, not as a global
       product.
1.4.4  Thresholds apply to calibrated lower-bound quantities.
1.4.5  Capital preservation outranks signal capture.
1.4.6  The numeric path is deterministic.
1.4.7  Kernels are pure and test-first.
1.4.8  Only authorized data is used.
1.4.9  Fail closed, log loudly.
1.4.10 Behave as a human at every layer.
1.4.11 Capture is isolated from analysis.
1.4.12 Every decision is auditable and versioned.
1.4.13 Money is stored as integer minor units.
1.4.14 Decision-critical state survives analytical-store
       unavailability.
1.4.15 Free sources are used for price and technical
       context; paid sources only when triggered.
1.4.16 One thesis, one snapshot, three presentations.
1.4.17 Reports are operating plans, not market recaps.
1.4.18 No executable recommendation before a live quote.
1.4.19 Provider queries are value-of-information gated.
1.4.20 DTE lanes are explicit.
1.4.21 Market structure is defined once in the Market Map
       and consumed by all workflows.
1.4.22 The gamma flip is dual-sourced; disagreement is a
       first-class outcome.
1.4.23 No hard-coded price source in the decision path.
1.4.24 Price observations record source, basis, and
       synthetic-proxy status independently.
1.4.25 Executable prices are stored as integer minor units.
1.4.26 The operator control plane is explicit, audited, and
       never bypasses gates.
1.4.27 Anti-detection is the frozen baseline defined in
       ARCH v5.1.5.1 Vol 3 §F. That volume is authoritative.
1.4.28 Structural dealer levels and tactical dealer levels
       are never merged into one view.
1.4.29 Static dealer bars cannot establish a spread; only
       Tier 1 or Tier 2 evidence suppresses standalone legs.
1.4.30 A perp/proxy price is never decision-eligible for
       ACTIONABLE_NOW regardless of basis.
1.4.31 Every "unique active X" invariant names its
       enforcement mechanism.
1.4.32 Anti-detection applies only to sources authorized for
       automation (see §11.0 of SPEC Vol 4).
1.4.33 Named numeric constants are defined exactly once in
       ARCH v5.1.5.1 Vol 1 §AI.3 and referenced by name
       elsewhere. A "named constant" is a value declared in
       AI.3 as UPPER_SNAKE_CASE. Embedded values (numeric
       literals inside formulas, lane-property tables, log-
       normal parameters, or other inline uses) are restated
       at each use and are subject to internal consistency
       only. Enforced by a document-level lint that scans for
       UPPER_SNAKE_CASE tokens.
1.4.34 A functional-prefix rule stated in prose is CI-
       enforced (§3.6). Prose alone is not a constraint.
1.4.35 0DTE cluster alerts are labeled MEDIUM_CONFLUENCE or
       HIGH_CONFLUENCE. These are evidence grades, not
       calibrated probabilities.

================================================================================
SECTION 2 — ARCHITECTURE AND SHARED SERVICES
================================================================================

2.1 Component Model

2.1.1  Ingestion Adapters
2.1.2  Raw Event Archive
2.1.3  Canonicalizer
2.1.4  Quality Gateway
2.1.5  Candidate Engine
2.1.6  Enrichment Adapters
2.1.7  Structure Detector
2.1.8  Classifiers
2.1.9  Scoring Engine
2.1.10 Router & Risk Gate
2.1.11 Signal Ledger
2.1.12 Delivery Outbox
2.1.13 Alert Formatter
2.1.14 Muse Facade
2.1.15 Storage Layer
2.1.16 Capture Worker
2.1.17 Capture-State IPC Bridge
2.1.18 Rhythm Scheduler
2.1.19 Notification Service
2.1.20 LivePriceProviderAdapter
2.1.21 Alert Trigger Ingest
2.1.22 SymbolThesisService
2.1.23 AnalysisSnapshotBuilder
2.1.24 ProviderQueryPlanner
2.1.25 DealerContextCache
2.1.26 DealerLevelMapService
2.1.27 TechnicalLevelService
2.1.28 ReportRenderers
2.1.29 OperatorControlPlane
2.1.30 MarketMapService
2.1.31 ListedOptionQuoteAdapter
2.1.32 PayoffKernel
2.1.33 ContextReconciler
2.1.34 ZeroDteClusterDetector
2.1.35 Operations

2.2 Runtime Isolation

2.2.1  Analytical process: quantd.
2.2.2  Capture process: provider_capture_worker.
2.2.3  Rhythm process: human_rhythm_scheduler.
2.2.4  Capture MUST NOT open stores directly.
2.2.5  Analytical MUST NOT launch browser automation.
2.2.6  Capture MUST NOT hold master vault token.
2.2.7  Analytical exposes localhost/Unix-socket endpoint.
2.2.8  Capture failure MUST NOT interrupt analytical.
2.2.9  Rhythm failure MUST NOT interrupt analytical.
2.2.10 All shared services live in the analytical process.
2.2.11 Only quantd writes to SQLite or DuckDB.
2.2.12 Operator mutations go through quantctl → quantd.

2.3 Capture-State IPC Contract

2.3.1  Capture emits typed state events.
2.3.2  Event types: session-opened, session-refreshed,
       session-closed, cookie-expiry-updated,
       engine-health-updated, engine-preference-changed,
       provider-state-changed, coverage-window-opened,
       coverage-window-closed, human-rhythm-state-entered,
       human-rhythm-state-left, heartbeat,
       alert-cycle-started, alert-cycle-completed,
       alert-item-configured, alert-item-removed,
       provider-observation-submitted, fingerprint-verified,
       challenge-detected, credential-request.
2.3.3  Each carries: type, provider/session_id, monotonic
       sequence, timestamp, payload, shared-secret token.
2.3.4  Analytical validates, idempotent applies, persists.
2.3.5  Duplicates on (type, id, seq) are ignored.
2.3.6  State reconciled on startup.
2.3.7  Stale sequence accepted; discontinuity logged.
2.3.8  No arbitrary SQL, paths, URLs.
2.3.9  provider-observation-submitted carries event_id,
       provider, source_ts, payload_hash, schema_version,
       authorization_id, source_trace_id, spool_ref or
       bounded_payload.
2.3.10 Capture prunes spool after quantd ACK.
2.3.11 fingerprint-verified carries session_id,
       wire_fp_hash, self_report_hash, verdict,
       mismatches_json.
2.3.12 challenge-detected carries provider, session_id, url,
       pattern_matched.
2.3.13 credential-request carries provider, session_id,
       purpose.

2.4 Data Flow

Trading pipeline:
  Source (Alerts view) → Adapter → Raw Event → Archive →
  Canonicalizer → Dedup → Quality → Candidate →
  (ProviderQueryPlanner gate) → Enrichment

Enrichment produces immutable references:
  DealerLevelMapService    → dealer_map_id
  TechnicalLevelService    → technical_snapshot_id
  LivePriceProviderAdapter → price_observation_id
  ListedOptionQuoteAdapter → option_quote_observation_id,
                             package_quote_observation_id

Map composition:
  dealer_map_id + technical_snapshot_id + price_observation_id
  + volatility + event context
  → MarketMapService → MarketMapSnapshot (map_id)

Then:
  structure → classifiers → scoring → router/risk
  → SymbolThesisService
  → AnalysisSnapshotBuilder
  → Signal Ledger + Outbox → Renderers → Delivery

0DTE cluster pipeline (parallel, non-executable):
  Alerts view → ZeroDteClusterDetector → zero_dte_cluster_current
  → zero_dte_cluster_snapshots (append-only)
  → renderers (immediate Discord + email at MEDIUM or HIGH)
  → zero_dte_cluster_outcomes (post-horizon markouts)

Ownership invariants:
  analysis_snapshot.dealer_map_id ==
    market_map_snapshot.dealer_map_id
  Current pointer rows reference immutable historical
  observation IDs.

Alert triggers:
  OpenMarket fires → Discord + email → listener →
  notification → SPX crossing state machine → optional
  VolLand escalation → optional thesis re-evaluation.

2.5 Component Contracts

Each component publishes: inputs, outputs, preconditions,
postconditions, invariants, failure modes, idempotency
semantics, timing budget. Contracts are self-contained per
component in this volume or its owning volume.

2.6 Deployment Model

2.6.1  USB-SSD root preferred; USB-flash discouraged.
2.6.2  External SATA III SSD, LUKS-encrypted, ext4.
2.6.3  Encrypted offsite backup.
2.6.4  Named Cloudflare Tunnel.
2.6.5  Cloudflare Access.
2.6.6  No open inbound ports.

2.7 External Interfaces

2.7.1  Muse via Tunnel + Access.
2.7.2  Discord webhook.
2.7.3  Provider adapters over HTTPS.
2.7.4  Bitwarden.
2.7.5  Offsite backup.
2.7.6  Resend + Mailgun.
2.7.7  Hyperliquid WebSocket via LivePriceProviderAdapter.
2.7.8  OpenMarket browser + webhook.
2.7.9  Authorized listed-option quote source.

2.8 SymbolThesisService

2.8.1 Purpose: aggregate independent flow events into one
      Symbol Thesis.
2.8.2 Thesis Identity:
      (ticker, expected_direction, dte_lane,
       structure_signature, target_horizon)
2.8.3 Fields: thesis_id, ticker, expected_direction,
      dte_lane, structure_signature, target_horizon, state,
      first_seen, last_seen, independent_event_count,
      corroborating_source_count, supporting_event_count,
      cumulative_premium_mills, opposite_flow_premium_mills,
      paired_opposite_thesis_id, contract_count,
      expiration_concentration, structure_state,
      evidence_tier, best_data_quality, flow_label,
      latest_snapshot_id, latest_signal_id,
      latest_signal_version, updated_at.
2.8.4 Aggregation Rules:
      2.8.4.1 First matching event creates thesis in
              CANDIDATE.
      2.8.4.2 Corroboration (same exchange event,
              cross-source dedup) increments
              corroborating_source_count; does NOT increment
              independent count; does NOT increase premium.
      2.8.4.3 Independent matching event (same direction,
              distinct exchange event) increments
              independent_event_count and
              cumulative_premium_mills.
      2.8.4.4 Supporting-evidence event (distinct event,
              cross-direction supportive) increments
              supporting_event_count and adds premium to
              cumulative_premium_mills.
      2.8.4.5 Opposite-direction event updates
              opposite_flow_premium_mills on the SAME
              thesis. If a separate opposite-direction
              thesis exists with the same key parts except
              direction, the event updates THAT thesis
              instead and the original thesis's
              paired_opposite_thesis_id is set.
      2.8.4.6 DTE lane change: new thesis; old expires.
      2.8.4.7 Material change writes thesis_versions.
2.8.5 State Transitions: gated by §8 of SPEC Vol 3.
2.8.6 Concurrency: receipt order; same-key coalescing
      within 100 ms.
2.8.7 Expiration: 5 trading days inactivity; 0DTE lane
      cross; horizon pass.
2.8.8 on_dealer_map_rollover: coalesced per ticker,
      GLOBAL budget, same-state → snapshot only.

2.9 AnalysisSnapshotBuilder

2.9.1 Purpose: build one immutable, reproducible decision
      snapshot.
2.9.2 Inputs: all immutable IDs plus market_open, all
      supplied by caller.
2.9.3 Outputs: the snapshot record (see ARCH Vol 4 §S.7).
2.9.4 Determinism:
      2.9.4.1 Pure with respect to inputs.
      2.9.4.2 No wall-clock reads except as_of.
      2.9.4.3 No random draws outside as_of-seeded PRNG.
      2.9.4.4 Same inputs + versions → byte-identical.
      2.9.4.5 Does NOT mutate external state.
      2.9.4.6 Does NOT make provider calls.
      2.9.4.7 Does NOT depend on prior outputs.
      2.9.4.8 Builder MUST NOT call any function whose name
              begins with fetch_, get_current_, or
              read_pointer_. Enforced by document-level lint
              plus AST lint in the code repository.
2.9.5 Cross-Workflow Invariant: same analysis_snapshot_id
      → same decision across workflows.
2.9.6 Storage: DuckDB analysis_snapshots.
2.9.7 Route-Selection Order per ARCH Vol 4 §S.5.

2.10 ProviderQueryPlanner

2.10.1 Interface: plan(thesis, workflow_scope) → query
       plan.
2.10.2 Pools per (provider, market_date):
       FLOW_ALERT (60% reserve), MORNING_AD_HOC (40%
       shared), GLOBAL (separate ceiling).
2.10.3 Pre-market borrow ≤ BUDGET_PREMARKET_BORROW_PCT.
2.10.4 SPX_INTRADAY draws from FLOW_ALERT.
2.10.5 ZERO_DTE_CLUSTER draws from FLOW_ALERT.
2.10.6 Value-of-information gate; no decorative queries.
2.10.7 Cache-hit preferred.
2.10.8 Queries are recorded in provider_query_budget per
       (provider, market_date, thesis_id, query_type,
       workflow_scope).

2.10a LivePriceProviderAdapter

2.10a.1 Purpose: provide decision-grade spot.
2.10a.2 Interface: get_spot(ticker) → price_observation_id.
2.10a.3 Source priority: listed-option underlying, official
        index, then authorized free sources.
2.10a.4 Quality flags recorded per observation.
2.10a.5 Instrument mapping recorded.
2.10a.6 Health monitored; failure → DEGRADED.

2.11 DealerContextCache

2.11.1 Purpose: cache dealer snapshots to avoid redundant
       provider calls.
2.11.2 TTLs per lane.
2.11.3 Invalidation on corporate action, spot move, IV move.
2.11.4 Read-only for detector and builders.
2.11.5–2.11.9 as documented in ARCH Vol 4 §U.

2.11A DealerLevelMapService

2.11A.1 Purpose: produce a scope-separated Dealer Level Map.
2.11A.2 Inputs: DealerContextCache, spot, calendar.
2.11A.3 Output: dealer_map_id (immutable).
2.11A.4 Level roles:
        POSITIVE_GAMMA_SUPPORT, POSITIVE_GAMMA_RESISTANCE,
        POSITIVE_GAMMA_PIN, NEGATIVE_GAMMA_ACCELERATOR,
        LOW_EXPOSURE_AIR_POCKET, VANNA_IV_UP_FLOW_LEVEL,
        VANNA_IV_DOWN_FLOW_LEVEL, PAIRED_EXPOSURE_ZONE,
        CONTEXT_ONLY.
2.11A.5 Level lifecycle: NEW, STABLE, STRENGTHENING,
        WEAKENING, MIGRATING, DISAPPEARED, EXPIRED.
2.11A.6–2.11A.15 as documented in ARCH Vol 4 §AB.

2.12 ReportRenderers

2.12.1 Three renderers: flow_alert, morning, ad_hoc.
2.12.2 Renderers cannot upgrade a decision.
2.12.3 Renderers read snapshot; do not write to it.
2.12.4 Renderer non-upgrade obligation is CI-enforced
       (§3.6).
2.12.5 Renderers read the notification table for Muse.

2.13 Shared Decision State Machine

2.13.1 Twelve decision states; authoritative in SPEC Vol 3
       §8.4.
2.13.2 States: NO_ACTIVE_FLOW_THESIS, CANDIDATE, WATCH,
       VALIDATED_PENDING_ENTRY, ACTIONABLE_NOW,
       PORTFOLIO_BLOCKED, ENTRY_UNAVAILABLE, STAND_DOWN,
       INVALIDATED, RETRACTED, EXPIRED, COMPLETED.
2.13.3 Precedence per SPEC Vol 3 §8.4.
2.13.4 Conflict resolution per SPEC Vol 3 §8.4.
2.13.5 signal_valid (SPEC Vol 3 §8.1a) does NOT include
       portfolio, market hours, or live entry. Those are
       evaluated separately per SPEC Vol 3 §8.4.
2.13.6 Terminal theses never routed.
2.13.7 Decision is written to signal_versions.

2.14 Workflow 1 — Real-Time Flow Alert

2.14.1 Trigger: canonical event passes quality + candidate.
2.14.2 Provider status mapping includes:
         RAPIDFIRE         red-highlighted rapid-fire
         REPEATER          red-highlighted repeated flow
         STEADY            yellow steady flow
         and their bearish analogs.
2.14.3 Mapping is versioned. Unknown mapping fails closed
       for the strong alert and for the 0DTE cluster tiers.
2.14.4–2.14.9 per the pipeline in §2.4.

2.14a 0DTE Cluster Signal Path

2.14a.1 Alerts view scanned continuously by
        ZeroDteClusterDetector.
2.14a.2 Basic cluster (see §2.20.7.2) stored silently.
2.14a.3 MEDIUM_CONFLUENCE gates pass → immediate Discord +
        email (category zero-dte-flow-cluster).
2.14a.4 HIGH_CONFLUENCE gates also pass → immediate
        upgrade (category zero-dte-dealer-confirmed). If
        already high at detection, send only the high alert.
2.14a.5 No route, size, or ACTIONABLE_NOW.
2.14a.6 Reversal and retraction emit corresponding
        categories.
2.14a.7 Cluster added to morning brief Prior-Day 0DTE
        Research line; ad hoc report dealer-context; next-
        day dealer-context enrichment queue.

2.15 Workflow 2 — Morning Action Brief

2.15.1–2.15.3 per pipeline.
2.15.4 Required Sections:
       A. Decision Summary.
       B. Market Playbook.
       C. Carryover Thesis Board.
       D. 2DTE and Expiration-Risk Board.
       E. Portfolio and Capacity.
       F. Prior-Day Audit — includes Prior-Day 0DTE Research
          (lead/lag, MFE/MAE, target-hit/invalidation
          outcomes for the prior session's 0DTE clusters).
       G. Event and No-Trade Calendar.
       H. Data and System Health.
       I. Dealer Level Map.
       J. Moving-Average Stack.
       Premarket may use prior valid map but must label it as
       requiring open refresh.
2.15.5–2.15.8: brief is an operating plan, not a recap.

2.16 Workflow 3 — Ad Hoc Symbol Report

2.16.1–2.16.8: on-demand per-symbol report. Dealer-context
       section (E) shows any active or recent 0DTE cluster
       for the ticker with grade, activation, target, and
       invalidation reference.

2.17 Thesis Merge/Split

2.17.1 Same ticker, same lane, same structure signature,
       same direction → merge.
2.17.2 Material structure change → split.
2.17.3 DTE lane change → new thesis; old expires.
2.17.4 Merges and splits write thesis_versions.
2.17.5 Operator confirmation via quantctl for manual
       merges/splits.

2.18 Thesis ↔ Signal Ledger Reconciliation

2.18.1 Every signal_versions row references a live thesis.
2.18.2 Every thesis with material change references the
       latest signal_versions.
2.18.3 Reconciliation runs on startup and daily.
2.18.4 Discrepancies → data-quality-alarm.
2.18.5 Discrepancies flagged in symbol_theses.reconciliation_required.

2.19 Notification Category Mapping

2.19.1 Categories to urgencies; per §18.14 of SPEC Vol 4.
2.19.2 Categories:
       manual-intervention-required, session-blocked,
       login-failed, schema-changed, refresh-failed,
       backup-drill-result, data-quality-alarm,
       weekly-audit-result, scheduler-heartbeat-gap,
       delivery-channel-degraded, price-alert-triggered,
       flow-alert-triggered, flow-state-change,
       flow-retraction, market-stand-down,
       plan-requires-open-revalidation,
       dealer-flip-disagreement, basis-tolerance-warning,
       challenge-detected, canary-drift,
       fingerprint-incoherent, behavioral-drift,
       external-signal, zero-dte-flow-cluster,
       zero-dte-dealer-confirmed, zero-dte-cluster-reversal,
       zero-dte-cluster-retraction.
       (Legacy alias zero-dte-cluster retained but not
       emitted.)
       AH categories (position-exit-required, exit-monitor-failure, valuation-unavailable).
       Additional observability categories (SPEC Vol 5
       §O.10): system-status-summary, slo-breach,
       escalation-required, trace-propagation-failure,
       observability-write-failure,
       provider-state-manual-required.
2.19.3 Subject Key:
       flow:{thesis_id}:{state}:{version}
       flow:{thesis_id}:retracted:{version}
       0dte:{ticker}:{direction}:{expiration_yyyymmdd}:{episode_id}:{state}
2.19.4 Body: full text + actions + one-line summary.

2.20 DTE Lanes

2.20.1 Definitions:
       0DTE               RESEARCH_ONLY (two-tier cluster
                          detection, §2.20.7)
       1DTE               RESEARCH_ONLY
       TACTICAL_2DTE      2 DTE, own rules
       SHORT_TACTICAL     3–7 DTE
       SWING              8–60 DTE
       LONGER_HORIZON     61+ DTE
2.20.2 Per Lane: holding horizon, quote freshness, dealer
       TTL, chase, spread model, exits, calibration,
       performance report.
2.20.3 No pooling.
2.20.4 Both calendar_dte and trading_sessions_remaining.
2.20.5 Migration per §2.17.3.
2.20.6 Sub-1-DTE still collected for surface and regime.

2.20.7 0DTE Cluster Detection — Two-Tier Real-Time
       Tactical Intelligence

2.20.7.1 Objective
        Real-time tactical intelligence about same-day
        expiry flow clusters at two evidence-graded tiers.
        Provides direction, activation level, target,
        support/invalidation, and evidence grade. Prohibits
        route selection, position sizing, and
        ACTIONABLE_NOW until a separately calibrated 0DTE
        execution lane exists.

2.20.7.2 Basic cluster (silent)
        Retained when the same ticker and same-day expiration
        produces at least ZERO_DTE_CLUSTER_MIN_EVENTS (2)
        independent canonical events across at least
        ZERO_DTE_CLUSTER_MIN_STRIKES (2) distinct strikes
        within ZERO_DTE_CLUSTER_WINDOW_S (900 s), with at
        least one recognized member of
        RAPIDFIRE_FAMILY = { RAPIDFIRE, RAPIDFIRE_BEARISH }
        or REPEATER_FAMILY = { REPEATER, REPEATER_BEARISH }
        in the provider's normalized_meaning field.
        Failing tiers → cluster_grade = BASIC, cluster_state
        = ACTIVE, episode_state = FORMING. No push. No
        email. BASIC clusters write to
        zero_dte_cluster_current and
        zero_dte_cluster_member_history only; at expiry they
        write a zero_dte_cluster_snapshots row with
        snapshot_type = 'BASIC_SHADOW', cluster_grade =
        'BASIC', alert_grade = 'BASIC', and alert_ts = NULL
        (no push, no directional outcome).
        Ticker scope is enforced through the centralized
        symbol_filter with workflow_scope =
        'ZERO_DTE_CLUSTER' (see §7.6). Default rows in
        §7.6 realize:
          include ticker == 'SPX' (index);
          include any ticker whose asset_type == 'EQUITY';
          exclude all ETFs (including SPY, QQQ, IWM);
          exclude other indexes, futures, perps, other
          asset types.
        Operator override is via symbol_filter rows at
        ZERO_DTE_CLUSTER scope; no separate blocklist
        config key is used.
        episode_id is deterministic:
          sha256(ticker | expiration | direction |
                 first_qualifying_canonical_event_id |
                 ruleset_version)[:32]
        Stable across restarts. Distinguishes two same-day
        episodes for the same (ticker, expiration,
        direction).

2.20.7.3 MEDIUM_CONFLUENCE tier (immediate Discord +
        email)
        Requires ALL:
          (a) DQ grade A/B, and either
              coverage = COMPLETE, or
              coverage = PARTIAL with
              provider_coverage_pct ≥
              ZERO_DTE_MEDIUM_MIN_COVERAGE_PCT (0.80).
              MANUAL_ONLY and UNKNOWN do not qualify for
              MEDIUM.
          (b) No canceled or materially late member.
          (c) Recognized provider status mapping.
          (d) Tier 1/2 spread package legs counted as one
              economic event.
          (e) Aggressor-adjusted direction unambiguous.
          (f) OpposingShare ≤ ZERO_DTE_OPPOSITE_FLOW_LIMIT
              (0.25), where
                B = Σ_k max(X_k, 0)
                R = Σ_k max(−X_k, 0)
                OpposingShare = min(B, R) / (B + R)
                DirectionalStrength = 1 − 2·OpposingShare
                                    = |B − R| / (B + R)
                SignedDirectionalImbalance = (B − R) / (B + R)
              Guard: B + R = 0 → no cluster.

              OpposingShare is the gate input (this gate).
              DirectionalStrength is the D_s input to Flow
              Strength (ARCH Vol 4 §D.14b). Zero for
              balanced flow; 0.5 at this gate's boundary;
              1 for fully directional flow.
              SignedDirectionalImbalance is display-only.
              Its sign gives direction; its absolute value
              equals DirectionalStrength.
          (g) Flow Strength F ≥
              ZERO_DTE_MEDIUM_FLOW_STRENGTH_MIN (0.70).
          (h) Either at least ZERO_DTE_MEDIUM_EVENT_MIN (3)
              independent events across at least
              ZERO_DTE_MEDIUM_STRIKE_MIN (3) distinct
              strikes, OR premium/delta intensity ≥ 90th
              same-time percentile per §2.20.7.4a.
          (i) Market phase gate:
              market_phase == REGULAR.
          (j) Freshness gate:
              last_qualifying_event_age ≤
              ZERO_DTE_ALERT_MAX_AGE_S (300).
          (k) Member latency gate:
              every counted member has
              member_latency_ms ≤
              ZERO_DTE_MEMBER_LATENCY_MAX_MS (3000).
          (l) Post-close reports audit-only:
              late or out-of-sequence members arriving after
              the instrument's regular close count for
              audit, not for push.

        Effect:
          - Immediate Discord + email.
          - Research-only; no route, no size, no
            ACTIONABLE_NOW.
          - Target/support/invalidation shown where the
            current session dealer map supports them.
          - Dealer map stale but within
            ZERO_DTE_DEALER_MAP_STALE_MAX_S (900 s) →
            dealer fields shown with explicit stale label.
          - Older than 900 s → dealer fields omitted;
            alert carries "dealer context unavailable".

2.20.7.4 HIGH_CONFLUENCE tier (immediate upgrade)
        Requires MEDIUM_CONFLUENCE plus ALL:
          (a) Fresh same-session dealer map: age ≤
              ZERO_DTE_DEALER_MAP_FRESHNESS_S (300 s).
              A stale map (up to 900 s) does NOT qualify.
          (a') Coverage == COMPLETE. PARTIAL, MANUAL_ONLY,
               and UNKNOWN do NOT qualify for HIGH. (MEDIUM
               continues to allow PARTIAL with the coverage
               cap; HIGH is stricter.)
          (a'') Dealer map expiration scope matches the
               cluster's expiration. A 0DTE cluster aligns
               only with a 0DTE dealer profile; cross-
               expiration alignment is not accepted.
          (b) Gamma or vanna alignment confirmed (see
              ARCH Vol 4 §D.14c).
          (c) Spot confirms activation by moving beyond it
              and holding for
              ZERO_DTE_CONFIRMATION_HOLD_S (60 s), with
              confirmation buffer
              b = max(ZERO_DTE_CONFIRMATION_BUFFER_PCT · S,
                      ZERO_DTE_CONFIRMATION_BUFFER_ATR · ATR_5m).
          (d) ConfluenceScore ≥
              ZERO_DTE_HIGH_CONFLUENCE_MIN (0.80).
          (e) Dealer regime is POSITIVE or NEGATIVE (not UNINFORMATIVE/UNAVAILABLE, not sign_fragile) and the map is
              not built on model A alone for 0DTE (ARCH Vol 4 §D.26.4).  [C12]

        Effect: immediate upgrade; revised target/support/
        invalidation and exact confirming evidence. If
        HIGH conditions already hold at first detection,
        send only the HIGH alert.

2.20.7.4a Percentile baseline (definitions)
        "Same-time percentile" = percentile of current 0DTE
        aggregate against same-ticker same-time-of-day
        trailing distribution.
        Baseline window: trailing
        ZERO_DTE_PERCENTILE_WINDOW_D (20) trading days,
        restricted to the same clock-minute bucket ±
        ZERO_DTE_PERCENTILE_BUCKET_S (600 s).
        Cold start policy (deterministic, default fail
        closed): if fewer than
        ZERO_DTE_PERCENTILE_MIN_DAYS (10) usable trailing
        sessions exist, the percentile branch of gate (h)
        in §2.20.7.3 does not pass. The 3-events/3-strikes
        branch of gate (h) is unaffected and continues to
        be evaluated. Optional config flag
        zero_dte_percentile_fallback_enabled = false
        permits labeled liquidity/sector-bucket fallback
        with ZERO_DTE_PERCENTILE_FALLBACK_PENALTY (0.15)
        applied to F; alert body must carry
        "percentile baseline: fallback".

2.20.7.5 Target and support/invalidation selection per
        ARCH Vol 4 §D.14c. All price levels (activation,
        target, support/resistance, invalidation) are
        stored and compared in _mills. Spot references
        remain in _micros.

2.20.7.6 Push policy
        Maximum normal pushes per episode: one MEDIUM + one
        HIGH upgrade. Additional same-direction members
        update silently unless grade, target, invalidation,
        or lead/lag state changes materially. Separate
        immediate notifications allowed for reversal
        (zero-dte-cluster-reversal), retraction
        (zero-dte-cluster-retraction), new MIXED cluster.
        No arbitrary global daily cap on 0DTE cluster
        pushes.

2.20.7.7 Corrections
        Canceled member removed from
        zero_dte_cluster_members (removed_at set,
        removal_reason recorded) and mirrored to
        zero_dte_cluster_member_history (append-only).
        Cluster recomputed. If it no longer qualifies for
        its current grade, immediate retraction by Discord
        and email.

2.20.7.8 Expiry
        Episode expires at instrument close (per §2.26.4).
        cluster_state = EXPIRED, episode_state = EXPIRED.
        Current row retired per invariant AA. For episodes
        with cluster_grade ∈ {MEDIUM_CONFLUENCE,
        HIGH_CONFLUENCE}, the final snapshot is retained in
        zero_dte_cluster_snapshots with snapshot_type =
        'EXPIRY'. For BASIC episodes, the final snapshot is
        retained with snapshot_type = 'BASIC_SHADOW',
        cluster_grade = 'BASIC', alert_grade = 'BASIC',
        and alert_ts = NULL.
        For all episodes, including
        BASIC, member history is retained in
        zero_dte_cluster_member_history. Next morning the
        episode appears only in Prior-Day 0DTE Research
        Audit.

2.20.7.9 Delivery
        Both MEDIUM and HIGH are immediate urgency.
        Discord and email dispatched in parallel. Email
        path: Resend primary, Mailgun fallback. Discord
        success does NOT suppress email. If both email
        providers fail, failed delivery retained and a
        delivery-channel-degraded notification is emitted.

2.20.7.10 Prohibited
        - No automatic 0DTE option route, quantity, or
          order instruction.
        - No HIGH_CONFLUENCE presented as a calibrated
          probability.
        - No target or stop invented from stale or missing
          data.
        - No negative-gamma strike used as "support" merely
          because it is below spot.

2.20.8 0DTE Cluster Lead/Lag and Markout Outcomes
       Computed after relevant horizon closes; never fed
       back into alert-time snapshot. Outcomes stored per
       (cluster_snapshot_id, horizon, calculation_version)
       so MEDIUM and HIGH produce separate rows.
       r_h    = d · (S_t_h − S_0) / S_0
       MFE_h  = max_{t ∈ (0, h]} ( d · (S_t − S_0) / S_0 )
       MAE_h  = max_{t ∈ (0, h]} ( d · (S_0 − S_t) / S_0 )
       d = +1 bullish, -1 bearish; S_0 spot at detection.
       Stored: pre_5m_return, first_event_to_detection_return,
       post_1m_return, post_5m_return, post_15m_return,
       post_30m_return, to_close_return, MFE, MAE,
       target_hit_at, invalidation_hit_at,
       lead_lag_class ∈ {FLOW_LED, COINCIDENT, PRICE_LED,
       INDETERMINATE}.

2.21 MarketMapService

2.21.1–2.21.10: inputs, outputs, invariants; composes
       dealer_map_id + technical_snapshot_id +
       price_observation_id + volatility + event context
       into an immutable map_id per symbol per session.

2.22 SUPER_BULLISH and SUPER_BEARISH States
2.22.1–2.22.5: supporting_event_count ≥ 1 added to the
       definition; state is descriptive, not a decision.

2.23 Closing FDI
2.23.1–2.23.7: FDI phase enum (PRE_CLOSE, UPDATE, FINAL);
       unique fdi_snapshot_id.

2.24 Workflow-Scoped ETF Filter
2.24.1–2.24.3: per symbol_filter.workflow_scope.

2.25 Operator Control Plane
2.25.1–2.25.6: quantctl → quantd; audit trail in
       operator_control_audit.

2.26 Time Discipline
2.26.1–2.26.6: UTC epoch-ms; SQLite INTEGER; DuckDB BIGINT;
       NTP drift alert threshold 50 ms.

2.27 Alert-Path Trust Boundary
2.27.1–2.27.6: webhook pattern, downstream revalidation,
       replay defenses.
2.27.7 Default operating mode in v2.0.5.1: Pattern 2
       (Discord message as untrusted wake-up with
       downstream revalidation) unless the provider's
       documented capabilities confirm Pattern 1 support.

================================================================================
SECTION 3 — INFRASTRUCTURE REQUIREMENTS
================================================================================

3.1 Host

3.2 Hardware Baseline
  Minimum: ≥ 4 cores, ≥ 16 GB RAM.
  Memory caps: quantd 4 GB, capture 2 GB (measured, see
  ARCH Vol 1 §B.1), rhythm 256 MB.
  Display-capable (Xvfb for headed browser).

3.3 Network

3.4 Named Tunnel

3.5 Access Control

3.6 Configuration
3.6.1 Params in operational store.
3.6.2 Every change logged.
3.6.3 No code for tuning.
3.6.4 Versions referenced.
3.6.5 Authoritative enums defined in one place.
3.6.6 Functional-prefix rules and renderer non-upgrade
      obligations are CI-enforced:
        (a) document-level lint that greps the specification
            and reports violations where the rule is
            restated;
        (b) code-level AST lint that rejects forbidden
            prefixes in the builder's body and rejects
            renderer code that writes to the snapshot's
            decision field.
      Prose alone is not sufficient.

3.7 Operator Control Plane per §2.25.
3.8 Time Discipline per §2.26.
3.9 Alert-Path Trust per §2.27.
3.10 Restore RTO: ≤ 4 hours; quarterly drill.

3.11 Log Retention
  Notifications 90 days; delivery records 30 days;
  persistent idempotency 7 days; trace fingerprints 90 days;
  coverage windows 1 year.

3.12 Retention for Append-Only Analytical Tables

  option_quote_observations:     30 days hot, 1 year warm
  package_quote_observations:    30 days hot, 1 year warm
  price_observations:            7 days hot, 90 days warm
  ohlcv_bars:                    90 days hot, 5 years warm
  market_map_snapshots:          1 year hot, 5 years warm
  dealer_level_maps:             1 year hot, 5 years warm
  technical_level_snapshots:     90 days hot, 3 years warm
  portfolio_snapshots:           1 year hot, 5 years warm
  zero_dte_cluster_snapshots:    1 year hot, 5 years warm
  zero_dte_cluster_outcomes:     indefinite (small)

================================================================================
SECTION 4 — SOURCE AUTHORIZATION & DATA SOURCES
================================================================================

4.1 Source Authorization Registry

4.1.1 The source_authorization table is the single authority.
4.1.2 Fields: source_id, provider_name, access_channel,
      license_tier_id, tos_version, tos_url,
      approved_endpoint_list, authorization_reference,
      permitted_data, permitted_retention_days,
      permitted_frequency, personal_use_only,
      redistribution_allowed, automation_allowed,
      entitlement_reference, sensitivity_class, approved_by,
      approved_at, review_expiry_at, last_reviewed_at,
      owner, status.
4.1.3 Status: APPROVED | PENDING | DISABLED | EXPIRED.
4.1.4 Rules: refuse unless APPROVED and unexpired; auto-
      expire; endpoint allowlist; daily check.
4.1.5 automation_allowed: INTEGER NOT NULL DEFAULT 0.
      Absence of clarity fails closed.
4.1.6 ToS-permitting-provision requirement: before a source
      is added with automation_allowed = 1, the operator
      MUST record in authorization_reference the specific
      provision of the source's ToS that permits automated
      access. A generic note is not sufficient. Absence
      fails closed.
4.1.7 Secrets rotation: at least quarterly.
4.1.7a If a source with automation_allowed = 1 serves a
       persistent challenge or persistent 403, the operator
       treats that as evidence the recorded ToS provision is
       wrong. Suspend automated access. Route the source to
       authorization review. Do not solve-and-continue.
4.1.7b review_expiry_at is tied to tos_version. A change to
       tos_version forces re-review before the next session.
4.1.7c The operator keeps a written per-source
       determination of what the anti-detection posture is
       for. Stored in the source_authorization record.

4.2 Authorized Categories
4.2.1 Free public.
4.2.2 Free-tier APIs.
4.2.3 Licensed paid.
4.2.4 Operator UI sessions.
4.2.5 Hyperliquid (via adapter).
4.2.6 OpenMarket.
4.2.7 Authorized listed-option quote source.
4.2.8 Trading calendar source:
      Primary: Cboe/official exchange calendar.
      Fallback: NYSE published holiday schedule.

4.3 Authorization Retention
4.4 Data Retention
4.5 Degradation

4.6 CFTC Commitment of Traders
4.6.1 Purpose: weekly positioning context. Not a trigger.
4.6.2 Source: cftc.gov historical reports. No auth.
4.6.3 Report family: Traders in Financial Futures (TFF).
4.6.4 Fields: market_code, as_of_date (Tuesday positions),
      release_at (Friday publication), report_type,
      revision_number, dealer_long/short,
      asset_manager_long/short, leveraged_funds_long/short,
      other_reportables_long/short, nonreportable_long/short,
      open_interest, percentiles_json (3-year),
      source_hash.
4.6.5 Cadence: weekly Friday fetch; backfill one-time at
      Stage 2.2.
4.6.6 Use: morning brief "so what" line; ad hoc context.
      Never triggers alerts.
4.6.7 Storage: cot_snapshots.
4.6.8 Fail closed: missing → INSUFFICIENT_DATA.

4.7 Leveraged ETF Mechanical-Pressure Research
4.7.1 Purpose: track structural flows driven by leveraged
      and inverse ETFs.
4.7.2 Instruments: SOXL/SOXS, TQQQ/SQQQ, optional SPXL/SPXS.
4.7.3 Signals: AUM and shares trend; creation/redemption
      pressure proxy; implied EOD rebalance flow;
      underlying dealer gamma concentration.
4.7.4 Fields: leverage_multiple, benchmark_return,
      aum_estimate, aum_as_of, nav_source, shares_change,
      estimated_rebalance_flow_dollars, flow_direction,
      underlying_dealer_gamma, confidence,
      calculation_version, coverage_flags, source_versions.
4.7.5 Use: research and morning context. Never actionable
      trigger alone.
4.7.6 Storage: leveraged_etf_pressure.
4.7.7 Sources: issuer ETF pages, yfinance OHLCV, VolLand
      cache.
4.7.8 Fail closed: missing → explicit INSUFFICIENT_DATA.
4.7.9 Workflow-scoped filter: excluded from FLOW_ALERT by
      default; visible in morning and ad hoc research only.

4.8 Authorized Real-Time Listed-Option Quote Source
4.8.1 Purpose: executable option and package quotes for
      actionability and entry-chase decisions.
4.8.2 Candidate sources documented in ARCH Vol 4 §AC.2.
4.8.3 Adapter interface per ARCH Vol 4 §AC.3.
4.8.4 Quality rules per ARCH Vol 4 §AC.4.
4.8.5 Fallbacks: VALIDATED_PENDING_ENTRY or WATCH.
4.8.6 Storage: current rows reference immutable observation
      IDs; history in DuckDB.

4.9 Corporate Action Ingestion
4.9.1 Corporate actions ingested daily.
4.9.2 Every action writes to corporate_action_ingestion in
      the operational SQLite store.
      Fields: action_id, ticker, action_type, effective_date,
      announced_at, ratio, source, applied_to_chains,
      applied_to_options_master, applied_at, status,
      error_detail.
4.9.3 Chains referencing adjusted contracts tagged with a
      new corporate_action_ver and invalidate cached greeks
      and dealer data.
4.9.4 Hard gate: if corporate_action_ingestion.status =
      'PENDING' for a ticker, flow alerts for that ticker
      are blocked until reconciliation completes.

================================================================================
SECTION 5 — CANONICAL EVENT & DEDUPLICATION
================================================================================

5.1 Raw Event Archive: immutable, append-only, hash-verified.

5.2 Canonical Event: event-time NBBO preserved.

5.3 Deduplication Fingerprint priority:
    exchange_execution_id → provider_event_id → content hash.

5.4 Cross-Provider Corroboration: one canonical event + many
    canonical_event_sources rows; never double-counts
    premium.

5.5 Relationship Classes:
    INDEPENDENT_REPEATED_FLOW, RELATED_CLUSTER,
    SAME_THESIS_UPDATE, SUPERSEDES.

5.6 Corrections and Out-of-Sequence Events: recorded with
    correction_status; late reports handled per §2.20.7.3(l).

5.7 Persistent Idempotency: survives restart; dedup_key with
    expiry.

5.8 Provider Alert Attributes

5.8.1 The canonical economic event does not carry
      provider-specific status/color/mapping fields.
5.8.2 Those fields live in provider_alert_attributes keyed
      to raw_event_id.
5.8.3 Unknown mapping_version fails closed for the strong
      0DTE alert tiers and for the flow alert.
5.8.4 Field list: raw_color, normalized_meaning,
      mapping_version, alert_type, trade_type, sweep_flag,
      block_flag, multi_leg_flag, oi_exceeded,
      repeated_oi_exceedance, canceled, late_or_out_of_sequence,
      provider_timestamp.
5.8.5 normalized_meaning enum includes RAPIDFIRE, REPEATER,
      STEADY, and their bearish analogs. Canonical family
      aliases:
        RAPIDFIRE_FAMILY = { RAPIDFIRE, RAPIDFIRE_BEARISH }
        REPEATER_FAMILY  = { REPEATER,  REPEATER_BEARISH  }
      Membership in a family counts as "recognized" for the
      basic-cluster requirement in §2.20.7.2 and for the
      MEDIUM_CONFLUENCE gate in §2.20.7.3(c).

================================================================================
SECTION 6 — DATA QUALITY GATEWAY
================================================================================

6.1 Grades: A, B, C, D, F. A/B actionability-eligible; C
    watch-only; D/F prohibited from the decision path.

6.2 Checks: quote freshness, staleness, source conflict,
    greek sign, spread width, coverage, canary agreement.

6.3 Quote Rejection Reasons: stale, crossed, wide, size
    zero, malformed, unknown source.

6.4 Coverage Caps: PARTIAL 0.70, MANUAL_ONLY 0.50, UNKNOWN
    watch-only (0.00). Applied inside the weighted sum.

6.5 Critical Evidence: covered per pipeline.

6.6 Coverage and Thesis Interaction: caps propagate to
    thesis and snapshot.

6.7 Grade Propagation: thesis.best_data_quality and
    snapshot.data_quality_grade updated on every material
    event.

================================================================================
SECTION 7 — CANDIDATE ENGINE
================================================================================

7.1 Pre-Screen Scoring: cheap-first screening order.
7.2 Screening Order: dedup → quality → candidate score.
7.3 Rejection Record: written to ingest_log with reason.
7.4 Shadow Sampling: feeds calibration cold start; sampled
    with probability stratification.
7.5 Promotion: from CANDIDATE to WATCH/ACTIONABLE per §8 of
    SPEC Vol 3.

7.6 Symbol Filter

  Actions: BLOCK | ALLOW | WATCH_ONLY. Workflow scope and
  asset type per schema.

  Workflow scopes (final):
    FLOW_ALERT        ordinary real-time flow alerts
    ZERO_DTE_CLUSTER  0DTE cluster detection
    MORNING           morning brief pipeline
    AD_HOC            ad-hoc report pipeline
    SPX_INTRADAY      SPX intraday crossing pipeline
    ALL               applies across scopes

  Default rows seeded at Stage 0 (baseline; operator may
  extend; existing rows must be preserved across upgrades):

    pattern  match_type  action  workflow_scope    asset_type  reason
    ------   ----------  ------  ----------------  ----------  ------
    *        glob        ALLOW   FLOW_ALERT        EQUITY      equity flow lane
    *        glob        BLOCK   FLOW_ALERT        ETF         ETF arb noise
    *        glob        BLOCK   FLOW_ALERT        INDEX       index noise
    *        glob        BLOCK   FLOW_ALERT        FUTURE      unsupported
    *        glob        BLOCK   FLOW_ALERT        OTHER       unsupported
    *        glob        ALLOW   ZERO_DTE_CLUSTER  EQUITY      equity 0DTE lane
    SPX      exact       ALLOW   ZERO_DTE_CLUSTER  INDEX       SPX 0DTE lane
    *        glob        BLOCK   ZERO_DTE_CLUSTER  ETF         ETF excluded
    *        glob        BLOCK   ZERO_DTE_CLUSTER  INDEX       non-SPX index excluded
    *        glob        BLOCK   ZERO_DTE_CLUSTER  FUTURE      unsupported
    *        glob        BLOCK   ZERO_DTE_CLUSTER  OTHER       unsupported
    *        glob        ALLOW   MORNING           ANY         morning brief scope
    *        glob        ALLOW   AD_HOC            ANY         ad hoc scope
    *        glob        ALLOW   SPX_INTRADAY      ANY         SPX cycle scope

  Rationale: ordinary flow alerts are equity-driven; ETFs
  and indexes are dominated by arbitrage and hedging flow
  that pollutes the ordinary lane. 0DTE cluster detection
  includes equities and SPX (the index the FSM tracks);
  ETFs and other indexes are excluded.

  Precedence (matching evaluation):
    exact ticker > glob > regex > asset-type wildcard > ALL
    On equal specificity: BLOCK > WATCH_ONLY > ALLOW

  Operator may add explicit rows at any specificity. A
  specific BLOCK overrides a wildcard ALLOW.

  The 0DTE detector calls the centralized symbol_filter
  with workflow_scope = 'ZERO_DTE_CLUSTER'. It does NOT
  bypass the filter. Ordinary FLOW_ALERT alerts and 0DTE
  cluster detection are additive and do not suppress each
  other.

7.7 Corporate Action Hard Gate: PENDING for a ticker blocks
    flow alerts for that ticker.

7.8 Funnel: measured counts per stage in DQ report.

7.9 Passing Candidates: emitted to enrichment.

================================================================================
SECTION 19 — DATA MODEL
================================================================================

19.1 Storage Split

19.1.1 SQLite operational store.
19.1.2 DuckDB analytical store.
19.1.3 Both on external encrypted volume.
19.1.4 Decision-critical state is not only in the analytical
       store.

19.2 Operational Entities (SQLite): see SPEC Vol 2 §19.2 for
     the full canonical list. Summary: 68 tables including
     source_authorization, provider_sessions, provider_state,
     provider_alert_attributes, live_price_current,
     option_quote_current, package_quote_current, signals,
     signal_versions, delivery_outbox, positions, symbol_filter,
     coverage_windows, raw_provider_events, canonical_events,
     canonical_event_sources, canonical_event_relationships,
     persistent_idempotency, corporate_action_ingestion,
     provider_query_pool, provider_query_budget, profile_cohort,
     wire_pins, expected_fingerprints, trace_fingerprints,
     trace_features, fingerprint_audit_log, detection_events,
     notifications, notification_deliveries,
     scheduler_heartbeats, scheduled_tasks, daily_alert_cycle,
     daily_alert_items, symbol_theses, thesis_versions,
     thesis_event_membership, zero_dte_cluster_current,
     zero_dte_cluster_members, zero_dte_cluster_member_history,
     report_runs, report_snapshot_refs,
     portfolio_state_current, dealer_context_cache_current,
     dealer_map_current, market_map_current,
     active_model_manifest, spx_crossing_state_current,
     operator_control_audit, ingest_log, backfill_log,
     behavioral_reference.

19.3 Analytical Entities (DuckDB): see SPEC Vol 2 §19.3 for
     the full canonical list. Summary: options_master,
     quote_snapshot_batches, option_quote_observations,
     package_quote_observations, chain_snapshots,
     greeks_snapshots, signal_ledger, signal_outcomes,
     position_leg_outcomes, shadow_samples, dealer_snapshot_batches,
     dealer_exposure_snapshot, volatility_snapshots,
     portfolio_snapshots, technical_level_snapshots,
     ohlcv_bars, vol_index_history, calibration_model,
     scoring_rule_registry, raw_provider_events (mirror),
     price_observations, analysis_snapshots,
     market_map_snapshots, market_map_levels, dealer_level_maps,
     dealer_levels, cot_snapshots, closing_fdi_snapshots,
     leveraged_etf_pressure, spx_crossing_state_history,
     market_events, macro_market_observations,
     macro_regime_snapshots, zero_dte_cluster_snapshots,
     zero_dte_cluster_outcomes.

19.4 Money and Units

19.4.1 Executable option prices use _cents.
19.4.2 Underlying and index prices use _micros.
19.4.3 Strikes and levels use _mills.
19.4.4 All are BIGINT.
19.4.5 DuckDB spot columns feeding executable logic are
       *_micros BIGINT.
19.4.6 DOUBLE columns are analysis only.

19.5 Relationships: as expressed by foreign keys and by
     ContextReconciler.

19.6 Invariants (full set)

A  provider_query_budget.thesis_id NOT NULL ('_GLOBAL').
B  Executable price fields use _cents.
C  market_map_snapshots and dealer_level_maps append-only.
D  Every operator action has operator_control_audit row.
E  Every price observation records source, staleness,
   synthetic-proxy, basis.
F  Every OpenMarket-triggered notification passed the trust
   boundary per §2.27.
G  analysis_snapshot.dealer_map_id ==
   market_map_snapshot.dealer_map_id.
H  Every executable decision references a valid
   quote_snapshot_id and, for multi-leg evidence,
   package_quote_observation_id (immutable). Constituent
   option quotes are captured in
   option_quote_observation_ids_json. The mutable
   package_quote_current.package_quote_id is cache
   identity only and is never decision evidence.
I  Same analysis_snapshot_id → same decision across
   workflows.
J  Every canonical event has ≥1 canonical_event_sources row.
K  Every applied migration recorded with checksum.
L  Active thesis key partial-unique on state NOT IN
   ('EXPIRED','COMPLETED','RETRACTED','INVALIDATED').
M  Active calibrator set enforced by active_model_manifest
   partial unique on (model_kind, scope_key, ruleset_version)
   WHERE active_to IS NULL AND model_role = 'CHAMPION'.
N  signal_versions.selected_route nullable; route_status
   distinguishes EXECUTABLE / NOT_APPLICABLE / UNROUTED.
O  Current pointer rows reference immutable historical
   observation IDs.
P  Technical level snapshots store full values.
Q  Portfolio snapshots store full risk-engine payload.
R  No perp/proxy price satisfies ACTIONABLE_NOW.
S  Every "unique active X" invariant names its enforcement
   mechanism.
T  Every signal_ledger.calib_model_id and
   analysis_snapshots.calibration_model_id references an
   existing calibration_model.model_id in DuckDB.
U  RECONCILIATION_REQUIRED is an audit flag on symbol_theses
   and positions, not a decision state.
V  Provider query pool: used + 1 ≤ ceiling + available_borrow
   at every query time.
W  Every DuckDB epoch-ms column is BIGINT. Every SQLite
   epoch-ms column is INTEGER. Enforced by schema test.
X  corporate_action_ingestion lives in SQLite.
Y  Every material 0DTE cluster transition writes exactly
   one append-only row to zero_dte_cluster_snapshots:
     MEDIUM/HIGH emission     → snapshot_type = 'ALERT'
     cluster becomes MIXED    → snapshot_type = 'MIXED'
     qualifying reversal      → snapshot_type = 'REVERSAL'
     cancel/correction        → snapshot_type = 'RETRACTION'
     MEDIUM/HIGH at close     → snapshot_type = 'EXPIRY'
     BASIC at close           → snapshot_type = 'BASIC_SHADOW'
   ALERT rows require non-null alert_grade in
   ('MEDIUM_CONFLUENCE','HIGH_CONFLUENCE') and non-null alert_ts.
   BASIC_SHADOW requires alert_grade='BASIC' and alert_ts=NULL.
   MIXED/REVERSAL/RETRACTION/EXPIRY require both alert_grade=NULL
   and alert_ts=NULL. Keep transition_ts and snapshot_type NOT NULL.
   Reject invalid NULL combinations explicitly in the SQL CHECK.
   Duplicate transitions are prevented by uq_0dtcs_transition on
   (cluster_id, snapshot_type, transition_ts). Only ALERT snapshots
   may produce directional outcome rows. BASIC_SHADOW does not push.
Z  No cluster snapshot references a future-as-of
   dealer_map_id or market_map_id relative to its own as_of.
AA zero_dte_cluster_current is populated only for the current
   session (session_date == today in exchange-local time);
   prior-session rows are retired.
AB cluster_grade contains only evidence-grade values
   (BASIC, MEDIUM_CONFLUENCE, HIGH_CONFLUENCE).
   cluster_state contains only lifecycle values (ACTIVE,
   MIXED, BULLISH_REVERSAL, BEARISH_REVERSAL, RETRACTED,
   EXPIRED). episode_state contains only episode-timeline
   values (FORMING, ACTIVE, UPGRADED, REVERSED, RETRACTED,
   EXPIRED). Enforced by CHECK constraints and a schema
   test.
AC every zero_dte_cluster_members row with removed_at NOT
   NULL has a corresponding
   zero_dte_cluster_member_history row.
AD zero_dte_cluster_current.episode_id is UNIQUE.
AE every zero_dte_cluster_outcomes row references a
   cluster_snapshot_id whose alert_grade matches the row's
   alert_grade.

19.7 Consistency: guaranteed by transaction boundaries and
     by ContextReconciler.

19.8 Date, Time, Timestamp Conventions

19.8.1 SQLite date columns TEXT in ISO 8601.
19.8.2 DuckDB native DATE.
19.8.3 Timestamps UTC epoch ms.
       SQLite: INTEGER (64-bit).
       DuckDB: BIGINT (DuckDB INTEGER is 32-bit and
       overflows).
       Enforced by a schema test with two rules:

       Rule 1 — Epoch timestamps. Column names matching
       *_ts, *_at, *_until, *_epoch_ms, *_epoch_ns, or
       *epoch_* MUST be BIGINT in DuckDB and INTEGER in
       SQLite.
       Failure to match is an error.

       Rule 2 — Bounded durations. Column names matching
       *latency_ms, *staleness_ms, *age_ms, *duration_ms,
       or *response_ms MUST be INTEGER. These are not
       epoch values and cannot overflow 32-bit under any
       realistic value.

       Ambiguous names (e.g., *_ms without a duration
       qualifier) fail the test and require an explicit
       rename.

19.8.4 Display timezone operator-local (default ET).
19.8.5 NTP drift alert threshold 50 ms.

================================================================================
SECTION 22 — APPENDIX
================================================================================

22.1 Document Map

  SPEC Vol 1 (this) — Foundations.
  SPEC Vol 2 — Data Sources, Canonicalization, Quality.
  SPEC Vol 3 — Decision Logic.
  SPEC Vol 4 — Capture Behavior, Delivery, Operations,
               Verification.
  SPEC Vol 5 — Observability.
  SPEC Vol 6 — Future Extensions (informational).
  ARCH Vol 1 — Components, Processes, State Machines,
               Recovery, Constants.
  ARCH Vol 2 — Data Model.
  ARCH Vol 3 — Capture Layer: Session Rhythm & Anti-Detection.
  ARCH Vol 4 — Formulas, Services, Workflows.
  SPEC Vol 7 — Research Addenda (AE, AF, AG).

22.2 Sign Conventions

  Dealer exposure is dealer-signed by an explicit model (OI_NAIVE | SIGNED_FLOW | PROVIDER); see ARCH Vol 4 §D.26.4.
  Gamma_$ per +1% = Gamma*S^2*0.01*M*OI; Vanna_$ per vol pt = Vanna*0.01*S*M*OI; Charm_$ per day = Charm/365*S*M*OI.
  H_$ hedge flow per ARCH Vol 4 §D.21.
  FDI signed per ARCH Vol 4 §D.25.
  Vanna = ∂Δ/∂σ.
  Charm = ∂Δ/∂t.

22.3 Glossary

  Thesis: durable aggregation sharing
    (ticker, expected_direction, dte_lane,
     structure_signature, target_horizon).
  Snapshot: one immutable Analysis Snapshot per decision
    moment.
  DTE Lane: 0DTE, 1DTE, TACTICAL_2DTE, SHORT_TACTICAL,
    SWING, LONGER_HORIZON.
  Evidence Tier: 1 CONFIRMED_SPREAD, 2 PROBABLE_SPREAD,
    3 POSSIBLE_SPREAD, 4 CONTEXT_ONLY.
  Cluster Grade: BASIC, MEDIUM_CONFLUENCE, HIGH_CONFLUENCE.
  Cluster State: ACTIVE, MIXED, BULLISH_REVERSAL,
    BEARISH_REVERSAL, RETRACTED, EXPIRED.
    (BASIC/MEDIUM/HIGH are grades, not states; see Cluster
    Grade.)
  Zero-DTE Episode State: FORMING, ACTIVE, UPGRADED,
    REVERSED, RETRACTED, EXPIRED.
  Lead/Lag Class: FLOW_LED, COINCIDENT, PRICE_LED,
    INDETERMINATE.
  Coverage: COMPLETE, PARTIAL, MANUAL_ONLY, UNKNOWN.
  DQ Grade: A, B, C, D, F.
  Calibrator Scope: (target, route, dte_lane, horizon,
    ruleset_version).
  RAPIDFIRE_FAMILY: { RAPIDFIRE, RAPIDFIRE_BEARISH }.
  REPEATER_FAMILY: { REPEATER, REPEATER_BEARISH }.
  OpposingShare: min(B,R)/(B+R).
  DirectionalStrength: 1 − 2·OpposingShare.
  SignedDirectionalImbalance: (B − R)/(B + R).
  Structure Signatures: 25 entries per SPEC Vol 3 §10.4.

22.4 Document Manifest

  SPEC_v2.0.5.1_Vol1_Foundations.md
  SPEC_v2.0.5.1_Vol2_Data_Canonical.md
  SPEC_v2.0.5.1_Vol3_Decision.md
  SPEC_v2.0.5.1_Vol4_Capture_Behavior_Ops_Verification.md
  SPEC_v2.0.5.1_Vol5_Observability.md
  SPEC_v2.0.5.1_Vol6_Future_Extensions.md
  SPEC_v2.0.5.1_Vol7_Research_Addenda.md
  ARCH_v5.1.5.1_Vol1_Foundation.md
  ARCH_v5.1.5.1_Vol2_DataModel.md
  ARCH_v5.1.5.1_Vol3_Capture_AntiDetection.md
  ARCH_v5.1.5.1_Vol4_Services_Workflows.md
  SHA-256 hashes recorded separately in MANIFEST.md.

22.5 Reference Qualification Rule

  Within the ten-file release, the phrases "per prior" and
  "as prior" are prohibited in normative text. Every such
  reference MUST be replaced by an explicit citation of the
  form "<SPEC|ARCH> v<X.Y.Z> Vol <N> §<S>".

  A CI check scans the ten files for the strings
  "per prior" and "as prior" and fails the build if any
  occurrence remains outside a historical-changelog block.

  Rationale: the release claims self-containment. An
  unqualified "per prior" reference cannot be resolved
  without v2.0.4/v5.1.4, which are not part of the release.

22.6 Frozen Layer Statement

  Anti-detection (SPEC Vol 4 §11 and ARCH v5.1.5.1 Vol 3 §F)
  is the frozen v5.1.5.1 baseline. No downstream change may
  weaken it. The acceptance suite may only grow.

================================================================================
22.7 Canonical JSON and Hashing
================================================================================

  Canonical JSON serialization follows RFC 8785 (JSON Canonicalization
  Scheme). All hashes over JSON object inputs use SHA-256 on the RFC 8785
  canonical form unless a section explicitly declares otherwise.

  Applies to (non-exhaustive):
    - canonical_fingerprint content hash (SPEC Vol 2 §5.3)
    - fdi_snapshot_id, cot_snapshot_id, analytics_id, observation_id
      (SPEC Vol 7)
    - interval_id, evaluation_id, episode_id
      (ARCH Vol 4 §D.14d, §AH.6.3)
    - input_manifest_hash on any analytical snapshot

  CANONICAL_TRACE_NAMESPACE is a fixed UUIDv5 constant, generated once
  during initial setup and committed to the repository. Trace IDs are
  uuid5(CANONICAL_TRACE_NAMESPACE, canonical_event_id) per SPEC Vol 5
  §O.6.1.


================================================================================
END OF SPEC Vol 1 v2.0.5.1
================================================================================