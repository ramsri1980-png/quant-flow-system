# QUANTFLOW — MASTER SESSION RUNBOOK

**Version:** 3.1
**Date updated:** 2026-10-14
**Purpose:** Single authoritative session-by-session execution checklist, fully expanded.
**Mode:** RESEARCH only. No autonomous orders. No ML until E8.
**Design authority:** `SPEC v2.0.5.1` / `ARCH v5.1.5.1` — 11-file release, frozen under `docs/reference/CURRENT`.
**POC source of truth:** `docs/reports/POC-transport-final.md` (tag `poc-transport-complete`).

---

## ENVIRONMENT MATRIX

| Role | Host | OS | Purpose |
|---|---|---|---|
| DEV | Lenovo laptop | Linux Mint 22 (bootable USB) | Authoring, tests, OpenCode, OpenSpec |
| PROD | Second laptop | Ubuntu Server | Runtime: quantd, capture, rhythm, observability |
| DB | SATA attached to PROD | Debian 13 host or Debian 13 container of PROD | `/data` — `quant_state.db` (SQLite WAL) + `quant_flow.duckdb` (DuckDB) |

**Cross-host rule:** SSH/Tailscale only. Never SFTP/SSHFS/NFS-mount a live SQLite file for writes. Only the single runtime owner writes `/data`.

**Locked tech stack** (must match POC — do not "upgrade"):

| Component | Version |
|---|---|
| Python | **3.14** |
| Package/env manager | `uv` (installer script) |
| MCP SDK | `mcp==1.30.0` (Python SDK v1 maintenance line) |
| ASGI | `starlette`, `uvicorn` |
| HTTP client | `httpx` |
| JWT | `PyJWT[crypto]` |
| Data | `duckdb==1.5.6`, `aiosqlite`, `pyarrow`, `polars`, `numpy`, `scipy`, `pandas-market-calendars` |
| Config | `pydantic`, `pydantic-settings` |
| CLI/logging | `typer`, `rich`, `structlog` |
| Serialization | `orjson`, `msgspec` |
| Retry | `tenacity` |
| Testing | `pytest`, `pytest-asyncio`, `pytest-cov`, `hypothesis`, `freezegun`, `respx` |
| Lint/type | `ruff`, `mypy`, `pre-commit` |
| SDD | OpenSpec 1.14.0 |
| Agent | OpenCode 1.18.34 |
| Secrets | Bitwarden Secrets Manager (`bws`) |
| Tunnel | `cloudflared` (Cloudflare apt repo) |

**Pin rule:** never replace `mcp==1.30.0` with unpinned `mcp` or `fastmcp 3.x`.

---

## OVERALL PROGRESS

| Phase | Sessions | Status |
|---|---|---|
| E0 Setup & Foundation | 1–7 | <span style="color:green">✅ Session 1 complete; Session 2 ~70%; POC transport complete</span> |
| E1 Storage & Durability | 8–13 | ⬜ Not started |
| E2 Canonical Event Pipeline | 14–17 | ⬜ Not started |
| E3 Pure Quant Kernels | 18–25 | ⬜ Not started |
| E4 Decision Evidence & Delivery | 26–29 | ⬜ Not started |
| E5 Provider Adapters | 30–35 | ⬜ Not started |
| E6 User Workflows | 36–42 | ⬜ Not started |
| E7 Interface, Ops & Release | 43–48 | ⬜ Not started — transport primitives proven by POC |
| E8 Forward Research | 49+ | ⬜ Not started |

---

## ACTIVITY STATUS DASHBOARD

### Session 1 — Encrypted Storage Foundation — <span style="color:green">✅ COMPLETE</span>

All 20 tasks done: host recorded, SABRENT detected (`152d:1561`), LUKS2 + ext4 (`quantdata`), `/data` mounted `noatime,nodiratime`, GRUB USB quirk, udev autosuspend, `evdi` fixed, group `quantflow` + 3 users, SQLite + DuckDB installed, `dbmount`/`dbunmount`/`dbstatus`, Bitwarden record, LUKS header backup (GPG AES256) uploaded to MEGA + SHA-256 in Bitwarden.

**Key values:** by-id `usb-SABRENT_SABRENT_DB9876543214E-0:0`, LUKS UUID `740ec50d-dbfb-4a59-a226-c13990f9837d`, label `quantdata`.

### Session 2 — Repository, Toolchain, Design Freeze — 🔄 70%

| Task | Activity | Status |
|---|---|---|
| 1 | LUKS header backup | <span style="color:green">✅ done</span> |
| 2 | User reconciliation | <span style="color:green">✅ done</span> |
| 3 | Directory reconciliation | <span style="color:green">✅ done</span> |
| 4 | ADR-001 anti-detection scope | ⬜ pending |
| 5 | Freeze design bundle (11 files) | ⬜ pending |
| 6 | Repo + `.gitignore` first | <span style="color:green">✅ done</span> |
| 7 | Folder structure | <span style="color:green">✅ done</span> |
| 8 | uv + Python 3.14 + foundation deps | ⬜ pending |
| 9 | `pyproject.toml` tool config | ⬜ pending |
| 10 | Commit + tag `foundation-complete` | ⬜ pending |
| 11 | Boot auto-mount | ⏳ deferred |

### POC Transport — <span style="color:green">✅ COMPLETE (2026-10-14, tag `poc-transport-complete`)</span>

All 5 gates pass. Muse → Cloudflare edge → WAF → Tunnel → origin `127.0.0.1:8765` → `X-Api-Key` gate → `hello` tool → back to Muse. Matching `response_id=e7049263-c532-495c-83df-9fa266ac7acd`.

---

## CHANGELOG

| Version | Date | Changes |
|---|---|---|
| 3.1 | 2026-10-14 | Every feature expanded with actual scope, deliverables, tests, exit criteria. Single file. Tech stack locked to POC (Python 3.14, mcp 1.30.0). |
| 3.0 | 2026-10-14 | Single file, colored dashboard, three-environment matrix, POC carry-forward. |
| 2.x | 2026-10-14 | Interim (superseded). |
| 1.2 | 2026-10-04 | Tasks 2, 3, 6, 7 complete. |
| 1.1 | 2026-10-04 | LUKS header backup complete. |
| 1.0 | 2026-10-03 | Initial. |

---

## POC CARRY-FORWARD

**Locked identifiers:** domain `qflowlab.trade`, hostname `interface.qflowlab.trade`, tunnel `quantflow-interface`, config `~/.cloudflared/quantflow-interface.yml`, origin `127.0.0.1:8765`, MCP SDK `mcp==1.30.0`, Python 3.14, Bitwarden project `quantflow`, machine account `QuantFlow-App` (Can read), Access scope `/healthz` only, WAF "Allow MCP" (skip BIC on `/mcp`), Bot Fight Mode off for POC.

**Files carried forward into Feature 070:**
- `src/quantflow/adapters/mcp/api_key.py`
- `src/quantflow/adapters/mcp/server.py`
- `src/quantflow/cli/mcp_probe.py`
- `docs/reports/POC-transport-final.md`

**Reuse:** folder layout, `.gitignore`, `pyproject.toml` structure, `src/quantflow/` package layout, `migrations/`, `scripts/`, `systemd/`, `tests/`, `config/`, `docs/`, `fixtures/`, `specs/`, `templates/`, `tools/`, users `quant`/`quant-cap`/`quant-rhythm`, `/data`+`/var/quant`, helper patterns, Cloudflare state, Bitwarden state.

**Do not reuse:** POC business logic, schemas, constants, anti-detection logic, provider adapters, scoring/decision logic, any POC DB, `POC_API_KEY` value, any POC secret/token/cookie/payload, `config/.env.local`.

---

## SESSION 1 — Encrypted Storage Foundation — <span style="color:green">✅ COMPLETE</span>

**Completed:** 2026-10-03

All tasks done. See ACTIVITY STATUS DASHBOARD for the full list and key values.

---

## SESSION 2 — Repository, Toolchain, Design Freeze

**Status:** 🔄 70% complete

### Task 1 — LUKS Header Backup <span style="color:green">✅</span>
Header (16 MB) GPG-AES256 encrypted with random 32-char passphrase. SHA-256 `c1b236d92af2382734ebb6aa5acc9364a40c6f24b0ddf3a58bed0ffafaf33da6`. Uploaded to MEGA. Local temp shredded. Bitwarden updated. Recovery: `gpg --decrypt` → verify SHA-256 → `cryptsetup luksHeaderRestore`.

### Task 2 — User Reconciliation <span style="color:green">✅</span>
| Name | UID | GID | Purpose |
|---|---|---|---|
| `quantflow` group | — | 986 | shared group |
| `quant` | 997 | 986 | SQLite writer, holds BWS token |
| `quant-cap` | 995 | 65534 | capture, NO `/data` write, no token |
| `quant-rhythm` | 994 | 986 | scheduler, no token |

Checks passed: `sudo -u quant touch /data/.test` works; `sudo -u quant-cap test ! -w /data` returns true.

### Task 3 — Directory Reconciliation <span style="color:green">✅</span>
`/data` and `/var/quant` created with `quant:quantflow 2770`. See previous runbook for full tree.

### Task 4 — Anti-Detection Scope ADR ⬜
Write `docs/architecture/adr/ADR-001-anti-detection-scope.md` stating: authorized automated access only; CAPTCHA human-only; persistent challenge/403 → authorization review; stock-Chrome probe separate; no bypass of unauthorized protections; no secrets in Git. Commit.

### Task 5 — Freeze Design Bundle ⬜
11 files (SPEC v2.0.5.1 Vol1–Vol7, ARCH v5.1.5.1 Vol1–Vol4) from `~/Downloads/lates_arch/` → `docs/reference/release-v2.0.5.1-v5.1.5.1/`. `sha256sum *.md > SHA256SUMS`, `sha256sum -c` passes. Symlink `docs/reference/CURRENT`. Commit.

### Task 6 — Repo + `.gitignore` First <span style="color:green">✅</span>
Repo at `~/src/quant-flow-system`. `.gitignore` committed first (`a0cee76`). Secret patterns ignored.

### Task 7 — Folder Structure <span style="color:green">✅</span>
Top-level dirs: `config`, `docs`, `fixtures`, `migrations`, `scripts`, `specs`, `src`, `systemd`, `templates`, `tests`, `tools`. `src/quantflow/` with subpackages. Committed `f640d85`.

### Task 8 — uv + Python 3.14 + Foundation Deps ⬜
```bash
curl -LsSf https://astral.sh/uv/0.12.22/install.sh | less
curl -LsSf https://astral.sh/uv/0.12.22/install.sh | sh
source ~/.bashrc
uv python install 3.14
cd ~/src/quant-flow-system
uv init --package --python 3.14
uv add pydantic pydantic-settings typer rich structlog orjson msgspec \
       httpx tenacity aiosqlite duckdb==1.5.6 pyarrow polars numpy scipy \
       pandas-market-calendars
uv add mcp==1.30.0 PyJWT[crypto] starlette uvicorn
uv add --dev pytest pytest-asyncio pytest-cov hypothesis ruff mypy \
       pre-commit freezegun respx
uv lock && uv sync --frozen
```
Verify `mcp==1.30.0`.

### Task 9 — `pyproject.toml` Tool Config ⬜
Add `[tool.pytest.ini_options]`, `[tool.coverage.run]`, `[tool.ruff]`, `[tool.ruff.lint]`, `[tool.mypy]`, `[tool.setuptools.packages.find]`. Ruff target `py314`; mypy `python_version = "3.14"`. Verify `ruff check .`, `mypy src`, `pytest` all pass (empty suite).

### Task 10 — Commit + Tag ⬜
`git commit -m "feat: repository scaffold, toolchain, design freeze"` then `git tag foundation-complete`.

### Task 11 — Boot Auto-Mount ⏳ Deferred
Manual `sudo mount /data` needed if SABRENT unplugged at boot. Defer.

---

## SESSION 3 — SDD Toolchain, Bitwarden, Feature 005 Kickoff

### Task 1 — OpenSpec 1.14.0 ⬜
```bash
npm install --global --prefix "$HOME/.local/share/qf-devtools" @fission-ai/openspec@1.14.0
export PATH="$HOME/.local/share/qf-devtools/bin:$PATH"
cd ~/src/quant-flow-system
mkdir -p pocs/interface && cd pocs/interface
openspec init --tools opencode
```

Adopt ChatGPT-POC concepts (constitution + change + capability specs + tasks). Do not reuse its files — the actual project has its own `CONSTITUTION.md` and 11-file design bundle.

### Task 2 — OpenCode 1.18.34 ⬜
```bash
npm install --global --prefix "$HOME/.local/share/qf-devtools" opencode-ai@1.18.34
export PATH="$HOME/.local/share/qf-devtools/bin:$PATH"
opencode --version
```
Configure exact free-model IDs through OpenRouter or OrcaRouter. Preflight public catalog before each session. Stop on paid routes.

### Task 3 — Bitwarden CLI (`bws`) ⬜
```bash
curl -fsSL https://bws.bitwarden.com/install -o /tmp/bws.sh
less /tmp/bws.sh
sh /tmp/bws.sh
sudo install -m 0755 "$(command -v bws)" /usr/local/bin/bws
bws --version
```
Move token out of repo to `/etc/quant-flow/bitwarden-bootstrap.env` (chmod 600).

### Task 4 — Systemd Encrypted Credential ⬜
```bash
sudo install -d -m 0700 /etc/quant-flow/credentials
printf %s "$BWS_ACCESS_TOKEN" | sudo systemd-creds encrypt \
  --name=bws_access_token - /etc/quant-flow/credentials/bws_access_token.cred
sudo rm -f /etc/quant-flow/bitwarden-bootstrap.env
```

### Task 5 — Add Project Secrets to Bitwarden ⬜
POC already stored: `POC_API_KEY` (rename value for production in 070), `ACCESS_CLIENT_ID`, `ACCESS_CLIENT_SECRET`. Add: `DISCORD_WEBHOOK_URL`, `RESEND_API_KEY`, `MAILGUN_API_KEY`, `MAILGUN_DOMAIN`, `MUSE_SERVICE_TOKEN`.

### Task 6 — Feature 005 Kickoff ⬜
```bash
git switch -c feature/005-domain-types-units-clock
```
Run `/opsx-propose` → human review → `/opsx-apply`. Resolve RQ-004 before baseline migration freeze.

**RQ-004 resolution:**
```
cluster_grade: BASIC | MEDIUM_CONFLUENCE | HIGH_CONFLUENCE
cluster_state: ACTIVE | MIXED | BULLISH_REVERSAL | BEARISH_REVERSAL | RETRACTED | EXPIRED
episode_state: FORMING | ACTIVE | UPGRADED | REVERSED | RETRACTED | EXPIRED
```

---

## SESSION 4–5 — Feature 005: Domain Types, Units, and Clock

**Feature 005 — Purpose.** Establish the canonical type system, unit system, and clock discipline that all downstream code depends on. Nothing else can be built correctly until this is frozen.

**Deliverables.**
- **Typed enums** (as Python `StrEnum` or `Literal` aliases): `ClusterGrade`, `ClusterState`, `EpisodeState`, `DTELane` (0DTE, 1DTE, TACTICAL_2DTE, SHORT_TACTICAL, SWING, LONGER_HORIZON), `DecisionState` (12 values), `ProviderState` (9 values), `Coverage` (COMPLETE/PARTIAL/MANUAL_ONLY/UNKNOWN), `DQGrade` (A/B/C/D/F), `NotificationDomain` (SYSTEM/TACTICAL/RESEARCH), `NotificationUrgency`, `NotificationState` (open/resolved/expired), `EvidenceTier` (1–4), `LeadLagClass`, `StructureSignature` (25 entries per SPEC Vol 3 §10.4).
- **Unit types** for money and price: `Cents`, `Micros`, `Mills` — with explicit constructors that reject mixing. All decision-path money uses integer minor units; `_cents` for option prices, `_micros` for underlying/index spot, `_mills` for strikes and levels.
- **Clock module:** `utc_epoch_ms()` (business timestamps), `jwt_seconds()` (JWT convention), `TradingCalendar` wrapper over `pandas-market-calendars` for regular sessions, half-days, holidays, and per-instrument close/`last_trade_at`. Half-day and holiday handling per SPEC Vol 3 §9.6 and ARCH Vol 4 §AH.5.
- **Canonical scope key format** per ARCH Vol 1 §AI.19: `"kind=<k>|target=<t>|route=<r>|lane=<l>|horizon=<h>"`, alphabetical, lowercase, `_ANY` for missing, ≤200 chars, reject non-canonical strings.
- **RQ-004 fix** applied: three disjoint vocabularies, no state ever named `BASIC`.

**Dependencies.** None. This is the first real code feature.

**Tests.**
1. Golden: valid enum construction; invalid values raise `ValueError`.
2. Boundary: unit conversion exactness (`mills = micros // 1000`, `micros = mills * 1000`) with rounding rules.
3. Sign/unit: cannot add `Cents` to `Micros`; mypy strict rejects at compile time.
4. Clock: `utc_epoch_ms()` monotonic, `jwt_seconds()` returns int seconds.
5. Trading calendar: regular day, half-day, holiday, `last_trade_at` per instrument.
6. Scope key: round-trip canonical, reject unordered fields, reject >200 chars.
7. Property: enum membership is closed; unknown value fails closed.
8. No-future-leakage: calendar lookups never return future session data.
9. Reproducibility: same input → same output byte-for-byte.
10. Coverage ≥95% for `src/quantflow/domain/`.

**Exit.** All tests pass. `ruff`, `mypy --strict` clean. Tag `feature-005-complete`. Merge to main.

---

## SESSION 6 — Feature 010: Migration Runner (E1)

**Feature 010 — Purpose.** A forward-only, checksum-verified migration runner for both stores (SQLite `quant_state.db` and DuckDB `quant_flow.duckdb`), with fresh-install and upgrade paths, per SPEC Vol 2 §19.1 and ARCH Vol 2 §C.3.

**Deliverables.**
- `migrations/sqlite/` and `migrations/duckdb/` directories. A baseline `000_baseline_v2.0.5.1.sql` per store that combines the final v2.0.5.1 schema through SQLite 069 / DuckDB 041. Historical upgrade migrations 001–064 (SQLite) and 001–037 (DuckDB) folded into the baseline.
- Real applied migrations SQLite 057–070, DuckDB 033–042 as immutable files with SHA-256 in a manifest.
- `schema_version_sqlite` / `schema_version_duckdb` tables recording `migration_id`, `checksum`, `applied_at`, `app_version`, `result`.
- Runner that (a) applies `000_baseline` once on fresh installs, (b) computes `pending = enabled_manifest_ids - baseline_covered_ids - applied_ids`, (c) validates dependency closure and checksums, (d) executes a stable topological ordering, (e) never uses `MAX(migration_id)`, (f) refuses to edit applied migrations.
- Reserved-but-not-applied slots: SQLite 071 (proposed core repair), 072–079; DuckDB 043–045 (AE/AF/AG research), 046–049 (future), 050 (proposed core repair).

**Dependencies.** Feature 005.

**Tests.**
1. Fresh install → schema matches baseline hash.
2. Upgrade from simulated prior state → all pending applied in order.
3. Checksum mismatch on an applied migration → abort with clear error.
4. Duplicate migration ID → abort.
5. Reapplying an already-applied migration → no-op.
6. Reserved numbers (043–045) NOT auto-applied on fresh install.
7. AF 044 adopted before AE 043 → later adoption still applies 043.
8. `schema_version_*` row written exactly once per migration with correct result.
9. Failure mid-migration → transaction rollback, `result=FAILED`, clear report.
10. Migration files hash identically to manifest entries.

**Exit.** All tests pass. Fresh and upgrade paths produce identical schemas for identical module sets. Commit and tag `feature-010-complete`.

---

## SESSION 7 — Feature 011: SQLite Repositories (E1)

**Feature 011 — Purpose.** A single-writer, WAL-mode, bounded-pool repository layer for `quant_state.db` that all SQLite access flows through. No component opens a raw SQLite connection.

**Deliverables.**
- Connection manager with `journal_mode=WAL`, `synchronous=NORMAL`, `cache_size=-16000`, `temp_store=MEMORY`, `mmap_size=268435456`, `foreign_keys=ON`, `busy_timeout=5000`.
- WAL checkpoint policy: `PRAGMA wal_checkpoint(TRUNCATE)` at low-activity session breaks and when `quant_state.db-wal` exceeds `WAL_SIZE_CEILING_MB = 50`.
- **Single writer task** serialized via `asyncio` queue. Only `quantd` owns this.
- **Bounded reader pool** for read-only queries from observability and Muse tools.
- Repository classes per table group: `source_authorization`, `provider_sessions`, `provider_state`, `provider_alert_attributes`, `live_price_current`, `option_quote_current`, `package_quote_current`, `signals`, `signal_versions`, `delivery_outbox`, `positions`, `position_legs`, `position_fills`, `symbol_filter`, `coverage_windows`, `raw_provider_events`, `canonical_events`, `canonical_event_sources`, `canonical_event_relationships`, `persistent_idempotency`, `corporate_action_ingestion`, `provider_query_pool`, `provider_query_budget`, `profile_cohort`, `wire_pins`, `expected_fingerprints`, `trace_fingerprints`, `trace_features`, `fingerprint_audit_log`, `detection_events`, `notifications`, `notification_deliveries`, `scheduler_heartbeats`, `scheduled_tasks`, `daily_alert_cycle`, `daily_alert_items`, `symbol_theses`, `thesis_versions`, `thesis_event_membership`, `zero_dte_cluster_current`, `zero_dte_cluster_members`, `zero_dte_cluster_member_history`, `report_runs`, `report_snapshot_refs`, `portfolio_state_current`, `dealer_context_cache_current`, `dealer_map_current`, `market_map_current`, `active_model_manifest`, `spx_crossing_state_current`, `operator_control_audit`, `ingest_log`, `backfill_log`, `behavioral_reference`, plus the observability tables.
- Immutable-row helpers: `insert_once`, `append`, `never_update` guards on `canonical_events`, `market_map_snapshots`, `dealer_level_maps`, `auth_audit`-style tables.

**Dependencies.** Feature 010 (schema exists).

**Tests.**
1. Contract per repository: create, read, list, delete (where allowed) round-trip.
2. WAL mode confirmed at startup; checkpoint truncates.
3. Single-writer concurrency test: 100 concurrent insert tasks serialize correctly, all rows land.
4. Reader pool under load: 50 concurrent reads while writer runs, no `SQLITE_BUSY`.
5. Foreign key enforcement: bad FK insert raises `IntegrityError`.
6. CHECK constraints enforced: negative `bid_cents`, `ask < bid`, singleton `portfolio_state_current` violation all rejected.
7. Immutability: update/delete on append-only table raises.
8. Restart safety: reopen DB after unclean shutdown, WAL replay consistent.
9. Half-open transaction rollback: exception mid-tx → no partial writes.
10. No reads/writes outside `/data/quant_state.db` in tests (temp paths only).

**Exit.** All tests pass. Tag `feature-011-complete`.

---

## SESSION 8 — Feature 012: DuckDB Repositories (E1)

**Feature 012 — Purpose.** A bounded-executor, single-writer analytical layer for `quant_flow.duckdb`. All writes go through `db_pool_executor`; the asyncio event loop is never blocked.

**Deliverables.**
- Connection with `memory_limit='1.2GB'`, `threads=2`, `temp_directory='/data/duckdb_tmp'`.
- Repository classes per analytical table: `options_master`, `quote_snapshot_batches`, `option_quote_observations`, `package_quote_observations`, `chain_snapshots`, `greeks_snapshots`, `signal_ledger`, `signal_outcomes`, `position_leg_outcomes`, `shadow_samples`, `dealer_snapshot_batches`, `dealer_exposure_snapshot`, `volatility_snapshots`, `portfolio_snapshots`, `technical_level_snapshots`, `ohlcv_bars`, `vol_index_history`, `calibration_model`, `scoring_rule_registry`, `raw_provider_events` (mirror), `price_observations`, `analysis_snapshots`, `market_map_snapshots`, `market_map_levels`, `dealer_level_maps`, `dealer_levels`, `cot_snapshots`, `closing_fdi_snapshots`, `leveraged_etf_pressure`, `spx_crossing_state_history`, `market_events`, `macro_market_observations`, `macro_regime_snapshots`, `zero_dte_cluster_snapshots`, `zero_dte_cluster_outcomes`, plus observability tables `trace_spans`, `slo_measurements`, and AH tables `exit_evaluations`, `ivr_history`.
- **No native `TIMESTAMP` columns** — epoch-ms as `BIGINT` everywhere, enforced by a schema test.
- `pending_ledger_sync` and `pending_exit_sync` drain to DuckDB asynchronously with idempotent IDs.

**Dependencies.** Feature 010.

**Tests.**
1. Contract per repository.
2. Bounded executor: a slow analytical query does not stall an asyncio tick.
3. No `TIMESTAMP` in DDL — schema scan rejects.
4. Epoch-ms columns are `BIGINT`.
5. Memory cap enforced: oversized query aborts cleanly.
6. Temp dir is `/data/duckdb_tmp`.
7. `pending_ledger_sync` drain idempotent: replay does not duplicate.
8. `pending_exit_sync` mirror: crash before ACK → retry succeeds, no duplicate.
9. Outage: DuckDB unavailable → SQLite state retained, queue grows, no data loss.
10. Schema hash matches SPEC Vol 2 §19.3 after whitespace normalization.

**Exit.** All tests pass. Tag `feature-012-complete`.

---

## SESSION 9 — Feature 013: Writer Queue and Outbox (E1)

**Feature 013 — Purpose.** A durable, bounded writer queue that guarantees at-least-once delivery of state transitions from the fast path to both stores, plus the `delivery_outbox` state machine for notification channels.

**Deliverables.**
- Bounded `asyncio.Queue` for state transitions with backpressure.
- `delivery_outbox` state machine per ARCH Vol 1 §N.11: `pending → in_progress → delivered | failed | exhausted`.
- Backoff schedule 30s → 60s → 120s → 300s → 900s, max 6 attempts.
- Fatal classification: 5xx / timeout / connection → retry; 4xx / auth / malformed → exhausted immediately, `fatal_delivery_error=1`, `delivery-channel-degraded` notification.
- `pending_ledger_sync` and `pending_exit_sync` per SPEC Vol 5 §O.11 and ARCH Vol 4 §AH.6.3.
- Idempotency keys: every enqueue uses a `dedup_key` persisted in `persistent_idempotency` with TTL 7 days.

**Dependencies.** Features 011, 012.

**Tests.**
1. Enqueue → process → ack flow happy path.
2. Bounded queue: 10k enqueue at 1k processing rate → queue fills, producers block, no OOM.
3. Restart with `in_progress` rows → reset to `pending` after lock expiry.
4. Idempotency: same `dedup_key` twice → second is no-op.
5. Retry backoff schedule observed.
6. Fatal 4xx → `exhausted` immediately, `fatal_delivery_error=1`.
7. `delivery-channel-degraded` fires on fatal.
8. `pending_ledger_sync` drains after restart.
9. `pending_exit_sync` drains after DuckDB recovery.
10. Crash mid-processing → row re-claimed by next worker.

**Exit.** All tests pass. Tag `feature-013-complete`.

---

## SESSION 10 — Feature 014: Scheduler and Rate Budgets (E1)

**Feature 014 — Purpose.** Async task scheduler with jittered timing, per-provider rate budgets, and OpenMarket cycle scheduling. No `time.sleep()` in the event loop.

**Deliverables.**
- `scheduled_tasks` state machine: `PENDING → RUNNING → DONE | FAILED`. Partial unique index on `dedup_key` where state IN (`PENDING`, `RUNNING`).
- Task types: nightly backup, T+1 OI job, DQ report, adversarial harness, SPX pre-market setup (μ = 06:45 ET, σ = 15 min, [06:00, 07:00]), SPX post-close cleanup (μ = 16:45 ET, σ = 15 min, [16:30, 17:30]), canary refresh, SLO evaluator (every 5 min), escalation runner (every 15 min).
- `provider_query_pool` and `provider_query_budget` enforcement per SPEC Vol 2 §19.2 and ARCH Vol 4 §D.26: FLOW_ALERT (60%), MORNING_AD_HOC (40% shared), GLOBAL (separate). Pre-market borrow ≤ `BUDGET_PREMARKET_BORROW_PCT = 20`, restored at 09:30 ET. Intraday FLOW_ALERT may draw MORNING_AD_HOC only when that pool is ≥80% unspent. ZERO_DTE_CLUSTER draws from FLOW_ALERT.
- Cancellation from `PENDING` only; `RUNNING` tasks complete or fail cleanly.
- `human_rhythm_scheduler` state machine: `offline → waking → active → deep-read → light-check → break → drifting → distracted → winding-down → offline`.

**Dependencies.** Feature 013.

**Tests.**
1. Task creation, run, DONE.
2. Failure increments attempts, re-enqueues with backoff, eventually `FAILED`.
3. Dedup: two `PENDING` with same key → second rejected.
4. Cancellation from `PENDING` only.
5. Restart: `RUNNING` at crash → reset to `PENDING`.
6. No `time.sleep()` in any async path — AST scan of `src/quantflow/` for `asyncio.sleep` misuse.
7. Budget: pool 60/40 split enforced; borrow rules enforced; over-budget query rejected.
8. SPX cycle scheduled within jitter window.
9. Rate-limit reset at day boundary.
10. Coverage ≥95% for `src/quantflow/services/scheduler.py`.

**Exit.** All tests pass. Tag `feature-014-complete`.

---

## SESSION 11 — Feature 015: Backup and Restore Drill (E1)

**Feature 015 — Purpose.** Nightly backup barrier per ARCH Vol 1 §M.1 and quarterly restore drill.

**Deliverables.**
- Barrier sequence: pause capture intake → drain `pending_ledger_sync` + in-flight outbox → `PRAGMA wal_checkpoint(TRUNCATE)` → close DuckDB cleanly → copy both files → verify SHA-256 → reopen → resume capture → `rclone` to encrypted offsite → log duration.
- Silent on success; always notify on failure.
- 30-day retention.
- Quarterly restore drill: download artifact → decrypt → verify SHA-256 → restore to scratch → open both stores → row-count + checksum spot checks → record duration → notify → log in `operator_control_audit`.
- RTO target ≤ 4 hours.

**Dependencies.** Features 011, 012, 013.

**Tests.**
1. Barrier happy path: both files copied, checksums match.
2. Failure during copy → notification, no partial backup retained.
3. Restore drill: scratch restore opens, spot checks pass.
4. Retention: 31 days → oldest pruned.
5. `rclone` failure → local backup retained, notification raised.
6. Barrier interruption → resume protocol works.
7. Restore RTO measured ≤ 4h in simulated run.
8. Offsite copy verified by SHA-256.
9. Notification fires on any failure path.
10. No production data read from `/data` in tests — temp paths only.

**Exit.** All tests pass. `docs/reports/phase-1-gate.md` written. **E1 gate cleared.** Tag `feature-015-complete`.

### E1 GATE
- [ ] Full test suite green
- [ ] Every E1 feature converged
- [ ] Synthetic epic integration scenario passes
- [ ] No P0/P1 deferred without ADR
- [ ] `docs/reports/phase-1-gate.md` committed

---

## SESSIONS 12–14 — E2 Canonical Event Pipeline

### Feature 020 — Ingestion Adapters
Per SPEC Vol 2 §4, §5. Raw event archive (immutable, append-only, hash-verified). Provider adapters load into `raw_provider_events` with `payload_hash`, `parser_version`, `schema_version`, `access_channel`, `authorization_id`, `source_trace_id`. Capture emits `provider-observation-submitted` IPC events per SPEC Vol 1 §2.3.9. Capture prunes spool after quantd ACK.

### Feature 021 — Canonicalizer and Dedup
Per SPEC Vol 2 §5. `canonical_events` with event-time NBBO preserved. Dedup fingerprint priority: `exchange_execution_id` → `provider_event_id` → content hash. `canonical_event_sources` bridges sources without double-counting. `canonical_event_relationships` records `INDEPENDENT_REPEATED_FLOW`, `RELATED_CLUSTER`, `SAME_THESIS_UPDATE`, `SUPERSEDES`. Corrections and out-of-sequence events recorded with `correction_status`.

### Feature 022 — Data Quality Gateway
Per SPEC Vol 2 §6. Grades A/B/C/D/F. Checks: freshness, staleness, source conflict, greek sign, spread width, coverage, canary agreement. Quote rejection reasons: stale, crossed, wide, size zero, malformed, unknown source. Coverage caps applied inside weighted sum: PARTIAL 0.70, MANUAL_ONLY 0.50, UNKNOWN 0.00.

### Feature 023 — Candidate Engine and Symbol Filter
Per SPEC Vol 1 §7. Pre-screen scoring order: dedup → quality → candidate score. Shadow sampling per §7.4. Default `symbol_filter` rows pinned per §7.6, including the `ZERO_DTE_CLUSTER` scope that includes equities and SPX, excludes ETFs and other indexes. Corporate action hard gate: `PENDING` for a ticker blocks flow alerts.

### Feature 024 — Corporate Actions and Backfill
Per SPEC Vol 2 §4.9. Daily ingestion → `corporate_action_ingestion`. Adjusted contracts tagged with new `corporate_action_ver`, cached greeks and dealer data invalidated. Backfill job per `backfill_log`.

**E2 gate.** Full pipeline from raw → canonical → DQ → candidate → filter tested with synthetic fixtures. `phase-2-gate.md`.

---

## SESSIONS 15–22 — E3 Pure Quant Kernels

Pure, deterministic, side-effect-free kernels. Coverage ≥95% mandatory.

### Feature 030 — Delta-Gamma-Theta-IV Decomposition
Per ARCH Vol 4 §D.3. Unit contract: option price dollars, delta-spot dollars, gamma per ($1 move)², theta per day, vega per vol point. `Δσ_impl,volpt = (ΔP$ − Δ·ΔS$ − ½·Γ·(ΔS$)² − Θ$/day · Δt_days) / V$/volpt`.

### Feature 031 — PayoffKernel
Per ARCH Vol 4 §D.5. **Separates exact contractual risk from the finite scenario grid.** Endpoint test at x=0 and every strike; upper-tail slope for unbounded loss/profit detection. `risk_status=FINITE` required for sizing. `scenario_worst_loss_cents` is diagnostic-only. Golden: short $100 put, credit $200, multiplier 100 → max loss $9,800 at x=0, not $8,800 at x=$10.

### Feature 032 — Position Sizing
Per ARCH Vol 4 §D.6. Lane parameterization: TACTICAL_2DTE `max_risk_pct_equity=0.005`; otherwise `BASE_RISK_PCT=0.0075`. `risk_per_package_cents = max_risk_per_package_cents + risk_cost_allowance_cents`. Both inputs from D.5. Missing/unbounded/zero-risk → no size.

### Feature 033 — FDI (Delta-Weighted Flow Imbalance)
Per ARCH Vol 4 §D.25. `S_i_dollars = S_i_micros / 1,000,000`. `D_i = Σ_j s_ij · Δ_ij · Q_ij · M_ij · S_i_dollars`. `FDI_t = Σ_i q_i·D_i / Σ_i q_i·|D_i|`.

### Feature 034 — Dealer Hedging Pressure
Per ARCH Vol 4 §D.21. `H_$ = -(gamma_flow_$per1pct × ΔS_pct + vanna_flow_$pervolpt × ΔIV_volpt + charm_flow_$perday × Δt_days)`. `H_signed = H_$ / ADV_$`. Opposing → `EV_lower -= HEDGE_PENALTY_DEFAULT × H_magnitude`. Single application only.

### Feature 035 — Flow Strength and Confluence
Per ARCH Vol 4 §D.14b. `X_k` sums signed leg deltas. `B = Σ max(X_k, 0)`, `R = Σ max(-X_k, 0)`. `OpposingShare = min(B,R)/(B+R)`. `DirectionalStrength = 1 − 2·OpposingShare`. `FlowStrength = w_Delta·P_Delta + w_Premium·P_premium + w_Direction·D_s + w_Events·E_s + w_Strikes·K_s`. `ConfluenceScore = 0.65·F + 0.25·D_c + 0.10·P_c`.

### Feature 036 — SPX Crossing State Machine
Per SPEC Vol 3 §9.6 and ARCH Vol 4 §AD. States: FAR, APPROACHING, TESTING, CONFIRMED_BREAKOUT, CONFIRMED_REVERSAL, FALSE_CROSS, COOLDOWN, REARMED, INVALIDATED. Hysteresis: retreat threshold `SPX_APPROACHING_RETREAT_PCT=0.005` strictly greater than entry `SPX_APPROACHING_PCT=0.003`. Intraday confirmation via 1-min bar close + 60s hold. Close-of-day resolution to COOLDOWN.

**E3 gate.** Every kernel ≥95% coverage. Property tests for algebraic invariants (sign symmetry, zero-detection, boundary-mass). `phase-3-gate.md`.

---

## SESSIONS 23–26 — E4 Decision Evidence and Delivery

### Feature 040 — AnalysisSnapshotBuilder
Per SPEC Vol 1 §2.9 and ARCH Vol 4 §S. **Pure with respect to inputs.** No wall-clock reads except `as_of`. No random draws outside `as_of`-seeded PRNG. Same inputs + versions → byte-identical. No external mutation, no provider calls. AST lint rejects `fetch_*`, `get_current_*`, `read_pointer_*` in builder body. `signal_valid` predicate per SPEC Vol 3 §8.1a.

### Feature 041 — Decision State Selection and Signal Ledger
Per SPEC Vol 3 §8.4. Order: external facts → DQ gate → signal validity → evaluated outcomes. `signal_versions` written on material change. `signal_ledger` (DuckDB) records full decision evidence. Route selection: long-call, long-put, short-put, debit-spread, spread-specific. Route undefined → WATCH.

### Feature 042 — Notification Delivery and Outbox
Per SPEC Vol 4 §16 and ARCH Vol 4 §G. Channels: Discord, Resend (primary email), Mailgun (fallback), Muse. Categories per SPEC Vol 4 §18.14. Cooldowns per-category. `delivery_outbox` from Feature 013 drives delivery. All-fail readable. Muse reads the table only.

**E4 gate.** First synthetic end-to-end fixture passes: canonical event → DQ → candidate → enrichment → snapshot → decision → notification → delivered. `phase-4-gate.md`.

---

## SESSIONS 27–32 — E5 Provider Adapters

### Feature 050 — LivePriceProviderAdapter
Per ARCH Vol 4 §P. Source priority: listed-option underlying, official index, then authorized free sources. Quality flags per observation. Basis discipline per SPEC Vol 3 §9.7. `BASIS_TOLERANCE_BPS=15`. Prior session close is not a basis reference.

### Feature 051 — ListedOptionQuoteAdapter
Per ARCH Vol 4 §AC. Interface: `get_quote(contract_id)` and `get_package_quote(legs)` → immutable observation IDs. Quality: bid ≥ 0, ask ≥ bid, spread and freshness within lane limits. Fallback to VALIDATED_PENDING_ENTRY or WATCH. **RQ-005 must be resolved before this:** `package_quote_observation_id` at evidence boundaries per SPEC Vol 2 §19.6 invariant AM.

### Feature 052 — Provider Capture Worker (phantomime)
Per ARCH Vol 3. Custom CDP client wrapping real Google Chrome stable, headed under Xvfb. **Not Playwright, not Puppeteer.** Per-profile persistent `user_data_dir`. Dependency-import lint rejects `playwright` and `puppeteer`. Session lifecycle per ARCH Vol 3 §E (log-normal 30 min median, σ 0.75, hard cap 60 min). Session rhythm per §E.6 micro-breaks, §E.7 pacing floor, §E.8 opening sequence, §E.9 idle disengagement, §E.10 session end. `challenge-detected` IPC event per ARCH Vol 1 §B.3. **ADR-001 governs 052.**

### Feature 053 — Provider State Machine and Loopback Echo
Per ARCH Vol 3 §F.N. States: HEALTHY, DEGRADED, CHALLENGED, MANUAL_REQUIRED, BLOCKED, COOLDOWN, AUTH_REQUIRED, SCHEMA_CHANGED, DISABLED. Loopback echo at `echo.quant.internal:9443` inside capture netns per §F.D.1 and §F.S.4. TLS 1.3 preferred, 1.2 accepted, ALPN `["h2","http/1.1"]`, real TLS cert.

### Feature 054 — Stock-Chrome Probe Environment
Per ARCH Vol 3 §F.U.2. Continuous stock Chrome against provider public endpoints. Jittered cadence 15 min [12, 18]. Own namespace, own egress, own `source_authorization` entry, separate Chrome `user_data_dir`. Single-machine fingerprint linkage decision per ARCH Vol 1 §AI.22.

**E5 gate.** All anti-detection checks pass per ARCH Vol 3 §F.Q (84 + 18 tests). `phase-5-gate.md`.

---

## SESSIONS 33–38 — E6 User Workflows

### Feature 060 — Real-Time Flow Alert
Per SPEC Vol 1 §2.14. Trigger: canonical event passes quality + candidate. Provider status mapping per §2.14.2. Unknown mapping fails closed. Renders to Discord + email.

### Feature 061 — 0DTE Cluster Detection
Per SPEC Vol 1 §2.20.7. Two tiers: MEDIUM_CONFLUENCE (immediate Discord + email) and HIGH_CONFLUENCE (immediate upgrade). Basic cluster silent. **RQ-003 must be resolved before 061:** 0DTE identity. `episode_id = sha256(ticker | expiration | direction | first_qualifying_canonical_event_id | ruleset_version)[:32]`. No route, no size, no ACTIONABLE_NOW.

### Feature 062 — Morning Action Brief
Per SPEC Vol 1 §2.15. Sections A–J: Decision Summary, Market Playbook, Carryover Thesis Board, 2DTE and Expiration-Risk Board, Portfolio and Capacity, Prior-Day Audit (with Prior-Day 0DTE Research), Event and No-Trade Calendar, Data and System Health, Dealer Level Map, Moving-Average Stack.

### Feature 063 — Ad Hoc Symbol Report
Per SPEC Vol 1 §2.16. On-demand per-symbol report. Dealer-context section (E) includes any active or recent 0DTE cluster for the ticker.

### Feature 064 — Daily SPX Price Alert Cycle
Per SPEC Vol 4 §18.19. Pre-market setup at μ = 06:45 ET, σ = 15 min, [06:00, 07:00]. Post-close cleanup at μ = 16:45 ET, σ = 15 min, [16:30, 17:30]. Alert spec: SPX, max 4 (2 upside + 2 downside, one may be flip). One-shot. Newsletter timeout clock: 06:15 ET. Verification window opens at setup completion, closes at 07:30 ET. Behavioral reference `operator_routine` records 06:45/16:45 acceptance.

**E6 gate.** All three workflows produce identical decisions from the same snapshot (`analysis_snapshot_id` → same decision). `phase-6-gate.md`.

---

## SESSIONS 39–44 — E7 Interface, Ops, Release

### Feature 070 — Muse MCP Interface (extends POC)
**Head start from POC:** transport path proven, `api_key.py` and `server.py` working, Cloudflare state persists, Bitwarden state persists.

**Must add:**
- Replace `POC_API_KEY` with a production API key.
- Extend `server.py` with real read-only tools per SPEC Vol 5 §O.3: `get_health`, `get_provider_state`, `get_dq_report`, `get_coverage_windows`, `get_detection_events`, `get_notification_timeline`, `get_pipeline_stage_status`, `get_slo_status`, `get_recent_errors`, `get_daily_summary`, `get_correlation_trace`.
- Role checks behind `MUSE_ADMIN` (reserved in v2.0.5.1; gated).
- Cache TTLs per SPEC Vol 5 §O.3.4.
- Move `mcp_probe.py` to `tests/integration/`.

### Feature 071 — Health Endpoint and Observability Sidecar
Per SPEC Vol 5 §O.2. FastAPI or aiohttp inside `quantd` as asyncio task, localhost:8091. `GET /health` full snapshot, `GET /health/{component}`, `GET /metrics`. Response schema per §O.2.3. `overall` computation per §O.2.4. Timeouts 200ms p95.

### Feature 072 — Log Persistence, Correlation IDs, and SLOs
Per SPEC Vol 5 §O.5, §O.6, §O.8. journald configuration, structured JSON logs, redaction at emit. `source_trace_id` (uuid4 at capture boundary) + `canonical_trace_id` (uuid5 from `canonical_event_id`) + `session_id` + `task_id` + `report_id`. SLO targets per §O.8.2. `slo_measurements` DuckDB table.

### Feature 073 — Alerting Tiers and Escalation
Per SPEC Vol 5 §O.7. Tiers: critical, immediate, warning, informational, daily. Escalation: SYSTEM + requires_ack=1 + unacknowledged → re-emit. Per-step reservation via `persistent_idempotency`. Root-aware, idempotent. Finite ladder per §O.7.4. Runs every 15 min.

### Feature 074 — Daily Status Summary and Dashboards
Per SPEC Vol 5 §O.9. Emitted at 08:00 ET daily via scheduled_tasks, idempotent on `(category='system-status-summary', subject_key=today)`. Content per §O.9.2. Dashboard views v1 driven by Muse tools.

**E7 gate.** Full acceptance suite passes: SPEC Vol 4 §20.71, §20.73, ARCH Vol 3 §F.Q, SPEC Vol 5 §O.13, plus new tests. `phase-7-gate.md` = **RESEARCH RELEASE**.

---

## SESSIONS 45+ — E8 Forward Research

### Feature 080 — Outcome Collection (Phase B)
Per SPEC Vol 6 §F.3. Sustained outcome collection across all live lanes. Scope gate: `N_scope >= max(300, 20 * p)`, at least 75 positive and 75 negative outcomes per scope. Per-scope arrival-rate estimates 3–18 months per SPEC Vol 3 §14.19.8a.

### Feature 081 — Minimal ML Challenger (Phase C)
Per SPEC Vol 6 §F.4. `LOGISTIC_L2` with 10–12 structured features. Chronological walk-forward. Pure local function. **CHALLENGER only** — no decision-path reachability. `model_predictions` table reserved (DuckDB 046).

### Feature 082 — Promote Only on Demonstrated Improvement (Phase D)
Per SPEC Vol 6 §F.5. Promotion requires: better Brier, better log loss, no worse calibration, better precision at same volume, lower FPs, 3 consecutive walk-forward windows, no regime failures, flow/dealer ablation shows value, replay integrity. `active_model_manifest.model_role = CHAMPION` workflow with full audit.

**E8 gate.** `phase-8-gate.md`.

---

## ARCH BUILD SEQUENCE MAPPING

| Runbook phase | ARCH Stage |
|---|---|
| E0 | Stage 0 — Pre-Code Setup |
| E1 | Stage 2 — Storage & Delivery |
| E2 | Stage 1/2 — Kernels + Storage |
| E3 | Stage 1 — Kernels |
| E4 | Stage 2.1–2.3 + Stage 3.2 |
| E5 | Stage 2.4–2.5 + Stage 3 — First Source |
| E6 | Stage 3.1–3.4 |
| E7 | Stage 2.6–2.7 + Stage 5 |
| E8 | Stage 4 + SPEC Vol 6 / Vol 7 |

---

## THREE-ENVIRONMENT WORKFLOW

**DEV (Lenovo Mint on USB).** VS Code + Remote SSH to PROD. OpenCode + OpenSpec here, never PROD. No runtime secrets. Author, test, review. Deploy deliberately.

**PROD (Ubuntu Server).** Runs `quantd`, `provider_capture_worker`, `human_rhythm_scheduler`, observability sidecar. Owns only writer to SQLite + DuckDB. Never runs AI agents.

**DB (Debian 13).** `/data` LUKS + ext4. `quant_state.db` (WAL) + `quant_flow.duckdb`. Only owner writes. Never over network for writes.

---

## DAILY PRACTICE

Start:
```bash
cd ~/src/quant-flow-system
git status && git pull --ff-only
uv sync --frozen
uv run pytest -q
```
Pick exactly one feature or task slice.

End:
```bash
uv run ruff check .
uv run mypy src
uv run pytest
git diff --check && git status --short
```
No uncommitted migrations. No untracked secrets.

---

## TESTING LADDER

1. Unit golden
2. Property
3. Contract
4. Migration
5. Repository
6. Pipeline fixture
7. Restart/idempotency
8. Replay
9. Workflow golden-output
10. Full acceptance
11. Opt-in live smoke

**Rule:** Never fix a failing live provider by weakening domain tests.

---

## PER-FEATURE 10 TEST CLASSES

1. Golden happy path
2. Boundary/units/sign
3. Missing/stale/malformed failure
4. Duplicate/idempotency/restart
5. Contract per port/adapter
6. Migration fresh + upgrade
7. Replay
8. Property invariants
9. No-future-leakage
10. Temp paths only (never `/data`)

Coverage ≥95% for `src/quantflow/kernels/**` and `src/quantflow/domain/**`.

---

## OPEN DESIGN CONFLICTS

| RQ | Resolution | Deadline |
|---|---|---|
| RQ-002 | `signal_valid` ordering | Before 037 |
| RQ-003 | 0DTE identity | Before 061 |
| RQ-004 | grade/state/episode split | Before baseline migration freeze (005) |
| RQ-005 | `package_quote_observation_id` at evidence boundaries | Before 040/051 |
| RQ-006 | "Per prior" placeholders | Per feature at clarify |

---

## ABSOLUTE PROHIBITIONS

- `time.sleep()` in async
- Unbounded queries/arrays/logs/tasks
- Secrets/DBs/payloads/sessions/screenshots in Git
- SQL/shell/URL/secret/order/migration tools in MCP
- LLM in the decision path
- Autonomous orders
- Undocumented provider endpoints
- Silent defaults for missing evidence
- Provider logic in kernels
- Editing applied migrations
- Archived designs over CURRENT
- CAPTCHA/challenge/403 bypass
- Developing or testing against `/data`
- ML libraries before E8
- Anti-detection: no bypass of unauthorized source protections
- Playwright or Puppeteer anywhere in capture tree
- DoH in the capture namespace

---

## WHEN SOMETHING FAILS

1. Stop.
2. Read the error carefully.
3. Check the log from that step.
4. Identify what changed.
5. If not found in 15 minutes, roll back and retry.
6. If it fails twice, do not push. Bring the exact error to the next session.

---

## RESUME POINT — START HERE NEXT TIME

**State:**
- Repo clean at `~/src/quant-flow-system`
- Design docs at `~/Downloads/lates_arch/` (11-file v2.0.5.1 / v5.1.5.1)
- Session 1 complete; Session 2 ~70%
- POC transport complete (`poc-transport-complete`)
- POC primitives preserved
- Cloudflare + Bitwarden state persists
- Tech stack locked: uv + Python **3.14** + `mcp==1.30.0`

**Next tasks in order:**
1. Task 5 — Freeze Design Bundle
2. Task 4 — ADR-001 anti-detection scope
3. Task 8 — uv + Python 3.14 + deps
4. Task 9 — `pyproject.toml` config
5. Task 10 — Commit + tag `foundation-complete`
6. Session 3 — OpenSpec + OpenCode + Bitwarden + Feature 005

**Verify state:**
```bash
cd ~/src/quant-flow-system
git log --oneline && git status
ls ~/Downloads/lates_arch/
git tag --list | grep -E 'poc|foundation'
```

---

## POC DEFERRED FAILURE DRILLS (OPTIONAL)

| # | Drill | Expected |
|---|---|---|
| 9.1 | Kill server mid-request | Muse gets transport error; no stale response |
| 9.2 | Restart server, same API key | New probe succeeds; old `response_id` not reused |
| 9.3 | Rotate `POC_API_KEY`, restart | Old key → 401; new key → pass |
| 9.4 | Stop cloudflared | Public probe fails; local probe works |
| 9.5 | Stop server, keep cloudflared | Public → 502; local refused |

---

## APPENDIX A — POC CLOUDFLARE CONFIGURATION (CARRY FORWARD)

```
~/.cloudflared/quantflow-interface.yml

tunnel: <UUID>
credentials-file: /home/<user>/.cloudflared/<UUID>.json
ingress:
  - hostname: interface.qflowlab.trade
    path: ^/(mcp|healthz)$
    service: http://127.0.0.1:8765
    originRequest:
      httpHostHeader: interface.qflowlab.trade
  - service: http_status:404
```

Access app `quantflow-interface`: path `/healthz` protected; `/mcp` outside Access. Policies: `operator` (Allow/Emails) + `admin-token` (Service Auth/token `quantflow-interface-admin`). WAF "Allow MCP" skips Browser Integrity Check on `/mcp`. Bot Fight Mode: off.

---

## APPENDIX B — 11-FILE DESIGN BUNDLE

```
docs/reference/
├── CURRENT -> release-v2.0.5.1-v5.1.5.1
└── release-v2.0.5.1-v5.1.5.1/
    ├── SHA256SUMS
    ├── SPEC_v2.0.5.1_Vol1_Foundations.md
    ├── SPEC_v2.0.5.1_Vol2_Data_Canonical.md
    ├── SPEC_v2.0.5.1_Vol3_Decision.md
    ├── SPEC_v2.0.5.1_Vol4_Capture_Behavior_Ops_Verification.md
    ├── SPEC_v2.0.5.1_Vol5_Observability.md
    ├── SPEC_v2.0.5.1_Vol6_Future_Extensions.md
    ├── SPEC_v2.0.5.1_Vol7_Research_Addenda.md
    ├── ARCH_v5.1.5.1_Vol1_Foundation.md
    ├── ARCH_v5.1.5.1_Vol2_DataModel.md
    ├── ARCH_v5.1.5.1_Vol3_Capture_AntiDetection.md
    └── ARCH_v5.1.5.1_Vol4_Services_Workflows.md
```

---

**END OF RUNBOOK v3.1**
