#!/usr/bin/env python3
"""Update runbook with current branch, recent commits, tree status.
Idempotent. Run after each git push (or via qfpush alias)."""
import subprocess
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RUNBOOK = (REPO / "docs" / "runbooks" / "QUANTFLOW-RUNBOOK.md").resolve()


def sh(*args):
    return subprocess.check_output(args, text=True, cwd=REPO).strip()


def main():
    branch = sh("git", "branch", "--show-current")
    log = sh("git", "log", "--oneline", "-10")
    status = sh("git", "status", "--short") or "(clean)"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    block = "\n".join([
        "",
        "### Runbook auto-update - " + now,
        "",
        "Branch: `" + branch + "`",
        "",
        "Recent commits:",
        "```",
        log,
        "```",
        "",
        "Working tree:",
        "```",
        status,
        "```",
        "",
    ])

    text = RUNBOOK.read_text()
    marker = "\n**END OF RUNBOOK"
    if marker in text:
        text = text.replace(marker, block + marker, 1)
    else:
        text = text + block
    RUNBOOK.write_text(text)
    print("updated " + str(RUNBOOK))


if __name__ == "__main__":
    main()
