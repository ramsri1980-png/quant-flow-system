# QUANT FLOW SYSTEM — SPECIFICATION v2.0.5.1
## VOLUME 2 — DATA SOURCES, CANONICALIZATION, QUALITY

Status: self-contained for the sections this volume owns.
Sections not owned by this volume reference the owning
volume within the 10-file set by section number.

CHANGES FROM v2.0.5
- P0-2: symbol_filter and provider_query_budget CHECK
  constraints include ZERO_DTE_CLUSTER.
- P0-3: zero_dte_cluster_current cluster_state is
  lifecycle-only.
- P0-4: positions and analysis_snapshots evidence fields
  renamed to immutable observation IDs.
- P0-5: 0DTE cluster level columns use _mills; spot
  references remain _micros.
- P0-6: zero_dte_cluster_snapshots gains snapshot_type;
  alert_grade CHECK narrowed to MEDIUM/HIGH only; add
  transition_ts; invariant Y rewritten.
- B4: all DuckDB TIMESTAMP columns converted to BIGINT.
- B7.1: notifications gains notification_domain,
  requires_ack, acknowledged_at, acknowledged_by,
  escalated_from_notification_id.
- AH: §19.2 position_exit_policies, broker_cutoff_registry,
  position_fills extension; §19.3 exit_evaluations,
  ivr_history; §19.6 invariants AQ/AR/AS.

CHANGES FROM THIS REVIEW (DB01-DB08)
- DB01: snapshot composite CHECK rewritten NULL-safe.
- DB02: invariant Y prose aligned with the CHECK.
- DB03: position_fills rebuilt with non-null execution
  identity and fill_origin. broker/account_ref/
  execution_id/execution_leg_key are all NOT NULL.
- DB03b: uq_fill_dedup replaces the nullable partial
  index with a non-null four-column unique key.
- DB04: position_exit_state, position_exit_events and
  pending_exit_sync added as operational exit tables.
- DB05: exit_evaluations rewritten as a reconstructable
  analytical mirror with operational_event_id and
  payload_json/payload_hash.
- DB06: invariants AQ-AS replaced; AT and AU added for
  theta continuity and durable operational exit.
- DB07: stale snapshot comment replaced.
- DB08: schema-hardening summary aligned.

CHANGES FROM v2.0.4
- §5.8.5 family aliases added.
- §7.6 default symbol_filter rows pinned.
- §19.2.55 zero_dte_cluster_current: grade/state/episode
  split; UNIQUE(episode_id); new columns.
- §19.2.57 zero_dte_cluster_member_history added.
- §19.3.9 signal_outcomes: materialized outcome_scope_id.
- §19.3.35/36 zero_dte_cluster_snapshots and _outcomes
  rewritten.
- §19.6 invariants extended.
- Schema hardening per §19.9.
- Migration entries added.

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
4.1.3 Status enum: APPROVED, PENDING, DISABLED, EXPIRED.
4.1.4 Rules: refuse unless APPROVED and unexpired; auto-
      expire; endpoint allowlist; daily check.
4.1.5 automation_allowed: INTEGER NOT NULL DEFAULT 0.
      Absence of clarity fails closed.
4.1.6 ToS-permitting-provision requirement (see SPEC Vol 1
      §4.1.6). Absence fails closed.
4.1.7 Secrets rotation at least quarterly.
4.1.7a Persistent challenge/403 on automation_allowed=1 →
       suspend, route to authorization review. Do not
       solve-and-continue.
4.1.7b review_expiry_at tied to tos_version.
4.1.7c Written per-source determination stored in record.

4.2 Authorized Categories
4.2.1 Free public.
4.2.2 Free-tier APIs.
4.2.3 Licensed paid.
4.2.4 Operator UI sessions.
4.2.5 Hyperliquid (via adapter).
4.2.6 OpenMarket.
4.2.7 Authorized listed-option quote source.
4.2.8 Trading calendar: Primary Cboe/official exchange;
      Fallback NYSE published holiday schedule.

4.3 Authorization Retention
4.4 Data Retention
4.5 Degradation
4.6 CFTC COT (canonical): TFF family; fields, cadence,
    storage, fail-closed per SPEC Vol 1 §4.6.
4.7 Leveraged ETF Mechanical-Pressure Research per SPEC Vol 1
    §4.7.
4.8 Authorized Real-Time Listed-Option Quote Source per
    SPEC Vol 1 §4.8.
4.9 Corporate Action Ingestion per SPEC Vol 1 §4.9.

================================================================================
SECTION 5 — CANONICAL EVENT & DEDUPLICATION
================================================================================

5.1 Raw Event Archive
5.2 Canonical Event (event-time NBBO preserved)
5.3 Deduplication Fingerprint priority:
    exchange_execution_id → provider_event_id → content hash.
5.4 Cross-Provider Corroboration: one canonical event + many
    sources rows; never double-counts premium.
5.5 Relationship Classes: INDEPENDENT_REPEATED_FLOW,
    RELATED_CLUSTER, SAME_THESIS_UPDATE, SUPERSEDES.
5.6 Corrections and Out-of-Sequence Events: recorded with
    correction_status.
5.7 Persistent Idempotency survives restart.

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
5.8.5 normalized_meaning enum: RAPIDFIRE, REPEATER, STEADY,
      RAPIDFIRE_BEARISH, REPEATER_BEARISH, STEADY_BEARISH,
      UNKNOWN. Family aliases:
        RAPIDFIRE_FAMILY = { RAPIDFIRE, RAPIDFIRE_BEARISH }
        REPEATER_FAMILY  = { REPEATER,  REPEATER_BEARISH  }

================================================================================
SECTION 6 — DATA QUALITY GATEWAY
================================================================================

6.1 Grades: A/B actionability-eligible; C watch-only; D/F
    prohibited from the decision path.
6.2 Checks: freshness, staleness, source conflict, greek
    sign, spread width, coverage, canary agreement.
6.3 Quote Rejection Reasons: stale, crossed, wide, size
    zero, malformed, unknown source.
6.4 Coverage Caps: PARTIAL 0.70, MANUAL_ONLY 0.50, UNKNOWN
    0.00. Applied inside weighted sum.
6.5 Critical Evidence
6.6 Coverage and Thesis Interaction
6.7 Grade Propagation

================================================================================
SECTION 7 — CANDIDATE ENGINE
================================================================================

7.1–7.5 per SPEC Vol 1 §7.
7.6 Symbol Filter default rows per SPEC Vol 1 §7.6.
7.7 Corporate Action Hard Gate.
7.8 Funnel.
7.9 Passing Candidates.

================================================================================
SECTION 19 — DATA MODEL (CANONICAL DDL)
================================================================================

19.1 Storage Split

19.1.1 SQLite operational store at /data/quant_state.db.
19.1.2 DuckDB analytical store at /data/quant_flow.duckdb.
19.1.3 Both on external encrypted volume.
19.1.4 Decision-critical state is not only in the analytical
       store.

19.2 Operational Entities (SQLite)

SQLite pragmas at open:
  journal_mode = WAL;
  synchronous = NORMAL;
  cache_size = -16000;
  temp_store = MEMORY;
  mmap_size = 268435456;
  foreign_keys = ON;
  busy_timeout = 5000;

WAL discipline: PRAGMA wal_checkpoint(TRUNCATE) forced
during low-activity session breaks and whenever
quant_state.db-wal exceeds WAL_SIZE_CEILING_MB. Persistent
failure raises data-quality-alarm.

SQLite date convention: TEXT ISO 8601 YYYY-MM-DD.
Timestamps: UTC epoch ms (INTEGER 64-bit).

-- schema_version_sqlite
CREATE TABLE schema_version_sqlite (
    migration_id TEXT PRIMARY KEY,
    checksum TEXT NOT NULL,
    applied_at INTEGER NOT NULL,
    app_version TEXT NOT NULL,
    result TEXT NOT NULL CHECK(result IN ('OK','FAILED'))
);

-- source_authorization
CREATE TABLE source_authorization (
    source_id TEXT PRIMARY KEY,
    provider_name TEXT NOT NULL,
    access_channel TEXT NOT NULL,
    license_tier_id TEXT,
    tos_version TEXT,
    tos_url TEXT,
    approved_endpoint_list TEXT NOT NULL,
    authorization_reference TEXT NOT NULL,
    permitted_data TEXT NOT NULL,
    permitted_retention_days INTEGER,
    permitted_frequency TEXT,
    personal_use_only INTEGER NOT NULL DEFAULT 1,
    redistribution_allowed INTEGER NOT NULL DEFAULT 0,
    automation_allowed INTEGER NOT NULL DEFAULT 0,
    entitlement_reference TEXT,
    sensitivity_class TEXT CHECK(sensitivity_class IN
        ('HIGH','MEDIUM','LOW')),
    approved_by TEXT NOT NULL,
    approved_at INTEGER NOT NULL,
    review_expiry_at INTEGER NOT NULL,
    last_reviewed_at INTEGER NOT NULL,
    owner TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN
        ('APPROVED','PENDING','DISABLED','EXPIRED'))
);

-- security_policies
CREATE TABLE security_policies (
    key TEXT PRIMARY KEY,
    value_int INTEGER,
    value_str TEXT,
    risk_note TEXT NOT NULL,
    updated_at INTEGER NOT NULL
);

-- provider_sessions
CREATE TABLE provider_sessions (
    provider TEXT PRIMARY KEY,
    token_type TEXT NOT NULL,
    token_expires_at INTEGER,
    cookie_expires_at INTEGER,
    last_refresh_at INTEGER,
    refresh_fail_count INTEGER DEFAULT 0,
    wire_fingerprint_hash TEXT NOT NULL,
    login_ip TEXT NOT NULL,
    login_geo TEXT NOT NULL,
    is_valid INTEGER DEFAULT 1,
    session_id TEXT,
    updated_at INTEGER NOT NULL
);

-- provider_state
CREATE TABLE provider_state (
    provider TEXT PRIMARY KEY,
    state TEXT NOT NULL CHECK(state IN
        ('HEALTHY','DEGRADED','CHALLENGED','MANUAL_REQUIRED',
         'BLOCKED','COOLDOWN','AUTH_REQUIRED','SCHEMA_CHANGED',
         'DISABLED')),
    reason TEXT,
    entered_at INTEGER NOT NULL,
    review_after INTEGER,
    updated_at INTEGER NOT NULL
);

-- provider_rate_limits
CREATE TABLE provider_rate_limits (
    provider TEXT PRIMARY KEY,
    requests_this_minute INTEGER DEFAULT 0,
    requests_today INTEGER DEFAULT 0,
    last_reset_minute INTEGER,
    last_reset_day INTEGER,
    ceiling_per_minute INTEGER NOT NULL,
    ceiling_per_day INTEGER NOT NULL,
    last_request_at INTEGER,
    next_break_threshold INTEGER,
    requests_since_break INTEGER DEFAULT 0,
    updated_at INTEGER NOT NULL
);

-- provider_instrument_map
CREATE TABLE provider_instrument_map (
    provider TEXT NOT NULL,
    canonical_ticker TEXT NOT NULL,
    provider_symbol TEXT NOT NULL,
    asset_type TEXT NOT NULL CHECK(asset_type IN
        ('EQUITY','ETF','INDEX','FUTURE','PERP','OTHER')),
    valid_from INTEGER NOT NULL,
    valid_to INTEGER,
    mapping_version TEXT NOT NULL,
    PRIMARY KEY (provider, canonical_ticker, valid_from)
);

-- provider_capabilities
CREATE TABLE provider_capabilities (
    provider TEXT PRIMARY KEY,
    supports_rt_spot INTEGER NOT NULL DEFAULT 0,
    supports_rt_options INTEGER NOT NULL DEFAULT 0,
    supports_historical INTEGER NOT NULL DEFAULT 0,
    supports_programmatic_ts INTEGER NOT NULL DEFAULT 0,
    entitlement_reference TEXT,
    updated_at INTEGER NOT NULL
);

-- provider_alert_attributes
CREATE TABLE provider_alert_attributes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    raw_event_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    raw_color TEXT,
    normalized_meaning TEXT CHECK(normalized_meaning IN
        ('RAPIDFIRE','REPEATER','STEADY',
         'RAPIDFIRE_BEARISH','REPEATER_BEARISH','STEADY_BEARISH',
         'UNKNOWN')),
    mapping_version TEXT,
    alert_type TEXT,
    trade_type TEXT,
    sweep_flag INTEGER,
    block_flag INTEGER,
    multi_leg_flag INTEGER,
    oi_exceeded INTEGER,
    repeated_oi_exceedance INTEGER,
    canceled INTEGER NOT NULL DEFAULT 0,
    late_or_out_of_sequence INTEGER NOT NULL DEFAULT 0,
    provider_timestamp INTEGER,
    FOREIGN KEY (raw_event_id)
        REFERENCES raw_provider_events(raw_id)
);
CREATE INDEX idx_paa_raw ON provider_alert_attributes(raw_event_id);
CREATE INDEX idx_paa_provider
    ON provider_alert_attributes(provider, provider_timestamp);

-- live_price_current
CREATE TABLE live_price_current (
    ticker TEXT PRIMARY KEY,
    observation_id TEXT NOT NULL,
    price_micros BIGINT NOT NULL,
    price_basis TEXT NOT NULL CHECK(price_basis IN
        ('CASH_INDEX','EQUITY_LAST','NBBO_MID','PERP_MARK','PROXY',
         'DELAYED','CACHED')),
    source TEXT NOT NULL,
    is_synthetic_proxy INTEGER NOT NULL DEFAULT 0,
    basis_vs_reference_bps REAL,
    reference_source TEXT,
    provider_ts INTEGER NOT NULL,
    received_at INTEGER NOT NULL,
    staleness_ms INTEGER NOT NULL,
    quality_flag TEXT NOT NULL,
    valid_until INTEGER,
    updated_at INTEGER NOT NULL
);

-- option_quote_current (hardened)
CREATE TABLE option_quote_current (
    provider TEXT NOT NULL,
    contract_id TEXT NOT NULL,
    observation_id TEXT NOT NULL,
    bid_cents INTEGER NOT NULL CHECK(bid_cents >= 0),
    ask_cents INTEGER NOT NULL CHECK(ask_cents >= bid_cents),
    last_cents INTEGER,
    bid_size INTEGER CHECK(bid_size IS NULL OR bid_size >= 0),
    ask_size INTEGER CHECK(ask_size IS NULL OR ask_size >= 0),
    provider_ts INTEGER NOT NULL,
    received_at INTEGER NOT NULL,
    staleness_ms INTEGER NOT NULL,
    correction_status TEXT,
    quality_flag TEXT NOT NULL,
    expires_at INTEGER NOT NULL,
    PRIMARY KEY (provider, contract_id)
);
CREATE INDEX idx_option_quote_expires
    ON option_quote_current(expires_at);

-- package_quote_current (hardened)
-- package_quote_current.package_quote_id is an operational
-- cache key only. It MUST NOT be written into any
-- decision-path table (see §19.6 invariant AM).
CREATE TABLE package_quote_current (
    package_quote_id TEXT PRIMARY KEY,
    observation_id TEXT NOT NULL,
    route TEXT NOT NULL,
    legs_hash TEXT NOT NULL,
    net_bid_cents INTEGER NOT NULL,
    net_ask_cents INTEGER NOT NULL CHECK(net_ask_cents >= net_bid_cents),
    net_mid_cents INTEGER,
    observed_at INTEGER NOT NULL,
    staleness_ms INTEGER NOT NULL,
    synchronized INTEGER NOT NULL,
    executable INTEGER NOT NULL,
    provider TEXT NOT NULL,
    quality_flags_json TEXT NOT NULL,
    expires_at INTEGER NOT NULL,
    UNIQUE(provider, legs_hash)
);
CREATE INDEX idx_pkg_quote_expires
    ON package_quote_current(expires_at);

-- signals
CREATE TABLE signals (
    signal_id TEXT PRIMARY KEY,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    latest_version INTEGER NOT NULL DEFAULT 1,
    current_state TEXT NOT NULL CHECK(current_state IN
        ('NO_ACTIVE_FLOW_THESIS','CANDIDATE','WATCH',
         'VALIDATED_PENDING_ENTRY','ACTIONABLE_NOW',
         'PORTFOLIO_BLOCKED','ENTRY_UNAVAILABLE','STAND_DOWN',
         'INVALIDATED','RETRACTED','EXPIRED','COMPLETED')),
    ticker TEXT NOT NULL,
    primary_contract_symbol TEXT,
    thesis_id TEXT,
    paper_mode TEXT NOT NULL DEFAULT 'RESEARCH'
        CHECK(paper_mode IN
        ('RESEARCH','PAPER','MANUAL_LIVE_DECISION_SUPPORT')),
    FOREIGN KEY (thesis_id) REFERENCES symbol_theses(thesis_id)
);
CREATE INDEX idx_signals_thesis ON signals(thesis_id);

-- signal_versions
CREATE TABLE signal_versions (
    signal_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    created_at INTEGER NOT NULL,
    previous_version INTEGER,
    decision_state TEXT NOT NULL,
    analysis_snapshot_id TEXT,
    selected_route TEXT,
    route_status TEXT CHECK(route_status IN
        ('EXECUTABLE','NOT_APPLICABLE','UNROUTED')),
    position_id TEXT,
    ruleset_version TEXT NOT NULL,
    feature_version TEXT NOT NULL,
    reason_for_change TEXT NOT NULL,
    changed_fields_json TEXT,
    payload_json TEXT NOT NULL,
    PRIMARY KEY (signal_id, version),
    FOREIGN KEY (signal_id) REFERENCES signals(signal_id),
    FOREIGN KEY (signal_id, previous_version)
        REFERENCES signal_versions(signal_id, version)
);
-- selected_route nullable. Route-free signals (e.g. 0DTE
-- research clusters) set route_status = 'NOT_APPLICABLE' and
-- leave selected_route NULL.

-- delivery_outbox
CREATE TABLE delivery_outbox (
    delivery_id INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    channel TEXT NOT NULL CHECK(channel IN
        ('discord','resend','mailgun','muse')),
    notification_id TEXT,
    payload_json TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN
        ('pending','in_progress','delivered','failed','exhausted')),
    fatal_delivery_error INTEGER NOT NULL DEFAULT 0,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 6,
    created_at INTEGER NOT NULL,
    last_attempt_at INTEGER,
    next_attempt_at INTEGER,
    locked_at INTEGER,
    lock_owner TEXT,
    delivered_at INTEGER,
    last_error TEXT,
    UNIQUE(signal_id, version, channel),
    FOREIGN KEY (signal_id, version)
        REFERENCES signal_versions(signal_id, version)
);
CREATE INDEX idx_outbox_pending
    ON delivery_outbox(status, next_attempt_at);

-- pending_ledger_sync
CREATE TABLE pending_ledger_sync (
    signal_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    snapshot_id TEXT,
    payload_hash TEXT,
    queued_at INTEGER NOT NULL,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    next_retry_at INTEGER,
    last_error TEXT,
    PRIMARY KEY (signal_id, version),
    FOREIGN KEY (signal_id, version)
        REFERENCES signal_versions(signal_id, version)
);
CREATE INDEX idx_pending_ledger ON pending_ledger_sync(queued_at);

-- position_exit_policies (AH)
CREATE TABLE position_exit_policies (
    position_id TEXT NOT NULL,
    policy_hash TEXT NOT NULL,
    policy_json TEXT NOT NULL,
    handler_version TEXT NOT NULL,
    activated_at INTEGER NOT NULL,
    entry_manifest_json TEXT NOT NULL,
    PRIMARY KEY (position_id, policy_hash),
    FOREIGN KEY (position_id) REFERENCES positions(position_id)
);
CREATE INDEX idx_exit_policy_activated
    ON position_exit_policies(activated_at);

-- broker_cutoff_registry (AH)
CREATE TABLE broker_cutoff_registry (
    broker TEXT PRIMARY KEY,
    forced_liquidation_cutoff_local TEXT,
    settlement_cutoff_local TEXT,
    calendar_id TEXT NOT NULL,
    explicitly_absent INTEGER NOT NULL DEFAULT 0
        CHECK(explicitly_absent IN (0,1)),
    reason TEXT,
    updated_at INTEGER NOT NULL
);

-- AH operational state: one active policy pointer per position.
CREATE TABLE position_exit_state (
    position_id TEXT PRIMARY KEY NOT NULL,
    active_policy_hash TEXT NOT NULL,
    policy_activation_id TEXT NOT NULL,
    policy_activated_at INTEGER NOT NULL,
    entry_premium_basis_cents INTEGER CHECK(entry_premium_basis_cents > 0),
    entry_completed_at INTEGER,
    quantity_revision INTEGER NOT NULL CHECK(quantity_revision >= 0),
    state_revision INTEGER NOT NULL CHECK(state_revision >= 0),
    theta_consumed_microcents INTEGER NOT NULL DEFAULT 0
        CHECK(theta_consumed_microcents >= 0),
    last_theta_interval_end_at INTEGER,
    last_model_manifest_hash TEXT,
    hard_deadline_at INTEGER NOT NULL,
    deadline_manifest_json TEXT NOT NULL,
    latched_triggers_json TEXT NOT NULL,
    exit_progress TEXT NOT NULL CHECK(exit_progress IN
        ('PENDING_ENTRY','MONITORING','EXIT_REQUIRED','PARTIALLY_CLOSED',
         'CLOSED','MANUAL_REVIEW')),
    evaluation_status TEXT NOT NULL CHECK(evaluation_status IN
        ('READY','EVALUATION_BLOCKED','EXIT_DUE_UNPRICED',
         'EXIT_DUE_PENDING_MARKET')),
    updated_at INTEGER NOT NULL,
    FOREIGN KEY (position_id) REFERENCES positions(position_id),
    FOREIGN KEY (position_id, active_policy_hash)
        REFERENCES position_exit_policies(position_id, policy_hash),
    CHECK ((entry_completed_at IS NULL AND entry_premium_basis_cents IS NULL)
        OR (entry_completed_at IS NOT NULL AND entry_premium_basis_cents IS NOT NULL))
);

-- Payload facts are append-only. Sync retries live in pending_exit_sync.
CREATE TABLE position_exit_events (
    event_id TEXT PRIMARY KEY NOT NULL,
    position_id TEXT NOT NULL,
    policy_hash TEXT NOT NULL,
    policy_activation_id TEXT NOT NULL,
    state_revision INTEGER NOT NULL CHECK(state_revision > 0),
    quantity_revision INTEGER NOT NULL CHECK(quantity_revision >= 0),
    event_type TEXT NOT NULL CHECK(event_type IN
        ('POLICY_ACTIVATED','ENTRY_BASIS_FROZEN','FILL_APPLIED',
         'THETA_INTERVAL','EVALUATION','OPERATOR_OVERRIDE','CLOSED')),
    occurred_at INTEGER NOT NULL,
    input_manifest_hash TEXT NOT NULL,
    interval_start_at INTEGER,
    interval_end_at INTEGER,
    theta_delta_microcents INTEGER,
    payload_json TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    UNIQUE(position_id, state_revision),
    FOREIGN KEY (position_id) REFERENCES positions(position_id),
    FOREIGN KEY (position_id, policy_hash)
        REFERENCES position_exit_policies(position_id, policy_hash),
    CHECK ((event_type = 'THETA_INTERVAL'
            AND interval_start_at IS NOT NULL AND interval_end_at IS NOT NULL
            AND interval_end_at > interval_start_at
            AND theta_delta_microcents IS NOT NULL AND theta_delta_microcents >= 0)
        OR (event_type <> 'THETA_INTERVAL'
            AND interval_start_at IS NULL AND interval_end_at IS NULL
            AND theta_delta_microcents IS NULL))
);
CREATE INDEX idx_exit_events_position
    ON position_exit_events(position_id, occurred_at);
CREATE UNIQUE INDEX uq_exit_theta_interval
    ON position_exit_events(position_id, policy_activation_id,
                            interval_start_at, interval_end_at,
                            quantity_revision, input_manifest_hash)
    WHERE event_type = 'THETA_INTERVAL';

CREATE TABLE pending_exit_sync (
    evaluation_id TEXT PRIMARY KEY NOT NULL,
    operational_event_id TEXT NOT NULL UNIQUE,
    queued_at INTEGER NOT NULL,
    attempt_count INTEGER NOT NULL DEFAULT 0 CHECK(attempt_count >= 0),
    next_retry_at INTEGER,
    last_error TEXT,
    FOREIGN KEY (operational_event_id) REFERENCES position_exit_events(event_id)
);

-- positions (P0-4 evidence fields renamed to immutable IDs)
CREATE TABLE positions (
    position_id TEXT PRIMARY KEY,
    signal_id TEXT NOT NULL,
    signal_version INTEGER NOT NULL,
    structure_type TEXT NOT NULL,
    selected_route TEXT,
    position_status TEXT NOT NULL DEFAULT 'PENDING' CHECK(position_status IN
        ('PENDING','OPEN','CLOSED','EXPIRED','ASSIGNED','CANCELLED')),
    net_debit_credit_cents INTEGER,
    max_profit_cents INTEGER,
    max_loss_cents INTEGER,
    currency TEXT NOT NULL DEFAULT 'USD',
    entry_source TEXT,
    exit_source TEXT,
    entry_package_observation_id TEXT,
    exit_package_observation_id TEXT,
    entry_option_observation_ids_json TEXT,
    exit_option_observation_ids_json TEXT,
    created_at INTEGER NOT NULL,
    entry_ts INTEGER,
    exit_ts INTEGER,
    paper_mode TEXT NOT NULL DEFAULT 'RESEARCH',
    reconciliation_required INTEGER NOT NULL DEFAULT 0,
    reconciliation_reason TEXT,
    reconciliation_flagged_at INTEGER,
    FOREIGN KEY (signal_id, signal_version)
        REFERENCES signal_versions(signal_id, version)
);

-- position_legs (hardened)
CREATE TABLE position_legs (
    position_id TEXT NOT NULL,
    leg_number INTEGER NOT NULL,
    contract_id TEXT NOT NULL,
    buy_sell TEXT NOT NULL CHECK(buy_sell IN ('BUY','SELL')),
    open_close TEXT NOT NULL CHECK(open_close IN ('OPEN','CLOSE')),
    ratio INTEGER NOT NULL DEFAULT 1 CHECK(ratio > 0),
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    multiplier INTEGER NOT NULL DEFAULT 100
        CHECK(multiplier > 0),
    entry_bid_cents INTEGER,
    entry_ask_cents INTEGER,
    entry_fill_cents INTEGER,
    exit_bid_cents INTEGER,
    exit_ask_cents INTEGER,
    exit_fill_cents INTEGER,
    delta REAL, gamma REAL, vega REAL, theta REAL,
    greeks_as_of INTEGER,
    greeks_source TEXT,
    PRIMARY KEY (position_id, leg_number),
    FOREIGN KEY (position_id) REFERENCES positions(position_id)
);

-- position_events
CREATE TABLE position_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    position_id TEXT NOT NULL,
    ts INTEGER NOT NULL,
    event_type TEXT NOT NULL CHECK(event_type IN
        ('SIGNAL','ENTRY_FILL','PARTIAL_FILL','EXIT_FILL',
         'ASSIGNMENT','EXPIRY','CANCEL','MANUAL_NOTE')),
    payload_json TEXT NOT NULL,
    FOREIGN KEY (position_id) REFERENCES positions(position_id)
);

-- position_fills (hardened; AH execution identity)
CREATE TABLE position_fills (
    fill_id TEXT PRIMARY KEY NOT NULL,
    position_id TEXT NOT NULL,
    leg_number INTEGER NOT NULL,
    ts INTEGER NOT NULL,
    side TEXT NOT NULL CHECK(side IN ('BUY','SELL')),
    position_effect TEXT NOT NULL CHECK(position_effect IN ('OPEN','CLOSE')),
    broker TEXT NOT NULL CHECK(length(trim(broker)) > 0),
    account_ref TEXT NOT NULL CHECK(length(trim(account_ref)) > 0),
    execution_id TEXT NOT NULL CHECK(length(trim(execution_id)) > 0),
    execution_leg_key TEXT NOT NULL CHECK(length(trim(execution_leg_key)) > 0),
    fill_origin TEXT NOT NULL CHECK(fill_origin IN ('BROKER','MANUAL','PAPER')),
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    fill_cents INTEGER NOT NULL CHECK(fill_cents >= 0),
    fee_cents INTEGER NOT NULL,
    venue TEXT,
    position_revision INTEGER NOT NULL CHECK(position_revision > 0),
    input_revision INTEGER NOT NULL CHECK(input_revision >= 0),
    FOREIGN KEY (position_id) REFERENCES positions(position_id),
    FOREIGN KEY (position_id, leg_number)
        REFERENCES position_legs(position_id, leg_number)
);
CREATE UNIQUE INDEX uq_fill_dedup
    ON position_fills(broker, account_ref, execution_id, execution_leg_key);

-- symbol_filter (P0-2 workflow_scope includes ZERO_DTE_CLUSTER)
CREATE TABLE symbol_filter (
    filter_id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern TEXT NOT NULL,
    match_type TEXT NOT NULL CHECK(match_type IN
        ('exact','glob','regex')),
    action TEXT NOT NULL CHECK(action IN
        ('BLOCK','ALLOW','WATCH_ONLY')),
    workflow_scope TEXT NOT NULL DEFAULT 'ALL' CHECK(workflow_scope IN
        ('FLOW_ALERT','ZERO_DTE_CLUSTER','MORNING','AD_HOC',
         'SPX_INTRADAY','ALL')),
    asset_type TEXT NOT NULL DEFAULT 'EQUITY' CHECK(asset_type IN
        ('EQUITY','ETF','INDEX','FUTURE','OTHER','ANY')),
    reason TEXT NOT NULL,
    category TEXT,
    expires_at INTEGER,
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    updated_by TEXT
);

-- symbol_filter_history
CREATE TABLE symbol_filter_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filter_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    old_json TEXT, new_json TEXT, reason TEXT,
    source TEXT NOT NULL, ts INTEGER NOT NULL,
    FOREIGN KEY (filter_id) REFERENCES symbol_filter(filter_id)
);

-- mode_transitions
CREATE TABLE mode_transitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts INTEGER NOT NULL, from_mode TEXT, to_mode TEXT NOT NULL,
    reason TEXT NOT NULL, approved_by TEXT
);

-- engine_health
CREATE TABLE engine_health (
    provider TEXT NOT NULL, engine TEXT NOT NULL,
    last_success_at INTEGER, last_failure_at INTEGER,
    consecutive_fails INTEGER DEFAULT 0,
    consecutive_success INTEGER DEFAULT 0,
    total_successes INTEGER DEFAULT 0,
    total_failures INTEGER DEFAULT 0,
    is_blocked INTEGER DEFAULT 0, blocked_until INTEGER,
    is_preferred INTEGER DEFAULT 0, preferred_since INTEGER,
    updated_at INTEGER NOT NULL,
    PRIMARY KEY (provider, engine)
);

-- provider_engine_profile
CREATE TABLE provider_engine_profile (
    provider TEXT PRIMARY KEY,
    preferred_engine TEXT NOT NULL, fallback_order TEXT NOT NULL,
    last_updated INTEGER NOT NULL, change_reason TEXT
);

-- engine_preference_history
CREATE TABLE engine_preference_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL, old_engine TEXT,
    new_engine TEXT NOT NULL, reason TEXT NOT NULL,
    ts INTEGER NOT NULL
);

-- human_rhythm_state
CREATE TABLE human_rhythm_state (
    state_id INTEGER PRIMARY KEY AUTOINCREMENT,
    entered_at INTEGER NOT NULL, left_at INTEGER,
    state TEXT NOT NULL, session_id TEXT,
    planned_duration_s INTEGER NOT NULL,
    actual_duration_s INTEGER, reason TEXT
);

-- coverage_windows
CREATE TABLE coverage_windows (
    window_id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,
    window_start INTEGER NOT NULL, window_end INTEGER,
    expected_session_end INTEGER, decision_cutoff INTEGER,
    status TEXT NOT NULL DEFAULT 'OPEN' CHECK(status IN
        ('OPEN','CLOSED','INTERRUPTED')),
    capture_channel TEXT NOT NULL,
    completeness TEXT CHECK(completeness IN
        ('COMPLETE','PARTIAL','MANUAL_ONLY','UNKNOWN')),
    provider_coverage_pct REAL,
    missed_interval_count INTEGER DEFAULT 0,
    session_id TEXT,
    notes TEXT
);
CREATE INDEX idx_coverage_provider_time
    ON coverage_windows(provider, window_start);

-- raw_provider_events
CREATE TABLE raw_provider_events (
    raw_id TEXT PRIMARY KEY,
    provider TEXT NOT NULL, provider_event_id TEXT,
    received_at INTEGER NOT NULL, source_ts INTEGER,
    payload_hash TEXT NOT NULL,
    spool_ref TEXT, inline_payload TEXT,
    parser_version TEXT NOT NULL, schema_version TEXT NOT NULL,
    access_channel TEXT NOT NULL, authorization_id TEXT,
    source_trace_id TEXT,
    ingested_at INTEGER NOT NULL,
    UNIQUE(provider, provider_event_id)
);
CREATE INDEX idx_raw_source_trace
    ON raw_provider_events(source_trace_id);

-- canonical_events
CREATE TABLE canonical_events (
    canonical_event_id TEXT PRIMARY KEY,
    contract_id TEXT NOT NULL, ticker TEXT NOT NULL,
    trade_ts INTEGER, quote_ts INTEGER,
    trade_price_cents INTEGER, quantity INTEGER,
    underlying_price_micros BIGINT,
    nbbo_bid_cents INTEGER,
    nbbo_ask_cents INTEGER,
    bid_size INTEGER,
    ask_size INTEGER,
    quote_source TEXT,
    exchange_execution_id TEXT,
    fingerprint_disambiguator TEXT,
    venue TEXT, sale_conditions TEXT,
    correction_status TEXT,
    completeness TEXT NOT NULL CHECK(completeness IN
        ('COMPLETE','PARTIAL','MANUAL_ONLY','UNKNOWN')),
    canonical_fingerprint TEXT NOT NULL,
    trace_id TEXT,
    capture_channel TEXT NOT NULL,
    created_at INTEGER NOT NULL
);
CREATE INDEX idx_canonical_trace
    ON canonical_events(trace_id);
CREATE INDEX idx_canonical_contract_ts
    ON canonical_events(contract_id, trade_ts);
CREATE INDEX idx_canonical_fingerprint
    ON canonical_events(canonical_fingerprint);
CREATE INDEX idx_canonical_execid
    ON canonical_events(exchange_execution_id);

-- canonical_event_sources
CREATE TABLE canonical_event_sources (
    canonical_event_id TEXT NOT NULL,
    raw_event_id TEXT NOT NULL,
    provider TEXT NOT NULL, provider_event_id TEXT,
    source_trace_id TEXT,
    canonical_trace_id TEXT,
    match_confidence REAL,
    received_at INTEGER NOT NULL,
    PRIMARY KEY (canonical_event_id, raw_event_id),
    FOREIGN KEY (canonical_event_id)
        REFERENCES canonical_events(canonical_event_id),
    FOREIGN KEY (raw_event_id)
        REFERENCES raw_provider_events(raw_id)
);
CREATE INDEX idx_event_sources_source_trace
    ON canonical_event_sources(source_trace_id);
CREATE INDEX idx_event_sources_canonical_trace
    ON canonical_event_sources(canonical_trace_id);

-- canonical_event_relationships
CREATE TABLE canonical_event_relationships (
    relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_canonical_event_id TEXT NOT NULL,
    to_canonical_event_id TEXT NOT NULL,
    relationship TEXT NOT NULL CHECK(relationship IN
        ('INDEPENDENT_REPEATED_FLOW','RELATED_CLUSTER',
         'SAME_THESIS_UPDATE','SUPERSEDES')),
    confidence REAL, created_at INTEGER NOT NULL,
    UNIQUE(from_canonical_event_id, to_canonical_event_id,
           relationship),
    FOREIGN KEY (from_canonical_event_id)
        REFERENCES canonical_events(canonical_event_id),
    FOREIGN KEY (to_canonical_event_id)
        REFERENCES canonical_events(canonical_event_id)
);

-- persistent_idempotency
CREATE TABLE persistent_idempotency (
    dedup_key TEXT PRIMARY KEY,
    created_at INTEGER NOT NULL, expires_at INTEGER NOT NULL
);
CREATE INDEX idx_idem_expiry
    ON persistent_idempotency(expires_at);

-- corporate_action_ingestion
CREATE TABLE corporate_action_ingestion (
    action_id TEXT PRIMARY KEY, ticker TEXT NOT NULL,
    action_type TEXT NOT NULL CHECK(action_type IN
        ('SPLIT','RENAME','MERGER','SPINOFF','ADJUSTED_CONTRACT')),
    effective_date TEXT NOT NULL, announced_at INTEGER,
    ratio DOUBLE, source TEXT NOT NULL,
    applied_to_chains INTEGER NOT NULL DEFAULT 0,
    applied_to_options_master INTEGER NOT NULL DEFAULT 0,
    applied_at INTEGER,
    status TEXT NOT NULL CHECK(status IN
        ('PENDING','APPLIED','FAILED')),
    error_detail TEXT, created_at INTEGER NOT NULL
);
CREATE INDEX idx_corp_action_ticker_status
    ON corporate_action_ingestion(ticker, status);

-- provider_query_pool
CREATE TABLE provider_query_pool (
    provider TEXT NOT NULL, market_date TEXT NOT NULL,
    pool TEXT NOT NULL CHECK(pool IN
        ('FLOW_ALERT','MORNING_AD_HOC','GLOBAL')),
    ceiling INTEGER NOT NULL,
    used INTEGER NOT NULL DEFAULT 0,
    borrowed INTEGER NOT NULL DEFAULT 0,
    borrow_source_pool TEXT,
    borrow_restored_at INTEGER,
    updated_at INTEGER NOT NULL,
    PRIMARY KEY (provider, market_date, pool)
);

-- provider_query_budget (P0-2 workflow_scope includes ZERO_DTE_CLUSTER)
CREATE TABLE provider_query_budget (
    provider TEXT NOT NULL, market_date TEXT NOT NULL,
    thesis_id TEXT NOT NULL, query_type TEXT NOT NULL,
    workflow_scope TEXT NOT NULL CHECK(workflow_scope IN
        ('FLOW_ALERT','ZERO_DTE_CLUSTER','MORNING','AD_HOC',
         'SPX_INTRADAY','GLOBAL')),
    calls_used INTEGER NOT NULL DEFAULT 0,
    last_call_at INTEGER,
    cache_hits INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY(provider, market_date, thesis_id, query_type,
                workflow_scope)
);

-- profile_cohort
CREATE TABLE profile_cohort (
    profile_id TEXT PRIMARY KEY,
    provider TEXT,
    browser_family TEXT NOT NULL, browser_version TEXT NOT NULL,
    impersonate_target TEXT NOT NULL,
    chrome_channel TEXT NOT NULL DEFAULT 'stable',
    os_version TEXT NOT NULL,
    hardware_concurrency INTEGER NOT NULL,
    device_memory REAL NOT NULL,
    gpu_vendor TEXT NOT NULL, gpu_renderer TEXT NOT NULL,
    font_set_id TEXT NOT NULL, locale TEXT NOT NULL,
    timezone TEXT NOT NULL,
    screen_width INTEGER, screen_height INTEGER,
    viewport_width INTEGER, viewport_height INTEGER,
    device_pixel_ratio REAL,
    webrtc_policy TEXT CHECK(webrtc_policy IN
        ('default','default_public_and_private_interfaces',
         'default_public_interface_only','disable_non_proxied_udp',
         'proxy_public_interface_only',
         'proxy_public_and_private_interfaces')),
    fp_seed TEXT,
    user_data_dir TEXT NOT NULL,
    deliberate_randomizations_json TEXT,
    expected_ja4_prefix TEXT,
    expected_ja4s_prefix TEXT,
    expected_ja4h_prefix TEXT,
    expected_h2_settings_hash TEXT,
    expected_header_order_hash TEXT,
    expected_alpn_json TEXT,
    probes_json TEXT,
    compatibility_matrix_json TEXT,
    reference_observed_ticket INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active'
        CHECK(status IN ('active','retired')),
    created_at INTEGER NOT NULL, retired_at INTEGER
);

-- profile_evolution
CREATE TABLE profile_evolution (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts INTEGER NOT NULL, prior_profile_id TEXT,
    new_profile_id TEXT NOT NULL,
    evolution_type TEXT NOT NULL CHECK(evolution_type IN
        ('browser_bump','os_bump','hardware_change','manual')),
    soak_started_at INTEGER, rollout_completed_at INTEGER,
    reason TEXT NOT NULL, operator TEXT,
    FOREIGN KEY (new_profile_id)
        REFERENCES profile_cohort(profile_id)
);

-- wire_pins (structure unchanged)
CREATE TABLE wire_pins (
    profile_id TEXT NOT NULL, platform TEXT NOT NULL,
    chrome_version TEXT NOT NULL,
    tls_profile TEXT NOT NULL CHECK(tls_profile IN
        ('tls13','tls12')),
    supported_versions_json TEXT, cipher_suites_json TEXT,
    extensions_json TEXT, extension_order_json TEXT,
    grease_pattern_json TEXT, alpn_json TEXT,
    sni_expected TEXT, key_share_json TEXT,
    post_quantum_present INTEGER, ech_state TEXT,
    signature_algorithms_json TEXT, supported_groups_json TEXT,
    psk_key_exchange_modes_json TEXT, alps_present INTEGER,
    compress_certificate_json TEXT, record_size_limit INTEGER,
    padding_class TEXT, ja4_prefix TEXT, ja4s_prefix TEXT,
    ja4h_prefix TEXT, h2_settings_json TEXT,
    h2_connection_window_update INTEGER,
    h2_stream_window_update INTEGER,
    h2_priority_present INTEGER,
    headers_pseudo_order_json TEXT,
    headers_continuation_count INTEGER,
    authority_present INTEGER,
    header_order_canonical_json TEXT,
    user_agent TEXT, sec_ch_ua TEXT, sec_ch_ua_mobile TEXT,
    sec_ch_ua_platform TEXT, sec_ch_ua_platform_version TEXT,
    sec_ch_ua_full_version TEXT, sec_ch_ua_arch TEXT,
    sec_ch_ua_bitness TEXT, sec_ch_ua_model TEXT,
    sec_ch_ua_wow64 TEXT, upgrade_insecure_requests TEXT,
    accept_default TEXT, accept_encoding TEXT,
    accept_language TEXT, sec_fetch_defaults_json TEXT,
    priority_header TEXT, referer_expected TEXT,
    conditional_headers_json TEXT,
    ocsp_stapling_present INTEGER, sct_present INTEGER,
    captured_from TEXT NOT NULL, captured_at INTEGER NOT NULL,
    PRIMARY KEY (profile_id, platform, chrome_version,
                 tls_profile),
    FOREIGN KEY (profile_id) REFERENCES profile_cohort(profile_id)
);

-- expected_fingerprints
CREATE TABLE expected_fingerprints (
    browser_family TEXT NOT NULL, browser_version TEXT NOT NULL,
    ja4_prefix TEXT NOT NULL, ja4s_prefix TEXT NOT NULL,
    ja4h_prefix TEXT NOT NULL, h2_settings_hash TEXT NOT NULL,
    header_order_hash TEXT NOT NULL, alpn_json TEXT NOT NULL,
    extensions_json TEXT NOT NULL,
    cipher_suites_json TEXT NOT NULL,
    supported_versions_json TEXT NOT NULL,
    ech_state TEXT,
    post_quantum_present INTEGER NOT NULL DEFAULT 0,
    captured_from TEXT NOT NULL, captured_at INTEGER NOT NULL,
    PRIMARY KEY (browser_family, browser_version)
);

-- client_hint_negotiation
CREATE TABLE client_hint_negotiation (
    origin TEXT NOT NULL, profile_id TEXT NOT NULL,
    accept_ch_list TEXT, critical_ch_list TEXT,
    negotiated_hint_set TEXT, last_seen INTEGER NOT NULL,
    PRIMARY KEY (origin, profile_id),
    FOREIGN KEY (profile_id) REFERENCES profile_cohort(profile_id)
);

-- trace_fingerprints
CREATE TABLE trace_fingerprints (
    session_id TEXT PRIMARY KEY,
    mouse_trace_hash TEXT, scroll_trace_hash TEXT,
    timing_trace_hash TEXT, dwell_trace_hash TEXT,
    created_at INTEGER NOT NULL, expires_at INTEGER NOT NULL
);

-- trace_features
CREATE TABLE trace_features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    modality TEXT NOT NULL CHECK(modality IN
        ('mouse','scroll','timing','dwell')),
    feature_vector_json TEXT NOT NULL,
    ts INTEGER NOT NULL
);

-- fingerprint_audit_log
CREATE TABLE fingerprint_audit_log (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts INTEGER NOT NULL, profile_id TEXT NOT NULL,
    checked_ja4 TEXT, expected_ja4_prefix TEXT,
    h2_settings_match INTEGER, header_order_match INTEGER,
    probes_passed INTEGER, probes_total INTEGER,
    reference_platform TEXT,
    result TEXT NOT NULL CHECK(result IN
        ('PASS','FAIL','DEGRADED')),
    detail_json TEXT,
    FOREIGN KEY (profile_id) REFERENCES profile_cohort(profile_id)
);

-- detection_events
CREATE TABLE detection_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts INTEGER NOT NULL, provider TEXT NOT NULL,
    session_id TEXT, signal TEXT NOT NULL,
    action TEXT NOT NULL CHECK(action IN
        ('HALT','HALT_MANUAL_REQUIRED','HALT_AUTH_REQUIRED',
         'HALT_CHALLENGED','ABORT_SESSION','COOLDOWN')),
    detail_json TEXT
);

-- notifications (P0-7 notification_domain + ack columns)
CREATE TABLE notifications (
    notification_id TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    urgency TEXT NOT NULL CHECK(urgency IN
        ('immediate','daily','informational')),
    title TEXT NOT NULL, body TEXT NOT NULL,
    provider TEXT, subject_key TEXT,
    state TEXT NOT NULL CHECK(state IN
        ('open','resolved','expired')),
    created_at INTEGER NOT NULL, resolved_at INTEGER,
    resolution_note TEXT, auto_resolve_condition TEXT,
    thesis_id TEXT, signal_id TEXT, signal_version INTEGER,
    snapshot_id TEXT,
    notification_domain TEXT NOT NULL
        CHECK(notification_domain IN
              ('SYSTEM','TACTICAL','RESEARCH')),
    requires_ack INTEGER NOT NULL
        CHECK(requires_ack IN (0,1)),
    acknowledged_at INTEGER,
    acknowledged_by TEXT,
    escalated_from_notification_id TEXT,
    tier TEXT CHECK(tier IS NULL OR tier IN
        ('critical','immediate','warning',
         'informational','daily'))
);
CREATE INDEX idx_notif_state
    ON notifications(state, urgency, created_at);
CREATE INDEX idx_notif_thesis ON notifications(thesis_id);
CREATE INDEX idx_notif_domain_ack
    ON notifications(notification_domain, requires_ack,
                     state, acknowledged_at);

-- notification_deliveries
CREATE TABLE notification_deliveries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    notification_id TEXT NOT NULL,
    channel TEXT NOT NULL CHECK(channel IN
        ('discord','resend','mailgun')),
    attempt_at INTEGER NOT NULL,
    status TEXT NOT NULL CHECK(status IN
        ('pending','delivered','failed','exhausted')),
    error_detail TEXT, provider_response_id TEXT,
    FOREIGN KEY (notification_id)
        REFERENCES notifications(notification_id)
);

-- scheduler_heartbeats
CREATE TABLE scheduler_heartbeats (
    heartbeat_id INTEGER PRIMARY KEY AUTOINCREMENT,
    written_at INTEGER NOT NULL,
    component TEXT NOT NULL CHECK(component IN
        ('quantd','capture','rhythm','backup','t1_oi','dq','misc')),
    instance_id TEXT NOT NULL, boot_id TEXT NOT NULL,
    sequence INTEGER NOT NULL, health_state TEXT NOT NULL,
    session_id TEXT, notes TEXT
);

-- scheduled_tasks
CREATE TABLE scheduled_tasks (
    task_id TEXT PRIMARY KEY, task_type TEXT NOT NULL,
    run_at INTEGER NOT NULL,
    state TEXT NOT NULL CHECK(state IN
        ('PENDING','RUNNING','DONE','FAILED','CANCELLED')),
    attempts INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 6,
    priority INTEGER NOT NULL DEFAULT 100,
    dedup_key TEXT,
    last_error TEXT, payload_json TEXT,
    locked_at INTEGER, lock_owner TEXT,
    abandoned_at INTEGER,
    next_retry_at INTEGER,
    created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL
);
CREATE INDEX idx_tasks_state_run ON scheduled_tasks(state, run_at);
CREATE UNIQUE INDEX uq_scheduled_task_dedup
    ON scheduled_tasks(dedup_key)
    WHERE state IN ('PENDING','RUNNING')
      AND dedup_key IS NOT NULL;
CREATE INDEX idx_tasks_lock ON scheduled_tasks(state, locked_at);

-- daily_alert_cycle
CREATE TABLE daily_alert_cycle (
    cycle_date TEXT PRIMARY KEY,
    newsletter_generated_at INTEGER,
    setup_started_at INTEGER, setup_completed_at INTEGER,
    cleanup_started_at INTEGER, cleanup_completed_at INTEGER,
    alerts_configured_count INTEGER DEFAULT 0,
    alerts_fired_count INTEGER DEFAULT 0,
    alerts_removed_count INTEGER DEFAULT 0,
    status TEXT NOT NULL CHECK(status IN
        ('PENDING','COMPLETE','PARTIAL','FAILED'))
);

-- daily_alert_items
CREATE TABLE daily_alert_items (
    cycle_date TEXT NOT NULL, item_index INTEGER NOT NULL,
    level_id TEXT NOT NULL, map_id TEXT NOT NULL,
    symbol TEXT NOT NULL DEFAULT 'SPX',
    level_price_mills BIGINT NOT NULL,
    expiration_scope TEXT,
    direction TEXT NOT NULL CHECK(direction IN ('above','below')),
    valid_until INTEGER, provider_alert_id TEXT, label TEXT,
    configured_at INTEGER, fired_at INTEGER,
    removed_at INTEGER,
    status TEXT NOT NULL CHECK(status IN
        ('PENDING','CONFIGURED','FIRED','REMOVED','FAILED','STALE')),
    error_detail TEXT,
    PRIMARY KEY (cycle_date, item_index),
    UNIQUE (cycle_date, level_id),
    FOREIGN KEY (cycle_date) REFERENCES daily_alert_cycle(cycle_date)
);

-- symbol_theses
CREATE TABLE symbol_theses (
    thesis_id TEXT PRIMARY KEY,
    ticker TEXT NOT NULL,
    expected_direction TEXT NOT NULL CHECK(expected_direction IN
        ('bullish','bearish','volatility','income_or_hedge',
         'indeterminate')),
    dte_lane TEXT NOT NULL CHECK(dte_lane IN
        ('0DTE','1DTE','TACTICAL_2DTE','SHORT_TACTICAL',
         'SWING','LONGER_HORIZON')),
    structure_signature TEXT NOT NULL,
    target_horizon TEXT NOT NULL,
    state TEXT NOT NULL CHECK(state IN
        ('NO_ACTIVE_FLOW_THESIS','CANDIDATE','WATCH',
         'VALIDATED_PENDING_ENTRY','ACTIONABLE_NOW',
         'PORTFOLIO_BLOCKED','ENTRY_UNAVAILABLE','STAND_DOWN',
         'INVALIDATED','RETRACTED','EXPIRED','COMPLETED')),
    strength_tier TEXT NOT NULL DEFAULT 'NORMAL' CHECK(strength_tier IN
        ('NORMAL','STRONG','SUPER_BULLISH','SUPER_BEARISH')),
    first_seen INTEGER NOT NULL, last_seen INTEGER NOT NULL,
    independent_event_count INTEGER NOT NULL DEFAULT 0,
    corroborating_source_count INTEGER NOT NULL DEFAULT 0,
    supporting_event_count INTEGER NOT NULL DEFAULT 0,
    cumulative_premium_mills BIGINT NOT NULL DEFAULT 0,
    opposite_flow_premium_mills BIGINT NOT NULL DEFAULT 0,
    paired_opposite_thesis_id TEXT,
    contract_count INTEGER, expiration_concentration REAL,
    structure_state TEXT,
    evidence_tier INTEGER CHECK(evidence_tier BETWEEN 1 AND 4),
    best_data_quality TEXT,
    flow_label TEXT,
    latest_snapshot_id TEXT, latest_signal_id TEXT,
    latest_signal_version INTEGER,
    reconciliation_required INTEGER NOT NULL DEFAULT 0,
    reconciliation_reason TEXT,
    reconciliation_flagged_at INTEGER,
    updated_at INTEGER NOT NULL
);
CREATE UNIQUE INDEX uq_active_thesis_key
    ON symbol_theses(ticker, expected_direction, dte_lane,
                     structure_signature, target_horizon)
    WHERE state NOT IN
        ('EXPIRED','COMPLETED','RETRACTED','INVALIDATED');

-- thesis_versions
CREATE TABLE thesis_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    thesis_id TEXT NOT NULL, version INTEGER NOT NULL,
    created_at INTEGER NOT NULL, previous_version INTEGER,
    state TEXT NOT NULL, strength_tier TEXT,
    snapshot_id TEXT, changed_fields_json TEXT, reason TEXT,
    UNIQUE(thesis_id, version),
    FOREIGN KEY (thesis_id) REFERENCES symbol_theses(thesis_id),
    FOREIGN KEY (thesis_id, previous_version)
        REFERENCES thesis_versions(thesis_id, version)
);

-- thesis_event_membership
CREATE TABLE thesis_event_membership (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    thesis_id TEXT NOT NULL,
    canonical_event_id TEXT NOT NULL,
    thesis_version INTEGER NOT NULL,
    membership_role TEXT NOT NULL CHECK(membership_role IN
        ('INDEPENDENT','CORROBORATION','SUPPORTING','OPPOSITE',
         'PACKAGE_LEG')),
    added_at INTEGER NOT NULL,
    removed_at INTEGER,
    removal_reason TEXT,
    FOREIGN KEY (thesis_id) REFERENCES symbol_theses(thesis_id),
    FOREIGN KEY (canonical_event_id)
        REFERENCES canonical_events(canonical_event_id)
);

-- zero_dte_cluster_current
-- (P0-3 cluster_state lifecycle-only; P0-5 levels in _mills)
CREATE TABLE zero_dte_cluster_current (
    cluster_id TEXT PRIMARY KEY,
    episode_id TEXT NOT NULL UNIQUE,
    session_date TEXT NOT NULL,
    thesis_id TEXT,
    ticker TEXT NOT NULL,
    expiration TEXT NOT NULL,
    direction TEXT NOT NULL CHECK(direction IN
        ('bullish','bearish','mixed')),
    cluster_grade TEXT NOT NULL CHECK(cluster_grade IN
        ('BASIC','MEDIUM_CONFLUENCE','HIGH_CONFLUENCE')),
    cluster_state TEXT NOT NULL CHECK(cluster_state IN
        ('ACTIVE','MIXED','BULLISH_REVERSAL',
         'BEARISH_REVERSAL','RETRACTED','EXPIRED')),
    episode_state TEXT NOT NULL CHECK(episode_state IN
        ('FORMING','ACTIVE','UPGRADED','REVERSED','RETRACTED',
         'EXPIRED')),
    first_event_ts INTEGER NOT NULL,
    last_event_ts INTEGER NOT NULL,
    independent_event_count INTEGER NOT NULL DEFAULT 0,
    distinct_strike_count INTEGER NOT NULL DEFAULT 0,
    gross_premium_mills BIGINT,
    net_delta_dollars REAL,
    directional_dominance REAL,
    opposing_share REAL,
    flow_strength REAL,
    dealer_alignment REAL,
    price_confirmation REAL,
    confluence_score REAL,
    dealer_context_status TEXT CHECK(dealer_context_status IN
        ('FRESH','STALE','UNAVAILABLE')),
    dealer_map_age_s INTEGER,
    gamma_align REAL,
    vanna_align REAL,
    premium_percentile REAL,
    delta_percentile REAL,
    baseline_id TEXT,
    flow_components_json TEXT,
    activation_level_mills BIGINT,
    activation_kind TEXT CHECK(activation_kind IN
        ('GAMMA_FLIP','BARRIER','ACCELERATOR','SUPPORT','RESISTANCE',
         'VANNA','CONFLUENCE') OR activation_kind IS NULL),
    target_level_mills BIGINT,
    target_kind TEXT,
    support_or_resistance_mills BIGINT,
    support_or_resistance_kind TEXT,
    invalidation_price_mills BIGINT,
    dealer_map_id TEXT,
    market_map_id TEXT,
    data_quality_grade TEXT,
    coverage TEXT,
    medium_notification_id TEXT,
    high_notification_id TEXT,
    ruleset_version TEXT NOT NULL,
    input_manifest_hash TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    expires_at INTEGER,
    updated_at INTEGER NOT NULL
);
CREATE INDEX idx_0dtc_ticker
    ON zero_dte_cluster_current(ticker, expiration, session_date);
CREATE INDEX idx_0dtc_state ON zero_dte_cluster_current(cluster_state);
CREATE INDEX idx_0dtc_grade ON zero_dte_cluster_current(cluster_grade);

-- zero_dte_cluster_members (P0-6 FK parity)
CREATE TABLE zero_dte_cluster_members (
    cluster_id TEXT NOT NULL,
    canonical_event_id TEXT NOT NULL,
    economic_package_id TEXT,
    membership_role TEXT NOT NULL CHECK(membership_role IN
        ('LEAD','CONFIRMING','PACKAGE_LEG','OPPOSITE')),
    added_at INTEGER NOT NULL,
    removed_at INTEGER,
    removal_reason TEXT,
    PRIMARY KEY (cluster_id, canonical_event_id),
    FOREIGN KEY (cluster_id)
        REFERENCES zero_dte_cluster_current(cluster_id),
    FOREIGN KEY (canonical_event_id)
        REFERENCES canonical_events(canonical_event_id)
);
CREATE INDEX idx_0dtcm_pkg
    ON zero_dte_cluster_members(economic_package_id);

-- zero_dte_cluster_member_history (new)
-- Append-only. Survives retirement of the current row.
CREATE TABLE zero_dte_cluster_member_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    cluster_id TEXT NOT NULL,
    episode_id TEXT NOT NULL,
    canonical_event_id TEXT NOT NULL,
    economic_package_id TEXT,
    membership_role TEXT NOT NULL,
    added_at INTEGER NOT NULL,
    removed_at INTEGER,
    removal_reason TEXT,
    snapshot_payload_json TEXT
);
CREATE INDEX idx_0dtcmh_cluster
    ON zero_dte_cluster_member_history(cluster_id, added_at);
CREATE INDEX idx_0dtcmh_episode
    ON zero_dte_cluster_member_history(episode_id, canonical_event_id);

-- report_runs
CREATE TABLE report_runs (
    report_id TEXT PRIMARY KEY,
    report_type TEXT NOT NULL CHECK(report_type IN
        ('flow_alert','morning_premarket','morning_open_addendum',
         'ad_hoc')),
    requested_at INTEGER NOT NULL, completed_at INTEGER,
    market_date TEXT NOT NULL, ticker TEXT,
    phase TEXT, intent TEXT, refresh_mode TEXT,
    status TEXT NOT NULL CHECK(status IN
        ('COMPLETE','PARTIAL','FAILED','NO_CHANGES','SKIPPED')),
    provider_calls_json TEXT NOT NULL,
    source_status_json TEXT NOT NULL,
    rendered_payload_json TEXT,
    ruleset_version TEXT NOT NULL, feature_version TEXT NOT NULL
);
CREATE INDEX idx_report_date ON report_runs(market_date, report_type);
CREATE INDEX idx_report_ticker ON report_runs(ticker, requested_at);

-- report_snapshot_refs
CREATE TABLE report_snapshot_refs (
    report_id TEXT NOT NULL,
    ref_type TEXT NOT NULL CHECK(ref_type IN
        ('analysis','market_map','dealer_map','dealer_snapshot',
         'technical_snapshot','volatility_snapshot',
         'portfolio_snapshot','quote_snapshot',
         'option_quote_observation','package_quote_observation',
         'price_observation','zero_dte_cluster')),
    ref_id TEXT NOT NULL,
    PRIMARY KEY (report_id, ref_type, ref_id),
    FOREIGN KEY (report_id) REFERENCES report_runs(report_id)
);

-- portfolio_state_current (singleton)
CREATE TABLE portfolio_state_current (
    singleton_id INTEGER PRIMARY KEY CHECK(singleton_id = 1),
    snapshot_id TEXT NOT NULL UNIQUE,
    as_of INTEGER NOT NULL,
    equity_cents INTEGER NOT NULL,
    cash_cents INTEGER NOT NULL,
    delta_dollars REAL, gamma_dollars REAL,
    vega_dollars REAL, theta_dollars REAL,
    assignment_exposure_cents INTEGER,
    sector_exposure_json TEXT,
    correlation_clusters_json TEXT,
    route_capacity_json TEXT,
    risk_engine_payload_json TEXT,
    payload_hash TEXT NOT NULL,
    updated_at INTEGER NOT NULL
);

-- dealer_context_cache_current
CREATE TABLE dealer_context_cache_current (
    provider TEXT NOT NULL, ticker TEXT NOT NULL,
    greek_metric TEXT NOT NULL, expiration_scope TEXT NOT NULL,
    model_version TEXT NOT NULL,
    dealer_perspective TEXT NOT NULL, data_scope TEXT NOT NULL,
    dealer_map_id TEXT, valid_until INTEGER,
    updated_at INTEGER NOT NULL,
    PRIMARY KEY (provider, ticker, greek_metric,
                 expiration_scope, model_version,
                 dealer_perspective, data_scope)
);

-- dealer_map_current
CREATE TABLE dealer_map_current (
    ticker TEXT NOT NULL, session_date TEXT NOT NULL,
    dealer_map_id TEXT NOT NULL, updated_at INTEGER NOT NULL,
    PRIMARY KEY (ticker, session_date)
);

-- market_map_current
CREATE TABLE market_map_current (
    ticker TEXT NOT NULL, session_date TEXT NOT NULL,
    map_id TEXT NOT NULL, updated_at INTEGER NOT NULL,
    PRIMARY KEY (ticker, session_date)
);

-- active_model_manifest
-- model_role disambiguates CHAMPION (drives decisions) from
-- CHALLENGER and SHADOW (research-only). Exactly one
-- CHAMPION per (model_kind, scope_key, ruleset_version) at
-- any time; enforced by the partial unique index below.
CREATE TABLE active_model_manifest (
    model_kind TEXT NOT NULL CHECK(model_kind IN
        ('calibrator','scoring_ruleset','exit_handler')),
    scope_key TEXT NOT NULL
        CHECK(length(scope_key) BETWEEN 1 AND 200),
    ruleset_version TEXT NOT NULL,
    model_id TEXT NOT NULL,
    model_role TEXT NOT NULL DEFAULT 'CHAMPION'
        CHECK(model_role IN ('CHAMPION','CHALLENGER','SHADOW')),
    active_from INTEGER NOT NULL,
    active_to INTEGER,
    payload_hash TEXT NOT NULL,
    PRIMARY KEY (model_kind, scope_key, ruleset_version,
                 model_id, active_from)
);
CREATE UNIQUE INDEX uq_active_champion_manifest
    ON active_model_manifest(model_kind, scope_key, ruleset_version)
    WHERE active_to IS NULL AND model_role = 'CHAMPION';
CREATE INDEX idx_manifest_role
    ON active_model_manifest(model_role, active_to);

-- spx_crossing_state_current
CREATE TABLE spx_crossing_state_current (
    level_id TEXT PRIMARY KEY,
    map_id TEXT, session_date TEXT NOT NULL,
    level_price_mills BIGINT NOT NULL,
    level_source TEXT NOT NULL, expiration_scope TEXT,
    direction TEXT,
    state TEXT NOT NULL CHECK(state IN
        ('FAR','APPROACHING','TESTING','CONFIRMED_BREAKOUT',
         'CONFIRMED_REVERSAL','FALSE_CROSS','COOLDOWN','REARMED',
         'INVALIDATED')),
    confirmation_window_s INTEGER,
    confirmation_distance_mills BIGINT,
    cooldown_until INTEGER, rearmed_at INTEGER,
    invalidated_by_map_id TEXT,
    entered_at INTEGER NOT NULL, last_transition_at INTEGER NOT NULL,
    spot_at_entry_micros BIGINT, close_price_micros BIGINT,
    evidence_json TEXT, updated_at INTEGER NOT NULL,
    CHECK(state != 'COOLDOWN'    OR cooldown_until        IS NOT NULL),
    CHECK(state != 'REARMED'     OR rearmed_at            IS NOT NULL),
    CHECK(state != 'INVALIDATED' OR invalidated_by_map_id IS NOT NULL)
);

-- operator_control_audit
CREATE TABLE operator_control_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts INTEGER NOT NULL, actor TEXT NOT NULL,
    channel TEXT NOT NULL CHECK(channel IN
        ('QUANTCTL','SIGNAL','SYSTEMD','MUSE_ADMIN')),
    action TEXT NOT NULL, target_ref TEXT,
    old_value_json TEXT, new_value_json TEXT, reason TEXT NOT NULL
);
CREATE INDEX idx_op_audit_ts ON operator_control_audit(ts);

-- ingest_log
CREATE TABLE ingest_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts INTEGER NOT NULL, job TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN
        ('OK','PARTIAL','FAILED','SKIPPED')),
    rows_moved INTEGER, rows_inserted INTEGER,
    rows_skipped INTEGER, checksum TEXT, detail_json TEXT,
    error_message TEXT
);
CREATE INDEX idx_ingest_ts ON ingest_log(ts);

-- backfill_log
CREATE TABLE backfill_log (
    backfill_id TEXT PRIMARY KEY,
    source TEXT NOT NULL, ticker TEXT,
    date_start TEXT, date_end TEXT,
    rows_loaded INTEGER,
    started_at INTEGER, completed_at INTEGER,
    status TEXT NOT NULL CHECK(status IN
        ('PENDING','RUNNING','DONE','FAILED')),
    error_message TEXT
);
CREATE INDEX idx_backfill_source
    ON backfill_log(source, started_at);

-- behavioral_reference
CREATE TABLE behavioral_reference (
    reference_id TEXT PRIMARY KEY,
    reference_type TEXT NOT NULL CHECK(reference_type IN
        ('login_timings','session_lengths','dwell_distributions',
         'weekend_pattern','holiday_pattern','operator_routine')),
    reference_json TEXT NOT NULL,
    observed_at INTEGER NOT NULL,
    source_note TEXT NOT NULL, updated_at INTEGER NOT NULL
);

-- Observability tables (observability_requests,
-- observability_daily_summary) and column additions
-- (notifications.tier; trace_id columns on
-- canonical_events, signal_ledger, analysis_snapshots;
-- session_id columns on provider_sessions,
-- coverage_windows, detection_events) are canonically
-- defined in SPEC v2.0.5.1 Vol 5 §O.11. Vol 5 owns those
-- DDL statements; the migration entries in ARCH Vol 2
-- §C.3 register them in the shared migration sequence.

--------------------------------------------------------------------------------

19.3 Analytical Entities (DuckDB)

DuckDB pragmas at open:
  memory_limit='1.2GB'; threads=2;
  temp_directory='/data/duckdb_tmp';

Timestamp rule: all DuckDB epoch-ms columns are BIGINT.
All SQLite epoch-ms columns are INTEGER. No native TIMESTAMP
columns are permitted in DuckDB. Enforced by schema test
that scans for TIMESTAMP and rejects.

-- schema_version_duckdb
CREATE TABLE schema_version_duckdb (
    migration_id TEXT PRIMARY KEY, checksum TEXT NOT NULL,
    applied_at BIGINT NOT NULL, app_version TEXT NOT NULL,
    result TEXT NOT NULL CHECK(result IN ('OK','FAILED'))
);

-- options_master
CREATE TABLE options_master (
    contract_id TEXT PRIMARY KEY, root TEXT NOT NULL,
    expiration DATE NOT NULL, strike_mills BIGINT NOT NULL,
    option_type TEXT NOT NULL,
    multiplier INTEGER NOT NULL DEFAULT 100,
    is_adjusted INTEGER NOT NULL DEFAULT 0,
    exercise_style TEXT, settlement_type TEXT,
    corporate_action_ver INTEGER NOT NULL DEFAULT 0,
    created_at BIGINT NOT NULL
);
CREATE INDEX idx_options_master_root_exp
    ON options_master(root, expiration);

-- quote_snapshot_batches
CREATE TABLE quote_snapshot_batches (
    quote_snapshot_id TEXT PRIMARY KEY,
    provider TEXT NOT NULL, ticker TEXT NOT NULL,
    as_of BIGINT NOT NULL, source_ts BIGINT,
    received_at BIGINT NOT NULL, payload_hash TEXT NOT NULL,
    created_at BIGINT NOT NULL
);

-- option_quote_observations
CREATE TABLE option_quote_observations (
    observation_id TEXT PRIMARY KEY,
    quote_snapshot_id TEXT NOT NULL,
    contract_id TEXT NOT NULL,
    bid_cents INTEGER, ask_cents INTEGER, last_cents INTEGER,
    bid_size INTEGER, ask_size INTEGER,
    provider_ts BIGINT, received_at BIGINT NOT NULL,
    staleness_ms INTEGER, quality_flag TEXT,
    FOREIGN KEY (quote_snapshot_id)
        REFERENCES quote_snapshot_batches(quote_snapshot_id)
);

-- package_quote_observations
CREATE TABLE package_quote_observations (
    observation_id TEXT PRIMARY KEY,
    quote_snapshot_id TEXT NOT NULL,
    route TEXT NOT NULL, legs_hash TEXT NOT NULL,
    net_bid_cents INTEGER, net_ask_cents INTEGER,
    net_mid_cents INTEGER,
    synchronized INTEGER NOT NULL, executable INTEGER NOT NULL,
    observed_at BIGINT NOT NULL,
    FOREIGN KEY (quote_snapshot_id)
        REFERENCES quote_snapshot_batches(quote_snapshot_id)
);

-- chain_snapshots (B4: observed_at, source_ts BIGINT)
CREATE TABLE chain_snapshots (
    snapshot_batch_id TEXT NOT NULL,
    observed_at BIGINT NOT NULL, provider TEXT NOT NULL,
    contract_id TEXT NOT NULL, ticker TEXT NOT NULL,
    expiration DATE NOT NULL, strike_mills BIGINT NOT NULL,
    option_type TEXT NOT NULL,
    bid_cents BIGINT, ask_cents BIGINT, last_cents BIGINT,
    volume BIGINT, open_interest BIGINT,
    implied_vol DOUBLE, delta DOUBLE, gamma DOUBLE,
    vega DOUBLE, theta DOUBLE, underlying_price DOUBLE,
    price_observation_id TEXT, quote_age_ms INTEGER,
    quality_flags TEXT, source_ts BIGINT,
    created_at BIGINT NOT NULL, ingested_at BIGINT NOT NULL,
    PRIMARY KEY (observed_at, provider, contract_id)
);

-- greeks_snapshots (B4: observed_at BIGINT)
CREATE TABLE greeks_snapshots (
    snapshot_id TEXT NOT NULL,
    observed_at BIGINT NOT NULL, provider TEXT NOT NULL,
    ticker TEXT NOT NULL, spot_micros BIGINT,
    net_gex DOUBLE, net_vanna DOUBLE, net_charm DOUBLE,
    spot_vol_beta DOUBLE, iv_rank DOUBLE, vrp_ratio DOUBLE,
    term_structure TEXT, skew DOUBLE,
    sigma_fair_30d DOUBLE, rv_forecast_30d DOUBLE,
    vrp_own DOUBLE, vrp_pct_2y DOUBLE, vrp_pct_sector DOUBLE,
    vix_close DOUBLE, vix_pct_5y DOUBLE, vix_pct_all DOUBLE,
    funding_rate DOUBLE,
    model_version TEXT, sign_convention TEXT,
    quality_flags TEXT,
    created_at BIGINT NOT NULL, ingested_at BIGINT NOT NULL,
    PRIMARY KEY (observed_at, provider, ticker)
);

-- signal_ledger
CREATE TABLE signal_ledger (
    ledger_id BIGINT,
    signal_id TEXT NOT NULL, version INTEGER NOT NULL,
    ts BIGINT NOT NULL, ticker TEXT NOT NULL,
    primary_contract_symbol TEXT,
    opt_type TEXT, strike_mills BIGINT, expiration DATE,
    position_id TEXT, thesis_id TEXT,
    analysis_snapshot_id TEXT NOT NULL,
    source_event_ts BIGINT, trade_event_ts BIGINT, quote_ts BIGINT,
    received_ts BIGINT, alert_generated_ts BIGINT,
    latency_ms INTEGER NOT NULL,
    canonical_event_fingerprint TEXT,
    fingerprint_disambiguator TEXT,
    cross_source_relation TEXT,
    quote_width_pct REAL NOT NULL, quote_age_ms INTEGER,
    correction_status TEXT,
    data_quality_grade TEXT NOT NULL,
    quality_flags_json TEXT,
    source_completeness TEXT NOT NULL,
    raw_score REAL NOT NULL, adjusted_score REAL NOT NULL,
    calibrated_p REAL, calibrated_p_lower REAL,
    calib_model_id TEXT,
    ruleset_version TEXT NOT NULL, feature_version TEXT NOT NULL,
    route TEXT NOT NULL,
    dim_scores_json TEXT NOT NULL, gate_fails_json TEXT NOT NULL,
    classification_conf_json TEXT NOT NULL,
    data_quality_json TEXT NOT NULL,
    eligibility_json TEXT NOT NULL,
    signal_confidence REAL NOT NULL,
    intent_uncertain INTEGER NOT NULL DEFAULT 0,
    expected_return_net_costs REAL, expected_return_lower REAL,
    expected_shortfall REAL,
    structure TEXT NOT NULL, structure_confidence REAL,
    structure_evidence_tier TEXT,
    paired_leg_count INTEGER, paired_notional_ratio REAL,
    paired_gamma_ratio REAL, paired_vanna_consistency REAL,
    unpaired_residual_exposure REAL,
    attribution_bucket TEXT NOT NULL DEFAULT 'clean',
    paper_mode TEXT NOT NULL DEFAULT 'RESEARCH',
    trace_id TEXT,
    PRIMARY KEY (signal_id, version),
    UNIQUE (ledger_id)
);
CREATE INDEX idx_ledger_trace
    ON signal_ledger(trace_id);

-- signal_outcomes (hardened; materialized scope id)
CREATE TABLE signal_outcomes (
    signal_id TEXT NOT NULL,
    signal_version INTEGER NOT NULL,
    position_id TEXT,
    outcome_scope_id TEXT NOT NULL,
    horizon TEXT NOT NULL,
    observed_at BIGINT NOT NULL,
    package_mark_cents BIGINT NOT NULL,
    spot_micros BIGINT, iv DOUBLE,
    ret_pct REAL, r_multiple REAL, exit_reason TEXT,
    entry_fill_cents BIGINT, exit_fill_cents BIGINT,
    modeled_slippage_cents BIGINT,
    entry_decision_ts BIGINT,
    analysis_snapshot_id TEXT,
    ruleset_version TEXT NOT NULL,
    fill_model_version TEXT NOT NULL,
    outcome_status TEXT, correction_version INTEGER,
    PRIMARY KEY (signal_id, signal_version, horizon, outcome_scope_id)
);

-- position_leg_outcomes
CREATE TABLE position_leg_outcomes (
    position_id TEXT NOT NULL, leg_number INTEGER NOT NULL,
    horizon TEXT NOT NULL, observed_at BIGINT NOT NULL,
    mark_cents BIGINT, exit_fill_cents BIGINT, ret_pct REAL,
    PRIMARY KEY (position_id, leg_number, horizon)
);

-- shadow_samples (hardened; feature_hash)
CREATE TABLE shadow_samples (
    sample_id BIGINT PRIMARY KEY, ts BIGINT NOT NULL,
    canonical_event_id TEXT NOT NULL, contract_id TEXT NOT NULL,
    ticker TEXT NOT NULL, provider_set TEXT NOT NULL,
    pre_screen_score REAL, rejection_stage TEXT NOT NULL,
    gate_fails_json TEXT NOT NULL,
    feature_hash TEXT NOT NULL,
    data_quality_grade TEXT NOT NULL,
    source_completeness TEXT NOT NULL,
    sampling_probability REAL NOT NULL,
    sampling_stratum TEXT NOT NULL,
    ruleset_version TEXT NOT NULL, feature_version TEXT NOT NULL,
    future_underlying_markout_1h REAL,
    future_underlying_markout_1d REAL,
    future_option_markout_1h REAL,
    future_option_markout_1d REAL,
    outcome_observed_at BIGINT, created_at BIGINT NOT NULL
);

-- dealer_snapshot_batches (B4: provider_as_of BIGINT)
CREATE TABLE dealer_snapshot_batches (
    dealer_snapshot_id TEXT PRIMARY KEY,
    provider TEXT NOT NULL, ticker TEXT NOT NULL,
    expiration_scope TEXT NOT NULL,
    provider_as_of BIGINT NOT NULL,
    model_version TEXT NOT NULL, sign_convention TEXT NOT NULL,
    payload_hash TEXT NOT NULL, created_at BIGINT NOT NULL
);

-- dealer_exposure_snapshot (B4: provider_as_of BIGINT)
CREATE TABLE dealer_exposure_snapshot (
    dealer_snapshot_id TEXT NOT NULL, provider TEXT NOT NULL,
    ticker TEXT NOT NULL, expiration DATE NOT NULL,
    option_type TEXT NOT NULL, strike_mills BIGINT NOT NULL,
    provider_as_of BIGINT NOT NULL,
    received_at BIGINT NOT NULL, spot_micros BIGINT,
    dealer_gamma_notional DOUBLE,
    dealer_vanna_notional DOUBLE,
    dealer_charm_notional DOUBLE,
    dealer_delta_decay_notional DOUBLE,
    dealer_vega_notional DOUBLE,
    dealer_delta_notional DOUBLE,
    gamma_units TEXT, vanna_units TEXT, charm_units TEXT,
    expiration_scope TEXT, spot_reference TEXT, perspective TEXT,
    sign_convention TEXT, units TEXT,
    source_lineage TEXT, analytics_vendor_lineage TEXT,
    classification_method TEXT, model_version TEXT,
    coverage_pct DOUBLE, raw_vs_fitted TEXT, payload_hash TEXT,
    PRIMARY KEY (provider, dealer_snapshot_id, expiration,
                 option_type, strike_mills)
);

-- volatility_snapshots
CREATE TABLE volatility_snapshots (
    volatility_snapshot_id TEXT PRIMARY KEY,
    ticker TEXT NOT NULL, as_of BIGINT NOT NULL,
    provider TEXT NOT NULL, model TEXT NOT NULL,
    iv_rank DOUBLE, vrp_vol DOUBLE,
    term_structure TEXT, skew DOUBLE,
    sigma_fair_30d DOUBLE, rv_forecast_30d DOUBLE,
    quality_flags TEXT, payload_hash TEXT NOT NULL,
    created_at BIGINT NOT NULL
);

-- portfolio_snapshots
CREATE TABLE portfolio_snapshots (
    portfolio_snapshot_id TEXT PRIMARY KEY,
    as_of BIGINT NOT NULL,
    equity_cents BIGINT NOT NULL, cash_cents BIGINT NOT NULL,
    delta_dollars DOUBLE, gamma_dollars DOUBLE,
    vega_dollars DOUBLE, theta_dollars DOUBLE,
    assignment_exposure_cents BIGINT,
    sector_exposure_json TEXT,
    correlation_clusters_json TEXT,
    route_capacity_json TEXT,
    open_positions_json TEXT NOT NULL,
    risk_engine_payload_json TEXT NOT NULL,
    payload_hash TEXT NOT NULL, created_at BIGINT NOT NULL
);

-- technical_level_snapshots
CREATE TABLE technical_level_snapshots (
    technical_snapshot_id TEXT PRIMARY KEY,
    ticker TEXT NOT NULL, as_of BIGINT NOT NULL,
    source_bar_set_id TEXT NOT NULL,
    session_vwap_micros BIGINT,
    session_twap_micros BIGINT,
    avwap_levels_json TEXT,
    ema_8_micros BIGINT, ema_21_micros BIGINT,
    sma_20_micros BIGINT, sma_50_micros BIGINT,
    sma_200_micros BIGINT,
    atr_micros BIGINT, expected_move_micros BIGINT,
    prior_day_high_micros BIGINT, prior_day_low_micros BIGINT,
    overnight_high_micros BIGINT, overnight_low_micros BIGINT,
    traditional_support_json TEXT,
    traditional_resistance_json TEXT,
    confluence_zones_json TEXT,
    price_relative_to_levels_json TEXT,
    payload_hash TEXT NOT NULL, created_at BIGINT NOT NULL
);

-- ohlcv_bars
CREATE TABLE ohlcv_bars (
    bar_set_id TEXT NOT NULL, symbol TEXT NOT NULL,
    interval TEXT NOT NULL, ts BIGINT NOT NULL,
    open DOUBLE, high DOUBLE, low DOUBLE, close DOUBLE,
    volume BIGINT, source TEXT NOT NULL,
    PRIMARY KEY (bar_set_id, symbol, interval, ts)
);

-- vol_index_history (B4: observation_time BIGINT)
CREATE TABLE vol_index_history (
    observation_time BIGINT NOT NULL,
    index_name TEXT NOT NULL, value DOUBLE, coverage DOUBLE,
    freshness_s DOUBLE, liquidity_confidence DOUBLE,
    component_contributions_json TEXT, index_version TEXT,
    PRIMARY KEY (observation_time, index_name)
);

-- calibration_model
CREATE TABLE calibration_model (
    model_id TEXT PRIMARY KEY, target TEXT NOT NULL,
    route TEXT NOT NULL, dte_lane TEXT NOT NULL,
    horizon TEXT NOT NULL,
    label_version TEXT NOT NULL, feature_version TEXT NOT NULL,
    ruleset_version TEXT NOT NULL,
    training_start BIGINT, training_end BIGINT,
    calibration_start BIGINT, calibration_end BIGINT,
    holdout_start BIGINT, holdout_end BIGINT,
    sample_size INTEGER NOT NULL, method TEXT NOT NULL,
    hyperparameters_json TEXT, grid_json TEXT,
    coefficients_json TEXT,
    brier DOUBLE, log_loss DOUBLE, calibration_error DOUBLE,
    validation_status TEXT NOT NULL,
    model_hash TEXT NOT NULL, fitted_at BIGINT NOT NULL,
    -- v2.0.5.1 ML provisions (additive; nullable for legacy rows)
    model_family TEXT
        CHECK(model_family IS NULL OR model_family IN
              ('DETERMINISTIC','LOGISTIC_L2','GBM','OTHER')),
    feature_names_json TEXT,
    preprocessor_json TEXT,
    minority_class_n INTEGER
);

-- model_predictions (RESERVED — do not create until
-- SPEC Vol 6 Phase C).
-- Will record one row per (analysis_snapshot_id, model_id,
-- target) for CHALLENGER and SHADOW models. Champion
-- predictions remain in the existing path
-- (signal_ledger.calibrated_p, analysis_snapshots.
-- calibrated_probability). See SPEC Vol 6 §F.4 for the DDL
-- applied when the first challenger ships.

-- scoring_rule_registry
CREATE TABLE scoring_rule_registry (
    rule_id TEXT NOT NULL, ruleset_version TEXT NOT NULL,
    hypothesis TEXT NOT NULL, feature_definition TEXT NOT NULL,
    threshold_json TEXT, expected_direction TEXT,
    eligible_strategy TEXT, target_horizon TEXT,
    effective_from BIGINT NOT NULL, effective_to BIGINT,
    training_sample INTEGER, validation_result TEXT,
    status TEXT NOT NULL,
    PRIMARY KEY (rule_id, ruleset_version)
);

-- raw_provider_events (analytical mirror)
CREATE TABLE raw_provider_events (
    raw_id TEXT PRIMARY KEY, provider TEXT NOT NULL,
    provider_event_id TEXT,
    received_at BIGINT NOT NULL, source_ts BIGINT,
    payload TEXT, payload_hash TEXT NOT NULL,
    parser_version TEXT NOT NULL, schema_version TEXT NOT NULL,
    access_channel TEXT NOT NULL, ingested_at BIGINT NOT NULL
);

-- price_observations
CREATE TABLE price_observations (
    observation_id TEXT PRIMARY KEY, ticker TEXT NOT NULL,
    price_micros BIGINT NOT NULL,
    price_basis TEXT NOT NULL CHECK(price_basis IN
        ('CASH_INDEX','EQUITY_LAST','NBBO_MID','PERP_MARK','PROXY',
         'DELAYED','CACHED')),
    source TEXT NOT NULL, provider_ts BIGINT NOT NULL,
    received_at BIGINT NOT NULL, sequence BIGINT,
    currency TEXT DEFAULT 'USD', staleness_ms INTEGER NOT NULL,
    quality_flag TEXT NOT NULL,
    is_synthetic_proxy INTEGER NOT NULL DEFAULT 0,
    basis_vs_reference_bps REAL, reference_source TEXT,
    reference_observation_id TEXT, created_at BIGINT NOT NULL
);
CREATE INDEX idx_price_obs_ticker
    ON price_observations(ticker, provider_ts);

-- analysis_snapshots (P0-4 evidence fields renamed)
CREATE TABLE analysis_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    thesis_id TEXT, ticker TEXT NOT NULL, as_of BIGINT NOT NULL,
    trigger_type TEXT NOT NULL CHECK(trigger_type IN
        ('flow-event','scheduled','ad-hoc','price-alert')),
    flow_cutoff_ts BIGINT,
    quote_snapshot_id TEXT,               -- FK: quote_snapshot_batches
    package_quote_observation_id TEXT,    -- FK: package_quote_observations.observation_id
    option_quote_observation_ids_json TEXT, -- JSON array; each element is an
                                          -- option_quote_observations.observation_id
    dealer_snapshot_id TEXT, volatility_snapshot_id TEXT,
    portfolio_snapshot_id TEXT, technical_snapshot_id TEXT,
    market_map_snapshot_id TEXT, dealer_map_id TEXT,
    calibration_model_id TEXT, route_ruleset_id TEXT,
    decision_kernel_version TEXT,
    ruleset_version TEXT NOT NULL, feature_version TEXT NOT NULL,
    data_quality_grade TEXT NOT NULL,
    source_completeness TEXT NOT NULL,
    dte_lane TEXT, structure TEXT, evidence_tier INTEGER,
    route TEXT, decision TEXT NOT NULL,
    actionability_reason TEXT,
    calibrated_probability DOUBLE,
    calibrated_probability_lower DOUBLE,
    expected_return_net_costs DOUBLE, expected_return_lower DOUBLE,
    expected_shortfall DOUBLE,
    dealer_map_outputs_json TEXT,
    trace_id TEXT,
    input_manifest_hash TEXT NOT NULL, payload_hash TEXT NOT NULL,
    payload_json TEXT NOT NULL, created_at BIGINT NOT NULL
);
CREATE INDEX idx_snap_thesis ON analysis_snapshots(thesis_id, as_of);
CREATE INDEX idx_snapshot_trace ON analysis_snapshots(trace_id);
CREATE INDEX idx_snap_ticker ON analysis_snapshots(ticker, as_of);
CREATE INDEX idx_snap_decision
    ON analysis_snapshots(decision, as_of);

-- market_map_snapshots
CREATE TABLE market_map_snapshots (
    map_id TEXT PRIMARY KEY, ticker TEXT NOT NULL,
    session_date DATE NOT NULL, as_of BIGINT NOT NULL,
    source_versions_json TEXT NOT NULL,
    dealer_map_id TEXT NOT NULL, technical_snapshot_id TEXT NOT NULL,
    price_observation_id TEXT NOT NULL,
    input_manifest_hash TEXT NOT NULL,
    ruleset_version TEXT NOT NULL, feature_version TEXT NOT NULL,
    anchored_vwap_levels_json TEXT,
    moving_average_stack_json TEXT,
    call_wall_levels_json TEXT, put_wall_levels_json TEXT,
    gamma_flip_json TEXT,
    vanna_magnets_json TEXT, vanna_repellents_json TEXT,
    charm_decay_levels_json TEXT, high_gamma_zone_json TEXT,
    zero_dte_delta_decay_json TEXT,
    major_support_levels_json TEXT, major_resistance_levels_json TEXT,
    confluence_zones_json TEXT,
    quality_flags TEXT, coverage_pct DOUBLE,
    created_at BIGINT NOT NULL
);
CREATE INDEX idx_map_ticker_date
    ON market_map_snapshots(ticker, session_date, as_of);

-- market_map_levels
CREATE TABLE market_map_levels (
    map_id TEXT NOT NULL, level_id TEXT NOT NULL,
    level_type TEXT NOT NULL, price_mills BIGINT NOT NULL,
    expiration_scope TEXT, source TEXT, magnitude DOUBLE,
    distance_sigma DOUBLE, quality_flags TEXT,
    PRIMARY KEY (map_id, level_id),
    FOREIGN KEY (map_id) REFERENCES market_map_snapshots(map_id)
);

-- dealer_level_maps
CREATE TABLE dealer_level_maps (
    dealer_map_id TEXT PRIMARY KEY, ticker TEXT NOT NULL,
    session_date DATE NOT NULL, spot_micros BIGINT,
    price_observation_id TEXT NOT NULL, price_basis TEXT NOT NULL,
    provider TEXT NOT NULL, provider_as_of BIGINT NOT NULL,
    received_at BIGINT NOT NULL,
    dealer_perspective TEXT NOT NULL, data_scope TEXT NOT NULL,
    model_version TEXT NOT NULL, sign_convention TEXT NOT NULL,
    exposure_unit TEXT NOT NULL,
    coverage DOUBLE, quality_grade TEXT,
    dealer_snapshot_ids_json TEXT NOT NULL,
    input_manifest_hash TEXT NOT NULL,
    ruleset_version TEXT NOT NULL, feature_version TEXT NOT NULL,
    volland_native_gamma_flip DOUBLE,
    quantflow_derived_gamma_flip DOUBLE,
    derived_flip_method_version TEXT, derived_flip_coverage DOUBLE,
    derived_flip_bracket_json TEXT,
    gamma_flip_difference_points DOUBLE,
    gamma_flip_difference_sigma DOUBLE,
    gamma_flip_alignment_status TEXT,
    cumulative_vanna_zero_cross DOUBLE,
    paired_exposure_zones_json TEXT, gamma_air_pockets_json TEXT,
    ranked_confluence_zones_json TEXT,
    bullish_scenario_path_json TEXT, bearish_scenario_path_json TEXT,
    term_structure_available INTEGER NOT NULL DEFAULT 0,
    expiration_attribution_available INTEGER NOT NULL DEFAULT 0,
    per_strike_delta_available INTEGER NOT NULL DEFAULT 0,
    iv_context_available INTEGER NOT NULL DEFAULT 0,
    charm_available INTEGER NOT NULL DEFAULT 0,
    zero_dte_delta_decay_available INTEGER NOT NULL DEFAULT 0,
    valid_from BIGINT NOT NULL, valid_until BIGINT,
    rollover_required INTEGER NOT NULL DEFAULT 0,
    created_at BIGINT NOT NULL
);

-- dealer_map_regime (DuckDB 051, PROPOSED CORE; C12; 1:1 child of dealer_level_maps, append-only)
CREATE TABLE dealer_map_regime (
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
CREATE INDEX idx_dlm_ticker_date
    ON dealer_level_maps(ticker, session_date, provider_as_of);

-- dealer_levels
CREATE TABLE dealer_levels (
    dealer_map_id TEXT NOT NULL, level_id TEXT NOT NULL,
    price_mills BIGINT NOT NULL, role TEXT NOT NULL,
    metric TEXT NOT NULL CHECK(metric IN
        ('gamma','vanna','charm','delta_decay')),
    expiration_scope TEXT NOT NULL, option_scope TEXT,
    component_expirations_json TEXT,
    signed_exposure_value DOUBLE, exposure_unit TEXT NOT NULL,
    magnitude_rank INTEGER, tactical_relevance_rank INTEGER,
    distance_sigma DOUBLE, first_seen BIGINT, last_seen BIGINT,
    strength DOUBLE, change_pct DOUBLE,
    lifecycle_status TEXT NOT NULL, scenario_activation_json TEXT,
    confidence DOUBLE, valid_until BIGINT,
    source_model_version TEXT, quality_flags TEXT,
    PRIMARY KEY (dealer_map_id, level_id),
    FOREIGN KEY (dealer_map_id)
        REFERENCES dealer_level_maps(dealer_map_id)
);
CREATE INDEX idx_dlevels_role
    ON dealer_levels(role, expiration_scope);

-- cot_snapshots
CREATE TABLE cot_snapshots (
    cot_snapshot_id TEXT PRIMARY KEY,
    market_code TEXT NOT NULL, as_of_date DATE NOT NULL,
    release_at BIGINT NOT NULL, report_type TEXT NOT NULL,
    revision_number INTEGER NOT NULL DEFAULT 0,
    dealer_long BIGINT, dealer_short BIGINT,
    asset_manager_long BIGINT, asset_manager_short BIGINT,
    leveraged_funds_long BIGINT, leveraged_funds_short BIGINT,
    other_reportables_long BIGINT, other_reportables_short BIGINT,
    nonreportable_long BIGINT, nonreportable_short BIGINT,
    open_interest BIGINT, percentiles_json TEXT,
    source_hash TEXT NOT NULL, created_at BIGINT NOT NULL
);
CREATE INDEX idx_cot_market_date
    ON cot_snapshots(market_code, as_of_date);

-- closing_fdi_snapshots
CREATE TABLE closing_fdi_snapshots (
    fdi_snapshot_id TEXT PRIMARY KEY,
    snapshot_date DATE NOT NULL, ticker TEXT NOT NULL,
    window_start BIGINT NOT NULL, window_end BIGINT NOT NULL,
    calculation_phase TEXT NOT NULL CHECK(calculation_phase IN
        ('PRE_CLOSE','UPDATE','FINAL')),
    fdi_raw DOUBLE,
    bull_delta_dollars DOUBLE, bear_delta_dollars DOUBLE,
    gross_delta_dollars DOUBLE,
    symbol_breadth DOUBLE, sector_breadth DOUBLE,
    flow_intensity_percentile DOUBLE,
    same_time_historical_percentile DOUBLE,
    coverage_pct DOUBLE, independent_event_count INTEGER,
    package_netted_count INTEGER,
    persistence_duration_s INTEGER,
    classification_version TEXT NOT NULL,
    quality_label_t1 TEXT, source_versions TEXT,
    calculated_at BIGINT NOT NULL,
    created_at BIGINT NOT NULL
);
CREATE INDEX idx_fdi_date_ticker
    ON closing_fdi_snapshots(snapshot_date, ticker,
                             calculation_phase);

-- leveraged_etf_pressure
CREATE TABLE leveraged_etf_pressure (
    snapshot_date DATE NOT NULL, etf_ticker TEXT NOT NULL,
    underlying_ticker TEXT NOT NULL,
    leverage_multiple REAL NOT NULL, benchmark_return DOUBLE,
    aum_estimate DOUBLE, aum_as_of BIGINT, nav_source TEXT,
    shares_change BIGINT,
    estimated_rebalance_flow_dollars DOUBLE, flow_direction TEXT,
    underlying_dealer_gamma DOUBLE, confidence DOUBLE,
    calculation_version TEXT NOT NULL, coverage_flags TEXT,
    source_versions TEXT, created_at BIGINT NOT NULL,
    PRIMARY KEY (snapshot_date, etf_ticker)
);

-- spx_crossing_state_history
CREATE TABLE spx_crossing_state_history (
    state_id BIGINT, level_id TEXT NOT NULL, map_id TEXT,
    session_date DATE NOT NULL,
    level_price_mills BIGINT NOT NULL, level_source TEXT NOT NULL,
    expiration_scope TEXT, direction TEXT, state TEXT NOT NULL,
    entered_at BIGINT NOT NULL, last_transition_at BIGINT NOT NULL,
    spot_at_entry_micros BIGINT, close_price_micros BIGINT,
    confirmation_window_s INTEGER,
    confirmation_distance_mills BIGINT,
    cooldown_until INTEGER, rearmed_at INTEGER,
    invalidated_by_map_id TEXT, evidence_json TEXT,
    created_at BIGINT NOT NULL, PRIMARY KEY (state_id),
    CHECK(state != 'COOLDOWN'    OR cooldown_until        IS NOT NULL),
    CHECK(state != 'REARMED'     OR rearmed_at            IS NOT NULL),
    CHECK(state != 'INVALIDATED' OR invalidated_by_map_id IS NOT NULL)
);
CREATE INDEX idx_spx_state_hist
    ON spx_crossing_state_history(state, entered_at);

-- market_events
CREATE TABLE market_events (
    event_id TEXT PRIMARY KEY, event_type TEXT NOT NULL,
    symbol TEXT, start_at BIGINT NOT NULL, end_at BIGINT,
    description TEXT, source TEXT NOT NULL,
    created_at BIGINT NOT NULL
);
CREATE INDEX idx_events_start ON market_events(start_at);

-- macro_market_observations (B4: observed_at BIGINT)
CREATE TABLE macro_market_observations (
    observed_at BIGINT NOT NULL, symbol TEXT NOT NULL,
    price DOUBLE, funding_rate DOUBLE, open_interest DOUBLE,
    volume_24h DOUBLE, source TEXT NOT NULL,
    PRIMARY KEY (observed_at, symbol)
);

-- macro_regime_snapshots (B4: observed_at BIGINT)
CREATE TABLE macro_regime_snapshots (
    observed_at BIGINT NOT NULL, symbol TEXT NOT NULL,
    close DOUBLE, return_5d DOUBLE, credit_spread_proxy DOUBLE,
    regime_label TEXT, source TEXT NOT NULL,
    PRIMARY KEY (observed_at, symbol)
);

-- exit_evaluations (AH analytical mirror)
CREATE TABLE exit_evaluations (
    evaluation_id TEXT PRIMARY KEY,
    operational_event_id TEXT NOT NULL UNIQUE,
    position_id TEXT NOT NULL,
    policy_hash TEXT NOT NULL,
    policy_activation_id TEXT NOT NULL,
    state_revision BIGINT NOT NULL,
    evaluated_at BIGINT NOT NULL,
    input_manifest_hash TEXT NOT NULL,
    position_revision INTEGER NOT NULL,
    theta_consumed_microcents BIGINT NOT NULL,
    hard_deadline_at BIGINT NOT NULL,
    triggers_json TEXT NOT NULL,
    primary_trigger TEXT,
    pricing_status TEXT,
    pnl_liq_cents BIGINT,
    loss_ratio DOUBLE,
    recommendation TEXT,
    payload_json TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    created_at BIGINT NOT NULL
);
CREATE INDEX idx_exit_eval_position
    ON exit_evaluations(position_id, evaluated_at);
CREATE INDEX idx_exit_eval_policy
    ON exit_evaluations(policy_hash, evaluated_at);

-- ivr_history (AH; 252-day IVR source)
CREATE TABLE ivr_history (
    ticker TEXT NOT NULL,
    observation_date DATE NOT NULL,
    iv_30d_atm DOUBLE NOT NULL,
    source TEXT NOT NULL,
    input_manifest_hash TEXT NOT NULL,
    created_at BIGINT NOT NULL,
    PRIMARY KEY (ticker, observation_date)
);
CREATE INDEX idx_ivr_ticker_date
    ON ivr_history(ticker, observation_date);

-- zero_dte_cluster_snapshots
-- ALERT: MEDIUM_CONFLUENCE/HIGH_CONFLUENCE + non-null alert_ts.
-- BASIC_SHADOW: alert_grade=BASIC + alert_ts=NULL.
-- MIXED/REVERSAL/RETRACTION/EXPIRY: grade and alert_ts both NULL.
-- cluster_grade remains an independent evidence-grade field.
-- transition_ts is required for every snapshot.
CREATE TABLE zero_dte_cluster_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    cluster_id TEXT NOT NULL,
    episode_id TEXT NOT NULL,
    thesis_id TEXT,
    ticker TEXT NOT NULL,
    expiration DATE NOT NULL,
    direction TEXT NOT NULL,
    cluster_grade TEXT NOT NULL CHECK(cluster_grade IN
        ('BASIC','MEDIUM_CONFLUENCE','HIGH_CONFLUENCE')),
    cluster_state TEXT NOT NULL,
    episode_state TEXT NOT NULL,
    as_of BIGINT NOT NULL,
    alert_grade TEXT CHECK(alert_grade IN
        ('BASIC','MEDIUM_CONFLUENCE','HIGH_CONFLUENCE')),
    snapshot_type TEXT NOT NULL CHECK(snapshot_type IN
        ('ALERT','MIXED','REVERSAL','RETRACTION','EXPIRY',
         'BASIC_SHADOW')),
    alert_ts BIGINT,
    transition_ts BIGINT NOT NULL,
    first_event_ts BIGINT, last_event_ts BIGINT,
    independent_event_count INTEGER,
    distinct_strike_count INTEGER,
    gross_premium_mills BIGINT,
    net_delta_dollars DOUBLE,
    directional_dominance DOUBLE,
    opposing_share DOUBLE,
    flow_strength DOUBLE,
    dealer_alignment DOUBLE,
    price_confirmation DOUBLE,
    confluence_score DOUBLE,
    activation_level_mills BIGINT,
    activation_kind TEXT,
    target_level_mills BIGINT,
    target_kind TEXT,
    support_or_resistance_mills BIGINT,
    support_or_resistance_kind TEXT,
    invalidation_price_mills BIGINT,
    reference_spot_micros BIGINT,
    dealer_map_id TEXT, market_map_id TEXT,
    member_canonical_ids_json TEXT NOT NULL,
    member_economic_package_ids_json TEXT,
    data_quality_grade TEXT, coverage TEXT,
    notification_ids_json TEXT,
    ruleset_version TEXT NOT NULL, payload_hash TEXT NOT NULL,
    created_at BIGINT NOT NULL,
    CHECK(cluster_state IN
        ('ACTIVE','MIXED','BULLISH_REVERSAL','BEARISH_REVERSAL',
         'RETRACTED','EXPIRED')),
    CHECK(episode_state IN
        ('FORMING','ACTIVE','UPGRADED','REVERSED','RETRACTED',
         'EXPIRED')),
    CHECK (
        (snapshot_type = 'ALERT'
         AND alert_grade IS NOT NULL
         AND alert_grade IN ('MEDIUM_CONFLUENCE','HIGH_CONFLUENCE')
         AND alert_ts IS NOT NULL)
        OR
        (snapshot_type = 'BASIC_SHADOW'
         AND alert_grade IS NOT NULL AND alert_grade = 'BASIC'
         AND alert_ts IS NULL)
        OR
        (snapshot_type IN ('MIXED','REVERSAL','RETRACTION','EXPIRY')
         AND alert_grade IS NULL AND alert_ts IS NULL)
    )
);
CREATE UNIQUE INDEX uq_0dtcs_transition
    ON zero_dte_cluster_snapshots(
        cluster_id, snapshot_type, transition_ts);
CREATE INDEX idx_0dtcs_cluster
    ON zero_dte_cluster_snapshots(cluster_id, as_of);
CREATE INDEX idx_0dtcs_ticker_date
    ON zero_dte_cluster_snapshots(ticker, expiration, as_of);
CREATE INDEX idx_0dtcs_grade
    ON zero_dte_cluster_snapshots(alert_grade, as_of);

-- zero_dte_cluster_outcomes (rewritten; split by alert grade)
CREATE TABLE zero_dte_cluster_outcomes (
    outcome_id TEXT PRIMARY KEY,
    cluster_snapshot_id TEXT NOT NULL,
    cluster_id TEXT NOT NULL,
    episode_id TEXT NOT NULL,
    alert_grade TEXT NOT NULL CHECK(alert_grade IN
        ('MEDIUM_CONFLUENCE','HIGH_CONFLUENCE')),
    alert_ts BIGINT NOT NULL,
    reference_spot_micros BIGINT NOT NULL,
    horizon TEXT NOT NULL CHECK(horizon IN
        ('1m','5m','15m','30m','CLOSE')),
    target_level_mills BIGINT,
    invalidation_price_mills BIGINT,
    pre_5m_return DOUBLE,
    first_event_to_detection_return DOUBLE,
    post_1m_return DOUBLE,
    post_5m_return DOUBLE,
    post_15m_return DOUBLE,
    post_30m_return DOUBLE,
    to_close_return DOUBLE,
    mfe DOUBLE, mae DOUBLE,
    lead_lag_class TEXT CHECK(lead_lag_class IN
        ('FLOW_LED','COINCIDENT','PRICE_LED','INDETERMINATE')),
    target_hit_at BIGINT,
    invalidation_hit_at BIGINT,
    calculation_version TEXT NOT NULL,
    calculated_at BIGINT NOT NULL,
    UNIQUE (cluster_snapshot_id, horizon, calculation_version)
);
CREATE INDEX idx_0dtco_cluster
    ON zero_dte_cluster_outcomes(cluster_id);
CREATE INDEX idx_0dtco_episode_grade
    ON zero_dte_cluster_outcomes(episode_id, alert_grade);

--------------------------------------------------------------------------------

19.4 Money and Units

19.4.1 Executable option prices use _cents.
19.4.2 Underlying and index prices use _micros.
19.4.3 Strikes and levels use _mills.
19.4.4 SQLite *_cents / *_mills / *_micros columns are
       INTEGER (64-bit). DuckDB *_micros columns are BIGINT.
       DuckDB *_cents and *_mills columns are INTEGER or
       BIGINT as declared. All *_mills and *_micros columns
       that appear in the decision path are BIGINT.
19.4.5 DuckDB spot columns feeding executable logic are
       *_micros BIGINT.
19.4.6 DOUBLE columns are analysis only.

19.5 Relationships: enforced by FKs and ContextReconciler.

19.6 Invariants (full)

A  provider_query_budget.thesis_id NOT NULL ('_GLOBAL').
B  Executable price fields use _cents.
C  market_map_snapshots, dealer_level_maps and dealer_map_regime append-only.
D  Every operator action has operator_control_audit row.
E  Every price observation records source, staleness,
   synthetic-proxy, basis.
F  Every OpenMarket-triggered notification passed the trust
   boundary.
G  analysis_snapshot.dealer_map_id ==
   market_map_snapshot.dealer_map_id.
H  Every executable decision references a valid
   quote_snapshot_id and, for multi-leg evidence,
   package_quote_observation_id (immutable). Constituent
   option quotes are captured in
   option_quote_observation_ids_json. The mutable
   package_quote_current.package_quote_id is cache
   identity only and is never decision evidence.
I  Same analysis_snapshot_id → same decision.
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
S  Every "unique active X" invariant names its enforcement.
T  Every signal_ledger.calib_model_id and
   analysis_snapshots.calibration_model_id references an
   existing calibration_model.model_id.
U  RECONCILIATION_REQUIRED is an audit flag, not a decision
   state.
V  Provider query pool: used + 1 ≤ ceiling + available_borrow.
W  Every DuckDB epoch-ms column is BIGINT. Every SQLite
   epoch-ms column is INTEGER.
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
   dealer_map_id or market_map_id.
AA zero_dte_cluster_current is populated only for the current
   session.
AB cluster_grade contains only evidence-grade values
   (BASIC, MEDIUM_CONFLUENCE, HIGH_CONFLUENCE).
   cluster_state contains only lifecycle values (ACTIVE,
   MIXED, BULLISH_REVERSAL, BEARISH_REVERSAL, RETRACTED,
   EXPIRED). episode_state contains only episode-timeline
   values (FORMING, ACTIVE, UPGRADED, REVERSED, RETRACTED,
   EXPIRED). Enforced by CHECK constraints and a schema
   test.
AC Every removed member has a member_history row.
AD zero_dte_cluster_current.episode_id is UNIQUE.
AE every zero_dte_cluster_outcomes row references a
   cluster_snapshot_id whose alert_grade matches the row's
   alert_grade.
AF every notification.tier value is NULL or in
   ('critical','immediate','warning','informational','daily').
   Enforced by CHECK constraint added in Vol 5 §O.11.
AG every observability request is logged; no health
   endpoint call is unlogged. Enforced by the endpoint
   wrapper.
AH observability writes never target a decision-path table.
   Enforced by a SQL audit test.
AHa Every trace_id column referenced by SPEC Vol 5 §O.6.2
   is materialized in the canonical DDL above:
   provider_sessions.session_id, coverage_windows.session_id,
   detection_events.session_id, raw_provider_events.
   source_trace_id, canonical_events.trace_id,
   canonical_event_sources.source_trace_id,
   canonical_event_sources.canonical_trace_id,
   signal_ledger.trace_id, analysis_snapshots.trace_id.
   Enforced by a schema test that scans for each column.
AI Any feature vector presented to a model (champion or
   challenger) MUST be derived exclusively from an immutable
   analysis_snapshot. No feature may be read from a live
   store, a provider call, or wall-clock state. Enforced by
   the AnalysisSnapshotBuilder purity rule (§2.9.4) and by
   a CI lint that rejects feature-extraction functions
   whose name begins with fetch_, get_current_, or
   read_pointer_.
AJ model_features_hash on any model prediction MUST be a
   deterministic hash of (feature_names, feature_values,
   feature_version, analysis_snapshot_id). Same inputs →
   same hash. Enforced by a replay test.
AK Challenger and shadow model outputs MUST NOT be readable
   by any code path that produces a decision, a route, a
   size, a target, a stop, or a probability that reaches a
   user. Enforced by an import-boundary CI check.
AL Every scheduled task row with dedup_key NOT NULL and
   state IN ('PENDING','RUNNING') is unique on dedup_key.
   Enforced by uq_scheduled_task_dedup.
AM analysis_snapshots.package_quote_observation_id, when
   non-null, references an immutable
   package_quote_observations.observation_id. Every element
   of analysis_snapshots.option_quote_observation_ids_json,
   positions.entry_option_observation_ids_json, and
   positions.exit_option_observation_ids_json references an
   immutable option_quote_observations.observation_id.
   package_quote_current.package_quote_id remains an
   operational cache key only; it is NEVER written into any
   decision-path table.
AN Exactly one active_model_manifest row per (model_kind,
   scope_key, ruleset_version) with model_role = 'CHAMPION'
   and active_to IS NULL. Enforced by
   uq_active_champion_manifest.
AO zero_dte_cluster_current and zero_dte_cluster_snapshots
   store price levels (activation, target,
   support/resistance, invalidation) in _mills. Spot
   references (reference_spot_micros, detection_spot_micros,
   first_spot_micros) remain in _micros. Conversion is
   ×1000 (mills = micros / 1000). Enforced by schema test.
AP Every DDL table that appears in both ARCH Vol 2 and
   SPEC Vol 2 hashes identically after whitespace
   normalization. Enforced by a schema-hash test.
AQ Before any supported route carries position risk, a
   position_exit_state row references its frozen active policy via
   (position_id, active_policy_hash). The primary key permits only
   one current pointer per position. Old policy rows remain immutable.
   An explicitly approved policy change records a new activation and
   operator audit; it does not reset accrued theta or latched risk.
AR Every exit evaluation is first committed with operational event
   evidence in SQLite. pending_exit_sync mirrors the same evaluation_id
   and payload hash into DuckDB. Retry with the same ID is a no-op;
   conflicting content for the same ID is a reconciliation fault.
AS New fill rows have non-null broker, account_ref, execution_id,
   execution_leg_key, leg_number, side and position_effect. The unique
   key is (broker, account_ref, execution_id, execution_leg_key),
   independent of position_id. Venue is not broker identity. Unknown
   legacy identity is reconciled/quarantined, never silently invented.
AT Theta intervals are non-overlapping and contiguous per activation
   and quantity epoch. The writer atomically checks the stored cursor,
   inserts the unique interval event and advances the accumulator.
   A unique key alone is not proof of non-overlap. Gap/overlap blocks
   accumulation until reconciled; a replay never increments twice.
AU Exit-trigger latches, active policy, deadline, quantity revision,
   event evidence, retry queue and material notification are committed
   in SQLite before delivery. DuckDB unavailability does not clear a
   known exit. New entries still respect all existing data gates.

19.7 Consistency: transaction boundaries + ContextReconciler.

19.8 Date, Time, Timestamp Conventions: per SPEC Vol 1 §19.8.

19.9 Schema Hardening Summary

  - position_legs.multiplier > 0 (was >= 0).
  - position_fills.quantity > 0.
  - position_fills FK to (position_id, leg_number).
  - position_fills execution identity is non-null; uq_fill_dedup is
    (broker, account_ref, execution_id, execution_leg_key).
  - option_quote_current: bid_cents >= 0; ask_cents >=
    bid_cents.
  - package_quote_current: net_ask_cents >= net_bid_cents.
  - portfolio_state_current singleton enforced by CHECK
    singleton_id = 1.
  - shadow_samples.feature_hash replaces feature_snapshot_id.
  - signal_outcomes.outcome_scope_id replaces PK COALESCE.
  - signal_outcomes.analysis_snapshot_id replaces
    feature_snapshot_id.
  - P0-4: evidence fields renamed to immutable observation
    IDs.
  - P0-5: 0DTE cluster level columns renamed to _mills.
  - P0-6: snapshot_type added to zero_dte_cluster_snapshots;
    explicit NULL-safe ALERT/BASIC_SHADOW/lifecycle branches;
    transition_ts required and transition uniqueness enforced.
  - B4: all DuckDB TIMESTAMP columns converted to BIGINT.
  - B7.1: notifications gains notification_domain,
    requires_ack, acknowledged_at, acknowledged_by,
    escalated_from_notification_id.

================================================================================
END OF SPEC Vol 2 v2.0.5.1
================================================================================