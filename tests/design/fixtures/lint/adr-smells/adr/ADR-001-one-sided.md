---
id: ADR-001
type: adr
title: Event-sourced order store
description: How the order store records state.
traces_from:
  - NFR-001
traces_to: {}
status: draft
decision_status: accepted
confidence: medium
created_at: 2026-08-14
considered_options:
  - Event sourcing
  - Snapshot table
chosen_option: Event sourcing
---

# ADR-001: Event-sourced order store

## Context and Problem Statement

The order store must answer "how did this order reach its current state".

## Decision Drivers

- The store must be scalable.
- NFR-001

## Considered Options

- **Event sourcing** — every state change is an appended event.

## Decision Outcome

Event sourcing.

### Consequences

- Good: the full history of every order is available by construction.
- Good: no separate audit log to keep in step with the store.
