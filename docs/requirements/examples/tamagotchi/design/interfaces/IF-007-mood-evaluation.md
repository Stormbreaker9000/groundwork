---
id: IF-007
type: interface
title: Mood Evaluation
description: The contract through which the presentation layer obtains the pet's current Mood as a named semantic value, separate from any decision about how that Mood is drawn or announced.
traces_from:
- FR-007
- FR-008
- NFR-003
traces_to:
  adr: []
  diagrams: []
  code: []
  tests: []
status: draft
confidence: medium
created_at: 2026-07-30
scope: project
parent_scope: null
provider: CMP-005
operations:
- name: current_mood
  summary: Return the pet's current Mood as a named value derived from its Stats and lifecycle state, carrying no colour, sprite, or other presentation choice.
interaction: synchronous
error_modes:
- Mood requested before Stats and lifecycle state are available — no Mood can be derived, and the caller must render nothing rather than a default that reads to the owner as a real Mood.
- Stat and lifecycle combination falls outside every defined Mood band — the mapping is incomplete and must say so rather than return an arbitrary nearby band, because NFR-003 announces this value by name to a screen reader.
---

# IF-007 — Mood Evaluation

The contract through which the presentation layer obtains the pet's current Mood as a
named semantic value, separate from any decision about how that Mood is drawn or
announced.

## Operations
- **current_mood** — Return the pet's current Mood as a named value derived from its
  Stats and lifecycle state, carrying no colour, sprite, or other presentation choice.

## Interaction
Synchronous, and close enough to be worth stating. FR-007 requires the displayed
expression to follow a threshold crossing within one second, which on its own argues
for a pushed mood-changed notification. It is a pull here because CMP-006 already
subscribes to stat changes (IF-005) and lifecycle transitions (IF-006), so it already
has the edges on which a mood could have changed and can re-derive on those edges — a
third subscription would add a second, independently-timed stream that could disagree
with the values drawn beside it. What would tip it to asynchronous is the mood mapping
becoming expensive or depending on inputs the window does not already observe; the
cost of the current choice is one extra call per observed change.

## Error Modes
- Mood requested before Stats and lifecycle state are available — no Mood can be
  derived, and the caller must render nothing rather than a default that reads to the
  owner as a real Mood.
- Stat and lifecycle combination falls outside every defined Mood band — the mapping
  is incomplete and must say so rather than return an arbitrary nearby band, because
  NFR-003 announces this value by name to a screen reader.

## Rationale
Satisfies CMP-006's declared need to obtain the Mood as a named value. NFR-003 is why
this is a contract rather than a rendering detail: the sprite and the announced
accessible name have to be two renderings of one value, which is only guaranteed if
the window is handed the value instead of computing it. Medium confidence because the
pull-versus-push choice above is inferred from the window's existing subscriptions,
not declared anywhere.
