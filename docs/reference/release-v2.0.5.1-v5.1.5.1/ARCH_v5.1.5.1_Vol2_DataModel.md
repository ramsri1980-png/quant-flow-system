# QUANT FLOW SYSTEM — TECHNICAL ARCHITECTURE v5.1.5.1
## VOLUME 2 — DATA MODEL

Status: self-contained for the sections this volume owns.
Sections not owned by this volume reference the owning
volume within the 10-file set by section number.

CHANGES FROM v5.1.5
- P0-3: cluster_state is lifecycle-only.
- P0-4: decision-path evidence fields renamed to immutable
  observation IDs.
- P0-5: price levels use _mills, spots use _micros.
- P0-6: snapshot_type on zero_dte_cluster_snapshots; DDL
  parity rule; FK parity on cluster members.
- B4: no native TIMESTAMP columns in DuckDB.
- B5.1: zero_dte_cluster_snapshots gains nullable alert
  fields, transition_ts, and CHECK constraints.
- B7.1: notifications gains notification_domain,
  requires_ack, acknowledged_at, acknowledged_by,
  escalated_from_notification_id.
- Migrations 065–067 added.
- AH: position_exit_policies, broker_cutoff_registry,
  position_fills exit columns, exit_evaluations,
  ivr_history. Migrations SQLite 070, DuckDB 042.

CHANGES FROM THIS REVIEW (M01–M10)
- M01: snapshot composite CHECK rewritten NULL-safe.
- M02: position_fills rebuilt with non-null execution
  identity and fill_origin.
- M02b: uq_fill_dedup replaces nullable partial index with
  a non-null four-column unique key.
- M03: position_exit_state, position_exit_events and
  pending_exit_sync added.
- M04: exit_evaluations rewritten as a reconstructable
  analytical mirror.
- M05: migration runner contract rewritten with
  enabled/adopted module set and per-module dependency.
- M06: SQLite 071 reserved for a proposed core repair
  (fill identity, exit state, events, retry queue).
- M07: DuckDB 050 reserved as a core repair without
  consuming research IDs 043–045.
- M08/M09: baseline wording clarified.
- M10: AH reconciliation rules replaced with active pointer
  and source identity.

CHANGES FROM v5.1.4
- zero_dte_cluster_current: grade/state/episode split;
  UNIQUE(episode_id); new columns.
- zero_dte_cluster_member_history added.
- Hardening: multiplier > 0, quantity > 0, quote checks,
  singleton portfolio_state_current, FK fills→legs,
  shadow_samples.feature_hash.
- signal_outcomes: outcome_scope_id materialized; renamed
  feature_snapshot_id → analysis_snapshot_id.
- zero_dte_cluster_snapshots/outcomes rewritten.
- Migrations 057–060 (SQLite), 033–034 (DuckDB) added.

Authoritative DDL lives in SPEC v2.0.5.1 Vol 2 §19. This
volume repeats the DDL in identical form for self-
containment; if the two ever differ, SPEC Vol 2 §19 is the
canonical home. DDL parity is enforced by a schema-hash
test (see §C.4).

================================================================================
C.1 SQLite — /data/quant_state.db
================================================================================

Pragmas at open:
  journal_mode = WAL;
  synchronous = NORMAL;
  cache_size = -16000;
  temp_store = MEMORY;
  mmap_size = 268435456;
  foreign_keys = ON;
  busy_timeout = 5000;

WAL discipline: PRAGMA wal_checkpoint(TRUNCATE) forced during
low-activity session breaks and whenever
quant_state.db-wal exceeds WAL_SIZE_CEILING_MB.

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

-- (security_policies, provider_sessions, provider_state,
--  provider_rate_limits, provider_instrument_map,
--  provider_capabilities, provider_alert_attributes,
--  live_price_current: identical to SPEC Vol 2 §19.2)

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
-- package_quote_current.package_quote_id is an operational
-- cache key only. It MUST NOT be written into any
-- decision-path table (see §C.4).

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

-- positions (P0-4 evidence fields renamed)
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

-- zero_dte_cluster_current (P0-3 cluster_state lifecycle-only;
-- P0-5 levels in _mills)
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

-- notifications (B7.1 notification_domain + ack columns)
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

-- behavioral_reference (added operator_routine type)
CREATE TABLE behavioral_reference (
    reference_id TEXT PRIMARY KEY,
    reference_type TEXT NOT NULL CHECK(reference_type IN
        ('login_timings','session_lengths','dwell_distributions',
         'weekend_pattern','holiday_pattern','operator_routine')),
    reference_json TEXT NOT NULL,
    observed_at INTEGER NOT NULL,
    source_note TEXT NOT NULL, updated_at INTEGER NOT NULL
);

-- (all other SQLite tables identical to SPEC Vol 2 §19.2)
-- P0-4 note: analysis_snapshots.package_quote_observation_id
-- and option_quote_observation_ids_json are the only
-- evidence fields permitted in decision-path tables.
-- package_quote_current.package_quote_id is operational
-- cache only and never enters decision evidence.
-- B2 note: the correlation columns referenced by SPEC Vol 5
-- §O.6.2 (provider_sessions.session_id,
-- coverage_windows.session_id, raw_provider_events.
-- source_trace_id, canonical_events.trace_id,
-- canonical_event_sources.{source_trace_id,
-- canonical_trace_id}) are canonically defined in SPEC
-- Vol 2 §19.2. The matching DuckDB trace columns
-- (signal_ledger.trace_id, analysis_snapshots.trace_id)
-- are canonically defined in SPEC Vol 2 §19.3.

================================================================================
C.2 DuckDB — /data/quant_flow.duckdb
================================================================================

Pragmas: memory_limit='1.2GB'; threads=2;
temp_directory='/data/duckdb_tmp'.

Epoch-ms rule: all DuckDB epoch-ms columns are BIGINT. No
native TIMESTAMP columns are permitted in DuckDB. Enforced
by schema test that scans for TIMESTAMP and rejects.

-- schema_version_duckdb
CREATE TABLE schema_version_duckdb (
    migration_id TEXT PRIMARY KEY, checksum TEXT NOT NULL,
    applied_at BIGINT NOT NULL, app_version TEXT NOT NULL,
    result TEXT NOT NULL CHECK(result IN ('OK','FAILED'))
);

-- signal_outcomes (hardened)
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

-- (all other DuckDB tables identical to SPEC Vol 2 §19.3)
-- B2 note: signal_ledger.trace_id and
-- analysis_snapshots.trace_id are canonically defined in
-- SPEC Vol 2 §19.3. Both feed the correlation-trace query
-- in SPEC Vol 5 §O.6.3.

================================================================================
C.3 Migration Order
================================================================================

migrations/
  sqlite/
    000_baseline_v2.0.5.1.sql   -- combined final v2.0.5.1 schema
                                -- through SQLite 069 / DuckDB 041;
                                -- first file on fresh install; then apply
                                -- enabled pending migrations below.
                                -- Historical upgrade migrations
                                -- 001..064 are folded into the
                                -- baseline. Filenames and SHA-256
                                -- values pinned in MANIFEST.md.
    057_zero_dte_cluster_grade_state_split.sql   (immutable)
    058_position_fills_and_legs_constraints.sql  (immutable)
    059_quote_current_check_constraints.sql      (immutable)
    060_portfolio_state_singleton.sql            (immutable)
    061_observability_requests.sql               (immutable)
    062_observability_daily_summary.sql          (immutable)
    063_notifications_tier.sql                   (immutable)
    064_correlation_ids_sqlite.sql               (immutable)
    065_zero_dte_current_lifecycle_rebuild.sql
        -- SQLite zero_dte_cluster_current only: cluster_state
        -- lifecycle-only; UNIQUE(episode_id). Snapshot-type
        -- changes live in DuckDB 040.
    066_positions_quote_observation_lineage.sql
        -- SQLite positions evidence fields → observation IDs.
        -- (analysis_snapshots is DuckDB; see DuckDB 038.)
    067_zero_dte_current_level_units.sql
        -- zero_dte_cluster_current: activation/target/
        -- support_or_resistance/invalidation_price
        -- → _mills. Backfill: value / 1000.
    068_notification_ack_domain.sql
        -- Add notification_domain, requires_ack,
        -- acknowledged_at, acknowledged_by,
        -- escalated_from_notification_id.
        -- Backfill existing rows via the category-policy
        -- function (SYSTEM + requires_ack=1 for SYSTEM
        -- categories; TACTICAL/RESEARCH + requires_ack=0
        -- otherwise). Then drop column defaults so callers
        -- must set both explicitly.
    069_correlation_source_columns.sql
        -- raw_provider_events.source_trace_id;
        -- canonical_event_sources.source_trace_id,
        -- .canonical_trace_id.
    070_position_exit_policies.sql       (AH)
        -- position_exit_policies, broker_cutoff_registry,
        --   position_fills exit-semantics columns
        --   (side, position_effect, execution_id,
        --    position_revision, input_revision).
    071_core_exit_state_and_fill_identity.sql (PROPOSED CORE REPAIR)
        -- position_fills rebuild; position_exit_state;
        -- position_exit_events; pending_exit_sync.
        -- Depends on SQLite 070; stop on unreconciled legacy fills.
    072..079 RESERVED (future explicit approval only).

  duckdb/
    000_baseline_v2.0.5.1.sql   -- combined final v2.0.5.1 schema
                                -- through SQLite 069 / DuckDB 041;
                                -- first file on fresh install; then apply
                                -- enabled pending migrations below.
                                -- Historical upgrade migrations
                                -- 001..037 are folded into the
                                -- baseline. Filenames and SHA-256
                                -- values pinned in MANIFEST.md.
    033_signal_outcomes_scope_id.sql             (immutable)
    034_zero_dte_cluster_outcomes_rewrite.sql    (immutable)
    035_trace_spans.sql                          (immutable)
    036_slo_measurements.sql                     (immutable)
    037_correlation_ids_duckdb.sql               (immutable)
    038_analysis_snapshot_quote_lineage.sql
        -- analysis_snapshots quote fields → observation IDs.
    039_zero_dte_snapshot_outcome_units.sql
        -- zero_dte_cluster_snapshots +
        -- zero_dte_cluster_outcomes level fields → _mills.
    040_zero_dte_snapshot_type_state_checks.sql
        -- DuckDB zero_dte_cluster_snapshots only: snapshot_type
        -- column, CHECK constraints (including BASIC_SHADOW
        -- branch and nullable alert_ts / alert_grade),
        -- transition_ts, and unique index on (cluster_id,
        -- snapshot_type, transition_ts).
    041_timestamp_epoch_bigint_normalization.sql
        -- All native TIMESTAMP columns → BIGINT epoch ms.
    042_exit_evaluations.sql             (AH)
        -- exit_evaluations, ivr_history.
    043_ae_closing_fdi.sql       (RESERVED, ADOPTION REQUIRED)
    044_af_cot_context.sql       (RESERVED, ADOPTION REQUIRED)
    045_ag_leveraged_pressure.sql (RESERVED, ADOPTION REQUIRED)
    046..049 RESERVED (future extensions, including 046 ML).
    050_core_snapshot_check_and_exit_mirror.sql (PROPOSED CORE REPAIR)
        -- Null-safe snapshot CHECK; expanded exit_evaluations mirror.
        -- Depends on core 040 and 042, NOT on research 043-045.
    051_dealer_map_regime.sql            (PROPOSED CORE, C12)
        -- dealer_map_regime: 1:1 append-only child of dealer_level_maps (regime, net/gross, sign_fragile).
        -- Depends on baseline dealer_level_maps only; NOT on 050 or research 043-045.
    052_operator_alert_ratings.sql       (PROPOSED CORE, evaluation)
        -- operator_alert_ratings: append-only operator feedback written via quantctl rate.

Forward-only. Never edit an applied migration.

Migration runner contract:

  Baseline stays at SQLite 001-069 / DuckDB 001-041.
  000_baseline_v2.0.5.1.sql MUST NOT be blindly generated from the
  patched final DDL, which additionally contains 070/042 and 071/050.
  Generate it from the verified historical chain through its declared
  maximum only. A new baseline would require a new explicit manifest.

  Manifest entries record store, migration_id, SHA-256, dependencies,
  component (CORE/AE/AF/AG/FUTURE), and explicit enabled/adopted state.
  Baseline-covered IDs and real applied IDs are different provenance;
  do not compare a baseline checksum as though it were each historical
  migration file's checksum. Preserve baseline coverage metadata.

  Fresh: apply 000 once, record covered IDs, then apply enabled pending
  core migrations in dependency order: SQLite 070 then 071;
  DuckDB 042, 050, 051, then 052. Reserved AE/AF/AG numbers are NOT automatically
  applied or marked covered because their number is lower than 050.

  Upgrade: never replay 000. Compute
    pending = enabled_manifest_ids - baseline_covered_ids - applied_ids.
  Validate dependency closure and each applied checksum; execute a
  stable topological ordering (numeric ID breaks ties only).
  Never infer completeness from MAX(migration_id). AF 044 may be adopted
  before AE 043; later adoption MUST still apply pending 043.
  Both have their own base dependencies, not a dependency on each other.

  Same approved module set -> identical normalized fresh/upgrade schema.
  A reserved unadopted module is absent from both paths. Do not edit
  any applied migration. These are document contracts; actual old
  migration files and the operator's applied ledger must be inspected
  before an upgrade can be declared executable.

================================================================================
C.4 Cross-Store Reconciliation
================================================================================

Uniqueness invariants (each names its enforcement mechanism):
  - active_model_manifest: partial unique on
    (model_kind, scope_key, ruleset_version)
    WHERE active_to IS NULL AND model_role = 'CHAMPION'.
  - symbol_theses: partial unique on active-thesis key.
  - provider_query_pool: PK on (provider, market_date, pool).
  - provider_query_budget: PK includes workflow_scope.
  - daily_alert_items: UNIQUE (cycle_date, level_id).
  - market_map_current / dealer_map_current: PK on
    (ticker, session_date).
  - zero_dte_cluster_current: PK on cluster_id;
    UNIQUE(episode_id).
  - scheduled_tasks: partial unique on (dedup_key)
    WHERE state IN ('PENDING','RUNNING').

Cross-store reconciliation (startup + daily):
  - every analysis_snapshot references valid DuckDB IDs.
  - current-pointer tables reference latest immutable rows.
  - every signal_ledger row maps to a live signal_version.
  - every outbox row references existing notification or
    signal.
  - active_model_manifest entries have matching DuckDB rows.
  - every signal_ledger.calib_model_id and
    analysis_snapshots.calibration_model_id maps to an
    existing calibration_model.model_id.
  - every profile_cohort expected_* column matches wire_pins.
  - every provider_query_pool.used ≤ ceiling + borrowed.
  - every corporate_action_ingestion PENDING row is surfaced
    in the DQ report and gates flow alerts.
  - every zero_dte_cluster_current row with cluster_grade
    IN ('MEDIUM_CONFLUENCE','HIGH_CONFLUENCE') maps to ≥1
    zero_dte_cluster_snapshots row with snapshot_type =
    'ALERT'. Every episode, including BASIC, writes a final
    snapshot at expiry: 'EXPIRY' for MEDIUM/HIGH,
    'BASIC_SHADOW' for BASIC.
  - every zero_dte_cluster_members row maps to existing
    zero_dte_cluster_current and canonical_events.
  - every removed member has a member_history row.
  - no cluster snapshot references a future-as-of dealer_map_id
    or market_map_id.
  - every notification row with tier NOT NULL has a tier in
    the CHECK set; NULL is permitted (legacy).
  - every canonical_events row created after the
    correlation-ID cutover has a non-null trace_id.
  - every decision-path evidence field
    (analysis_snapshots.package_quote_observation_id,
    analysis_snapshots.option_quote_observation_ids_json,
    positions.entry_package_observation_id,
    positions.exit_package_observation_id,
    positions.entry_option_observation_ids_json,
    positions.exit_option_observation_ids_json) references
    an immutable observation table. package_quote_current
    keys are never written into decision evidence.
  - every open position has one position_exit_state active pointer
    resolving to its immutable position_exit_policies record.
  - fills are unique on (broker, account_ref, execution_id,
    execution_leg_key), without nullable identity components.
  - replaying a position_exit_events ID/hash does not advance state,
    accrue theta, consume depth or create notifications twice.
  - theta intervals have exact contiguous endpoints and quantity epochs;
    conflicts/gaps are explicit, not skipped.
  - pending_exit_sync resolves to durable EVALUATION events; mirrored
    exit_evaluations carry identical IDs and hashes. DuckDB downtime
    does not remove active operational exit state.
  - DDL parity: every CREATE TABLE and CREATE INDEX
    statement that appears in both ARCH V2 and SPEC V2
    hashes identically after whitespace and comment
    normalization. Enforced by a schema-hash comparison
    test that walks both files, extracts each CREATE TABLE
    and CREATE INDEX block by name, and asserts identical
    normalized hash per block and per set. Any divergence —
    including a missing index, an extra index, a different
    column type, or a differing CHECK constraint — is a
    data-quality-alarm.
  Discrepancies → data-quality-alarm.

================================================================================
END OF ARCH Vol 2 v5.1.5.1
================================================================================