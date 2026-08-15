# M2 Mixed-Mode Interaction — Design

**Ticket:** STO-216
**Date:** 2026-08-11
**Status:** approved, ready for implementation planning

## Problem

`interaction` is declared once per contract, as a two-value enum on the
interface branch of `design.schema.json` (line 223):

```json
"interaction": {
  "type": "string",
  "description": "Interaction style.",
  "enum": ["synchronous", "asynchronous"]
}
```

Interaction is not a property of a contract. It is a property of an operation.
`flush` blocks and `record` does not, and no fact about the contract they are
bundled into changes either one. Where a contract's operations disagree, the
field must misdescribe half of them — and the schema offers no way to say so.

`agents/design-critic.md:68` then makes the mismatch a gate failure:

> **Interaction matches the described wait.** If the body says the consumer
> blocks on the result, `interaction` must be `synchronous`, and vice versa.
> A mismatch between the prose and the field is a `revise` — one of the two is
> wrong and you cannot silently pick which.

For a contract whose operations genuinely differ, that rule is unsatisfiable.
Both branches of "one of the two is wrong" are false: the prose is right, the
field is right about the operation it happens to describe, and no rewording
reconciles them. The critic is correct to flag it and powerless to let it pass.

## Evidence

The shipped tamagotchi worked example produced four such interfaces on a real
run, of which the critic caught three. Those three are recorded as standing
findings that `docs/requirements/examples/tamagotchi/README.md:136` explains
cannot be cleared: "the schema cannot express a mixed-mode contract, so no
wording of these artifacts would satisfy the check."

| Interface | Operations | Consumers | Declared | Flagged |
| --- | --- | --- | --- | --- |
| IF-002 Diagnostic Log Recording | `record` (fire-and-forget), `flush` (blocking) | CMP-001, CMP-003, CMP-004, CMP-007 | `asynchronous` | yes |
| IF-012 Desktop Notification Delivery | `show_reminder` (async), `delivery_available` (sync query) | CMP-008 | `asynchronous` | yes |
| IF-006 Pet Lifecycle State | `current_lifecycle_state` (blocking read), `subscribe_to_transitions` (push) | CMP-003, CMP-005, CMP-006 | `synchronous` | yes |
| IF-005 Pet Stat Observation | `current_stats` (snapshot read), `subscribe_to_stat_changes` (push) | CMP-004, CMP-005, CMP-006, CMP-008 | `asynchronous` | **no** |

The fourth row is the sharpest evidence in the set. IF-005 is structurally
identical to IF-006 — a blocking read and a subscription on one contract — and
the critic passed it. Its body argues the dominant mode rather than the mixture:
"The snapshot read exists for recovery and for the first read after seeding, not
as the normal path." That is a defensible sentence, and it is exactly the escape
a single contract-level field leaves open. The IF-012 finding calls itself the
"Third instance of the same shape in this set (IF-002, IF-006, IF-012)," so the
miss was not noticed at the time either.

The contract-level field therefore does not merely force an artifact to
misdescribe itself. It gives the author a way to argue past the gate, and the
critic no operand precise enough to refuse. Under D1 the question stops being
"what is this contract's dominant mode" and becomes "does `current_stats`
block," which has one answer.

The cost is recorded in three separate places, which is itself evidence that
the pipeline noticed the defect and had nowhere to put the fix. IF-006's own
body:

> Both are on the contract, and the interaction is recorded as synchronous
> because the correctness-critical use is the blocking one — a missed push
> shows a stale mood for a moment, a missed gate revives a dead pet.

`design/drivers.md:21` carries it as a tradeoff — "Half the contract is
misdescribed by its own declared interaction, and the two push consumers get a
notification stream the field denies" — and `critique-report.yaml:155,235`
carries it as findings against IF-002 and IF-006.

The four cases are not the same defect, and the difference decides the design.
IF-002, IF-012 and IF-005 have **coincident consumer sets**: every consumer of
the contract uses every operation on it. Splitting them would force CMP-008 to
depend on two notification interfaces it always uses together, would sever
`record` from the `flush` that exists to bound it, and would separate IF-005's
seeding read from the subscription the same four components hold — its body
places the read in those consumers' first-read phase, not in a different
consumer. Those are genuine mixed-mode contracts.

IF-006's consumer sets **diverge** — CMP-003 takes only the blocking read,
CMP-005 and CMP-006 only the push — which is the same nested-consumer-set
argument under which `docs/requirements/examples/tamagotchi/README.md` already
records IF-003 as a contract that should have been two.

## Decisions

### D1 — `interaction` moves onto the operation; `mixed` is never a stored value

`operations.items` gains a required `interaction` with the existing two-value
enum. The contract-level field is removed from the interface branch's
`required` list and from its `properties`.

The alternative considered was widening the contract-level enum to
`synchronous | asynchronous | mixed`, with per-operation detail required only
when the contract says `mixed`. It was rejected on two grounds.

First, it stores the same fact twice. The schema's own description states the
principle it would violate: "The dependency edge lives once as
`CMP.depends_on -> IF.provider` (there is no `consumers` field)." A
contract-level summary of its operations' interaction styles is a
denormalization, and denormalizations need a derivation rule and a check that
nobody has broken it. Under D1 there is nothing to keep consistent.

Second, `mixed` alone does not repair the critic rule. It relabels the
imprecision rather than resolving it: there is still no per-operation field for
the critic to check the prose against, so the three findings would clear by
fiat rather than by becoming true. That is worse than leaving them open,
because it converts a visible limitation into an invisible one.

A mixed-mode contract therefore needs no name in the data. It is an interface
whose operations disagree, and any consumer that wants the word can compute it.

### D2 — The contract-level field is retired, not deprecated

There is no transition period in which both shapes validate. `interaction` on
an interface's top level becomes an error.

The schema enforces this without a new rule: `unevaluatedProperties: false`
(line 343) rejects any property that no branch evaluated, and once `interaction`
leaves the interface branch's `properties`, a stale one is unevaluated. The
error text will be the generic unexpected-property line described in the
diagnostic note at line 342 — which is why D3 adds a named one.

Retirement is affordable because the design stage has exactly one emitter. Every
interface artifact in existence was written by `design-formatter.md` from a
`draft_interfaces` hand-off, and both are updated here. There is no corpus of
hand-authored interfaces to migrate, and the only shipped data is the worked
examples, handled in D6.

### D3 — The fallback validator gains its first nested check and a named retired-field error

`validate_design.py` carries a reduced mode for when `jsonschema` is absent
(line 135: "The JSON Schema is the single source of truth when jsonschema is
available"). Three edits keep it at parity:

- `_FALLBACK_REQUIRED_BY_TYPE["interface"]` (line 144) drops `"interaction"`.
- `_FALLBACK_ENUMS` (line 152) drops its top-level `"interaction"` entry. That
  dict is a flat scan of top-level keys and cannot reach into a list of
  mappings.
- A new check walks `operations` on interface artifacts, requiring
  `interaction` on each entry and testing its value against the enum. This is
  the first nested check on this path; the `traces_to` and `traces_from` type
  guards at lines 200–206 are the shape to follow.

Beyond parity, the fallback also gains an explicit check for a top-level
`interaction` on an interface, erroring with a message that names the move
rather than describing an unexpected key. Without it, the retirement in D2 is
enforced only when `jsonschema` is installed, and a pre-STO-216 artifact would
pass the reduced path carrying a field nothing reads. That is the exact failure
class STO-102 fixed in `artifact_core.py`: a validator that silently loses a
field in fallback mode reports success over data it never checked. Reduced mode
is already announced to the user, so the check need not be perfect — it needs
to not be silent.

### D4 — The consumer-set guard is instructional, in the interface specialist

Mixed interaction is legal only when the contract's operations share a consumer
set. Divergent consumer sets are a split, not a mixed contract. That rule lives
in `agents/interface-specialist.md`'s `interaction` section (line 228), as a
corollary to the merge/split rules the file already carries — not as a critic
check.

This follows the precedent STO-216's immediate predecessor set. The capability
granularity spec (`2026-08-01-m2-capability-granularity-design.md`) declined a
critic check for the analogous rule: "the primary fix is instructional, in the
specialists themselves. A granularity criterion in `design-critic.md` adds a
judgment call the critic can get wrong in both directions." The same reasoning
applies unchanged.

It is also the only place the rule *can* live. The guard asks whether every
consumer uses every operation, and no stage holds per-operation consumption
data. `depends_on` and the transient `consumed_by` both record consumption per
interface. The specialist is the only actor that knows which consumer wanted
which operation, because it is the actor that read the capabilities and decided
what to put on the contract. A downstream check would be guessing.

Because the rule is taught rather than enforced, it is taught by example: the
worked example in `agents/interface-specialist.md` (line 378) is a three-
operation card-payment contract, all synchronous, and gains a second, shorter
example of a legitimately mixed contract with its consumer-set justification
stated. A rule with no example in a file that teaches by example is a rule that
will be missed.

### D5 — The critic's rule becomes per-operation

`agents/design-critic.md:68` is rewritten to check each operation against the
prose describing it, rather than the contract against the body as a whole. The
question becomes answerable: does this operation's body text describe a
consumer waiting, and does this operation's `interaction` agree?

This is a strengthening, not a relaxation. The old rule could only be applied
to contracts whose operations happened to agree; on the rest it produced a
finding no one could act on. The new one applies to every operation on every
interface, including the ones that were previously unreachable behind a
contract-level summary.

IF-005 is the case that proves the difference. Under the old rule the critic had
to weigh a whole-contract claim against a whole body, and a body arguing the
dominant mode beat it. Under the new one there is no dominant mode to argue:
`current_stats` either blocks or it does not, and its own summary says it
returns a snapshot.

### D6 — The worked examples are updated mechanically here; regeneration stays STO-219

All 12 tamagotchi interface artifacts move `interaction` onto their operations,
preserving the existing wording. Where an interface is uniform, every operation
takes the value the contract carried. Where it is mixed — IF-002, IF-006,
IF-012 — each operation takes the value its own body prose already describes.

Where a mixed contract's body already argues one mode for the whole contract —
IF-005's "Asynchronous. …", IF-006's "Synchronous, and this is the closest call
in the set" — the opening word is corrected to describe the mixture, and the
argument the body makes for the dominant mode is kept. Those paragraphs are the
reasoning that earned the artifact its `confidence` value; only the claim that a
single mode covers the contract is wrong.

This is a mechanical frontmatter edit, not a regeneration, and it does not
encroach on STO-219. STO-100 and STO-217 both declined to touch
`docs/requirements/examples/` because neither invalidated the data; this ticket
does invalidate it, and a committed example that fails its own validator is not
a state to leave main in. STO-102 set the precedent, editing four example
requirement files when its own fix made them invalid.

**The gate this relies on does not yet exist.** The only regression test over
the worked example is `test_shipped_tamagotchi_example_is_clean`
(`test_validate_traceability.py:452`), and it invokes `validate_traceability.py`
— a tool that by its own Global Constraints never schema-validates. No test runs
`validate_design.py` over `docs/requirements/examples/tamagotchi/design/`, so
the 12 interface artifacts have no structural gate in CI and would go stale
under this change without anything turning red. That test is added here, in the
task that edits the data, because it is what makes the edit verifiable.

Two of the three standing findings genuinely clear. IF-002 and IF-012 can now
state what they always were, as can IF-005, which was never flagged. IF-006 does
not clear: it converts from a schema limitation into a segregation divergence,
joining IF-003 in the README's granularity section. The README's current text at
line 136 — three interfaces, unsatisfiable check — is rewritten to say what is
now true, including that a fourth instance went uncaught. The example's value is
as an honest record of what the pipeline produced, and that is served by
restating the findings correctly, not by removing evidence that the pipeline
once had nowhere to put them.

### D7 — Generated history is not edited

`design/critique-report.yaml` and `design/drivers.md` are output of a real
pipeline run made under the old schema. Their IF-006 tradeoff and their IF-002
and IF-006 findings were accurate when produced. They are left untouched.

Editing them would falsify the record — a critique report that shows the critic
raising a finding the schema of its own era could not have expressed is not a
better artifact, it is a fabricated one. The README is the correct place to note
that the schema has since changed, because the README is the document that
speaks in the present tense about a set that does not.

## Files changed

| File | Change |
| --- | --- |
| `skills/design/schema/design.schema.json` | Interface branch: `interaction` moves into `operations.items`, out of the branch's `required` and `properties`. Line 5 description and line 176 `$comment` both name it as a contract field |
| `skills/design/scripts/validate_design.py` | D3 — three parity edits plus the retired-field check |
| `skills/design/scripts/tests/test_validate_design.py` | `_base_interface` (line 270) and the exact-key-set assertion (line 366) both assert the old shape; gains the new schema/fallback cases and the missing tamagotchi structural regression |
| `skills/design/scripts/tests/fixtures/valid/interfaces/IF-001-payment-api.md` | Move `interaction` onto operations |
| `skills/design/scripts/tests/fixtures/invalid/dangling_provider/interfaces/IF-001-dangling-provider.md` | Same |
| `agents/interface-specialist.md` | `interaction` section (228) gains the D4 guard; output template (254); schema-shape paragraph (277); worked example (388) plus the D4 mixed example |
| `agents/design-orchestrator.md` | Hand-off template (261) |
| `agents/design-formatter.md` | Frontmatter template (226); branch-field rule (251) |
| `agents/design-critic.md` | Rule at 68 becomes per-operation (D5) |
| `skills/design/SKILL.md` | Summary line (251) renders `mixed` when a contract's operations disagree |
| `docs/requirements/examples/tamagotchi/design/interfaces/*.md` | 12 files, mechanical (D6) |
| `docs/requirements/examples/tamagotchi/README.md` | Line 136 finding restated; IF-006 joins the granularity section (D6) |

Not touched: `index.yaml` does not carry `interaction`; `validate_traceability.py`
does not read it; `requirement.schema.json` is unaffected; the gdpr example has
a `requirements/` tree only and no design artifacts.

## Testing

- **Schema, jsonschema path.** An interface with per-operation `interaction`
  validates. One with a contract-level `interaction` fails. One with an
  operation missing `interaction` fails. One with an operation carrying an
  out-of-enum value fails.
- **Schema, fallback path.** The same four cases, with `jsonschema` unavailable,
  asserting the retired-field message names the move rather than reporting an
  unexpected key.
- **Mixed contract.** An interface whose two operations carry different values
  validates on both paths — the case that does not exist today.
- **Regression.** A new `test_shipped_tamagotchi_example_passes_structural_gate`
  in `test_validate_design.py` runs `validate_design.py` over the worked
  example's `design/` directory and asserts exit 0. This is the gate D6 needs
  and the repo does not have; the existing traceability regression continues to
  pass unchanged, since that tool does not read `interaction`.

Agent Markdown has no test suite, so the instruction changes are verified by
inspection against the checkable claims in "Files changed": no template in any
of the four agent files emits a contract-level `interaction`, and every one
emits it per operation.

## Out of scope

- **Splitting IF-006.** D6 records it as a divergence; acting on it is a
  regeneration, which is STO-219.
- **Regenerating the worked examples** (STO-219). This ticket edits the existing
  artifacts in place and does not re-run the pipeline.
- **A critic check for the consumer-set guard** (D4). Instructional by
  precedent.
- **Per-operation error modes.** `error_modes` stays contract-level. The same
  "it is a property of the operation" argument could be made, and no shipped
  evidence supports making it — no artifact and no critic finding has yet been
  unable to say what it meant. Widening this ticket to every field that might
  eventually want splitting is how it stops landing.
- **C4 diagrams** (STO-101). `diagrams/` stays in `SKIP_DIRNAMES`.

## Sequencing note

`2026-08-03-m2-adr-generation-design.md:365` flagged this collision: STO-100 and
STO-216 both edit the interface branch's neighbourhood in
`design.schema.json`, and "whichever lands second rebases." STO-100 landed in
PR #13, so this ticket is the one that rebases. The ADR branch it added sits
after the interface branch and is not otherwise disturbed.

STO-219 is blocked on this ticket, STO-217 (landed), and STO-208. This is the
second of its three blockers to land.
