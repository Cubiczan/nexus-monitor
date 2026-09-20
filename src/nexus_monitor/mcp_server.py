"""MCP server for the nexus-monitor engine.

Exposes deterministic sales/use-tax nexus determination as Model Context
Protocol tools. Thin wrapper — all determination logic lives in
``nexus_monitor.engine`` and ``nexus_monitor.evidence`` and is reused
verbatim; nothing here touches the network, and the threshold table is the
dated config snapshot, not live statute. Not tax advice.

Follows the same publishing path proven by invoice-audit-engine /
codesentinel: namespace ``io.github.icohangar-ops/nexus-monitor``, stdio transport, published
via the ``mcp-publisher`` CLI.

Run it:

    uvx --from 'nexus-monitor[mcp]' nexus-monitor-mcp
    # or, from a checkout:
    uv run --with 'mcp>=1.2,<2' --with . python -m nexus_monitor.mcp_server
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Any

from mcp.server.fastmcp import FastMCP

from nexus_monitor.engine import DEFAULT_THRESHOLDS, Activity, determine
from nexus_monitor.evidence import evidence_pack

mcp = FastMCP(
    "nexus-monitor",
    instructions=(
        "Deterministic sales/use-tax nexus monitoring. Supply jurisdiction "
        "activity; the tools compare trailing activity to the dated threshold "
        "snapshot (config, not live statute — not tax advice), estimate "
        "uncollected-tax exposure where nexus exists and collection is off, "
        "and render the evidence pack a specialist can reperform."
    ),
)

_BY_JDX = {t.jurisdiction: t for t in DEFAULT_THRESHOLDS}


def _activity_from_dict(row: dict[str, Any]) -> Activity:
    """Build an Activity from the CLI/JSON shape (same keys as the CLI's input file)."""
    return Activity(
        jurisdiction=row["jurisdiction"],
        period_end=date.fromisoformat(row["period_end"]),
        sales=row["sales"],
        transactions=row["transactions"],
        employees=row.get("employees", 0),
        inventory=row.get("inventory", False),
        owned_property=row.get("owned_property", False),
        collecting=row.get("collecting", False),
    )


def _threshold_for(jurisdiction: str) -> Any:
    threshold = _BY_JDX.get(jurisdiction)
    if threshold is None:
        raise ValueError(
            f"jurisdiction '{jurisdiction}' is not in the DEFAULT_THRESHOLDS snapshot"
        )
    return threshold


def _jsonify(value: Any) -> Any:
    """JSON-safe conversion: Decimals become strings so cents survive exactly."""
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _jsonify(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonify(v) for v in value]
    return value


@mcp.tool()
def determine_nexus(activity: dict[str, Any]) -> dict[str, Any]:
    """Determine nexus for one jurisdiction's trailing activity against the threshold snapshot.

    Returns the nexus kind (none / physical / economic / both), the reasons
    that fired, and the estimated exposure when nexus exists and collection
    is off. Amounts are exact decimal strings.

    Args:
        activity: Trailing-period activity. Expected keys mirror the CLI
            input file: jurisdiction, period_end (ISO date), sales,
            transactions, employees, inventory, owned_property, collecting.
    """
    row = _activity_from_dict(activity)
    return _jsonify(asdict(determine(row, _threshold_for(row.jurisdiction))))


@mcp.tool()
def nexus_evidence_pack(
    activities: list[dict[str, Any]],
    period_label: str = "current",
) -> dict[str, Any]:
    """Build the nexus evidence pack a specialist can reperform without the source code.

    Evaluates every supplied jurisdiction against the snapshot and aggregates
    the register (at-risk count, estimated uncollected tax, per-jurisdiction
    detail, owner sign-off). Unsigned packs are not evidence; a specialist
    must still verify the snapshot against current statute.

    Args:
        activities: Activity rows, same shape as determine_nexus's input.
        period_label: Close period label (e.g. "H1 2026").
        Sign-off: MCP never accepts an owner — packs built here are always
        unsigned (EXPLORING, not evidence). A named human signs via the CLI
        (--owner), never through MCP.
    """
    determinations = tuple(
        determine(_activity_from_dict(row), _threshold_for(row["jurisdiction"]))
        for row in activities
    )
    pack = evidence_pack(
        determinations,
        period_label,
        "",
        "DEFAULT_THRESHOLDS snapshot 2026-08-01",
        invoked_via="mcp",
    )
    return _jsonify(pack)


def main() -> None:
    """Console-script entry point: run the server over stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
