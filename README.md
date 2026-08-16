# nexus-monitor

> **Cubiczan stack** — [CHP](https://github.com/Cubiczan/consensus-hardening-protocol) · [control-spine](https://github.com/Cubiczan/control-spine) · **You are here:** `nexus-monitor`

**Sales and use tax nexus determination.** Physical presence and economic thresholds, evaluated every period against trailing activity. CreditRiskMonitor's Item 4.02 was nexus the annual review never saw. `complyai` is marketing-compliance. This is the tax-threshold engine that was missing.

Not tax advice. Thresholds are a **dated config snapshot** (1 August 2026). A CPA or sales-tax specialist signs the determination. The engine produces the computation they reperform.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## What it produces

| Artefact | What a tester samples |
|---|---|
| Obligation register | Every configured jurisdiction, kind of nexus, trigger text |
| Supporting computation | Sales and transaction counts vs the snapshot threshold |
| Exposure estimate | Taxable sales × configured rate, only where nexus exists and collection is off |
| Disclaimer | Snapshot date and "not a filing position" on every pack |

Economic nexus fires if **either** the dollar test or the transaction test (where the state still has one) is met. Physical nexus fires on employees, inventory, or owned/leased property. Both can be true at once.

## Quick start

```bash
pip install -e ".[dev]"
pytest -q
nexus-monitor examples/activity.json --period "H1 2026" --owner "Tax manager"
```

South Dakota at $100,000 of sales and a 4.5% rate estimates **$4,500** of uncollected tax. That number is in the tests. Re-run them. Then have a specialist replace the snapshot table with the statutes that actually apply to the entity.

Uncollected nexus is a blocking finding. A signed at-risk pack is `PROVISIONAL_LOCK`, not evidence. Collection on and a named owner reach `LOCKED`.

## Compliance spine

Vendored `control-spine`. The snapshot date is in the foundation. The engine cannot countersign a filing position.
