<!--
  GENERATED FILE — do not edit.
  Source: docs/requirements/examples/tamagotchi/requirements/business-rules/
  Regenerate: python3 site/scripts/export_examples.py
-->

# Business rules

The 2 business rules from the `tamagotchi` worked example, exactly as the pipeline wrote them.

## BR-001 — Terminal end-of-life is reached only through sustained, unremedied neglect [#br-001]

| Field | Value |
| --- | --- |
| Type | business_rule |
| Tier | business |
| Priority | must |
| Status | draft |
| Confidence | low |
| Verification | test |

### Statement
A pet reaches the terminal end-of-life status only as the consequence of
sustained, unremedied neglect by its owner: the pet must have passed through
the sick state and left at least one pet stat below its neglect threshold,
unremedied, for the defined neglect period. Elapsed time alone, or a fault in
the application, is never a legitimate cause of the terminal status.

This rule asserts nothing about what happens to a pet after it reaches the
terminal status. That question is open question Q-2, and the policy that holds
in the meantime is BR-002.

### Implemented by
FR-008 (progress sustained neglect toward a terminal health status) enforces
this rule in the system, and enforces it at the same granularity this rule
states it: FR-008 AC-2 advances a sick pet to the terminal status when at
least one stat has stayed below its neglect threshold for the further defined
duration. FR-008 likewise asserts nothing about what follows the terminal
status; both artifacts are held at low confidence until Q-1 fixes the neglect
period and Q-2 closes.

### Rationale
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

### Fit Criterion
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

## BR-002 — Pending Q-2, a terminal pet's state is preserved and no disposition is implemented [#br-002]

| Field | Value |
| --- | --- |
| Type | business_rule |
| Tier | business |
| Priority | must |
| Status | draft |
| Confidence | low |
| Verification | inspection |

### Statement
Until open question Q-2 is resolved, no terminal pet's accumulated state may
be discarded or overwritten, and no disposition of a terminal pet may be
implemented. Whichever disposition Q-2 selects shall be a single
project-wide policy, applied consistently to every terminal pet.

This rule asserts no disposition. It does not decide whether the terminal
status is permanent or a configurable soft reset; it fixes only what must
remain true while that question is open.

### Implemented by
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

### Rationale
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

### Fit Criterion
Inspection of every code path that writes, clears or replaces persisted pet
state finds 0 paths that discard or overwrite the accumulated state of a pet
in the terminal status.

At no point does the codebase contain more than one implementation of a
terminal-pet disposition policy; while Q-2 is open that count is zero.
