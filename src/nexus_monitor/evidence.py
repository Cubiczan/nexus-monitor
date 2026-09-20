from __future__ import annotations

from decimal import Decimal

from control_spine import Finding, render_spine, seal
from nexus_monitor.engine import Determination, money

FOUNDATION = (
    "Not tax advice. Thresholds are a dated config snapshot, not live statute.",
    "Economic nexus fires on dollar OR transaction tests where the snapshot still has a transaction test.",
    "Physical nexus fires on employees, inventory, or owned/leased property.",
    "Exposure = sales × snapshot rate, only where nexus exists and collection is off.",
)

ENGINE_ID = "nexus-monitor-engine"
ENGINE_VERSION = "0.1.0"


def evidence_pack(
    determinations: tuple[Determination, ...],
    period_label: str,
    owner: str,
    threshold_snapshot: str,
    invoked_via: str | None = None,
) -> dict:
    at_risk = [d for d in determinations if d.kind.value != "none" and not d.collecting]
    estimated = money(sum((d.exposure for d in at_risk), Decimal("0")))
    pack = {
        "control_id": "ICFR-NEXUS-01",
        "control_objective": "Jurisdictional nexus is monitored against live activity, not reviewed once a year.",
        "period": period_label,
        "population_count": len(determinations),
        "threshold": "Every configured jurisdiction is evaluated each period; physical OR economic nexus is sufficient.",
        "threshold_snapshot": threshold_snapshot,
        "disclaimer": "Not tax advice. Thresholds are a dated config snapshot and must be verified against current statute before any filing position.",
        "at_risk_count": len(at_risk),
        "estimated_uncollected": str(estimated),
        "register": [
            {
                "jurisdiction": d.jurisdiction,
                "kind": d.kind.value,
                "sales": str(d.sales),
                "transactions": d.transactions,
                "threshold_sales": str(d.threshold_sales) if d.threshold_sales is not None else None,
                "threshold_transactions": d.threshold_transactions,
                "collecting": d.collecting,
                "exposure": str(d.exposure),
                "trigger": d.trigger,
                "physical_reasons": list(d.physical_reasons),
                "economic_reasons": list(d.economic_reasons),
            }
            for d in determinations
        ],
        "prepared_by": ENGINE_ID,
        "owner_signoff": owner,
        "conclusion": (
            "No uncollected nexus."
            if not at_risk
            else f"{len(at_risk)} jurisdiction(s) over threshold and not collecting. Specialist review required before this is a filing position."
        ),
    }
    blocking = tuple(
        Finding(
            "NEXUS-UNCOLLECTED",
            f"{d.jurisdiction}: {d.kind.value} nexus, not collecting, exposure {d.exposure}",
        )
        for d in at_risk
    )
    if invoked_via is not None:
        pack["invoked_via"] = invoked_via
    return seal(
        pack,
        engine_id=ENGINE_ID,
        engine_version=ENGINE_VERSION,
        inputs={
            "jurisdictions": [d.jurisdiction for d in determinations],
            "snapshot": threshold_snapshot,
            "period": period_label,
        },
        foundation=FOUNDATION,
        blocking_findings=blocking,
    )


def evidence_markdown(pack: dict) -> str:
    lines = [
        f"# Nexus determination pack — {pack['period']}",
        "",
        *render_spine(pack),
        f"**Control:** {pack['control_id']}",
        f"**Snapshot:** {pack['threshold_snapshot']}",
        f"**Disclaimer:** {pack['disclaimer']}",
        f"**At risk:** {pack['at_risk_count']}  **Estimated uncollected:** {pack['estimated_uncollected']}",
        f"**Owner sign-off:** {pack['owner_signoff'] or '_unsigned_'}",
        "",
        "| Jdx | Kind | Sales | Txns | Collecting | Exposure | Trigger |",
        "|---|---|---:|---:|---|---:|---|",
    ]
    for row in pack["register"]:
        lines.append(
            f"| {row['jurisdiction']} | {row['kind']} | {row['sales']} | {row['transactions']} | "
            f"{row['collecting']} | {row['exposure']} | {row['trigger']} |"
        )
    lines += ["", "## Conclusion", "", pack["conclusion"], ""]
    return "\n".join(lines)
