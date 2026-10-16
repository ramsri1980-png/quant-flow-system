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
# 005a 1.5: extended ban set. Generic names ("time()", "today()") flag any
# method of that name -- intended fail-closed behaviour (design decision 4):
# a false positive is a review prompt, a false negative leaks wall-clock time.
BANNED_CALL_NAMES = {
    "now",
    "utcnow",
    "today",
    "monotonic",
    "time",
    "time_ns",
    "monotonic_ns",
    "perf_counter",
    "perf_counter_ns",
    "process_time",
    "process_time_ns",
    "urandom",
}
BANNED_MODULES = {"time", "datetime", "secrets"}
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
        elif isinstance(node, ast.ImportFrom) and node.level > 0:
            # 005a 1.5: relative imports are banned in domain/kernels. Checked
            # before the node.module branch so "from . import x" (module None)
            # and "from ..adapters import clock" are both caught.
            violations.append(
                f"{path}:{node.lineno} relative import "
                "(use absolute quantflow.* imports in domain/kernels)"
            )
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module.partition(".")[0] in BANNED_MODULES:
                violations.append(f"{path}:{node.lineno} from {node.module} import")
            elif _is_adapters_module(node.module):
                violations.append(
                    f"{path}:{node.lineno} from {node.module} import "
                    "(adapters banned in domain/kernels: inject a Clock)"
                )
            elif node.module == "quantflow" and any(
                alias.name == "adapters" for alias in node.names
            ):
                # "from quantflow import adapters" reaches the same concrete
                # clocks without the quantflow.adapters prefix (task 8.1)
                violations.append(
                    f"{path}:{node.lineno} from {node.module} import adapters "
                    "(quantflow.adapters banned in domain/kernels: inject a Clock)"
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
    assert len(violations) == 5, violations


# 7.1/8.1 Red fixture: domain/kernels may never import a concrete clock
# (design decision 3; spec epoch-clock "No clock is reachable without
# injection" -- an adapters import reaches ambient time without injection)
def test_scan_detects_adapter_imports_fixture(tmp_path):
    bad = tmp_path / "bad_fixture.py"
    bad.write_text(
        "from quantflow.adapters.clock import SystemClock\n"
        "import quantflow.adapters.mcp.server\n"
        "from quantflow import adapters\n"
    )
    violations = find_wall_clock_violations(bad)
    assert sum("quantflow.adapters" in v for v in violations) == 3, violations


# 005a 1.5 fixtures: prove each newly banned shape is detected.
def test_scan_detects_additional_clock_calls(tmp_path):
    bad = tmp_path / "bad_fixture.py"
    bad.write_text(
        "def f(c, os):\n"
        "    return (\n"
        "        c.time_ns()\n"
        "        + c.perf_counter()\n"
        "        + c.perf_counter_ns()\n"
        "        + c.monotonic_ns()\n"
        "        + c.process_time()\n"
        "        + c.process_time_ns()\n"
        "        + os.urandom(8)\n"
        "    )\n"
    )
    assert len(find_wall_clock_violations(bad)) == 7


def test_scan_detects_relative_imports(tmp_path):
    bad = tmp_path / "bad_fixture.py"
    bad.write_text("from . import x\nfrom ..adapters import clock\n")
    assert len(find_wall_clock_violations(bad)) == 2


def test_scan_detects_secrets_import(tmp_path):
    bad = tmp_path / "bad_fixture.py"
    bad.write_text("import secrets\n")
    assert len(find_wall_clock_violations(bad)) == 1
