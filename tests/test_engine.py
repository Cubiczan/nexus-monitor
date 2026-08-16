from datetime import date
from decimal import Decimal

from nexus_monitor.engine import DEFAULT_THRESHOLDS, Activity, NexusKind, determine
from nexus_monitor.evidence import evidence_pack


def _sd():
    return next(t for t in DEFAULT_THRESHOLDS if t.jurisdiction == "SD")


def test_below_both_thresholds() -> None:
    activity = Activity("SD", date(2026, 6, 30), sales="90000", transactions=50)
    d = determine(activity, _sd())
    assert d.kind is NexusKind.NONE
    assert d.exposure == Decimal("0.00")


def test_economic_sales_threshold() -> None:
    activity = Activity("SD", date(2026, 6, 30), sales="100000", transactions=10)
    d = determine(activity, _sd())
    assert d.kind is NexusKind.ECONOMIC
    assert d.exposure == Decimal("4500.00")  # 100000 * 4.5%


def test_economic_transaction_threshold() -> None:
    activity = Activity("SD", date(2026, 6, 30), sales="1000", transactions=200)
    d = determine(activity, _sd())
    assert d.kind is NexusKind.ECONOMIC


def test_physical_inventory_even_below_economic() -> None:
    activity = Activity(
        "SD", date(2026, 6, 30), sales="1000", transactions=1, inventory=True
    )
    d = determine(activity, _sd())
    assert d.kind is NexusKind.PHYSICAL
    assert "inventory" in d.physical_reasons[0]


def test_collecting_zeroes_exposure() -> None:
    activity = Activity(
        "SD", date(2026, 6, 30), sales="100000", transactions=200, collecting=True
    )
    d = determine(activity, _sd())
    assert d.kind is NexusKind.ECONOMIC
    assert d.exposure == Decimal("0.00")


def test_california_has_no_transaction_test() -> None:
    ca = next(t for t in DEFAULT_THRESHOLDS if t.jurisdiction == "CA")
    activity = Activity("CA", date(2026, 6, 30), sales="100000", transactions=5000)
    d = determine(activity, ca)
    assert d.kind is NexusKind.NONE


def test_evidence_pack_flags_uncollected() -> None:
    activity = Activity("SD", date(2026, 6, 30), sales="100000", transactions=10)
    d = determine(activity, _sd())
    pack = evidence_pack((d,), "H1 2026", "Tax manager", "2026-08-01")
    assert pack["at_risk_count"] == 1
    assert pack["estimated_uncollected"] == "4500.00"
    assert "Not tax advice" in pack["disclaimer"]
    assert pack["lock_state"] == "PROVISIONAL_LOCK"
    assert pack["is_evidence"] is False


def test_unsigned_pack_is_exploring_not_evidence() -> None:
    activity = Activity("SD", date(2026, 6, 30), sales="100000", transactions=10)
    d = determine(activity, _sd())
    pack = evidence_pack((d,), "H1 2026", "", "2026-08-01")
    assert pack["lock_state"] == "EXPLORING"
    assert pack["is_evidence"] is False


def test_collecting_signed_pack_locks() -> None:
    activity = Activity(
        "SD", date(2026, 6, 30), sales="100000", transactions=10, collecting=True
    )
    d = determine(activity, _sd())
    pack = evidence_pack((d,), "H1 2026", "Tax manager", "2026-08-01")
    assert pack["at_risk_count"] == 0
    assert pack["lock_state"] == "LOCKED"
    assert pack["is_evidence"] is True
