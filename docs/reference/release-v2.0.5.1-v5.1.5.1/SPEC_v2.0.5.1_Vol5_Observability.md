# QUANT FLOW SYSTEM — SPECIFICATION v2.0.5.1
## VOLUME 5 — OBSERVABILITY, HEALTH, DASHBOARDS, LOGS, SLOs

Status: self-contained for the sections this volume owns.
Sections not owned by this volume reference the owning
volume within the 10-file set by section number. Additive to
v2.0.5.1. Does not modify the frozen anti-detection layer
(ARCH v5.1.5.1 Vol 3 §F). Does not modify the decision
pipeline (SPEC v2.0.5.1 Vol 3 §8.4). Read-only consumer of
existing stores.

CHANGES FROM v2.0.5
- Header version bump to v2.0.5.1.
- No content changes.
- §O.10: three AH notification categories added
  (position-exit-required, exit-monitor-failure,
  valuation-unavailable).

CHANGES FROM THIS REVIEW (O01, O02)
- O01: §O.7.4 replaced with a finite, root-aware, idempotent
  escalation step ladder; "original unacknowledged root does
  not suppress its own first escalation"; per-step
  reservation uses persistent_idempotency; acknowledgment
  anywhere stops future steps without resolving the
  underlying condition.
- O02: health scorer resolves notification_domain and
  requires_ack through O.10's exhaustive category-policy
  mapping. The inline list inside the health-scorer is
  replaced by a pointer to that mapping.

CHANGES FROM v2.0.4
- New Volume 5 introduced at v2.0.5. No prior content.

AUTHORITY
  Anti-detection remains authoritative in ARCH v5.1.5.1 Vol 3
  §F. Observability MUST NOT weaken it.
  Decision precedence remains authoritative in SPEC v2.0.5.1
  Vol 3 §8.4. Observability MUST NOT influence it.
  This volume defines the observability contract only. Where
  it conflicts with any other volume, the other volume wins
  and this volume is corrected.

GUARDRAILS (non-negotiable)
  G1 Read-only on decision tables: observability MUST NOT
     write to signal_ledger, signal_versions, analysis_
     snapshots, symbol_theses, thesis_versions, positions,
     position_legs, position_fills, delivery_outbox, or any
     decision-path table.
  G2 Never influence decisions: an SLO breach, a health
     warning, or a dashboard annotation MUST NOT change a
     signal state, a thesis state, or a route.
  G3 Fail-open: if the observability stack is unavailable,
     quantd, capture, and rhythm MUST continue normally.
  G4 No secrets in logs: no credentials, no tokens, no full
     payloads; use payload_hash.
  G5 No external exposure: health endpoint binds to
     localhost only. Dashboards/Muse go through Cloudflare
     Tunnel + Access.
  G6 Non-blocking: observability writes MUST NOT stall the
     pipeline; use async/queued writes.
  G7 Frozen layer: ARCH v5.1.5.1 Vol 3 §F is untouched.

CONTENTS
  O.1  Observability Contract
  O.2  Health Endpoint
  O.3  Muse Tool Expansion
  O.4  Dashboard Views (contract)
  O.5  Log Persistence Policy
  O.6  Correlation IDs
  O.7  Alerting Tiers & Escalation
  O.8  SLOs
  O.9  Daily Status Summary
  O.10 Notification Category Additions
  O.11 Data Model Additions
  O.12 Build Sequence
  O.13 Verification & Acceptance
  O.14 Implementation Notes (stack)
  O.15 Frozen-Layer Compliance Statement
  O.16 Local Narrative Service (Reserved Interface, Disabled)

================================================================================
O.1 OBSERVABILITY CONTRACT
================================================================================

O.1.1 Purpose
      Provide the operator with a truthful, queryable,
      real-time view of system state; a durable record of
      failures; and a measurable definition of health. Reduce
      time-to-detect and time-to-diagnose. Never participate
      in trading decisions.

O.1.2 Subsystem obligation
      Every long-running subsystem MUST expose at least:
        - liveness (last_heartbeat_ms)
        - last_success_at (last successful unit of work)
        - current_state (FSM state or health state)
        - error_count_24h (aggregate count)
      Subsystems:
        quantd, provider_capture_worker, human_rhythm_scheduler,
        backup_runner, t1_oi_job, dq_reporter, muse,
        provider:<name> (per authorized provider).

O.1.3 Observability components
      - Health endpoint (O.2)
      - Muse tools (O.3)
      - Dashboard views (O.4)
      - Log persistence (O.5)
      - Correlation IDs (O.6)
      - Alerting tiers (O.7)
      - SLOs (O.8)
      - Daily status summary (O.9)

O.1.4 Process placement
      The health endpoint runs as a sidecar inside quantd's
      process (asyncio task on localhost:8091). It is not a
      separate process. Rationale: keeps the single-writer
      discipline and avoids a second SQLite reader.
      Muse tools live inside quantd and are exposed via the
      existing Cloudflare Tunnel.

O.1.5 Failure semantics
      If the health endpoint crashes, quantd continues. The
      endpoint is restarted by quantd's supervisor task.
      If Muse is unreachable, the alert channel (Discord +
      email) remains the operator's fallback.
      Observability write failures are logged and counted,
      never raised into the decision path.

================================================================================
O.2 HEALTH ENDPOINT
================================================================================

O.2.1 Binding
      localhost:8091. IPv4 and IPv6 loopback only.
      No external exposure. No TLS (localhost only).
      Cloudflare Tunnel route: /muse/health → quantd:8091.

O.2.2 Route
      GET /health             full snapshot
      GET /health/{component} single component
      GET /metrics            Prometheus text format (optional)

O.2.3 Response shape (JSON)

    {
      "as_of_ms": 1759500000000,
      "overall": "ok" | "degraded" | "critical",
      "components": {
        "quantd": {
          "status": "ok",
          "last_heartbeat_ms": 1759500000000,
          "last_success_at": 1759499990000,
          "uptime_s": 86400,
          "error_count_24h": 0,
          "message": null
        },
        "provider_capture_worker": { ... },
        "human_rhythm_scheduler": { ... },
        "backup_runner": { ... },
        "t1_oi_job": { ... },
        "dq_reporter": { ... },
        "muse": { ... },
        "providers": {
          "voland": {"status": "...", "provider_state": "HEALTHY", ...},
          "blackbox": { ... }
        }
      },
      "open_notifications": 3,
      "open_notifications_by_urgency": {
        "critical": 0, "immediate": 2, "warning": 1, "info": 0
      },
      "recent_detections_24h": 0,
      "slo_breaches_24h": 0
    }

O.2.4 overall computation

      Health scoring uses SYSTEM-domain notifications only.
      Trading (TACTICAL) and research notifications do not
      affect health.

      Resolve notification_domain and requires_ack through O.10's
      exhaustive category-policy mapping. This includes AH categories:
      position-exit-required is TACTICAL; exit-monitor-failure and
      valuation-unavailable are SYSTEM. Do not maintain a second
      divergent category list inside the health scorer.

      effective_tier = COALESCE(notification.tier,
                                notification.urgency)

      critical: any component status = critical, OR any open
                SYSTEM-domain notification with
                effective_tier = critical.
      degraded: any component status = degraded, OR any open
                SYSTEM-domain notification with
                effective_tier = immediate.
      ok:       otherwise.

      TACTICAL and RESEARCH notifications are visible in
      open_notifications_by_urgency but do NOT affect
      overall.

O.2.5 Timeouts
      Endpoint responds within 200 ms p95.
      If a component query blocks > 500 ms, it returns
      {"status": "timeout", "message": "..."} and overall
      is degraded.

O.2.6 Log of requests
      Each request logged to observability_requests
      (rolling, 7-day retention) with:
        ts, path, remote_addr, response_ms, status.

================================================================================
O.3 MUSE TOOL EXPANSION
================================================================================

O.3.1 Existing tools (v2.0.5.1)
      pending_notifications
      notification_detail

O.3.2 Added tools (v2.0.5.1)

  get_health() -> dict
      Same shape as O.2.3.

  get_provider_state(provider: str | None) -> list | dict
      Reads provider_state joined with engine_health and
      provider_capabilities.

  get_dq_report(date: str) -> dict
      The DQ report for the given YYYY-MM-DD. Includes
      alarms, standing residuals, funnel counts.

  get_coverage_windows(date: str, provider: str | None) -> list
      Coverage windows on that date.

  get_detection_events(since_ms: int, until_ms: int | None,
                       provider: str | None) -> list
      Ordered by ts DESC.

  get_notification_timeline(since_ms: int, until_ms: int | None,
                            category: str | None) -> list
      Includes delivery records per channel.

  get_pipeline_stage_status() -> dict
      Counts and last-event-timestamps per stage:
        canonical_events, candidates, enriched, signals,
        alerts, notifications, deliveries.

  get_slo_status() -> dict
      Current SLO values and targets per O.8.

  get_recent_errors(since_ms: int, limit: int = 200) -> list
      Aggregated error events from detection_events,
      ingest_log, backfill_log, report_runs.

  get_daily_summary(date: str) -> dict
      The O.9 summary for the given date.

  get_correlation_trace(trace_id: str) -> dict
      All rows across the pipeline joined by trace_id.

O.3.3 Access control
      All tools read-only.
      All tools behind MUSE_ADMIN when it is enabled.
      In v2.0.5.1 MUSE_ADMIN remains reserved; tools are
      exposed but the resolve_notification tool stays gated.

O.3.4 Cache
      get_health: 1 s TTL.
      get_dq_report: 60 s TTL.
      get_coverage_windows: 60 s TTL.
      get_pipeline_stage_status: 5 s TTL.
      get_slo_status: 30 s TTL.
      Others: no cache.

================================================================================
O.4 DASHBOARD VIEWS (CONTRACT)
================================================================================

O.4.1 Required views
      The following views MUST be constructible from Muse
      tools or a read-only mirror of the stores. The stack
      used to render them is an implementation choice (O.14).

  1. System Health
     All components from O.2.3, color-coded, with
     last_heartbeat age.

  2. Provider Status
     Per-provider FSM state, reason, entered_at,
     review_after, last transition history (last 24h).

  3. Pipeline Flow
     Hourly counts of canonical_events → candidates →
     enriched → signals → alerts → notifications →
     deliveries.

  4. Open Notifications
     Table of notifications where state = 'open', sorted by
     urgency DESC, created_at DESC. Includes delivery
     status per channel.

  5. DQ Trends
     Daily count of data-quality-alarm notifications,
     canary-drift, EWMA-shift; 30-day rolling.

  6. Coverage Calendar
     Calendar heatmap of coverage windows per provider,
     with completeness per day.

  7. SPX Cycle Status
     Today's cycle: newsletter_generated_at,
     setup_started_at, setup_completed_at,
     alerts_configured_count, alerts_fired_count,
     cleanup_completed_at, status.

  8. SLO Dashboard
     Per SLO in O.8: current value, target, window, breached.

  9. Position / Portfolio Snapshot
     Latest portfolio_state_current plus open positions.

 10. Correlation Trace Viewer
     Given a trace_id, show the full pipeline trace.

O.4.2 Refresh cadence
      Manual refresh anytime.
      Auto-refresh: 5 s for views 1–4; 60 s for 5–7, 9; 300 s
      for 8.

O.4.3 Data source
      All views read from:
        - The health endpoint.
        - Read-only queries against SQLite (quant_state.db).
        - Read-only queries against DuckDB (quant_flow.duckdb).
      No view writes to any store.

================================================================================
O.5 LOG PERSISTENCE POLICY
================================================================================

O.5.1 journald configuration
      /etc/systemd/journald.conf.d/quant.conf:
        [Journal]
        Storage=persistent
        SystemMaxUse=2G
        SystemKeepFree=500M
        MaxRetentionSec=90d
        MaxFileSec=1day
        RateLimitIntervalSec=30s
        RateLimitBurst=10000

O.5.2 Per-unit drop-ins
      For quantd, provider_capture_worker,
      human_rhythm_scheduler:
        [Service]
        StandardOutput=journal
        StandardError=journal
        SyslogIdentifier=<unit_name>

O.5.3 Optional file mirror
      /var/quant/logs/<component>.log
      logrotate daily, 30-day retention, gzip.
      Enabled by config flag quant.observability.file_mirror.
      Default: disabled (journald is sufficient).
      Rationale: mirror exists for forensic export; not
      required for normal operation.

O.5.4 Structured logging
      Log lines from quantd, capture, rhythm, and their
      subcomponents are JSON-encoded where practical:
        {"ts": ..., "component": ..., "level": ...,
         "trace_id": ..., "session_id": ..., "msg": ...,
         "extra": {...}}
      Plaintext logs are acceptable for third-party tools.

O.5.5 Redaction
      Automated redaction list applied at log emit time:
        - vault tokens
        - API keys
        - passwords
        - cookie values
        - full raw_provider_events payloads (log payload_hash
          only)
      Enforcement: redaction function wraps the logger;
      CI test asserts no known-secret-shaped string can
      appear in sample logs.

O.5.6 Log levels
      DEBUG, INFO, WARNING, ERROR, CRITICAL.
      Default runtime level: INFO.
      Level changeable via quantctl set-log-level (audited).

================================================================================
O.6 CORRELATION IDs
================================================================================

O.6.1 Types
      source_trace_id    : uuid4 generated at the capture
                           boundary, one per inbound
                           observation. Written into
                           raw_provider_events.source_trace_id
                           and carried in the IPC envelope.
                           Correlates pre-canonicalization
                           activity only.
      canonical_trace_id : deterministic hash of
                           canonical_event_id, computed as
                           uuid5(CANONICAL_TRACE_NAMESPACE,
                           canonical_event_id) or an equivalent
                           namespace-scoped deterministic
                           hash. Written into
                           canonical_events.trace_id and
                           propagated post-canonicalization.
      session_id         : one per capture session.
      task_id            : one per scheduled_tasks row.
      report_id          : one per report_runs row.
      notification_id    : existing.
O.6.2 Propagation

      Two trace identifiers exist. They are distinct.

      source_trace_id:
        - Generated at the capture boundary (uuid4 or
          equivalent per observation).
        - Carried in the IPC envelope for
          provider-observation-submitted events.
        - Written into raw_provider_events.source_trace_id
          (reserved column).
        - Correlates pre-canonicalization activity.

      canonical_trace_id:
        - Generated deterministically from
          canonical_event_id post-canonicalization.
        - Written into canonical_events.trace_id.
        - Propagated to signal_ledger.trace_id and
          analysis_snapshots.trace_id.
        - NOT written to zero_dte_cluster_members or
          zero_dte_cluster_snapshots: a cluster aggregates
          several canonical events and carries no single
          trace. Cluster correlation is resolved by join:
            zero_dte_cluster_members.canonical_event_id
              → canonical_events.trace_id
          and, for immutable snapshots, by parsing
          zero_dte_cluster_snapshots.member_canonical_ids_json
          back to canonical_events.
        - Included in every log line that concerns the
          canonicalized event.
        - Included in every notification body that cites
          the event.

      canonical_event_sources:
        - Bridges source_trace_id to canonical_trace_id
          via explicit columns source_trace_id and
          canonical_trace_id.

      Column homes (canonical DDL, after migrations 064, 069,
      and 037):
        raw_provider_events.source_trace_id          TEXT (SQLite only; the
                                                     analytical DuckDB mirror
                                                     is not required to carry
                                                     it — the mirror is
                                                     append-only history, and
                                                     correlation is served
                                                     from the operational row)
        canonical_events.trace_id                    TEXT (SQLite)
        canonical_event_sources.source_trace_id      TEXT (SQLite)
        canonical_event_sources.canonical_trace_id   TEXT (SQLite)
        signal_ledger.trace_id                       TEXT (DuckDB)
        analysis_snapshots.trace_id                  TEXT (DuckDB)

      session_id is written into:
        - provider_sessions.session_id.
        - coverage_windows.session_id.
        - detection_events.session_id.
        - All log lines emitted from the capture process.

O.6.3 Query
      Muse tool get_correlation_trace(trace_id) returns rows
      from: canonical_events, canonical_event_sources,
      thesis_event_membership, signal_ledger,
      analysis_snapshots, notifications, notification_
      deliveries, zero_dte_cluster_members,
      zero_dte_cluster_snapshots.

      Detection events are resolved through session_id where
      the source trace belongs to a known capture session;
      detection_events has no trace_id column. Log lines with
      the same trace_id are included where available.

      Cluster correlation is returned via join, not via a
      stored trace column:
        zero_dte_cluster_members rows whose
          canonical_event_id joins to a canonical_events
          row whose trace_id equals the requested value;
        zero_dte_cluster_snapshots rows whose
          member_canonical_ids_json contains any such
          canonical_event_id.
      The tool annotates each returned cluster row with
      "resolved_via": "member_join".

O.6.4 Missing IDs
      If a trace_id is missing (legacy row or failed
      propagation), tools return the rows it can find and
      annotate "partial_trace": true. Propagation failures
      are logged and counted; they are a warning-tier
      notification, not immediate.

================================================================================
O.7 ALERTING TIERS & ESCALATION
================================================================================

O.7.1 Tiers (extends v2.0.5.1's {immediate, daily,
      informational})

      critical      : page now (Discord + email; optional SMS
                      via a configured provider)
      immediate     : existing v2.0.5.1 behaviour
      warning       : batched into the next daily summary
      informational : logged, shown in dashboards only
      daily         : existing v2.0.5.1 behaviour

      The existing urgencies {immediate, daily,
      informational} remain in the DDL CHECK constraint.
      critical and warning are carried in a new column
      `tier` (see O.11). urgency remains for backwards
      compatibility.

O.7.2 Tier mapping (defaults)
      critical:
        - escalation-required
        - slo-breach (when the SLO has tier=critical)
        - provider-state-manual-required
      immediate: (unchanged)
      warning:
        - trace-propagation-failure
        - slo-breach (when the SLO has tier=warning)
        - observability-write-failure
      informational:
        - system-status-summary
        - behavioral-drift (existing)
      daily: (unchanged)

O.7.3 Escalation rules

      Escalation applies ONLY to SYSTEM-domain notifications
      with requires_ack = 1. TACTICAL and RESEARCH
      notifications default to requires_ack = 0 and never
      escalate, regardless of open age. This mirrors the
      health-scoring domain split in O.2.4.

      Escalation query:
        state = 'open'
        AND notification_domain = 'SYSTEM'
        AND requires_ack = 1
        AND acknowledged_at IS NULL
        AND age > ESCALATION_*_HOURS

      immediate + SYSTEM + requires_ack + unacknowledged for
      ESCALATION_IMMEDIATE_HOURS (4) → re-emit as
      escalation-required (critical).
      critical + SYSTEM + requires_ack + unacknowledged for
      ESCALATION_CRITICAL_HOURS (1) → escalate channel
      (add SMS if configured; else re-emit with subject
      prefix "[ESCALATED]").

      Acknowledgment is distinct from resolution:
        Acknowledged = seen: acknowledged_at set,
                       acknowledged_by set. Notification
                       stops escalating; state remains open.
        Resolved    = condition ended: state = 'resolved'
                       with resolution_note, OR
                       auto_resolve_condition met.

      Escalation task runs every 15 min.

O.7.4 Re-emit: root-aware, idempotent escalation steps

  Only SYSTEM + requires_ack=1 + unacknowledged open incidents qualify.
  root_id is the original notification_id, resolved by traversing
  escalated_from_notification_id. Stop on a cycle or missing parent and
  surface a data-quality fault; never invent a root.

  Proposed finite step ladder (no change to existing age thresholds):
    root tier=immediate -> STEP1_CRITICAL at original age >4h;
    then STEP2_CHANNEL at STEP1 age >1h if still unacknowledged.
    root tier=critical -> STEP1_CHANNEL at original age >1h.
  Critical/channel steps use existing configured transports; without
  SMS the channel step uses the existing [ESCALATED] message behavior.
  No infinite sequence of duplicate pages is implied.

  step_key = 'escalation:' + root_id + ':' + step_code.
  Suppress a requested step only if:
    any row in that root chain is acknowledged; OR the incident was
    resolved/expired; OR that exact step_key already committed; OR
    an already-emitted descendant represents that requested step.
  The original unacknowledged root is NEVER itself a descendant and
  does not suppress its own first escalation. An earlier, lower step
  does not suppress a distinct next step after its due time.

  In one quantd SQLite transaction, reserve step_key in
  persistent_idempotency, create the new notification referencing its
  immediate predecessor, and queue channel attempts. Retain the key
  through incident retention so scheduler retries/restarts cannot emit
  that step again. Use a separate root for a genuinely new incident.
  Reuse stable keys/IDs; do not infer success from a transport timeout.
  Acknowledgment anywhere prevents subsequent escalation but is not
  resolution of the underlying condition.

O.7.5 Suppression
      Quiet hours for critical: none.
      Quiet hours for immediate: configurable 22:00–06:00
      local, default disabled.
      Quiet hours for warning/informational: batched into
      daily summary regardless.

O.7.6 Configuration
      quantctl set-escalation <category> <hours>
      quantctl set-tier <category> <tier>
      Every change audited in operator_control_audit.

================================================================================
O.8 SLOs
================================================================================

O.8.1 Definition
      A Service Level Objective is a measurable target over
      a rolling window with an owner and an alerting tier.

O.8.2 Objectives

  Name                                    Target         Tier
  --------------------------------------  -------------  --------
  pipeline_print_to_signal_p95_TACTICAL_2DTE    ≤  3000 ms   critical
  pipeline_print_to_signal_p95_SHORT_TACTICAL   ≤  5000 ms   critical
  pipeline_print_to_signal_p95_SWING            ≤ 10000 ms   critical
  pipeline_print_to_signal_p95_LONGER_HORIZON   ≤ 30000 ms   critical
  heartbeat_availability_per_component    ≥ 99.5% /day   critical
  notification_delivery_success           ≥ 99% /5min    immediate
  dq_alarm_mttd                           ≤ 15 min       warning
  capture_session_success_rate            ≥ 95% /day     immediate
  signal_ledger_write_consistency         100%           critical
  backup_completion_within_60min          100%           immediate
  health_endpoint_p95_response            ≤ 200 ms       warning
  trace_propagation_completeness          ≥ 99%           warning

O.8.3 Window and evaluation
      Rolling 24-hour window unless otherwise noted.
      Evaluated by a scheduled task every 5 minutes.

O.8.4 Breach handling
      On breach:
        - Write slo_measurements row (breached = 1).
        - Emit notification per the SLO's tier (cooldown
          applies per §18.14).
        - Record in the daily summary.
      No automatic action beyond notifying.

O.8.5 Configuration
      SLO thresholds overridable via config key
      observability.slo.<name>.target. Changes audited.

================================================================================
O.9 DAILY STATUS SUMMARY
================================================================================

O.9.1 Schedule
      Emitted at 08:00 ET daily via scheduled_tasks row.
      Emitted even if there are no failures.
      Emitted once per calendar day, idempotent on
      (category='system-status-summary', subject_key=today).

O.9.2 Content
      One line per subsystem:

        [SYSTEM STATUS 2026-10-02]
        quantd:           OK (uptime 14d 3h, 0 errors/24h)
        capture:          OK (3 sessions, 92% coverage)
        rhythm:           OK (5 sessions scheduled)
        backup:           OK (last: 02:14 ET, 47 min, verified)
        t1_oi:            OK (last: 2026-10-01 19:30 ET)
        dq:               WARN (3 alarms/24h: bad quotes x1,
                               stale spot x2)
        providers:        voland=HEALTHY, blackbox=HEALTHY,
                          tradytics=DEGRADED (network)
        notifications:    2 open (1 immediate, 1 warning)
        SLOs:             OK (0 breaches/24h)
        muse:             OK

O.9.3 Tier
      system-status-summary is informational.
      Subject prefix changes if any subsystem is WARN or
      CRIT.

O.9.4 Delivery
      Discord + email (Resend primary, Mailgun fallback).
      Email subject: "[STATUS] 2026-10-02 — OK" or
      "[STATUS] 2026-10-02 — 1 WARN".

O.9.5 Storage
      Written to notifications as a normal notification row.
      Also persisted to a rolling observability_daily_summary
      table (see O.11) for trend display.

================================================================================
O.10 NOTIFICATION CATEGORY ADDITIONS
================================================================================

New categories added to the set:

  system-status-summary     informational, daily cadence
  slo-breach                tier-dependent (per O.8.2)
  escalation-required       critical
  trace-propagation-failure warning
  observability-write-failure warning
  provider-state-manual-required critical (mirrors the
                            existing manual-intervention-required
                            category for provider FSM)
  position-exit-required    TACTICAL, ack=0, immediate (AH.6.4)
  exit-monitor-failure      SYSTEM, ack=1, immediate (AH.6.4)
  valuation-unavailable     SYSTEM, ack=1, immediate (AH.6.4)

Cooldowns (defaults):
  system-status-summary     86400 (once per day)
  slo-breach                3600
  escalation-required       3600
  trace-propagation-failure 86400
  observability-write-failure 86400
  provider-state-manual-required 3600
  position-exit-required    300 (per position/policy/trigger
                            epoch)
  exit-monitor-failure      3600
  valuation-unavailable     3600

All new categories are additive. The prior category set is
unchanged.

Category → (notification_domain, requires_ack) mapping.
These fields have NO column default; every insert path
MUST set them explicitly via the category-policy function.
The mapping is:

  SYSTEM + requires_ack=1:
    challenge-detected, fingerprint-incoherent,
    scheduler-heartbeat-gap, data-quality-alarm,
    login-failed, session-blocked, refresh-failed,
    schema-changed, delivery-channel-degraded,
    manual-intervention-required,
    provider-state-manual-required, slo-breach,
    escalation-required, trace-propagation-failure,
    observability-write-failure, exit-monitor-failure,
    valuation-unavailable.

  TACTICAL + requires_ack=0:
    flow-alert-triggered, flow-state-change,
    flow-retraction, market-stand-down,
    price-alert-triggered, zero-dte-flow-cluster,
    zero-dte-dealer-confirmed, zero-dte-cluster-reversal,
    zero-dte-cluster-retraction, position-exit-required.

  RESEARCH + requires_ack=0:
    canary-drift, behavioral-drift,
    basis-tolerance-warning, dealer-flip-disagreement,
    external-signal, weekly-audit-result,
    backup-drill-result, plan-requires-open-revalidation,
    system-status-summary.

================================================================================
O.11 DATA MODEL ADDITIONS
================================================================================

O.11.1 SQLite additions

  -- observability_requests (rolling 7-day)
  CREATE TABLE observability_requests (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      ts INTEGER NOT NULL,
      path TEXT NOT NULL,
      remote_addr TEXT NOT NULL,
      response_ms INTEGER NOT NULL,
      status_code INTEGER NOT NULL
  );
  CREATE INDEX idx_obs_req_ts ON observability_requests(ts);

  -- observability_daily_summary
  CREATE TABLE observability_daily_summary (
      summary_date TEXT PRIMARY KEY,
      as_of INTEGER NOT NULL,
      overall TEXT NOT NULL CHECK(overall IN ('ok','degraded','critical')),
      payload_json TEXT NOT NULL,
      created_at INTEGER NOT NULL
  );

  -- notifications: add tier column
  ALTER TABLE notifications ADD COLUMN tier TEXT
      CHECK(tier IN ('critical','immediate','warning','informational','daily'));
  -- tier nullable for backwards compatibility; consumers fall
  -- back to the urgency-based default tier when null.

  -- correlation id column additions (SQLite only)
  -- Migration 064 (064_correlation_ids_sqlite.sql):
  ALTER TABLE canonical_events ADD COLUMN trace_id TEXT;
  CREATE INDEX idx_canonical_trace ON canonical_events(trace_id);
  ALTER TABLE provider_sessions ADD COLUMN session_id TEXT;
  ALTER TABLE coverage_windows ADD COLUMN session_id TEXT;
  -- detection_events.session_id already exists in the DDL;
  -- no ALTER needed.

  -- Migration 069 (069_correlation_source_columns.sql):
  ALTER TABLE raw_provider_events
      ADD COLUMN source_trace_id TEXT;
  ALTER TABLE canonical_event_sources
      ADD COLUMN source_trace_id TEXT;
  ALTER TABLE canonical_event_sources
      ADD COLUMN canonical_trace_id TEXT;
  CREATE INDEX idx_raw_source_trace
      ON raw_provider_events(source_trace_id);
  CREATE INDEX idx_event_sources_source_trace
      ON canonical_event_sources(source_trace_id);
  CREATE INDEX idx_event_sources_canonical_trace
      ON canonical_event_sources(canonical_trace_id);

  -- signal_ledger and analysis_snapshots live in DuckDB;
  -- their trace_id columns are added in O.11.2 via
  -- migration 037 (037_correlation_ids_duckdb.sql).

O.11.2 DuckDB additions

  -- trace_spans (optional; populated when span instrumentation
  -- is enabled)
  CREATE TABLE trace_spans (
      trace_id TEXT NOT NULL,
      span_id TEXT NOT NULL,
      parent_span_id TEXT,
      component TEXT NOT NULL,
      operation TEXT NOT NULL,
      started_at BIGINT NOT NULL,
      ended_at BIGINT,
      status TEXT CHECK(status IN ('ok','error','cancelled')),
      attributes_json TEXT,
      PRIMARY KEY (trace_id, span_id)
  );
  CREATE INDEX idx_trace_spans_trace ON trace_spans(trace_id, started_at);

  -- slo_measurements
  CREATE TABLE slo_measurements (
      measurement_id TEXT PRIMARY KEY,
      slo_name TEXT NOT NULL,
      window_start BIGINT NOT NULL,
      window_end BIGINT NOT NULL,
      value DOUBLE NOT NULL,
      target DOUBLE NOT NULL,
      breached INTEGER NOT NULL DEFAULT 0,
      tier TEXT NOT NULL,
      recorded_at BIGINT NOT NULL
  );
  CREATE INDEX idx_slo_meas_name
      ON slo_measurements(slo_name, window_end);

  -- signal_ledger / analysis_snapshots trace_id
  -- (Migration 037: 037_correlation_ids_duckdb.sql)
  ALTER TABLE signal_ledger ADD COLUMN trace_id TEXT;
  ALTER TABLE analysis_snapshots ADD COLUMN trace_id TEXT;
  CREATE INDEX idx_ledger_trace ON signal_ledger(trace_id);
  CREATE INDEX idx_snapshot_trace ON analysis_snapshots(trace_id);

O.11.3 Retention
  observability_requests:            7 days
  observability_daily_summary:       1 year hot, 5 years warm
  trace_spans:                       30 days hot, 1 year warm
  slo_measurements:                  1 year hot, indefinite warm

O.11.4 Migration entries
  sqlite/
    061_observability_requests.sql
    062_observability_daily_summary.sql
    063_notifications_tier.sql
    064_correlation_ids_sqlite.sql
    068_notification_ack_domain.sql
    069_correlation_source_columns.sql
  duckdb/
    035_trace_spans.sql
    036_slo_measurements.sql
    037_correlation_ids_duckdb.sql

================================================================================
O.12 BUILD SEQUENCE
================================================================================

Stage 2.7 — Observability (new)

  2.7a  Health endpoint (localhost:8091 sidecar inside quantd).
  2.7b  Muse tool expansion (O.3 tools).
  2.7c  Log persistence policy (journald drop-ins; optional
        file mirror).
  2.7d  Correlation ID propagation (source_trace_id,
        canonical_trace_id, session_id, task_id, report_id).
  2.7e  SLO instrumentation (O.8).
  2.7f  Alerting tiers and escalation (O.7).
  2.7g  Daily status summary (O.9).
  2.7h  Dashboard views v1 (Muse-tool-driven; no external
        viz tool yet).

  Dependencies: Stage 2.6 (Operational Shell) must be
  complete. Observability reads from stores populated by
  Stage 2.5 and earlier.

Stage 3.5 — Dashboard visualization (optional, later)

  3.5a  Lightweight web UI (SvelteKit/Next.js) served
        through the existing Cloudflare Tunnel.
  3.5b  OR Grafana pointed at exported Parquet.

  Trigger to build: after v2.0.5.1 is running in production
  for ≥4 weeks, if the operator finds Muse tools insufficient.

================================================================================
O.13 VERIFICATION & ACCEPTANCE
================================================================================

O.13.1 Health endpoint
  1. GET /health returns 200 within 200 ms.
  2. Response shape matches O.2.3 schema.
  3. overall = 'critical' when any open notification with
     notification_domain = 'SYSTEM' has effective_tier =
     'critical'.
  3a. overall remains 'ok' or 'degraded' (not 'critical')
     when the only open critical-tier notification is
     notification_domain IN ('TACTICAL','RESEARCH').
  4. overall = 'degraded' when any open notification with
     notification_domain = 'SYSTEM' has effective_tier =
     'immediate'.
  4a. overall remains 'ok' when the only open
     immediate-tier notifications are
     notification_domain IN ('TACTICAL','RESEARCH').
  5. Endpoint binds to localhost only (external connect fails).
  6. Endpoint survives a component heartbeat stall (returns
     'timeout' for that component, overall degraded).

O.13.2 Muse tools
  7. Each O.3 tool returns a value matching its declared
     shape.
  8. get_correlation_trace(trace_id) returns rows across all
     tables listed in O.6.3.
  9. get_daily_summary(today) returns the same content as
     the emitted notification body.
 10. Read-only guard: attempting to write through any Muse
     tool fails (no write tools exposed).

O.13.3 Logs
 11. journald retention policy applied (systemd-analyze
     verify).
 12. Redaction: sample log lines contain no token-shaped
     strings.
 13. Log level change via quantctl is audited.

O.13.4 Correlation IDs
 14. A canonical event created in a synthetic test carries
     canonical_trace_id through to signal_ledger and
     analysis_snapshots.
 15. IPC envelope preserves source_trace_id from capture to
     quantd; raw_provider_events.source_trace_id is
     populated.
 16. get_correlation_trace(canonical_trace_id) returns the
     full chain across canonical_events,
     canonical_event_sources, signal_ledger, and
     analysis_snapshots.
 16a. get_correlation_trace(canonical_trace_id) also
     returns any zero_dte_cluster_members and
     zero_dte_cluster_snapshots rows resolvable by joining
     through member canonical_event_ids, annotated with
     "resolved_via": "member_join".
 16b. No table in the returned chain reads a trace_id
     column that does not exist in its DDL.

O.13.5 Alerting
 17. SYSTEM + requires_ack=1 + immediate + unacknowledged
     for 4 h → re-emit as escalation-required critical.
 17a. TACTICAL or RESEARCH notification of any tier,
     unacknowledged for 24 h → no escalation, no re-emit.
 18. SYSTEM + requires_ack=1 + critical + unacknowledged
     for 1 h → re-emit with [ESCALATED] prefix.
 18a. Acknowledging any row in an escalation chain stops
     further re-emits for that subject_key; the row stays
     open.
 18b. While an unacknowledged open descendant exists for a
     subject_key, no further re-emits are produced for that
     subject_key, regardless of age.
 19. Escalation task runs every 15 min.
 20. Escalation bypasses cooldown, and produces at most one
     re-emit per subject_key per ESCALATION_INTERVAL_S.
 20a. A synthetic 24-hour idle SYSTEM/immediate thread
     yields exactly one escalation-required re-emit at the
     4 h mark and no further rows until ack or resolve.

O.13.6 SLOs
 21. Each SLO in O.8.2 has a measurement task.
 22. Breach writes slo_measurements with breached = 1.
 23. Breach emits notification at the SLO's tier.
 24. Window rolling correctly (24 h by default).

O.13.7 Daily summary
 25. Emitted once per day at 08:00 ET.
 26. Content matches O.9.2 format.
 27. Delivered via Discord + email.
 28. Idempotent on (category, subject_key).

O.13.8 Failure modes
 29. Health endpoint crash: quantd continues; endpoint
     restarts within 30 s.
 30. Observability write failure: logged, counted, emits
     observability-write-failure warning; decision path
     unaffected.
 31. Muse unreachable: Discord + email continue to deliver.

O.13.9 Frozen-layer compliance
 32. Diff of ARCH v5.1.5.1 Vol 3 §F against the prior
     baseline remains empty except for the P0-8
     authorization provision (§F.0.2).
 33. No observability write touches a decision-path table
     (verified by SQL audit of the observability code's
     write surface).

O.13.10 Test suite additions
  The observability suite adds 33 tests as above. Suite
  may only grow.

================================================================================
O.14 IMPLEMENTATION NOTES (STACK)
================================================================================

O.14.1 Health endpoint
      FastAPI or aiohttp inside quantd (asyncio task).
      Port 8091, localhost only.
      Runs on the same event loop as quantd's main pipeline;
      must be non-blocking (all queries async or run in
      db_pool_executor).

O.14.2 Muse
      Existing Muse facade. Tools added per O.3.
      Auth via Cloudflare Access. Read-only.

O.14.3 Dashboards
      Stage 2.7: driven by Muse tools only (the operator uses
      a Muse client to query).
      Stage 3.5 (optional): SvelteKit or Next.js app served
      through the same tunnel, calling /health and read-only
      DB queries. Or Grafana, if the operator prefers.
      Recommendation: start with Muse tools; build UI only if
      needed.

O.14.4 Logs
      journald by default. Optional mirror to
      /var/quant/logs with logrotate.
      No external shipping in v2.0.5.1. Loki or equivalent is
      a Stage 3.5 consideration.

O.14.5 Correlation IDs
      source_trace_id generated at the capture boundary.
      canonical_trace_id generated at canonicalization.
      Both propagated via IPC envelope and stored in columns
      added in O.11.
      No spans required in v2.0.5.1; trace_spans table is
      optional instrumentation.

O.14.6 SLO evaluator
      Runs as a scheduled task every 5 min.
      Reads from the operational and analytical stores
      read-only.
      Writes only to slo_measurements and notifications.

O.14.7 Escalation runner
      Scheduled task every 15 min.
      Scans notifications for open rows past their escalation
      threshold; emits escalation-required.
      Writes only to notifications.

O.14.8 Resource budget
      Health endpoint: negligible (< 50 MB RSS).
      Observability tasks: < 100 MB additional quantd RSS.
      Total additional storage:
        observability_requests: ~50 MB / 7 days at peak.
        trace_spans: ~500 MB / 30 days at peak.
        slo_measurements: ~10 MB / year.
      No new processes required in v2.0.5.1.

================================================================================
O.15 FROZEN-LAYER COMPLIANCE STATEMENT
================================================================================

O.15.1 Observability is read-only with respect to the
       decision pipeline. It never writes to signal_ledger,
       signal_versions, analysis_snapshots, symbol_theses,
       thesis_versions, positions, position_legs,
       position_fills, delivery_outbox, or any table that
       participates in a trading decision.

O.15.2 Observability does not weaken anti-detection. No
       change in this volume modifies ARCH v5.1.5.1 Vol 3 §F.
       The frozen-layer diff remains empty except for the
       P0-8 authorization provision (§F.0.2), which
       strengthens the layer by adding a fail-closed
       condition.

O.15.3 Observability failures never block the pipeline.
       Fail-open is the contract (G3).

O.15.4 The SLO and alerting tiers do not create an
       alternate decision path. They are operator-facing
       metadata only.

O.15.5 The daily status summary is informational and carries
       no actionability.

================================================================================
O.16 LOCAL NARRATIVE SERVICE (RESERVED INTERFACE, DISABLED)
================================================================================

O.16.1 Status
       Reserved. Disabled by default. Not built in v2.0.5.1.
       Interface declared here so that future additions do
       not require touching the decision path.

O.16.2 Purpose
       Optional semantic narration of an immutable Analysis
       Snapshot. Plain-English summaries, explanations,
       structured text extraction. Never numeric.

O.16.3 Inputs
       analysis_snapshot_id only. The service MUST NOT read
       any live store, any provider, or any non-snapshot
       state.

O.16.4 Outputs
       A narrative block stored in
       report_runs.rendered_payload_json (key: "narrative")
       or in a future narrative_annotations table. NEVER
       written to:
         - analysis_snapshots (immutable, deterministic)
         - signal_versions (decision-path)
         - notifications.body (deterministic template)
         - symbol_theses, positions, or any decision table.

O.16.5 Constraints
       - Non-blocking: alerts do not wait for narration.
       - Non-authoritative: narration cannot alter decision,
         route, probability, target, stop, or size.
       - Fail-open: if narration fails, the report is still
         delivered without it.
       - No provider I/O.
       - No decision-path reads.
       - Deterministic-input only: same
         analysis_snapshot_id → same narration content
         (given same model version and prompt version).

O.16.6 Configuration
       Config key: observability.narrative.enabled
       (default: false). When false, the service is not
       invoked and no narrative block is written.

O.16.7 Verification
       - Test: with narrative.enabled = false, no behavior
         change and no new fields appear anywhere.
       - Test: with narrative.enabled = true, narration
         appears only in report_runs.rendered_payload_json
         and nowhere else.
       - Test: a narration failure does not delay, degrade,
         or alter any notification or decision.

================================================================================
END OF SPEC Vol 5 v2.0.5.1
================================================================================