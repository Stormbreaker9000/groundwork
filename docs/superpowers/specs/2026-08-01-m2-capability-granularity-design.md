# M2 Capability & Interface Granularity — Design

**Ticket:** STO-217
**Date:** 2026-08-01
**Status:** approved, ready for implementation planning

## Problem

Nothing in the M2 pipeline tells the component specialist how finely to slice a
capability, or tells the interface specialist whether two capabilities from the
same provider are one interface or two. Both specialists independently reported
this as the biggest gap in their instructions after the STO-99 end-to-end run.
Neither was prompted to look for it.

The completeness check cannot catch a wrong choice. It verifies that every
declared capability is satisfied by exactly one interface — not that the set was
carved correctly in the first place. "Preserve the pet's state across restarts"
(one capability, one interface) and "load saved state" + "record current state"
(two, two) both satisfy every rule currently written down. Two runs over
identical requirements can produce twelve interfaces or eight with nothing
violated in either.

That undermines the reproducibility the rest of the pipeline works hard for, and
it makes the artifact count a coin-flip rather than a design decision.

## Evidence

Two findings from the shipped tamagotchi example, both new to this design work.

**The consumer test reproduces a judgment the specialist already made.** CMP-003
provides three interfaces. The ticket cites this as a case where one interface
"would have passed identically":

| Interface | Consumers |
| --- | --- |
| IF-005 Pet Stat Observation | CMP-004, CMP-005, CMP-006, CMP-008 |
| IF-008 Care Action Application | CMP-006 |
| IF-009 Session State Seeding | CMP-007 |

Three of IF-005's four consumers only observe; IF-009's sole consumer only
seeds. A rule that separates interfaces unless every consumer of one needs the
others produces exactly the split the specialist chose intuitively. The rule
ratifies the example rather than invalidating it.

**Operation counts are uniform in a way design does not explain.** Across all
twelve interfaces:

| Interface | Ops | Interface | Ops | Interface | Ops |
| --- | --- | --- | --- | --- | --- |
| IF-001 | 2 | IF-005 | 2 | IF-009 | 2 |
| IF-002 | 2 | IF-006 | 2 | IF-010 | 2 |
| IF-003 | 2 | IF-007 | **1** | IF-011 | 2 |
| IF-004 | 2 | IF-008 | 2 | IF-012 | 2 |

Eleven of twelve have exactly two operations. Twelve independent contracts over
a clock, a log, a store, a decay calculator, a mood evaluator and a notifier do
not converge on two operations each by coincidence. This is the specialist
pattern-matching a shape inferred from the examples in its own instructions and
then carving granularity to fit it — the ticket's thesis demonstrated more
sharply than the CMP-003 case it cites.

## The component-side rule: one provider, exactly

`component-specialist.md` already requires that *"Every capability you declare
must be providable by a component in your own output."* The granularity rule is
that existing requirement read one notch harder: not that **a** provider exists,
but that **exactly one provider suffices**.

This matters for adoption. The rule is not new machinery competing for the
specialist's attention; it is a sharpening of a constraint the file already
carries and the specialist already honours.

It yields one test applicable at the moment of writing: **name the single
component that could satisfy this capability entirely.**

| | Example | Verdict |
| --- | --- | --- |
| Too narrow — a mechanism | `"call the Stripe API"` | existing table row |
| **Right** | `"take card payments"` | one provider, whatever operation count it takes |
| **Right** | `"preserve the pet's state across restarts"` | one provider (the local store); two operations is fine |
| **Too broad — spans providers** | `"keep the pet alive while the app is closed"` | needs the clock *and* the decay engine *and* the store — **new row** |
| Too vague — a category | `"persistence"` | existing table row |

**The load-bearing distinction: an outcome is bad when it spans providers, not
when it needs several operations.** Without that line, the obvious reading of
"do not phrase capabilities as outcomes" would condemn "preserve the pet's state
across restarts" as badly phrased. With it, the band rules out the genuinely
unusable phrasings and leaves the legitimate ones alone.

Note that this settles only the *component-side* question. Whether the resulting
contract is later split into two interfaces is the interface specialist's call
under the ISP rule below, decided on consumer sets the component specialist
cannot see. A well-phrased capability can still become two interfaces; that is
the pipeline working, not a contradiction. IF-003 is exactly this case — see
"Known divergence" below.

The existing table's three bad rows are all *too specific* (mechanism) or *too
vague* (category). The band adds the missing failure mode on the other side.

## The interface-side rule: Interface Segregation

A third corollary joins the two already in `interface-specialist.md`:

> Different capabilities from the same provider are **one** interface when every
> consumer of one also consumes the others, and **separate** interfaces
> otherwise.

"Consumer" means a component listing the capability in its
`required_capabilities`, and the test is over capabilities, not operations — a
consumer is never expected to use every operation of a contract it depends on,
only to genuinely need the capability the contract satisfies.

Stated as the Interface Segregation Principle. These files earn their authority
by citing standards — ISO/IEC 25010, ISO/IEC/IEEE 42010, ATAM, INCOSE, EARS —
rather than asserting taste, and ISP is the specific principle this is. Naming
it gives the rule the same provenance as everything around it.

The worked example is CMP-003's real consumer table above.

## Why each rule lives where it does

The component specialist **cannot** apply the ISP test. It has no view of the
final interface shape or of which components will consume what — it runs first
precisely to break the authoring cycle. The interface specialist **can**, because
by then `component_set` names every consumer.

Each file gets the rule it is positioned to execute. Giving both files the same
principle would require the component specialist to predict something it
structurally cannot see, which produces guessing dressed as method.

## Scope

**In:**

- `agents/component-specialist.md` — one new table row plus a short rule
  paragraph in the existing "Declaring capabilities" section. No new section.
- `agents/interface-specialist.md` — a third corollary in the existing
  merge/split list, with the CMP-003 worked example.
- `docs/requirements/examples/tamagotchi/README.md` — a short subsection
  recording both divergences as artifacts of a pre-heuristic run.

**Out:**

- **No critic check.** The ticket's own read is that the primary fix is
  instructional, in the specialists themselves. A granularity criterion in
  `design-critic.md` adds a judgment call the critic can get wrong in both
  directions.
- **No regeneration of the example.** Tracked as STO-219, which is blocked on
  this ticket plus STO-216 and STO-208 so the examples are re-run once, after
  the last shape-changing change lands, rather than three times.
- **No operation-count rule**, despite the 11-of-12 finding. It goes into the
  README as evidence and into this spec's rationale, not into the instructions.
  A rule like "do not default to two operations" invites over-correction into
  artificial variety — the same failure wearing different clothes. The
  granularity band addresses the cause; the symptom does not need its own rule.

## Known divergence, deliberately not fixed

IF-003 (Durable Pet State Persistence) is one interface carrying `load` and
`commit`, consumed by CMP-007 and CMP-003. Under the ISP rule this design
introduces, it is arguably two interfaces — CMP-007 seeds, CMP-003 commits.

It stays as-is. The example's value is as an honest record of what the pipeline
produced, which is the same reason its seven open critic findings were left
standing. The divergence is recorded in the README and carried as acceptance
criteria on STO-219.

## Verification

No test suite covers agent Markdown, so verification is by inspection against
specific, checkable claims:

1. All thirteen files in `agents/` parse to single-key `description` frontmatter.
2. The capability hand-off vocabulary still agrees across
   `component-specialist.md`, `interface-specialist.md`, and
   `design-orchestrator.md` — the same cross-file check STO-99's plan used.
3. Both rules applied by hand to the tamagotchi example: the CMP-003 three-way
   split is reproduced by the ISP rule, and the IF-003 tension is documented
   rather than silently left.
4. Every capability phrasing in the new table rows is one a reader can classify
   without further context.
5. The 95-test suite still passes — no script changes are expected, so a
   regression here means something unintended was touched.
