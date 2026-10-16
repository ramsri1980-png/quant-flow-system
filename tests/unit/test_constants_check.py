"""Task 4.2: UPPER_SNAKE duplicate/unsourced lint (fail-closed fixtures).

Scenario: an AI.3 constant redefined outside domain/constants.py fails; an
UPPER_SNAKE constant not sourced from AI.3 fails; documented structural
constants pass (check_constants.STRUCTURAL_ALLOWLIST). Sources: SPEC V1
Sec 1.4.33-1.4.34; constitution Sec 4 (constants defined once, by name).
"""

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
SCRIPTS = REPO_ROOT / "scripts"
ARCH_VOL1 = REPO_ROOT / "docs" / "reference" / "CURRENT" / "ARCH_v5.1.5.1_Vol1_Foundation.md"


def _load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen_constants = _load_script("gen_constants")
check_constants = _load_script("check_constants")

GENERATED_NAMES = {c.name for c in gen_constants.parse_ai3_constants(ARCH_VOL1.read_text())}


def test_duplicate_ai3_constant_fails_the_check(tmp_path):
    (tmp_path / "bad.py").write_text("MIN_VEGA = 1\n")
    violations = check_constants.scan_source_tree(tmp_path, GENERATED_NAMES)
    assert any("MIN_VEGA" in v and "duplicate" in v for v in violations), violations


def test_unsourced_upper_snake_constant_fails_the_check(tmp_path):
    (tmp_path / "bad.py").write_text("MY_INVENTED_THRESHOLD = 2\n")
    violations = check_constants.scan_source_tree(tmp_path, GENERATED_NAMES)
    assert any("MY_INVENTED_THRESHOLD" in v for v in violations), violations


def test_structural_allowlisted_constants_pass(tmp_path):
    (tmp_path / "ok.py").write_text(
        '"""Structural constants are allowlisted with reasons."""\n'
        "INT64_MIN = -(2**63)\n"
        "DURATION_MS_MAX = 2**31 - 1\n"
    )
    assert check_constants.scan_source_tree(tmp_path, GENERATED_NAMES) == []


def test_enum_members_are_not_flagged(tmp_path):
    (tmp_path / "vocab.py").write_text(
        "from enum import Enum\n"
        "\n"
        "\n"
        "class Vocab(Enum):\n"
        '    """Closed vocabulary."""\n'
        "\n"
        '    ACTIVE = "ACTIVE"\n'
    )
    assert check_constants.scan_source_tree(tmp_path, GENERATED_NAMES) == []


# 6.1 Red fixtures: every scope and assignment form; canonical-path skip only
def test_chained_assignment_duplicate_fails_the_check(tmp_path):
    (tmp_path / "bad.py").write_text("MIN_VEGA = INVENTED_X = 1\n")
    violations = check_constants.scan_source_tree(tmp_path, GENERATED_NAMES)
    assert any("MIN_VEGA" in v and "duplicate" in v for v in violations), violations
    assert any("INVENTED_X" in v for v in violations), violations


def test_function_local_duplicate_fails_the_check(tmp_path):
    (tmp_path / "bad.py").write_text("def compute():\n    MIN_VEGA = 1\n")
    violations = check_constants.scan_source_tree(tmp_path, GENERATED_NAMES)
    assert any("MIN_VEGA" in v and "duplicate" in v for v in violations), violations


def test_class_body_duplicate_fails_the_check(tmp_path):
    (tmp_path / "bad.py").write_text("class Settings:\n    MIN_VEGA = 1\n")
    violations = check_constants.scan_source_tree(tmp_path, GENERATED_NAMES)
    assert any("MIN_VEGA" in v and "duplicate" in v for v in violations), violations


def test_non_canonical_constants_module_is_scanned(tmp_path):
    # only the real domain/constants.py (canonical path) may be skipped
    (tmp_path / "constants.py").write_text("MIN_VEGA = 1\n")
    violations = check_constants.scan_source_tree(tmp_path, GENERATED_NAMES)
    assert any("MIN_VEGA" in v and "duplicate" in v for v in violations), violations


def test_tuple_assignment_targets_are_flagged(tmp_path):
    (tmp_path / "bad.py").write_text("MY_INVENTED_A, MY_INVENTED_B = 1, 2\n")
    violations = check_constants.scan_source_tree(tmp_path, GENERATED_NAMES)
    assert any("MY_INVENTED_A" in v for v in violations), violations
    assert any("MY_INVENTED_B" in v for v in violations), violations


def test_real_source_tree_is_clean():
    violations = check_constants.scan_source_tree(REPO_ROOT / "src" / "quantflow", GENERATED_NAMES)
    assert violations == [], violations


def test_real_constants_module_has_no_drift():
    assert (
        check_constants.verify_no_drift(
            ARCH_VOL1, REPO_ROOT / "src" / "quantflow" / "domain" / "constants.py"
        )
        == []
    )
