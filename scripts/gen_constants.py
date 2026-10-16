"""Generate src/quantflow/domain/constants.py from ARCH v5.1.5.1 Vol 1 §AI.3.

SPEC V1 §1.4.33: named numeric constants are defined exactly once in AI.3
(the canonical home of every UPPER_SNAKE_CASE named constant) and referenced
by name elsewhere. Values are emitted verbatim from the frozen bundle
(docs/reference/CURRENT). Constants inside the AI.3 "[RECOMMENDED ...]"
block get explicit NAME_APPROVAL_PENDING = True companions so downstream
features cannot adopt them silently. The block's label is read from the
marker text at generation time; this script hardcodes no label.

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
# The bracketed text of the approval marker, used as the pending-set label so
# the generated docstring never hardcodes a stale group name (005c Q5).
APPROVAL_LABEL = re.compile(r"\[([^\[\]]+)\]")


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


def parse_pending_label(text: str) -> str | None:
    """Return the AI.3 "[RECOMMENDED ...]" marker's bracketed text, or None.

    Derived so the generated docstring/pending comment name the real
    approval-pending set instead of a hardcoded group (005c Q5).
    """
    lines = text.splitlines()
    starts = [i for i, line in enumerate(lines) if AI3_START.match(line)]
    if not starts:
        return None
    for line in lines[starts[-1] + 1 :]:
        if NEXT_SUBSECTION.match(line):
            break
        if APPROVAL_MARKER in line:
            match = APPROVAL_LABEL.search(line)
            if match:
                return match.group(1).strip()
    return None


ACCESSOR_BLOCK_TEMPLATE = '''
# --- approved(name) accessor (005b Q6): fail-closed constant reads ---
# Values table references approved names only; pending names are reachable
# solely through the *_APPROVAL_PENDING flags above (never as a value).
_VALUES: dict[str, int | float] = {{
{values}}}
_PENDING_NAMES: frozenset[str] = frozenset(
    {{
{pending}    }}
)


def approved(name: str) -> int | float:
    """Return the constant value only when the name is approved (fail closed)."""
    if name in _PENDING_NAMES:
        raise ConstantsError(f"{{name}}: approval pending; read denied until operator approval")
    try:
        return _VALUES[name]
    except KeyError:
        raise ConstantsError(f"{{name}}: unknown constant") from None
'''


def render_constants_module(entries: list[Constant], pending_label: str | None = None) -> str:
    """Render the generated module; ruff-format-stable, deterministic."""
    marker = pending_label or "RECOMMENDED ... approval"
    header = (
        '"""Named constants generated from ARCH v5.1.5.1 Vol 1 §AI.3 (SPEC V1 §1.4.33).\n'
        "\n"
        "GENERATED FILE -- do not edit by hand.\n"
        "Regenerate: python3 scripts/gen_constants.py\n"
        "Values are verbatim from the frozen bundle (docs/reference/CURRENT).\n"
        f'Approval-pending companions mark the AI.3 "[{marker}]" set:\n'
        "features require recorded operator approval before relying on them\n"
        "(never silently adopted; shadow-only per constitution Sec 7). Read\n"
        "constants via approved(name): pending and unknown names raise\n"
        "ConstantsError (SPEC V1 §1.4.33, 005b Q6).\n"
        '"""\n'
        "\n"
        "from quantflow.domain.errors import ConstantsError\n"
    )
    body = "".join(f"{c.name} = {c.value}\n" for c in entries)
    pending_entries = [c for c in entries if c.approval_pending]
    pending_block = ""
    accessor_block = ""
    if pending_entries:
        pending_block = (
            "\n"
            f"# --- AI.3 [{marker}] set: approval pending ---\n"
            + "".join(f"{c.name}_APPROVAL_PENDING = True\n" for c in pending_entries)
        )
        approved_entries = [c for c in entries if not c.approval_pending]
        values = "".join(f'    "{c.name}": {c.name},\n' for c in approved_entries)
        pending_names = "".join(f'        "{c.name}",\n' for c in pending_entries)
        accessor_block = ACCESSOR_BLOCK_TEMPLATE.format(values=values, pending=pending_names)
    return header + "\n" + body + pending_block + accessor_block


def generate(arch_path: Path = ARCH_VOL1) -> str:
    """Read ARCH Vol 1 §AI.3 and render the constants module source."""
    text = arch_path.read_text()
    return render_constants_module(parse_ai3_constants(text), parse_pending_label(text))


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
