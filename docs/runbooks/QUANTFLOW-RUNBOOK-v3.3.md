# QUANTFLOW — MASTER SESSION RUNBOOK

**Version:** 3.3
**Date updated:** 2026-10-15
**Purpose:** Single authoritative session-by-session execution checklist, fully expanded.
**Mode:** RESEARCH only. No autonomous orders. No ML until E8.
**Design authority:** `SPEC v2.0.5.1` / `ARCH v5.1.5.1` — 11-file release, frozen under `docs/reference/CURRENT`.
**POC source of truth:** `docs/reports/POC-transport-final.md` (tag `poc-transport-complete`).

---

<!-- AUTO:CURRENT-STATE:START -->
## CURRENT STATE (auto 2026-10-17T20:12:25Z)

| Item | Status |
|---|---|
| Session 1 (storage) | COMPLETE |
| Session 2 (repo, toolchain, design freeze) | COMPLETE |
| Session 3 (OpenCode + OpenSpec zero-token setup) | COMPLETE |
| Feature 005 | COMPLETE — tag `feature-005-complete` |
| Feature 005a | COMPLETE — tag `feature-005a-complete` |
| Feature 005b | COMPLETE — tag `feature-005b-complete` |
| Feature 005c | COMPLETE — tag `feature-005c-complete` |
| Feature 010a | COMPLETE — tag `feature-010a-complete` |
| Repo | branch `master` |
| Working tree | clean |
| Tags | `feature-005-complete`, `feature-005a-complete`, `feature-005b-complete`, `feature-005c-complete`, `feature-010a-complete`, `foundation-complete`, `poc-transport-complete`, `session3-complete` |
| Last commit | `d0c3867 Update repo index` |

**Next action:** Continue active change: 010a-migration-runner-core

<!-- AUTO:CURRENT-STATE:END -->


---

## ENVIRONMENT MATRIX

| Role | Host | OS | Purpose |
|---|---|---|---|
| DEV | Lenovo laptop | Linux Mint 22 (bootable USB) | Authoring, tests, OpenCode, OpenSpec |
| PROD | Second laptop | Ubuntu Server | Runtime: quantd, capture, rhythm, observability |
| DB | SATA attached to PROD | Debian 13 host or Debian 13 container of PROD | `/data` — `quant_state.db` (SQLite WAL) + `quant_flow.duckdb` (DuckDB) |

**Cross-host rule:** SSH/Tailscale only. Never SFTP/SSHFS/NFS-mount a live SQLite file for writes. Only the single runtime owner writes `/data`.

**Locked tech stack** (as installed and verified 2026-10-14):

| Component | Installed version |
|---|---|
| OS (dev) | Linux Mint 22 on USB |
| Python | 3.14.7 |
| Package/env manager | uv 0.13.1 |
| Node.js (dev tooling) | 24.22.0 (LTS, Active) |
| npm | 11.19.1 |
| MCP SDK | **mcp==1.30.0** (v1 maintenance line — pinned per ADR-004) |
| ASGI | starlette 1.8.0, uvicorn 0.54.0 |
| HTTP client | httpx 0.28.1 |
| JWT | PyJWT 2.15.1 |
| Data | duckdb==1.5.6 (parked), aiosqlite 0.22.1, pyarrow 26.0.0, polars 2.0.0, numpy 2.5.4, scipy 1.18.1, pandas-market-calendars 5.5.0 |
| Config | pydantic 2.14.1, pydantic-settings 2.16.0 |
| CLI/logging | typer 0.27.3, rich 15.0.0, structlog 26.1.0 |
| Serialization | orjson 3.13.0, msgspec 0.22.0 |
| Retry | tenacity 9.2.1 |
| Testing | pytest 9.1.1, pytest-asyncio 1.4.0, pytest-cov 7.1.0, hypothesis 6.169.1, freezegun 1.5.5, respx 0.23.1 |
| Lint/type | ruff 0.17.0, mypy 2.4.0, pre-commit 4.7.0 |
| SDD | OpenSpec 1.14.1 |
| Agent | OpenCode 2.0.24 |
| Secrets | Bitwarden Secrets Manager (`bws` 2.1.0) |
| Tunnel | cloudflared 2026.10.0 (Cloudflare apt repo) |

**Pin rule:** never replace `mcp==1.30.0` with unpinned `mcp` or `fastmcp 3.x`. Never add `playwright` or `puppeteer` (ARCH Vol 3 §F.F).

---

<!-- AUTO:OVERALL-PROGRESS:START -->
## OVERALL PROGRESS

| Phase | Sessions | Status |
|---|---|---|
| E0 Setup & Foundation | 1–7 | Feature 005 done · Feature 005a done · Feature 005b done · Feature 005c done |
| E1 Storage & Durability | 8–13 | Feature 010a done |
| E2 Canonical Event Pipeline | 14–17 | ⬜ Not started |
| E3 Pure Quant Kernels | 18–25 | ⬜ Not started |
| E4 Decision Evidence & Delivery | 26–29 | ⬜ Not started |
| E5 Provider Adapters | 30–35 | ⬜ Not started |
| E6 User Workflows | 36–42 | ⬜ Not started |
| E7 Interface, Ops & Release | 43–48 | ⬜ Not started |
| E8 Forward Research | 49+ | ⬜ Not started |

**Phase notes:**
- E7: transport primitives proven by POC

<!-- AUTO:OVERALL-PROGRESS:END -->

---

## ACTIVITY STATUS DASHBOARD

### Session 1 — Encrypted Storage Foundation — <span style="color:green">✅ COMPLETE</span>

All 20 tasks done: host recorded, SABRENT detected (`152d:1561`), LUKS2 + ext4 (`quantdata`), `/data` mounted `noatime,nodiratime`, GRUB USB quirk, udev autosuspend, `evdi` fixed, group `quantflow` + 3 users, SQLite + DuckDB installed, `dbmount`/`dbunmount`/`dbstatus`, Bitwarden record, LUKS header backup (GPG AES256) uploaded to MEGA + SHA-256 in Bitwarden.

**Key values:** by-id `usb-SABRENT_SABRENT_DB9876543214E-0:0`, LUKS UUID `740ec50d-dbfb-4a59-a226-c13990f9837d`, label `quantdata`.

### Session 2 — Repository, Toolchain, Design Freeze — <span style="color:green">✅ COMPLETE</span>

| Task | Activity | Status |
|---|---|---|
| 1 | LUKS header backup | <span style="color:green">✅ done</span> |
| 2 | User reconciliation | <span style="color:green">✅ done</span> |
| 3 | Directory reconciliation | <span style="color:green">✅ done</span> |
| 4 | ADR-001 anti-detection scope | <span style="color:green">✅ done</span> |
| 5 | Freeze design bundle (11 files) | <span style="color:green">✅ done</span> |
| 6 | Repo + `.gitignore` first | <span style="color:green">✅ done</span> |
| 7 | Folder structure | <span style="color:green">✅ done</span> |
| 8 | uv + Python 3.14 + foundation deps | <span style="color:green">✅ done</span> |
| 9 | `pyproject.toml` tool config | <span style="color:green">✅ done</span> |
| 10 | Commit + tag `foundation-complete` | <span style="color:green">✅ done</span> |
| 11 | Boot auto-mount | ⏳ deferred (accepted) |

Extra work done beyond the original Session 2 scope:
- **ADR-002** (no containers) — committed
- **ADR-003** (Python version) — committed
- **ADR-004** (MCP SDK v1.30.0 vs v2.2.0, proposed) — committed
- Node.js upgraded to **24.22.0 LTS**; `.local/bin/node`/`npm`/`npx` repointed to v24
- uv upgraded to **0.13.1**
- OpenSpec upgraded to **1.14.1**
- `pydantic-settings` 2.16.0, `filelock` 4.2.0 bumps committed
- Smoke test suite added (`tests/test_smoke.py`, 5 tests)
- `docs/runbooks/archive/` for pre-freeze runbooks
- `docs/reports/POC-transport-final.md` for POC evidence

### Session 3 — SDD Toolchain, Bitwarden, Feature 005 — COMPLETE (2026-10-15, tag `session3-complete`)

| Task | Activity | Status |
|---|---|---|
| 1 | OpenSpec 1.14.1 installed | done |
| 2 | OpenCode 2.0.24 present | done |
| 3 | Bitwarden CLI (bws 2.1.0) | done (POC) |
| 4 | Systemd encrypted credential | done (POC) |
| 5 | Project secrets in Bitwarden | done (POC) |
| 6 | OpenSpec init in pocs/interface (delivery=commands, profile=custom) | done |
| 7 | Zero-token OpenCode setup (playbooks + qf-* wrappers + per-agent tools) | done |
| 8 | AGENTS.md (reuse-first rules) | done |
| 9 | Claude openspec/ (config, constitution, conflicts, 41 prompts) | done |
| 10 | scripts/gen_modules_index.py | done |
| 11 | 6 external skills moved to .agents/skills-disabled/ | done |
| 12 | Live /qf-doubt test passed - 11.8K current context | done |
| 13 | Commit 56a6d22, tag session3-complete | done |

**What we built:** pocs/interface/ contains opencode.json (tools.skill=false + 4 restricted agents), AGENTS.md (21 lines), scripts/gen_modules_index.py, openspec/ (config.yaml, constitution.md, conflicts-and-gaps.md, modules.md, 41 prompts), .opencode/ (9 opsx-* generated + 6 qf-* ours, 9 playbooks). Idle cost 0 tokens/message.

### SESSION 3 GOTCHAS (don't repeat)

1. opencode-triage is V1-only. No V2 lazy-skill plugin exists.
2. @devcxl/opencode-spec@0.2.0 is broken on v2.
3. @felipegenef/opencode-lazy-skills silently no-ops on v2.
4. opencode --standalone --print-logs starts a server. Never for diagnostics.
5. /context and /tokens don't exist in v2.0.24. Use the TUI sidebar.
6. @slkiser/opencode-quota works but shows cumulative (misleading). Removed.
7. OpenCode does not read project node_modules/ for plugins.
8. openspec update regenerates .opencode/commands/opsx-*.md. Never edit those.
9. delivery: commands stops OpenSpec writing openspec-* skills.
10. Config merge is additive (global harness + project).
11. Agent frontmatter (agent: qf-build) is respected on v2.0.24.
12. MCP tools bypass per-agent restrictions. Block by explicit name.
13. MiMo free model over-explores. qf-doubt.md patched with tool budget.


### POC Transport — <span style="color:green">✅ COMPLETE (2026-10-14, tag `poc-transport-complete`)</span>

All 5 gates pass. Muse → Cloudflare edge → WAF → Tunnel → origin `127.0.0.1:8765` → `X-Api-Key` gate → `hello` tool → back to Muse. Matching `response_id=e7049263-c532-495c-83df-9fa266ac7acd`.

---

## CHANGELOG

| Version | Date | Changes |
|---|---|---|
| 3.3 | 2026-10-15 | Session 3 closed. Zero-token OpenCode+OpenSpec delivered. Gotchas recorded. |
| 3.2 | 2026-10-14 | Session 2 closed. Tech stack updated with actual installed versions (Node 24.22.0, uv 0.13.1, OpenSpec 1.14.1, OpenCode 2.0.24, Python 3.14.7). ADR-004 added. RQ-007 merged into main conflict table. Session 3 in progress. |
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

## SESSION 2 — Repository, Toolchain, Design Freeze — <span style="color:green">✅ COMPLETE</span>

**Completed:** 2026-10-14

### Task 1 — LUKS Header Backup <span style="color:green">✅</span>
Header (16 MB) GPG-AES256 encrypted with random 32-char passphrase. SHA-256 `c1b236d92af2382734ebb6aa5acc9364a40c6f24b0ddf3a58bed0ffafaf33da6`. Uploaded to MEGA. Local temp shredded. Bitwarden updated.

### Task 2 — User Reconciliation <span style="color:green">✅</span>
| Name | UID | GID | Purpose |
|---|---|---|---|
| `quantflow` group | — | 986 | shared group |
| `quant` | 997 | 986 | SQLite writer, holds BWS token |
| `quant-cap` | 995 | 65534 | capture, NO `/data` write, no token |
| `quant-rhythm` | 994 | 986 | scheduler, no token |

### Task 3 — Directory Reconciliation <span style="color:green">✅</span>
`/data` and `/var/quant` created with `quant:quantflow 2770`.

### Task 4 — ADRs <span style="color:green">✅</span>
- `docs/architecture/adr/ADR-001-anti-detection-scope.md` — Option A (authorized session management)
- `docs/architecture/adr/ADR-002-no-containers.md`
- `docs/architecture/adr/ADR-003-python-version.md`
- `docs/architecture/adr/ADR-004-mcp-sdk-version.md` (Proposed — decision deferred)

### Task 5 — Freeze Design Bundle <span style="color:green">✅</span>
11 files in `docs/reference/release-v2.0.5.1-v5.1.5.1/`. `SHA256SUMS` verified. `docs/reference/CURRENT` symlink. Committed.

### Task 6 — Repo + `.gitignore` First <span style="color:green">✅</span>
Repo at `~/src/quant-flow-system`. `.gitignore` committed first (`a0cee76`).

### Task 7 — Folder Structure <span style="color:green">✅</span>
Top-level dirs: `config`, `docs`, `fixtures`, `migrations`, `scripts`, `specs`, `src`, `systemd`, `templates`, `tests`, `tools`. `src/quantflow/` with subpackages. Committed `f640d85`.

### Task 8 — uv + Python 3.14 + Foundation Deps <span style="color:green">✅</span>
Python 3.14.7, uv 0.13.1. All foundation deps installed and locked. `mcp==1.30.0` pinned. `PyJWT[crypto]` and `pandas-market-calendars` added.

### Task 9 — `pyproject.toml` Tool Config <span style="color:green">✅</span>
Ruff (target py314, per-file ignore `tests/**` for S101), mypy (Python 3.14, strict, POC adapter overrides), pytest, coverage configured. `ruff`, `mypy`, `pytest` all green.

### Task 10 — Commit + Tag <span style="color:green">✅</span>
Tag `foundation-complete`. Commits `bff035a`, `2ce33ea`, and follow-ups.

### Task 11 — Boot Auto-Mount <span style="color:green">✅ deferred (accepted)</span>
If SABRENT unplugged at boot, manual `sudo mount /data` needed. Accepted as known behavior.

---

## SESSION 3 — SDD Toolchain, Bitwarden, Feature 005 — COMPLETE (2026-10-15, tag `session3-complete`)

| Task | Activity | Status |
|---|---|---|
| 1 | OpenSpec 1.14.1 installed | done |
| 2 | OpenCode 2.0.24 present | done |
| 3 | Bitwarden CLI (bws 2.1.0) | done (POC) |
| 4 | Systemd encrypted credential | done (POC) |
| 5 | Project secrets in Bitwarden | done (POC) |
| 6 | OpenSpec init in pocs/interface (delivery=commands, profile=custom) | done |
| 7 | Zero-token OpenCode setup (playbooks + qf-* wrappers + per-agent tools) | done |
| 8 | AGENTS.md (reuse-first rules) | done |
| 9 | Claude's openspec/ (config, constitution, conflicts, 41 prompts) | done |
| 10 | scripts/gen_modules_index.py | done |
| 11 | 6 external skills moved to .agents/skills-disabled/ | done |
| 12 | Live /qf-doubt test passed - 11.8K current context | done |
| 13 | Commit 56a6d22, tag session3-complete | done |

### What we built

pocs/interface/
├── opencode.json # tools.skill=false + 4 restricted agents
├── AGENTS.md # 21 lines, every message
├── scripts/gen_modules_index.py
├── openspec/
│ ├── config.yaml
│ ├── constitution.md
│ ├── conflicts-and-gaps.md
│ ├── modules.md
│ ├── prompts/ # 41 feature briefs
│ └── changes/ and specs/
└── .opencode/
├── commands/ # 9 opsx-* (generated) + 6 qf-* (ours)
└── playbooks/ # 9 playbooks, NOT scanned by OpenCode
text


### Per-agent tool restrictions

| Agent | Enabled | Denied |
|---|---|---|
| qf-plan | read, glob, grep, write, edit | bash, task, webfetch, websearch |
| qf-build | read, write, edit, bash, glob, grep, todowrite/read | task, webfetch, websearch |
| qf-review | read, glob, grep | write, edit, bash, task |
| qf-doubt | read, glob, grep | write, edit, bash, task |

### qf-* wrapper routing

| Command | Agent | Playbooks |
|---|---|---|
| /qf-propose @openspec/prompts/NNN-*.md | qf-plan | 09 + constitution + conflicts + modules |
| /qf-apply <change> group N | qf-build | 01, 02, 03, 04 |
| /qf-kernel <change> | qf-build | 01, 04, 08 |
| /qf-migrate <change> | qf-build | 04, 07 + conflicts |
| /qf-review | qf-review | 05, 06 |
| /qf-doubt <question> | qf-doubt | 06 (tool budget: max 2 calls) |

**Idle cost: 0 tokens/message.** Verified live: 11.8K current context after a full `/qf-doubt` run.

### SESSION 3 GOTCHAS (don't repeat)

1. opencode-triage is V1-only. No V2 lazy-skill plugin exists as of 2026-10-15.
2. @devcxl/opencode-spec@0.2.0 is broken on v2 (V1-shaped plugin API).
3. @felipegenef/opencode-lazy-skills silently no-ops on v2.
4. opencode --standalone --print-logs starts a server. Never for diagnostics.
5. /context and /tokens don't exist in v2.0.24. Use the TUI sidebar.
6. @slkiser/opencode-quota works but shows cumulative (misleading). Removed.
7. OpenCode does not read project node_modules/ for plugins.
8. openspec update regenerates .opencode/commands/opsx-*.md. Never edit those.
9. delivery: commands stops OpenSpec writing openspec-* skills.
10. Config merge is additive (global harness + project).
11. Agent frontmatter (agent: qf-build) is respected on v2.0.24.
12. MCP tools bypass per-agent restrictions. Block by explicit name.
13. MiMo free model over-explores. qf-doubt.md patched with tool budget.

---


SESSION 4–5 — Feature 005: Domain Types, Units, and Clock

Feature 005 — Purpose. Establish the canonical type system, unit system, and clock discipline that all downstream code depends on. Nothing else can be built correctly until this is frozen.

Deliverables.

    Typed enums (as Python StrEnum or Literal aliases): ClusterGrade, ClusterState, EpisodeState, DTELane (0DTE, 1DTE, TACTICAL_2DTE, SHORT_TACTICAL, SWING, LONGER_HORIZON), DecisionState (12 values), ProviderState (9 values), Coverage (COMPLETE/PARTIAL/MANUAL_ONLY/UNKNOWN), DQGrade (A/B/C/D/F), NotificationDomain (SYSTEM/TACTICAL/RESEARCH), NotificationUrgency, NotificationState (open/resolved/expired), EvidenceTier (1–4), LeadLagClass, StructureSignature (25 entries per SPEC Vol 3 §10.4).

    Unit types for money and price: Cents, Micros, Mills — with explicit constructors that reject mixing. All decision-path money uses integer minor units; _cents for option prices, _micros for underlying/index spot, _mills for strikes and levels.

    Clock module: utc_epoch_ms() (business timestamps), jwt_seconds() (JWT convention), TradingCalendar wrapper over pandas-market-calendars for regular sessions, half-days, holidays, and per-instrument close/last_trade_at. Half-day and holiday handling per SPEC Vol 3 §9.6 and ARCH Vol 4 §AH.5.

    Canonical scope key format per ARCH Vol 1 §AI.19: "kind=<k>|target=<t>|route=<r>|lane=<l>|horizon=<h>", alphabetical, lowercase, _ANY for missing, ≤200 chars, reject non-canonical strings.

    RQ-004 fix applied: three disjoint vocabularies, no state ever named BASIC.

Dependencies. None. This is the first real code feature.

Tests.

    Golden: valid enum construction; invalid values raise ValueError.

    Boundary: unit conversion exactness (mills = micros // 1000, micros = mills * 1000) with rounding rules.

    Sign/unit: cannot add Cents to Micros; mypy strict rejects at compile time.

    Clock: utc_epoch_ms() monotonic, jwt_seconds() returns int seconds.

    Trading calendar: regular day, half-day, holiday, last_trade_at per instrument.

    Scope key: round-trip canonical, reject unordered fields, reject >200 chars.

    Property: enum membership is closed; unknown value fails closed.

    No-future-leakage: calendar lookups never return future session data.

    Reproducibility: same input → same output byte-for-byte.

    Coverage ≥95% for src/quantflow/domain/.

Exit. All tests pass. ruff, mypy --strict clean. Tag feature-005-complete. Merge to main.
SESSION 6 — Feature 010: Migration Runner (E1)

Feature 010 — Purpose. A forward-only, checksum-verified migration runner for both stores (SQLite quant_state.db and DuckDB quant_flow.duckdb), with fresh-install and upgrade paths, per SPEC Vol 2 §19.1 and ARCH Vol 2 §C.3.

Deliverables.

    migrations/sqlite/ and migrations/duckdb/ directories. A baseline 000_baseline_v2.0.5.1.sql per store that combines the final v2.0.5.1 schema through SQLite 069 / DuckDB 041. Historical upgrade migrations 001–064 (SQLite) and 001–037 (DuckDB) folded into the baseline.

    Real applied migrations SQLite 057–070, DuckDB 033–042 as immutable files with SHA-256 in a manifest.

    schema_version_sqlite / schema_version_duckdb tables recording migration_id, checksum, applied_at, app_version, result.

    Runner that (a) applies 000_baseline once on fresh installs, (b) computes pending = enabled_manifest_ids - baseline_covered_ids - applied_ids, (c) validates dependency closure and checksums, (d) executes a stable topological ordering, (e) never uses MAX(migration_id), (f) refuses to edit applied migrations.

    Reserved-but-not-applied slots: SQLite 071 (proposed core repair), 072–079; DuckDB 043–045 (AE/AF/AG research), 046–049 (future), 050 (proposed core repair).

Dependencies. Feature 005.

Tests.

    Fresh install → schema matches baseline hash.

    Upgrade from simulated prior state → all pending applied in order.

    Checksum mismatch on an applied migration → abort with clear error.

    Duplicate migration ID → abort.

    Reapplying an already-applied migration → no-op.

    Reserved numbers (043–045) NOT auto-applied on fresh install.

    AF 044 adopted before AE 043 → later adoption still applies 043.

    schema_version_* row written exactly once per migration with correct result.

    Failure mid-migration → transaction rollback, result=FAILED, clear report.

    Migration files hash identically to manifest entries.

Exit. All tests pass. Fresh and upgrade paths produce identical schemas for identical module sets. Commit and tag feature-010-complete.
SESSION 7 — Feature 011: SQLite Repositories (E1)

Feature 011 — Purpose. A single-writer, WAL-mode, bounded-pool repository layer for quant_state.db that all SQLite access flows through. No component opens a raw SQLite connection.

Deliverables.

    Connection manager with journal_mode=WAL, synchronous=NORMAL, cache_size=-16000, temp_store=MEMORY, mmap_size=268435456, foreign_keys=ON, busy_timeout=5000.

    WAL checkpoint policy: PRAGMA wal_checkpoint(TRUNCATE) at low-activity session breaks and when quant_state.db-wal exceeds WAL_SIZE_CEILING_MB = 50.

    Single writer task serialized via asyncio queue. Only quantd owns this.

    Bounded reader pool for read-only queries from observability and Muse tools.

    Repository classes per table group (all SQLite operational tables per SPEC Vol 2 §19.2).

    Immutable-row helpers: insert_once, append, never_update guards on append-only tables.

Dependencies. Feature 010 (schema exists).

Tests.

    Contract per repository: create, read, list, delete (where allowed) round-trip.

    WAL mode confirmed at startup; checkpoint truncates.

    Single-writer concurrency test: 100 concurrent insert tasks serialize correctly, all rows land.

    Reader pool under load: 50 concurrent reads while writer runs, no SQLITE_BUSY.

    Foreign key enforcement: bad FK insert raises IntegrityError.

    CHECK constraints enforced: negative bid_cents, ask < bid, singleton portfolio_state_current violation all rejected.

    Immutability: update/delete on append-only table raises.

    Restart safety: reopen DB after unclean shutdown, WAL replay consistent.

    Half-open transaction rollback: exception mid-tx → no partial writes.

    No reads/writes outside /data/quant_state.db in tests (temp paths only).

Exit. All tests pass. Tag feature-011-complete.
SESSION 8 — Feature 012: DuckDB Repositories (E1)

Feature 012 — Purpose. A bounded-executor, single-writer analytical layer for quant_flow.duckdb. All writes go through db_pool_executor; the asyncio event loop is never blocked.

Deliverables.

    Connection with memory_limit='1.2GB', threads=2, temp_directory='/data/duckdb_tmp'.

    Repository classes per analytical table (all DuckDB tables per SPEC Vol 2 §19.3).

    No native TIMESTAMP columns — epoch-ms as BIGINT everywhere, enforced by a schema test.

    pending_ledger_sync and pending_exit_sync drain to DuckDB asynchronously with idempotent IDs.

Dependencies. Feature 010.

Tests.

    Contract per repository.

    Bounded executor: a slow analytical query does not stall an asyncio tick.

    No TIMESTAMP in DDL — schema scan rejects.

    Epoch-ms columns are BIGINT.

    Memory cap enforced: oversized query aborts cleanly.

    Temp dir is /data/duckdb_tmp.

    pending_ledger_sync drain idempotent: replay does not duplicate.

    pending_exit_sync mirror: crash before ACK → retry succeeds, no duplicate.

    Outage: DuckDB unavailable → SQLite state retained, queue grows, no data loss.

    Schema hash matches SPEC Vol 2 §19.3 after whitespace normalization.

Exit. All tests pass. Tag feature-012-complete.
SESSION 9 — Feature 013: Writer Queue and Outbox (E1)

Feature 013 — Purpose. A durable, bounded writer queue that guarantees at-least-once delivery of state transitions from the fast path to both stores, plus the delivery_outbox state machine for notification channels.

Deliverables.

    Bounded asyncio.Queue for state transitions with backpressure.

    delivery_outbox state machine per ARCH Vol 1 §N.11: pending → in_progress → delivered | failed | exhausted.

    Backoff schedule 30s → 60s → 120s → 300s → 900s, max 6 attempts.

    Fatal classification: 5xx / timeout / connection → retry; 4xx / auth / malformed → exhausted immediately, fatal_delivery_error=1, delivery-channel-degraded notification.

    pending_ledger_sync and pending_exit_sync per SPEC Vol 5 §O.11 and ARCH Vol 4 §AH.6.3.

    Idempotency keys: every enqueue uses a dedup_key persisted in persistent_idempotency with TTL 7 days.

Dependencies. Features 011, 012.

Tests.

    Enqueue → process → ack flow happy path.

    Bounded queue: 10k enqueue at 1k processing rate → queue fills, producers block, no OOM.

    Restart with in_progress rows → reset to pending after lock expiry.

    Idempotency: same dedup_key twice → second is no-op.

    Retry backoff schedule observed.

    Fatal 4xx → exhausted immediately, fatal_delivery_error=1.

    delivery-channel-degraded fires on fatal.

    pending_ledger_sync drains after restart.

    pending_exit_sync drains after DuckDB recovery.

    Crash mid-processing → row re-claimed by next worker.

Exit. All tests pass. Tag feature-013-complete.
SESSION 10 — Feature 014: Scheduler and Rate Budgets (E1)

Feature 014 — Purpose. Async task scheduler with jittered timing, per-provider rate budgets, and OpenMarket cycle scheduling. No time.sleep() in the event loop.

Deliverables.

    scheduled_tasks state machine: PENDING → RUNNING → DONE | FAILED. Partial unique index on dedup_key where state IN (PENDING, RUNNING).

    Task types: nightly backup, T+1 OI job, DQ report, adversarial harness, SPX pre-market setup (μ = 06:45 ET, σ = 15 min, [06:00, 07:00]), SPX post-close cleanup (μ = 16:45 ET, σ = 15 min, [16:30, 17:30]), canary refresh, SLO evaluator (every 5 min), escalation runner (every 15 min).

    provider_query_pool and provider_query_budget enforcement per SPEC Vol 2 §19.2 and ARCH Vol 4 §D.26: FLOW_ALERT (60%), MORNING_AD_HOC (40% shared), GLOBAL (separate). Pre-market borrow ≤ BUDGET_PREMARKET_BORROW_PCT = 20, restored at 09:30 ET. Intraday FLOW_ALERT may draw MORNING_AD_HOC only when that pool is ≥80% unspent. ZERO_DTE_CLUSTER draws from FLOW_ALERT.

    Cancellation from PENDING only; RUNNING tasks complete or fail cleanly.

    human_rhythm_scheduler state machine: offline → waking → active → deep-read → light-check → break → drifting → distracted → winding-down → offline.

Dependencies. Feature 013.

Tests.

    Task creation, run, DONE.

    Failure increments attempts, re-enqueues with backoff, eventually FAILED.

    Dedup: two PENDING with same key → second rejected.

    Cancellation from PENDING only.

    Restart: RUNNING at crash → reset to PENDING.

    No time.sleep() in any async path — AST scan of src/quantflow/ for asyncio.sleep misuse.

    Budget: pool 60/40 split enforced; borrow rules enforced; over-budget query rejected.

    SPX cycle scheduled within jitter window.

    Rate-limit reset at day boundary.

    Coverage ≥95% for src/quantflow/services/scheduler.py.

Exit. All tests pass. Tag feature-014-complete.
SESSION 11 — Feature 015: Backup and Restore Drill (E1)

Feature 015 — Purpose. Nightly backup barrier per ARCH Vol 1 §M.1 and quarterly restore drill.

Deliverables.

    Barrier sequence: pause capture intake → drain pending_ledger_sync + in-flight outbox → PRAGMA wal_checkpoint(TRUNCATE) → close DuckDB cleanly → copy both files → verify SHA-256 → reopen → resume capture → rclone to encrypted offsite → log duration.

    Silent on success; always notify on failure.

    30-day retention.

    Quarterly restore drill: download artifact → decrypt → verify SHA-256 → restore to scratch → open both stores → row-count + checksum spot checks → record duration → notify → log in operator_control_audit.

    RTO target ≤ 4 hours.

Dependencies. Features 011, 012, 013.

Tests.

    Barrier happy path: both files copied, checksums match.

    Failure during copy → notification, no partial backup retained.

    Restore drill: scratch restore opens, spot checks pass.

    Retention: 31 days → oldest pruned.

    rclone failure → local backup retained, notification raised.

    Barrier interruption → resume protocol works.

    Restore RTO measured ≤ 4h in simulated run.

    Offsite copy verified by SHA-256.

    Notification fires on any failure path.

    No production data read from /data in tests — temp paths only.

Exit. All tests pass. docs/reports/phase-1-gate.md written. E1 gate cleared. Tag feature-015-complete.
E1 GATE

    □

    Full test suite green
    □

    Every E1 feature converged
    □

    Synthetic epic integration scenario passes
    □

    No P0/P1 deferred without ADR
    □

    docs/reports/phase-1-gate.md committed

SESSIONS 12–14 — E2 Canonical Event Pipeline
Feature 020 — Ingestion Adapters

Per SPEC Vol 2 §4, §5. Raw event archive (immutable, append-only, hash-verified). Provider adapters load into raw_provider_events with payload_hash, parser_version, schema_version, access_channel, authorization_id, source_trace_id. Capture emits provider-observation-submitted IPC events per SPEC Vol 1 §2.3.9. Capture prunes spool after quantd ACK.
Feature 021 — Canonicalizer and Dedup

Per SPEC Vol 2 §5. canonical_events with event-time NBBO preserved. Dedup fingerprint priority: exchange_execution_id → provider_event_id → content hash. canonical_event_sources bridges sources without double-counting. canonical_event_relationships records INDEPENDENT_REPEATED_FLOW, RELATED_CLUSTER, SAME_THESIS_UPDATE, SUPERSEDES. Corrections and out-of-sequence events recorded with correction_status.
Feature 022 — Data Quality Gateway

Per SPEC Vol 2 §6. Grades A/B/C/D/F. Checks: freshness, staleness, source conflict, greek sign, spread width, coverage, canary agreement. Quote rejection reasons: stale, crossed, wide, size zero, malformed, unknown source. Coverage caps applied inside weighted sum: PARTIAL 0.70, MANUAL_ONLY 0.50, UNKNOWN 0.00.
Feature 023 — Candidate Engine and Symbol Filter

Per SPEC Vol 1 §7. Pre-screen scoring order: dedup → quality → candidate score. Shadow sampling per §7.4. Default symbol_filter rows pinned per §7.6, including the ZERO_DTE_CLUSTER scope that includes equities and SPX, excludes ETFs and other indexes. Corporate action hard gate: PENDING for a ticker blocks flow alerts.
Feature 024 — Corporate Actions and Backfill

Per SPEC Vol 2 §4.9. Daily ingestion → corporate_action_ingestion. Adjusted contracts tagged with new corporate_action_ver, cached greeks and dealer data invalidated. Backfill job per backfill_log.

E2 gate. Full pipeline from raw → canonical → DQ → candidate → filter tested with synthetic fixtures. phase-2-gate.md.
SESSIONS 15–22 — E3 Pure Quant Kernels

Pure, deterministic, side-effect-free kernels. Coverage ≥95% mandatory.
Feature 030 — Delta-Gamma-Theta-IV Decomposition

Per ARCH Vol 4 §D.3. Unit contract: option price dollars, delta-spot dollars, gamma per (1move)2,thetaperday,vegapervolpoint.‘Δσimpl,volpt=(ΔP1move)2,thetaperday,vegapervolpoint.‘Δσi​mpl,volpt=(ΔP − Δ·ΔS−½⋅Γ⋅(ΔS−½⋅Γ⋅(ΔS)² − Θ/day⋅Δtdays)/V/day⋅Δtd​ays)/V/volpt`.
Feature 031 — PayoffKernel

Per ARCH Vol 4 §D.5. Separates exact contractual risk from the finite scenario grid. Endpoint test at x=0 and every strike; upper-tail slope for unbounded loss/profit detection. risk_status=FINITE required for sizing. scenario_worst_loss_cents is diagnostic-only. Golden: short $100 put, credit $200, multiplier 100 → max loss $9,800 at x=0, not $8,800 at x=$10.
Feature 032 — Position Sizing

Per ARCH Vol 4 §D.6. Lane parameterization: TACTICAL_2DTE max_risk_pct_equity=0.005; otherwise BASE_RISK_PCT=0.0075. risk_per_package_cents = max_risk_per_package_cents + risk_cost_allowance_cents. Both inputs from D.5. Missing/unbounded/zero-risk → no size.
Feature 033 — FDI (Delta-Weighted Flow Imbalance)

Per ARCH Vol 4 §D.25. S_i_dollars = S_i_micros / 1,000,000. D_i = Σ_j s_ij · Δ_ij · Q_ij · M_ij · S_i_dollars. FDI_t = Σ_i q_i·D_i / Σ_i q_i·|D_i|.
Feature 034 — Dealer Hedging Pressure

Per ARCH Vol 4 §D.21. H_$ = -(gamma_flow_$per1pct × ΔS_pct + vanna_flow_$pervolpt × ΔIV_volpt + charm_flow_$perday × Δt_days). H_signed = H_$ / ADV_$. Opposing → EV_lower -= HEDGE_PENALTY_DEFAULT × H_magnitude. Single application only.
Feature 035 — Flow Strength and Confluence

Per ARCH Vol 4 §D.14b. X_k sums signed leg deltas. B = Σ max(X_k, 0), R = Σ max(-X_k, 0). OpposingShare = min(B,R)/(B+R). DirectionalStrength = 1 − 2·OpposingShare. FlowStrength = w_Delta·P_Delta + w_Premium·P_premium + w_Direction·D_s + w_Events·E_s + w_Strikes·K_s. ConfluenceScore = 0.65·F + 0.25·D_c + 0.10·P_c.
Feature 036 — SPX Crossing State Machine

Per SPEC Vol 3 §9.6 and ARCH Vol 4 §AD. States: FAR, APPROACHING, TESTING, CONFIRMED_BREAKOUT, CONFIRMED_REVERSAL, FALSE_CROSS, COOLDOWN, REARMED, INVALIDATED. Hysteresis: retreat threshold SPX_APPROACHING_RETREAT_PCT=0.005 strictly greater than entry SPX_APPROACHING_PCT=0.003. Intraday confirmation via 1-min bar close + 60s hold. Close-of-day resolution to COOLDOWN.

E3 gate. Every kernel ≥95% coverage. Property tests for algebraic invariants (sign symmetry, zero-detection, boundary-mass). phase-3-gate.md.
SESSIONS 23–26 — E4 Decision Evidence and Delivery
Feature 040 — AnalysisSnapshotBuilder

Per SPEC Vol 1 §2.9 and ARCH Vol 4 §S. Pure with respect to inputs. No wall-clock reads except as_of. No random draws outside as_of-seeded PRNG. Same inputs + versions → byte-identical. No external mutation, no provider calls. AST lint rejects fetch_*, get_current_*, read_pointer_* in builder body. signal_valid predicate per SPEC Vol 3 §8.1a.
Feature 041 — Decision State Selection and Signal Ledger

Per SPEC Vol 3 §8.4. Order: external facts → DQ gate → signal validity → evaluated outcomes. signal_versions written on material change. signal_ledger (DuckDB) records full decision evidence. Route selection: long-call, long-put, short-put, debit-spread, spread-specific. Route undefined → WATCH.
Feature 042 — Notification Delivery and Outbox

Per SPEC Vol 4 §16 and ARCH Vol 4 §G. Channels: Discord, Resend (primary email), Mailgun (fallback), Muse. Categories per SPEC Vol 4 §18.14. Cooldowns per-category. delivery_outbox from Feature 013 drives delivery. All-fail readable. Muse reads the table only.

E4 gate. First synthetic end-to-end fixture passes: canonical event → DQ → candidate → enrichment → snapshot → decision → notification → delivered. phase-4-gate.md.
SESSIONS 27–32 — E5 Provider Adapters
Feature 050 — LivePriceProviderAdapter

Per ARCH Vol 4 §P. Source priority: listed-option underlying, official index, then authorized free sources. Quality flags per observation. Basis discipline per SPEC Vol 3 §9.7. BASIS_TOLERANCE_BPS=15. Prior session close is not a basis reference.
Feature 051 — ListedOptionQuoteAdapter

Per ARCH Vol 4 §AC. Interface: get_quote(contract_id) and get_package_quote(legs) → immutable observation IDs. Quality: bid ≥ 0, ask ≥ bid, spread and freshness within lane limits. Fallback to VALIDATED_PENDING_ENTRY or WATCH. RQ-005 must be resolved before this: package_quote_observation_id at evidence boundaries per SPEC Vol 2 §19.6 invariant AM.
Feature 052 — Provider Capture Worker (phantomime)

Per ARCH Vol 3. Custom CDP client wrapping real Google Chrome stable, headed under Xvfb. Not Playwright, not Puppeteer. Per-profile persistent user_data_dir. Dependency-import lint rejects playwright and puppeteer. Session lifecycle per ARCH Vol 3 §E. Session rhythm per §E.6–§E.10. challenge-detected IPC event per ARCH Vol 1 §B.3. ADR-001 governs 052.
Feature 053 — Provider State Machine and Loopback Echo

Per ARCH Vol 3 §F.N. States: HEALTHY, DEGRADED, CHALLENGED, MANUAL_REQUIRED, BLOCKED, COOLDOWN, AUTH_REQUIRED, SCHEMA_CHANGED, DISABLED. Loopback echo at echo.quant.internal:9443 inside capture netns per §F.D.1 and §F.S.4. TLS 1.3 preferred, 1.2 accepted, ALPN ["h2","http/1.1"], real TLS cert.
Feature 054 — Stock-Chrome Probe Environment

Per ARCH Vol 3 §F.U.2. Continuous stock Chrome against provider public endpoints. Jittered cadence 15 min [12, 18]. Own namespace, own egress, own source_authorization entry, separate Chrome user_data_dir. Single-machine fingerprint linkage decision per ARCH Vol 1 §AI.22.

E5 gate. All anti-detection checks pass per ARCH Vol 3 §F.Q (84 + 18 tests). phase-5-gate.md.
SESSIONS 33–38 — E6 User Workflows
Feature 060 — Real-Time Flow Alert

Per SPEC Vol 1 §2.14. Trigger: canonical event passes quality + candidate. Provider status mapping per §2.14.2. Unknown mapping fails closed. Renders to Discord + email.
Feature 061 — 0DTE Cluster Detection

Per SPEC Vol 1 §2.20.7. Two tiers: MEDIUM_CONFLUENCE (immediate Discord + email) and HIGH_CONFLUENCE (immediate upgrade). Basic cluster silent. RQ-003 must be resolved before 061: 0DTE identity. episode_id = sha256(ticker | expiration | direction | first_qualifying_canonical_event_id | ruleset_version)[:32]. No route, no size, no ACTIONABLE_NOW.
Feature 062 — Morning Action Brief

Per SPEC Vol 1 §2.15. Sections A–J: Decision Summary, Market Playbook, Carryover Thesis Board, 2DTE and Expiration-Risk Board, Portfolio and Capacity, Prior-Day Audit (with Prior-Day 0DTE Research), Event and No-Trade Calendar, Data and System Health, Dealer Level Map, Moving-Average Stack.
Feature 063 — Ad Hoc Symbol Report

Per SPEC Vol 1 §2.16. On-demand per-symbol report. Dealer-context section (E) includes any active or recent 0DTE cluster for the ticker.
Feature 064 — Daily SPX Price Alert Cycle

Per SPEC Vol 4 §18.19. Pre-market setup at μ = 06:45 ET, σ = 15 min, [06:00, 07:00]. Post-close cleanup at μ = 16:45 ET, σ = 15 min, [16:30, 17:30]. Alert spec: SPX, max 4 (2 upside + 2 downside, one may be flip). One-shot. Newsletter timeout clock: 06:15 ET. Verification window opens at setup completion, closes at 07:30 ET. Behavioral reference operator_routine records 06:45/16:45 acceptance.

E6 gate. All three workflows produce identical decisions from the same snapshot (analysis_snapshot_id → same decision). phase-6-gate.md.
SESSIONS 39–44 — E7 Interface, Ops, Release
Feature 070 — Muse MCP Interface (extends POC)

Head start from POC: transport path proven, api_key.py and server.py working, Cloudflare state persists, Bitwarden state persists.

Must add:

    Replace POC_API_KEY with a production API key.

    Extend server.py with real read-only tools per SPEC Vol 5 §O.3.

    Role checks behind MUSE_ADMIN (reserved in v2.0.5.1; gated).

    Cache TTLs per SPEC Vol 5 §O.3.4.

    Move mcp_probe.py to tests/integration/.

    Evaluate RQ-007: if MCP SDK v2.2.0 migration is chosen here, do it as part of the same rewrite. If not, keep v1.30.0.

Feature 071 — Health Endpoint and Observability Sidecar

Per SPEC Vol 5 §O.2. FastAPI or aiohttp inside quantd as asyncio task, localhost:8091. GET /health full snapshot, GET /health/{component}, GET /metrics. Response schema per §O.2.3. overall computation per §O.2.4. Timeouts 200ms p95.
Feature 072 — Log Persistence, Correlation IDs, and SLOs

Per SPEC Vol 5 §O.5, §O.6, §O.8. journald configuration, structured JSON logs, redaction at emit. source_trace_id + canonical_trace_id + session_id + task_id + report_id. SLO targets per §O.8.2. slo_measurements DuckDB table.
Feature 073 — Alerting Tiers and Escalation

Per SPEC Vol 5 §O.7. Tiers: critical, immediate, warning, informational, daily. Escalation: SYSTEM + requires_ack=1 + unacknowledged → re-emit. Per-step reservation via persistent_idempotency. Root-aware, idempotent. Finite ladder per §O.7.4. Runs every 15 min.
Feature 074 — Daily Status Summary and Dashboards

Per SPEC Vol 5 §O.9. Emitted at 08:00 ET daily via scheduled_tasks, idempotent on (category='system-status-summary', subject_key=today). Content per §O.9.2. Dashboard views v1 driven by Muse tools.

E7 gate. Full acceptance suite passes. phase-7-gate.md = RESEARCH RELEASE.
SESSIONS 45+ — E8 Forward Research
Feature 080 — Outcome Collection (Phase B)

Per SPEC Vol 6 §F.3. Sustained outcome collection across all live lanes. Scope gate: N_scope >= max(300, 20 * p), at least 75 positive and 75 negative outcomes per scope. Per-scope arrival-rate estimates 3–18 months per SPEC Vol 3 §14.19.8a.
Feature 081 — Minimal ML Challenger (Phase C)

Per SPEC Vol 6 §F.4. LOGISTIC_L2 with 10–12 structured features. Chronological walk-forward. Pure local function. CHALLENGER only — no decision-path reachability. model_predictions table reserved (DuckDB 046).
Feature 082 — Promote Only on Demonstrated Improvement (Phase D)

Per SPEC Vol 6 §F.5. Promotion requires: better Brier, better log loss, no worse calibration, better precision at same volume, lower FPs, 3 consecutive walk-forward windows, no regime failures, flow/dealer ablation shows value, replay integrity. active_model_manifest.model_role = CHAMPION workflow with full audit.

E8 gate. phase-8-gate.md.
ARCH BUILD SEQUENCE MAPPING
Runbook phase	ARCH Stage
E0	Stage 0 — Pre-Code Setup
E1	Stage 2 — Storage & Delivery
E2	Stage 1/2 — Kernels + Storage
E3	Stage 1 — Kernels
E4	Stage 2.1–2.3 + Stage 3.2
E5	Stage 2.4–2.5 + Stage 3 — First Source
E6	Stage 3.1–3.4
E7	Stage 2.6–2.7 + Stage 5
E8	Stage 4 + SPEC Vol 6 / Vol 7
THREE-ENVIRONMENT WORKFLOW

DEV (Lenovo Mint on USB). VS Code + Remote SSH to PROD. OpenCode + OpenSpec here, never PROD. No runtime secrets. Author, test, review. Deploy deliberately.

PROD (Ubuntu Server). Runs quantd, provider_capture_worker, human_rhythm_scheduler, observability sidecar. Owns only writer to SQLite + DuckDB. Never runs AI agents.

DB (Debian 13). /data LUKS + ext4. quant_state.db (WAL) + quant_flow.duckdb. Only owner writes. Never over network for writes.
DAILY PRACTICE

Start:
bash

cd ~/src/quant-flow-system
git status && git pull --ff-only
uv sync --frozen
uv run pytest -q

Pick exactly one feature or task slice.

End:
bash

uv run ruff check .
uv run mypy src
uv run pytest
git diff --check && git status --short

No uncommitted migrations. No untracked secrets.
TESTING LADDER

    Unit golden

    Property

    Contract

    Migration

    Repository

    Pipeline fixture

    Restart/idempotency

    Replay

    Workflow golden-output

    Full acceptance

    Opt-in live smoke

Rule: Never fix a failing live provider by weakening domain tests.
PER-FEATURE 10 TEST CLASSES

    Golden happy path

    Boundary/units/sign

    Missing/stale/malformed failure

    Duplicate/idempotency/restart

    Contract per port/adapter

    Migration fresh + upgrade

    Replay

    Property invariants

    No-future-leakage

    Temp paths only (never /data)

Coverage ≥95% for src/quantflow/kernels/** and src/quantflow/domain/**.
OPEN DESIGN CONFLICTS
RQ	Resolution	Deadline
RQ-002	signal_valid ordering	Before 037
RQ-003	0DTE identity	Before 061
RQ-004	grade/state/episode split	Before baseline migration freeze (005)
RQ-005	package_quote_observation_id at evidence boundaries	Before 040/051
RQ-006	"Per prior" placeholders	Per feature at clarify
RQ-007	MCP SDK v1.30.0 → v2.2.0 migration (FastMCP→MCPServer, camelCase→snake_case, httpx→httpx2, streamablehttp_client removal, McpError→MCPError). Decide via ADR-004.	Before Feature 070

C13 — DEALER POSITIONING (DEFERRED IMPLEMENTATION)

Plan: openspec/c13-dealer-positioning-implementation-plan.md
Status: PROPOSED -- operator approval pending
Blocks: Feature 033 (FDI), Feature 034 (Dealer Hedging Pressure),
        Feature 035 (Flow Strength and Confluence),
        Feature 041 (Decision State Selection),
        and any downstream kernel that consumes dealer gamma,
        dealer sign, or aggressor classification.

Gate before implementing any blocked feature:

  Stage A -- Design and contract verification
    C13-01 baseline sign model (OI_NAIVE)
    C13-03 model independence and disagreement semantics
    C13-04 source fields and provenance matrix
    Existing evaluation protocol and Q6 review
    Operator approves proposed design changes

  Stage B -- Guardrails
    C13-05 estimator approval boundary
    C13-07 AST/static enforcement with CI negative and positive fixtures

  Then Stage C (shadow logging) and Stage D (model research)

Why gated:

  Constitution line 38 forbids generating a baseline from the patched
  final DDL. Feature 034's H_$ formula depends on dealer gamma and sign
  conventions defined in C13-01. Building 034 before those contracts
  exist risks silently adopting an unapproved estimator and
  contaminating the decision path.

Do NOT implement any new dealer positioning estimator, numerical
constant, or 0DTE override until the corresponding C13 stage has been
approved by the operator.

Reference:
  Plan file: openspec/c13-dealer-positioning-implementation-plan.md
  Linked from: openspec/conflicts-and-gaps.md (## C13 section)
  Related: Q6 in conflicts-and-gaps.md (approval-pending constant
  enforcement; 005c shipped approved() + AST scan -- C13-05 builds
  on that primitive)

ABSOLUTE PROHIBITIONS

    time.sleep() in async

    Unbounded queries/arrays/logs/tasks

    Secrets/DBs/payloads/sessions/screenshots in Git

    SQL/shell/URL/secret/order/migration tools in MCP

    LLM in the decision path

    Autonomous orders

    Undocumented provider endpoints

    Silent defaults for missing evidence

    Provider logic in kernels

    Editing applied migrations

    Archived designs over CURRENT

    CAPTCHA/challenge/403 bypass

    Developing or testing against /data

    ML libraries before E8

    Anti-detection: no bypass of unauthorized source protections

    Playwright or Puppeteer anywhere in capture tree

    DoH in the capture namespace

WHEN SOMETHING FAILS

    Stop.

    Read the error carefully.

    Check the log from that step.

    Identify what changed.

    If not found in 15 minutes, roll back and retry.

    If it fails twice, do not push. Bring the exact error to the next session.

RESUME POINT — START HERE NEXT TIME

State:

    Repo clean at ~/src/quant-flow-system

    Design bundle frozen: docs/reference/CURRENT/ → 11 files, SHA256SUMS verified

    Tags: poc-transport-complete, foundation-complete

    ADR-001..004 committed

    POC primitives preserved (src/quantflow/adapters/mcp/*, src/quantflow/cli/mcp_probe.py)

    Cloudflare tunnel + Bitwarden secrets persist from POC

    Tech stack: uv 0.13.1, Python 3.14.7, Node 24.22.0, npm 11.19.1, mcp==1.30.0 pinned

    OpenSpec 1.14.1, OpenCode 2.0.24, bws 2.1.0, cloudflared 2026.10.0

    Smoke tests: 5 passed. ruff + mypy + pytest all green

Next tasks in order:

    OpenSpec init --tools opencode in pocs/interface

    git switch -c feature/005-domain-types-units-clock

    Draft Feature 005 change (proposal + design + tasks + domain spec) using the ChatGPT POC's SDD concepts

    Run /opsx-propose → human review → /opsx-apply

    Apply RQ-004 three-way enum split in Feature 005

Verify state:
bash

cd ~/src/quant-flow-system
git log --oneline | head -5
git status --short
git tag --list
readlink docs/reference/CURRENT
uv run pytest -q

POC DEFERRED FAILURE DRILLS (OPTIONAL)
#	Drill	Expected
9.1	Kill server mid-request	Muse gets transport error; no stale response
9.2	Restart server, same API key	New probe succeeds; old response_id not reused
9.3	Rotate POC_API_KEY, restart	Old key → 401; new key → pass
9.4	Stop cloudflared	Public probe fails; local probe works
9.5	Stop server, keep cloudflared	Public → 502; local refused
APPENDIX A — POC CLOUDFLARE CONFIGURATION (CARRY FORWARD)
text

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

Access app quantflow-interface: path /healthz protected; /mcp outside Access. Policies: operator (Allow/Emails) + admin-token (Service Auth/token quantflow-interface-admin). WAF "Allow MCP" skips Browser Integrity Check on /mcp. Bot Fight Mode: off.
APPENDIX B — 11-FILE DESIGN BUNDLE
text

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

APPENDIX C — LOCAL ENVIRONMENT QUIRKS

    Node.js 24 LTS is provided by NVM. .local/bin/node, .local/bin/npm, .local/bin/npx are symlinked to the v24 install; any new shell that shows nvm current → system needs .local/bin to win PATH, which it does by default.

    ~/.config/opencode/ has harness tooling on top of OpenCode v2. Any QuantFlow-specific OpenCode config should be project-scoped (~/src/quant-flow-system/opencode.json) so it layers on top of the harness config rather than overwriting it.

    ~/.config/opencode/opencode.json uses the v2 schema: providers (with package + settings, not npm + options), agents, mcp.servers. Follow this convention for any new agent/provider entries.

    ~/Downloads/lates_arch/ is the source for the 11-file design bundle. If the symlink at docs/reference/CURRENT breaks, re-copy from there and regenerate SHA256SUMS.

END OF RUNBOOK v3.2
text


Save it:

```bash
cd ~/src/quant-flow-system
nano docs/runbooks/QUANTFLOW-RUNBOOK.md
# paste the whole markdown block above, save (Ctrl+O, Enter, Ctrl+X)

git add docs/runbooks/QUANTFLOW-RUNBOOK.md
git commit -m "docs: runbook v3.2 — Session 2 closed, Session 3 in progress, actual installed versions"
git log --oneline | head -3

Then post:
bash

git log --oneline | head -3
git status --short

Session 3 next: openspec init --tools opencode in pocs/interface.

---

## APPENDIX D — CLAUDE'S PACKAGES (deferred)

Location: `~/Downloads/qf/` and `~/Downloads/qf-oc/`.
Purpose: qf/ = 41 OpenSpec feature prompts + constitution + config; qf-oc/ = 9 playbooks + 6 qf-* command wrappers.
Status: not yet installed. Will be probed feature-by-feature in Session 4+.

Outstanding conflicts to resolve before their prompts are used: C1, C3, C4, C10, C11, RQ-002..RQ-006 (see runbook §Open Design Conflicts).


---

## GITHUB REMOTE (2026-10-15)

| Item | Value |
|---|---|
| Owner | `ramsri1980-png` |
| Repo | `quant-flow-system` |
| URL | https://github.com/ramsri1980-png/quant-flow-system |
| SSH remote | `git@github.com:ramsri1980-png/quant-flow-system.git` |
| Default branch | `master` |
| Tracking branches | `master`, `chore/openspec-c12`, `feature/005-...` (pushed as created) |
| Access | SSH key at `~/.ssh/id_ed25519` registered with GitHub |
| First push | 2026-10-15, commits `c877019` (master) and `1eca93e` (chore/openspec-c12) |

**Routine commands:**

```bash
# Push current branch
git push

# Push new branch
git push -u origin <branch>

# Fetch + rebase before starting work
git fetch origin && git rebase origin/master
---

## CONVENTIONS — SAFE DOCUMENT UPDATES (2026-10-15)

Rule: never use nano, cat >> with heredocs, or manual copy-paste to modify files under docs/reference/, docs/runbooks/, 
docs/architecture/adr/, or openspec/. Use anchored Python scripts or file-based cat/cp to modify files. Heredocs collide
with EOF-like strings, pasted prompt lines corrupt bash state, and manual edits lose determinism.
### Pattern 1 — Append a section (idempotent, anchored)

```python
from pathlib import Path
p = Path("path/to/doc.md")
text = p.read_text()
if "## New Section Title" in text:
    print("already present")
else:
    insert = "\n\n## New Section Title\n\n...content...\n"
    idx = text.rfind("\nEND OF")
    text = text[:idx] + insert + text[idx:]
    p.write_text(text)
```

### Pattern 2 — Run after every `git push`

```bash
python3 scripts/update_runbook.py
```

Updates the runbook with current branch, last 10 commits, working tree status, and UTC timestamp. Idempotent.

Alias in h~/.bashrc`:

```bash
alias qfpush='git push && python3 scripts/update_runbook.py'
```

### Pattern 2b — Run after merging to master

After any merge to master, CI pushes an `Update repo index` commit
(`.github/workflows/repo-index.yml`). Your local master is then behind
origin, and a plain `qfpush` fails with "fetch first". Use `qfmerge`
instead:

    alias qfmerge='git pull --rebase --autostash origin master && qfpush'

Add it to `~/.bashrc`. Sequence after a merge:

    git merge --no-ff feature/<name> -m "merge: feature <name> complete"
    git push
    qfmerge
    git add docs/runbooks/QUANTFLOW-RUNBOOK-v3.3.md
    git commit -m "docs: runbook auto-update after feature <name> merge"
    git push

`qfmerge` is `qfpush` with a mandatory `git pull --rebase --autostash origin master`
in front. The pull is required because the repo-index workflow almost always
adds a commit between your merge push and your next local action.

### Pattern 3 — Regenerate SHA256SUMS after errata

```bash
cd docs/reference/release-v2.0.5.1-v5.1.5.1
sha256sum *.md > SHA256SUMS
sha256sum -c SHA256SUMS
```

### Pattern 4 — Verify frozen layer

```bash
git show 2ce33ea:docs/reference/release-v2.0.5.1-v5.1.5.1/ARCH_v5.1.5.1_Vol3_Capture_AntiDetection.md | sha256sum
```

Expected: `2d7a90e533196af61745bc4efd3259b7b64b519b8ec78662392b50a911285e23`

### Pattern 5 — Pre-commit verification

```bash
git diff 2ce33ea..HEAD -- docs/reference/release-v2.0.5.1-v5.1.5.1/ARCH_v5.1.5.1_Vol3_Capture_AntiDetection.md | head
(cd docs/reference/release-v2.0.5.1-v5.1.5.1 && sha256sum -c SHA256SUMS)
pgrep -af 'nano|python3' || true
```

### Pattern 6 — Pitfalls to avoid

| Pitfall | Cause | Prevention |
|---|---|---|
| `>` prompt stuck | Heredoc never terminated | Always paste full blocks; never interrupt `<<EOF` |
| `bash: sriram@...: No such file` | Pasted prompt lines as commands | Never copy the `sriram@...$` prefix |
| `syntax error near unexpected token` | Pasted `<branch>` placeholder | Use real values or quote |
| Lost runbook content | Overwrote with partial `cat >` | Always use `cat >>` from a file, or Python anchor insert |
| MANIFEST drift | Manual SHA256SUMS edit | Always regenerate with `sha256sum *.md` |
| Python triple-quote corrupted | Triple-quoted strings inside heredoc | Write content to /tmp/file with nano, install with `cp` or `cat >>` |

### Runbook auto-update - 2026-10-15T20:56:49Z

Branch: `feature/005-domain-types-units-clock`

Recent commits:
```
0659c05 docs: add frozen-layer audit pointer to ADR-001
5db02f0 spec+prompt: errata (C5/C6/C9, RFC 8785, dedup, backup) + ADR-001 amendment + anti-detection brief repairs
f3ac486 merge: C12 kit + OpenCode setup + runbook GitHub remote
6d9063b docs: record GitHub remote in runbook
1eca93e opencode: merge C12 kit at repo root
6207b98 docs: C12 dealer/greeks corrections, DuckDB 051 dealer_map_regime
c877019 docs: resolve C1 (bundle version) and C8 (column type rule)
3c645e7 prompt(005): add ChatGPT process rigor block — RESOLVED/PROPOSED/BLOCKED taxonomy, one-question-at-a-time, no silent adoption
532b5c2 docs: runbook v3.3 - Session 3 complete, gotchas recorded, full feature detail preserved
56a6d22 chore(session3): zero-token OpenCode+OpenSpec setup
```

Working tree:
```
M docs/runbooks/QUANTFLOW-RUNBOOK-v3.3.md
?? scripts/update_runbook.py
```


## SESSION 3 POST-CLOSE -- 2026-10-15

Beyond the original Session 3 scope:

- ADR-001 amended: source-scope only; ARCH Vol 3 E/F apply in full to authorized sources
- Spec errata applied: C5 (17.5), C6 (20.72), C9 (DuckDB BIGINT), RFC 8785 22.7,
  dedup 5.3, backup M.1
- Anti-detection audit: ARCH Vol 3 E/F byte-identical to freeze
  (hash 2d7a90e533196af61745bc4efd3259b7b64b519b8ec78662392b50a911285e23)
- Feature briefs 050, 052, 064 repaired (Claude had silently weakened E/F coverage)
- Claude's "drop schedule jitter" and "exclude mimicry/fingerprint" rejected
- Safe-update conventions + scripts/update_runbook.py + qfpush alias added
- Evaluation framework reviewed 2026-10-15: additive, no anti-detection impact
  (see STEPS-EVAL.md, migration DuckDB 052, brief 041b, 4 new observability categories)
- Ready for Feature 005: /qf-propose @openspec/prompts/005-domain-types-units-clock.md



### Pattern 7 -- One-shot Python heredoc for edits + commit + push

Canonical pattern for every doc change. No nano, no /tmp file, no base64.

Shape: one bash command, one Python heredoc, unique delimiter.

    cd ~/src/quant-flow-system

    python3 <<'ENDOFSCRIPT'
    from pathlib import Path
    import subprocess
    REPO = Path.home() / "src" / "quant-flow-system"
    TARGET = REPO / "docs" / "runbooks" / "SOME-FILE.md"
    BLOCK = '''
    ## New Section
    content
    '''
    # 1. read utf-8, abort on null bytes
    # 2. skip if section already present
    # 3. append at marker or EOF
    # 4. write utf-8
    # 5. git add + commit + push current branch
    print("DONE")
    ENDOFSCRIPT

Rules:
- ASCII-only content in BLOCK. Use -- not em-dash. Use E/F not the section-sign.
- Unique delimiter. Never repeat a delimiter string inside the content.
- Do not nest heredocs. If the content needs to show a heredoc, show it indented
  in prose, not as a live example -- this is why Pattern 7 exists.
- Self-verify: read_text(encoding="utf-8") catches decode errors; null byte check
  catches binary corruption before write.
- Idempotent: check if section title already in text, skip if present.
- One transaction: read, verify, write, add, commit, push all inside the script.

Banned for doc edits: nano, cat >> with heredocs, base64 -d, triple-quoted
strings inside an outer heredoc. Each failed at least once in Session 3.

### Runbook auto-update - 2026-10-15T21:13:54Z

Branch: `feature/005-domain-types-units-clock`

Recent commits:
```
2b24b5c eval: adopt pre-registered evaluation framework (docs+DDL)
17eb0be docs: add Pattern 7 to runbook conventions
28dfe5a docs: runbook v3.3 Session 3 post-close status
607cf3e docs: add safe-update conventions + reusable runbook updater
0659c05 docs: add frozen-layer audit pointer to ADR-001
5db02f0 spec+prompt: errata (C5/C6/C9, RFC 8785, dedup, backup) + ADR-001 amendment + anti-detection brief repairs
f3ac486 merge: C12 kit + OpenCode setup + runbook GitHub remote
6d9063b docs: record GitHub remote in runbook
1eca93e opencode: merge C12 kit at repo root
6207b98 docs: C12 dealer/greeks corrections, DuckDB 051 dealer_map_regime
```

Working tree:
```
(clean)
```

### Runbook auto-update - 2026-10-15T21:17:33Z

Branch: `feature/005-domain-types-units-clock`

Recent commits:
```
fb2d477 docs: runbook auto-update after eval adoption
2b24b5c eval: adopt pre-registered evaluation framework (docs+DDL)
17eb0be docs: add Pattern 7 to runbook conventions
28dfe5a docs: runbook v3.3 Session 3 post-close status
607cf3e docs: add safe-update conventions + reusable runbook updater
0659c05 docs: add frozen-layer audit pointer to ADR-001
5db02f0 spec+prompt: errata (C5/C6/C9, RFC 8785, dedup, backup) + ADR-001 amendment + anti-detection brief repairs
f3ac486 merge: C12 kit + OpenCode setup + runbook GitHub remote
6d9063b docs: record GitHub remote in runbook
1eca93e opencode: merge C12 kit at repo root
```

Working tree:
```
(clean)
```


## HYBRID PROMPT RECIPE -- feature spec workflow

Purpose: for every future feature NNN, produce ONE file at
openspec/prompts/NNN-slug.md that combines three inputs.

Inputs:
1. ChatGPT prompt  -- process discipline. Yields the Process block:
   RESOLVED_FROM_SOURCE / PROPOSED / BLOCKED taxonomy,
   one-question-at-a-time, no-silent-adoption of thresholds /
   notifications / schema amendments, exact inputs-units-IDs-store-
   ownership, map each requirement to a source, check repo state
   not only plans.
2. Claude prompt   -- feature content. Yields header (Epic, Depends,
   Blockers, Capabilities), Sources list with SPEC/ARCH section
   citations, numbered Requirements, Seed scenarios, Open questions
   (do-not-invent), Out of scope.
3. Assistant review -- cross-check against the frozen design bundle.
   Confirms every cited section exists in docs/reference/CURRENT.
   Flags C-items and RQ-items. Audits anti-detection impact.

Output order:
  # NNN Feature title
  Epic | Depends | Blockers
  Use: /qf-propose @openspec/prompts/NNN-slug.md
  Capabilities: ...
  Sources: SPEC Vn section, ...; ARCH Vn section, ...; runbook Task N

  ## Process
  (from ChatGPT, 6 bullets)

  Requirements:
  1. ... (maps to source)
  2. ...

  Seed scenarios: ...
  Open questions (do not invent): ...
  Out of scope: ...

Rules:
- ASCII-only in the file. Use -- not em-dash. Use E/F not the section-sign.
- Every Sources citation must be grep-able in the current design bundle.
  An unverifiable citation -> mark that requirement BLOCKED.
- [P] values (proposed thresholds, sample sizes, horizons) require
  explicit operator approval before /qf-apply. Never silently adopted.
- Anti-detection gate: any feature that touches ARCH Vol 3 E or F, or
  SPEC Vol 4 section 11, must be reviewed by the assistant before
  commit. Frozen-layer diff (git diff 2ce33ea..HEAD on
  ARCH_v5.1.5.1_Vol3_Capture_AntiDetection.md) must be empty.
  Any reviewer proposal to weaken (drop jitter, exclude mimicry, weaken
  a challenge rule, remove rate limits) is rejected and recorded in
  openspec/conflicts-and-gaps.md under ## Rejected.
- Installation: one-shot Python heredoc (Pattern 7). No nano, no
  cat >> with heredoc, no base64.

Per-feature flow:
  1. Operator supplies ChatGPT prompt + Claude prompt.
  2. Assistant reads both, drafts hybrid, checks every citation,
     audits anti-detection, drafts in-memory.
  3. Operator approves.
  4. Assistant writes the file via a one-shot Python heredoc:
     reads the target, skips if present, writes, git add, commit, push.
  5. Run /qf-propose @openspec/prompts/NNN-slug.md

### Runbook auto-update - 2026-10-16T06:11:11Z

Branch: `feature/005-domain-types-units-clock`

Recent commits:
```
cbccc7e fix(005): close round-3 review MINORs + tidy update_runbook.py
024716a fix(005): close review MAJORs and MINORs — wall-clock adapter ban, duration bound wording
69602bc chore: opencode v2 permissions, tool routing, 005 design rulings
b5f2262 docs: add HYBRID PROMPT RECIPE to runbook
87d4b14 docs: runbook snapshot before feature 005
fb2d477 docs: runbook auto-update after eval adoption
2b24b5c eval: adopt pre-registered evaluation framework (docs+DDL)
17eb0be docs: add Pattern 7 to runbook conventions
28dfe5a docs: runbook v3.3 Session 3 post-close status
607cf3e docs: add safe-update conventions + reusable runbook updater
```

Working tree:
```
(clean)
```

### Runbook auto-update - 2026-10-16T06:21:53Z

Branch: `feature/005-domain-types-units-clock`

Recent commits:
```
fb2db35 chore: ruff format pre-existing files (POC carry-forward + runbook script)
6a2b7f5 archive(005): domain-types-units-clock — specs synced to main
be1588a docs: runbook auto-update after feature 005 review cycles
cbccc7e fix(005): close round-3 review MINORs + tidy update_runbook.py
024716a fix(005): close review MAJORs and MINORs — wall-clock adapter ban, duration bound wording
69602bc chore: opencode v2 permissions, tool routing, 005 design rulings
b5f2262 docs: add HYBRID PROMPT RECIPE to runbook
87d4b14 docs: runbook snapshot before feature 005
fb2d477 docs: runbook auto-update after eval adoption
2b24b5c eval: adopt pre-registered evaluation framework (docs+DDL)
```

Working tree:
```
(clean)
```

### Runbook auto-update - 2026-10-16T16:08:20Z

Branch: `feature/005a-domain-hardening`

Recent commits:
```
3e3afc5 chore(opencode): bump qf-build steps 30 -> 50 for multi-task apply runs
04cf0bf feat(005a): domain hardening — review fixes for 005
04ba126 Update repo index
1ecc637 Add GitHub Actions workflow for repo index generation
1cebdaa merge: feature 005 complete
696f18e docs: runbook auto-update after feature 005 archive
fb2db35 chore: ruff format pre-existing files (POC carry-forward + runbook script)
6a2b7f5 archive(005): domain-types-units-clock — specs synced to main
be1588a docs: runbook auto-update after feature 005 review cycles
cbccc7e fix(005): close round-3 review MINORs + tidy update_runbook.py
```

Working tree:
```
(clean)
```

### Runbook auto-update - 2026-10-16T16:24:22Z

Branch: `feature/005a-domain-hardening`

Recent commits:
```
06a1259 docs: runbook auto-update after feature 005a
3e3afc5 chore(opencode): bump qf-build steps 30 -> 50 for multi-task apply runs
04cf0bf feat(005a): domain hardening — review fixes for 005
04ba126 Update repo index
1ecc637 Add GitHub Actions workflow for repo index generation
1cebdaa merge: feature 005 complete
696f18e docs: runbook auto-update after feature 005 archive
fb2db35 chore: ruff format pre-existing files (POC carry-forward + runbook script)
6a2b7f5 archive(005): domain-types-units-clock — specs synced to main
be1588a docs: runbook auto-update after feature 005 review cycles
```

Working tree:
```
M docs/runbooks/QUANTFLOW-RUNBOOK-v3.3.md
?? docs/runbooks/QUANTFLOW-RUNBOOK-v3.3.md.bak-markers-1792167817
?? scripts/update_runbook.py.bak-1792167846
```

### Runbook auto-update - 2026-10-16T16:32:47Z

Branch: `feature/005a-domain-hardening`

Recent commits:
```
06a1259 docs: runbook auto-update after feature 005a
3e3afc5 chore(opencode): bump qf-build steps 30 -> 50 for multi-task apply runs
04cf0bf feat(005a): domain hardening — review fixes for 005
04ba126 Update repo index
1ecc637 Add GitHub Actions workflow for repo index generation
1cebdaa merge: feature 005 complete
696f18e docs: runbook auto-update after feature 005 archive
fb2db35 chore: ruff format pre-existing files (POC carry-forward + runbook script)
6a2b7f5 archive(005): domain-types-units-clock — specs synced to main
be1588a docs: runbook auto-update after feature 005 review cycles
```

Working tree:
```
M docs/runbooks/QUANTFLOW-RUNBOOK-v3.3.md
 M scripts/update_runbook.py
?? docs/runbooks/QUANTFLOW-RUNBOOK-v3.3.md.bak-markers-1792167817
?? scripts/update_runbook.py.bak-1792167846
```

### Runbook auto-update - 2026-10-16T16:33:30Z

Branch: `feature/005a-domain-hardening`

Recent commits:
```
06a1259 docs: runbook auto-update after feature 005a
3e3afc5 chore(opencode): bump qf-build steps 30 -> 50 for multi-task apply runs
04cf0bf feat(005a): domain hardening — review fixes for 005
04ba126 Update repo index
1ecc637 Add GitHub Actions workflow for repo index generation
1cebdaa merge: feature 005 complete
696f18e docs: runbook auto-update after feature 005 archive
fb2db35 chore: ruff format pre-existing files (POC carry-forward + runbook script)
6a2b7f5 archive(005): domain-types-units-clock — specs synced to main
be1588a docs: runbook auto-update after feature 005 review cycles
```

Working tree:
```
M docs/runbooks/QUANTFLOW-RUNBOOK-v3.3.md
 M scripts/update_runbook.py
?? docs/runbooks/QUANTFLOW-RUNBOOK-v3.3.md.bak-markers-1792167817
?? scripts/update_runbook.py.bak-1792167846
```

### Runbook auto-update - 2026-10-16T17:13:00Z

Branch: `feature/005a-domain-hardening`

Recent commits:
```
b72e1bb chore(runbook): auto-refresh top state tables from git + openspec
06a1259 docs: runbook auto-update after feature 005a
3e3afc5 chore(opencode): bump qf-build steps 30 -> 50 for multi-task apply runs
04cf0bf feat(005a): domain hardening — review fixes for 005
04ba126 Update repo index
1ecc637 Add GitHub Actions workflow for repo index generation
1cebdaa merge: feature 005 complete
696f18e docs: runbook auto-update after feature 005 archive
fb2db35 chore: ruff format pre-existing files (POC carry-forward + runbook script)
6a2b7f5 archive(005): domain-types-units-clock — specs synced to main
```

Working tree:
```
M scripts/update_runbook.py
```

### Runbook auto-update - 2026-10-16T17:13:59Z

Branch: `feature/005a-domain-hardening`

Recent commits:
```
bc43669 chore(runbook): preserve per-phase notes below OVERALL PROGRESS table
b72e1bb chore(runbook): auto-refresh top state tables from git + openspec
06a1259 docs: runbook auto-update after feature 005a
3e3afc5 chore(opencode): bump qf-build steps 30 -> 50 for multi-task apply runs
04cf0bf feat(005a): domain hardening — review fixes for 005
04ba126 Update repo index
1ecc637 Add GitHub Actions workflow for repo index generation
1cebdaa merge: feature 005 complete
696f18e docs: runbook auto-update after feature 005 archive
fb2db35 chore: ruff format pre-existing files (POC carry-forward + runbook script)
```

Working tree:
```
(clean)
```

### Runbook auto-update - 2026-10-16T17:18:27Z

Branch: `master`

Recent commits:
```
dd5e006 Update repo index
058213b merge: feature 005a complete
6f60204 docs: runbook auto-update after feature 005a tag
bc43669 chore(runbook): preserve per-phase notes below OVERALL PROGRESS table
b72e1bb chore(runbook): auto-refresh top state tables from git + openspec
06a1259 docs: runbook auto-update after feature 005a
3e3afc5 chore(opencode): bump qf-build steps 30 -> 50 for multi-task apply runs
04cf0bf feat(005a): domain hardening — review fixes for 005
04ba126 Update repo index
1ecc637 Add GitHub Actions workflow for repo index generation
```

Working tree:
```
(clean)
```

### Runbook auto-update - 2026-10-16T21:02:54Z

Branch: `master`

Recent commits:
```
d37d37f Update repo index
bcc3061 merge: feature 005b complete
0792a0e feat(005b): domain fail-closed hardening — Q6, Q8, Q12, Q13
246a329 fix(005b): close aliased-import evasion in constants AST guard
64b82f9 docs(005b): manual propose artifacts — proposal, design, tasks, deltas
7ae1373 docs(005b): tighten propose-phase scope + clean stray change dirs
e784408 Update repo index
15a6c14 docs(005b): add fail-closed prompt + record Q9 resolution
cc60bac docs(runbook): document qfmerge alias (pull + push + runbook refresh)
1e513bb docs(runbook): document qfmerge alias (pull + push + runbook refresh)
```

Working tree:
```
M openspec/specs/epoch-clock/spec.md
 M scripts/update_runbook.py
?? openspec/changes/archive/2026-10-16-005b-domain-fail-closed/
?? openspec/specs/domain-constants/
```

### Runbook auto-update - 2026-10-16T21:06:37Z

Branch: `master`

Recent commits:
```
1a7b0a4 Update repo index
4f5faeb fix(runbook): handle dict-shaped openspec list --json output
941dfbf archive(005b): sync specs — domain-constants added, epoch-clock modified
d37d37f Update repo index
bcc3061 merge: feature 005b complete
0792a0e feat(005b): domain fail-closed hardening — Q6, Q8, Q12, Q13
246a329 fix(005b): close aliased-import evasion in constants AST guard
64b82f9 docs(005b): manual propose artifacts — proposal, design, tasks, deltas
7ae1373 docs(005b): tighten propose-phase scope + clean stray change dirs
e784408 Update repo index
```

Working tree:
```
(clean)
```

### Runbook auto-update - 2026-10-16T21:12:24Z

Branch: `master`

Recent commits:
```
96a1c44 Update repo index
fc7a6a8 docs(005d): record decisions for Q2, Q11, Q14, Q15, Q16 and freeze pocs/interface
46f995c docs: runbook auto-update after feature 005b merge
1a7b0a4 Update repo index
4f5faeb fix(runbook): handle dict-shaped openspec list --json output
941dfbf archive(005b): sync specs — domain-constants added, epoch-clock modified
d37d37f Update repo index
bcc3061 merge: feature 005b complete
0792a0e feat(005b): domain fail-closed hardening — Q6, Q8, Q12, Q13
246a329 fix(005b): close aliased-import evasion in constants AST guard
```

Working tree:
```
(clean)
```

### Runbook auto-update - 2026-10-16T22:49:27Z

Branch: `master`

Recent commits:
```
eafaf0d Update repo index
055903d merge: feature 005c complete
9793760 feat(005c): domain cleanup — Q3/Q4/Q5/Q7, cooldown_until, random regression, test gaps
ebdb121 Revert "docs: restructure conflicts-and-gaps — move Q2/Q11/Q14/Q15/Q16 to Resolved, add Q8/Q13"
0bb8c1e docs: restructure conflicts-and-gaps — move Q2/Q11/Q14/Q15/Q16 to Resolved, add Q8/Q13
d1cd170 docs: runbook auto-update after 005d decisions
96a1c44 Update repo index
fc7a6a8 docs(005d): record decisions for Q2, Q11, Q14, Q15, Q16 and freeze pocs/interface
46f995c docs: runbook auto-update after feature 005b merge
1a7b0a4 Update repo index
```

Working tree:
```
(clean)
```

### Runbook auto-update - 2026-10-17T04:30:12Z

Branch: `master`

Recent commits:
```
fff528c Update repo index
20a387b chore(openspec): implement feature-group layout and flat change naming rule (constitution §12)
ccae010 docs: runbook auto-update after feature 005c merge
eafaf0d Update repo index
055903d merge: feature 005c complete
9793760 feat(005c): domain cleanup — Q3/Q4/Q5/Q7, cooldown_until, random regression, test gaps
ebdb121 Revert "docs: restructure conflicts-and-gaps — move Q2/Q11/Q14/Q15/Q16 to Resolved, add Q8/Q13"
0bb8c1e docs: restructure conflicts-and-gaps — move Q2/Q11/Q14/Q15/Q16 to Resolved, add Q8/Q13
d1cd170 docs: runbook auto-update after 005d decisions
96a1c44 Update repo index
```

Working tree:
```
(clean)
```

### Runbook auto-update - 2026-10-17T14:10:20Z

Branch: `feature/010a-migration-runner-core`

Recent commits:
```
360d865 test(010a): group 2.5 — baseline_covered fail-closed boundary tests (task 2.5)
b26e0ff feat(010a): group 2.4 — dependencies, cycles, stable topological order (task 2.4)
08857a4 feat(010a): group 2.3 — slot policy + unmanifested-file validation (task 2.3)
b0a978c feat(010a): group 2.2 — manifest schema loading + path safety (task 2.2)
b7168b4 test(010a): group 2.1 — red manifest validator test classes (task 2.1)
a774ebb chore(010a): fix pre-existing ruff format drift + record D2 CLI amendment
cfbb173 feat(010a): group 1 — package scaffold, CLI entry, migration error types (tasks 1.1-1.4)
321b2a9 docs(010a): propose artifacts via qf-propose + resolve OQ-1/OQ-2
7508ada chore(010a): pre-resolve 5 conflicts for qf-propose
198af98 docs(010a): add migration runner core prompt
```

Working tree:
```
M docs/runbooks/QUANTFLOW-RUNBOOK-v3.3.md
 M openspec/conflicts-and-gaps.md
 M openspec/formulas-dealer-greeks.md
 M src/quantflow/migrations/manifest.py
?? openspec/c13-dealer-positioning-implementation-plan.md
```

### Runbook auto-update - 2026-10-17T14:16:39Z

Branch: `feature/010a-migration-runner-core`

Recent commits:
```
e10dd30 fix(openspec): remove stale 005b-domain-fail-closed source after archive
360d865 test(010a): group 2.5 — baseline_covered fail-closed boundary tests (task 2.5)
b26e0ff feat(010a): group 2.4 — dependencies, cycles, stable topological order (task 2.4)
08857a4 feat(010a): group 2.3 — slot policy + unmanifested-file validation (task 2.3)
b0a978c feat(010a): group 2.2 — manifest schema loading + path safety (task 2.2)
b7168b4 test(010a): group 2.1 — red manifest validator test classes (task 2.1)
a774ebb chore(010a): fix pre-existing ruff format drift + record D2 CLI amendment
cfbb173 feat(010a): group 1 — package scaffold, CLI entry, migration error types (tasks 1.1-1.4)
321b2a9 docs(010a): propose artifacts via qf-propose + resolve OQ-1/OQ-2
7508ada chore(010a): pre-resolve 5 conflicts for qf-propose
```

Working tree:
```
M docs/runbooks/QUANTFLOW-RUNBOOK-v3.3.md
 M openspec/conflicts-and-gaps.md
 M openspec/formulas-dealer-greeks.md
 M src/quantflow/migrations/manifest.py
?? openspec/c13-dealer-positioning-implementation-plan.md
```

### Runbook auto-update - 2026-10-17T20:12:25Z

Branch: `master`

Recent commits:
```
d0c3867 Update repo index
5fbf349 merge: feature 010a complete — migration runner core (32/32 tasks, 496 tests, migrations 99-100% coverage)
760dd9b 010a-7.4: repo cleanliness verified — no forbidden-path diffs, status clean, conflicts-and-gaps current
d180d16 010a-7.3: anti-detection SHA gate verified — ARCH Vol3 matches pinned digest
fc9d308 010a-7.2: coverage gate — migrations 99-100%, domain 100%; 35 fail-closed branch tests; check_constants green
9cb02d5 010a-7.1: full suite green — pytest 461 passed, ruff check+format clean, mypy --strict clean
ee47170 chore(harness): lean tool usage fallback for sessions without harness-tools
b244933 fix(010a): mypy strict + ruff clean on CLI — domain.errors, conn: Any, sys.exit(.exit_code), S608 noqa
15adca4 010a-6.2: wire tests/migration integration suite — integration marker, <10s budget, /data path guards
4fa9166 010a-6.1: fresh-vs-upgrade schema equivalence (canonical sqlite_master / DuckDB introspection)
```

Working tree:
```
(clean)
```
