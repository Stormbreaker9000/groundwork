---
id: CON-001
type: constraint
tier: solution
title: Runtime baseline overhead must leave headroom in the idle-footprint budget
description: "The runtime or application shell the product is built on shall consume no more than 40% of the idle-footprint budget while running an empty do-nothing application, leaving the remainder as headroom for the pet application itself. Any candidate whose empty-shell baseline alone exceeds that allowance is excluded from the design space."
rationale: "The pet is an always-on background companion the owner is expected to leave running all day; a runtime that consumes a meaningful share of the machine at idle makes the daily-return habit the product exists to create feel like a cost rather than a small pleasure, and owners will quit the app between check-ins, breaking the loop. The budget therefore removes whole runtime families from the design space rather than being tuned — a shell whose empty baseline already exceeds it (a full Chromium/Electron shell being the stated example) cannot be brought under it by optimising the pet code. The allowance exists because the same reasoning applies to a shell that merely sits just under the budget while empty: the delivered application must fit inside the same figure, so a screen with no headroom admits precisely the candidates it exists to exclude. Which runtime is actually selected is open question Q-4 (owner engineering) and is deliberately NOT decided here; this constraint only bounds the set of admissible answers, so it is held at low confidence until Q-4 closes."
fit_criterion: "For any candidate runtime, an empty do-nothing application built on it and left idle for 10 minutes on the reference machine consumes no more than 40% of the NFR-002 idle budget — that is, <=0.4% of one core and <=60 MB RSS — leaving the remaining 0.6% of one core and 90 MB RSS as headroom for the pet application itself. Binary check: a candidate whose empty-shell baseline exceeds either figure is excluded from selection and is recorded as rejected in the runtime decision record. The screen is executable only against a fixed reference-machine specification: until open question Q-5 records that specification, no candidate may be recorded as having passed or failed this screen, and any candidate measured against an unrecorded baseline counts as unassessed rather than admitted."
priority: must
confidence: low
verification_method: analysis
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

# CON-001 — Runtime baseline overhead must leave headroom in the idle-footprint budget

## Statement
The runtime or application shell the product is built on shall consume no more
than 40% of the idle-footprint budget while running an empty do-nothing
application — no more than 0.4% of one core and no more than 60 MB RSS against
the NFR-002 budget of 1% of one core and 150 MB RSS. The remaining 0.6% of a
core and 90 MB RSS is reserved as headroom for the pet application itself.

Any runtime or application shell whose baseline overhead alone — measured with
no pet logic running — exceeds that allowance is excluded from the design
space. A full Chromium/Electron-class shell is the stated example of an
excluded runtime. This constraint names no chosen runtime; the selection is
open question Q-4.

The screen depends normatively on the reference-machine specification recorded
by open question Q-5. Until Q-5 is answered, no candidate may be recorded as
having passed or failed this screen; a candidate measured against an
unrecorded baseline is unassessed, not admitted.

## Category
technical

## Bounds / Implemented by
Bounds NFR-002 (idle CPU and memory footprint of the always-on process).
NFR-002 states the measurable quality target on a scale; CON-001 is the
boundary on the design space that target implies — it removes runtime options
outright at selection time rather than being tuned toward afterwards.

## Rationale
The pet is an always-on background companion the owner is expected to leave
running all day. A runtime that consumes a meaningful share of the machine at
idle makes the daily-return habit feel like a cost, and owners will quit the
app between check-ins — breaking the attachment loop the product exists to
create. A shell whose empty baseline already exceeds the budget cannot be
brought under it by optimising pet code, so the boundary must be applied at
runtime-selection time.

The headroom allowance exists because that same argument holds for a shell
sitting just under the budget: the delivered application has to fit inside the
same 150 MB, so a screen with no allowance would admit a 149 MB shell that
makes NFR-002 unachievable before a line of pet code is written. The allowance
is set at two fifths because the delivered application adds to the empty shell
everything the pet actually is — sprite and mood-animation assets held in
memory, the decay scheduler, the persistence layer and its save buffer — and
because a shell's own footprint grows once it renders a real window rather than
nothing. 90 MB and 0.6% of a core is the smallest remainder that work can be
expected to fit in without measurement to argue from; the split is an
engineering judgement recorded as an assumption, not a stated figure, and is
one of the reasons this constraint is held at low confidence.

Which runtime is selected is open question Q-4 (owner: engineering); this
constraint deliberately asserts no positive choice.

## Fit Criterion
For any candidate runtime, an empty do-nothing application built on it and left
idle for 10 minutes on the reference machine consumes no more than 40% of the
NFR-002 idle budget: <=0.4% of one core and <=60 MB RSS. A candidate whose
empty-shell baseline exceeds either figure is excluded from selection and is
recorded as rejected in the runtime decision record.

The screen is executable only against a fixed reference-machine specification.
Until open question Q-5 records that specification, no candidate may be
recorded as having passed or failed this screen, and any candidate measured
against an unrecorded baseline counts as unassessed rather than admitted.
