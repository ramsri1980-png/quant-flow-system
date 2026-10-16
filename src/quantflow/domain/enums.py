"""Disjoint domain vocabularies: cluster_grade / cluster_state / episode_state.

Literal sets come verbatim from the SPEC V2 §19.2 CHECK constraints
(zero_dte_cluster_current) and invariant AB. The three types are disjoint:
shared literals (ACTIVE, RETRACTED, EXPIRED) never bridge vocabularies, and
BASIC is a grade only (SPEC V1 §1.4.35: evidence grades, not probabilities).
Closed sets: unknown or case-mangled literals fail closed, never coerced.
"""

from enum import Enum
from typing import NoReturn

from quantflow.domain.errors import VocabularyError


class _ClosedVocabulary(Enum):
    """Base for closed literal vocabularies; unknown literals raise."""

    @classmethod
    def _missing_(cls, value: object) -> NoReturn:
        raise VocabularyError(f"{cls.__name__}: unknown literal {value!r}")


class ClusterGrade(_ClosedVocabulary):
    """Evidence-grade vocabulary (SPEC V2 §19.2; BASIC is a grade only)."""

    BASIC = "BASIC"
    MEDIUM_CONFLUENCE = "MEDIUM_CONFLUENCE"
    HIGH_CONFLUENCE = "HIGH_CONFLUENCE"


class ClusterState(_ClosedVocabulary):
    """Cluster lifecycle vocabulary (SPEC V2 §19.2)."""

    ACTIVE = "ACTIVE"
    MIXED = "MIXED"
    BULLISH_REVERSAL = "BULLISH_REVERSAL"
    BEARISH_REVERSAL = "BEARISH_REVERSAL"
    RETRACTED = "RETRACTED"
    EXPIRED = "EXPIRED"


class EpisodeState(_ClosedVocabulary):
    """Episode-timeline vocabulary (SPEC V2 §19.2)."""

    FORMING = "FORMING"
    ACTIVE = "ACTIVE"
    UPGRADED = "UPGRADED"
    REVERSED = "REVERSED"
    RETRACTED = "RETRACTED"
    EXPIRED = "EXPIRED"
