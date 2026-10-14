# QuantFlow — Tech Stack

**Status:** locked 2026-10-13.
**Rule:** `pyproject.toml` + `uv.lock` are the source of truth.
**Policy:** adding or removing a major dependency requires an ADR.

## Runtime
- Python 3.14
- Package manager: uv
- Config: pydantic + pydantic-settings 2.x
- MCP: `mcp==1.30.0` (official SDK)
- ASGI: starlette + uvicorn
- HTTP client: httpx 0.28.x + tenacity
- Logging: structlog

## Clients and channels
- Muse custom connector (single `X-Api-Key`)
- Discord webhook
- Resend (primary email)
- Mailgun (fallback email)

## Storage (later phases)
- SQLite (stdlib + aiosqlite) for operational state
- DuckDB 1.5.6 for analytical state
- polars, pyarrow, numpy, scipy

## Development
- pytest, pytest-asyncio, pytest-cov, hypothesis, freezegun, respx
- ruff (lint + format)
- mypy strict
- pre-commit

## Infrastructure
- Tailscale
- Cloudflare Tunnel `quantflow-interface`
- Bitwarden Secrets Manager (`bws`)
- systemd-creds (prod) / shell env (POC)
- No containers (ADR-002)

## Not in stack (requires ADR to add)
PostgreSQL, MySQL, MariaDB, Redis, Memcached, ORMs, Alembic, pandas,
the `fastmcp` package, Celery / RQ / dramatiq, Prometheus / Grafana / Loki,
Docker / Podman / Kubernetes, PyTorch / TensorFlow / JAX,
Poetry / pipenv / pip-tools, black / flake8 / isort / pyupgrade,
bandit, pyright, conda / mamba, ThetaData.
