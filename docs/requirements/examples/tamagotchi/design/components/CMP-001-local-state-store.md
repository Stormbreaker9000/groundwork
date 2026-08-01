---
id: CMP-001
type: component
title: Local State Store
description: The sole owner of the application's on-disk state file — the pet's saved stats, its last-saved timestamp, and the owner's local preferences — together with the transactional protocol by which that file is written and validated.
traces_from:
- FR-001
- FR-010
- NFR-002
- NFR-004
- NFR-005
- NFR-006
- CON-002
- CON-003
traces_to:
  adr: []
  diagrams: []
  code: []
  tests: []
status: draft
confidence: high
created_at: 2026-07-30
scope: project
parent_scope: null
responsibility: Owns the application's durable local state as the single source of truth across process lifetimes.
boundary: internal
depends_on:
- IF-001
- IF-002
---

# CMP-001 — Local State Store

The sole owner of the application's on-disk state file — the pet's saved stats,
its last-saved timestamp, and the owner's local preferences — together with the
transactional protocol by which that file is written and validated.

## Responsibility
Owns the application's durable local state as the single source of truth across
process lifetimes.

## Rationale
FR-001 makes durable state a first-class element: the pet's authoritative value
lives on disk between process lifetimes, so something must own the on-disk
representation and the last-saved timestamp that every later computation is
anchored to. NFR-004 is what makes it exactly one something — tolerating a kill at
any write point means no other component may touch the file, so the commit
protocol (temp file, fsync, rename) and the load-side integrity check are owned
here and exposed only as a transactional save. FR-010's missing-or-corrupt path and
the Quarantine of the unreadable file are the load side of that same ownership.
NFR-006 and CON-003 keep the platform-specific parts of this job — app-data path
resolution and atomic rename semantics — inside this component rather than in the
simulation, so a macOS or Linux build changes this component and nothing above it.
NFR-005 and CON-002 are satisfied negatively: this component holds no network
client, and there is no remote counterpart to the state file.
