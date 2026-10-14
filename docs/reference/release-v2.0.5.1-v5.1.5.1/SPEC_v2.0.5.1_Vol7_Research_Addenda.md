# QUANT FLOW SYSTEM — SPECIFICATION v2.0.5.1
## VOLUME 7 — RESEARCH ADDENDA (AE, AF, AG)

Status: additive to v2.0.5.1. Research-only, non-normative
until each section is formally adopted by the operator.
Does not modify the frozen anti-detection layer
(ARCH v5.1.5.1 Vol 3 §F), the decision pipeline
(SPEC v2.0.5.1 Vol 3 §8.4), or the canonical DDL
(SPEC v2.0.5.1 Vol 2 §19).

CHANGES FROM THE PRIOR REVIEW DRAFT
- R-AE01 through R-AE07: scope manifest, exact window
  boundaries with calculated_at separation, D0→DQ naming
  fix, package sentence repair, removal of the undefined
  package_netted_amount, sign fix on the worked example,
  and AE.8 replacement plus new AE.9 (baselines and
  percentile policy), AE.10 (annotation policy and late
  knowledge) and AE.11 (snapshot identity and storage).
- R-AF01 through R-AF04: single spreading count per group;
  availability fields split into local availability and
  HISTORICAL_PIT evidence; half-open 3-year lookback;
  cot_analytics keyed by category with fractional ranks.
- R-AG01 through R-AG06: simple return (not log); partial
  universe confidence wording; AUM/NAV discrepancy ratio
  normalization; fund/group observation identity;
  percentile in [0,100]; and remaining-orders wording.
- R-ADOPT: the ADOPTION section now carries explicit target
  schemas for AE, AF and AG, plus the module registry,
  invariants and required migration tests.

AUTHORITY
  AE, AF, AG are research-only, non-normative. They do
  not affect any decision, any alert, any route, or any
  sizing. They are additive to v2.0.5.1. Each section
  becomes normative only when the operator formally
  adopts it and applies its migration deltas.

  AH is NOT in this volume. AH is binding at Stage 4
  (Forward Paper) and lives in ARCH v5.1.5.1 Vol 4 §AH.

  Where any section here conflicts with any other volume,
  the other volume wins and this volume is corrected.

CONTENTS
  AE  Closing FDI (research context)
  AF  CFTC COT (weekly positioning context)
  AG  Leveraged ETF Pressure (research estimate)
  ADOPTION  Adoption procedure, target schemas, invariants
  APPENDIX  Source references

SOURCE NOTES
  This volume captures the research contract provided by
  the operator's technical clarification (AE_TECH_V1,
  AF_TECH_V1, AG_NO_FUND_FLOW_V1) and the associated
  research addenda. It is intended as a durable home so
  that the research is not lost. Numbers labeled [P] are
  proposed implementation choices, not validated market
  facts. Numbers labeled [R] come from primary sources
  cited in the Appendix.

================================================================================
AE. CLOSING FDI
================================================================================

AE.1 Meaning and Scope [E/P]

  Closing means near the session close, NOT a trade known
  to close a position.

  Measure captured provider-alert flow, not the full OPRA
  market and not actual dealer inventory.

  Freeze the canonical scope manifest defined in AE.2:
    target, universe_version, DTE_mask, provider_set_id,
    session_profile, classifier_version.
  scope_key = "ae1:" + SHA256(canonical JSON of that manifest).
  It is not a date, snapshot ID or ad-hoc concatenation.
  Scope changes require new compatible historical baselines.

  Default daily pulse: index/ETF context is a separately
  configured research scope. Preserve ordinary FLOW_ALERT
  exclusions.

  Keep 0DTE, 1DTE and >=2DTE components separate; an
  optional ALL_DTE summary must show each gross share and
  use its own baseline. Unknown opening/closing intent
  remains UNKNOWN. No flow is manufactured from
  gamma/vanna. Input/source changes reset baseline
  comparability.

AE.2 Scope Key, Provider Set, Candidate Denominator [P]

  SCOPE KEY
    Stable identity of the analysis population and method;
    NOT a session, date or snapshot ID.
    Content:
      target + universe_version + DTE_mask
        + provider_set_id + session_profile
        + classifier_version
    target = ticker or group; universe_version pins
    members and filters. Separate 0DTE, 1DTE and >=2DTE
    scopes.
    Identity:
      scope_key = "ae1:" + SHA256(canonical JSON).
      Sort keys/set-like lists; retain manifest.
      Also match window, session type and close offset
      for baselines.

  PROVIDER SET
    Expected feeds, frozen before collection.
    Manifest: source ID, Alerts view/filter, parser +
    mapping versions, authorization reference.
    Versioning:
      provider_set_id = hash(sorted manifest). Config
      change: new scope. Outage: lower coverage, same
      set. Cross-provider copies count once.

  CANDIDATE DENOMINATOR
    In-scope, time-eligible captured candidates known at
    evaluation; corrected and deduplicated BEFORE signing,
    quality or strength rejection.
    Count + premium ratios:
      count_ratio   = N_used / N_candidate
      premium_ratio = P_used / P_candidate
    Confirmed package = one count unit.
    Unresolved candidates stay in the denominator, not
    the numerator. P sums unsigned leg premiums once;
    never net the premiums.
    UNKNOWN is not 100%:
      Missing action/delta/multiplier stays in denominator.
      Missing premium, unlocatable records, or zero
      denominator => unavailable ratio; no strong pulse.

  CAPTURE COVERAGE
    C = min over expected providers p of
          (observed_seconds_p / 1,800)
    Count overlapping observed intervals once.
    Zero alerts is not downtime. Keep failed providers
    in the set; never remove one to make coverage rise.

  TEST EXAMPLE
    Blackbox 1,800s + Tradytics 1,260s: C = 70%.
    18/20 used: 90%.
    $90k/$120k signable premium: 75%.
    RESULT: NO STRONG PULSE.

  AE requires DQ A/B + coverage >= 90% + both signability
  ratios >= 90%, plus the remaining AE gates. Capture
  quality is NOT OPRA-market coverage.

AE.3 Exact Window and Phases [P; existing 30-minute choice]

  W = 1800 seconds. C is the versioned regular-session close.
  Cutoffs:
    PRE_CLOSE u=C-30m;
    UPDATE u=C-25m,-20m,-15m,-10m,-5m;
    FINAL u=C; calculate FINAL at C+120s for late arrivals.
  Every window is [u-W,u), inclusive start and exclusive end.
  window_end is u, NOT calculated_at; FINAL never includes after-close
  trades just because computation occurs two minutes later.
  Include only events and classifications available by calculated_at;
  the immutable snapshot itself becomes available only after it commits.

  For normal equities PRE_CLOSE covers 15:00-15:30 New York;
  FINAL covers 15:30-16:00. Half-day equivalents are 12:00-12:30
  and 12:30-13:00. Calendar exceptions come from the frozen calendar.
  SPX profiles use their declared cash/option session basis. Do not
  extend expiring SPXW beyond last_trade_at or substitute a 16:15
  profile silently. Missing calendar or a session shorter than 60m
  blocks computation. PRE_CLOSE/UPDATE are labelled PREVIEW.

AE.4 Event-Time Inputs and Quality [E/P]

  For each canonical economic event/package k:
    event_ts, available_at,
    leg actions a = +1 buy / -1 sell,
    quantities q, multipliers M,
    signed long-option deltas delta,
    event_spot_micros, DQ, package_id,
    source ids and versions.
  Require event_ts in window and available_at <=
  calculated_at; classifier/package membership must also
  have been known then.
  Reuse the canonical classifier; do not sign the same
  leg twice.

  Use latest Greek observation AT OR BEFORE the trade:
  maximum age 60s, or 5s for 0DTE. Synchronized spot
  age <= 2s [P].
  Missing action, delta, quantity or multiplier: exclude
  from signed totals but retain in candidate-quality
  denominator.
  Tier 1/2 packages count once, with actual leg quantities q already
  including the package ratios. Do not multiply a ratio twice.
  Unresolved candidates remain in N_candidate but not N_used; uncertain
  packages cannot inflate an independent-event numerator.

AE.5 Calculation and Units [E/P]

    S_kj = spot_micros_kj / 1,000,000 dollars
    X_k  = SUM_j(a_kj * delta_kj * q_kj * M_kj * S_kj)
    B = SUM max(X_k, 0)
    R = SUM max(-X_k, 0)
    G = B + R
    N = B - R
  Persist fdi_raw = N, bull_delta_dollars = B,
  bear_delta_dollars = R, gross_delta_dollars = G.
  I = N / G and fdi_norm = 100 * I only when G > 0.
  OpposingShare = min(B, R) / G.

  Call buy and put sell normally contribute positive;
  call sell and put buy negative, using signed vanilla
  delta. These are directional delta-dollar equivalents,
  not cash paid or dealer hedges.
  Flat net does not imply no activity:
    N = 0, G > 0 -> BALANCED
    G = 0 -> NO_SIGNED_FLOW and I = NULL.
  Never divide by max(G, 1), which fabricates a neutral
  score.

AE.6 Counts, Breadth, Concentration, Coverage [P]

  N_used = unique qualifying economic events (one per
  package).
  package_netted_count = count of used multi-leg packages.
  For a group of active symbols with G_s > 0:
    symbol_breadth = SUM sign(N_s) / n_s.
  Sector breadth uses sign of net flow aggregated within
  each sector, then equal weights across sectors.
  Largest-share = max_k abs(X_k) / G.
  Breadth range [-1, +1]. Require >= 5 active symbols
  and >= 3 active sectors; otherwise corresponding
  breadth = NULL. Single-symbol rows have NULL breadth.
  Store active-symbol count, universe version and
  unknown-sector share. A zero-event but observed symbol
  is not a bearish vote. Largest-share > 0.60 is
  SINGLE_EVENT_DOMINATED; do not claim broad conviction.

  C_p = observed seconds / 1,800 for each expected
  provider, capped at 1.
  coverage_pct = min_p(C_p) using the predeclared provider
  set.
  Signable-count = N_used / N_candidate.
  Signable-premium = usable unsigned reported premium /
  all candidate unsigned premium; use each canonical leg
  once and flag missing premium.
  Persistence uses consecutive completed,
  non-overlapping 5m bins ending at u whose I_bin has the
  same sign and abs(I_bin) >= 0.20.
  A no-event bin breaks persistence; a missing-coverage
  bin invalidates it.
  persistence_duration_s = 300 * consecutive-bin count.
  Coverage describes capture of an Alerts view, NOT total
  option-market coverage.
  Require DQ A/B, coverage >= 0.90, both signability
  ratios >= 0.90 for a strong pulse. Missing denominators
  block the pulse rather than being treated as 100%.

AE.7 Golden Examples

  +$2.0m bullish and $0.5m bearish => N = $1.5m,
  G = $2.5m, I = 0.60, opposing = 0.20.
  A +$600k / -$450k package contributes +$150k ONCE.
  Duplicate source copies change none of these totals.

AE.8 Alerts and adoption boundary

  NO_NEW_ALERTS remains the current policy. After calculation adoption,
  FDI may appear as dated context in morning/ad-hoc reports. It cannot
  satisfy actionability, change probability, route or size. A future
  closing-flow-pulse needs its own explicit notification adoption;
  neither this repair nor an AG notice enables it.

AE.9 Baselines, percentile ties and normalization [P]

  Use the most recent 60 eligible PRIOR sessions within the prior 90
  exchange trading sessions. Same scope_key, calculation/classifier
  version, 1800s window, session type and minutes-to-close offset.
  Exclude the current session and future/unavailable data. Match
  half-days only to half-days. Do not pool other DTE masks, providers,
  tickers or amended universes to reach a sample threshold.
  At most one accepted snapshot per logical prior-session cutoff;
  choose the latest version available at the current evaluation time.
  Every reference row must pass the same DQ/coverage/signability rules.
  Retain baseline snapshot IDs and evaluation cutoff.
  n<20: BASELINE_WARMUP, raw values only; 20-59 LIMITED_HISTORY;
  60 FULL_HISTORY. Do not extrapolate missed flow or fill absent days.

  Define the shared percentile on a nonempty eligible sample H:
    PR(x,H)=100*(count(h<x)+0.5*count(h=x))/len(H).
  PR uses scale [0,100], never [0,1], and is not a probability.
  Compare dollar values quantized to nearest $1 using ROUND_HALF_UP;
  ratios and percentage-point measures to 0.000001 with ROUND_HALF_UP.
  For AE: direction_rank=PR(I,H_I), intensity_rank=PR(G,H_G),
    intensity_multiple=G/median(H_G), unavailable if median=0;
    z_I=(I-median(H_I))/max(1.4826*MAD(H_I),0.05).
  I=N/G uses [-1,1], not the displayed 100*I. Store uncapped z;
  clip display only to [-5,5]. AF/AG use their own required samples
  and floors while sharing this midrank convention.

AE.10 Annotation policy and late knowledge [P]

  Primary label precedence:
    INVALID_OR_MISSING -> NO_SIGNED_FLOW -> BASELINE_WARMUP ->
    PARTIAL_CAPTURE_OR_SPARSE -> SINGLE_EVENT_DOMINATED ->
    BULLISH/BEARISH/BALANCED.
  The last direction uses abs(I)<0.20 as the neutral band.
  With adequate history, direction ranks >=95 / <=5 may be described
  as unusually bullish/bearish CAPTURED ALERT flow, not dealer orders
  or whole-market positioning. Add independent flags for preview,
  limited history, DTE mix, stale/conflicting dealer context and
  unconfirmed price. Invalid metadata takes precedence over a zero G.
  These annotations do not enable notifications.

  T+1 annotations are append-only records with known_at, method_version,
  evidence_hash and source snapshot ID. They are retrospective aggregate
  consistency evidence, not proof of which trade opened a position.
  As-of rendering selects only annotations known by the requested time.
  Do not update an old FDI value or immutable snapshot using T+1 data.

AE.11 Snapshot identity and storage [P]

  fdi_snapshot_id=SHA256(canonical JSON [session_date, scope_key,
    calculation_phase, window_end, calculation_version, input_manifest_hash]).
  input_manifest_hash includes the deduplicated candidate/classification,
  package, provider-coverage and baseline manifests used in calculation.
  All manifest observations must be available by calculated_at.
  Same inputs -> same ID. Changed late data -> new immutable snapshot,
  supersedes_id and correction_reason. Do not mutate the first FINAL.
  available_at is actual local commit/availability time, never backdated.
  For group scope, ticker is NULL and scope_key identifies the group.
  Keep full scope/provider manifests, candidate denominator diagnostics,
  baseline IDs and flags in the declared JSON fields.
  Target schema and append-only fdi_annotations are in ADOPTION.
  Existing quality_label_t1 remains NULL for new immutable rows; expose
  the latest-known annotation via a derived view, not a row UPDATE.

================================================================================
AF. CFTC COT
================================================================================

AF.1 Report Scope and Market Mapping [E/R/P]

  Primary family = TFF, report_type = FUTURES_ONLY.
  Optional FUTURES_AND_OPTIONS_COMBINED is a separate
  scope and baseline.
  Seed exact market strings/codes:
    SPX/SPY context -> CME E-MINI S&P 500, 13874A
    QQQ context     -> CME NASDAQ MINI, 209742
  Verify code+name+unit from each official release.
  No automatic substitution with consolidated codes
  (13874+, 20974+) or micro contracts.

  COT positions aggregate futures tenors; they are not
  the SPX options dealer book. Four reportable groups are
  dealer/intermediary, asset manager/institutional,
  leveraged funds and other reportables; nonreportable
  is separate. Do not label futures-only minus combined
  as identified option positions. Preserve report_type in
  every output.

AF.2 Fields and Source Validation [E/P]

  Preserve exact source artifact/hash, report family/type, market code,
  position date, parser version and the four reportable groups plus
  nonreportable long/short counts. Use ONE spreading count per reportable
  group: dealer_spreading, asset_manager_spreading,
  leveraged_funds_spreading, other_reportables_spreading.
  Do not create separate spread-long/spread-short measures.
  For the existing FUTURES_ONLY profile require nonnegative position
  counts and OI>0, then reconcile exactly:
    SUM_g(long_g + spreading_g) + nonreportable_long = OI;
    SUM_g(short_g + spreading_g) + nonreportable_short = OI.
  The same spreading count participates once in each side's total;
  net_g remains long_g-short_g. Nonreportable spreading is unavailable,
  not a made-up zero measure. Missing trader-count metadata is NULL,
  not a substitute for position counts. A combined profile needs its
  own explicit rounding/reconciliation policy before activation.
  Invalid rows are quarantined per market/date; do not discard another
  valid market. Schema field meanings must match the pinned source map.

AF.3 Record Identity [P schema patch]

  Logical key
    K = {CFTC, TFF, report_type, market_code,
         as_of_date}
  row_hash hashes canonical business fields, excluding
  fetch clocks and derived percentiles.
  cot_snapshot_id = SHA256(canonical JSON
    [K, row_hash, parser_version]).
  UNIQUE(K, row_hash, parser_version).
  source_hash hashes the exact downloaded artifact;
  store separately.
  revision_number is a local sequence per K, starting at
  0; never claim it is a CFTC-issued revision ID.

  Same artifact/row/parser ingested twice is a no-op.
  New content or a parser repair creates another
  immutable row with supersedes_id and revision_kind.
  A file reverting to an already known old hash is not
  a new latest revision.
  Unexplained conflicting artifacts require review.
  CFTC says it does not routinely backdate historical
  updates; this is a defensive versioning contract, not
  an assumed revision feed.

AF.4 Availability and Selection [P]

  Store source_published_at (nullable, verified only), first_seen_at,
  normalized_at, available_at, historical_available_at (nullable),
  availability_basis, point_in_time_verified and publication_evidence_hash.
  release_at is a nullable compatibility alias of source_published_at,
  not an assumed scheduled time. Update its NOT NULL constraint only
  in AF's approved migration.

  LIVE / local replay:
    available_at=max(first_seen_at, normalized_at,
                     source_published_at when independently verified).
  A report or parser repair cannot be available before this validated
  normalized version actually existed locally. Never backdate local
  availability when an archive downloaded today describes an old date.

  Historical research may separately use historical_available_at only
  with version-specific publication evidence, point_in_time_verified=1
  and an explicitly labelled HISTORICAL_PIT_EVIDENCE evaluation mode.
  Parser repairs discovered later are not inserted into earlier local
  replays. LATEST_REVISED research is NON_POINT_IN_TIME and not a valid
  substitute for an as-known trading backtest.

  For each logical key K, first filter rows by the requested clock and
  cutoff t; then select the highest accepted local revision_number.
  revision_number is allocated atomically per K, never a CFTC-issued ID.
  Reappearance of an old row/parser hash does not make it a new latest
  version. Conflicting source artifacts are quarantined until accepted.
  Preserve source snapshot IDs and selected clock mode in every result.

AF.5 Exact Measures [P]

  For group g:
    N_g           = L_g - S_g
    net_pct_oi    = 100 * N_g / OI
    long_pct      = 100 * L_g / OI
    short_pct     = 100 * S_g / OI
    spread_pct    = 100 * spread_g / OI
    Change_1w     = N_g(t) - N_g(t - 7d)
      (only with the exact earlier report date)
    flow_pct_oi   = 100 * Change_1w / OI(t - 7d)
    Change_4w     = N_g(t) - N_g(t - 28d)
    net_share_change = difference of net_pct_oi values,
      in percentage points.

  If a required endpoint is missing, that delta is NULL;
  optionally show change_since_previous with its exact
  span, never call it weekly. Zero OI invalidates
  ratios. Keep counts and shares together; a ratio change
  alone can be caused by OI shrinking. Do not treat
  changes in classifications, entrants or exits as
  identified trading.

AF.6 Lookback and Version Endpoints [P]

  For report date d and evaluation t:
    H contains the latest available-at-t version of each
    PRIOR date in
      [d - 3 calendar years, d).
  February 29 maps to February 28 when needed.
  Keep most recent 156 distinct weekly dates.
  Same market, TFF type, category, unit and comparable
  classification regime.
  Exclude d, all future dates and unavailable revisions.
  1w/4w endpoints are exact d-7 / d-28, not 1/4 rows
  back.

  n < 52: no percentiles.
  52 <= n <= 103: provisional descriptive percentiles
    only.
  n >= 104: eligible for the optional exceptional-change
    notice.
  156 is the target full sample.
  Missing reports are not forward-filled.
  Save baseline IDs, selection time, n and endpoint range.
  A documented market/category break starts a new
  comparable baseline.

AF.7 Rank, Ties, Normalization [P]

  Use AE midrank PR for net_pct_oi and flow_pct_oi.
  Compare counts exactly; percentage-point measures
  quantized to 1e-6 with half-up rounding.
  z_net = (net_pct_oi - med(H_net))
        / max(1.4826 * MAD(H_net), 0.25pp).
  z_change uses the same formula on historical
  flow_pct_oi.
  4w deltas are ranked only against earlier valid 4w
  deltas. No min-max COT index is silently substituted.

  High/low crowding:
    net-position rank >= 95 / <= 5 with >= 104
    observations. This is a positioning extreme, not a
    trend forecast or reversal signal.
  Store raw z and cap chart labels only to [-5, +5].
  If all past shares equal, ties rank at 50 and the
  0.25pp floor prevents numerical explosions.

AF.8 Exact Release-Calendar Procedure [R/P]

  Use the official, versioned CFTC date list; normal
  scheduled time is 15:30 America/New_York.
  Refresh calendar at startup and 06:00 ET daily; retain
  hash and retrieval time.
  > 7 calendar days without successful refresh =>
  SCHEDULE_UNVERIFIED.
  Fetch at scheduled +2m, +10m, +30m, +60m, then hourly
  until +6h. Respect Retry-After. After that retry
  08:00 ET daily until a verified report or new schedule
  exists.

  No "Friday unless NYSE open" rule: for example, the
  official 2026 list includes April 3, while the equity
  exchange calendar observes Good Friday. Holidays,
  agency delays and exceptional release changes come from
  CFTC notices, not guessed business-day shifts.
  Parse actual as_of_date from report; do not synthesize
  Tuesday. Recheck changed schedules before declaring a
  missing release.

AF.9 Freshness and Delivery Calendar [P]

  A valid latest report is CURRENT until the next
  scheduled release + 60m; next due but absent =>
  DELAYED. At + 6h overdue, or position_date older than
  14 calendar days, mark STALE; an announced delay
  changes the expected deadline but still show actual
  age. Position age > 10 days adds OLD_POSITIONS.
  Unknown/stale schedule prevents exception-based
  freshness claims.

  Display last valid data with its age; do not replace
  with zeros. No exceptional-change push when DELAYED,
  STALE or SCHEDULE_UNVERIFIED. Default commentary
  appears at the first equity-trading-session morning
  brief after availability. A Monday holiday shifts that
  brief to Tuesday. A real report released on a market
  holiday can still be ingested immediately.

AF.10 Useful Output and Optional Alert [E/P]

  Default: one compact Monday/next-session section for
  SPX/SPY and QQQ with all groups, 1w/4w changes, net
  shares and ranks.

  Optional weekly-positioning-update (RESEARCH, ack=0)
  only for fresh new reports:
    n >= 104
    AND abs(flow_pct_oi) >= 2pp
    AND (change-rank >= 95 OR <= 5).
  One combined notice per release; ordinary releases
  stay in the newsletter.
  Revisions are correction notices, not fresh
  directional signals.

  Example:
    "ES futures: leveraged funds remain net short, but
     net shorts reduced by 10k (+2pp prior OI); asset
     managers reduced longs. Positions dated Tuesday;
     published Friday. Mixed weekly backdrop; require
     live flow and price confirmation."
  No universal smart-money score, automatic contrarian
  trade, or probability upgrade.

AF.11 Persistence and Acceptance [P]

  Raw snapshot logical key K=(CFTC,TFF,report_type,market_code,as_of_date).
  cot_snapshot_id=SHA256(canonical JSON [K,normalized_row_hash,parser_version]).
  Enforce UNIQUE(K,normalized_row_hash,parser_version) and UNIQUE(K,
  revision_number). Source artifact hash remains a separate field.
  Never mutate accepted source counts. A parser repair is a new version
  with supersedes_id, revision_kind, new normalized_at and available_at.

  ONE category per cot_analytics row:
    DEALER, ASSET_MANAGER, LEVERAGED_FUNDS, OTHER_REPORTABLES,
    NONREPORTABLE.
  analytics_id=SHA256(canonical JSON [cot_snapshot_id,category,
    method_version,baseline_manifest_hash,evaluation_clock_mode,as_of]).
  category is required in both identity and storage. Store net/count
  changes and percentage-point measures, exact 1w/4w endpoint IDs,
  baseline IDs and separate valid sample counts for each measure.
  rank_net/rank_change are DOUBLE in [0,100], preserving fractional
  midranks. n<52 -> unavailable ranks; 52-103 descriptive only;
  exceptional-change notices need n>=104 for their change baseline.
  percentiles_json is deprecated raw-row storage for new results; use
  cot_analytics, not UPDATE of an old report's raw counts.

  Keep AF.8's official CFTC schedule, AF.9's delayed/stale policy and
  AF.10's separately adopted RESEARCH notice. No COT-only trade gate.
  Acceptance: all five categories coexist for one snapshot; fractional
  rank survives storage; exact date endpoints; no current-date baseline;
  one spreading count per group reconciles both sides; duplicate and
  reverted hashes; parser repairs; holiday release; unknown publication;
  a local download today is unavailable to yesterday's local replay.

================================================================================
AG. LEVERAGED ETF PRESSURE
================================================================================

AG.1 Exact Benchmark Registry [R/P]

  Seed mappings verified from issuers:
    SOXL +3 and SOXS -3 -> NYSE Semiconductor Index
      (ICESEMIT)
    TQQQ +3 and SQQQ -3 -> Nasdaq-100 Index
    optional SPXL +3 and SPXS -3 -> S&P 500 Index
  Registry stores fund, benchmark_id, licensed-feed
  series_id, return_variant, leverage, effective_from/to
  and issuer-document hash.

  Use the exact published benchmark series used by the
  issuer, including its price/total-return variant;
  validate vendor binding before enabling.
  A provider symbol is configuration, not an inferred
  alias. SOXX/QQQ/SPY share prices are proxies, not
  silently interchangeable with index levels.
  No current mapping is backfilled into dates before its
  documented effective range.

AG.2 Mandatory Observation Clocks [P]

  d0 = previous exchange trading session.
  A0 = issuer total net assets at d0 close;
  alternatively NAV_d0 * shares_outstanding_d0 from the
  SAME date and split basis.
  Both must have been available by evaluation.
  r_b(t) = b(t) / b(d0 close) - 1 on the same benchmark
  series. This is a SIMPLE return fraction: 0.01 means +1%.
  Do not pass ln(price_ratio), percentage-point values or the ETF's
  own leveraged return into H=A0*L*(L-1)*r_b(t).

  Prior official closing level and current authorized
  index observation are mandatory; current age <= 60s,
  no delayed feed masquerading as live.

  Exact previous-session AUM is required for a
  publishable intraday estimate; a long weekend is not
  automatically stale. Missing that date => unavailable,
  not AUM carried forward indefinitely.
  Daily FINAL uses the official closing index level.
  Seed evaluation: C-30m then every 5m through C; index
  finalization verified after close.
  Calendar, mapping or corporate-action uncertainty
  blocks publication.

AG.3 No-Fund-Flow Derivation [R; explicit assumptions]

  Let A0 be prior-close dollars, L signed daily leverage
  and r the simple benchmark return.
    Prior exposure before rebalance
      E_minus = L * A0 * (1 + r)
    NAV before rebalance
      A_t = A0 * (1 + L * r)
    Target exposure
      E_target = L * A_t
    Therefore
      H = E_target - E_minus
        = A0 * L * (L - 1) * r
  Positive H = buy/increase benchmark exposure;
  negative H = sell/decrease exposure.

  Assumptions: daily leverage reset, no investor net
  flow, no fees/financing/dividend mismatch, no intraday
  reset and linear benchmark exposure.
  r = 0.01 means 1%, not 1.
  Reject A0 <= 0, nonfinite inputs or 1 + L*r <= 0.
  Fund subscriptions, prior intraday hedges and
  counterparties can change actual remaining close
  demand.

AG.4 Correct Sign Examples [calculated]

  For A0 = $1bn and r = +1%:
    L = +3 -> H = $60m
    L = -3 -> H = $120m
    Combined same-benchmark pair -> +$180m, NOT -$60m
  At -1%, values reverse.
  H / A0 = L * (L - 1) * r; sensitivity to +1% benchmark
  move is 0.01 * A0 * L * (L - 1).
  Dollar input AUM already includes no leverage
  multiplication.
  For L = +1, H = 0 under this price-only model.
  For L = -1, coefficient = 2.
  These tests catch the common L*r*A0 error and
  subtraction of inverse-fund demand.
  Do not use a fund's own leveraged return as r; that
  applies leverage twice.
  Exposure notional is not a prediction of executed
  closing-auction dollars.

AG.5 Fund Flows and Optional Observations [P]

  V1 always records fund_flows_excluded = true; today's
  share change, ETF trading volume, NAV premium/discount
  and dealer gamma are diagnostics only.
  Volume is not creation/redemption.
  A separate V2 may use
    H = A0 * L * (L - 1) * r + L * F
  when F is externally verified net subscriptions
  received as uninvested cash immediately before reset;
  other flow timing requires a different model.

  Do not replace unknown F with an assertion that actual
  net flows were zero.
  For display-only shares_change, adjust both dates to
  one split basis first. NAV changes and reverse splits
  are not creations.
  V1 formula/version is frozen in every result. V2 is
  disabled here; it cannot be selected silently by a
  coding agent.

AG.6 Group Aggregation and Scale [P]

  For one benchmark b:
    H_b = SUM_i H_i over the enabled fund universe.
  Require all enabled pair members for a complete group.
  Cross-benchmark figures are not naively added.
  With known point-in-time constituent weights, stock
  allocation is:
    h_j = SUM_b w_jb * H_b.
  V20_close = mean over prior 20 complete sessions of
    SUM_j(close_window_shares_j * VWAP_j),
    using constituent universe/weights known then.
  pressure_ratio = abs(H_b) / V20_close.

  Optional pressure_ratio needs all component coverage;
  otherwise NULL. It is an exposure-to-cash-volume
  scale, not predicted participation. No dollar "index
  trading volume" exists to insert directly. Missing a
  fund yields PARTIAL_SCOPE with valid subtotal, never
  a complete total. Avoid adding this mechanical
  estimate to dealer-flow dollars; the hedging channels
  may overlap.

AG.7 Mandatory Gates and Confidence [P]

  Mandatory:
    valid daily-reset mapping;
    exact prior-session A0;
    prior and current same-series index levels;
    calendar;
    source available;
    at <= evaluation;
    finite r;
    no unresolved split/NAV discrepancy.

  q_A = 1.00 for issuer AUM, 0.90 for same-date
        NAV * shares.
  q_B = 1 at age <= 15s, else 1 - 0.2 * ((age - 15) /
        45) until 60s, > 60s = 0.
  q_R = 1 after exact schema/calendar/lineage checks,
        else 0.
  input_confidence = min(q_A, q_B, q_R).
  Any mandatory failure => H = NULL and confidence = 0.
  If all declared funds have mandatory inputs, group confidence is the
  minimum constituent confidence and H_b is the full subtotal.
  If any declared fund is missing, scope_status=PARTIAL_SCOPE: report
  a valid observed subtotal only, with confidence capped at 0.50,
  and block the standalone watch. Never claim the missing demand is 0.
  These are data-quality scores, not probabilities of flow or direction.
  Missing dealer gamma removes that commentary, not the base H estimate.

AG.8 Optional Ages and Comparison [P]

  Underlying dealer context must be same-session and
  within its existing lane TTL; otherwise label stale
  and do not use it to confirm.
  Shares-change diagnostic must refer to two consecutive
  known issuer dates.
  Require issuer_AUM>0 and same-date/split-basis NAV and shares.
  discrepancy = abs(issuer_AUM - NAV * shares) / issuer_AUM.
  discrepancy > 0.02 -> discrepancy flag;
  discrepancy >= 0.05 -> unresolved; block until reconciled.
  Matching AUM and NAV*shares must produce exactly zero discrepancy.
  Missing comparison inputs -> comparison unavailable, not zero;
  the base model still follows its declared mandatory AUM policy.
  Official mapping revalidated weekly and on announced
  changes.

  An exact benchmark never downgrades to a proxy
  automatically. Counterfactual proxy calculations may
  be saved separately as PROXY_RESEARCH with
  confidence <= 0.50 and no push.
  Final return must use official close, not
  last-after-hours trade.
  Missing source timestamps do not qualify as fresh.

AG.9 Two Persistence Roles and Primary Keys [P schema patch]

  Daily table leveraged_etf_pressure retains PK(snapshot_date,etf_ticker)
  for ONE immutable as-published FUND final, from the version frozen
  before open. Add observation_id referencing the chosen fund snapshot.
  Do not insert benchmark groups into etf_ticker as pseudo-symbols.

  leveraged_etf_pressure_observations supports scope_kind FUND or
  BENCHMARK_GROUP; scope_key pins the fund/group universe and mapping.
  benchmark_group_id is present for both; etf_ticker is present ONLY
  for FUND. GROUP rows carry member_fund_observation_ids_json.
  phase is one of PRE_CLOSE,UPDATE,FINAL,REVISION; as_of is a separate
  epoch-ms field, not a combined as_of_phase string.
  observation_id=SHA256(canonical JSON [session_date,scope_kind,scope_key,
    as_of,phase,calculation_version,input_manifest_hash]).
  Record input_manifest_json, available_at, mapping version, status,
  quality flags, baseline IDs, source observations and supersedes_id.
  Same exact inputs -> no extra row; different as_of/version -> new row.

  Intraday/group/revision rows live only in observations. Select the
  first validated official FUND final after close+30m; if no valid
  input by close+4h, publish a declared INSUFFICIENT_DATA fund-day row
  with NULL H, not zero. Only funds in the predeclared valid registry
  are in the daily-final obligation. A later correction is a REVISION;
  never rewrite as-published history. A corrected view is separate.
  Existing calculation_version already exists in the daily table;
  migration 045 must not ADD it a second time.

AG.10 Baselines and Default Report [P]

  Use 60 prior eligible same-time/session-type
  observations within 90 sessions for abs(H_b), same
  fund universe/mapping/calculation version; minimum
  20, provisional below 60.
  Midrank PR(abs(H_b), H_abs) uses the AE tie policy.
  FINAL compares only to FINAL.
  Freeze chosen model version daily; replay uses
  available_at selection.
  Report H, rank, AUM date, benchmark return, quality
  and no-fund-flow assumption.

  Default output is newsletter/ad-hoc context, not a
  standalone trade.
  FINAL is retrospective; it cannot forecast the close
  that already happened.
  Intraday wording:
    "If the benchmark closes near +1%, the price-only modelled
     reset is +$180m of exposure; actual remaining orders are unknown,"
    never "funds must buy $180m at 15:59."

AG.11 Scenario Formulas [P]

  For an assumed final daily benchmark return
  r_close_scenario:
    scenario_reset_usd
      = K_b * r_close_scenario
    scenario_change_from_now_usd
      = K_b * (r_close_scenario - r_b(t))

  An assumed additional return s from the CURRENT price
  must first be converted:
    r_close_scenario = (1 + r_b(t)) * (1 + s) - 1
  Do not incorrectly add simple returns for a precise
  implementation.

  15-minute comparison:
    both endpoints must use the SAME AUM date/version,
    fund universe, benchmark mapping and calculation
    version. A change in those inputs produces
    INPUT_REVISION, not a market-pressure acceleration
    signal. Missing endpoint => NULL, not zero.

  Label all scenario outputs conditional, not predictions
  or confidence intervals.

AG.12 Optional Closing Rebalance Watch [P]

  New closing-rebalance-watch is RESEARCH / ack=0, off
  until adopted.
  Evaluate only C-30m through C-5m.
  Require complete fund scope, confidence >= 0.80,
  n >= 20, abs(H) rank >= 95.0, pressure_ratio >= 0.01
  and same sign across 3 consecutive 5m observations.
  Without constituent-volume data, retain report context
  but do not issue this standalone watch.

  Combine with AE into one closing brief when both pass.
  A separate condition plan additionally needs an
  existing live-flow thesis and independent fresh
  price/map confirmation, then all current decision
  gates.
  Alert example:
    "NDX modelled buy pressure is unusually large;
     live bullish flow agrees. Watch the confirmed map
     level; no trade if it fails."
  No extra confidence points without forward validation.

AG.13 Timing and Research Notifications

  C is the versioned official close for the selected
  benchmark session.
  Early monitoring every five minutes from C-180m is a
  PROPOSED research extension. For a normal 16:00 New
  York close it starts at 13:00 New York. Short sessions
  use the close-relative schedule, not hard-coded
  afternoon wall-clock times.

  Early observations use the existing UPDATE observation
  phase plus monitoring_stage = EARLY_SHADOW; existing
  PRE_CLOSE and FINAL semantics remain intact.
  Do not borrow a C-30m percentile distribution for
  C-180m. Each baseline uses compatible time-to-close,
  session type, universe, AUM vintage rules and formula
  version.

  Annotations:
    PRESSURE_WATCH       existing AG quality, completeness,
                         percentile, liquidity and
                         persistence gates pass.
                         Unusually large modelled reset.
                         Watch only; no independent trade
                         authorization.
    PRICE_CONFIRMED      existing qualified flow thesis
                         and existing price/level
                         confirmation agree; map is fresh
                         and basis-compatible. A separate
                         conditional plan may cite the
                         already-approved map
                         target/invalidation. All normal
                         decision gates remain required.
    PRESSURE_FADING      material decline in same-direction
                         H after a watch. Proposed
                         materiality seed: > 50% decline
                         from the post-watch peak absolute
                         H with the sign unchanged,
                         present at two consecutive
                         5-minute evaluations. Seed is
                         unvalidated and versioned.
                         Report fading buying/selling,
                         not automatically the opposite
                         direction.
    SETUP_INVALIDATED    previously issued plan's existing
                         price invalidation fires, or H
                         crosses to the opposite sign on
                         two consecutive evaluations.
                         Immediately communicate a
                         verified price invalidation;
                         sign-change-only trigger uses
                         its persistence rule. Invalidate
                         the previous context, not
                         automatically reverse the trade.

  No new entry watch after C-5m by default; continue
  cancellation/risk messages and FINAL accounting.
  Each material transition is idempotent using
  (session, benchmark_group, episode_id, annotation,
  transition_id, ruleset_version). Routine
  recalculations do not send new messages. Coalesce
  benchmark notices where practical, but do not suppress
  distinct valid symbols merely to meet a fixed daily
  alert quota.

  Domain: RESEARCH; requires_ack = 0.
  A true provider/system fault uses the existing SYSTEM
  policy.
  Exit recommendations remain owned by AH and do not
  treat an acknowledgment as an execution.

AG.14 Use in All Three Workflows

  Morning:
    show reset sensitivity to benchmark scenarios such as
    +/-0.5% and +/-1%, current verified AUM vintage, and
    a clearly dated recap of yesterday. Do not present
    yesterday's completed reset as today's unfilled
    flow.
  Intraday flow:
    attach group context to an existing allowed equity
    thesis. Preserve ordinary ETF/index FLOW_ALERT
    filters. A separate research pressure notice does
    not bypass the instrument filter for trade alerts.
  Ad hoc:
    show H, its 15-minute change, sensitivities, input
    quality, liquidity scale, conditional price map and
    unknown execution/crowding status.
  Closing brief:
    combine AG and AE when both pass their own gates.
    Early monitoring must not pretend the final Closing
    FDI window has already occurred.

AG.15 Validation and Minimum Build

  Within one benchmark and frozen session inputs, H is
  exactly K times the day's return. Its sign therefore is
  NOT independent price confirmation. A model that
  awards points for H > 0 and price return > 0 risks
  counting the same information twice.

  Before using the overlay to improve decisions, compare
  chronological held-out performance against a baseline
  that already contains cumulative return, recent
  momentum, realized volatility, time-to-close,
  liquidity and event context. Test the incremental
  contribution of K, constituent exposure concentration
  and liquidity-normalized H. Use only information
  available at the cutoff; do not use today's final
  AUM/shares/holdings in an afternoon replay. Measure
  after-cost outcomes at equal alert volume and report
  sessions in which the context failed.

  Minimum implementation adds no ML or new mandatory
  paid feed: one registry expansion, local K/H
  calculations, five-minute observations, diagnostic
  payload fields, and versioned research annotations.
  Optional constituent mapping or auction data can
  follow later.

  Acceptance cases:
    1. +3 and -3 coefficients and signs at
       positive/negative returns.
    2. Current-AUM substitution rejected; prior-close
       dollars are not levered twice.
    3. 15-minute delta uses identical input versions;
       revision classified separately.
    4. Repeated five-minute H values never accumulate
       into executed-flow volume.
    5. Shrinking positive H remains buying-pressure-
       fading, not selling.
    6. Return scenario conversion includes the cross
       term.
    7. Next-day zero return yields zero price-only reset
       despite yesterday's rally.
    8. Early cutoffs use early-cutoff history;
       half-days use close-relative clocks.
    9. A missing inverse fund is a partial-scope
       subtotal, never a complete group.
   10. Correlated benchmarks remain separate; stock-
       level allocations are not added back to their
       parent totals.
   11. No unknown execution fraction, trader identity
       or auction evidence is fabricated.
   12. Old FINAL rows remain immutable; new
       calculations/corrections go to observations.

AG.16 Synthetic Example

  Prior-close AUM: $20bn for a +3 fund and $5bn for a
  -3 fund on the SAME benchmark.
  K = 20bn * 6 + 5bn * 12 = 180bn.

    Daily benchmark return    Modelled reset
    +0.60%                    +$1.08bn
    +1.00%                    +$1.80bn
    +0.40%                    +$0.72bn
     0.00%                     $0
    -0.20%                    -$0.36bn

  A change from +0.60% to +1.00% increases the modelled
  reset by $720m.
  A retreat from +1.00% to +0.40% shrinks it by $1.08bn,
  but the remaining model output is still a BUY estimate.
  A negative change in H is not automatically a SELL
  estimate.
  None of these amounts proves unexecuted orders.

AG.17 Observation and Interpretation Policy

  Price-only reset H:
    Publish subject to existing mandatory input-quality
    gates; label MODELLED_RESET_NO_FUND_FLOW.
  Actual outstanding rebalance demand:
    NULL / UNKNOWN without authenticated
    position/execution information. Do not assume every
    fund waits until the close.
  Already-executed fraction:
    NULL / UNKNOWN; no invented 30%, 50% or other
    adjustment.
  Anticipatory positioning:
    Unobserved; price momentum is not proof of who traded
    or why.
  Market overextension:
    Optional observable proxy based on price versus
    VWAP/AVWAP and historical same-time distance; label
    PRICE_EXTENDED, never FRONT_RUNNING_CONFIRMED. Use
    only basis-compatible data.
  Optional closing-auction imbalance:
    Separate licensed venue-level evidence. It does not
    identify LETF-origin orders or capture all derivative
    hedging channels. Missing feed => UNAVAILABLE, with
    no fabricated proxy.
  Dealer gamma/vanna:
    Keep the existing fresh-map interpretation alongside
    H. Do not add dealer hedge notional to H because
    channels may overlap.
  Next-session pressure:
    Reinitialize from the new reset point and AUM.
    Yesterday's positive H does not persist as today's
    required buying.

  Verified net investor cash flow F can be represented by
  H_adjusted = H + L*F only under the explicitly modeled
  end-of-period uninvested-cash assumption.
  Other cash-flow timing, in-kind transfers, derivative
  resets and prior hedging require a different
  exposure-accounting model. Keep the existing V2
  fund-flow extension disabled until supported by data.

AG.18 Safe Failure, Tests, No Double Counting [P]

  Calculation runs locally from cached inputs; fresh
  official reads are budgeted.
  Missing/expired mandatory input => store unavailable
  result and reason, not H = 0.
  No provider fallback outside mapped universe.
  Calculation failure leaves other queue workflows
  running.
  Compare model forecasts with subsequent official.

  Tests:
    +/-3 at +1 / -1%;
    L = 1;
    zero/negative AUM;
    percent-vs-fraction error;
    split leaves AUM unchanged;
    Monday uses Friday correctly;
    holiday;
    missing exposure;
    actual remaining trades unknown;
    no double counting;
    no intraday ID;
    two calculation versions;
    inverse fund;
    future AUM;
    stale index;
    no automatic FLOW_ALERT or dealer-flow dollar
    addition.

  Required schema decision:
    the daily table is immutable as-published, the new
    observations table carries all intraday values and
    later corrections. There is no ambiguous upsert
    policy.

================================================================================
ADOPTION
================================================================================

  AE/AF/AG remain separately gated research modules. Editing this draft
  does not adopt them. Each adoption records module, method/config hash,
  approved_by, approved_at, exact target DDL and migration hashes.
  Calculation/report-context permission and push-notification permission
  are separate flags. AE remains NO_NEW_ALERTS. AF/AG push is disabled
  until explicitly adopted. None can override the core decision gates.

  Registry:
    DuckDB 043_ae_closing_fdi.sql       -- AE only, optional
    DuckDB 044_af_cot_context.sql       -- AF only, optional
    DuckDB 045_ag_leveraged_pressure.sql -- AG only, optional
  Each depends on its real baseline/core prerequisites, NOT on the
  other research modules. Pending IDs are chosen by the applied-ID SET,
  never by MAX(id). Core DuckDB 050 does not mark 043-045 as installed.
  Proposed SQLite 071 is core AH repair; 072-079 remain reserved.
  DuckDB 046-049 remain reserved for future extensions.

  On adoption only: move that module's approved final CREATE definitions
  below into SPEC Vol 2, mirror relevant definitions in ARCH Vol 2,
  register the real migration, update constants/policy registries and
  regenerate source packets. Do not execute these full CREATE targets
  as if they were ALTER migrations against populated existing tables.
  Changes to nullability, constraints, keys or existing columns need a
  reviewed rebuild/backfill plan for the pinned database engine.
  Missing legacy scope, availability, baseline, identity or source
  evidence cannot be filled with invented values. Stop the adoption
  migration and preserve the original tables/evidence until the operator
  explicitly reconciles/quarantines the affected records.
  Existing daily calculation_version must NOT be added again.

  New columns/constraints below are PROPOSED completion of R01-R04,
  not claims that this DDL was already present or approved.

AE TARGET SCHEMA -- after adoption 043 only

CREATE TABLE closing_fdi_snapshots (
    fdi_snapshot_id TEXT PRIMARY KEY,
    snapshot_date DATE NOT NULL,
    ticker TEXT,
    scope_key TEXT NOT NULL,
    scope_manifest_json TEXT NOT NULL,
    provider_manifest_json TEXT NOT NULL,
    session_id TEXT,
    window_start BIGINT NOT NULL,
    window_end BIGINT NOT NULL,
    u_cutoff_ts BIGINT NOT NULL,
    c_close_ts BIGINT NOT NULL,
    session_type TEXT NOT NULL,
    minutes_to_close INTEGER NOT NULL,
    calculation_phase TEXT NOT NULL CHECK(calculation_phase IN
        ('PRE_CLOSE','UPDATE','FINAL')),
    fdi_raw DOUBLE,
    bull_delta_dollars DOUBLE,
    bear_delta_dollars DOUBLE,
    gross_delta_dollars DOUBLE,
    fdi_norm DOUBLE,
    symbol_breadth DOUBLE,
    sector_breadth DOUBLE,
    flow_intensity_percentile DOUBLE,
    same_time_historical_percentile DOUBLE,
    coverage_pct DOUBLE,
    signable_count_ratio DOUBLE,
    signable_premium_ratio DOUBLE,
    largest_share DOUBLE,
    active_symbol_count INTEGER,
    active_sector_count INTEGER,
    independent_event_count INTEGER,
    candidate_count INTEGER,
    candidate_premium_cents BIGINT,
    used_premium_cents BIGINT,
    package_netted_count INTEGER,
    persistence_duration_s INTEGER,
    classification_version TEXT NOT NULL,
    calculation_version TEXT NOT NULL,
    ruleset_version TEXT NOT NULL,
    feature_version TEXT NOT NULL,
    input_manifest_hash TEXT NOT NULL,
    input_manifest_json TEXT NOT NULL,
    baseline_ids_json TEXT NOT NULL,
    baseline_n INTEGER NOT NULL,
    baseline_cutoff BIGINT NOT NULL,
    diagnostics_json TEXT NOT NULL,
    quality_label_t1 TEXT,
    source_versions TEXT,
    supersedes_id TEXT,
    correction_reason TEXT,
    calculated_at BIGINT NOT NULL,
    available_at BIGINT NOT NULL,
    created_at BIGINT NOT NULL,
    CHECK(window_end - window_start = 1800000),
    CHECK(window_end = u_cutoff_ts),
    CHECK(calculated_at >= window_end AND available_at >= calculated_at)
);
CREATE INDEX idx_fdi_scope_cutoff
    ON closing_fdi_snapshots(scope_key,snapshot_date,window_end);
CREATE INDEX idx_fdi_date_ticker
    ON closing_fdi_snapshots(snapshot_date,ticker,calculation_phase);
CREATE TABLE fdi_annotations (
    annotation_id TEXT PRIMARY KEY,
    fdi_snapshot_id TEXT NOT NULL,
    known_at BIGINT NOT NULL,
    method_version TEXT NOT NULL,
    label TEXT NOT NULL,
    evidence_hash TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    supersedes_id TEXT,
    FOREIGN KEY(fdi_snapshot_id) REFERENCES closing_fdi_snapshots(fdi_snapshot_id)
);
CREATE INDEX idx_fdi_annotation_known
    ON fdi_annotations(fdi_snapshot_id,known_at);

AF TARGET SCHEMA -- after adoption 044 only

CREATE TABLE cot_snapshots (
    cot_snapshot_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL CHECK(source_id='CFTC'),
    report_family TEXT NOT NULL CHECK(report_family='TFF'),
    report_type TEXT NOT NULL CHECK(report_type IN
        ('FUTURES_ONLY','FUTURES_AND_OPTIONS_COMBINED')),
    market_code TEXT NOT NULL,
    as_of_date DATE NOT NULL,
    release_at BIGINT,
    source_published_at BIGINT,
    first_seen_at BIGINT NOT NULL,
    normalized_at BIGINT NOT NULL,
    available_at BIGINT NOT NULL,
    historical_available_at BIGINT,
    availability_basis TEXT NOT NULL,
    point_in_time_verified INTEGER NOT NULL CHECK(point_in_time_verified IN (0,1)),
    publication_evidence_hash TEXT,
    revision_number INTEGER NOT NULL CHECK(revision_number >= 0),
    revision_kind TEXT,
    supersedes_id TEXT,
    dealer_long BIGINT NOT NULL CHECK(dealer_long>=0),
    dealer_short BIGINT NOT NULL CHECK(dealer_short>=0),
    dealer_spreading BIGINT NOT NULL CHECK(dealer_spreading>=0),
    asset_manager_long BIGINT NOT NULL CHECK(asset_manager_long>=0),
    asset_manager_short BIGINT NOT NULL CHECK(asset_manager_short>=0),
    asset_manager_spreading BIGINT NOT NULL CHECK(asset_manager_spreading>=0),
    leveraged_funds_long BIGINT NOT NULL CHECK(leveraged_funds_long>=0),
    leveraged_funds_short BIGINT NOT NULL CHECK(leveraged_funds_short>=0),
    leveraged_funds_spreading BIGINT NOT NULL CHECK(leveraged_funds_spreading>=0),
    other_reportables_long BIGINT NOT NULL CHECK(other_reportables_long>=0),
    other_reportables_short BIGINT NOT NULL CHECK(other_reportables_short>=0),
    other_reportables_spreading BIGINT NOT NULL CHECK(other_reportables_spreading>=0),
    nonreportable_long BIGINT NOT NULL CHECK(nonreportable_long>=0),
    nonreportable_short BIGINT NOT NULL CHECK(nonreportable_short>=0),
    open_interest BIGINT NOT NULL CHECK(open_interest>0),
    percentiles_json TEXT,
    source_hash TEXT NOT NULL,
    normalized_row_hash TEXT NOT NULL,
    parser_version TEXT NOT NULL,
    created_at BIGINT NOT NULL,
    UNIQUE(source_id,report_family,report_type,market_code,as_of_date,
           normalized_row_hash,parser_version),
    UNIQUE(source_id,report_family,report_type,market_code,as_of_date,revision_number),
    CHECK(available_at >= first_seen_at AND available_at >= normalized_at),
    CHECK((release_at IS NULL AND source_published_at IS NULL) OR
          (release_at IS NOT NULL AND source_published_at IS NOT NULL
           AND release_at=source_published_at)),
    CHECK(historical_available_at IS NULL OR
          (point_in_time_verified=1 AND publication_evidence_hash IS NOT NULL))
);
CREATE INDEX idx_cot_market_date ON cot_snapshots(market_code,as_of_date);
CREATE INDEX idx_cot_available ON cot_snapshots(available_at);
CREATE TABLE cot_analytics (
    analytics_id TEXT PRIMARY KEY,
    snapshot_id TEXT NOT NULL,
    category TEXT NOT NULL CHECK(category IN
        ('DEALER','ASSET_MANAGER','LEVERAGED_FUNDS','OTHER_REPORTABLES','NONREPORTABLE')),
    method_version TEXT NOT NULL,
    baseline_manifest_hash TEXT NOT NULL,
    baseline_ids_json TEXT NOT NULL,
    evaluation_clock_mode TEXT NOT NULL CHECK(evaluation_clock_mode IN
        ('LOCAL_AS_KNOWN','HISTORICAL_PIT_EVIDENCE','LATEST_REVISED')),
    as_of BIGINT NOT NULL,
    net_contracts BIGINT,
    change_1w_contracts BIGINT,
    change_4w_contracts BIGINT,
    endpoint_1w_snapshot_id TEXT,
    endpoint_4w_snapshot_id TEXT,
    net_pct_oi DOUBLE,
    long_pct_oi DOUBLE,
    short_pct_oi DOUBLE,
    spread_pct_oi DOUBLE,
    flow_pct_oi DOUBLE,
    net_share_change_pp DOUBLE,
    z_net DOUBLE,
    z_change DOUBLE,
    rank_net DOUBLE CHECK(rank_net BETWEEN 0 AND 100),
    rank_change DOUBLE CHECK(rank_change BETWEEN 0 AND 100),
    rank_4w DOUBLE CHECK(rank_4w BETWEEN 0 AND 100),
    baseline_n_net INTEGER NOT NULL,
    baseline_n_change INTEGER NOT NULL,
    baseline_n_4w INTEGER NOT NULL,
    crowding_signal TEXT,
    created_at BIGINT NOT NULL,
    FOREIGN KEY(snapshot_id) REFERENCES cot_snapshots(cot_snapshot_id),
    UNIQUE(snapshot_id,category,method_version,baseline_manifest_hash,
           evaluation_clock_mode,as_of)
);
CREATE INDEX idx_cot_analytics_snapshot ON cot_analytics(snapshot_id,category,as_of);

AG TARGET SCHEMA -- after adoption 045 only

CREATE TABLE leveraged_etf_registry (
    registry_id TEXT PRIMARY KEY,
    etf_ticker TEXT NOT NULL,
    benchmark_id TEXT NOT NULL,
    licensed_feed_series_id TEXT NOT NULL,
    return_variant TEXT NOT NULL,
    signed_leverage INTEGER NOT NULL,
    effective_from DATE NOT NULL,
    effective_to DATE,
    issuer_document_hash TEXT NOT NULL,
    created_at BIGINT NOT NULL,
    CHECK(effective_to IS NULL OR effective_to>effective_from)
);
CREATE TABLE leveraged_etf_pressure_observations (
    observation_id TEXT PRIMARY KEY,
    session_date DATE NOT NULL,
    scope_kind TEXT NOT NULL CHECK(scope_kind IN ('FUND','BENCHMARK_GROUP')),
    scope_key TEXT NOT NULL,
    etf_ticker TEXT,
    benchmark_group_id TEXT NOT NULL,
    member_fund_observation_ids_json TEXT,
    phase TEXT NOT NULL CHECK(phase IN ('PRE_CLOSE','UPDATE','FINAL','REVISION')),
    monitoring_stage TEXT,
    as_of BIGINT NOT NULL,
    H_usd DOUBLE,
    K_b DOUBLE,
    benchmark_return_fraction DOUBLE,
    pressure_ratio DOUBLE,
    pressure_percentile DOUBLE CHECK(pressure_percentile BETWEEN 0 AND 100),
    input_confidence DOUBLE CHECK(input_confidence BETWEEN 0 AND 1),
    scope_status TEXT NOT NULL CHECK(scope_status IN
        ('COMPLETE','PARTIAL_SCOPE','INSUFFICIENT_DATA','PROXY_RESEARCH')),
    fund_flows_excluded INTEGER NOT NULL CHECK(fund_flows_excluded=1),
    quality_flags TEXT NOT NULL,
    supersedes_id TEXT,
    benchmark_mapping_version TEXT NOT NULL,
    calculation_version TEXT NOT NULL,
    input_manifest_hash TEXT NOT NULL,
    input_manifest_json TEXT NOT NULL,
    baseline_ids_json TEXT NOT NULL,
    available_at BIGINT NOT NULL,
    created_at BIGINT NOT NULL,
    CHECK(available_at >= as_of),
    CHECK((scope_kind='FUND' AND etf_ticker IS NOT NULL)
       OR (scope_kind='BENCHMARK_GROUP' AND etf_ticker IS NULL
           AND member_fund_observation_ids_json IS NOT NULL)),
    UNIQUE(session_date,scope_kind,scope_key,as_of,phase,
           calculation_version,input_manifest_hash)
);
CREATE INDEX idx_letf_obs_scope_time
    ON leveraged_etf_pressure_observations(scope_key,as_of);
CREATE TABLE leveraged_etf_pressure (
    snapshot_date DATE NOT NULL,
    etf_ticker TEXT NOT NULL,
    underlying_ticker TEXT NOT NULL,
    leverage_multiple REAL NOT NULL,
    benchmark_return DOUBLE,
    aum_estimate DOUBLE,
    aum_as_of BIGINT,
    nav_source TEXT,
    shares_change BIGINT,
    estimated_rebalance_flow_dollars DOUBLE,
    flow_direction TEXT,
    underlying_dealer_gamma DOUBLE,
    confidence DOUBLE,
    calculation_version TEXT NOT NULL,
    coverage_flags TEXT,
    source_versions TEXT,
    observation_id TEXT NOT NULL,
    benchmark_id TEXT NOT NULL,
    K_b DOUBLE,
    pressure_ratio DOUBLE,
    pressure_percentile DOUBLE CHECK(pressure_percentile BETWEEN 0 AND 100),
    input_confidence DOUBLE CHECK(input_confidence BETWEEN 0 AND 1),
    quality_flags TEXT,
    created_at BIGINT NOT NULL,
    PRIMARY KEY(snapshot_date,etf_ticker),
    FOREIGN KEY(observation_id)
        REFERENCES leveraged_etf_pressure_observations(observation_id)
);

  Application-level invariants supplement the DDL:
    AE scope/provider/baseline manifests are canonical and fully retained;
    as-of annotation queries never include future known_at;
    AF accepted revisions increase once per K, source counts reconcile,
    categories and exact date endpoints do not silently substitute;
    AG registry effective intervals do not overlap per fund, group rows
    refer only to compatible same-cutoff FUND observations, daily final
    points to a FUND/FINAL or declared unavailable final for the same day;
    partial scopes never claim zero missing demand or full confidence.
  The writer validates these and acceptance tests exercise violations.

  Numerical registry when adopted:
    AE: W=1800s; baseline target=60 within 90 prior sessions; minimum=20;
        direction band=0.20; z floor=0.05 on I; capture/signability=0.90.
    AF: lookback=3 years; minimum percentile=52; eligible notice=104;
        full target=156; MAD floor=0.25pp; percentile high/low=95/5.
    AG: existing confidence gate=0.80; rank gate=95.0 on [0,100];
        pressure_ratio=0.01; same-sign count=3; fading seed=0.50.
  Keep original source-aware calendar rules; these are research choices,
  not calibrated success probabilities. Common PR is a pure utility,
  not a runtime dependency requiring AE adoption before AF or AG.

  Optional notification categories:
    weekly-positioning-update: RESEARCH, requires_ack=0;
    closing-rebalance-watch: RESEARCH, requires_ack=0.
  Adoption inserts these into the existing operator-controlled category
  policy/configuration, not a new SQL enum. Persist adopted config and
  its hash with existing operator audit; no research notification is
  enabled by the presence of a table. No AE category is added here.

  Required migration tests:
    AF adopted before AE, then AE later;
    no adopted modules -> none of their adoption additions automatically
      applied to the existing baseline;
    new and upgraded installations with the same module set match;
    no duplicate calculation_version column;
    fractional ranks round-trip; NULL publication stays unknown;
    a group observation cannot masquerade as a fund final;
    same identity replay is a no-op; corrections append, never overwrite.

================================================================================
APPENDIX — SOURCE REFERENCES
================================================================================

  AE: AE_TECH_V1 technical pack (operator-supplied
      clarification).
  AF:
    R1 CFTC TFF notes
    R2 CFTC release schedule
    R3 COT FAQ
    R4 official TFF market codes
    R10-R11 external calendar
  AG:
    R5-R8 issuer benchmark objectives
    R9 Federal Reserve FEDS 2013-48, Section III,
       rebalancing derivation
    Ivanov and Lenkey, Federal Reserve FEDS 2014-106,
      equations (4)-(6).
    Tuzun, Tuzun, Federal Reserve FEDS 2013-48.
    Julian Oakland, Bank Underground, 2023.
    ProShares TQQQ summary prospectus.
    Direxion SOXL/SOXS official objective.
    Nasdaq Closing Cross FAQ.

================================================================================
END OF SPEC Vol 7 v2.0.5.1
================================================================================