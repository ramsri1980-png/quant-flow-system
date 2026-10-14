# ADR-004 — MCP SDK version: v1.30.0 vs v2.2.0

## Status
Proposed — decision deferred

## Date
2026-10-14

## Context
The POC transport (Muse -> Cloudflare -> Tunnel -> MCP origin) was
proven on `mcp==1.30.0`, the SDK v1 maintenance line. The latest
release is `mcp==2.2.0`, a full SDK rewrite with these breaking
changes:

- `FastMCP` renamed to `MCPServer`
- `inputSchema` (camelCase) -> `input_schema` (snake_case)
- `McpError` -> `MCPError`
- HTTP transport dependency changed from `httpx` / `httpx-sse`
  to `httpx2`
- `streamablehttp_client` removed/renamed
- `LATEST_PROTOCOL_VERSION` changed value/semantics
- `RootModel` unions replaced with plain unions + `TypeAdapter`

The v1 line continues to receive critical bug fixes and security
patches. It is not abandoned.

Two OpenCode-side facts reduce migration pressure:
1. OpenCode v2.0.24 (already installed) supports both the POC's
   streamable HTTP MCP servers and the existing stdio
   `harness-tools` server. The OpenCode side does not need any
   change.
2. Feature 070 (Muse MCP interface) will rewrite `server.py` and
   `mcp_probe.py` anyway to expose real read-only tools. That is
   the natural moment for an SDK migration.

Feature 005 (domain types, units, clock) does not touch the MCP
layer. Sessions 3 through 6 will not touch the MCP layer. There
is no forced migration window before Feature 070.

## Decision
Deferred. Options retained.

## Options

### A. Stay on mcp==1.30.0 (current)
- Zero rework today.
- v1.30.0 matches the POC transport exactly; the POC report at
  `docs/reports/POC-transport-final.md` remains valid.
- Security patches continue on the v1 line.
- Downside: the SDK is in maintenance mode; new MCP protocol
  features (2026-07-28 spec) are not available.

### B. Upgrade to mcp==2.2.0 now, before Feature 005
- Gets the latest SDK in place before any real code depends on it.
- Downside: rewrites the POC's `server.py` and `mcp_probe.py`
  before the actual tool surface is designed; the rewrite would
  happen twice.
- Downside: invalidates part of the POC transport evidence.

### C. Upgrade to mcp==2.2.0 during Feature 070
- One rewrite: the tool surface and the SDK move together.
- Downside: the migration work is on the critical path for E7.

### D. Dual-pin: v1 for capture, v2 for tools
- Preserves POC evidence while adopting v2 for new work.
- Downside: two SDK versions in one repo is a maintenance and
  attack-surface burden.
- Rejected unless a concrete v1-only need persists.

## Consequences
- Until this ADR is Decided, `mcp==1.30.0` remains pinned in
  `pyproject.toml`.
- Feature 070 planning will reference this ADR and pick between
  Option A and Option C.
- No production code written between now and Feature 070 will
  import the MCP SDK directly.

## Related
- ARCH v5.1.5.1 Vol 3 §F (frozen anti-detection) — unaffected;
  SDK version is not part of the frozen layer.
- `docs/reports/POC-transport-final.md` — the transport evidence
  that depends on v1.30.0.
- SPEC v2.0.5.1 Vol 5 §O.3 — the eventual tool surface for
  Feature 070.
