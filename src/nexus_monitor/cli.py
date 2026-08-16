from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from control_spine import exit_code
from nexus_monitor.engine import DEFAULT_THRESHOLDS, Activity, determine
from nexus_monitor.evidence import evidence_markdown, evidence_pack


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Sales/use tax nexus monitor + evidence pack")
    p.add_argument("activity_json")
    p.add_argument("--period", default="current")
    p.add_argument("--owner", default="")
    args = p.parse_args(argv)
    raw = json.loads(Path(args.activity_json).read_text())
    by_jdx = {t.jurisdiction: t for t in DEFAULT_THRESHOLDS}
    determinations = []
    for row in raw["activity"]:
        threshold = by_jdx[row["jurisdiction"]]
        activity = Activity(
            jurisdiction=row["jurisdiction"],
            period_end=date.fromisoformat(row["period_end"]),
            sales=row["sales"],
            transactions=row["transactions"],
            employees=row.get("employees", 0),
            inventory=row.get("inventory", False),
            owned_property=row.get("owned_property", False),
            collecting=row.get("collecting", False),
        )
        determinations.append(determine(activity, threshold))
    pack = evidence_pack(
        tuple(determinations),
        args.period,
        args.owner,
        "DEFAULT_THRESHOLDS snapshot 2026-08-01",
    )
    print(evidence_markdown(pack))
    print(pack["lock_state"], file=sys.stderr)
    return exit_code(pack)


if __name__ == "__main__":
    raise SystemExit(main())
