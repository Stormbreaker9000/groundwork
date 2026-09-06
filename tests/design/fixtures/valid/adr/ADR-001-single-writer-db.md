---
id: ADR-001
type: adr
title: Single-writer database
description: Whether the order store admits concurrent writers.
traces_from:
  - NFR-001
traces_to: {}
status: draft
decision_status: accepted
confidence: high
created_at: 2026-07-18
considered_options:
  - Single writer
  - Multi-writer with optimistic locking
chosen_option: Single writer
---

# ADR-001: Single-writer database

## Context and Problem Statement

The order store is written by the order service and read by everything else.
Admitting a second writer would require a conflict-resolution story.

## Decision Drivers

- NFR-001

## Considered Options

- **Single writer** — one component owns every write.
- **Multi-writer with optimistic locking** — any component may write; conflicts
  are resolved on commit.

## Decision Outcome

Single writer. `CMP-001` owns every write to the order store.

### Consequences

- Good: no conflict-resolution path to design, test, or get wrong.
- Bad: every write funnels through one component, which becomes a throughput
  ceiling if order volume grows past a single process.
