# FINAL POC RUNBOOK — Hello World Plumbing Proof (v2.0)

**Status:** v2.0 — 2026-10-13. Supersedes v1.0.
**Nature:** This POC is the **first increment of the real project**, not a throwaway. Every file except `adapters/market/fixture.py` is production code from day one. Connectivity resources are created once, with final names.

**Purpose:** prove the plumbing joints connect end to end with **100% synthetic data**:


## STATUS — as of 2026-10-13

Legend: ✅ done · 🔄 in progress · ⬜ not started · ⏳ blocked · ❌ failed

### Foundations (from the master runbook)

| Item | Status | Notes |
|---|---|---|
| Session 1 — LUKS storage, users, directories | ✅ | `quant`, `quant-cap`, `quant-rhythm`; LUKS UUID `740ec50d-…`; SATA mounted on the DB appliance |
| Session 2 Task 1 — LUKS header backup | ✅ | MEGA-encrypted, SHA-256 in Bitwarden |
| Session 2 Task 2 — user reconciliation | ✅ | `quant` / `quant-cap` / `quant-rhythm` exist on this host |
| Session 2 Task 3 — directory reconciliation | ✅ | `/data` tree, `/var/quant` tree |
| Session 2 Task 4 — ADR-001 anti-detection scope | ⬜ | needs writing before Feature 052 |
| Session 2 Task 5 — freeze design bundle | ⬜ | `docs/reference/release-*/` + SHA256SUMS + CURRENT symlink |
| Session 2 Task 6 — repo + `.gitignore` first | ✅ | two commits present |
| Session 2 Task 7 — folder structure | ✅ | `f640d85` |
| Session 2 Task 8 — `uv` + Python 3.12 + foundation deps | ⬜ | `uv` installed (0.12.21); `pydantic` import fails |
| Session 2 Task 9 — `pyproject.toml` tool config | ⬜ | not applied |
| Session 2 Task 10 — commit + `foundation-complete` tag | ⬜ | tag missing |
| Session 2 Task 11 — boot auto-mount | ⏳ | deferred by design |

### Hardware

| Item | Status | Notes |
|---|---|---|
| Lenovo TSC instability fix | ✅ | `tsc=reliable clocksource=tsc` in GRUB; 24 h uptime before last shutdown; `LENOVO-TSC-FIX.md` recorded |
| Lenovo BIOS downgrade | ⬜ | fallback only; not needed if stability holds |
| DB appliance (`srirampc`) | ✅ | Debian 13; LUKS; Quack on port 9494; Tailscale `100.86.117.49` |
| App host machine | 🔄 | current dev host is the Lenovo running Mint from USB; planned prod host is a separate Ubuntu gateway laptop; planned backup host is a Lenovo Yoga |

### Connectivity and secrets

| Item | Status | Notes |
|---|---|---|
| Muse compatibility check | ✅ | Muse supports one API key or provider OAuth only; two-header Access not supported. Decision recorded: single API key at origin |
| Cloudflare account and domain | ⬜ | `[GET AT BUILD]` |
| Cloudflare Tunnel `quantflow-interface` | ⬜ | not created; created once with final name |
| Cloudflare Access app | ⬜ | admin / curl path only; not on Muse's path |
| Bitwarden project `QuantFlow-Interface` | ⬜ | item `INTERFACE_API_KEY` to be created |
| Tailscale tailnet | ✅ | working; `srirampc` reachable |
| ADR-002 no-containers | ⬜ | to be written with Session 2 Task 4 |

### POC scaffolding (this runbook)

| Item | Status | Notes |
|---|---|---|
| Repo layout confirmed (`src/quantflow/…`) | ✅ | decided in this document |
| `docs/PREREQUISITES.md` | ⬜ | Appendix A content ready to paste |
| `docs/HOST_INVENTORY.md` | ⬜ | to be filled per machine |
| `scripts/bootstrap.sh` | ⬜ | Appendix B content ready to paste |
| `scripts/poc-run.sh` | ⬜ | Appendix C content ready to paste |
| `config/.env.example` | ⬜ | spec in §2 |
| Python source (`fixture`, `store`, `pricer`, `signer`, `pipeline`, `api_key`, `mcp_server`, `mcp_probe`, `watcher`) | ⬜ | to be written |
| Unit tests | ⬜ | to be written |
| Integration test (`test_mcp_probe.py`) | ⬜ | to be written |

### POC phases (this runbook)

| Phase | Status | Gate |
|---|---|---|
| P0 — store init | ⬜ | stores exist; cadence from DB |
| P1 — fixture lands | ⬜ | 60 contracts, 40 trades |
| P2 — pricer self-check | ⬜ | ATM delta ≈ 0.52 |
| P3 — pipeline idempotent | ⬜ | level card + no-op rerun |
| P4 — MCP + API-key gate | ⬜ | 401 / 401 / pass |
| P5 — revoke + restart | ⬜ | old key 401; state survives |
| P6 — watcher dry-run | ⬜ | one ping then quiet |
| P7 — optional Muse E2E | ⬜ | only when authorized |

### Immediate blockers before Phase 0 can start

1. **Session 2 Tasks 5, 8, 9, 10 not done.** `pydantic` import fails, no `foundation-complete` tag. Run the commands in §"Step 2" below.
2. **Repo scaffolding not present.** `scripts/poc-run.sh`, `scripts/bootstrap.sh`, `docs/PREREQUISITES.md`, `config/.env.example` need to be created from the appendices.
3. **Python source not present.** Nothing under `src/quantflow/` except `__init__.py` files.

Everything else is either already done or is a `[GET AT BUILD]` item that does not block the POC.




```text
fixture -> write-once landing -> DuckDB/SQLite stores -> pricer
-> signer-lite -> level card -> outbox -> MCP server with API-key gate
-> MCP probe -> watcher dry-run
```

**Not proven by this POC:** real market-data quality, signing accuracy, Greek accuracy vs a vendor, Volland parity, predictions, or live alerts. Those belong to the real build phases.

**Data rule:** anything real is marked `[GET AT BUILD]`. These must not block the POC: ThetaData Terminal, real SATA production paths, Cloudflare Tunnel hostname in DNS, dedicated mailbox, Muse connector setup, real Bitwarden production items.

**Packaging rule:** the POC is not a separate bundle. The code lives in `src/quantflow/` at the paths that Feature 070 will use. There is no `pocs/` directory.

---

## 0. Decisions locked

1. **Muse edge auth = one API key.** Muse's custom connector supports a single API key or provider OAuth; it does **not** support injecting both `CF-Access-Client-Id` and `CF-Access-Client-Secret`. The MCP server therefore validates one `X-Api-Key` header at the origin. Cloudflare Access remains available for admin and curl paths and is tested separately; it is not the Muse end-to-end gate.

2. **No containers.** `uv` + `pyproject.toml` + `uv.lock` reproduces Python deps exactly. System packages are documented in `docs/PREREQUISITES.md` and installed by `scripts/bootstrap.sh`. Recorded in ADR-002.

3. **DB is minimum but final-shaped.** DuckDB for analytics, SQLite for local operations and audit. No PostgreSQL, Redis, Timescale, ORM, or DB server.

4. **Single writer per DuckDB file.** The POC runs on one machine, but table names and write ownership match the production design so the laptop re-test is meaningful.

5. **Connectivity is created once, with final names.** Tunnel `quantflow-interface`, hostname `interface.<yourdomain>`, Bitwarden project `QuantFlow-Interface`. No "poc" suffix. Same resources serve dev, prod, and backup.

6. **Foreground first.** No systemd unit, no cron, no background schedule until every foreground phase passes and you explicitly say go.

---

## 1. Repo layout

The POC lives inside the existing repo:

```text
~/src/quant-flow-system/
├── pyproject.toml                    # canonical deps
├── uv.lock
├── README.md
├── src/quantflow/
│   ├── __init__.py
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── market/
│   │   │   ├── __init__.py
│   │   │   └── fixture.py            # POC only — replaced by thetadata.py later
│   │   └── notify/
│   │       ├── __init__.py
│   │       ├── discord.py
│   │       ├── resend.py
│   │       └── mailgun.py
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── pricer.py                 # real BS + greeks
│   │   ├── signer.py                 # interface; flat impl replaced later
│   │   └── types.py
│   ├── interface/
│   │   ├── __init__.py
│   │   ├── api_key.py                # auth primitive
│   │   ├── mcp_server.py             # Feature 070 extends
│   │   └── mcp_probe.py              # real MCP client
│   ├── store/
│   │   ├── __init__.py
│   │   ├── duckdb_store.py
│   │   ├── sqlite_store.py
│   │   └── init.py
│   ├── pipeline.py
│   └── watcher.py
├── tests/
│   ├── unit/
│   ├── integration/
│   │   └── test_mcp_probe.py
│   └── evidence/
├── scripts/
│   ├── bootstrap.sh
│   └── poc-run.sh
├── systemd/                          # templates, empty at POC time
├── docs/
│   ├── PREREQUISITES.md
│   ├── HOST_INVENTORY.md
│   ├── architecture/
│   │   └── adr/
│   │       ├── ADR-001-anti-detection-scope.md
│   │       └── ADR-002-no-containers.md
│   └── reports/
│       └── FINAL-POC-RUNBOOK-hello-world.md
├── config/
│   └── .env.example
├── data/                             # gitignored
│   └── poc_data/
├── landing/
└── outbox/
```

**What stays forever:** everything under `src/quantflow/` except `adapters/market/fixture.py`, plus tests, scripts, docs, pyproject, lock, config.

**What gets replaced:** `adapters/market/fixture.py` when real data arrives; the flat implementation in `domain/signer.py`; contents of `landing/`, `outbox/`, `data/poc_data/`; the POC API key value.

---

## 2. Configuration contract

`config/.env.example` (names only, no values):

```bash
POC_DATA_DIR=./data/poc_data
POC_LOCAL_DIR=./data/poc_data/local
POC_HOST=127.0.0.1
POC_PORT=8765
POC_API_KEY=CHANGE_ME
POC_SYMBOL=SPY
```

Rules:

- `reference.duckdb`, `intraday.duckdb`, `eod.duckdb` live under `POC_DATA_DIR`. In production they move to the SATA per the frozen design; the POC uses local paths.
- `ops.sqlite` lives under `POC_LOCAL_DIR`. **SQLite is never placed on a network share.**
- No production database is touched. If `/data` exists, create only a new POC subfolder such as `/data/poc-interface`; never open or migrate `quant_state.db` or `quant_flow.duckdb`.

Dev machine: copy `.env.example` to `.env` and use a throwaway key.
Production: same variables loaded via `systemd-creds` from Bitwarden.

---

## 3. Database design

### 3.1 `reference.duckdb`

```sql
CREATE TABLE IF NOT EXISTS config (
  key VARCHAR PRIMARY KEY,
  value VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS universe (
  symbol VARCHAR PRIMARY KEY
);

INSERT OR REPLACE INTO config VALUES ('poll_cadence_min', '30');
INSERT OR IGNORE INTO universe VALUES ('SPY');
```

The watcher reads `poll_cadence_min` at runtime. Changing cadence is one SQL update, no code change.

### 3.2 `intraday.duckdb`

```sql
CREATE TABLE IF NOT EXISTS chain_snapshot (
  symbol VARCHAR,
  expiry DATE,
  strike DOUBLE,
  right VARCHAR,
  bid DOUBLE,
  ask DOUBLE,
  iv DOUBLE,
  oi BIGINT,
  asof TIMESTAMP,
  git_hash VARCHAR,
  sign_version VARCHAR
);

CREATE TABLE IF NOT EXISTS trades_signed (
  symbol VARCHAR,
  strike DOUBLE,
  right VARCHAR,
  side SMALLINT,
  method VARCHAR,
  confidence DOUBLE,
  size BIGINT,
  run_key VARCHAR
);

CREATE TABLE IF NOT EXISTS level_card (
  symbol VARCHAR,
  spot DOUBLE,
  flip_low DOUBLE,
  flip_high DOUBLE,
  call_wall DOUBLE,
  put_wall DOUBLE,
  coverage_pct DOUBLE,
  asof TIMESTAMP,
  sign_version VARCHAR
);
```

### 3.3 `ops.sqlite`

```sql
CREATE TABLE IF NOT EXISTS job_runs (
  run_key TEXT PRIMARY KEY,
  job TEXT NOT NULL,
  rows INTEGER NOT NULL,
  finished_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS watcher_state (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS mcp_audit (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts_utc TEXT NOT NULL,
  tool TEXT NOT NULL,
  principal TEXT NOT NULL,
  allowed INTEGER NOT NULL,
  response_id TEXT,
  nonce_hash TEXT
);
```

`mcp_audit` stores hashes, not nonces or keys.

### 3.4 Deliberately omitted for the POC

Contract master, stored Greeks history, OI daily history, blackout tables, skew history, strike graph, predictions, Volland scorecards, alert lifecycle, SQLite grant tables, migration framework. Those come later; the POC proves the shape without pretending to be the platform.

---

## 4. Phase 0 — setup and store init

One-time prerequisites:

- `docs/PREREQUISITES.md` (in repo) documents system packages
- `scripts/bootstrap.sh` (in repo) installs them idempotently
- Python deps reproduced by `uv sync --frozen`

Then:

```bash
cd ~/src/quant-flow-system
uv sync --frozen
cp config/.env.example config/.env
# edit config/.env if you want non-default paths
./scripts/poc-run.sh store-init
```

**Expected:**

```
stores ready; poll_cadence_min = 30
```

**Gate P0:** `reference.duckdb`, `intraday.duckdb`, and `ops.sqlite` exist; cadence read from DB, not hardcoded.

---

## 5. Phase 1 — synthetic fixture to landing

```bash
./scripts/poc-run.sh fixture
```

Or: `uv run python -m quantflow.adapters.market.fixture`

Deterministic output: SPY spot 745, strikes 715–785, two expiries, calls and puts, crude IV smile, synthetic OI, bid/ask, 40 fake prints.

**Expected shape:**

```
fixture: 60 contracts, 40 trades
```

**Gate P1:** `landing/theta/chain.ndjson` and `landing/trades/trades.ndjson` exist, treated as write-once raw inputs.

---

## 6. Phase 2 — pricer self-check

```bash
uv run python -c "from quantflow.domain.pricer import greeks; \
  print(greeks(745, 745, 0.08, 0.04, 0.013, 0.16, 'C'))"
```

**Expected:** ATM call delta ≈ 0.52, gamma positive.

**Gate P2:** delta, gamma, vanna, charm, speed return finite numbers for calls and puts across the fixture chain. `[GET AT BUILD: cross-check first-order Greeks against ThetaData served values.]`

---

## 7. Phase 3 — idempotent pipeline to level card

Run twice:

```bash
./scripts/poc-run.sh pipeline
./scripts/poc-run.sh pipeline
```

First run expected shape:

```
SPY level card — spot 745.0, flip band [737.0, 751.0],
call wall ..., put wall ..., signed coverage ...%
(signer poc-sign-0.1, synthetic data)
```

Second run expected:

```
already ran — no-op
```

Verify:

```bash
cat outbox/spy_level_card.txt
uv run python -c "
import duckdb
con = duckdb.connect('data/poc_data/intraday.duckdb', read_only=True)
print(con.execute('select count(*) from trades_signed').fetchone()[0])
"
```

**Gate P3:** signed-trade count stays at 40 after the second run; outbox card carries `sign_version` and says synthetic data.

---

## 8. Phase 4 — MCP server with API-key gate

Terminal A:

```bash
set -a; source config/.env; set +a
uv run python -m quantflow.interface.mcp_server
```

Two read-only tools:

- `hello(name, nonce)` → `{message, nonce, response_id, server_time_utc, auth_mode: "api_key", synthetic: true}`. Same `response_id` appears in the server log and `mcp_audit`.
- `get_levels(ticker)` → latest level card from `intraday.duckdb`.

Terminal B, negative tests:

```bash
curl -s -o /dev/null -w '%{http_code}\n' -X POST http://127.0.0.1:8765/mcp \
  -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
# expected: 401

curl -s -o /dev/null -w '%{http_code}\n' -X POST http://127.0.0.1:8765/mcp \
  -H 'x-api-key: wrong-key' -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
# expected: 401
```

Positive probe:

```bash
NONCE=$(openssl rand -hex 16)
uv run python -m quantflow.interface.mcp_probe --nonce "$NONCE"
grep -F "response_id" outbox/mcp_server.log | tail -5
uv run python -c "
import sqlite3
con = sqlite3.connect('data/poc_data/local/ops.sqlite')
print(con.execute('select ts_utc, tool, allowed, response_id from mcp_audit order by id desc limit 3').fetchall())
"
```

**Gate P4:** no-key and wrong-key are 401; probe returns a fresh `response_id`; same `response_id` appears in the server log and `mcp_audit`; `auth_mode` is `api_key`.

---

## 9. Phase 5 — revoke, restart, persistence

1. Stop Terminal A with `Ctrl+C`.
2. Change `POC_API_KEY` in `config/.env` to a new throwaway value.
3. Restart Terminal A.
4. Old key returns 401. New key passes the probe.
5. `get_levels` still returns the Phase 3 card.
6. `./scripts/poc-run.sh pipeline` still says `already ran — no-op`.

**Gate P5:** revocation works by key rotation; stored POC state survives restart; idempotency survives restart.

---

## 10. Phase 6 — watcher dry-run, DB cadence, dedupe

Create one fake alert if not present:

```bash
cat > inbox_fake/msg-001.json <<'JSON'
{"id":"msg-001","from":"alerts@your-system",
 "subject":"ALERT SPY 750C sweep A/AA","body":"synthetic"}
JSON
./scripts/poc-run.sh watcher
./scripts/poc-run.sh watcher
```

First run expected:

```
WOULD PING (cadence 30 min): ALERT SPY 750C sweep A/AA
-> verify via M-SIGN + levels, then chat
```

Second run expected:

```
quiet — nothing new
```

Change cadence in DB, add a second fake message, re-run:

```bash
uv run python -c "
import duckdb
c = duckdb.connect('data/poc_data/reference.duckdb')
c.execute(\"UPDATE config SET value='20' WHERE key='poll_cadence_min'\")
print(c.execute(\"SELECT value FROM config WHERE key='poll_cadence_min'\").fetchone()[0])
"
cat > inbox_fake/msg-002.json <<'JSON'
{"id":"msg-002","from":"alerts@your-system",
 "subject":"ALERT SPY 745P sweep B/BB","body":"synthetic"}
JSON
./scripts/poc-run.sh watcher
```

**Gate P6:** printed cadence follows the DB (30 then 20); each fake message produces exactly one would-ping ever. `[GET AT BUILD: real dedicated mailbox, sender/subject pattern, and arming decision.]`

---

## 11. Optional public/Muse connection test — gated, not part of POC PASS

Do not perform this until you explicitly say go.

- Use the tunnel created with the final name: `cloudflared tunnel create quantflow-interface`
- DNS: `cloudflared tunnel route dns quantflow-interface interface.<yourdomain>`
- Bitwarden project: `QuantFlow-Interface`
- Origin still validates the single API key. Do not remove auth to make a client work.
- Do not paste the key in chat. Enter it through Muse's secure credential flow.
- If the client cannot send the API key to the exact endpoint, record the failing layer and stop.
- Cloudflare Access two-header service auth is a separate protocol experiment only; mark `MUSE_COMPATIBILITY_BLOCKED` for Muse end-to-end unless Muse's connector capability changes.

**Gate P7:** only when authorized — Muse calls `hello` with a fresh nonce, returned `response_id` matches the server log, `auth_mode` is still `api_key`.

---

## 12. Failure drills

| Drill | Action | Expected |
|---|---|---|
| Duplicate pipeline | Run `./scripts/poc-run.sh pipeline` again | `already ran — no-op`; row count unchanged |
| Anonymous request | MCP request with no key | 401; no tool executes |
| Wrong secret | MCP request with wrong key | 401; audit row records denied without the key |
| Double ping | Re-run watcher after a fake alert | exactly one would-ping ever per message |
| Cadence change | Set DB cadence to 20 | watcher output follows DB, no code change |
| Kill/restart | `Ctrl+C` server, restart | old runs committed; no partial level card; probe passes |
| Bad path | Point `POC_DATA_DIR` at an unwritable folder in a scratch copy | job fails loudly; no silent fallback |

Any failed drill stops the POC. Fix the smallest layer, rerun the phase, then rerun the affected gate.

---

## 13. Evidence to save

Under `tests/evidence/`:

```text
p0_store_init.txt
p1_fixture.txt
p2_pricer_check.txt
p3_pipeline_run1.txt
p3_pipeline_run2_noop.txt
p4_negative_401.txt
p4_probe_hello.txt
p4_server_log_response_id.txt
p4_mcp_audit_row.txt
p5_revoke_restart.txt
p6_watcher_run1.txt
p6_watcher_run2_quiet.txt
p6_watcher_cadence_change.txt
```

Redact keys before sharing. Nonces are test markers; response IDs and timestamps should match across probe output, server log, and audit rows.

---

## 14. Laptop re-test checklist

After the POC passes on the current machine:

1. `git clone <repo>` on the target machine.
2. `./scripts/bootstrap.sh` — installs system packages, `uv`, `cloudflared`, `tailscale`.
3. `uv sync --frozen` — reproduces Python deps exactly.
4. `cp config/.env.example config/.env`; adjust `POC_DATA_DIR` / `POC_LOCAL_DIR`.
5. Create a POC-only API key item in Bitwarden. Paste the value into `.env` or shell env locally. Never send it to Muse.
6. Run Phases 0–6 unchanged.
7. Record machine facts for the hardware verdict: CPU model, core count, RAM, storage type, OS, Phase 3 wall-clock time.
8. Stop the server. Remove the throwaway key if it was only for POC. Keep evidence.

---

## 15. Done criteria

The POC passes only when all are true:

- [ ] Fixture lands as immutable ndjson; stores initialize from the DB design.
- [ ] Pricer self-check sane; signer-lite returns side/method/confidence; coverage prints.
- [ ] Pipeline produces a level card and is idempotent on rerun and after restart.
- [ ] MCP server denies no-key and wrong-key.
- [ ] Fresh nonce returns a server-generated `response_id` matching server log and audit row.
- [ ] Key rotation revokes old key without losing stored state.
- [ ] Watcher reads cadence from DB, never double-pings a fake alert.
- [ ] Evidence folder contains gate outputs with secrets redacted.
- [ ] Nothing real is connected: no ThetaData, no real mailbox, no production DB, no live alert, no scheduled job.

---

## 16. What carries forward

Everything in `src/quantflow/` except `adapters/market/fixture.py` and the flat signer implementation. In particular:

- `interface/mcp_server.py` — Feature 070 extends it
- `interface/api_key.py` — production auth primitive
- `interface/mcp_probe.py` — real MCP client, used as regression
- `pipeline.py`, `watcher.py` — orchestration and cadence
- `store/*` — DuckDB + SQLite patterns
- `domain/pricer.py` — real math
- `domain/signer.py` — interface preserved; implementation swapped
- `pyproject.toml`, `uv.lock` — canonical dependency set
- `scripts/bootstrap.sh`, `docs/PREREQUISITES.md` — machine provisioning
- `docs/architecture/adr/ADR-002-no-containers.md`

Cloudflare Tunnel `quantflow-interface`, its DNS record, the Access app, Tailscale tailnet, and the Bitwarden `QuantFlow-Interface` project are all created once and reused unchanged for dev, prod, and backup.

**Next after green:** replace `adapters/market/fixture.py` with the real ThetaData adapter. Everything else stays.

---

## Appendix A — `docs/PREREQUISITES.md` (create in repo)

```markdown
# Host Prerequisites

Install once per machine.

## Every machine (dev and prod)

- Debian 13 or Ubuntu 24.04 LTS
- `python3-venv`, `python3-dev`, `build-essential`
- `git`, `curl`, `ca-certificates`
- `uv` (official installer; version recorded in README)

## DB appliance only (`srirampc`)

- `cryptsetup`, `systemd-cryptsetup`
- LUKS on the SATA drive (UUID in `docs/HOST_INVENTORY.md`)
- `duckdb` binary (official release)
- `tailscale` (official install script)

## App host only (Mint now, Ubuntu gateway later)

- `cloudflared` (Cloudflare apt repo)
- `tailscale`

## Python dependencies

Reproduced by `uv sync --frozen` from `uv.lock`.
Do not `pip install` anything manually.

## Install sequence on a fresh machine

1. Run `./scripts/bootstrap.sh`.
2. `git clone <repo>` if not already cloned.
3. `cd <repo> && uv sync --frozen`.
4. `uv run pytest -q` (should pass).
5. Configure external services per `docs/HOST_INVENTORY.md`.
```

---

## Appendix B — `scripts/bootstrap.sh` (create in repo)

```bash
#!/usr/bin/env bash
set -euo pipefail

# System packages
sudo apt-get update
sudo apt-get install -y \
    python3-venv python3-dev build-essential \
    git curl ca-certificates \
    cryptsetup systemd-cryptsetup

# uv
if ! command -v uv >/dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # shellcheck disable=SC1091
    source "$HOME/.bashrc"
fi

# cloudflared
if ! command -v cloudflared >/dev/null 2>&1; then
    sudo mkdir -p --mode=0755 /usr/share/keyrings
    curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg \
        | sudo tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null
    echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] \
        https://pkg.cloudflare.com/cloudflared any main" \
        | sudo tee /etc/apt/sources.list.d/cloudflared.list
    sudo apt-get update
    sudo apt-get install -y cloudflared
fi

# tailscale
if ! command -v tailscale >/dev/null 2>&1; then
    curl -fsSL https://tailscale.com/install.sh | sh
fi

# Python deps
cd "$(git rev-parse --show-toplevel)"
uv sync --frozen

echo "Bootstrap complete. Run 'uv run pytest -q' to verify."
```

---

## Appendix C — `scripts/poc-run.sh` (create in repo)

```bash
#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"
[ -f config/.env ] && { set -a; source config/.env; set +a; }

case "${1:-}" in
  store-init) uv run python -m quantflow.store.init ;;
  fixture)    uv run python -m quantflow.adapters.market.fixture ;;
  pipeline)   uv run python -m quantflow.pipeline ;;
  server)     uv run python -m quantflow.interface.mcp_server ;;
  probe)      shift; uv run python -m quantflow.interface.mcp_probe "$@" ;;
  watcher)    uv run python -m quantflow.watcher ;;
  *)
    echo "usage: $0 {store-init|fixture|pipeline|server|probe|watcher}" >&2
    exit 2
    ;;
esac
```

---

**END OF FINAL-POC-RUNBOOK-hello-world.md v2.0**
