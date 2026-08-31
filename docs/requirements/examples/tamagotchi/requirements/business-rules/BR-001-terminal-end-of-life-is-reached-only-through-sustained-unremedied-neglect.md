---
id: BR-001
type: business_rule
tier: business
title: Terminal end-of-life is reached only through sustained, unremedied neglect
description: "A pet reaches the terminal end-of-life status only as the consequence of sustained, unremedied neglect: it must have passed through the sick state and left at least one pet stat below its neglect threshold, unremedied, for the defined neglect period. Elapsed time alone, or a fault in the application, is never a legitimate cause."
rationale: "The emotional weight of the terminal status is what gives the daily-return habit its stakes, so the policy must be that it is earned by the owner's own sustained neglect and never by elapsed time alone, a crash, or a save file that fails to load. Neglect is measured per stat, not across the pet as a whole: one need left unmet for the neglect period is neglect, which is the same threshold FR-008 enforces and the reason an owner who feeds hourly but never cleans has still neglected the pet. This rule states only the causation half of the end-of-life policy; it is verified by test against transition paths. The interim policy governing what may be done with a terminal pet before open question Q-2 closes is carried separately by BR-002, because that half is verified by inspection of code paths rather than by test and can hold or fail independently of this one. Confidence is low: the neglect period has no numeric value until decay-curve tuning (Q-1) fixes one, and the meaning of the terminal status itself stays provisional until Q-2 closes."
fit_criterion: "100% of terminal transitions arrive via the sick state and 0% arrive directly from the healthy state. 0% of terminal transitions occur for a pet in which every stat was raised back above its neglect threshold at some point within the defined neglect period; a care interaction that raises a different stat and leaves the neglected one below its threshold does not interrupt the period. 0 terminal transitions arise from an application fault: the recovery paths for a missing save file and for a save file that fails integrity validation produce no terminal pet under any input."
priority: must
confidence: low
verification_method: test
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

# BR-001 — Terminal end-of-life is reached only through sustained, unremedied neglect

## Statement
A pet reaches the terminal end-of-life status only as the consequence of
sustained, unremedied neglect by its owner: the pet must have passed through
the sick state and left at least one pet stat below its neglect threshold,
unremedied, for the defined neglect period. Elapsed time alone, or a fault in
the application, is never a legitimate cause of the terminal status.

This rule asserts nothing about what happens to a pet after it reaches the
terminal status. That question is open question Q-2, and the policy that holds
in the meantime is BR-002.

## Implemented by
FR-008 (progress sustained neglect toward a terminal health status) enforces
this rule in the system, and enforces it at the same granularity this rule
states it: FR-008 AC-2 advances a sick pet to the terminal status when at
least one stat has stayed below its neglect threshold for the further defined
duration. FR-008 likewise asserts nothing about what follows the terminal
status; both artifacts are held at low confidence until Q-1 fixes the neglect
period and Q-2 closes.

## Rationale
The emotional weight of the terminal status is what gives the daily check-in
its stakes, so the policy must be that it is earned by the owner's own
sustained neglect — never by elapsed time alone, and never by a crash or a bad
save file. A pet that dies because the application failed is not a pet the
owner neglected, and treating the two the same would make the loss arbitrary
and the stakes meaningless.

Neglect is measured per stat rather than across the pet as a whole. One need
left unmet for the neglect period is neglect: an owner who feeds hourly and
never cleans keeps hygiene below its threshold continuously, and that pet has
been neglected however attentive the feeding was. Requiring every need to be
starved at once would let a single need be ignored indefinitely with no
consequence — the outcome FR-008's rationale rejects for the same reason.

This rule carries only the causation half of the end-of-life policy. The
interim preservation policy — what may and may not be done with a terminal pet
while Q-2 is unresolved — is BR-002. The two are separate rules because they
are measured differently: causation is proven by exercising transition paths
under test, while preservation is proven by inspecting the code paths that
write persisted state. Either can hold while the other fails, so a single
verdict across both would carry no usable information.

## Fit Criterion
100% of terminal transitions arrive via the sick state; 0% arrive directly from
the healthy state. 0% of terminal transitions occur for a pet in which every
stat was raised back above its neglect threshold at some point within the
defined neglect period. A care interaction that raises a different stat and
leaves the neglected one below its threshold does not interrupt the period.
0 terminal transitions arise from an application fault: the recovery paths for
a missing save file and for a save file that fails integrity validation produce
no terminal pet under any input.

The neglect-period figures are checkable only once decay-curve tuning (Q-1)
fixes a value for that period.
