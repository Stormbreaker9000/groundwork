---
id: NFR-005
type: non_functional
tier: solution
title: Local-only handling of pet and owner data
description: The application shall perform all core pet-simulation function using local storage only, emitting no outbound network connection and transmitting no pet or owner data unless the owner has explicitly opted in.
rationale: The owner was promised a fully offline toy with no telemetry beyond explicit opt-in, and the only way that promise is meaningful is if it is observable at the network interface rather than asserted in a privacy note. It also keeps the app usable with no connectivity at all, which the offline-first constraint requires.
fit_criterion: Across a capture session of >= 30 minutes exercising every functional requirement in this set with no opt-in granted, 0 outbound TCP, UDP or DNS attempts are attributable to the application; all pet and owner data is written only within the application's local data directory and its quarantine location.
priority: must
confidence: high
verification_method: test
status: draft
created_at: 2026-08-24
traces_from: [FR-001, FR-009, CON-002]
traces_to:
  design: []
  tests: []
  code: []
scope: project
parent_scope: null
---

# NFR-005 — Local-only handling of pet and owner data

## ISO 25010 Characteristic
Security → Confidentiality (with Resistance implications: no network attack
surface is exposed at all)

## Quality Attribute Scenario
- **Source of stimulus:** An observer of the machine's network traffic — the
  privacy-conscious owner auditing the app, or a reviewer verifying the claim.
- **Stimulus:** The owner exercises every functional requirement in this set —
  the four care actions, wake, save and load, offline decay, mood display,
  sickness and terminal progression, local reminders, default-pet
  initialization, and save-file quarantine — with no opt-in granted.
- **Environment:** Normal operation on a machine with all traffic captured at
  the OS network interface, including a run with the network interface disabled
  entirely.
- **Artifact:** The whole application process, its dependencies, its local data
  directory, and the quarantine location.
- **Response:** All function completes using local storage and local
  notifications only; no outbound connection is attempted; the app behaves
  identically with networking disabled.
- **Response measure:** 0 outbound TCP, UDP or DNS attempts attributable to the
  application across a >= 30 minute capture that exercises every functional
  requirement in this set; 100% of those requirements pass with the network
  interface disabled; pet and owner data written only inside the application's
  local data directory and its quarantine location; any future opt-in telemetry
  path is off by default and inert until explicitly enabled by the owner.

## Rationale
Offline-only operation is both a stated constraint and the basis of the privacy
promise made to the owner. Stating it as a measurable network-capture assertion
turns it into a regression test rather than a policy statement, and the
network-disabled run proves no core function has quietly acquired a dependency
on connectivity. The scope is bound to "every functional requirement in this
set" rather than a fixed range so that a later-added FR cannot fall outside the
capture session by omission — which is exactly how FR-011 and FR-012 escaped the
previous wording.
