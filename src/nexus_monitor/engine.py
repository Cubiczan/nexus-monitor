"""Sales and use tax nexus determination.

Economic and physical nexus in jurisdictions where the company has not been
collecting. Annual review structurally cannot catch a threshold crossed in
month four.

This engine compares trailing activity to a dated threshold table. The table is
config, not live statute. It is not tax advice. A CPA or sales-tax specialist
signs the determination; the engine produces the computation they reperform.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum


CENTS = Decimal("0.01")


def money(value: object) -> Decimal:
    return Decimal(str(value)).quantize(CENTS, rounding=ROUND_HALF_UP)


class NexusKind(str, Enum):
    NONE = "none"
    PHYSICAL = "physical"
    ECONOMIC = "economic"
    BOTH = "both"


@dataclass(frozen=True)
class Threshold:
    jurisdiction: str
    name: str
    economic_sales: Decimal | None
    economic_transactions: int | None
    sales_tax_rate: Decimal
    snapshot_date: date
    source: str

    def __post_init__(self) -> None:
        if self.economic_sales is not None:
            object.__setattr__(self, "economic_sales", money(self.economic_sales))
        object.__setattr__(self, "sales_tax_rate", Decimal(str(self.sales_tax_rate)))


@dataclass(frozen=True)
class Activity:
    jurisdiction: str
    period_end: date
    sales: Decimal
    transactions: int
    employees: int = 0
    inventory: bool = False
    owned_property: bool = False
    collecting: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "sales", money(self.sales))


@dataclass(frozen=True)
class Determination:
    jurisdiction: str
    kind: NexusKind
    physical_reasons: tuple[str, ...]
    economic_reasons: tuple[str, ...]
    sales: Decimal
    transactions: int
    threshold_sales: Decimal | None
    threshold_transactions: int | None
    collecting: bool
    exposure: Decimal
    trigger: str


def physical_reasons(activity: Activity) -> tuple[str, ...]:
    reasons = []
    if activity.employees > 0:
        reasons.append(f"{activity.employees} employee(s) in jurisdiction")
    if activity.inventory:
        reasons.append("inventory in jurisdiction")
    if activity.owned_property:
        reasons.append("owned or leased property in jurisdiction")
    return tuple(reasons)


def economic_reasons(activity: Activity, threshold: Threshold) -> tuple[str, ...]:
    reasons = []
    if threshold.economic_sales is not None and activity.sales >= threshold.economic_sales:
        reasons.append(
            f"sales {activity.sales} >= economic threshold {threshold.economic_sales}"
        )
    if (
        threshold.economic_transactions is not None
        and activity.transactions >= threshold.economic_transactions
    ):
        reasons.append(
            f"transactions {activity.transactions} >= threshold {threshold.economic_transactions}"
        )
    return tuple(reasons)


def determine(activity: Activity, threshold: Threshold) -> Determination:
    if activity.jurisdiction != threshold.jurisdiction:
        raise ValueError("activity and threshold jurisdiction must match")
    phys = physical_reasons(activity)
    econ = economic_reasons(activity, threshold)
    if phys and econ:
        kind = NexusKind.BOTH
    elif phys:
        kind = NexusKind.PHYSICAL
    elif econ:
        kind = NexusKind.ECONOMIC
    else:
        kind = NexusKind.NONE

    exposure = Decimal("0.00")
    if kind is not NexusKind.NONE and not activity.collecting:
        exposure = money(activity.sales * threshold.sales_tax_rate)

    if kind is NexusKind.NONE:
        trigger = "below threshold; continue monitoring"
    elif activity.collecting:
        trigger = "nexus present; collection already on"
    else:
        trigger = "nexus present and not collecting — exposure estimated; specialist review required"

    return Determination(
        jurisdiction=activity.jurisdiction,
        kind=kind,
        physical_reasons=phys,
        economic_reasons=econ,
        sales=activity.sales,
        transactions=activity.transactions,
        threshold_sales=threshold.economic_sales,
        threshold_transactions=threshold.economic_transactions,
        collecting=activity.collecting,
        exposure=exposure,
        trigger=trigger,
    )


# Dated snapshot. Verify against current statute before using as a filing position.
# Snapshot date is 2026-08-01. Sources are typical published economic-nexus rules;
# several states have dropped transaction tests or raised dollar tests since Wayfair.
DEFAULT_THRESHOLDS: tuple[Threshold, ...] = (
    Threshold("SD", "South Dakota", Decimal("100000"), 200, Decimal("0.045"), date(2026, 8, 1), "Wayfair original / SD"),
    Threshold("CA", "California", Decimal("500000"), None, Decimal("0.0725"), date(2026, 8, 1), "CA CDTFA economic nexus"),
    Threshold("NY", "New York", Decimal("500000"), 100, Decimal("0.04"), date(2026, 8, 1), "NY Tax Law economic nexus"),
    Threshold("TX", "Texas", Decimal("500000"), None, Decimal("0.0625"), date(2026, 8, 1), "TX Comptroller economic nexus"),
    Threshold("WA", "Washington", Decimal("100000"), None, Decimal("0.065"), date(2026, 8, 1), "WA DOR economic nexus"),
    Threshold("IL", "Illinois", Decimal("100000"), 200, Decimal("0.0625"), date(2026, 8, 1), "IL DOR economic nexus"),
    Threshold("FL", "Florida", Decimal("100000"), None, Decimal("0.06"), date(2026, 8, 1), "FL DOR economic nexus"),
    Threshold("PA", "Pennsylvania", Decimal("100000"), None, Decimal("0.06"), date(2026, 8, 1), "PA DOR economic nexus"),
)
