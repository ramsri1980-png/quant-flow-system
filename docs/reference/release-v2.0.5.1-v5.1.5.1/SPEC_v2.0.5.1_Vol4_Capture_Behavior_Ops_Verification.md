# QUANT FLOW SYSTEM — SPECIFICATION v2.0.5.1
## VOLUME 4 — CAPTURE BEHAVIOR, DELIVERY, OPERATIONS,
##             VERIFICATION

Status: self-contained for the sections this volume owns.
Sections not owned by this volume reference the owning
volume within the 10-file set by section number. ARCH
v5.1.5.1 Vol 3 §F remains the authoritative anti-detection
text.

CHANGES FROM v2.0.5
- Header version bump to v2.0.5.1.
- No content changes. P0-1 through P0-8 are located in
  other volumes.
- §21 Stage 4 pointer to ARCH V4 §AH added.

CHANGES FROM THIS REVIEW (V01, V02)
- V01: §20.73 added, core correction acceptance tests
  (C01–C06) with the SQLite and DuckDB CHECK matrix, the
  exact-risk sizing golden, the paper-depth and fill
  identity tests, the day-clock and deadline tests, the
  durability/restart tests and the escalation/ack tests.
- V02: §18.14 gains the AH notification domain mapping
  (position-exit-required TACTICAL/ack=0; exit-monitor-
  failure and valuation-unavailable SYSTEM/ack=1 after the
  60 s while-open condition) resolved through SPEC Vol 5
  §O.10's category-policy function.

CHANGES FROM v2.0.4
- §11.2a cohort count reconciled to "3–5 total; 2–3 active".
- §18.9 DQ report: residuals separated from alarms.
- §18.14 notifications state enum lowercase canonical.
- §18.19 SPX cycle: setup window [06:00, 07:00]; verification
  opens at setup completion; newsletter timeout clock
  defined; behavioral reference note added.
- §20.71 test 7 reworded.
- §20.71 tests added (19–36).

================================================================================
SECTION 11 — ANTI-DETECTION LAYER (POLICY SUMMARY)
================================================================================

11.0 Authorization Precondition
  11.0.1 Authorized automated access only.
  11.0.2 MUST NOT be used for sources lacking automation
         authorization.
  11.0.3 Expired review → provider forced manual-only.
  11.0.4 CAPTCHA and challenges always resolved by the human
         operator; never automated.
  11.0.5 Fail closed on any ambiguity.
  11.0.6 Stock-Chrome probe environment is a separate
         activity with its own source_authorization entry.
  11.0.7 Persistent challenge or 403 on an automation_allowed
         source → route to authorization review; do not
         solve-and-continue.

11.1 Threat Model: fourteen layers.

11.2 Network Identity: routed namespace per ARCH Vol 3 §F.S.

11.2a Cohort Rotation
      3–5 total cohort profiles; 2–3 active at any time.
      profile↔provider binding via profile_cohort.provider.

11.3 TCP Fingerprint validated over real egress.
11.4 TLS Fingerprint pinned; storage in wire_pins.
11.4a Cross-Layer Compatibility Matrix evaluated at session
      start; INCOMPATIBLE aborts; UNKNOWN never passes.

11.5 TLS Session Resumption
     Negotiated via PSK in ClientHello. Not exposed in
     response headers. Observation requires a second
     connection (echo issues GOAWAY after first response).
     Scope: validates browser resumption against the echo;
     says nothing about the provider path.

11.6 HTTP/2 pinned per ARCH Vol 3 §F.R.4.

11.7 HTTP/3
     Status in v2.0.5.1: HTTP/3 fingerprint is NOT OBSERVED.
     Reported as a standing status line in the DQ report per
     §18.9. Full H3 pinning planned for v5.2.0.

11.8–11.9 per ARCH Vol 3 §F.

11.10 Session Lifecycle
      11.10.7 Bound to wire-observed fingerprint. Login IP
              logged separately; never part of the binding
              hash. IP changes do not invalidate the session.

11.11 Login
      11.11.9 Credentials via quantd-mediated
              credential-request/response IPC.
11.11a Protocol Stack Continuity: no mid-session switch.

11.12 Provider State Machine: see ARCH Vol 3 §F.N.

11.13 Behavioral Pacing
      11.13.7 No fixed cycle. All canary and pacing timing
              jittered.
      11.13.11 Navigation shape.

11.14–11.19 per ARCH Vol 3 §F.

11.20 Google Armor
      Weekly comparison between capture profile and a fresh
      minimal non-persistent context. Fallback context never
      contacts an authenticated endpoint. Exempted from the
      fresh-context prohibition. Alternative explanations
      recorded. 4 consecutive weeks → escalate.

11.21 SSRF Guard with loopback echo hostname exception.
11.22–11.24a per ARCH Vol 3 §F.

11.25 Prohibited
      All prior items. IP mismatch qualified: "No login-vs-
      API IP mismatch WITHIN a session. Cross-session IP
      changes are logged and alerted, not prohibited, and do
      not invalidate the session."

11.26 Challenge Detection with escalation per
      CHALLENGED_MANUAL_ESCALATION_DAYS.
11.27 Data Canaries per ARCH Vol 3 §F.J.
11.28 Behavioral History Comparison with circularity
      avoidance.
11.29 Adversarial Test Harness
      11.29.1 Runs daily; weekly audit reviews results.
11.30 Provider-Side Telemetry — Unobservable.
11.31 Chrome Release Tracking.
11.32 Reference Browser Verification
      11.32.3 Frozen fields include JA4, JA4S, JA4H,
              H2 SETTINGS hash, header order hash, ALPN,
              TCP fingerprint over the real egress.
11.33 Renderer & Interaction Hygiene.
11.34 Verification
      The acceptance suite lives in ARCH v5.1.5.1 Vol 3 §F.Q.
      Count not hard-coded here.

11.35 Continuous Degradation Monitoring (policy).
11.36 Faster Provider-Evolution Response (policy).
11.37 Reference-Pin Policy (F.R summary).
11.38 Network Isolation Policy (F.S summary).
11.39 Alert-Path Pattern Constructibility. Default
      Pattern 2.

================================================================================
SECTION 12 — HUMAN RHYTHM & READING
================================================================================

12.1 State Machine: CLOSED → WARMING → ACTIVE →
     WINDING_DOWN → CLOSED.
12.2 Reading: dwell per page from word-equivalent.
12.3 Scroll: variable velocity, pauses, occasional scroll-
     back.
12.4 Attention Drift: occasional drift and recovery.
12.5 Mouse: bezier + tremor + jitter; overshoot-correct.
12.6 Session Length
     Log-normal (median 30 min, σ_param 0.75), sampled with
     the rejection-sampling primitive.
     Range 15–60. Hard cap 60; terminates at cap.
     Session count by activity level:
       high     → 3–4 sessions
       medium   → 2 sessions
       low      → 1 session
       minimal  → 0–1 sessions
       off      → 0 sessions
     Second session on medium-activity and above.
     Sessions 3–4 on high-activity days only.
     Minimum inter-session gap 90 minutes.
     Pre-close cutoff: last session start ≤ 14:45 ET.
12.6a Session Lifecycle.
12.7 Daily Rhythm: 5-level distribution (high/medium/low/
     minimal/off weights 0.15/0.40/0.25/0.15/0.05).
12.8 Weekly Rhythm: Mon 1.2, Tue 1.0, Wed 1.0, Thu 1.0,
     Fri 0.7, Sat 0.15, Sun 0.05.
12.9 Vacation
     Holiday mode (no sessions on holiday dates) is a
     separate configuration from the weekly multipliers.
     Vacation mode operator-set via quantctl
     set-vacation-mode.
12.10–12.13 per ARCH Vol 3 §E.

================================================================================
SECTION 16 — ALERT DELIVERY & LIFECYCLE
================================================================================

16.1 Notification created on category match.
16.2 Channels: Discord, Resend, Mailgun, Muse.
16.3 Delivery per channel; independent; retries per §18.15.
16.4 Notifications written before delivery.
16.5 Retry and exhaustion per outbox state machine.
16.6 Alert-Path Trust per SPEC Vol 1 §2.27.
16.7 Rejected or malformed alerts logged with reason; never
     enter notifications as price-alert-triggered.

================================================================================
SECTION 18 — OPERATIONS, SECRETS, INTEGRATION
================================================================================

18.1 Operational ownership: single operator; every control
     action audited in operator_control_audit.
18.2 Secrets. Bitwarden Secrets Manager machine account.
     Access via environment variable BWS_ACCESS_TOKEN
     injected into quantd only, via encrypted systemd
     credential (LoadCredentialEncrypted). Least-privilege
     project scope: read-only on the provider credentials
     subvault. No .env file in any repository. The capture
     process (provider_capture_worker) and the rhythm
     scheduler never hold the token; credentials are
     delivered to capture only via the one-time-use
     quantd-mediated credential-request/response IPC
     (ARCH Vol 1 §B.7). Rotation at least quarterly
     (SPEC Vol 1 §4.1.7).
18.3 Config: parameters in the operational store; every
     change logged; no tuning via code.
18.4 Provider credentials rotation: at least quarterly.
18.5 TLS pin maintenance: see ARCH Vol 3 §F.R.
18.6 Corporate action ingestion: see SPEC Vol 1 §4.9.
18.7 Time discipline: NTP-synced; drift threshold 50 ms.
18.8 Backup barrier: see ARCH Vol 1 §M.1.

18.9 DQ Report
     Daily.

     Alarms (actionable defects):
       bad quotes, stale spot, source conflict, greek sign
       flips, quote rejects, fingerprint collisions,
       coverage gaps, canary drift, EWMA-shift, uncovered
       degradation modes, external-signal review pending.

     Standing residuals (permanent by design; reported but
     not alarmed):
       provider-side telemetry unknown (outside observation
       scope).
       HTTP/3 fingerprint unknown (echo does not negotiate
       H3; planned for v5.2.0).

18.10 Edge Cases.
18.11 Reviews
     Weekly: rhythm, engine preference, detection audit,
     dependencies, adversarial harness (previous 7 days),
     trace uniqueness, continuous degradation monitoring,
     provider-evolution response, external signal review.
     Monthly: behavioral drift comparison, calibration refit
     review.
     Quarterly: restore drill, authorization review,
     dependency deep review.
     Annually: canary coverage audit.
18.12 Muse.
18.13 Resource Budget.

18.14 Notifications

  Single table source of truth. Written before delivery.
  Channels are transports. Failure of one channel does not
  block another. All-fail readable. Muse reads the table
  only.

  Fields (canonical DDL names):
    notification_id, category, urgency, title, body,
    provider, subject_key, state, created_at, resolved_at,
    resolution_note, auto_resolve_condition, thesis_id,
    signal_id, signal_version, snapshot_id.

  Delivery record per channel (canonical DDL names):
    channel, attempt_at, status, error_detail,
    provider_response_id.

  Categories per SPEC Vol 1 §2.19.2.
  Urgencies: immediate, daily, informational.

  Category → urgency mapping:
    immediate:
      flow-alert-triggered, flow-state-change,
      flow-retraction, market-stand-down,
      price-alert-triggered, challenge-detected,
      fingerprint-incoherent, manual-intervention-required,
      session-blocked, login-failed, schema-changed,
      refresh-failed, data-quality-alarm,
      delivery-channel-degraded, scheduler-heartbeat-gap,
      zero-dte-flow-cluster, zero-dte-dealer-confirmed,
      zero-dte-cluster-reversal, zero-dte-cluster-retraction.
    daily:
      plan-requires-open-revalidation,
      dealer-flip-disagreement, canary-drift,
      backup-drill-result, weekly-audit-result,
      external-signal.
    informational:
      basis-tolerance-warning, behavioral-drift.

  AH mappings use SPEC Vol 5 O.10:
    position-exit-required -> TACTICAL, requires_ack=0, immediate;
    exit-monitor-failure -> SYSTEM, requires_ack=1, immediate;
    valuation-unavailable -> SYSTEM, requires_ack=1, immediate only
      after its existing 60s while-open fault condition.
  Resolve through the category-policy function, not a fallback default.
  Ordinary exits cannot lower system health or enter escalation.

  State enum (canonical, lowercase):
    open, resolved, expired.
    DDL CHECK constraint uses lowercase.

  Per-category cooldowns (seconds):
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
    zero-dte-cluster                86400 (legacy alias;
                                      not emitted)
    scheduler-heartbeat-gap         3600
    (all others)                    3600

  Observability tier extension (SPEC Vol 5 §O.7):
    The urgency field is preserved for backwards
    compatibility. A parallel tier field carries the
    extended semantics {critical, immediate, warning,
    informational, daily}. Consumers fall back to urgency
    when tier is NULL. See Vol 5 §O.7 for tier-to-category
    mapping and escalation rules.

  Resolution via quantctl resolve-notification
  <notification_id> --note "...". MUSE_ADMIN reserved; not
  enabled in v2.0.5.1.
  Auto-resolve. Age-out. Manual intervention stays open.

18.15 Email Delivery: Resend primary, Mailgun fallback, 2
     attempts each. 15-min retry job.

18.16 Muse Notification Tools
     pending_notifications, notification_detail.
     resolve_notification gated behind MUSE_ADMIN.

18.17 Scheduler Heartbeat: no heartbeat 15 min → immediate
     notification (category scheduler-heartbeat-gap,
     urgency immediate).

18.18 OpenMarket Price Alerts
     Free tier 5; configured cap 4.
     Alert-path pattern default Pattern 2.
     Config keys: openmarket.discord_webhook_url,
     openmarket.discord_listener_channel_id,
     openmarket.email_recipient,
     openmarket.escalation_gate_enabled,
     openmarket.escalation_watchlist.

18.19 Daily SPX Price Alert Cycle

     Purpose: automate daily SPX alert config and cleanup.
     Role: trigger channel. Notifies crossings. No trade
     signal. SPX only. Not overnight.
     Levels: from the morning newsletter pin zones.
     Ingestion path: newsletter retrieved by the operator via
     authorized source, parsed for pin zones, mapped to
     Market Map level_id / map_id before pre-market setup.
     Publication time: ~06:00 ET.
     Pre-market setup window: opens at 06:00 ET.
     Market Map pre-market build: completes by 06:00 ET.
     Alert spec: SPX. Max 4 (configurable max_daily_alerts).
     Composition: 2 upside + 2 downside. One of the four may
     be designated a flip level; the flip designation does
     not add a fifth slot.
     One-shot. Discord webhook + email.

     Pre-market setup scheduling:
       scheduled_tasks row with run_at sampled from
       Gaussian (μ = 06:45 ET, σ = 15 min) constrained to
       [06:00, 07:00] via the rejection-sampling primitive.

     Rationale for μ = 06:45 and window [06:00, 07:00]:
       newsletter publication is ~06:00. Sampling at 06:45
       gives retrieval time. Capping setup at 07:00
       guarantees at least 30 minutes for verification
       before the 07:30 close.

     Newsletter timeout clock (defined):
       NEWSLETTER_POLL_TIMEOUT_S (900) runs from the
       newsletter's publication time (~06:00 ET). If the
       newsletter is not retrieved and parsed by 06:15 ET,
       the day's SPX alert coverage is skipped; one daily
       notification records the gap. Fail-closed by design.
       Where the operator's retrieval obligation ("before
       06:15") and the poll timeout disagree, the 06:15
       clock governs.

     Post-close cleanup: scheduled_tasks row with run_at
     sampled from Gaussian (μ = 16:45 ET, σ = 15 min)
     constrained to [16:30, 17:30].

     Active-hours exemption: the OpenMarket cycle runs
     OUTSIDE the 07:00–16:00 ET flow-capture pacing window.
     The active-hours rule applies to flow-capture pacing
     only.

     Verification: opens at setup_completed_at; closes at
     07:30 ET. Strictly positive window guaranteed (setup
     ≤ 07:00). Count matches. Correct level and direction.
     Delivery confirmed. Cleanup by 17:30 ET. No overnight.
     Status COMPLETE. cycle_date per market calendar.
     On half-days, cycle_date is the calendar date of the
     half-day. Holidays produce no cycle row.

     Behavioral reference: the pre-market setup (~06:45) and
     post-close cleanup (~16:45) are recorded in
     behavioral_reference as an operator routine under
     reference_type = 'operator_routine'. The reference
     records the operator's acceptance that this is an
     automated task bound to the operator's own account.

     Non-goals: no individual symbol automation. No
     overnight. No data feed. No flip detection from alert.

18.20–18.24 Reserved. Referenced topics from earlier drafts
     (runbook index, incident response ladder, degraded-ops
     checklists, restore-drill records, external-review
     tracking) are not normative at v2.0.5.1. The operator's
     routine obligations are enumerated in §18.26.

18.25 Vacation Mode
      Operator-set via quantctl set-vacation-mode.
      Suppresses session scheduling for the specified range.
      Orthogonal to holiday mode.

18.26 Operator-Hours Budget
  18.26.1 Recurring obligations:
    Daily:
      - review DQ report
      - adversarial harness result review
      - newsletter retrieval before 06:15 ET
      - solve any CAPTCHA / challenge as raised
    Weekly:
      - rhythm review
      - engine preference review
      - detection audit
      - dependency review
      - adversarial harness weekly summary
      - trace uniqueness review
      - continuous degradation review
      - provider-evolution response review
      - external signal review
    Monthly:
      - behavioral drift comparison
      - calibration refit review
    Quarterly:
      - restore drill
      - authorization review
      - dependency deep review
    Annually:
      - canary coverage audit
    Chrome cadence (~4 weeks):
      - 7-day soak
      - weighted rollout (may span releases)

  18.26.2 Estimated weekly hours:
    Baseline (steady state):             6–9 h
    Quarterly drill week:                8–12 h
    CAPTCHA-heavy week (if challenges):  +2–4 h
    Chrome stable ships ~4 weeks; a Chrome bump week is the
    norm.

  18.26.3 Degraded-ops tier.
  18.26.4 Over budget two consecutive weeks → informational.

================================================================================
SECTION 20 — VERIFICATION & ACCEPTANCE
================================================================================

20.1 Categories with 0DTE Cluster Detection added.

20.2–20.70 Reserved. The acceptance suite at v2.0.5.1 is:
     - SPEC Vol 4 §20.71 (0DTE cluster detection, 36 tests)
     - SPEC Vol 4 §20.73 (core correction acceptance)
     - ARCH Vol 3 §F.Q (anti-detection, 84 + 18 tests)
     - SPEC Vol 5 §O.13 (observability, 33 tests)
     Additional acceptance tests referenced in earlier drafts
     are not normative at v2.0.5.1 and are deferred. The
     suite may only grow.

20.71 Zero-DTE Cluster Detection

  Detection and quality:
    1. Same raw alert repeated twice counts once.
    2. Same exchange event from Blackbox and Tradytics
       counts once.
    3. Two legs of a Tier 1/2 spread count as one package.
    4. Two low-quality events do not push.
    5. Unknown status mapping fails closed.
    6. Late/out-of-sequence event cannot qualify.
    7. Index/ETF symbol filter scope at ZERO_DTE_CLUSTER:
         Assert default symbol_filter rows at
         workflow_scope = 'ZERO_DTE_CLUSTER' ALLOW all
         equities (asset_type = EQUITY) and SPX (exact),
         and BLOCK ETFs and other indexes. A non-default
         blocked equity must have an explicit BLOCK row.
    8. Basic 2×2 cluster stores silently.

  Dealer, lifecycle and delivery:
    9. Same-session dealer map is immutable and cannot be
       replaced by next-day data.
   10. Flat/missing IV cannot confirm vanna.
   11. Negative-gamma level cannot be labeled support
       automatically.
   12. Cancellation can downgrade/retract a cluster.
   13. Separate opposite episode creates MIXED or reversal.
   14. One medium and one high push maximum per episode,
       absent reversal/retraction.
   15. Email is attempted independently of Discord.
   16. Episode expires at correct close; cluster_state =
       EXPIRED and episode_state = EXPIRED; member history
       preserved in zero_dte_cluster_member_history; a
       final snapshot is written with snapshot_type =
       'EXPIRY' (MEDIUM/HIGH episode, alert_grade = NULL,
       alert_ts = NULL, transition_ts NOT NULL) or 'BASIC_SHADOW' (alert_grade =
       'BASIC', alert_ts IS NULL).
   17. No route selected and no ACTIONABLE_NOW.
   18. Markouts/MFE/MAE computed only after horizon close,
       per (cluster_snapshot_id, horizon,
       calculation_version).

  Additional assertions (v2.0.5 additions):
   19. HIGH_CONFLUENCE cannot be emitted with a dealer map
       older than 300 s.
   20. OpposingShare = min(B,R)/(B+R); OpposingShare > 0.25
       cannot pass MEDIUM.
   21. Percentile cold start (default) retains cluster at
       cluster_grade = BASIC, cluster_state = ACTIVE when
       fewer than 10 trailing sessions exist.
   22. TESTING still active at close (no intraday
       confirmation, no false-cross) transitions to
       COOLDOWN with reason
       CONFIRMATION_NOT_ACHIEVED_AT_CLOSE.
   23. APPROACHING retreats to FAR when |spot − level|/spot
       > 0.005 (hysteresis).
   24. Member latency gate: a member with
       member_latency_ms > 3000 cannot count toward MEDIUM.
   25. Market-phase gate: MEDIUM cannot fire when
       market_phase ≠ REGULAR.
   26. Alert-age boundary: last_qualifying_event_age = 301
       cannot pass; = 300 passes.
   27. ConfluenceScore boundary: HIGH requires ≥ 0.80;
       0.79 fails.
   28. HIGH_CONFLUENCE cannot be emitted with coverage !=
       COMPLETE (PARTIAL, MANUAL_ONLY, UNKNOWN all fail).
   29. HIGH_CONFLUENCE cannot be emitted with a dealer map
       whose expiration scope does not match the cluster's
       expiration.
   30. Restart during an active episode produces an
       identical episode_id (deterministic sha256 per
       ARCH Vol 4 §D.14d).
   31. Changing only price behavior cannot change
       GammaAlign or VannaAlign; changing only dealer-map
       structure cannot change P_c.
   32. SPX TESTING → CONFIRMED_BREAKOUT fires intraday
       when a 1m bar closes beyond the level by more than
       SPX_CONFIRMATION_BUFFER_PCT × spot and spot holds
       beyond for SPX_CONFIRMATION_HOLD_S (60 s). No
       close-of-day gate; no SPX_CONFIRM_WINDOW_S
       dependency.
   33. SPX TESTING → CONFIRMED_REVERSAL fires intraday on
       the mirrored rule.
   34. 0DTE cluster detector: TSLA (equity) is accepted;
       SPY, QQQ, IWM (ETFs) are rejected; SPX (index) is
       accepted; other ETFs/indexes are rejected. This is
       asserted at workflow_scope = 'ZERO_DTE_CLUSTER'
       through symbol_filter.
   35. Operator blocklist realized as a symbol_filter BLOCK
       row at ZERO_DTE_CLUSTER scope overrides the default
       ALLOW rule: a listed equity is rejected even though
       the rule would accept it.
   36. DirectionalStrength = 1 − 2·OpposingShare =
       |B − R| / (B + R). At OpposingShare = 0.25 (gate
       boundary), DirectionalStrength = 0.5. At B = R
       (balanced flow), DirectionalStrength = 0.
       SignedDirectionalImbalance = (B − R) / (B + R); its
       absolute value equals DirectionalStrength.

20.72 (Reserved. See §20.71 (0DTE cluster detection) and §20.73 (core correction acceptance) for the normative acceptance suite.)

20.73 Core correction acceptance (C01–C06)

  Snapshot SQL: test the Cartesian matrix of six snapshot_type values,
  grades {NULL,BASIC,MEDIUM_CONFLUENCE,HIGH_CONFLUENCE,INVALID} and
  timestamps {NULL,valid_epoch_ms}. Only ALERT+MEDIUM/HIGH+timestamp,
  BASIC_SHADOW+BASIC+NULL and lifecycle-only+NULL+NULL may insert.
  Execute in SQLite (predicate probe) AND native DuckDB (real table).

  Risk: standard $100 short put / $200 credit / multiplier 100 gives
  $9,800 max loss at S=0, not $8,800 at S=$10. Long call loss=debit and
  unbounded profit does not mean unbounded loss. Unsupported calendar
  or adjusted deliverable returns unavailable. Scaling quantity or
  multiplier applies once. Zero/unbounded/unknown loss never sizes.

  Fills: 1:1, depth 100/100 -> capacity 25 before remaining-position cap;
  1:2, depth 100/100 -> capacity 12; depth absent -> no paper fill.
  Same quote/side cannot fund a second batch or another position.
  Exact source execution replay is a no-op; missing identity rejected;
  same execution reallocated to another position rejected.

  Clock: Friday 15:00 entry with a 6-session-hour horizon -> next
  regular session 14:30 absent a tighter bound (ordinary 09:30-16:00
  sessions). Half-days clamp correctly; holidays skip; halt time counts.
  AM-settled contracts use verified last_trade_at. A mandatory pre-0DTE
  bound precedes expiry-day trading; no 0DTE entry relabeling occurs.
  Simultaneous GAP and PREMIUM records both and selects GAP.

  Durability: duplicate theta interval adds zero; adjoining intervals
  with the same model hash both add once; overlapping/gap interval is
  blocked. Fill boundary splits old/new quantities. Restart preserves
  active policy, basis, clock cursor, deadline, latches and partial fills.
  DuckDB outage retains SQLite state/notifications and queued mirror.
  Crash after mirror insert before ACK does not duplicate history.
  SQLite failure cannot be reported as successful committed monitoring.

  Alerts: normal exit is TACTICAL/ack=0; monitor failure SYSTEM/ack=1.
  First overdue SYSTEM root may escalate; duplicate scheduler poll
  cannot create the same escalation step twice; acknowledgement anywhere
  suppresses future steps. TACTICAL/RESEARCH never escalate.

  Migration: same adopted-module set gives identical fresh/upgrade
  schemas. Adopting AF 044 before AE 043 must not skip 043 later.
  Unknown legacy identities or NOT NULL backfills stop with a report,
  never fabricate values. Retain all original evidence.

================================================================================
SECTION 21 — BUILD SEQUENCE
================================================================================

21.1 Six stages. Sequential.
21.2 Stage 0 — Pre-Code Setup
21.3 Stage 1 — Kernels (adds 0DTE cluster detector kernel)
21.4 Stage 2 — Storage & Delivery (includes new tables)
21.5 Stage 2.1 — Dealer + Technical Level Services
21.6 Stage 2.2 — Historical Backfill
21.6a Stage 2.3 — Scheduled Task Infrastructure
21.6b Stage 2.4 — Fingerprint Registry & Audit
21.7 Stage 2.5 — Anti-Detection & Human Realism
21.8 Stage 2.6 — Operational Shell
21.8b Stage 2.7 — Observability (per SPEC Vol 5 §O.12):
      health endpoint, Muse tool expansion, log persistence,
      correlation IDs, SLO instrumentation, alerting tiers,
      daily status summary, dashboard views v1.
      Dependencies: Stage 2.6 complete.
21.8a Stage 3.1 — SPX Crossing FSM
21.9 Stage 3 — First Source
21.10 Stage 3.2 — Flow Workflow (0DTE cluster active)
21.11 Stage 3.3 — Morning Workflow
21.12 Stage 3.4 — Ad Hoc Workflow
21.13 Stage 4 — Forward Paper
      Stage 4 MUST adopt ARCH v5.1.5.1 Vol 4 §AH as the
      binding route-specific exit contract before any
      position-carrying lane opens a position. Without a
      declared exit handler per §15.5, no route can reach
      ACTIONABLE_NOW.
21.14 Stage 5 — Ongoing
21.15 Scope Note

v2.0.5.1 key changes:
- P0-1 all_pass → signal_valid (SPEC Vol 3 §8.1a).
- P0-2 ZERO_DTE_CLUSTER workflow scope replaces ticker
  allowlist.
- P0-3 lifecycle-only cluster_state; deterministic
  episode_id.
- P0-4 evidence fields renamed to immutable observation
  IDs.
- P0-5 0DTE cluster levels in _mills.
- P0-6 snapshot_type on zero_dte_cluster_snapshots; BASIC
  episodes write BASIC_SHADOW at expiry.
- P0-7 §22.4 manifest dedup; §22.6 reference rule.
- P0-8 §F.0.2 authorization provision.

================================================================================
END OF SPEC Vol 4 v2.0.5.1
================================================================================