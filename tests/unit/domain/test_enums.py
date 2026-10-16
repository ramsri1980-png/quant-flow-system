"""Domain-enums spec (005): three disjoint vocabularies (tasks 3.1-3.3).

The golden test parses the frozen SPEC V2 Sec 19.2 DDL
(zero_dte_cluster_current CHECK constraints) to prevent drift (design
decision 4). Sources: SPEC V2 Sec 19.2, invariant AB; SPEC V1 Sec 1.4.35.
"""

import re
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from quantflow.domain.enums import ClusterGrade, ClusterState, EpisodeState
from quantflow.domain.errors import VocabularyError

FROZEN_VOL2 = (
    Path(__file__).parents[3]
    / "docs"
    / "reference"
    / "CURRENT"
    / "SPEC_v2.0.5.1_Vol2_Data_Canonical.md"
)

ALL_MEMBERS = [*ClusterGrade, *ClusterState, *EpisodeState]


def _ddl_check_literals(table: str, column: str) -> set[str]:
    text = FROZEN_VOL2.read_text()
    start = text.index(f"CREATE TABLE {table}")
    end = text.index(");", start)
    block = text[start:end]
    match = re.search(rf"{column} TEXT NOT NULL CHECK\(\s*{column} IN\s*\(([^)]*)\)", block)
    assert match, f"no CHECK({column} IN ...) found in {table} DDL"
    return set(re.findall(r"'([A-Z_]+)'", match.group(1)))


# 3.1 Golden: literal sets match the frozen DDL exactly
@pytest.mark.parametrize(
    ("column", "enum_cls"),
    [
        ("cluster_grade", ClusterGrade),
        ("cluster_state", ClusterState),
        ("episode_state", EpisodeState),
    ],
    ids=["cluster_grade", "cluster_state", "episode_state"],
)
def test_literal_sets_match_the_ddl_exactly(column, enum_cls):
    assert {member.value for member in enum_cls} == _ddl_check_literals(
        "zero_dte_cluster_current", column
    )


def test_expected_literals_pinned():
    # Defense in depth: hardcoded mirror of the SPEC V2 Sec 19.2 CHECK lists.
    assert [m.value for m in ClusterGrade] == ["BASIC", "MEDIUM_CONFLUENCE", "HIGH_CONFLUENCE"]
    assert [m.value for m in ClusterState] == [
        "ACTIVE",
        "MIXED",
        "BULLISH_REVERSAL",
        "BEARISH_REVERSAL",
        "RETRACTED",
        "EXPIRED",
    ]
    assert [m.value for m in EpisodeState] == [
        "FORMING",
        "ACTIVE",
        "UPGRADED",
        "REVERSED",
        "RETRACTED",
        "EXPIRED",
    ]


# 3.2 Boundary: shared literals do not bridge types
def test_shared_literal_does_not_bridge_types():
    for literal in ["ACTIVE", "RETRACTED", "EXPIRED"]:
        assert ClusterState(literal).value == literal
        assert EpisodeState(literal).value == literal
        with pytest.raises(VocabularyError):
            ClusterGrade(literal)


def test_cross_enum_instance_construction_fails():
    with pytest.raises(VocabularyError):
        EpisodeState(ClusterState.RETRACTED)
    with pytest.raises(VocabularyError):
        ClusterState(EpisodeState.EXPIRED)


def test_basic_is_grade_only():
    assert ClusterGrade("BASIC") is ClusterGrade.BASIC
    for vocabulary in (ClusterState, EpisodeState):
        with pytest.raises(VocabularyError):
            vocabulary("BASIC")


@pytest.mark.parametrize("vocabulary", [ClusterGrade, ClusterState, EpisodeState])
@pytest.mark.parametrize(
    "bad",
    ["basic", "High_Confluence", " ACTIVE", "ACTIVE ", "active", "DIRECTIONAL"],
    ids=["lower", "mixed-case", "leading-ws", "trailing-ws", "lower-active", "unknown"],
)
def test_unknown_or_mangled_literal_is_rejected(vocabulary, bad):
    with pytest.raises(VocabularyError):
        vocabulary(bad)


# 3.3 Property invariants: grades are evidence grades, never probabilities
@given(st.sampled_from(ALL_MEMBERS))
def test_property_no_implicit_float_conversion(member):
    with pytest.raises(TypeError):
        float(member)
    with pytest.raises(TypeError):
        int(member)
    assert isinstance(member.value, str)


# 005a 1.3: pin the vocabulary behaviour the 005 review flagged. The two
# state vocabularies legitimately share ACTIVE/RETRACTED/EXPIRED (SPEC V2
# Sec 19.2); what must hold is that the types never bridge.
def _values(enum_cls) -> set[str]:
    return {member.value for member in enum_cls}


def test_overlap_is_exactly_the_documented_shared_literals():
    assert _values(ClusterState) & _values(EpisodeState) == {
        "ACTIVE",
        "RETRACTED",
        "EXPIRED",
    }


def test_grade_is_disjoint_from_both_state_vocabularies():
    assert _values(ClusterGrade).isdisjoint(_values(ClusterState))
    assert _values(ClusterGrade).isdisjoint(_values(EpisodeState))


def test_shared_literals_never_compare_equal_across_types():
    assert ClusterState.ACTIVE != EpisodeState.ACTIVE
    # ...but the underlying values document the deliberate overlap.
    assert ClusterState.ACTIVE.value == EpisodeState.ACTIVE.value


@pytest.mark.parametrize("literal", ["FORMING", "UPGRADED", "REVERSED"])
def test_episode_only_literals_rejected_by_cluster_state(literal):
    with pytest.raises(VocabularyError):
        ClusterState(literal)


@pytest.mark.parametrize(
    "literal",
    ["ACTIVE", "active", "Basic", ""],
    ids=["upper", "lower", "mixed-case", "empty"],
)
def test_grade_rejects_unknown_and_case_mangled(literal):
    with pytest.raises(VocabularyError):
        ClusterGrade(literal)
