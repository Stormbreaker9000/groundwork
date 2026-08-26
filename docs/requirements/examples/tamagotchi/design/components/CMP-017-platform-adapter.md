---
id: CMP-017
type: component
title: Platform Adapter
description: The single named layer holding every platform-specific behaviour the application needs — local data directory paths, file reads, atomic writes, log measurement and roll-over, the byte-identical quarantine move, wall-clock and interval access, recurring-timer access, native notification delivery, the host rendering surface, and native accessibility exposure.
traces_from: [FR-002, FR-009, FR-011, FR-012, NFR-003, NFR-004, NFR-005, NFR-006, NFR-007, CON-002, CON-003]
traces_to:
  adr: [ADR-002, ADR-003, ADR-004, ADR-006]
  diagrams: [DIA-003]
  code: []
  tests: []
status: draft
confidence: high
created_at: '2026-08-24'
scope: project
parent_scope: null
responsibility: Confines every platform-specific behaviour to one layer so the rest of the codebase stays platform-agnostic.
boundary: internal
depends_on: [IF-023, IF-024]
---

# CMP-017 — Platform Adapter

The single named layer holding every platform-specific behaviour the application needs
— local data directory paths, file reads, atomic writes, log measurement and roll-over,
the byte-identical quarantine move, wall-clock and interval access, recurring-timer
access, native notification delivery, the host rendering surface, and native
accessibility exposure.

## Responsibility
Confines every platform-specific behaviour to one layer so the rest of the codebase
stays platform-agnostic.

## Rationale
NFR-006 is the most directly structural requirement in the set: it names a layer and
then counts violations of it — zero platform conditionals outside it — and enumerates
the seams it must hold, including the byte-identical quarantine move and the
across-close wall-clock interval derivation. CON-003 makes that boundary binding now,
while only Windows is being built, because a platform-exclusive API adopted anywhere
outside this layer forecloses a named target. NFR-005 and CON-002 add the other half:
this is the only component permitted to touch anything outside the process, and what it
touches is enumerable and contains no network client.

NFR-006's enumeration is taken in full rather than in part. Rendering and accessibility
integration are the two seams most easily left outside a layer like this one, because the
runtime appears to supply them and it is tempting to read "the runtime does it" as
"nobody has to own it". NFR-006 does not allow that reading — it counts platform
conditionals outside this layer against a target of zero — and NFR-003's measure runs
through three distinct native accessibility stacks (UI Automation, NSAccessibility,
AT-SPI). So both live here: this layer owns the host surface the owner-facing view is
drawn onto, and the exposure of the pet's mood expression and health status as text to
whichever native accessibility API the platform provides. CMP-016 supplies the semantic
content; this layer decides what each platform does with it. A-21 assumes each target
provides a usable native accessibility API, and NFR-003 is cited here for that reason.

Recurring-timer access is the third seam of the same kind, and it is named in the same
clause of NFR-006 as the clock: "wall-clock and timer access". The two are not one seam.
Reading the clock answers what time it is; a recurring timer drives the application
without being asked, and it is the machinery NFR-002 budgets by name at idle. So this
layer offers both, through separate contracts, and CMP-010 keeps what is genuinely its
own — the evaluation cadence's period, its coalescing rule, and when it starts and stops
— while consuming timer access from here rather than reaching for a platform timer
directly. Without that seam, CMP-010 could not observe an unavailable timer facility at
all, and NFR-006's zero-conditionals count would be violated by the one component whose
whole purpose is to be driven by the platform.

None of those three seams — the rendering surface, accessibility exposure and timer
access — is declared as an outward need on an external component, and the asymmetry with
the clock and the notification service is deliberate. It is not, however, a claim about
where the code runs. The design context names exactly two integration points, the OS
notification service and the platform wall clock, and this decomposition does not add to
that list; the file primitives this layer already offers are held on the same footing.
All three are real platform facilities that can be absent or not running in a given
session — NFR-003's measure runs through three distinct native accessibility stacks, and
AT-SPI on a CON-003 target is a service in its own right — and the contracts this layer
offers say so in their error modes. What keeps them out of the external component set is
the integration-point list this stage inherited, not a belief that there is no party on
the other end of the call.

The clock contract it offers returns a signed interval and applies none of the
non-positive-interval rules: FR-002's clamp belongs to CMP-004, FR-011's re-basing to
CMP-006 and FR-008's re-basing to CMP-005, and a clock that pre-corrected any of them
would defeat all three (A-6, A-7).
