---
id: ADR-006
type: adr
title: Pet-state evaluation cadence period
description: How often the running application re-evaluates pet state, and what bounds that interval against the idle-footprint budget.
traces_from: [NFR-002]
traces_to: {}
status: draft
confidence: low
created_at: '2026-08-24'
decision_status: proposed
---

# ADR-006: Pet-state evaluation cadence period

## Context and Problem Statement

The undecided question is the evaluation cadence period — still open — measured against a budget that is itself not evaluable until a reference machine is recorded, also still open. NFR-002's own measure concedes it: not evaluable until the reference machine is recorded. The scheduler component and its contract are at low confidence for exactly this reason and both say so. The partial coverage is worth naming and it improved this round without moving the verdict: the period is isolated in one component so it can be tuned against the budget without touching what an evaluation does; the scheduler's overrun mode coalesces ticks rather than queueing them, so a slow evaluation cannot accumulate a backlog that spends the budget; the refresh contract coalesces redraws for the same reason and no longer re-announces on every tick regardless of change; and the background timer machinery the measure budgets by name now has a contract of its own that defends the budget at its own boundary, rejecting a non-positive or sub-resolution period rather than coercing it to the fastest tick the host can deliver. What remains undecided is the parameter itself, and it cannot be decided inside the artifact set.

## Decision Drivers

- NFR-002

## Considered Options

- None — no alternatives are recorded yet.

## Decision Outcome

Pending. No value has been chosen and no discrete options have been recorded, because what is undecided is a parameter rather than a choice among named alternatives. The question is owned by engineering and is tracked as open question Q-12, the design-side refinement of the still-open cadence question Q-10, now that the period is a named parameter on the platform recurring-timer contract rather than an unstated implementation detail. It is the sharpest parameter in the design: shorten it and the wake, the neglect progression and the mood update all become prompt while the idle budget is spent on the exact machinery the requirement names; lengthen it and the budget is safe while every time-driven behaviour becomes stale. The flip cannot be measured today, only argued, because the budget that would bound it from the other side is not evaluable until a reference machine is recorded.

### Consequences

- None — the decision is pending.
