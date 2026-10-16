"""Repo-bootstrap spec (005): generated constants + frozen-bundle hashes.

Tasks 4.1 (byte-identical regeneration), 4.3 (tamper/symlink fail closed),
4.4 (AI.3 [RECOMMENDED ... approval] gating). Design decisions 5-6: plain
pytest, temp-paths only for negative fixtures; the real bundle is read,
never written.
"""

import ast
import hashlib
import importlib.util
import shutil
from pathlib import Path

import pytest

from quantflow.domain import constants as generated_constants

REPO_ROOT = Path(__file__).parents[2]
SCRIPTS = REPO_ROOT / "scripts"
ARCH_VOL1 = REPO_ROOT / "docs" / "reference" / "CURRENT" / "ARCH_v5.1.5.1_Vol1_Foundation.md"
BUNDLE_DIR = REPO_ROOT / "docs" / "reference" / "CURRENT"
COMMITTED_MODULE = REPO_ROOT / "src" / "quantflow" / "domain" / "constants.py"


def _load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen_constants = _load_script("gen_constants")


def _committed_assignments() -> dict[str, object]:
    tree = ast.parse(COMMITTED_MODULE.read_text())
    values: dict[str, object] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                values[target.id] = ast.literal_eval(node.value)
    return values


def _verify_bundle_hashes(bundle_dir: Path) -> list[str]:
    violations: list[str] = []
    manifest = bundle_dir / "SHA256SUMS"
    if not manifest.exists():
        return [f"{manifest}: missing SHA256SUMS manifest"]
    expected: dict[str, str] = {}
    for line in manifest.read_text().splitlines():
        digest, sep, name = line.partition("  ")
        assert sep, f"malformed SHA256SUMS line: {line!r}"
        expected[name] = digest
    for name, digest in expected.items():
        path = bundle_dir / name
        if not path.exists():
            violations.append(f"{name}: listed in SHA256SUMS but missing")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            violations.append(f"{name}: hash mismatch")
    # Set equality (spec repo-bootstrap: "expected frozen file set"): every
    # bundle entry is in the manifest. SHA256SUMS is the manifest itself and
    # cannot list its own hash.
    files_in_dir = {entry.name for entry in bundle_dir.iterdir() if entry.name != "SHA256SUMS"}
    for name in sorted(files_in_dir - set(expected)):
        violations.append(f"{name}: present but not in SHA256SUMS")
    return violations


def _check_current_symlink(link: Path) -> list[str]:
    if not link.is_symlink():
        return [f"{link}: not a symlink to a frozen release directory"]
    if not link.exists():
        return [f"{link}: symlink target missing"]
    return []


# 4.1 Golden: byte-identical regeneration (drift = red, naming the constant)
def test_parser_scope_is_ai3_only():
    # AI.1/AI.2 constants are out of scope (spec delta: Sec AI.3 only).
    entries = gen_constants.parse_ai3_constants(ARCH_VOL1.read_text())
    names = [c.name for c in entries]
    assert names[0] == "MIN_VEGA"  # first constant of AI.3 Additional Constants
    assert "BASE_RISK_PCT" not in names  # AI.1 Sizing & Risk
    assert "PREMIUM_STOP_PCT" not in names  # AI.2 Stops


# 6.2 Fail closed: a non-comment AI.3 line that is neither prose nor a constant raises
def test_parser_fails_closed_on_assignment_style_constant_line():
    text = (
        "AI.3 Additional Constants\n  MIN_VEGA 0.005\n  DEALER_T_MIN_S = 300\nAI.4 Chase Limits\n"
    )
    with pytest.raises(ValueError, match="unparsable AI.3"):
        gen_constants.parse_ai3_constants(text)


def test_parser_fails_closed_on_constant_line_missing_value():
    text = "AI.3 Additional Constants\n  ORPHAN_NAME\nAI.4 Chase Limits\n"
    with pytest.raises(ValueError, match="unparsable AI.3"):
        gen_constants.parse_ai3_constants(text)


def test_parser_still_parses_prose_and_group_labels():
    text = (
        "AI.3 Additional Constants\n"
        "  MIN_VEGA 0.005\n"
        "  0DTE cluster constants:\n"
        "    ZERO_DTE_CLUSTER_WINDOW_S 900\n"
        "  Route-specific exit constants (AH):\n"
        "  These are engineering/paper-model choices.\n"
        "  ZERO_DTE ticker scope (rule, enforced by symbol_filter):\n"
        "  probabilities. The 900s buffer applies.\n"
        "  Lane latency hard cutoffs (ms):\n"
        "    SWING 10000\n"
        "AI.4 Chase Limits\n"
    )
    entries = gen_constants.parse_ai3_constants(text)
    assert [c.name for c in entries] == ["MIN_VEGA", "ZERO_DTE_CLUSTER_WINDOW_S", "SWING"]


def test_constants_module_is_byte_identical_regeneration():
    expected = gen_constants.generate(ARCH_VOL1).encode()
    actual = COMMITTED_MODULE.read_bytes()
    if expected != actual:
        parsed = {c.name: c.value for c in gen_constants.parse_ai3_constants(ARCH_VOL1.read_text())}
        committed = _committed_assignments()
        drifted = sorted(n for n, v in parsed.items() if committed.get(n) != float(v))
        pytest.fail(f"constants.py drifted from ARCH V1 AI.3; constants: {drifted}")
    assert expected == actual


def test_generated_module_is_importable_and_nonempty():
    assert hasattr(generated_constants, "MIN_VEGA")
    assert isinstance(generated_constants.MIN_VEGA, float)


# 4.3 Malformed/missing: tampered file, missing file, broken symlink
def test_real_bundle_hashes_verify():
    assert _check_current_symlink(BUNDLE_DIR) == []
    assert _verify_bundle_hashes(BUNDLE_DIR) == []
    assert len(sorted(BUNDLE_DIR.resolve().glob("*.md"))) == 11


def test_tampered_bundle_file_fails(tmp_path):
    copy = tmp_path / "bundle"
    shutil.copytree(BUNDLE_DIR.resolve(), copy)
    target = copy / "SPEC_v2.0.5.1_Vol1_Foundations.md"
    target.write_text(target.read_text() + "\n-- tampered --\n")
    assert _verify_bundle_hashes(copy) == ["SPEC_v2.0.5.1_Vol1_Foundations.md: hash mismatch"]


def test_missing_bundle_file_fails(tmp_path):
    copy = tmp_path / "bundle"
    shutil.copytree(BUNDLE_DIR.resolve(), copy)
    (copy / "SPEC_v2.0.5.1_Vol7_Research_Addenda.md").unlink()
    assert _verify_bundle_hashes(copy) == [
        "SPEC_v2.0.5.1_Vol7_Research_Addenda.md: listed in SHA256SUMS but missing"
    ]


def test_broken_current_symlink_fails(tmp_path):
    link = tmp_path / "CURRENT"
    link.symlink_to(tmp_path / "does-not-exist")
    assert _check_current_symlink(link)


def test_non_symlink_current_fails(tmp_path):
    plain = tmp_path / "CURRENT"
    plain.mkdir()
    assert _check_current_symlink(plain)


# 6.3 Set equality: a file in the bundle but not in SHA256SUMS fails the check
def test_extra_bundle_file_fails(tmp_path):
    copy = tmp_path / "bundle"
    shutil.copytree(BUNDLE_DIR.resolve(), copy)
    (copy / "stray_notes.txt").write_text("not part of the frozen bundle\n")
    assert _verify_bundle_hashes(copy) == ["stray_notes.txt: present but not in SHA256SUMS"]


# 4.4 Approval gating: RECOMMENDED set carries explicit pending markers
def test_recommended_constants_carry_approval_pending_markers():
    entries = gen_constants.parse_ai3_constants(ARCH_VOL1.read_text())
    pending = {c.name for c in entries if c.approval_pending}
    assert "DEALER_T_MIN_S" in pending  # sanity: the C12 set is captured
    assert "MIN_VEGA" not in pending  # declared before the [RECOMMENDED] marker
    for name in pending:
        assert getattr(generated_constants, f"{name}_APPROVAL_PENDING") is True
    for entry in entries:
        if not entry.approval_pending:
            assert not hasattr(generated_constants, f"{entry.name}_APPROVAL_PENDING")
