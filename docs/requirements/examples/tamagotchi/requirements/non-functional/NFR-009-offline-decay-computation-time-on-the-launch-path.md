---
id: NFR-009
type: non_functional
tier: solution
title: Offline-decay computation time on the launch path
description: On launch, the offline-decay computation shall complete within 250 ms at p95 for the worst-case 30-day elapsed interval on the project's designated reference machine.
rationale: FR-002 puts up to 30 days of decay computation on the owner-visible launch path, and nothing else in the set bounds its wall-clock cost. 250 ms keeps the decay stage a small share of a launch that should land inside the ~1 s window a user still perceives as uninterrupted, leaving room for process start, committed-save read and first render. The apportionment is reasoned rather than elicited — no total launch budget was ever stated — and the figure has no admissible baseline until the reference-machine specification is recorded by Q-5, which is why priority is should and confidence is low. The machine-independent half of this concern, which is verifiable today, is NFR-008.
fit_criterion: "On the project's designated reference machine, the offline-decay computation for a 30-day elapsed interval completes in <= 250 ms at p95 and <= 500 ms at maximum across 20 cold-start runs, measured between the completion of the committed-save read and the first render of the pet. This figure is executable only against a fixed reference-machine specification: until open question Q-5 records that specification, no run may be recorded as passing or failing this requirement, and any measurement taken against an unrecorded baseline counts as unassessed rather than passing."
priority: should
confidence: low
verification_method: test
status: draft
created_at: 2026-08-24
traces_from: [FR-002]
traces_to:
  design: []
  tests: []
  code: []
scope: project
parent_scope: null
---

# NFR-009 — Offline-decay computation time on the launch path

## ISO 25010 Characteristic
Performance Efficiency → Time behavior

## Quality Attribute Scenario
- **Source of stimulus:** The owner, relaunching the application after being
  away.
- **Stimulus:** Launch occurs after a 30-day offline interval — the worst case
  that NFR-001's test matrix already exercises — requiring the full elapsed
  decay to be computed and applied before the pet can be shown.
- **Environment:** Cold start on the project's designated reference machine
  (specification pending Q-5) under normal desktop use, with a valid committed
  save file present and no other application load contrived.
- **Artifact:** The offline-decay computation on the launch path, between the
  completion of the committed-save read and the first render of the pet.
- **Response:** The owner sees the post-decay pet without a perceptible stall;
  the decay stage consumes a minor share of the launch rather than dominating
  it.
- **Response measure:** For a 30-day elapsed interval, the computation completes
  in <= 250 ms at p95 and <= 500 ms at maximum across 20 cold-start runs on the
  designated reference machine. The measure is not evaluable until Q-5 records
  that machine's specification; a measurement taken against an unrecorded
  baseline is unassessed, not passing.

## Rationale
Elsewhere the set treats every interaction as instantaneous, but that is an
assertion rather than a measurement, and this one path contradicts it: FR-002
places an interval-proportional computation directly in front of the only moment
the owner meets the product. Bounding the stage at 250 ms keeps the decay work a
minor share of a launch budget rather than its dominant term.

The figure inherits NFR-002's and CON-001's dependency on the unfixed reference
machine (Q-5), which is why confidence is low — until Q-5 is answered, "250 ms"
names a duration with no hardware to hold it against, and the fit criterion says
so rather than pretending otherwise. The verification method is fully defined and
the single missing parameter is tracked, so the requirement is verifiable in the
INCOSE sense even though it cannot be executed today.

Priority is `should` rather than `must` because the property that separates a
correct implementation from a broken one is the scaling behaviour in NFR-008,
which is a `must` and is testable now. This absolute bound is the refinement on
top of it: worth holding, but not a gate that can be enforced before a product
decision lands.
