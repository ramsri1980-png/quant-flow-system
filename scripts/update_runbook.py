#!/usr/bin/env python3
"""Update the QuantFlow runbook.

Appends a timestamped snapshot at the bottom and refreshes the two
top state tables between AUTO markers. Idempotent.

Run after each `git push` (or via the qfpush alias).
"""
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RUNBOOK = (REPO / "docs" / "runbooks" / "QUANTFLOW-RUNBOOK.md").resolve()


def sh(*args):
    return subprocess.check_output(args, text=True, cwd=REPO).strip()  # noqa: S603


def tags():
    return sorted(set(sh("git", "tag", "--list").splitlines()))


def branch():
    return sh("git", "branch", "--show-current") or "(detached)"


def last_commit():
    return sh("git", "log", "-1", "--format=%h %s")


def tree_state():
    return sh("git", "status", "--short") or "(clean)"


def active_changes():
    try:
        out = subprocess.check_output(  # noqa: S603
            ["openspec", "list", "--json"], text=True, cwd=REPO
        )
        data = json.loads(out)
        if isinstance(data, list):
            return [c.get("name", str(c)) if isinstance(c, dict) else str(c) for c in data]
        return data.get("changes", []) or []
    except Exception:
        return []


def completed_features():
    out = []
    for t in tags():
        m = re.match(r"feature-(\d+[a-z]?)-complete$", t)
        if m:
            out.append((m.group(1), t))
    return out


def phase_of(feature_num):
    m = re.match(r"(\d+)", feature_num)
    if not m:
        return "E0"
    n = int(m.group(1))
    for hi, code in [(10, "E0"), (20, "E1"), (30, "E2"), (40, "E3"),
                     (50, "E4"), (60, "E5"), (70, "E6"), (80, "E7")]:
        if n < hi:
            return code
    return "E8"


def build_current_state():
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    b = branch()
    lc = last_commit()
    tree = tree_state()
    ts = tags()
    feats = completed_features()
    active = active_changes()

    rows = []
    for sid, tagname in [
        ("Session 1 (storage)", "session1-complete"),
        ("Session 2 (repo, toolchain, design freeze)", "foundation-complete"),
        ("Session 3 (OpenCode + OpenSpec zero-token setup)", "session3-complete"),
    ]:
        if tagname == "session1-complete" or tagname in ts:
            rows.append(f"| {sid} | COMPLETE |")
    for fid, tagname in feats:
        rows.append(f"| Feature {fid} | COMPLETE — tag `{tagname}` |")

    if active:
        next_action = "Continue active change: " + ", ".join(active)
    else:
        prompts = sorted((REPO / "openspec" / "prompts").glob("[0-9]*.md"))
        done_ids = {fid for fid, _ in feats}
        next_action = "See conflicts-and-gaps.md for open questions"
        for p in prompts:
            m = re.match(r"(\d+[a-z]?)", p.stem)
            if m and m.group(1) not in done_ids:
                slug = p.stem.split("-", 1)[-1].replace("-", " ")
                next_action = f"Feature {m.group(1)} — {slug}"
                break

    tree_line = "clean" if tree == "(clean)" else tree.splitlines()[0]

    lines = [
        f"## CURRENT STATE (auto {now})",
        "",
        "| Item | Status |",
        "|---|---|",
        *rows,
        f"| Repo | branch `{b}` |",
        f"| Working tree | {tree_line} |",
        f"| Tags | {', '.join(f'`{t}`' for t in ts)} |",
        f"| Last commit | `{lc}` |",
        "",
        f"**Next action:** {next_action}",
        "",
    ]
    return "\n".join(lines)

PHASE_NOTES = {
    "E7": "transport primitives proven by POC",
}


def build_overall_progress():
    by_phase = {}
    for fid, _ in completed_features():
        by_phase.setdefault(phase_of(fid), []).append(fid)

    phases = [
        ("E0", "Setup & Foundation", "1–7"),
        ("E1", "Storage & Durability", "8–13"),
        ("E2", "Canonical Event Pipeline", "14–17"),
        ("E3", "Pure Quant Kernels", "18–25"),
        ("E4", "Decision Evidence & Delivery", "26–29"),
        ("E5", "Provider Adapters", "30–35"),
        ("E6", "User Workflows", "36–42"),
        ("E7", "Interface, Ops & Release", "43–48"),
        ("E8", "Forward Research", "49+"),
    ]

    rows = []
    for code, name, sessions in phases:
        done = sorted(by_phase.get(code, []))
        if done:
            status = " · ".join(f"Feature {d} done" for d in done)
        else:
            status = "⬜ Not started"
        rows.append(f"| {code} {name} | {sessions} | {status} |")

    lines = [
        "## OVERALL PROGRESS",
        "",
        "| Phase | Sessions | Status |",
        "|---|---|---|",
        *rows,
    ]

    if PHASE_NOTES:
        lines.append("")
        lines.append("**Phase notes:**")
        for code, note in sorted(PHASE_NOTES.items()):
            lines.append(f"- {code}: {note}")

    lines.append("")
    return "\n".join(lines)


def refresh_top_sections(text):
    for name, builder in [
        ("CURRENT-STATE", build_current_state),
        ("OVERALL-PROGRESS", build_overall_progress),
    ]:
        start = f"<!-- AUTO:{name}:START -->"
        end = f"<!-- AUTO:{name}:END -->"
        if start not in text or end not in text:
            continue
        block = f"{start}\n{builder()}\n{end}"
        text = re.sub(
            re.escape(start) + r".*?" + re.escape(end),
            lambda _m, b=block: b,
            text,
            count=1,
            flags=re.DOTALL,
        )
    return text


def main():
    b = branch()
    log = sh("git", "log", "--oneline", "-10")
    status = sh("git", "status", "--short") or "(clean)"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    block = "\n".join([
        "",
        "### Runbook auto-update - " + now,
        "",
        "Branch: `" + b + "`",
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

    text = RUNBOOK.read_text(encoding="utf-8")
    text = text.rstrip() + "\n" + block
    text = refresh_top_sections(text)
    RUNBOOK.write_text(text, encoding="utf-8")
    print("runbook updated:", RUNBOOK)


if __name__ == "__main__":
    main()
