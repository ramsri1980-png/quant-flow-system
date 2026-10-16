"""005b Q6: approved(name) accessor + AST ban on direct approval-pending reads.

Spec domain-constants "Approved constants accessor": approved(name) returns
the value only when the name is not approval-pending; pending and unknown
names raise ConstantsError (fail closed, never a silent default). Direct
reads of approval-pending names in domain/** or kernels/** fail the AST
test and must be replaced by approved(...).
Source: ARCH V1 Sec AI.3 (approval-pending set); 005a review Q6.
"""

import ast
from pathlib import Path

import pytest

from quantflow.domain import constants
from quantflow.domain.errors import ConstantsError

SRC_ROOT = Path(__file__).parents[3] / "src" / "quantflow"

# Pending base names derived from the generated *_APPROVAL_PENDING flags, so
# the scan cannot drift from the module it guards.
PENDING_BASE_NAMES = frozenset(
    name.removesuffix("_APPROVAL_PENDING")
    for name in dir(constants)
    if name.endswith("_APPROVAL_PENDING") and getattr(constants, name)
)


def test_approved_returns_value_for_approved_constant():
    # THETA_MICROCENTS_PER_CENT has no approval-pending companion (spec
    # scenario "Approved constant is readable").
    value = constants.approved("THETA_MICROCENTS_PER_CENT")
    assert value == 1000000
    assert isinstance(value, int)


def test_approved_returns_float_constant():
    assert constants.approved("MIN_VEGA") == 0.005


def test_approved_raises_on_approval_pending_name():
    # DEALER_T_MIN_S carries DEALER_T_MIN_S_APPROVAL_PENDING = True (C12).
    with pytest.raises(ConstantsError, match="approval pending"):
        constants.approved("DEALER_T_MIN_S")


def test_approved_raises_on_unknown_name():
    with pytest.raises(ConstantsError, match="unknown"):
        constants.approved("NOT_A_REAL_CONSTANT")


def test_approved_raises_on_pending_flag_name():
    # The *_APPROVAL_PENDING flags are bookkeeping, never readable values.
    with pytest.raises(ConstantsError, match="unknown"):
        constants.approved("DEALER_T_MIN_S_APPROVAL_PENDING")


def _direct_pending_reads(path: Path) -> list[str]:
    """Names loaded directly (not via approved) that are pending or flags."""
    tree = ast.parse(path.read_text(), filename=str(path))
    reads: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            name: str | None = node.id
        elif isinstance(node, ast.Attribute):
            name = node.attr
        elif isinstance(node, ast.alias):
            # Check both the alias (local name) and the original name.
            # `from ... import DEALER_T_MIN_S as T` must be flagged even
            # though the local binding is just "T".
            candidates = [node.asname, node.name.partition(".")[0]]
            for cand in candidates:
                if cand and (cand.endswith("_APPROVAL_PENDING") or cand in PENDING_BASE_NAMES):
                    reads.append(f"{path}:{node.lineno} direct read of {cand}")
            continue
        else:
            name = None
        if name is None:
            continue
        if name.endswith("_APPROVAL_PENDING") or name in PENDING_BASE_NAMES:
            reads.append(f"{path}:{node.lineno} direct read of {name}")
    return reads


def _py_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py") if "__pycache__" not in p.parts)


def test_domain_and_kernels_have_no_direct_pending_reads():
    # The generated constants module references only approved names in its
    # value table; pending names appear solely as flag definitions (Store
    # context) and string literals, so the real tree passes with no exemption.
    violations: list[str] = []
    for package in ("domain", "kernels"):
        for path in _py_files(SRC_ROOT / package):
            violations.extend(_direct_pending_reads(path))
    assert violations == []


def test_scan_detects_direct_pending_flag_read(tmp_path):
    bad = tmp_path / "bad_fixture.py"
    bad.write_text(
        "from quantflow.domain import constants\n"
        "\n"
        "\n"
        "def flag():\n"
        "    return constants.DEALER_T_MIN_S_APPROVAL_PENDING\n"
    )
    assert len(_direct_pending_reads(bad)) == 1


def test_scan_detects_direct_pending_base_name_read(tmp_path):
    bad = tmp_path / "bad_fixture.py"
    bad.write_text(
        "from quantflow.domain.constants import DEALER_T_MIN_S\n"
        "\n"
        "\n"
        "def threshold():\n"
        "    return DEALER_T_MIN_S\n"
    )
    assert len(_direct_pending_reads(bad)) == 2


def test_scan_allows_approved_access(tmp_path):
    ok = tmp_path / "ok_fixture.py"
    ok.write_text(
        "from quantflow.domain.constants import approved\n"
        "\n"
        "\n"
        "def threshold():\n"
        '    return approved("THETA_MICROCENTS_PER_CENT")\n'
    )
    assert _direct_pending_reads(ok) == []


def test_scan_detects_aliased_pending_import(tmp_path):
    """An aliased from-import of a pending name must still be flagged."""
    bad = tmp_path / "bad_alias.py"
    bad.write_text("from quantflow.domain.constants import DEALER_T_MIN_S as T\nx = T\n")
    hits = _direct_pending_reads(bad)
    assert any("DEALER_T_MIN_S" in h for h in hits), hits
