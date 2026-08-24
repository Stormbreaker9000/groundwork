---
id: BR-002
type: business_rule
tier: business
title: Pending Q-2, a terminal pet's state is preserved and no disposition is implemented
description: "Until open question Q-2 is resolved, no terminal pet's accumulated state may be discarded or overwritten, and no disposition of a terminal pet may be implemented. Whichever disposition Q-2 selects shall be a single project-wide policy applied consistently to every terminal pet."
rationale: "What becomes of a pet once it has reached the terminal status — permanence, or a configurable soft reset — is open question Q-2, owned by product, and is genuinely unresolved: it trades the weight of a permanent loss against the risk of an owner abandoning the product after one bad week. A previous draft invented \"reset to a new pet\" as the answer; that was a fabrication. This rule is the interim policy that keeps BOTH answers reachable rather than merely declining to pick one — a pet whose accumulated state still exists can later be made permanent, archived, or reset, while a pet whose state has already been overwritten has had Q-2 answered for it silently and irreversibly. The prohibition on implementing any disposition at all follows from the same purpose: an implemented disposition is a decision taken, and Q-2 is not this rule's to take. That prohibition binds every code path, not only the transition that produces the terminal status, which is why it is verified by inspection of all state-writing paths. Whether a disposition must additionally be surfaced to the owner is a candidate constraint on Q-2's answer, recorded against Q-2 rather than asserted here, because requiring it would itself rule out answers Q-2 may legitimately choose. Held at low confidence because the rule is scoped to a pending question."
fit_criterion: "Inspection of every code path that writes, clears or replaces persisted pet state finds 0 paths that discard or overwrite the accumulated state of a pet in the terminal status. At no point does the codebase contain more than one implementation of a terminal-pet disposition policy; while Q-2 is open that count is zero."
priority: must
confidence: low
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

# BR-002 — Pending Q-2, a terminal pet's state is preserved and no disposition is implemented

## Statement
Until open question Q-2 is resolved, no terminal pet's accumulated state may
be discarded or overwritten, and no disposition of a terminal pet may be
implemented. Whichever disposition Q-2 selects shall be a single
project-wide policy, applied consistently to every terminal pet.

This rule asserts no disposition. It does not decide whether the terminal
status is permanent or a configurable soft reset; it fixes only what must
remain true while that question is open.

## Implemented by
FR-001 (persist pet state on stat change and app close) implements the
preservation clause: persistence is the only place a pet's accumulated state
can be destroyed, so the prohibition on discarding or overwriting a terminal
pet's state binds the save-and-replace path.

FR-008 (progress sustained neglect toward a terminal health status)
implements the no-implementation clause at the point of transition: FR-008
is the only requirement that reaches the terminal status, and it is
therefore the requirement most likely to acquire a disposition by
continuation. FR-008 deliberately asserts nothing about what follows that
status — this rule is why it stops there, and why an implementation may not
quietly continue past it.

The prohibition itself is not confined to FR-008. A disposition could
equally be written into a launch path, which is why this rule's fit
criterion inspects every code path that writes, clears or replaces
persisted pet state rather than only FR-008's.

## Rationale
Q-2 — permanence versus a configurable soft reset — is a product call with
real weight on both sides, and it is not one to settle by default inside a
requirement. The purpose of this rule is not to decline the question but to
keep both of its answers reachable while it is open. A terminal pet whose
accumulated state still exists can later be made permanent, archived, or
reset; a terminal pet whose state was already overwritten has had Q-2
answered for it, silently and irreversibly, by whichever code path ran
first. A soft reset can archive rather than delete, so this interim
invariant forecloses nothing that Q-2 might choose.

The prohibition on implementing any disposition follows from the same
purpose. An implemented disposition is a decision taken; while Q-2 is open
there is no answer to implement, and building one would settle the question
by shipping order rather than by product judgement. The single-policy clause
covers the moment after Q-2 closes: it prevents the codebase acquiring two
competing dispositions, which would make Q-2's answer a merge problem rather
than a decision.

A requirement that a disposition be surfaced to the owner is deliberately
absent. It is a plausible constraint on Q-2's answer, but asserting it here
would rule out candidate answers Q-2 may legitimately choose — a silent soft
reset on next launch among them — and a rule whose purpose is to hold a
question open must not pre-commit its answer. It is recorded against Q-2 as
an input to that decision instead.

This is a separate rule from BR-001 because it cannot share BR-001's
verification method: causation is proven by exercising transition paths
under test, whereas preservation is proven by inspecting the code paths that
write persisted state. Either can hold while the other fails, so a single
verdict across both would carry no usable information.

## Fit Criterion
Inspection of every code path that writes, clears or replaces persisted pet
state finds 0 paths that discard or overwrite the accumulated state of a pet
in the terminal status.

At no point does the codebase contain more than one implementation of a
terminal-pet disposition policy; while Q-2 is open that count is zero.
