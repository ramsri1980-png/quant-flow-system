# Host Prerequisites

Once per machine.

## System packages
- python3-venv, python3-dev, build-essential
- git, curl, ca-certificates, jq
- uv (official installer)
- cloudflared (Cloudflare apt repo)
- bws (Bitwarden Secrets Manager CLI)
- tailscale (official install script)

## Python dependencies
Reproduced by `uv sync --frozen` from `uv.lock`.
Never `pip install` manually.

## Install
Run `./scripts/bootstrap.sh`. Then `uv sync --frozen`.
