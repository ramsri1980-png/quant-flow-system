"""Direct NewType construction of unit wrappers is banned outside units.py/time.py.

The unit wrappers (Cents, Micros, Mills, EpochMs, DurationMs) are
``typing.NewType`` aliases, a runtime no-op: ``Cents(1.5)``, ``Cents(True)``
and ``Micros(2**70)`` all succeed. Only the validating factories (``cents``,
``micros``, ``mills``, ``epoch_ms``, ``duration_ms``) reject bad input
fail-closed. This AST scan enforces that the factories are the only
sanctioned constructors (005a task 1.2).

Known limit: ``typing.cast(Cents, x)`` is not detected -- a cast is a
type-checker assertion, not construction, and no runtime value is created.
Aliased calls (``from ... import Cents as C``) are likewise not detected;
the scan targets direct construction with the wrapper names.
"""

import ast
from pathlib import Path

SRC_ROOT = Path(__file__).parents[2] / "src" / "quantflow"
WRAPPER_NAMES = {"Cents", "Micros", "Mills", "EpochMs", "DurationMs"}
ALLOWED_FILES = {
    SRC_ROOT / "domain" / "units.py",
    SRC_ROOT / "domain" / "time.py",
}


def find_direct_wrapper_calls(path: Path) -> list[str]:
    """Return direct wrapper constructions in ``path`` as ``path:line`` strings."""
    tree = ast.parse(path.read_text(), filename=str(path))
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                name: str | None = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr
            else:
                name = None
            if name in WRAPPER_NAMES:
                found.append(f"{path}:{node.lineno} direct {name}(...); use the validating factory")
    return found


def test_no_direct_wrapper_construction_in_src():
    violations: list[str] = []
    for path in sorted(SRC_ROOT.rglob("*.py")):
        if path in ALLOWED_FILES or "__pycache__" in path.parts:
            continue
        violations.extend(find_direct_wrapper_calls(path))
    assert violations == []


def test_scan_detects_deliberately_bad_fixture(tmp_path):
    bad = tmp_path / "bad_fixture.py"
    bad.write_text(
        "from quantflow.domain.units import Cents\n"
        "import quantflow.domain.time as t\n"
        "x = Cents(1.5)\n"
        "y = t.EpochMs(-1)\n"
    )
    assert len(find_direct_wrapper_calls(bad)) == 2
