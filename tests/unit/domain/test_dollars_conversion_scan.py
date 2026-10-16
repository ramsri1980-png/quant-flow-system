"""005c 2.7 (Q14): AST guard against dollars conversion in domain/** and kernels/**.

Money in the decision path is integer-valued in `_cents` / `_micros` / `_mills`
(SPEC V1 Sec 19.4); dollars conversion is forbidden (RQ-006 -- rounding is
integer-only at the display boundary). The guard flags a `BinOp(Div)` whose
divisor is a dollars literal (`100`, `1000`, `1_000_000`) or a named dollars
divisor (`MICROS_PER_DOLLAR`, `MILLS_PER_DOLLAR`, `CENTS_PER_DOLLAR`), unless the
enclosing function name is in the allowlist.

The allowlist is **empty and fail-closed** (design 2.7): a legitimate divisor must
be a named unit constant (e.g. `MICROS_PER_MILL`), not a dollars conversion. A
kernel that legitimately needs one registers itself in a follow-up.

Design 2.7 nuance: `micros_to_mills` does not divide directly -- it delegates to
`_round_half_even_div`, which uses `divmod` -- so `src/quantflow/domain/**` today
contains no true-division `BinOp` at all (`kernels/` does not exist yet) and the
real-tree scan passes trivially. Detection is proven by the positive fixtures.

Sources: SPEC V1 Sec 19.4, SPEC V2 Sec 19.4.6; 005c brief 2.7.
"""

import ast
from pathlib import Path

SRC_ROOT = Path(__file__).parents[3] / "src" / "quantflow"
SCAN_PACKAGES = ("domain", "kernels")

DOLLARS_LITERALS = frozenset({100, 1000, 1_000_000})
DOLLARS_DIVISOR_NAMES = frozenset({"MICROS_PER_DOLLAR", "MILLS_PER_DOLLAR", "CENTS_PER_DOLLAR"})

# Empty and fail-closed (design 2.7). Entries are enclosing function names.
DOLLARS_DIVISION_ALLOWLIST: frozenset[str] = frozenset()


def _node_owners(tree: ast.Module) -> dict[int, str]:
    """Map node id -> innermost enclosing function qualified name."""
    owners: dict[int, str] = {}
    stack: list[str] = []

    def visit(node: ast.AST) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            stack.append(node.name)
            for child in ast.iter_child_nodes(node):
                visit(child)
            stack.pop()
            return
        owners[id(node)] = ".".join(stack)
        for child in ast.iter_child_nodes(node):
            visit(child)

    visit(tree)
    return owners


def _text_divisor_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def find_dollars_conversions(
    path: Path, allowlist: frozenset[str] = DOLLARS_DIVISION_ALLOWLIST
) -> list[str]:
    """Return violations: divisions by a dollars literal or dollars divisor."""
    tree = ast.parse(path.read_text(), filename=str(path))
    owners = _node_owners(tree)
    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.Div):
            continue
        divisor = node.right
        if isinstance(divisor, ast.Constant) and divisor.value in DOLLARS_LITERALS:
            flagged = f"literal {divisor.value}"
        else:
            name = _text_divisor_name(divisor)
            if name not in DOLLARS_DIVISOR_NAMES:
                continue
            flagged = name
        owner = owners.get(id(node), "")
        if owner in allowlist:
            continue
        violations.append(
            f"{path}:{node.lineno} dollars division by {flagged} (in {owner or '<module>'})"
        )
    return violations


def _scan_tree() -> list[str]:
    violations: list[str] = []
    for package in SCAN_PACKAGES:
        root = SRC_ROOT / package
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            violations.extend(find_dollars_conversions(path))
    return violations


def _divisions(path: Path) -> list[ast.BinOp]:
    """True-division (`/`) BinOps in a file, to prove a fixture is in scope."""
    tree = ast.parse(path.read_text(), filename=str(path))
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div)
    ]


def test_allowlist_starts_empty_and_fail_closed():
    assert DOLLARS_DIVISION_ALLOWLIST == frozenset()


def test_real_tree_has_no_dollars_conversion():
    assert _scan_tree() == []


def test_micros_to_mills_named_division_is_not_flagged():
    # Divisor is the named unit constant MICROS_PER_MILL, not a dollars value.
    units = SRC_ROOT / "domain" / "units.py"
    assert find_dollars_conversions(units) == []


def test_named_unit_divisor_is_not_flagged(tmp_path):
    # Non-vacuity: the fixture really contains a true-division BinOp, so the
    # "not flagged" result is a genuine exemption, not an unparsed file.
    good = tmp_path / "good_unit.py"
    good.write_text(
        "MICROS_PER_MILL = 1000\n\n\ndef to_mills(micros):\n    return micros / MICROS_PER_MILL\n"
    )
    assert len(_divisions(good)) == 1
    assert find_dollars_conversions(good) == []


def test_scan_detects_dollars_literal_division(tmp_path):
    bad = tmp_path / "bad_literal.py"
    bad.write_text(
        "def micros_to_dollars_repr(micros):\n"
        "    return micros / 1_000_000\n"
        "\n"
        "\n"
        "def cents_to_dollars_repr(cents):\n"
        "    return cents / 100\n"
    )
    violations = find_dollars_conversions(bad)
    assert len(violations) == 2, violations


def test_scan_detects_named_dollars_divisor(tmp_path):
    bad = tmp_path / "bad_named.py"
    bad.write_text(
        "MICROS_PER_DOLLAR = 1_000_000\n"
        "\n"
        "\n"
        "def micros_to_dollars_repr(micros):\n"
        "    return micros / MICROS_PER_DOLLAR\n"
    )
    violations = find_dollars_conversions(bad)
    assert len(violations) == 1, violations


def test_module_level_dollars_division_is_flagged(tmp_path):
    bad = tmp_path / "bad_module.py"
    bad.write_text("DOLLAR_RATIO = 1_000_000 / 100\n")
    violations = find_dollars_conversions(bad)
    assert len(violations) == 1, violations
    assert "<module>" in violations[0]


def test_enclosing_function_allowlist_exempts_a_registered_function(tmp_path):
    bad = tmp_path / "kernelish.py"
    bad.write_text(
        "def display_dollars(micros):\n"
        "    return micros / 1_000_000\n"
        "\n"
        "\n"
        "def other(micros):\n"
        "    return micros / 1_000_000\n"
    )
    # Fail-closed by default: both functions are flagged.
    assert len(find_dollars_conversions(bad)) == 2
    # A registered function is exempt; the other is still flagged.
    violations = find_dollars_conversions(bad, allowlist=frozenset({"display_dollars"}))
    assert len(violations) == 1
    assert "other" in violations[0]
