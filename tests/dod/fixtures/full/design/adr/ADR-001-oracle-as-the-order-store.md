---
id: ADR-001
type: adr
title: Oracle as the order store
description: Whether order state lives in Oracle 19c or moves to a document store.
traces_from: [CON-001]
traces_to: {}
status: draft
confidence: high
created_at: '2026-09-07'
decision_status: accepted
considered_options:
- Oracle 19c as the system of record
- A document store fronting Oracle
chosen_option: Oracle 19c as the system of record
---

# ADR-001: Oracle as the order store

## Context and Problem Statement
CON-001 fixes the store for this release.

## Decision Drivers
- CON-001 requires the order store to remain Oracle 19c for this release.

## Considered Options
- Oracle 19c as the system of record
- A document store fronting Oracle

## Decision Outcome
Chosen option: "Oracle 19c as the system of record", because CON-001 fixes it
for this release.

### Consequences
Order state continues to live in Oracle 19c; no migration work is scheduled
for this release.
