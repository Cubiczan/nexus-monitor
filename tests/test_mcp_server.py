"""The MCP server registers the engine's deterministic determination as callable tools.

Pins the README/tests canonical case (South Dakota at $100,000 of sales and a
4.5% rate estimates $4,500 of uncollected tax) through the MCP tool path.
Skipped cleanly when the optional ``mcp`` SDK is not installed.
"""

from __future__ import annotations

import asyncio

import pytest

pytest.importorskip("mcp")

from nexus_monitor import mcp_server  # noqa: E402
from control_spine import canonical_hash


def _tool_names() -> set[str]:
    tools = asyncio.run(mcp_server.mcp.list_tools())
    return {t.name for t in tools}


def _activity() -> dict:
    return {
        "jurisdiction": "SD",
        "period_end": "2026-06-30",
        "sales": "100000",
        "transactions": 10,
    }


def test_expected_tools_registered() -> None:
    assert _tool_names() >= {"determine_nexus", "nexus_evidence_pack"}


def test_determine_nexus_pins_the_readme_exposure() -> None:
    d = mcp_server.determine_nexus(_activity())
    assert d["kind"] == "economic"
    assert d["exposure"] == "4500.00"


def test_unknown_jurisdiction_is_a_loud_error() -> None:
    with pytest.raises(ValueError, match="not in the DEFAULT_THRESHOLDS snapshot"):
        mcp_server.determine_nexus({**_activity(), "jurisdiction": "ZZ"})


def test_evidence_pack_totals_population() -> None:
    pack = mcp_server.nexus_evidence_pack(
        [_activity()], period_label="H1 2026"
    )
    assert pack["population_count"] == 1
    assert pack["lock_state"] == "EXPLORING"
    assert pack["is_evidence"] is False
    assert pack["invoked_via"] == "mcp"
    assert pack["spine"]["envelope_hash"] == canonical_hash(
        {k: v for k, v in pack["spine"].items() if k != "envelope_hash"}
    )
    assert pack["at_risk_count"] == 1
    assert pack["estimated_uncollected"] == "4500.00"
