"""Enforce the feature-group layout and flat change naming (constitution §12)."""
import re
from pathlib import Path

OPENSPEC = Path(__file__).parents[2] / "openspec"
CHANGE_RE = re.compile(r"^\d{3}[a-z]?(-\d{3})?-[a-z][a-z0-9]*(-[a-z0-9]+)*$")
BRIEF_FILE_RE = re.compile(r"^\d{3}[a-z]?-[A-Za-z][A-Za-z0-9-]*\.md$")
GROUP_RE = re.compile(r"^\d{3}-[a-z][a-z0-9]*(-[a-z0-9]+)*$")
FEATURE_RE = re.compile(r"^(?!000)\d{3}-[a-z][a-z0-9]*(-[a-z0-9]+)*\.md$")

def test_active_changes_are_flat_and_named():
    for p in sorted((OPENSPEC / "changes").iterdir()):
        if p.name == "archive" or not p.is_dir():
            continue
        assert CHANGE_RE.match(p.name), p.name
        nested = [c.name for c in p.iterdir() if c.is_dir() and c.name != "specs"]
        assert nested == [], f"nested folders in {p.name}: {nested}"

def test_prompt_layout():
    for p in sorted((OPENSPEC / "prompts").iterdir()):
        if p.is_file():
            assert BRIEF_FILE_RE.match(p.name), p.name
            continue
        assert GROUP_RE.match(p.name), p.name
        assert (p / "000-overview.md").is_file(), f"{p.name}: missing 000-overview.md"
        for f in sorted(p.iterdir()):
            if f.name == "000-overview.md":
                continue
            assert f.is_file() and FEATURE_RE.match(f.name), f"{p.name}/{f.name}"

def test_regexes_accept_legacy_and_new_names():
    for name in ("005-domain-types-units-clock", "005-001-domain-enums"):
        assert CHANGE_RE.match(name)
    for name in ("080-position-exit-AH.md", "041b-evaluation-protocol.md", "005a-domain-hardening.md"):
        assert BRIEF_FILE_RE.match(name)
    assert not CHANGE_RE.match("005-001")
    assert not FEATURE_RE.match("000-overview.md")
