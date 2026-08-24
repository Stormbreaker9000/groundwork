---
id: NFR-002
type: non_functional
tier: solution
title: Idle CPU and memory footprint of the always-on process
description: While left running with no owner input, the delivered application shall hold mean CPU at or below 1% of one core and peak resident memory at or below 150 MB, measured on the project's designated reference machine (specification pending Q-5).
rationale: The pet is meant to sit open all day, so its idle cost is what decides whether the owner keeps it running — and an app that keeps returning as a fan-spinning, memory-hungry process gets closed, which kills the check-in habit outright. The 1% / 150 MB figures come from the source context and are not in doubt; what is in doubt is the baseline they are measured against, which is why this requirement names the designated reference machine normatively and is unverifiable until Q-5 records that specification. Confidence is low for that reason alone — the budget is deliberately runtime-neutral and survives every answer to Q-4.
fit_criterion: Over a 10-minute idle observation window on the project's designated reference machine — the single baseline desktop hardware and OS specification recorded for the project, which is not yet fixed and is tracked as Q-5 — mean CPU across all processes of the application is <= 1% of one core, peak resident set size is <= 150 MB, and final RSS is within 5% of the 1-minute-mark RSS. Measurement is admissible only against that recorded baseline; no substitute or ad-hoc developer machine may stand in for it, and until Q-5 is answered this requirement has no admissible test environment and can be neither passed nor failed.
priority: must
confidence: low
verification_method: test
status: draft
created_at: 2026-08-24
traces_from: [FR-002, FR-009, CON-001]
traces_to:
  design: []
  tests: []
  code: []
scope: project
parent_scope: null
---

# NFR-002 — Idle CPU and memory footprint of the always-on process

## ISO 25010 Characteristic
Performance Efficiency → Resource utilization (with Capacity implications for
the always-on process)

## Quality Attribute Scenario
- **Source of stimulus:** The owner, who leaves the application running
  unattended between check-ins.
- **Stimulus:** The application sits in an idle steady state — pet alive, window
  open, no owner input, no care action in progress.
- **Environment:** The project's designated reference machine under normal
  desktop use. That machine is a single named baseline whose hardware and OS
  specification has not yet been recorded (Q-5); this requirement depends on it
  normatively rather than assuming one. A continuous 10-minute observation
  window; measurements taken from OS process accounting and summed across every
  process the application owns.
- **Artifact:** The complete delivered runtime — the application process, any
  child or helper processes, and whatever rendering or background timer
  machinery the chosen implementation uses.
- **Response:** The application continues to keep time, render the pet, and
  remain ready for a care action, without accumulating CPU or memory.
- **Response measure:** On the designated reference machine, mean CPU <= 1% of
  one core and peak resident memory <= 150 MB across the 10-minute window; no
  monotonic growth — final RSS within 5% of the RSS sampled at the 1-minute
  mark. A run on any machine other than the recorded baseline is not evidence
  either way.

## Rationale
This is an application designed to be left open indefinitely, so its idle cost
determines whether the owner tolerates it running at all. A budget expressed in
measured CPU and RSS is testable against any candidate implementation, which is
what lets the runtime decision (Q-4) stay open without leaving the quality target
unspecified — so Q-4 is explicitly *not* what limits confidence here. What limits
it is that "1% of one core" and "150 MB" are not comparable figures without a
named baseline to measure them on, and no requirement, constraint or glossary
entry yet fixes one. That gap is tracked as Q-5, and this requirement becomes
verifiable the moment Q-5 is answered — the figures themselves need no revisiting.
CON-001 inherits the same dependency.
