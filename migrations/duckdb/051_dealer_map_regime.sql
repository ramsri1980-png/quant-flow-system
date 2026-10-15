-- DuckDB 051 (PROPOSED CORE, C12). Forward-only. Depends: baseline dealer_level_maps. Not research 043-045.
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
