---
id: NFR-004
type: non_functional
tier: solution
title: Crash-safe atomic persistence and recovery
description: After forced termination or power loss at any point, including mid-write, the application shall next launch into the last committed state, or — where no committed state survives — into the recovery state defined by FR-010 and FR-012, and never into a partially written one.
rationale: The pet's persisted state is the owner's accumulated investment; a single corrupt save destroys the attachment that the whole product is built to create, and a kill during a write is an ordinary event on a desktop app that saves on every stat change. Atomic commit is what makes that loss impossible rather than merely unlikely — an interrupted write must never replace the file that is already committed, which is why the measure discriminates between restoring the owner's pet and initializing a fresh one. The recovery behaviour when no committed state survives is owned by FR-010 (no save file present) and FR-012 (a save file that fails integrity validation, including its quarantine), and is referenced here rather than restated.
fit_criterion: Across 200 fault-injection trials that kill the process at randomized points including mid-save, 100% of subsequent launches reach a valid pet state, with 0 corrupt loads and 0 unhandled exceptions; in 100% of those trials where a committed state existed before the kill, that committed state is the state restored, and recovery to a default pet occurs in 0% of such trials; across 50 clean restart cycles, 100% restore the exact prior state.
priority: must
confidence: high
verification_method: test
status: draft
created_at: 2026-08-24
traces_from: [FR-001, FR-010, FR-012]
traces_to:
  design: []
  tests: []
  code: []
scope: project
parent_scope: null
---

# NFR-004 — Crash-safe atomic persistence and recovery

## ISO 25010 Characteristic
Reliability → Fault tolerance and Recoverability

## Quality Attribute Scenario
- **Source of stimulus:** An external fault — forced process termination, OS
  crash, or power loss.
- **Stimulus:** The process is killed at an arbitrary point in its lifetime,
  including part-way through writing the save file.
- **Environment:** Normal operation with fault injection, covering saves
  triggered both by a stat change and by application close; local disk, no
  network involved.
- **Artifact:** The state persistence layer and the save file on local disk.
- **Response:** The next launch loads the last committed state. A partially
  written file is never presented as valid, because an interrupted write never
  reaches committed status and never replaces the file that is already
  committed. Where no committed state survives, the launch proceeds by the
  FR-owned recovery paths — FR-012 where a save file is present but fails
  integrity validation (including its quarantine), FR-010 where no save file is
  present — and this requirement asserts no behaviour of its own beyond
  reaching a valid state.
- **Response measure:** 200 fault-injection trials yield 100% launches into a
  valid pet state, 0 corrupt loads, 0 unhandled exceptions. In 100% of those
  trials where a committed state existed before the kill, that committed state
  is the state restored; recovery to a default pet occurs in 0% of such trials.
  50 clean restart cycles restore the exact prior state 100% of the time.

## Rationale
State written on every stat change means writes are frequent and a kill during a
write is routine rather than exotic. Because the persisted pet is the owner's
accumulated investment, corruption is not a degraded experience but a total loss
of the thing the product exists to build, so the recovery target is stated as an
absolute rather than a rate.

The discriminating half of the measure exists because "launches into a valid pet
state" is satisfied by a brand-new default pet, and a default pet is precisely
the outcome this requirement exists to prevent — it is the same loss BR-002
forbids applying silently. Requiring that a pre-existing committed state be the
one restored is achievable with single-generation retention and needs no new
scope: atomic commit means the in-progress write never touches the file that is
already committed, so the pre-kill committed state survives the kill intact and
the FR-012 path is never reached. Only where no committed state survives at all
does recovery apply.

What the owner is or is not told during recovery is a product decision this
quality target has no basis to assert, so it is left entirely to the FRs that own
recovery.
