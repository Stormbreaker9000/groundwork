---
id: IF-027
type: interface
title: Platform Presentation Surface
description: The platform-adapter contract through which the owner's view is painted onto the host's rendering surface and the pet's mood expression and health status are exposed as text to the platform's native accessibility API.
traces_from: [FR-002, FR-007, NFR-003, NFR-006, NFR-009, CON-003]
traces_to:
  adr: [ADR-002, ADR-003]
  diagrams: []
  code: []
  tests: []
status: draft
confidence: medium
created_at: '2026-08-24'
scope: project
parent_scope: null
provider: CMP-017
operations:
- name: draw_view
  summary: Paint the supplied owner-facing view onto the host's rendering surface and return once the frame has been presented, so that a caller measuring a render boundary has one to observe.
  interaction: synchronous
- name: announce_status_text
  summary: Expose the supplied textual equivalents of the pet's mood expression and health status to the platform's native accessibility API, so a screen reader on this platform conveys them without reference to colour.
  interaction: synchronous
error_modes:
- No rendering surface is available on this platform — nothing can be painted, no frame is presented, and a caller measuring first render has no boundary to close.
- The frame is presented but the surface is occluded, minimised, or on a disconnected display — the owner sees nothing while the application correctly believes it rendered; not detectable through this contract.
- The platform's native accessibility stack is absent or not running in this session — the status text is not exposed, and NFR-003 counts the mood and health status as not perceivable rather than as degraded.
- The supplied status text is empty, or a mood expression or health status has no textual equivalent — rejected rather than announced blank, because a blank announcement is indistinguishable to a screen-reader user from no announcement at all.
- The host coalesces or interrupts consecutive announcements — a rapid sequence of state changes reaches the owner as only the last of them, which is what NFR-003's scripted screen-reader walkthrough on each platform is run to catch.
- A platform exposes accessibility through a stack this build has not integrated — the visual view still paints and the status text reaches nobody, so the failure is silent on that platform and visible only in NFR-006's cross-platform acceptance run.
---

# IF-027 — Platform Presentation Surface

The platform-adapter contract through which the owner's view is painted onto the host's rendering
surface and the pet's mood expression and health status are exposed as text to the platform's
native accessibility API.

## Operations
- **draw_view** — Paint the supplied owner-facing view onto the host's rendering surface and
  return once the frame has been presented.
- **announce_status_text** — Expose the supplied textual equivalents of the pet's mood expression
  and health status to the platform's native accessibility API.

## Interaction
Both synchronous. `draw_view` must be, because both of its callers' contracts depend on knowing
the frame landed: IF-017's first render is the closing boundary of NFR-009's measurement window,
and IF-030's redraw coalescing needs to know when a draw is still in flight. `announce_status_text`
is synchronous too, but not because the call is purely local — that premise was wrong. On some
targets the announcement goes to an accessibility bridge inside this process; on others it crosses
to a service in its own right, AT-SPI on a CON-003 Linux target being a D-Bus service, which is why
this contract's own third and sixth error modes have that stack absent, not running, or
un-integrated. Synchronous is the right answer under either premise, and the remote one argues for
it the more strongly: it is exactly when there is a party on the other end that can be missing that
the caller must learn the announcement did not land. Making it asynchronous would make NFR-003's
failure — a status that never became perceivable — unreportable to the only component that could
act on it.

**Why the two seams are one contract.** They are both provided by the platform adapter and both
consumed by exactly one component, the presentation shell, and the consumer uses both every time
it uses either: NFR-003 requires the textual equivalent to accompany the visual state, so there is
no render in this product that is drawn but not announced, and no announcement that does not
accompany a render. Splitting them would hand the shell two contracts it always holds together,
which is the shape the Interface Segregation rule exists to avoid rather than to produce. The
operations stay two, because their failure modes are entirely different and NFR-003 and NFR-006
trace to them separately.

**Why these seams sit in the adapter at all.** NFR-006 names rendering and accessibility
integration among the platform-touching behaviours that must live inside the platform-adapter
layer, and counts conditionals outside it against a target of zero. The previous round had the
presentation shell reaching both directly, which put two of the six named seams outside the layer
that exists to contain them; NFR-003's measure compounds it, because it runs through each
platform's own native stack, so "announce as text" is three different integrations behind one
contract. This is the seam that keeps that divergence in one place. CON-003 stages the platforms —
Windows first, macOS and Linux after v1 — so in practice this contract has one implementation at
v1 and its cross-platform value is realised later; that is a reason to fix the seam now, not to
defer it.

## Error Modes
- No rendering surface available — nothing painted, and a caller measuring first render has no
  boundary to close.
- The frame is presented but the surface is occluded, minimised, or on a disconnected display —
  the owner sees nothing while the application correctly believes it rendered.
- The platform's native accessibility stack is absent or not running — the status text is not
  exposed, which NFR-003 counts as a failure rather than a degradation.
- Empty status text, or a mood or health status with no textual equivalent — rejected rather than
  announced blank.
- The host coalesces or interrupts consecutive announcements — a rapid sequence reaches the owner
  as only its last.
- A platform whose accessibility stack this build has not integrated — the view paints, the text
  reaches nobody, and only NFR-006's cross-platform run shows it.

## Rationale
Satisfies both platform capabilities declared by CMP-016: drawing the owner's view, and announcing
mood and health status as text through the native accessibility API. Confidence is medium: Q-8
(still_open) asks whether the Sleeping state is rendered to the owner, and its answer changes what
a view carries and what the announcement must include. The operations survive either answer; their
content does not.
