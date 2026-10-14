"""Session 2 toolchain smoke test. Confirms Python 3.14, mcp 1.30.0,
FastMCP is importable, and the design bundle is wired up."""

import importlib.metadata as md
import sys
from pathlib import Path


def test_python_314():
    assert sys.version_info[:2] == (3, 14)


def test_mcp_1_30_0():
    assert md.version("mcp") == "1.30.0"


def test_fastmcp_importable():
    from mcp.server.fastmcp import FastMCP  # noqa: F401


def test_design_bundle_current():
    current = Path("docs/reference/CURRENT")
    assert current.exists() and current.is_symlink()
    md_files = list(current.resolve().glob("*.md"))
    assert len(md_files) == 11


def test_uv_lock_present():
    assert Path("uv.lock").exists()
