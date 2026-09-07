---
id: ADR-002
type: adr
title: Event sourcing for order state
description: Whether order state lives in Oracle 19c or moves to a document store.
traces_from: [CON-001]
traces_to: {}
status: draft
confidence: high
created_at: '2026-09-07'
decision_status: rejected
considered_options:
- Event sourcing for order state
- Direct state mutation
chosen_option: Direct state mutation
---

# ADR-002: Event sourcing for order state

## Context and Problem Statement
CON-001 fixes the store for this release.

## Decision Drivers
- CON-001 requires the order store to remain Oracle 19c for this release.

## Considered Options
- Event sourcing for order state
- Direct state mutation

## Decision Outcome
Chosen option: "Direct state mutation", because CON-001 fixes the store for
this release and event sourcing was rejected as unnecessary complexity.

### Consequences
Order state is mutated directly in place; no event log is maintained.
