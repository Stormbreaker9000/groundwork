# Design Drivers

The architecturally significant requirements behind this decomposition, the
tradeoffs taken, and the points where a small change to a decision would move a
quality attribute sharply.

## Architecturally Significant Requirements
- NFR-001 (quality_attribute) — the confidentiality budget on payment data is
  what forces the gateway behind an explicit contract (IF-001) rather than an
  in-process call.
- CON-001 (constraint) — the single-writer database boundary constrains
  CMP-001's persistence strategy.

## Tradeoffs
- Routing all card traffic through IF-001 gains an auditable boundary and a
  single place to enforce the confidentiality budget; it costs a synchronous
  hop on the checkout path, which spends part of NFR-001's latency budget.

## Sensitivity Points
- IF-001's `interaction: synchronous` choice. Switching it to asynchronous
  would relax the latency budget but breaks the read-after-write expectation
  CMP-001 relies on. Affects NFR-001.
