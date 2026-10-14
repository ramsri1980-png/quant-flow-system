# QuantFlow POC — Transport Hello World

**Status:** COMPLETE — 2026-10-14
**Tag:** poc-transport-complete
**Nature:** Transport-only proof. Muse reaches one MCP tool over HTTPS through Cloudflare Tunnel with a single X-Api-Key header. No database, no pipeline, no provider adapters, no /data access.

---

## RESULT

All five gates pass, including Muse end-to-end with a matching response_id.

| Gate | Result | Evidence |
|---|---|---|
| LOCAL_MCP | PASS | 401 / 401 / probe returns response_id |
| TUNNEL_ROUTING | PASS | 302 anon / 401 token-only / 200 both |
| Access-layer | PASS | anonymous /healthz redirects to cloudflareaccess.com |
| PUBLIC_MCP | PASS | probe via Bitwarden-fetched key returns fresh response_id |
| MUSE_E2E | PASS | response_id=e7049263-c532-495c-83df-9fa266ac7acd matched origin log |

Muse -> Cloudflare edge -> WAF -> Tunnel -> origin 127.0.0.1:8765 -> X-Api-Key gate -> hello tool -> back to Muse.

---

## 1. WHAT THIS POC PROVED

| Proved | Not proved |
|---|---|
| Muse reaches an MCP origin over Streamable HTTP | Any pipeline step |
| Single X-Api-Key accepted end to end | Any market-data correctness |
| Cloudflare Tunnel routes to the origin | Anything about production auth |
| Access denies unauthenticated admin/curl on /healthz | Anything about real reports |
| /mcp reachable with API key only | Anything about storage |
| WAF Browser Integrity Check skippable for /mcp | Anything about later phases |
| Server response_id matches client's | - |

---

## 2. ENVIRONMENT

| Item | Value |
|---|---|
| Domain | qflowlab.trade (Cloudflare Registrar) |
| Public hostname | interface.qflowlab.trade |
| Tunnel | quantflow-interface |
| Tunnel config | ~/.cloudflared/quantflow-interface.yml |
| Origin | 127.0.0.1:8765 |
| OS | Linux Mint 22 |
| Python | 3.14 |
| MCP SDK | mcp==1.30.0 |
| Secrets store | Bitwarden Secrets Manager, project quantflow |
| Machine account | QuantFlow-App (Can read) |

---

## 3. WHAT WE DID

### 3.1 Prerequisites
Installed: uv, cloudflared (Cloudflare apt repo), bws, jq, xclip.

### 3.2 Files created
| File | Purpose |
|---|---|
| src/quantflow/adapters/mcp/api_key.py | ASGI middleware. hmac.compare_digest on X-Api-Key; 401 on missing/wrong. |
| src/quantflow/adapters/mcp/server.py | FastMCP server. One read-only tool hello(name, nonce). /healthz endpoint. DNS-rebinding protection aware of POC_PUBLIC_HOST. |
| src/quantflow/cli/mcp_probe.py | CLI probe. Initializes MCP, lists tools, calls hello, prints JSON. |
| config/.env.example | Template. |

### 3.3 Tunnel and DNS

    cloudflared tunnel login
    cloudflared tunnel create quantflow-interface
    cloudflared tunnel route dns quantflow-interface interface.qflowlab.trade
    cloudflared tunnel --config ~/.cloudflared/quantflow-interface.yml ingress validate

Config at ~/.cloudflared/quantflow-interface.yml:

    tunnel: <UUID>
    credentials-file: /home/sriram/.cloudflared/<UUID>.json
    ingress:
      - hostname: interface.qflowlab.trade
        path: ^/(mcp|healthz)$
        service: http://127.0.0.1:8765
        originRequest:
          httpHostHeader: interface.qflowlab.trade
      - service: http_status:404

### 3.4 Cloudflare Access
- App quantflow-interface, hostname interface.qflowlab.trade
- Path: /healthz — leaves /mcp outside Access
- Policy operator — Allow / Emails
- Policy admin-token — Service Auth / Service Token quantflow-interface-admin

### 3.5 WAF skip rule
Added "Allow MCP" rule — expression (http.request.uri.path contains "/mcp"), action Skip with Browser Integrity Check ticked. Bot Fight Mode: Off.

### 3.6 Bitwarden
Project quantflow. Secrets stored manually via web UI:
- POC_API_KEY — 64-hex, matches server
- ACCESS_CLIENT_ID
- ACCESS_CLIENT_SECRET — rotated after chat exposure

Access token at ~/.config/quantflow/bws.env (chmod 600). UUID map at ~/.config/quantflow/secret-map.json. Plaintext config/.env.local retired.

### 3.7 Muse connector
- Endpoint https://interface.qflowlab.trade/mcp
- Transport: MCP Streamable HTTP
- Auth: single X-Api-Key header entered via Muse's secure credential link

---

## 4. WHAT BROKE AND HOW WE FIXED IT

| Problem | Symptom | Fix |
|---|---|---|
| cloudflared missing | command not found | Installed via Cloudflare apt repo |
| YAML pasted into shell | syntax error near unexpected token | Wrote config via heredoc / editor |
| Env file without key prefix | POC_API_KEY empty | Rewrote with printf POC_API_KEY=%s |
| bws secret create 404 | Resource not found | Machine account had Can read; created secrets manually in web UI |
| Probe pre-check failed on /healthz | ok:false, error:RuntimeError | Made /healthz non-fatal in mcp_probe.py — warns instead of raising; /healthz is behind Access by design |
| Cloudflare error 1010 | Muse got "browser signature banned" — request never reached origin | Browser Integrity Check blocked non-browser User-Agent. Created WAF Custom Rule to Skip BIC for /mcp; turned Bot Fight Mode off |
| Access credentials pasted in chat | Exposure | Rotated service token (Revoke immediately); updated Bitwarden and access.env |

---

## 5. EVIDENCE

### 5.1 DNS resolves to Cloudflare edge

    $ dig +short interface.qflowlab.trade
    72.67.184.220
    104.21.68.16

### 5.2 Access layer over public HTTPS

| Request | Response |
|---|---|
| GET /healthz (no headers) | 302 -> blue-darkness-6530.cloudflareaccess.com/cdn-cgi/access/login/... |
| GET /healthz with Access token only | 401 with www-authenticate: ApiKey |
| GET /healthz with Access + API key | 200 {"status":"ok","service":"quantflow-transport-poc","synthetic_only":true} |
| POST /mcp with X-Api-Key only | Full JSON-RPC response (not behind Access) |

### 5.3 MUSE_E2E

Muse called hello with name="sriram".

Origin log (Terminal A):

    {"event": "tool=hello response_id=e7049263-c532-495c-83df-9fa266ac7acd nonce_prefix=764616c6", "timestamp": "2026-10-14T19:26:44.949869Z", "level": "info"}

Muse returned the same response_id: e7049263-c532-495c-83df-9fa266ac7acd.

Match confirmed.

### 5.4 Public probe (Bitwarden-fetched key)

    warning: healthz returned 302 (expected if behind Cloudflare Access)
    {
      "protocol_version": "2025-11-25",
      "tools": ["hello"],
      "hello": {
        "message": "hello operator",
        "nonce": "...",
        "response_id": "...",
        "server_time_utc": "...",
        "auth_mode": "api_key",
        "synthetic": true
      }
    }

---

## 6. SECRETS POSTURE

| Secret | Location | Status |
|---|---|---|
| POC_API_KEY | Bitwarden quantflow | stored, matches server |
| ACCESS_CLIENT_ID | Bitwarden quantflow | stored |
| ACCESS_CLIENT_SECRET | Bitwarden quantflow | rotated after exposure |
| BWS_ACCESS_TOKEN | ~/.config/quantflow/bws.env (chmod 600) | only disk-resident secret |
| config/.env.local | - | removed |
| config/.env.local.bak | - | removed |

---

## 7. DECISIONS LOCKED

1. Muse edge auth = single X-Api-Key; Access only for admin/curl
2. Connectivity created once with final names (tunnel, hostname, Bitwarden project)
3. No containers; uv + pyproject
4. Foreground only; no systemd for the POC
5. Code lives in src/quantflow/adapters/mcp/
6. Nothing touches /data; no database
7. Access scoped to /healthz only. /mcp outside Access.
8. Domain via Cloudflare Registrar (no nameserver delegation)
9. WAF Custom Rule skips BIC on /mcp; Bot Fight Mode off
10. Bitwarden is the only secret store; no plaintext env file in repo
11. Access service token rotated after chat exposure

---

## 8. WHAT WAS NOT TOUCHED

- No file under /data was read or written
- No database
- No pipeline step
- No provider adapter
- No real report data

The POC exercised transport only.

---

## 9. CLOUDFLARE STATE CARRIED FORWARD

- Tunnel quantflow-interface
- DNS CNAME interface.qflowlab.trade -> tunnel UUID
- Access app quantflow-interface, path /healthz, two policies
- Access service token quantflow-interface-admin (rotated)
- WAF Custom Rule "Allow MCP"
- Bot Fight Mode: off for POC (revisit for production)

---

## 10. FILES KEPT FOR FEATURE 070

| File | Feature 070 use |
|---|---|
| src/quantflow/adapters/mcp/api_key.py | Production auth primitive; extend with role checks |
| src/quantflow/adapters/mcp/server.py | Add real tools (get_health, get_pipeline_stage_status, get_dq_report) alongside hello |
| src/quantflow/cli/mcp_probe.py | Integration regression test in tests/integration/ |
| docs/reports/POC-transport-final.md | This file — evidence record |

---

## 11. DEFERRED — FAILURE DRILLS (PART 9)

Not run. Can be done anytime; tunnel, Access, and Bitwarden all persist.

| # | Drill | Expected |
|---|---|---|
| 9.1 | Kill server mid-request | Muse gets transport error; no stale response |
| 9.2 | Restart server, same API key | New probe succeeds; old response_id not reused |
| 9.3 | Rotate POC_API_KEY, restart server | Old key -> 401; new key -> pass |
| 9.4 | Stop cloudflared | Public probe fails; local probe still works |
| 9.5 | Stop server, keep cloudflared | Public -> 502; local refused |

---

END OF POC-transport-final.md — POC COMPLETE
