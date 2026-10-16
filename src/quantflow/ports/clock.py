"""Clock port: injectable time source; domain/kernels never read the clock.

Source: SPEC V1 §2.9.4.2 (no wall-clock reads except as_of); the port is the
only sanctioned in-process time source (design decision 3).
"""

from typing import Protocol, runtime_checkable

from quantflow.domain.time import EpochMs


@runtime_checkable
class Clock(Protocol):
    """Read-only UTC clock; domain/kernels observe time only via injection."""

    def now_ms(self) -> EpochMs:
        """Current UTC epoch ms (SPEC V1 §19.8.3)."""
        ...
