"""Generate src/quantflow/domain/constants.py from ARCH v5.1.5.1 Vol 1 §AI.3.

SPEC V1 §1.4.33: named numeric constants are defined exactly once in AI.3
(the canonical home of every UPPER_SNAKE_CASE named constant) and referenced
by name elsewhere. Values are emitted verbatim from the frozen bundle
(docs/reference/CURRENT). Constants in the AI.3 "[RECOMMENDED ... approval]"
block (C12 dealer/greeks set) get explicit NAME_APPROVAL_PENDING = True
companions so features 031-036 cannot adopt them silently.

Usage: python3 scripts/gen_constants.py [--output PATH]
"""

import argparse
import re
import sys
from pathlib import Path
from typing import NamedTuple

REPO_ROOT = Path(__file__).resolve().parent.parent
CURRENT_BUNDLE = REPO_ROOT / "docs" / "reference" / "CURRENT"
ARCH_VOL1 = CURRENT_BUNDLE / "ARCH_v5.1.5.1_Vol1_Foundation.md"
DEFAULT_OUTPUT = REPO_ROOT / "src" / "quantflow" / "domain" / "constants.py"

AI3_START = re.compile(r"^AI\.3\b")
NEXT_SUBSECTION = re.compile(r"^AI\.[4-9]\b")
# Entry: indented NAME value, value verbatim (int or float), optional comment.
ENTRY = re.compile(r"^\s+([A-Z][A-Z0-9_]*)\s+(-?\d+(?:\.\d+)?)\s*(?:#.*)?$")
APPROVAL_MARKER = "[RECOMMENDED"


class Constant(NamedTuple):
    """One AI.3 named constant: name, verbatim value, approval-pending flag."""

    name: str
    value: str
    approval_pending: bool


# A bare UPPER_SNAKE first token; used to tell constant-like lines from prose.
CONSTANT_HEAD = re.compile(r"^[A-Z][A-Z0-9_]*\b")


def _looks_like_constant(stripped: str) -> bool:
    """True when a non-entry AI.3 line still looks like a constant (drift).

    Prose/group labels fail this test: their head is mixed-case, starts with a
    digit, or continues in lowercase after an UPPER_SNAKE first token (e.g.
    "ZERO_DTE ticker scope ..."), so they remain skippable prose.
    """
    head = CONSTANT_HEAD.match(stripped)
    if head is None:
        return False
    remainder = stripped[head.end() :].lstrip()
    if not remainder:
        return True  # bare name, value missing: format drift, not prose
    first = remainder[0]
    return first.isdigit() or first.isupper() or first in "=:.+-'\""


def parse_ai3_constants(text: str) -> list[Constant]:
    """Parse the AI.3 subsection; fail closed on duplicate names.

    Anchors on the LAST "AI.3" section header so changelog mentions of
    "AI.3" earlier in the document cannot shift the start (scope is the
    AI.3 subsection only, per SPEC V1 Sec 1.4.33 / spec delta).
    """
    lines = text.splitlines()
    starts = [i for i, line in enumerate(lines) if AI3_START.match(line)]
    if not starts:
        raise ValueError("AI.3 subsection not found in ARCH Vol 1")
    start = starts[-1]
    entries: list[Constant] = []
    seen: set[str] = set()
    pending = False
    for line in lines[start + 1 :]:
        if NEXT_SUBSECTION.match(line):
            break
        if APPROVAL_MARKER in line:
            pending = True
            continue
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = ENTRY.match(line)
        if not match:
            if _looks_like_constant(stripped):
                raise ValueError(f"unparsable AI.3 constant line (format drift): {line!r}")
            pending = False  # group label or prose ends the pending block
            continue
        name, value = match.group(1), match.group(2)
        if name in seen:
            raise ValueError(f"duplicate constant {name} in AI.3 (defined exactly once)")
        seen.add(name)
        entries.append(Constant(name, value, pending))
    if not entries:
        raise ValueError("no constants parsed from AI.3 (unparsable doc format?)")
    return entries


def render_constants_module(entries: list[Constant]) -> str:
    """Render the generated module; ruff-format-stable, deterministic."""
    header = (
        '"""Named constants generated from ARCH v5.1.5.1 Vol 1 §AI.3 (SPEC V1 §1.4.33).\n'
        "\n"
        "GENERATED FILE -- do not edit by hand.\n"
        "Regenerate: python3 scripts/gen_constants.py\n"
        "Values are verbatim from the frozen bundle (docs/reference/CURRENT).\n"
        'Approval-pending companions mark the AI.3 "[RECOMMENDED ... approval]"\n'
        "set (C12 dealer/greeks): features 031-036 require recorded operator\n"
        "approval before relying on them (never silently adopted; shadow-only\n"
        "per constitution Sec 7).\n"
        '"""\n'
    )
    body = "".join(f"{c.name} = {c.value}\n" for c in entries)
    pending_entries = [c for c in entries if c.approval_pending]
    pending_block = ""
    if pending_entries:
        pending_block = (
            "\n"
            "# --- AI.3 [RECOMMENDED ... approval] set (C12): approval pending ---\n"
            + "".join(f"{c.name}_APPROVAL_PENDING = True\n" for c in pending_entries)
        )
    return header + "\n" + body + pending_block


def generate(arch_path: Path = ARCH_VOL1) -> str:
    """Read ARCH Vol 1 §AI.3 and render the constants module source."""
    return render_constants_module(parse_ai3_constants(arch_path.read_text()))


def main(argv: list[str] | None = None) -> int:
    """Write the generated module (default: domain/constants.py)."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    args.output.write_text(generate())
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
