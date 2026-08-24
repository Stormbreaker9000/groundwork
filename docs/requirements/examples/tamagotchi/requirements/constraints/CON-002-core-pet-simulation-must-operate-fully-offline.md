---
id: CON-002
type: constraint
tier: business
title: Core pet simulation must operate fully offline
description: "The application shall operate fully offline: no core pet-simulation function — launch, offline-elapsed decay, the four care interactions, mood expression, health progression, persistence, recovery, or care reminders — may depend on an outbound network connection or a remote service."
rationale: "The pet, its history and its care record are personal local data belonging to a single desktop owner, and the product promises that the pet is theirs and always there. A dependency on a remote service would make the pet unavailable exactly when the owner is offline, breaking the daily-return habit through no fault of the owner, and would move personal care data off the machine. This is an absolute boundary, not a reliability target: the core loop either works with the network unplugged or it does not."
fit_criterion: With every network interface on the test machine disabled, 100% of core pet-simulation function completes normally — launch, offline-elapsed decay application, all four care interactions, mood display, health progression, save, and recovery from a missing or corrupted save file. Inspection of the core-path dependency graph finds 0 network client libraries and 0 outbound socket or HTTP calls.
priority: must
confidence: high
verification_method: inspection
status: draft
created_at: 2026-08-24
traces_from: []
traces_to:
  design: []
  tests: []
  code: []
scope: project
parent_scope: null
---

# CON-002 — Core pet simulation must operate fully offline

## Statement
The application shall operate fully offline. No core pet-simulation
function — launch, offline-elapsed decay, the four care interactions,
mood expression, health progression, persistence, recovery, or care
reminders — may depend on an outbound network connection or a remote
service. Care reminders in particular are local notifications only.

## Category
technical

## Bounds / Implemented by
Bounds FR-001 (persist pet state — the store must be local, ruling out
cloud sync as the system of record), FR-009 (care-reminder
notifications — local delivery only, no push service), and NFR-005
(local-only handling of pet and owner data).

## Rationale
The pet, its history and its care record are personal local data
belonging to a single desktop owner, and the product promises the pet
is theirs and always there. A remote dependency would make the pet
unavailable exactly when the owner is offline — breaking the
daily-return habit through no fault of the owner — and would move
personal care data off the machine. This is an absolute boundary rather
than a reliability target: the core loop either works with the network
unplugged or it does not.

## Fit Criterion
With every network interface on the test machine disabled, 100% of core
pet-simulation function completes normally — launch, offline-elapsed
decay application, all four care interactions, mood display, health
progression, save, and recovery from a missing or corrupted save file.
Inspection of the core-path dependency graph finds 0 network client
libraries and 0 outbound socket or HTTP calls.
