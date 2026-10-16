"""Port contract (005 task 2.3) + determinism zero-iteration case (task 6.4).

Source: SPEC V1 Sec 2.9.4.2 (no wall-clock reads except as_of); design
decision 3 (Clock Protocol in ports/, concrete clock in adapters/ only).
"""

from pathlib import Path

import pytest

from quantflow.adapters.clock import SystemClock
from quantflow.domain.time import EPOCH_MS_MIN, EpochMs, epoch_ms
from quantflow.ports.clock import Clock


class FakeClock:
    """Injected test double; the only clock domain/kernels may observe."""

    def __init__(self, now: EpochMs) -> None:
        self._now = now

    def now_ms(self) -> EpochMs:
        return self._now


def test_fake_clock_satisfies_the_clock_protocol():
    fake = FakeClock(epoch_ms(1729012345678))
    assert isinstance(fake, Clock)
    assert fake.now_ms() == 1729012345678


def test_injected_clock_is_deterministic_with_no_ambient_fallback():
    clock: Clock = FakeClock(epoch_ms(EPOCH_MS_MIN))
    assert clock.now_ms() == epoch_ms(EPOCH_MS_MIN)
    assert clock.now_ms() == clock.now_ms()


def test_system_clock_lives_outside_domain():
    assert SystemClock.__module__.startswith("quantflow.adapters")
    assert not SystemClock.__module__.startswith("quantflow.domain")
    now = SystemClock().now_ms()
    assert isinstance(now, int)


# 6.4 Determinism golden (spec epoch-clock: "Same as_of yields identical
# results"). Zero-iterations case: 005 ships no kernel modules. The empty
# set is pinned so the scenario cannot pass vacuously; the first kernel
# module flips the assertion and forces real same-as_of coverage.
EXPECTED_KERNEL_MODULES: list[str] = []
KERNELS_ROOT = Path(__file__).parents[2] / "src" / "quantflow" / "kernels"


def _kernel_modules() -> list[str]:
    if not KERNELS_ROOT.exists():
        return []
    return sorted(
        str(path.relative_to(KERNELS_ROOT))
        for path in KERNELS_ROOT.rglob("*.py")
        if path.name != "__init__.py" and "__pycache__" not in path.parts
    )


def _assert_kernel_modules_pinned(modules: list[str]) -> None:
    assert modules == EXPECTED_KERNEL_MODULES, (
        f"kernel modules changed: {modules}; invoke every pure kernel twice with an "
        "identical as_of and assert identical output (spec epoch-clock determinism "
        "scenario), then update EXPECTED_KERNEL_MODULES"
    )


def test_same_as_of_yields_identical_results_zero_iteration_case_pinned():
    _assert_kernel_modules_pinned(_kernel_modules())


def test_kernel_module_pin_detects_change():
    # deliberately-bad fixture: the pin must fire when a kernel appears
    with pytest.raises(AssertionError, match="kernel modules changed"):
        _assert_kernel_modules_pinned(["pure_flow.py"])
