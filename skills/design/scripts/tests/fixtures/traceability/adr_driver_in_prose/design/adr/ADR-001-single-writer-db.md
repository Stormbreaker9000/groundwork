---
id: ADR-001
type: adr
traces_from:
- NFR-001
traces_to: {}
decision_status: accepted
---

# ADR-001: Single-writer database

## Context and Problem Statement

Whether the order store admits concurrent writers.

## Decision Drivers

- NFR-001: keep p99 write latency under 200ms.

  This supersedes the earlier FR-014 framing, which was renumbered away before
  this ADR was written. It is prose about the decision's history, not a driver.

## Considered Options

- Single writer
- Multi-writer with optimistic locking

## Decision Outcome

Single writer.

### Consequences

- Good: no conflict-resolution path to get wrong.
