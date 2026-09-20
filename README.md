# nexus-monitor

> **Cubiczan stack** — [CHP](https://github.com/Cubiczan/consensus-hardening-protocol) · [control-spine](https://github.com/Cubiczan/control-spine) · **You are here:** `nexus-monitor`

**Sales and use tax nexus determination.** Physical presence and economic thresholds, evaluated every period against trailing activity — the review an annual checklist structurally cannot catch. `complyai` is marketing-compliance. This is the tax-threshold engine.

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

UiPath can generate the same `activity.json` payload and hand it to this CLI when tax data lives in inboxes, spreadsheets, or staged evidence files.

South Dakota at $100,000 of sales and a 4.5% rate estimates **$4,500** of uncollected tax. That number is in the tests. Re-run them. Then have a specialist replace the snapshot table with the statutes that actually apply to the entity.

Uncollected nexus is a blocking finding. A signed at-risk pack is `PROVISIONAL_LOCK`, not evidence. Collection on and a named owner reach `LOCKED`. Unsigned packs — including every pack built through MCP — render `EXPLORING`, a first-class lock state in `control-spine` that is never evidence.

## Compliance spine

Vendored `control-spine`. The snapshot date is in the foundation. The engine cannot countersign a filing position.

## MCP server

`src/nexus_monitor/mcp_server.py` publishes the engine over Model Context Protocol: a thin wrapper in the `io.github.icohangar-ops/nexus-monitor` namespace (stdio transport) whose tools — `determine_nexus` and `nexus_evidence_pack` — call `nexus_monitor.engine` and `nexus_monitor.evidence` verbatim. All determination logic lives in the engine module; the wrapper adds no logic, touches no network, and serves the same dated threshold snapshot — config, not live statute. Not tax advice. Evidence packs built through MCP are always unsigned — the tool takes no owner, so the spine renders `EXPLORING` and `is_evidence: false`; a named human signs via the CLI (`--owner`), never through MCP. MCP access is opt-in, keeping the deterministic core zero-dependency: the engine and CLI install with no runtime dependencies, and the MCP server ships behind the `mcp` extra (`pip install 'nexus-monitor[mcp]'`) — chosen over a hard dependency after prelint review, since a default install must stay dependency-free. CI installs `.[dev,mcp]` so the MCP tests still run.

```bash
uvx --from 'nexus-monitor[mcp]' nexus-monitor-mcp
# or from a checkout:
uv run --with 'mcp>=1.2,<2' --with . python -m nexus_monitor.mcp_server
```
