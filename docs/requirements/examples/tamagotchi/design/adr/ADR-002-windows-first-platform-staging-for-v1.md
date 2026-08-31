---
id: ADR-002
type: adr
title: Windows-first platform staging for v1
description: Whether v1 ships on Windows alone with macOS and Linux staged after it, or on all three desktop targets at once.
traces_from: [CON-003, NFR-006, NFR-003, FR-009, FR-012]
traces_to: {}
status: draft
confidence: high
created_at: '2026-08-24'
decision_status: accepted
considered_options:
- Windows ships first for v1, with macOS and Linux staged after it
- All three desktop targets ship at v1
chosen_option: Windows ships first for v1, with macOS and Linux staged after it
---

# ADR-002: Windows-first platform staging for v1

## Context and Problem Statement

CON-003 requires that no design, dependency or platform-API decision foreclose any of the three desktop targets, and it says explicitly that it asserts no ship order — so the ship order was left as a separate decision to take. It is a real decision because the v1 acceptance surface differs enormously between the two answers: NFR-003's measure runs a scripted screen-reader walkthrough through each platform's own native accessibility stack, FR-009's delivery path rests on each platform's native notification API, and FR-012's byte-identical quarantine move has different file-move semantics on each target. NFR-006's zero-conditionals-outside-the-adapter-layer count is the measure that most depends on the answer, because it is only checkable against a second platform.

## Decision Drivers

- CON-003
- NFR-006
- NFR-003
- FR-009
- FR-012

## Considered Options

### Windows ships first for v1, with macOS and Linux staged after it

- Pros: Concentrates the v1 acceptance surface on one platform's accessibility stack and one set of path and file-move semantics, which is what a team with no dedicated platform specialists can actually verify.
- Cons: The cross-platform boundary still binds in full while only one target is being built, so the platform-adapter seam earns nothing measurable at v1 and a seam drawn wrong stays undetected until the staged targets arrive.

### All three desktop targets ship at v1

- Pros: The zero-conditionals measure and the cross-platform acceptance run are checkable from the start, so an adapter seam drawn in the wrong place is found while it is still cheap to move.
- Cons: Triples the v1 acceptance surface — three native accessibility stacks, three notification APIs and three sets of file-move semantics — against a team constraint of no dedicated platform specialists.

## Decision Outcome

Windows ships first for v1; macOS and Linux are staged after it. The staging changes the ship order only: CON-003's boundary is unaffected by it, so the platform-adapter seam is still drawn now, in full, while only one target is being built.

### Consequences

- Good:
  - Concentrates the v1 acceptance surface on one platform's accessibility stack and one set of path and file-move semantics, which is what a team with no platform specialists can actually verify.
- Bad:
  - CON-003's boundary still binds in full while only one target is being built, so the platform-adapter seam earns nothing measurable at v1.
  - NFR-006's zero-conditionals-outside-the-layer measure has no second platform to be checked against until after v1, so a seam drawn wrong stays undetected until then.
