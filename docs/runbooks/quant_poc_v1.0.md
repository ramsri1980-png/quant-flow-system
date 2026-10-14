# QuantFlow POC — Transport Hello World (Runbook + Status)

**Status:** v2.0 — 2026-10-13
**Nature:** transport-only proof. Muse calls one MCP tool over HTTPS through Cloudflare Tunnel with a single `X-Api-Key` header. No database, no pipeline, no provider adapters, no `/data` access.
**Save as:** `docs/reports/POC-RUNBOOK-transport.md`
**Companion:** none. This file is both the runbook (how) and the tracker (status). No separate TOC file.

**Legend:** ✅ done · 🔄 in progress · ⬜ not started · ⏳ deferred · ❌ failed

---

# TABLE OF CONTENTS

| PART | Title | Status |
|---|---|---|
| PART 0 | Tech Stack | ⬜ not saved |
| PART 1 | What this POC proves | n/a (context) |
| PART 2 | Decisions locked | ✅ decided |
| PART 3 | Prerequisites | ⬜ not installed |
| PART 4 | Phase 0 — Repo state | ⬜ not started |
| PART 5 | Phase 1 — Local MCP with X-Api-Key | ⬜ not started |
| PART 6 | Phase 2 — Cloudflare Tunnel and Access | ⬜ not started |
| PART 7 | Phase 3 — Bitwarden and public probe | ⬜ not started |
| PART 8 | Phase 4 — Muse end-to-end | ⬜ not started |
| PART 9 | Phase 5 — Failure drills | ⬜ not started |
| PART 10 | Decommission | ⬜ not started |
| PART 11 | Exit criteria | ⬜ not started |
| PART 12 | Handoff | n/a (context) |

---

# PART 0 — TECH STACK

**Status:** ⬜ `docs/STACK.md` not yet saved. This is the canonical content.

Rule: `pyproject.toml` + `uv.lock` are the source of truth. This section is the human-readable mirror.

## Runtime

| Layer | Choice | Version |
|---|---|---|
| OS — DB appliance (`srirampc`) | Debian 13 (trixie) | 13.x |
| OS — prod app host | Ubuntu 24.04 LTS | 24.04 |
| OS — dev laptop | Linux Mint 22 | 22 |
| Language | Python | **3.14** |
| Package manager | uv | latest |
| Config | pydantic + pydantic-settings | 2.x |
| MCP | `mcp` (official Python SDK v1) | **1.30.0** |
| ASGI | starlette + uvicorn | 0.50 / 0.48 |
| HTTP client | httpx | 0.28.1 |
| Logging | structlog | 24.x |

## Clients and channels

| Thing | Choice |
|---|---|
| Muse | Meta Muse custom connector — single API key |
| Discord | webhook (no SDK) |
| Resend | `resend` SDK (primary email) |
| Mailgun | `mailgun` SDK (fallback email) |

## Storage (later phases only — not for this POC)

| Layer | Choice | Version |
|---|---|---|
| SQLite | stdlib `sqlite3` + aiosqlite | 0.20 |
| DuckDB | duckdb | 1.5.6 |
| Columnar | pyarrow | 18.x |
| Dataframe | polars | 1.x |
| Numerics | numpy / scipy | 2.x / 1.14 |

## Development

| Layer | Choice |
|---|---|
| Tests | pytest, pytest-asyncio, pytest-cov, hypothesis, freezegun, respx |
| Lint | ruff |
| Types | mypy strict |
| Hooks | pre-commit |
| Spec-driven | OpenSpec (to be confirmed before Session 3) |
| AI coding | OpenCode with router-based models |

## Infrastructure

| Layer | Choice |
|---|---|
| VPN | Tailscale |
| Public ingress | Cloudflare Tunnel `quantflow-interface` |
| Origin auth (Muse) | single `X-Api-Key` header |
| Origin auth (admin/curl) | Cloudflare Access service token |
| Secrets store | Bitwarden Secrets Manager (`bws`) |
| Secret delivery | systemd-creds (prod); shell env (POC) |
| Process supervisor | systemd (foreground for POC) |
| Containerization | none (ADR-002) |

## Not in stack (requires ADR to add)

PostgreSQL, MySQL, MariaDB, Redis, Memcached, ORMs, Alembic, pandas, the `fastmcp` package, Celery / RQ / dramatiq, Prometheus / Grafana / Loki, Docker / Podman / Kubernetes, PyTorch / TensorFlow / JAX, Poetry / pipenv / pip-tools, black / flake8 / isort / pyupgrade, bandit, pyright, conda / mamba, **ThetaData**.

Substitutes:

- SQLite + DuckDB cover storage; no server DB
- In-process scheduler and caches; no Redis
- Hand-written SQL + forward-only migration runner; no ORM, no Alembic
- polars covers dataframes; no pandas
- `mcp==1.30.0` already contains `mcp.server.fastmcp`; the separate `fastmcp` PyPI package is excluded
- SPEC Vol 5 §O defines observability in-process; no Prometheus/Grafana/Loki
- ADR-002 excludes containers
- SPEC Vol 6 §F defers ML; no torch/tensorflow/jax
- uv replaces Poetry/pipenv/pip-tools, conda/mamba
- ruff replaces black/flake8/isort/pyupgrade
- mypy strict replaces pyright

## Version policy

1. `uv.lock` pins every Python dependency. Never hand-edit.
2. Patch/minor bump: `uv lock --upgrade-package X`, one commit.
3. Major bump or new dependency: ADR + PR.
4. Python version bump: ADR + all tool configs + full acceptance.
5. System packages documented in `docs/PREREQUISITES.md`.
6. Secrets live in Bitwarden Secrets Manager. No `.env` with real values ever committed.

---

# PART 1 — WHAT THIS POC PROVES

| Proved | Not proved |
|---|---|
| Muse reaches an MCP origin over Streamable HTTP | Any pipeline step |
| Single `X-Api-Key` is accepted end to end | Any market-data correctness |
| Cloudflare Tunnel routes to the origin | Anything about production auth |
| Cloudflare Access denies unauthenticated admin/curl | Anything about real reports |
| Origin denies missing and wrong API key | Anything about storage |
| Response ID matches server log | Anything about later phases |

---

# PART 2 — DECISIONS LOCKED

| # | Decision | Status |
|---|---|---|
| 2.1 | Muse edge auth = single `X-Api-Key`; Access only for admin/curl | ✅ |
| 2.2 | Connectivity created once with final names (tunnel `quantflow-interface`, hostname `interface.<yourdomain>`, Bitwarden project `QuantFlow-Interface`) | ✅ |
| 2.3 | No containers; uv + pyproject + bootstrap.sh | ✅ |
| 2.4 | Foreground only; no systemd for the POC | ✅ |
| 2.5 | Code lives in `src/quantflow/adapters/mcp/`; Feature 070 extends | ✅ |
| 2.6 | Nothing touches `/data`; no database | ✅ |

---

# PART 3 — PREREQUISITES

**Status:** ⬜ `docs/PREREQUISITES.md` and `scripts/bootstrap.sh` not yet created.

System packages:

- `python3-venv`, `python3-dev`, `build-essential`
- `git`, `curl`, `ca-certificates`
- `uv` (official installer)
- `cloudflared` (Cloudflare apt repo)
- `bws` (Bitwarden Secrets Manager CLI)
- `jq` (helper for reading the local UUID map)

Create `scripts/bootstrap.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

sudo apt-get update
sudo apt-get install -y \
    python3-venv python3-dev build-essential \
    git curl ca-certificates jq

if ! command -v uv >/dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # shellcheck disable=SC1091
    source "$HOME/.bashrc"
fi

if ! command -v cloudflared >/dev/null 2>&1; then
    sudo mkdir -p --mode=0755 /usr/share/keyrings
    curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg \
        | sudo tee /usr/share/keyrings/cloudflare-main.gpg >/dev/null
    echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared any main" \
        | sudo tee /etc/apt/sources.list.d/cloudflared.list
    sudo apt-get update
    sudo apt-get install -y cloudflared
fi

if ! command -v tailscale >/dev/null 2>&1; then
    curl -fsSL https://tailscale.com/install.sh | sh
fi

if ! command -v bws >/dev/null 2>&1; then
    curl -fsSL https://bws.bitwarden.com/install | sh
fi

cd "$(git rev-parse --show-toplevel)"
uv sync --frozen
echo "Bootstrap complete."
```

Once per machine:

```bash
cd ~/src/quant-flow-system
chmod +x scripts/bootstrap.sh
./scripts/bootstrap.sh
```

**Checklist:**

| # | Item | Status |
|---|---|---|
| 3.1 | `docs/PREREQUISITES.md` created | ⬜ |
| 3.2 | `scripts/bootstrap.sh` created and executable | ⬜ |
| 3.3 | `./scripts/bootstrap.sh` run successfully on dev host | ⬜ |
| 3.4 | `uv`, `cloudflared`, `bws`, `jq` all present | ⬜ |
| 3.5 | `docs/HOST_INVENTORY.md` filled | ⬜ |

---

# PART 4 — PHASE 0 — REPO STATE

**Status:** ⬜ not started.

Required before starting:

- `foundation-complete` tag exists
- `pyproject.toml` contains `requires-python = ">=3.14"`
- `uv sync --frozen` succeeds
- `uv run python -c "import pydantic; print(pydantic.VERSION)"` prints a version

```bash
cd ~/src/quant-flow-system
git tag --list | grep foundation-complete
uv run python -c "import pydantic, mcp; print('ok')"
```

If `mcp` is not importable:

```bash
uv add "mcp==1.30.0" "starlette>=0.50" "uvicorn[standard]>=0.48" \
       "httpx>=0.28,<0.29" "structlog>=24.4" \
       "pydantic>=2.9" "pydantic-settings>=2.5"
uv add --dev pytest pytest-asyncio pytest-cov ruff mypy
uv lock && uv sync --frozen
uv run python -c "import mcp; print(mcp.__version__)"
```

Expected: `1.30.0`.

**Checklist:**

| # | Item | Status |
|---|---|---|
| 4.1 | `foundation-complete` tag present | ⬜ |
| 4.2 | `uv sync --frozen` succeeds | ⬜ |
| 4.3 | `import pydantic` prints a version | ⬜ |
| 4.4 | `import mcp` prints `1.30.0` | ⬜ |

---

# PART 5 — PHASE 1 — LOCAL MCP WITH X-API-KEY

**Status:** ⬜ not started.

## 5.1 Config template

Create `config/.env.example`:

```bash
POC_HOST=127.0.0.1
POC_PORT=8765
POC_API_KEY=CHANGE_ME
POC_PUBLIC_HOST=
```

## 5.2 File — `src/quantflow/adapters/mcp/api_key.py`

```python
"""X-Api-Key gate. Wraps any ASGI app."""
from __future__ import annotations

import hmac
import logging

from starlette.datastructures import Headers
from starlette.responses import JSONResponse

log = logging.getLogger(__name__)


class ApiKeyGate:
    def __init__(self, app, api_key: str) -> None:
        if not api_key or len(api_key) < 16:
            raise ValueError("api_key must be >= 16 chars")
        self.app = app
        self._expected = api_key.encode()

    async def __call__(self, scope, receive, send):
        if scope["type"] == "lifespan":
            return await self.app(scope, receive, send)
        if scope["type"] != "http":
            return
        headers = Headers(scope=scope)
        provided = headers.get("x-api-key", "")
        if not provided:
            log.info("auth_denied reason=missing_key path=%s", scope["path"])
            return await self._reject(scope, receive, send, "AUTH_REQUIRED")
        if not hmac.compare_digest(provided.encode(), self._expected):
            log.info("auth_denied reason=invalid_key path=%s", scope["path"])
            return await self._reject(scope, receive, send, "INVALID_KEY")
        await self.app(scope, receive, send)

    async def _reject(self, scope, receive, send, code):
        resp = JSONResponse(
            {"error": code},
            status_code=401,
            headers={
                "WWW-Authenticate": "ApiKey",
                "Cache-Control": "no-store",
            },
        )
        await resp(scope, receive, send)
```

## 5.3 File — `src/quantflow/adapters/mcp/server.py`

```python
"""Transport-only MCP server. One read-only tool: hello(name, nonce)."""
from __future__ import annotations

import logging as _logging
import os
import time
import uuid
from contextlib import asynccontextmanager

import structlog
import uvicorn
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from quantflow.adapters.mcp.api_key import ApiKeyGate

log = structlog.get_logger("quantflow.mcp.server")

HOST = os.environ.get("POC_HOST", "127.0.0.1")
PORT = int(os.environ.get("POC_PORT", "8765"))


def create_app(api_key: str, public_host: str | None = None) -> Starlette:
    allowed_hosts = [f"127.0.0.1:{PORT}", f"localhost:{PORT}"]
    allowed_origins = [f"http://127.0.0.1:{PORT}", f"http://localhost:{PORT}"]
    if public_host:
        allowed_hosts += [public_host, f"{public_host}:443"]
        allowed_origins.append(f"https://{public_host}")

    mcp = FastMCP(
        "QuantFlow",
        instructions="Transport POC. One read-only synthetic tool.",
        host=HOST,
        port=PORT,
        stateless_http=True,
        json_response=True,
        streamable_http_path="/mcp",
        max_request_body_size=8192,
        log_level="WARNING",
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=allowed_hosts,
            allowed_origins=allowed_origins,
        ),
    )

    ro = ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    )

    @mcp.tool(annotations=ro)
    async def hello(name: str, nonce: str) -> dict:
        """Echo name and nonce. Return a fresh server response_id."""
        if not name or len(name) > 64:
            raise ValueError("name must be 1-64 chars")
        if not nonce or len(nonce) < 16 or len(nonce) > 128:
            raise ValueError("nonce must be 16-128 chars")
        response_id = str(uuid.uuid4())
        log.info("tool=hello response_id=%s nonce_prefix=%s",
                 response_id, nonce[:8])
        return {
            "message": f"hello {name}",
            "nonce": nonce,
            "response_id": response_id,
            "server_time_utc": time.strftime(
                "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
            ),
            "auth_mode": "api_key",
            "synthetic": True,
        }

    mcp_app = mcp.streamable_http_app()

    @asynccontextmanager
    async def lifespan(app):
        async with mcp.session_manager.run():
            yield

    async def health(_request):
        return JSONResponse({
            "status": "ok",
            "service": "quantflow-transport-poc",
            "synthetic_only": True,
        })

    app = Starlette(
        routes=[Route("/healthz", health), Mount("/", app=mcp_app)],
        lifespan=lifespan,
    )
    return ApiKeyGate(app, api_key)


def main() -> None:
    _logging.basicConfig(level=_logging.INFO)
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ],
    )
    api_key = os.environ.get("POC_API_KEY")
    if not api_key:
        raise SystemExit("POC_API_KEY required")
    public_host = os.environ.get("POC_PUBLIC_HOST") or None
    app = create_app(api_key, public_host)
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        proxy_headers=False,
        access_log=False,
        limit_concurrency=16,
        timeout_keep_alive=5,
    )


if __name__ == "__main__":
    main()
```

## 5.4 File — `src/quantflow/cli/mcp_probe.py`

```python
"""MCP probe. Connects, lists tools, calls hello with a fresh nonce."""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import secrets
import sys

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


async def run(url: str, api_key: str, nonce: str | None = None) -> dict:
    nonce = nonce or secrets.token_hex(16)
    headers = {"x-api-key": api_key}
    async with httpx.AsyncClient(
        headers=headers, timeout=15, follow_redirects=False
    ) as http:
        health_url = url.replace("/mcp", "/healthz")
        h = await http.get(health_url)
        if h.status_code != 200:
            raise RuntimeError(f"healthz returned {h.status_code}")
        async with streamable_http_client(url, http_client=http) as (r, w, _):
            async with ClientSession(r, w) as session:
                init = await session.initialize()
                tools = sorted(
                    t.name for t in (await session.list_tools()).tools
                )
                call = await session.call_tool(
                    "hello", {"name": "operator", "nonce": nonce}
                )
                if call.isError:
                    raise RuntimeError("hello tool returned error")
                payload = call.structuredContent or json.loads(
                    call.content[0].text
                )
                return {
                    "protocol_version": init.protocolVersion,
                    "tools": tools,
                    "hello": payload,
                }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="http://127.0.0.1:8765/mcp")
    p.add_argument("--api-key", default=None)
    p.add_argument("--nonce", default=None)
    args = p.parse_args()

    api_key = args.api_key or os.environ.get("POC_API_KEY")
    if not api_key:
        print("POC_API_KEY required", file=sys.stderr)
        sys.exit(2)

    try:
        result = asyncio.run(run(args.url, api_key, args.nonce))
    except Exception as exc:
        print(json.dumps({"ok": False, "error": type(exc).__name__}))
        sys.exit(1)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
```

## 5.5 Local smoke test

Terminal A:

```bash
cd ~/src/quant-flow-system
export POC_API_KEY="$(openssl rand -hex 32)"
echo "POC_API_KEY=$POC_API_KEY" > config/.env.local
echo "POC_HOST=127.0.0.1" >> config/.env.local
chmod 600 config/.env.local
uv run python -m quantflow.adapters.mcp.server
```

Terminal B:

```bash
cd ~/src/quant-flow-system
source config/.env.local

# No key → 401
curl -s -o /dev/null -w '%{http_code}\n' \
  -X POST http://127.0.0.1:8765/mcp \
  -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
# expect: 401

# Wrong key → 401
curl -s -o /dev/null -w '%{http_code}\n' \
  -X POST http://127.0.0.1:8765/mcp \
  -H 'x-api-key: wrong' -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
# expect: 401

# Correct key → MCP probe
uv run python -m quantflow.cli.mcp_probe --url http://127.0.0.1:8765/mcp
```

Expected probe output:

```json
{
  "protocol_version": "2025-11-25",
  "tools": ["hello"],
  "hello": {
    "message": "hello operator",
    "nonce": "<the 32-hex nonce>",
    "response_id": "<uuid>",
    "server_time_utc": "...",
    "auth_mode": "api_key",
    "synthetic": true
  }
}
```

Match the `response_id` to the Terminal A log line.

**Gate LOCAL_MCP.** No key → 401. Wrong key → 401. Correct key → response_id echoed back and matching log. If this fails, do not proceed.

**Checklist:**

| # | Item | Status |
|---|---|---|
| 5.1 | `config/.env.example` created | ⬜ |
| 5.2 | `api_key.py` created | ⬜ |
| 5.3 | `server.py` created | ⬜ |
| 5.4 | `mcp_probe.py` created | ⬜ |
| 5.5 | Server starts without error | ⬜ |
| 5.6 | No-key request → 401 | ⬜ |
| 5.7 | Wrong-key request → 401 | ⬜ |
| 5.8 | Correct key → probe passes | ⬜ |
| 5.9 | `response_id` in probe matches server log | ⬜ |

---

# PART 6 — PHASE 2 — CLOUDFLARE TUNNEL AND ACCESS

**Status:** ⬜ not started.

## 6.1 Tunnel (one-time, reused forever)

```bash
cloudflared tunnel login
cloudflared tunnel create quantflow-interface
# note the UUID
cloudflared tunnel route dns quantflow-interface interface.<yourdomain>
```

Tunnel config at `~/.cloudflared/quantflow-interface.yml`:

```yaml
tunnel: <tunnel-uuid>
credentials-file: /home/<you>/.cloudflared/<tunnel-uuid>.json
ingress:
  - hostname: interface.<yourdomain>
    path: ^/(mcp|healthz)$
    service: http://127.0.0.1:8765
    originRequest:
      httpHostHeader: interface.<yourdomain>
  - service: http_status:404
```

Validate:

```bash
cloudflared tunnel --config ~/.cloudflared/quantflow-interface.yml \
  ingress validate
```

## 6.2 Access app for admin/curl

Cloudflare dashboard → Zero Trust → Access → Applications → Add → Self-hosted:

| Field | Value |
|---|---|
| Name | `quantflow-interface` |
| Hostname | `interface.<yourdomain>` |
| Path | blank |
| Policy 1 | Allow — your operator email |
| Policy 2 | Service Auth — new token `quantflow-interface-admin` |

Copy the service token's Client ID and Secret. Store as Bitwarden items `ACCESS_CLIENT_ID` and `ACCESS_CLIENT_SECRET` in project `QuantFlow-Interface`.

## 6.3 Restart server with public host

Terminal A:

```bash
cd ~/src/quant-flow-system
export POC_PUBLIC_HOST=interface.<yourdomain>
uv run python -m quantflow.adapters.mcp.server
```

Terminal C:

```bash
cloudflared tunnel --config ~/.cloudflared/quantflow-interface.yml run
```

## 6.4 Access check

```bash
# Anonymous
curl -s -o /dev/null -w '%{http_code}\n' \
  https://interface.<yourdomain>/healthz
# expect: 302 or 403

# Access token only, no API key
curl -s -o /dev/null -w '%{http_code}\n' \
  -H "CF-Access-Client-Id: $ACCESS_CLIENT_ID" \
  -H "CF-Access-Client-Secret: $ACCESS_CLIENT_SECRET" \
  https://interface.<yourdomain>/healthz
# expect: 401

# Both
curl -s \
  -H "CF-Access-Client-Id: $ACCESS_CLIENT_ID" \
  -H "CF-Access-Client-Secret: $ACCESS_CLIENT_SECRET" \
  https://interface.<yourdomain>/healthz | jq
# expect: {"status":"ok", ...}
```

**Gate TUNNEL_ROUTING.** Anonymous 302/403. Access-token-only 401. Both headers → 200.

**Checklist:**

| # | Item | Status |
|---|---|---|
| 6.1 | Tunnel `quantflow-interface` created | ⬜ |
| 6.2 | DNS route `interface.<yourdomain>` created | ⬜ |
| 6.3 | Tunnel YAML written and validated | ⬜ |
| 6.4 | Access app created | ⬜ |
| 6.5 | Access service token created | ⬜ |
| 6.6 | Anonymous request → 302/403 | ⬜ |
| 6.7 | Access-only request → 401 | ⬜ |
| 6.8 | Both headers → 200 | ⬜ |

---

# PART 7 — PHASE 3 — BITWARDEN AND PUBLIC PROBE

**Status:** ⬜ not started.

## 7.1 Bitwarden project

Web vault → Secrets Manager → project `QuantFlow-Interface` → new secret `INTERFACE_API_KEY`, value = `openssl rand -hex 32`.

Local UUID map (outside the repo):

```bash
mkdir -p ~/.config/quantflow
cat > ~/.config/quantflow/secret-map.json <<'EOF'
{
  "backend": "bws",
  "ids": {
    "INTERFACE_API_KEY": "<uuid-here>"
  }
}
EOF
chmod 600 ~/.config/quantflow/secret-map.json
```

## 7.2 Public probe

```bash
export BWS_ACCESS_TOKEN="<poc-scoped-machine-token>"
export POC_API_KEY="$(
  bws secret get \
    "$(jq -r '.ids.INTERFACE_API_KEY' ~/.config/quantflow/secret-map.json)" \
    --output json | jq -r '.value'
)"

uv run python -m quantflow.cli.mcp_probe \
  --url https://interface.<yourdomain>/mcp \
  --api-key "$POC_API_KEY"
```

**Gate PUBLIC_MCP.** Valid key → pass. Wrong key → probe fails with 401.

**Checklist:**

| # | Item | Status |
|---|---|---|
| 7.1 | Bitwarden project created | ⬜ |
| 7.2 | Secret `INTERFACE_API_KEY` stored | ⬜ |
| 7.3 | `secret-map.json` written | ⬜ |
| 7.4 | Public probe with `bws`-fetched key passes | ⬜ |

---

# PART 8 — PHASE 4 — MUSE END-TO-END

**Status:** ⬜ not started.

## 8.1 Fresh nonce

```bash
openssl rand -hex 16
```

## 8.2 Muse connector prompt

```
Create a reusable read-only custom connector named "QuantFlow Transport POC".

Endpoint: https://interface.<yourdomain>/mcp
Transport: MCP Streamable HTTP. Not stdio. Not legacy SSE.

Authentication: ONE custom request header on every request:
  X-Api-Key: <the INTERFACE_API_KEY from Bitwarden>
Enter it through your secure credential UI. Never in chat, source, URLs or logs.

Initialize, list tools (expect exactly one: hello), then call hello once with:
  name  = "operator"
  nonce = "<the 32-hex value above>"

Show the returned message, nonce, response_id, server_time_utc and auth_mode.
auth_mode must be "api_key". Never invent a result if the call fails.

No polling, no browser, no extra tools. Stop after two failures.
If the connector cannot send a custom X-Api-Key header to the exact hostname,
report MUSE_COMPATIBILITY_BLOCKED. Do not remove authentication to make it work.
```

## 8.3 Verify

Muse returns a `response_id`. In Terminal A:

```bash
grep <the response_id>
```

**Gate MUSE_E2E.** Fresh nonce and `response_id` match the origin log line. A model repeating an example without a matching log line is a fail.

**Checklist:**

| # | Item | Status |
|---|---|---|
| 8.1 | Fresh nonce generated | ⬜ |
| 8.2 | Muse connector created | ⬜ |
| 8.3 | Muse `hello` call returns `response_id` | ⬜ |
| 8.4 | `response_id` matches origin log | ⬜ |

---

# PART 9 — PHASE 5 — FAILURE DRILLS

**Status:** ⬜ not started.

| Drill | Expected |
|---|---|
| Kill server mid-request | Muse gets transport error; no stale response |
| Restart server, same API key | New probe succeeds; old `response_id` not reused |
| Rotate `INTERFACE_API_KEY`, restart server | Old key → 401; new key → pass |
| Stop cloudflared | Public probe fails; local probe still works |
| Stop server, keep cloudflared | Public → 502; local refused |

Record each in `docs/reports/poc-transport-report.md`.

**Checklist:**

| # | Drill | Status |
|---|---|---|
| 9.1 | Kill server mid-request | ⬜ |
| 9.2 | Restart with same key | ⬜ |
| 9.3 | Rotate key | ⬜ |
| 9.4 | Stop cloudflared | ⬜ |
| 9.5 | Stop server, keep cloudflared | ⬜ |

---

# PART 10 — DECOMMISSION

**Status:** ⬜ not started. Optional.

To keep tunnel/API key for Session 3:

- Keep: tunnel `quantflow-interface`, DNS, Access app, Bitwarden project.
- Remove only: `config/.env.local` and the running processes.

Full teardown:

```bash
cloudflared tunnel delete quantflow-interface
# Cloudflare dashboard: delete Access app and DNS record
# Bitwarden: delete project QuantFlow-Interface
rm ~/.config/quantflow/secret-map.json
rm ~/.cloudflared/quantflow-interface.yml
```

---

# PART 11 — EXIT CRITERIA

**Status:** ⬜ not started.

- [ ] LOCAL_MCP passes: 401/401/pass, `response_id` matches log
- [ ] TUNNEL_ROUTING passes: 302/401/200
- [ ] PUBLIC_MCP passes: valid key through Access + public hostname
- [ ] MUSE_E2E passes: fresh nonce + matching `response_id` in origin log
- [ ] Failure drills recorded in `docs/reports/poc-transport-report.md`
- [ ] Nothing under `/data` was touched
- [ ] Repo tag `poc-transport-complete`

If MUSE_E2E is blocked but LOCAL_MCP, TUNNEL_ROUTING and PUBLIC_MCP pass, tag `poc-transport-partial` and record the Muse limitation in the report.

---

# PART 12 — HANDOFF

Files created in this POC that Feature 070 keeps:

- `src/quantflow/adapters/mcp/api_key.py` — production auth primitive; Feature 070 extends with role checks.
- `src/quantflow/adapters/mcp/server.py` — Feature 070 adds real tools (`get_health`, `get_pipeline_stage_status`, `get_dq_report`, etc.) alongside `hello`.
- `src/quantflow/cli/mcp_probe.py` — becomes a regression test in `tests/integration/`.
- `docs/reports/poc-transport-report.md` — evidence.

No file is deleted. Only the POC runbook itself is historical.

---

**END OF POC-RUNBOOK-transport.md v2.0**