# QUANT FLOW SYSTEM — TECHNICAL ARCHITECTURE v5.1.5.1
## VOLUME 1 — COMPONENTS, PROCESSES, STATE MACHINES, RECOVERY, CONSTANTS

Status: self-contained for the sections this volume owns.
Sections not owned by this volume reference the owning
volume within the 10-file set by section number.

CHANGES FROM v5.1.5
- P0-2: ZERO_DTE_CLUSTER workflow scope replaces the
  parallel ticker allowlist; symbol_filter is the single
  enforcement point.
- P0-3: cluster_state vocabulary is lifecycle-only
  (ACTIVE, MIXED, BULLISH_REVERSAL, BEARISH_REVERSAL,
  RETRACTED, EXPIRED); BASIC/MEDIUM/HIGH are grades.
- P0-3: episode_id uses first_qualifying_canonical_event_id
  and ruleset_version; no |seq=N fallback.

CHANGES FROM v5.1.4
- §N.5 SPX FSM: hysteresis, close-of-day resolution, cadence.
- §N.9 notification state enum lowercase canonical.
- §N.14 0DTE: separate cluster_state, cluster_grade,
  episode_state; UNIQUE(episode_id).
- §AI.3 new constants:
    ZERO_DTE_ALERT_MAX_AGE_S (300)
    ZERO_DTE_MEMBER_LATENCY_MAX_MS (3000)
    ZERO_DTE_PERCENTILE_WINDOW_D (20)
    ZERO_DTE_PERCENTILE_BUCKET_S (600)
    ZERO_DTE_PERCENTILE_MIN_DAYS (10)
    ZERO_DTE_PERCENTILE_FALLBACK_PENALTY (0.15)
    SPX_APPROACHING_RETREAT_PCT (0.005)
    SPX_EVALUATION_CADENCE_S (30)
- §AI.16 setup window narrowed to [06:00, 07:00].
- §AI.17 enums split; RAPIDFIRE_FAMILY / REPEATER_FAMILY.
- §AI.22 new: single-machine fingerprint linkage decision.
- AH route-specific exit constants added to §AI.3.

CHANGES FROM THIS REVIEW (A1-01, A1-02, A1-03)
- A.3 PayoffKernel paragraph rewritten to separate exact
  contractual risk from the finite scenario grid.
- AI.9 PayoffKernel section rewritten with the same
  separation and the analytical endpoint/tail rules.
- AI.3 gains three named implementation constants:
  POSITION_EXPIRY_EXIT_BUFFER_S, PAPER_DEPTH_PARTICIPATION_PCT,
  THETA_MICROCENTS_PER_CENT.

================================================================================
A. COMPONENT ARCHITECTURE
================================================================================

A.1 High-Level

    INTERFACE LAYER
      Muse (free tier)          Discord (push + price alerts)
                | HTTPS + Cloudflare Access | Webhook
                v                           v

    PRIMARY BOX — USB-SSD (LUKS, Linux + App)
      Named Cloudflare Tunnel + Access
      Token Shield (deterministic)
      FastMCP / OpenAPI Facade (read-only, fixed templates)

      PROCESS 1: quantd (asyncio, single SQLite writer)
        Pipeline:
          canonicalizer → quality → candidate → enrichment
          → DealerLevelMapService → TechnicalLevelService
          → MarketMapService
          → structure → classifiers → scoring → router/risk
          → SymbolThesisService
          → AnalysisSnapshotBuilder
          → Signal Ledger + Outbox
          → 0DTE cluster detector (parallel) → renderers
          → Delivery
        Discord listener (HMAC or downstream revalidation).
        SPX crossing state machine.
        ProviderQueryPlanner (pool-based budgets).
        LivePriceProviderAdapter + ListedOptionQuoteAdapter.
        quantctl control socket.
        DuckDB writes on db_pool_executor.
        SQLite writes on single writer task with WAL
        checkpoint policy.
        No Playwright. No Puppeteer.
        No time.sleep() in async paths.
        No headless browser. No fresh contexts.

      PROCESS 2: provider_capture_worker
        phantomime (custom CDP driver) wrapping real Google
        Chrome stable, headed under Xvfb, per-profile
        persistent user_data_dir.
        Subcomponents:
          - Session orchestrator.
          - Humanization engine.
          - Engine router.
          - Loopback echo server.
          - Loopback canary page.
          - OpenMarket cycle runner.
        Non-privileged user. cgroup MemoryMax=2G (measured).
        Restartable.

      PROCESS 3: human_rhythm_scheduler
        State machine, daily/weekly rhythm, vacation schedule.
        MemoryMax=256M.

      LOCAL runtime files on USB-SSD (LUKS, /var/quant)
                | USB 3.0 / SATA
                v

    EXTERNAL SATA III SSD (240+ GB, ext4):
      /data/quant_flow.duckdb   (analytical)
      /data/quant_state.db      (operational, WAL)
      /data/warm/               (warm-tier Parquet)
      /data/duckdb_tmp/         (temp)

    ENCRYPTED OFFSITE BACKUP (rclone --crypt-remote → B2/R2)

    BITWARDEN SECRETS MANAGER (TPM-sealed access token)

    DATA SOURCES
      Free: yfinance, Cboe CSV, DoltHub, Kaggle, Massive,
            Finnhub free, CFTC COT (TFF), Hyperliquid via
            adapter
      Paid: VolLand, Blackbox, Tradytics, FlashAlpha, ORATS,
            authorized listed-option quote source

    NOTIFICATION CHANNELS
      Discord, Resend (primary email), Mailgun (fallback)
      OpenMarket (price-alert triggers)

A.2 Data Flow

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
  Alerts view → cluster detector → zero_dte_cluster_current
  → zero_dte_cluster_snapshots (append-only)
  → renderers (immediate Discord + email at MEDIUM or HIGH)
  → zero_dte_cluster_outcomes (post-horizon markouts)

Ownership invariants:
  analysis_snapshot.dealer_map_id ==
    market_map_snapshot.dealer_map_id
  Current pointer rows reference immutable historical
  observation IDs.

Alert triggers:
  OpenMarket fires → Discord + email → listener → notification
  → SPX crossing state machine → optional VolLand escalation
  → optional thesis re-evaluation.

A.3 Shared Services (in quantd only)

  SymbolThesisService
  AnalysisSnapshotBuilder
  ProviderQueryPlanner
  DealerContextCache
  DealerLevelMapService
  TechnicalLevelService
  MarketMapService
  LivePriceProviderAdapter
  ListedOptionQuoteAdapter
  ZeroDteClusterDetector
  ReportRenderers
  PayoffKernel
  ContextReconciler

  ContextReconciler:
    Inputs:  SQLite current-pointer rows; DuckDB immutable
             rows.
    Outputs: reconciliation report; reconciliation_required
             flags.
    Runs:    startup + daily.
    Never writes analytical data. Never fabricates references.
    Failure mode: raises data-quality-alarm and blocks new
    signals for affected scopes until resolved.

  PayoffKernel:
    Inputs: verified package legs and signed entry cash; separate
            nonnegative cost allowance; optional positive spot grid.
    Outputs: exact contractual risk/status from analytical zero,
             strike and upper-tail tests; bounded-profit amount or
             explicit profit_unbounded flag; breakevens; separate
             scenario_worst_loss_cents and grid_status.
    Pure, deterministic, no I/O. Implement ARCH Vol 4 §D.5.
    An unavailable or truncated scenario grid is never a finite
    contractual-risk estimate. Unsupported/unbounded risk blocks
    sizing. Required EV/scenario failures keep their own entry gates.

  ZeroDteClusterDetector:
    Inputs:  stream of accepted canonical events tagged 0DTE.
    Outputs: cluster state transitions on
             zero_dte_cluster_current; snapshots on
             zero_dte_cluster_snapshots; notification rows.
    Pure detection logic. No provider access.
    Never selects a route. Never creates a position.
    Read-only against the current session's dealer map.
    Calls the centralized symbol_filter with workflow_scope
    = 'ZERO_DTE_CLUSTER'; does NOT bypass the filter.

A.4 Service Dependencies

  DealerLevelMapService   ← DealerContextCache + Volland
  TechnicalLevelService   ← OHLCV + market calendar
  MarketMapService        ← DealerLevelMapService +
                             TechnicalLevelService +
                             LivePriceProviderAdapter
  AnalysisSnapshotBuilder ← all above; pure
  ZeroDteClusterDetector  ← canonical events + current
                             dealer map + current market map

================================================================================
B. PROCESS MODEL & ISOLATION
================================================================================

B.1 Process Contract

    Process                   | Runs as   | Memory cap | Responsibility
    --------------------------|-----------|------------|------------------
    quantd                    | quant     | 4 GB       | analytical +
                              |           |            | writer
    provider_capture_worker   | quant-cap | 2 GB       | browser only
    human_rhythm_scheduler    | quant     | 256 MB     | rhythm only

  Memory cap note:
    The 2 GB capture cap is an initial default. Operator must
    measure peak RSS under real workload and set MemoryMax to
    peak + 25%. If the cap is too low, OOM kills become
    abnormal terminations (a monitored anomaly).

B.2 Isolation Rules

  1. Capture has NO DB access.
  2. Capture has NO master vault token.
  3. Capture talks to quantd via localhost/Unix socket only.
  4. quantd never launches Playwright or Puppeteer.
  5. quantd never calls time.sleep() in async paths.
  6. Capture and rhythm can restart without affecting quantd.
  7. Shared services never run in capture or rhythm.
  8. Only quantd writes to SQLite or DuckDB.
  9. All operator mutations go through quantctl → quantd.
 10. Loopback echo runs inside the capture namespace and is
     reachable only from within it.

B.3 IPC Events

  Types:
    session-opened, session-refreshed, session-closed,
    cookie-expiry-updated, engine-health-updated,
    engine-preference-changed, provider-state-changed,
    coverage-window-opened, coverage-window-closed,
    human-rhythm-state-entered, human-rhythm-state-left,
    heartbeat, alert-cycle-started, alert-cycle-completed,
    alert-item-configured, alert-item-removed,
    provider-observation-submitted,
    fingerprint-verified,
    challenge-detected,
    credential-request

  Envelope: type, provider/session_id, monotonic sequence,
  timestamp, payload, shared-secret token.

  provider-observation-submitted payload:
    event_id, provider, source_ts, payload_hash, schema_version,
    authorization_id, source_trace_id, spool_ref | bounded_payload.

  fingerprint-verified payload:
    session_id, wire_fp_hash, self_report_hash, verdict,
    mismatches_json.

  challenge-detected payload:
    provider, session_id, url, pattern_matched.

  credential-request payload:
    provider, session_id, purpose ("re-login" | "session-refresh").

  credential-response payload (quantd → capture):
    one-time-use token with TTL, scoped to provider.

  Capture prunes spool after quantd ACK.

B.4 Process Supervision

  systemd units per process.
  Restart=on-failure. RestartSec=5.
  WatchdogSec for quantd and rhythm.
  MemoryMax enforced per contract.
  Crash-loop backoff configurable.
  Heartbeats every 5 min per component.

B.5 Async Writer Discipline

  All DuckDB writes MUST be delegated to db_pool_executor:
    await asyncio.get_running_loop().run_in_executor(
        db_pool_executor, duckdb_write_func)
  SQLite writes serialized on a single writer task (WAL).
  No synchronous analytical I/O in the event loop.

B.6 Capture Timing

  Capture timing code runs in the capture process with its
  own clock/seed discipline. The no-sleep rule applies to
  quantd async paths only.

B.7 Credential Path for Capture

  Capture has no master vault token and no passwords on disk.
  Mechanism:
    - quantd holds master vault token and scoped read access
      to the provider credentials subvault.
    - Capture emits credential-request IPC event.
    - quantd validates: provider_state ∈ {HEALTHY, DEGRADED},
      source APPROVED with automation_allowed = 1, per-
      provider credential request rate limit.
    - quantd responds with a one-time-use token, TTL 60 s.
    - Token passed to the login form inside the capture
      namespace; not written to disk.
    - After login attempt, token is invalidated.
    - Every request/response logged to operator_control_audit
      with a hashed reference, never the credential itself.

================================================================================
M. BACKUP, RESTORE, RECOVERY
================================================================================

M.1 Nightly Backup Barrier

  Barrier sequence:
    1. Pause capture intake.
    2. Drain pending_ledger_sync and in-flight outbox.
    3. PRAGMA wal_checkpoint(TRUNCATE).
    4. Close DuckDB cleanly.
    5. Copy both store files.
    6. Compute and verify SHA-256 for each copy.
    7. Reopen.
    8. Resume capture.
    9. rclone copy to encrypted offsite (rclone-crypt remote to B2 or R2).
       MEGA is reserved for the LUKS header backup only.
   10. Log barrier duration.

  Success is silent. Failure always notifies.
  Retention: 30 days.

M.2 Quarterly Restore Drill

  1. Download latest offsite artifact.
  2. Decrypt.
  3. Verify SHA-256.
  4. Restore to scratch path.
  5. Open both stores.
  6. Row-count and checksum spot checks.
  7. Record duration.
  8. Notify result.
  9. Log in operator_control_audit.

  Checkpoint ≠ backup. Restore RTO target ≤ 4 hours.

M.3 Crash Recovery Protocol

  On quantd restart, before accepting new work:
    1. WAL integrity check (both stores).
    2. IPC spool replay (idempotent).
    3. scheduled_tasks rows in RUNNING → PENDING with backoff.
    4. delivery_outbox rows in_progress → pending after lock
       expiry.
    5. pending_ledger_sync drain.
    6. ContextReconciler startup run.
    7. Dangling references → reconciliation_required = 1 on
       the affected symbol_theses or positions row; emit
       data-quality-alarm.
    8. Validate every signal_ledger.calib_model_id and
       analysis_snapshots.calibration_model_id against
       calibration_model.model_id in DuckDB.
    9. Heartbeats resume with new boot_id.
   10. Only then does quantd resume accepting signals.

M.4 Retention Job

  Per SPEC Vol 1 §3.12. Nightly job moves hot-tier rows
  older than the per-table hot window to /data/warm/ as ZSTD
  Parquet. Row-count + checksum verified before delete.
  Audit record in ingest_log. Failure → data-quality-alarm.

M.5 Operator Control Snapshot

  Before quarterly drill, snapshot operator_control_audit,
  active_model_manifest, scheduler_heartbeats.

================================================================================
N. STATE MACHINES
================================================================================

N.1 Decision States

  Twelve decision states; authoritative in SPEC Vol 3 §8.4.
  This volume does not restate; the precedence is:
    RETRACTED > INVALIDATED > STAND_DOWN >
    WATCH (from C/D/F grade or UNKNOWN coverage) >
    WATCH (from signal_valid failure, per SPEC Vol 3 §8.1a) >
    PORTFOLIO_BLOCKED > VALIDATED_PENDING_ENTRY >
    ENTRY_UNAVAILABLE > ACTIONABLE_NOW > CANDIDATE >
    NO_ACTIVE_FLOW_THESIS
  Any divergence resolved in favor of SPEC Vol 3 §8.4.

N.2 Provider States (authoritative)

    HEALTHY, DEGRADED, CHALLENGED, MANUAL_REQUIRED, BLOCKED,
    COOLDOWN, AUTH_REQUIRED, SCHEMA_CHANGED, DISABLED.

  Transitions:
    HEALTHY ⇄ DEGRADED     (network failure)
    → CHALLENGED           (challenge interstitial; auto-
                            resume at next session boundary
                            after operator solves)
    → BLOCKED → MANUAL_REQUIRED
                           (persistent 403)
    → COOLDOWN             (429 until next day)
    → AUTH_REQUIRED        (second 401)
    → SCHEMA_CHANGED       (UI / API shape)
    → DISABLED             (operator)

  CHALLENGED escalation:
    If operator does not resolve within
    CHALLENGED_MANUAL_ESCALATION_DAYS (3) consecutive
    sessions, provider auto-escalates to MANUAL_REQUIRED with
    manual-intervention-required notification.

  MANUAL_REQUIRED and AUTH_REQUIRED require operator action
  without automatic resume.
  CHALLENGED is a same-day pause with auto-resume.
  COOLDOWN is timed.
  Every transition logged with reason.

N.3 Capture Session Lifecycle

  CLOSED → WARMING → ACTIVE → WINDING_DOWN → CLOSED.
  Hard cap 60 min.
  No cross-day auth tokens.
  Abnormal terminations counted and monitored.

  Interaction with pauses:
    The 60-minute cap is a ceiling on wall-clock duration.
    Micro-breaks and idle disengagement pause activity but do
    not extend the cap.
    If a break would push the session past the cap, the pause
    is truncated to fit or the session enters WINDING_DOWN
    early. Never terminates mid-break without wind-down.

N.4 Human Rhythm States

  offline, waking, active, deep-read, light-check, break,
  drifting, distracted, winding-down.

N.5 SPX Crossing States

  FAR, APPROACHING, TESTING, CONFIRMED_BREAKOUT,
  CONFIRMED_REVERSAL, FALSE_CROSS, COOLDOWN, REARMED,
  INVALIDATED.

  Only Market Map levels trigger.
  Transitions per SPEC Vol 3 §9.6.5 including:
    APPROACHING → FAR on retreat beyond
      SPX_APPROACHING_RETREAT_PCT (0.005) with hysteresis.
    TESTING → CONFIRMED_BREAKOUT intraday when a 1-minute
      bar closes beyond the level by more than
      SPX_CONFIRMATION_BUFFER_PCT × spot and spot holds
      beyond for SPX_CONFIRMATION_HOLD_S (60 s).
    TESTING → CONFIRMED_REVERSAL intraday on the mirrored
      rule.
    TESTING → COOLDOWN at close when still TESTING
      (CONFIRMATION_NOT_ACHIEVED_AT_CLOSE).
    Evaluation cadence at least every
      SPX_EVALUATION_CADENCE_S (30) while active.
  Current pointer in SQLite; history in DuckDB.

N.6 Report States

  COMPLETE, PARTIAL, FAILED, NO_CHANGES, SKIPPED.

N.7 Engine Health

  blocked (cooldown) / preferred / normal.
  Promote after consecutive successes.
  Demote on 4xx.

N.8 Signal Lifecycle

  Persisted lifecycle uses the twelve decision states.
  Descriptive audit labels (candidate, classified, structure-
  pending, probable, confirmed, validated, updated, T+1-*)
  recorded in signal_versions.reason_for_change. They are
  NOT decision states.

N.9 Notification State

  Canonical (lowercase): open, resolved, expired.
  Transitions: open → resolved | expired.
  DDL CHECK constraint uses lowercase.

N.10 Daily Alert Cycle

  PENDING → COMPLETE | PARTIAL | FAILED.

N.11 Outbox Worker

  pending → in_progress → delivered | failed | exhausted.
  Backoff: 30s → 60s → 120s → 300s → 900s.
  Fatal classification:
    5xx / timeout / connection → retry.
    4xx / auth / malformed → exhausted immediately,
      fatal_delivery_error = 1, escalate to
      delivery-channel-degraded.

N.12 Scheduled Task

  PENDING → RUNNING → DONE | FAILED.
  Failure increments attempts and re-enqueues with backoff.
  Cancellation allowed from PENDING only.

N.13 Dealer Map Rollover

  When dealer_map_current advances A → B for a ticker:
    - coalesce: at most one rollover re-evaluation per
      ticker per ROLLOVER_COALESCE_S.
    - budget: draws from workflow_scope = 'GLOBAL'.
    - SymbolThesisService.on_dealer_map_rollover(ticker, B)
      enumerates non-terminal theses.
    - same-state outcome: write new analysis snapshot only.
    - material change: normal transition protocol.

N.14 0DTE Episode State

  Three independent columns:

    cluster_grade ∈ { BASIC, MEDIUM_CONFLUENCE,
                      HIGH_CONFLUENCE }.
    cluster_state ∈ { ACTIVE, MIXED, BULLISH_REVERSAL,
                      BEARISH_REVERSAL, RETRACTED, EXPIRED }.
    episode_state ∈ { FORMING, ACTIVE, UPGRADED, REVERSED,
                      RETRACTED, EXPIRED }.

  cluster_grade is the evidence grade.
  cluster_state is the lifecycle classification.
  episode_state is the episode timeline.
  BASIC is a grade only, never a state.
  Grade and state vocabularies are disjoint.

  Transitions (episode_state):
    FORMING → ACTIVE
    ACTIVE → UPGRADED
    ACTIVE → REVERSED | RETRACTED
    UPGRADED → REVERSED | RETRACTED | EXPIRED
    Any → EXPIRED at instrument close.

  Storage: zero_dte_cluster_current with grade, cluster
  state, and episode state as separate columns;
  UNIQUE(episode_id).

================================================================================
AI. CONSTANTS, ENUMS, SESSION PHASES
================================================================================

AI.3 is the canonical home of every UPPER_SNAKE_CASE named
constant.

AI.1 Sizing & Risk

  BASE_RISK_PCT                    0.0075
  Kelly shadow                     × 0.25
  net_vega_pct_equity              0.005
  net_delta_notional_mult          1.5
  daily_theta_pct_equity           0.003
  corr_threshold                   0.70
  max_cluster_positions            2
  assignment_pct_cash              1.00
  TACTICAL_2DTE max_risk_pct_equity 0.005

AI.2 Stops

  PREMIUM_STOP_PCT        0.50
  THETA_BUDGET_PCT        0.30
  TIME_STOP_DAYS          45
  VOLATILITY_EXIT_IVR     60
  ROUTE_GAP_TRIGGER_PCT   0.015 (symmetric default)

AI.3 Additional Constants

  MIN_VEGA                            0.005
  # --- C12 dealer/greeks constants [RECOMMENDED values; running the patch script = approval] ---
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
  VANNA_THETA_PCTL                    90
  MIN_POSITIVE_SPOT_MICROS            10000000
  FLIP_DISAGREEMENT_PERSIST_SNAPS     2
  TRACE_FLAG_COUNT_ALERT              5
  TRACE_SIMILARITY_ALERT              0.85
  HEDGE_PENALTY_DEFAULT               0.15
  DELTA_FLOOR_WEIGHT_ADJUST           0.02
  HOT_TIER_RETENTION_DAYS             7
  PAYOFF_KERNEL_GRID_MIN_FRAC         0.001
  PAYOFF_KERNEL_GRID_MAX_MULT         5
  PAYOFF_KERNEL_MAX_INVALID_PCT       0.05
  GRID_MAX_POINTS                     4096
  BUDGET_FLOW_ALERT_RESERVE_PCT       60
  BUDGET_PREMARKET_BORROW_PCT         20
  STAGE4_MIN_N_PER_CELL               20
  PASSIVE_CANARY_CONTRACT_COUNT       5
  MIN_VOL_INDEX_COVERAGE              0.60
  ROLLOVER_COALESCE_S                 120
  WAL_SIZE_CEILING_MB                 50
  SAFETY_MARGIN                       0.05
  SPX_FALSE_CROSS_TOLERANCE_PCT       0.0015
  SPX_FALSE_CROSS_HOLD_S              60
  SPX_APPROACHING_PCT                 0.003
  SPX_APPROACHING_RETREAT_PCT         0.005
  SPX_EVALUATION_CADENCE_S            30
  SPX_COOLDOWN_S                      600
  SPX_CONFIRMATION_BUFFER_PCT         0.0015
  SPX_CONFIRMATION_HOLD_S             60
  GAMMA_FLIP_AGREEMENT_PCT            0.0015
  WALL_PROXIMITY_PCT                  0.015
  CHALLENGED_MANUAL_ESCALATION_DAYS   3
  NEWSLETTER_POLL_TIMEOUT_S           900

  0DTE cluster constants:
    ZERO_DTE_CLUSTER_WINDOW_S           900
    ZERO_DTE_CLUSTER_MIN_EVENTS         2
    ZERO_DTE_CLUSTER_MIN_STRIKES        2
    ZERO_DTE_MEDIUM_FLOW_STRENGTH_MIN   0.70
    ZERO_DTE_MEDIUM_EVENT_MIN           3
    ZERO_DTE_MEDIUM_STRIKE_MIN          3
    ZERO_DTE_HIGH_CONFLUENCE_MIN        0.80
    ZERO_DTE_CONFIRMATION_BUFFER_PCT    0.0015
    ZERO_DTE_CONFIRMATION_BUFFER_ATR    0.15
    ZERO_DTE_CONFIRMATION_HOLD_S        60
    ZERO_DTE_DEALER_MAP_FRESHNESS_S     300
    ZERO_DTE_DEALER_MAP_STALE_MAX_S     900
    ZERO_DTE_VANNA_RELEVANCE_MIN        0.10   # DEPRECATED (C12): replaced by VANNA_THETA_PCTL rule, ARCH V4 D.14c
    ZERO_DTE_OPPOSITE_FLOW_LIMIT        0.25
    ZERO_DTE_ALERT_MAX_AGE_S            300
    ZERO_DTE_MEMBER_LATENCY_MAX_MS      3000
    ZERO_DTE_PERCENTILE_WINDOW_D        20
    ZERO_DTE_PERCENTILE_BUCKET_S        600
    ZERO_DTE_PERCENTILE_MIN_DAYS        10
    ZERO_DTE_PERCENTILE_FALLBACK_PENALTY 0.15
    ZERO_DTE_MEDIUM_MIN_COVERAGE_PCT     0.80

  Route-specific exit constants (AH):
    POSITION_EXIT_EVAL_INTERVAL_S             5
    POSITION_DEADLINE_WATCHDOG_S              1
    POSITION_DEADLINE_ALERT_LEAD_S            300
    POSITION_VALUATION_UNAVAILABLE_MAX_S      60
    EXIT_EVALUATION_BUCKET_S                  1
    PAPER_FEE_PER_CONTRACT_CENTS              65
    IVR_HISTORY_REQUIRED_SESSIONS             252
    STRUCTURE_STOP_MIN_PCT                    0.0005
    STRUCTURE_STOP_ATR_MULT                   0.10
    POSITION_EXPIRY_EXIT_BUFFER_S             900
    PAPER_DEPTH_PARTICIPATION_PCT             0.25
    THETA_MICROCENTS_PER_CENT                 1000000

  These are engineering/paper-model choices, not calibrated market
  probabilities. The 900s buffer applies to the named contract and
  pre-0DTE bounds; it is not a timestamp. Microcents are an internal
  model-accumulator unit only. Executable option quotes/fills stay in
  cents; use Decimal at the model-to-fixed-point boundary.

  ZERO_DTE ticker scope (rule, enforced by symbol_filter):
    Effective rule, realized as default rows in SPEC Vol 1
    §7.6 at workflow_scope = 'ZERO_DTE_CLUSTER':
      include ticker == 'SPX' (index);
      include any ticker whose asset_type == 'EQUITY';
      exclude all ETFs (including SPY, QQQ, IWM);
      exclude other indexes, futures, perps, other asset
      types.
    Operator override is via symbol_filter rows at
    ZERO_DTE_CLUSTER scope. No separate blocklist config
    key is used. The 0DTE detector calls symbol_filter with
    workflow_scope = 'ZERO_DTE_CLUSTER'; it does NOT bypass
    the filter.

  Flow and confluence weights (D.14b):
    ZERO_DTE_FLOW_WEIGHT_DELTA          0.35
    ZERO_DTE_FLOW_WEIGHT_PREMIUM        0.25
    ZERO_DTE_FLOW_WEIGHT_DIRECTION      0.20
    ZERO_DTE_FLOW_WEIGHT_EVENTS         0.10
    ZERO_DTE_FLOW_WEIGHT_STRIKES        0.10
    ZERO_DTE_CONFLUENCE_WEIGHT_FLOW     0.65
    ZERO_DTE_CONFLUENCE_WEIGHT_DEALER   0.25
    ZERO_DTE_CONFLUENCE_WEIGHT_PRICE    0.10

  Lane latency hard cutoffs (ms):
    TACTICAL_2DTE                     3000
    SHORT_TACTICAL                    5000
    SWING                             10000
    LONGER_HORIZON                    30000

AI.4 Chase Limits

  SWING                   0.10
  SHORT_TACTICAL          0.075
  TACTICAL_2DTE           0.05
  1DTE                    0.03  (research-only; not exercised)
  LONGER_HORIZON          0.15

AI.5 DTE Lanes

  0DTE            RESEARCH_ONLY (cluster detection only)
  1DTE            RESEARCH_ONLY
  TACTICAL_2DTE   2 DTE (own rules)
  SHORT_TACTICAL  3–7 DTE
  SWING           8–60 DTE
  LONGER_HORIZON  61+ DTE

  TACTICAL_2DTE contract:
    directional_alerts          true
    research_push               false
    hold_horizon_hours          6
    quote_freshness_s           15 (5 with streaming source)
    dealer_ttl_s                900
    chase_max                   0.05
    paper_mode_required         true
    max_risk_pct_equity         0.005
    voland_freshness_s          900
    confirmation_delay_s        60
    latest_entry_time           15:30 ET
    mandatory_exit_before_0dte  true
    routes                      debit_spread, long_call, long_put
    calibrator_scope            TACTICAL_2DTE

  0DTE lane:
    directional_alerts          false
    research_only               true
    research_push               true
    cluster_detection           true
    chase_max                   0

AI.6 Cache TTLs (seconds)

  TACTICAL_2DTE                   900
  SHORT_TACTICAL                  1800
  SWING                           3600
  LONGER_HORIZON                  7200
  Structural vanna                3600–7200
  Front gamma 0DTE                600–900
  Front gamma 1–7 DTE             900–1800
  SPX 0DTE near-key               120–300
  IV_MOVE_THRESHOLD               1.5 vol points

AI.7 Provider Query Budgets

  Pools per (provider, market_date):
    FLOW_ALERT       60% reserved
    MORNING_AD_HOC   40% shared
    GLOBAL           separate ceiling
  Pre-market borrow ≤ BUDGET_PREMARKET_BORROW_PCT.
  SPX_INTRADAY draws from FLOW_ALERT.
  ZERO_DTE_CLUSTER draws from FLOW_ALERT.

  0DTE cluster VolLand policy:
    On a 0DTE medium alert, reuse the current session's
    cached dealer map. If cached map is fresher than
    ZERO_DTE_DEALER_MAP_FRESHNESS_S, use as-is. If older but
    younger than ZERO_DTE_DEALER_MAP_STALE_MAX_S, use with
    dealer-context explicitly marked "stale" in the alert
    body. If older than ZERO_DTE_DEALER_MAP_STALE_MAX_S,
    omit dealer-derived fields and label the alert
    "dealer context unavailable".
    A fresh VolLand fetch on the medium alert is NOT
    performed by default. The operator may enable a single
    value-of-information-gated refresh per episode via
    config flag, drawing from the FLOW_ALERT pool.
    High-confluence upgrade reuses the same session's map
    unless the TTL, spot move, IV move, or level crossing
    invalidates it.

AI.8 Calibration

  MIN_CALIBRATION_N           200
  sigmoid                     n < 500
  isotonic                    MAY for n ≥ 500
  FALLBACK_CONFIDENCE_FACTOR  0.7
  monthly refit
  embargo                     5 days
  max label horizon           5 days
  weight change ≤ max(0.10|w|, DELTA_FLOOR_WEIGHT_ADJUST)
  OPPOSITE_FRACTION           0.5
  PROMOTION_THRESHOLD         3 independent events
  INACTIVITY_WINDOW           5 trading days

AI.9 PayoffKernel

  Exact contractual risk: analytical x=0, every strike, and the
  upper-tail slope per ARCH Vol 4 D.5; x is hypothetical spot.
  Positive finite scenario grid: step 0.5% geometric; caps per AI.3;
  union valid positive strike/epsilon nodes. Do not pass literal
  infinity or zero into a numerical pricing model.
  MIN_POSITIVE_SPOT_MICROS=10000000 remains a SCENARIO-grid floor
  only. It is not a contractual lower bound on the underlying.
  Scenario extrema never determine maximum loss for position sizing.

AI.10 Spread Detection

  Similarity floor            0.80 (1:1)
  Interval                    10 minutes max
  Spot move                   1% max
  Staleness                   15 minutes max

AI.11 Market Map & SPX

  Per AI.3:
    GAMMA_FLIP_AGREEMENT_PCT, WALL_PROXIMITY_PCT,
    SPX_APPROACHING_PCT, SPX_APPROACHING_RETREAT_PCT,
    SPX_EVALUATION_CADENCE_S, SPX_COOLDOWN_S,
    SPX_FALSE_CROSS_TOLERANCE_PCT, SPX_FALSE_CROSS_HOLD_S,
    SPX_CONFIRMATION_BUFFER_PCT, SPX_CONFIRMATION_HOLD_S,
    FLIP_DISAGREEMENT_PERSIST_SNAPS.

AI.12 Basis

  BASIS_TOLERANCE_BPS default 15 (cash/index sources)
  Reference priority: listed-option underlying, official
  index.
  Prior session close is not a basis reference.

AI.13 Pacing / Rhythm: authoritative in ARCH Vol 3 §E.

AI.14 Sessions / IPC

  coalesce                    100 ms
  ROLLOVER_COALESCE_S         per AI.3
  re-login max                1 per session
  heartbeat                   5 min
  gap alert                   15 min
  process-exit alert          60 s
  credential token TTL        60 s (single-use)

AI.15 Delivery

  email retries               2 attempts per provider
                              (Resend then Mailgun)
  email retry job             15 min
  outbox max_attempts         6
  notification cooldown       per category (SPEC Vol 4
                              §18.14)
  alert payload cap           8 KB
  ALERT_FRESHNESS_S           120

AI.16 Ops

  WAL_SIZE_CEILING_MB         per AI.3
  checkpoint timeout          5 s
  backup retention            30 days
  DuckDB memory               1.2 GB
  DuckDB threads              2
  quantd memory cap           4 GB
  capture memory cap          2 GB (measured)
  rhythm memory cap           256 MB
  daily alert cycle setup     jittered Gaussian μ = 06:45 ET,
                              σ = 15 min, constrained to
                              [06:00, 07:00] via E.0
  daily alert cycle cleanup   jittered Gaussian μ = 16:45 ET,
                              σ = 15 min, constrained to
                              [16:30, 17:30] via E.0
  max SPX alerts per day      4
  verification window         opens at setup completion;
                              closes at 07:30 ET
  cleanup deadline            17:30 ET
  newsletter timeout clock    from ~06:00 ET publication;
                              hard cutoff 06:15 ET

AI.17 Enums

  Decision states:            12
  Provider states:            9
  DTE lanes:                  6
  Evidence tiers:             1–4
  Cluster grade:              BASIC, MEDIUM_CONFLUENCE,
                              HIGH_CONFLUENCE
  Cluster state:              ACTIVE, MIXED,
                              BULLISH_REVERSAL,
                              BEARISH_REVERSAL, RETRACTED,
                              EXPIRED
  Zero-DTE episode state:     FORMING, ACTIVE, UPGRADED,
                              REVERSED, RETRACTED, EXPIRED
  Lead/lag class:             FLOW_LED, COINCIDENT,
                              PRICE_LED, INDETERMINATE
  Provider alert status:      RAPIDFIRE, REPEATER, STEADY,
                              RAPIDFIRE_BEARISH,
                              REPEATER_BEARISH, STEADY_BEARISH,
                              UNKNOWN

  Provider alert families:    RAPIDFIRE_FAMILY =
                                { RAPIDFIRE, RAPIDFIRE_BEARISH }
                              REPEATER_FAMILY =
                                { REPEATER, REPEATER_BEARISH }
  Coverage:                   COMPLETE, PARTIAL, MANUAL_ONLY,
                              UNKNOWN
  DQ grades:                  A, B, C, D, F
  Notification categories:    per SPEC Vol 1 §2.19.2
                              plus Vol 5 §O.10 additions
  Notification tiers:         critical, immediate, warning,
                              informational, daily
  Model roles:                CHAMPION, CHALLENGER, SHADOW
                              (see SPEC Vol 6 §F for phase plan)
  Notification urgencies:     immediate, daily, informational
  Notification state:         open, resolved, expired
                              (canonical lowercase)
  Structure signatures:       per SPEC Vol 3 §10.4 (25 entries)
  Dealer level roles:         POSITIVE_GAMMA_SUPPORT,
                              POSITIVE_GAMMA_RESISTANCE,
                              POSITIVE_GAMMA_PIN,
                              NEGATIVE_GAMMA_ACCELERATOR,
                              LOW_EXPOSURE_AIR_POCKET,
                              VANNA_IV_UP_FLOW_LEVEL,
                              VANNA_IV_DOWN_FLOW_LEVEL,
                              PAIRED_EXPOSURE_ZONE,
                              CONTEXT_ONLY
  Dealer level lifecycle:     NEW, STABLE, STRENGTHENING,
                              WEAKENING, MIGRATING,
                              DISAPPEARED, EXPIRED
  Workflow scopes (symbol_filter):
                              FLOW_ALERT, ZERO_DTE_CLUSTER,
                              MORNING, AD_HOC, SPX_INTRADAY,
                              ALL
  Workflow scopes (provider_query_budget):
                              FLOW_ALERT, ZERO_DTE_CLUSTER,
                              MORNING, AD_HOC, SPX_INTRADAY,
                              GLOBAL
  SPX crossing states:        per N.5
  Session phases:             REGULAR, SPX_CASH_ONLY, CLOSED
  Calibration sample sources: SIGNAL_OUTCOME, T1_OI_LABEL,
                              TERMINAL_THESIS, SHADOW_SAMPLE
  Relationship classes:       CORROBORATION,
                              SUPPORTING_EVIDENCE,
                              INDEPENDENT, OPPOSITE, NEW

AI.18 Sign Conventions

  Dealer exposure:            dealer-signed per explicit model (OI_NAIVE | SIGNED_FLOW | PROVIDER), ARCH V4 D.26.4
  H_$ hedge flow:             negative of dealer flow
  FDI:                        signed delta-weighted
  Vanna:                      ∂Δ/∂σ
  Charm:                      ∂Δ/∂t

AI.19 Scope Key Format (active_model_manifest)

  Canonical format:
    "kind=<k>|target=<t>|route=<r>|lane=<l>|horizon=<h>"
  Fields alphabetical. Values lowercase. Missing components
  use '_ANY'. Length ≤ 200 chars. Application rejects non-
  canonical strings.

AI.20 Date and Time Conventions

  SQLite date columns are TEXT ISO 8601 YYYY-MM-DD.
  DuckDB uses native DATE.
  Timestamps: UTC epoch ms.
    SQLite: INTEGER (64-bit signed).
    DuckDB: BIGINT.
  Display timezone operator-local (default ET).
  NTP drift alert threshold 50 ms.

AI.21 Frozen Layer Statement

  Anti-detection (ARCH Vol 3 §F) is the frozen v5.1.5
  baseline. Amendments require a diffed change proposal and
  a re-run of the ARCH Vol 3 §F.Q suite. The suite may only
  grow.

AI.22 Single-Machine Fingerprint Linkage Decision

  Canvas/WebGL/audio fingerprints are the physical machine's
  real values and shared by all cohorts on the machine. The
  stock-Chrome probe environment would present an identical
  device fingerprint to authenticated cohorts if it ran on
  the same hardware.

  Decision:
    - Preferred: run the stock-Chrome probe environment on
      separate hardware (or a separate VM with distinct GPU
      and audio stack) from authenticated cohorts.
    - If separate hardware is not feasible, the operator
      records an explicit per-provider accepted-risk note in
      source_authorization.authorization_reference stating
      that anonymous probe traffic and authenticated cohort
      traffic share a device fingerprint, and that the risk
      of cross-traffic linkage is accepted.
    - Enabling fp_seed for the probe (JS-level patching) is
      permitted for the probe only, with tradeoff recorded,
      because the probe never authenticates.

================================================================================
END OF ARCH Vol 1 v5.1.5.1
================================================================================