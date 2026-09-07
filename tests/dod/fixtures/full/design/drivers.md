# Design Drivers

The architecturally significant requirements behind this decomposition, the
tradeoffs taken, and the points where a small change to a decision would move a
quality attribute sharply.

## Architecturally Significant Requirements
- CON-001 (constraint) — fixes the order store as Oracle 19c for this release,
  which is what ADR-001 records.
- FR-001 (functional) — cancellation must go through the Order Service's
  persistence contract (IF-001) rather than a direct store access.

## Tradeoffs
- Keeping Oracle 19c as the order store (ADR-001) avoids a migration this
  release; it costs the option of a document store's flexible schema.

## Sensitivity Points
- IF-001's `interaction: synchronous` choice. Switching it to asynchronous
  would relax the persistence latency budget but breaks the read-after-write
  expectation CMP-001 relies on. Affects FR-001.
