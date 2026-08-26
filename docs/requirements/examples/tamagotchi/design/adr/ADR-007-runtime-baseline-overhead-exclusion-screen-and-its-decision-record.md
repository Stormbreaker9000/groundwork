---
id: ADR-007
type: adr
title: Runtime baseline-overhead exclusion screen and its decision record
description: Whether the runtime baseline-overhead exclusion screen has actually been executed, and where the runtime decision record naming the rejected candidates lives.
traces_from: [CON-001]
traces_to: {}
status: draft
confidence: low
created_at: '2026-08-24'
decision_status: proposed
---

# ADR-007: Runtime baseline-overhead exclusion screen and its decision record

## Context and Problem Statement

The undecided question is the reference machine. CON-001's exclusion screen is a measurement on a reference machine that has not been recorded, and the design context says so outright: the screen has not actually been executed, and the selection is provisional against measurement rather than settled by it. Nothing in the artifact set can address this and nothing should try — the constraint is settled before any component exists, it is a boundary on the shell everything else is built inside, and CON-001 additionally requires a runtime decision record naming the rejected candidates, which is an ADR rather than a component. It is deferred with no partial coverage to name: two components cite the constraint in their traces_from, but a citation is not coverage. The corresponding runtime selection is recorded as ADR-003, with its provisionality stated as a consequence there.

## Decision Drivers

- CON-001

## Considered Options

- None — no alternatives are recorded yet.

## Decision Outcome

Pending. No option has been chosen, and none can be recorded here yet, because what is outstanding is the execution of a measurement rather than a choice among candidates. The question is owned by engineering and is tracked as open question Q-13; it cannot be closed until the still-open reference-machine question Q-5 records a specification to measure against. Until then the runtime selection in ADR-003 rests on published baselines rather than on this project's own measurement, and the constraint's own rule is that a candidate measured against an unrecorded baseline counts as unassessed rather than admitted. This record is the runtime decision record the constraint mandates; it cannot record a pass or a fail against the exclusion screen until the reference machine lands.

### Consequences

- None — the decision is pending.
