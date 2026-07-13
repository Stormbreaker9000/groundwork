---
id: NFR-002
type: non_functional
tier: solution
title: Idle CPU and memory footprint budget
description: While running idle in the background, the application process shall consume no more than the defined CPU and resident-memory budget on the reference machine.
rationale: The app is always-on and competes with the user's real work for resources; an ambient companion that noticeably heats the fan or eats hundreds of megabytes of RAM will be uninstalled, so a hard idle budget is central to the product's viability and directly gates the runtime/framework choice.
fit_criterion: Over a 10-minute idle window on the reference machine, average CPU utilization by the app process is <= 1% of one core and resident memory is <= 150 MB, sampled at 1-second intervals.
priority: must
confidence: low
verification_method: test
status: draft
created_at: 2026-07-10
traces_from: []
traces_to:
  design: []
  tests: []
  code: []
scope: project
parent_scope: null
---

# NFR-002 — Idle CPU and memory footprint budget

## ISO 25010 Characteristic
Performance Efficiency → Resource Utilization

## Quality Attribute Scenario
- **Source of stimulus:** The passage of time with no user interaction (idle clock).
- **Stimulus:** The application sits in the background performing only its decay tick.
- **Environment:** Steady-state idle operation on the reference desktop machine, no window focus.
- **Artifact:** The running application process and its chosen UI runtime.
- **Response:** The process maintains its timers and state without sustained CPU or memory growth.
- **Response measure:** Over a 10-minute idle window, average CPU utilization is <= 1% of one core and resident memory is <= 150 MB, sampled at 1-second intervals.

## Rationale
The app is always-on and competes with the user's real work for resources; an
ambient companion that noticeably heats the fan or eats hundreds of megabytes of
RAM will be uninstalled, so a hard idle budget is central to the product's
viability and directly gates the runtime/framework choice (Q-4). The exact budget
numbers depend on the framework selected, so this target is held at low confidence
until that decision is made.
