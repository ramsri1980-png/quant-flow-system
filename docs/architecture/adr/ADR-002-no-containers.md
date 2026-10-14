# ADR-002 — No containers

Status: Accepted
Date: 2026-10-13

## Context
The frozen architecture (ARCH Vol 1 §A.1, §B.1) defines three
systemd processes on one machine with a LUKS-encrypted SATA
volume at /data. DuckDB and SQLite are embedded stores with
single-writer discipline. Observability writes to filesystem
paths and journald.

## Decision
Do not containerize. Reproduce Python dependencies with
`uv` + `pyproject.toml` + `uv.lock`. Install system packages
with `scripts/bootstrap.sh`. Supervise with systemd.

## Alternatives
- Docker / Podman / Kubernetes: rejected. Adds cgroup and bind
  mount complexity on top of systemd, obscures SQLite file
  locking, duplicates memory caps.
- Nix: rejected. Higher operator overhead for a single-machine
  deployment; no operational benefit.

## Consequences
- A new machine is provisioned by `./scripts/bootstrap.sh`
  followed by `uv sync --frozen`.
- Adding containerization later requires a new ADR.
