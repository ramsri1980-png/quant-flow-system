-- DuckDB 052 (PROPOSED CORE, evaluation). Forward-only. Append-only; latest rated_at per alert_ref wins.
CREATE TABLE operator_alert_ratings (
    rating_id TEXT PRIMARY KEY,
    alert_kind TEXT NOT NULL CHECK(alert_kind IN ('FLOW_ALERT','ZERO_DTE_CLUSTER','MORNING_BRIEF','AD_HOC')),
    alert_ref TEXT NOT NULL,                 -- notification_id or cluster_snapshot_id
    rating TEXT NOT NULL CHECK(rating IN ('USEFUL','NOT_USEFUL','UNSURE')),
    reason_code TEXT,                        -- optional short code, e.g. LATE, WRONG_DIRECTION, NOISE
    note TEXT,
    audit_id BIGINT NOT NULL,                -- operator_control_audit.id (SQLite) of the quantctl call
    rated_at BIGINT NOT NULL
);
CREATE INDEX idx_oar_alert ON operator_alert_ratings(alert_kind, alert_ref, rated_at);
