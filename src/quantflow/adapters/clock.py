"""Wall-clock adapter: the only sanctioned live time source (SPEC V1 §2.9.4.2).

Implements the Clock port (ports/clock.py). Never imported by domain/ or
kernels/ (enforced by the wall-clock AST scan, tests/unit/test_wall_clock_scan.py).
"""

import time

from quantflow.domain.time import EpochMs, epoch_ms


class SystemClock:
    """Concrete Clock reading the OS clock; wired at the application edge."""

    def now_ms(self) -> EpochMs:
        """Current UTC epoch ms from the OS clock (integer, no float)."""
        return epoch_ms(time.time_ns() // 1_000_000, field="now_ms")
