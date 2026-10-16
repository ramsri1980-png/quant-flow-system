"""No-future-leakage (005 task 2.4): no wall-clock reads in domain//kernels.

Mirrors the SPEC V1 Sec 2.9.4.8 lint pattern (fail closed: a banned call or
import is a test failure, not a warning). Task 7.1: also bans
quantflow.adapters.* imports under domain/** and kernels/** (design decision
3: only injected clocks; the application layer wires adapters). A
deliberately-bad fixture proves the scan detects each ban.
"""

import ast
from pathlib import Path

SRC_ROOT = Path(__file__).parents[2] / "src" / "quantflow"
BANNED_CALL_NAMES = {"now", "utcnow", "today", "monotonic", "time"}
BANNED_MODULES = {"time", "datetime"}
BANNED_ADAPTER_PREFIX = "quantflow.adapters"


def _is_adapters_module(module: str) -> bool:
    """True for quantflow.adapters itself or any submodule (exact prefix)."""
    return module == BANNED_ADAPTER_PREFIX or module.startswith(BANNED_ADAPTER_PREFIX + ".")


def find_wall_clock_violations(path: Path) -> list[str]:
    """Return violations: banned wall-clock calls/imports + adapter imports."""
    tree = ast.parse(path.read_text(), filename=str(path))
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute):
                name: str | None = func.attr
            elif isinstance(func, ast.Name):
                name = func.id
            else:
                name = None
            if name in BANNED_CALL_NAMES:
                violations.append(f"{path}:{node.lineno} wall-clock call {name}()")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.partition(".")[0] in BANNED_MODULES:
                    violations.append(f"{path}:{node.lineno} import {alias.name}")
                elif _is_adapters_module(alias.name):
                    violations.append(
                        f"{path}:{node.lineno} import {alias.name} "
                        "(adapters banned in domain/kernels: inject a Clock)"
                    )
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module.partition(".")[0] in BANNED_MODULES:
                violations.append(f"{path}:{node.lineno} from {node.module} import")
            elif _is_adapters_module(node.module):
                violations.append(
                    f"{path}:{node.lineno} from {node.module} import "
                    "(adapters banned in domain/kernels: inject a Clock)"
                )
    return violations


def _py_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py") if "__pycache__" not in p.parts)


def test_domain_and_kernels_have_no_wall_clock_reads():
    violations: list[str] = []
    for package in ("domain", "kernels"):
        for path in _py_files(SRC_ROOT / package):
            violations.extend(find_wall_clock_violations(path))
    assert violations == []


def test_scan_detects_deliberately_bad_fixture(tmp_path):
    bad = tmp_path / "bad_fixture.py"
    bad.write_text(
        "import datetime\n"
        "import time\n"
        "\n"
        "\n"
        "def stamp():\n"
        "    return datetime.now() + time.time() + time.monotonic()\n"
    )
    violations = find_wall_clock_violations(bad)
    assert len(violations) >= 4, violations


# 7.1 Red fixture: domain/kernels may never import a concrete clock
# (design decision 3; spec epoch-clock "No clock is reachable without
# injection" -- an adapters import reaches ambient time without injection)
def test_scan_detects_adapter_imports_fixture(tmp_path):
    bad = tmp_path / "bad_fixture.py"
    bad.write_text(
        "from quantflow.adapters.clock import SystemClock\nimport quantflow.adapters.mcp.server\n"
    )
    violations = find_wall_clock_violations(bad)
    assert sum("quantflow.adapters" in v for v in violations) == 2, violations
