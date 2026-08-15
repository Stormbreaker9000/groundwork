# M2 Design Content-Quality Linter — Design

**Ticket:** STO-208
**Date:** 2026-08-14
**Status:** approved

## Problem

M1 shipped two tiers of quality gate. M2 shipped only one.

- **Structural** (STO-97, then STO-197 for design) — schema, unique IDs, dangling
  traces. A hard gate: non-zero exit, the pipeline stops.
- **Advisory content** (STO-136) — vague qualifiers, compound requirements, EARS
  non-conformance, passive-nameless, implementation bias. Warns, always exits 0,
  guides prose quality without blocking.

Every M2 ticket to date — STO-197, STO-99, STO-100, STO-101, STO-102 — is
structural or generative. Nothing owns design *quality*. The tier does not
exist, and STO-197's own design defers to it repeatedly (its Part D.1), so the
gap is load-bearing on a spec that is already approved.

`agents/design-critic.md:260-264` also defers to it by name, telling the critic
not to sweep for "dependency cycles, orphan interfaces, and vague
`responsibility` prose" because "these belong to STO-208's content linter." That
deferral currently points at nothing.

## Evidence

Confirmed empirically against the shipped tamagotchi worked example on
`main` at `d17cd1d` (11 components, 12 interfaces, 0 ADRs).

**The example contains a dependency cycle that no tool in the pipeline
detects.**

```
CMP-003 Pet State Manager      --IF-006 Pet Lifecycle State-->  CMP-004
CMP-004 Pet Lifecycle Manager  --IF-005 Pet Stat Observation--> CMP-003
```

`CMP-003` consumes `IF-006`, provided by `CMP-004`. `CMP-004` consumes
`IF-005`, provided by `CMP-003`. The graph is well-formed at every level the
structural validator checks — both interfaces resolve, both providers exist,
no ID dangles — and `validate_design.py` and `validate_traceability.py` both
exit 0 over the set. The shape is the defect, and shape is precisely what the
structural tier cannot see.

The cycle is not an artifact of sloppy authoring; it is semantically real. The
stat manager reads lifecycle state before mutating a stat, and the lifecycle
manager observes stats to decide when to transition. Those are the same two
interfaces STO-216 reworked — `IF-006`'s body already admits "one consumer must
read lifecycle state *before* mutating a stat." The mutual dependency was
visible in prose to anyone reading both files, and invisible to every automated
check.

The other four proposed rules produce **no** findings over the same set: no
orphan interfaces, no vague `responsibility` prose, no hand-waved `error_modes`,
no `and`/`or`-joined action verbs. That is a useful negative result — it means
the example's remaining exposure is one warn-severity cycle rather than a wall
of noise, and it supports the test posture in D7.

The example carries **zero ADRs**: it was generated before STO-100 landed.
The ADR rules therefore have no worked-example coverage and must be driven
entirely by fixtures. Regenerating the example is STO-219, not this ticket.

## Decisions

### D1 — The linter runs at SKILL.md Step 4, not in the critic

STO-208's own description says this should land "so the architecture pipeline's
critic has a script-backed pass, the way the requirements critic does." That
premise is stale and is **not** built to.

STO-215 moved the structural gate off the critic, and
`agents/requirements-critic.md:60` now states plainly: "Do not run
`lint_requirements_content.py` here." The M1 content linter is invoked from
`skills/requirements/SKILL.md` Step 4, after the formatter's structural gate,
where the skill describes it as "the only script-backed lint run in the
pipeline."

The reason is not stylistic. The critic runs before anything is on disk — it
judges the in-memory draft set — so a script that reads files cannot run there.
This is the same reasoning that produced STO-215.

`lint_design_content.py` therefore runs from `skills/design/SKILL.md` Step 4,
after the formatter's two hard gates (`validate_design.py`, then
`validate_traceability.py`) have both exited 0. The critic continues to apply
these checks by inspection at gate time and continues not to run the script.
`agents/design-critic.md`'s existing deferral text stays as written; it gains
only a pointer to the now-real script.

### D2 — Advisory, exactly like M1

Exit 0 regardless of findings. `--strict` promotes any `error`-severity finding
to exit 1. `--json` emits machine-readable findings. `--quiet` prints one line
per finding. Same four flags, same semantics, same `Finding` shape as
`lint_requirements_content.py`.

No rule in this ticket emits `error` severity. `--strict` is wired for symmetry
with M1 and for future rules, and its effect today is a no-op. This is stated
rather than left to be discovered.

The tool never rewrites a file. Findings route back through the critique loop to
the owning specialist, the same routing SKILL.md Step 4 already documents for
M1 — not hand-edits into formatter output.

### D3 — Shared machinery is extracted to `lib/lint_core.py`

This mirrors STO-197, which extracted `lib/artifact_core.py` when the design
stage needed the requirements validators' parsing and reporting machinery. The
same situation now recurs one tier down.

Moves to `lib/lint_core.py`:

| Symbol | Why it is shared |
|---|---|
| `Finding` | The finding record is the output contract of both linters |
| `_text`, `_sentences` | Frontmatter-to-prose coercion; no stage knowledge |
| `_print_report` | The human report format is one format |
| `main()` scaffold | Identical argparse surface across both tools |
| `VAGUE_TERMS` | The word list most in need of staying in sync |
| `ACTION_VERBS` | Consumed by M1's `compound` and M2's `god-component` |
| `body_section()` | New; see D5 |

Stays per-stage:

- The `CHECKS` / `SET_CHECKS` registries.
- The rule functions themselves.
- Stage-only vocabularies (`TECH_TERMS`, `EARS_LEADS`, the glossary regexes).
- `lint_dir`, because discovery differs: M1 walks `vr.discover_files`, M2 walks
  `vd.discover_files` with its own skip sets.

The extraction is behavior-preserving. M1's 240-line suite is the regression
net, the same posture `artifact_core.py`'s extraction took.

`main()` is parameterized by the pieces that differ — the default directory
(`.sdlc/requirements` vs `.sdlc/design`), the report noun, and the `lint_dir`
callable — following `artifact_core.print_report`'s existing `noun` parameter
precedent.

### D4 — `Finding.req_id` is renamed to `Finding.artifact_id`

A shared record cannot keep a requirements-flavoured field name. The rename is
not a new convention: `validate_traceability.py`'s own `Finding` already
declares `artifact_id` (STO-102), and `artifact_core.ArtifactFile` exposes
`artifact_id` for the same reason (STO-197). M1's linter is the last holdout,
and the extraction is what forces the question. `req_id` also survives in
`validate_traceability.py` on a *different* record — its `Requirement` — where
it is correct and stays.

This changes M1's `--json` key from `req_id` to `artifact_id`. A grep across the
repo confirms nothing reads it: no agent, skill, script, or test outside
`lint_requirements_content.py` and its own suite names the field, and the M1
skill invokes the linter without `--json`. The blast radius is the M1 test
suite and the M1 script README.

It is nonetheless a shipped `--json` contract changing, so it is recorded here
as a deliberate call rather than absorbed silently into a refactor. The
alternative — keeping `req_id` in a design linter — was rejected as the kind of
inherited misnomer that costs more to live with than to fix now, while exactly
one consumer exists.

### D5 — ADR rules read body prose, via a generic section extractor

ADR frontmatter carries only `decision_status`, `considered_options`, and
`chosen_option`. Decision drivers, considered-options detail, and consequences
all live in the **body**, under the five MADR headings `validate_design.py`
gates for presence.

So the design linter's per-artifact checks take `(artifact_id, fm, body)` where
M1's take `(req_id, fm)`. The registries are per-stage, so M1's rule signatures
are untouched.

`lint_core` gains `body_section(text, heading) -> str`, returning the raw text
under a heading up to the next heading of the same or higher level.

`validate_traceability.py` already has a near-equivalent
`decision_drivers_section(path)`. It is deliberately **not** reused. That
function is hard-coded to one heading and lives inside a hard-gate validator;
importing it would make the advisory linter depend on the tool it is meant to
sit beside, to save roughly fifteen lines. The near-duplication is recorded
here as known and accepted. Collapsing the two is a legitimate follow-up, and
is not done inside a ticket whose whole point is that it never blocks the
pipeline.

### D6 — The rule set

Eight rules — two on components, two on interfaces, three on ADRs, one
set-level. Severity is `warn` unless noted.

**Components**

| Rule | Sev | Field | Fires on |
|---|---|---|---|
| `vague-responsibility` | warn / info | `responsibility` | A `VAGUE_TERMS` hit. Demoted to `info` when the sentence contains a digit, mirroring M1's `vague-qualifier` — a quantified "fast (under 200ms)" is not the failure being hunted |
| `god-component` | warn | `responsibility` | `and`/`or` joining two `ACTION_VERBS` |

`god-component` ports M1's `compound` heuristic. M1 anchors its scan on the
`shall` keyword and searches the predicate after it; a `responsibility` has no
such keyword, so the scan runs over the whole field. The verb-anchoring is what
keeps it quiet: "Persists pet state **and sends** lifecycle notifications"
fires, "Persists pet state durably **and atomically**" does not. The
alternative — flagging every coordinating conjunction — was rejected as the
noise that trains a reader to ignore a rule, the same argument STO-102's spec
(D2/D4) used to make `uncovered-fr` a warning.

**Interfaces**

| Rule | Sev | Field | Fires on |
|---|---|---|---|
| `orphan-interface` | warn | `id` | An `IF-` that appears in no component's `depends_on`. The `glossary-unused` analogue: defined-but-unused is a warning, not a gate |
| `error-modes-handwaved` | warn | `error_modes` | An entry whose content is an adverb of intent — "handled gracefully", "appropriately", "properly", "as needed", "as appropriate" |

There is no `error-modes-empty` rule: the schema already sets `minItems: 1` on
`error_modes`, so an empty list fails the structural gate before the linter ever
runs.

**ADRs**

| Rule | Sev | Field | Fires on |
|---|---|---|---|
| `adr-consequences-one-sided` | warn | `consequences` | `### Consequences` carries at least one Good bullet and no Bad bullet |
| `adr-vague-driver` | warn / info | `decision_drivers` | A `VAGUE_TERMS` hit in the `## Decision Drivers` section. Demoted to `info` when the driver line contains a digit, mirroring `vague-responsibility` — a quantified driver is not the failure being hunted |
| `adr-option-unexamined` | info | `considered_options` | An option named in frontmatter that never appears in the `## Considered Options` body |

`adr-consequences-one-sided` encodes the claim that every real decision costs
something: a consequences section that is all upside records a decision that was
not weighed. It is skipped for `decision_status: proposed` and for the
formatter's honest placeholder (`- None — the decision is pending.`), both of
which are correct output for a decision that has not been taken.

`adr-vague-driver` targets the ADR's link to the NFRs. "Must be scalable" as a
decision driver is the vague-qualifier failure at its most load-bearing, because
the driver is what the decision claims to answer.

`adr-option-unexamined` catches options added to clear the schema's
`minItems: 2` without ever being weighed. It is `info`, not `warn`: an option
can be legitimately named in frontmatter and discussed under `## Decision
Outcome` rather than `## Considered Options`, so the rule reports a smell it
cannot prove. Single-option ADRs are **not** a lint concern — `minItems: 2` is
already a structural gate for accepted decisions.

**Set-level**

| Rule | Sev | Fires on |
|---|---|---|
| `dependency-cycle` | warn | A cycle in the `CMP.depends_on → IF.provider → CMP` graph |

The graph has one edge type: component *A* depends on component *B* when *A*
lists an interface whose `provider` is *B*. Cycles are reported as a full path
(`CMP-003 → IF-006 → CMP-004 → IF-005 → CMP-003`), naming the interfaces as
well as the components, because the interfaces are where the fix is made.

Self-loops — a component consuming an interface it provides itself — are
included, and are reported as a one-component path.

Each distinct cycle is reported **once**. A naive DFS over the tamagotchi set
yields the same two-component cycle six times, once per entry path; the rule
canonicalizes each cycle by rotating it to start at its lowest-sorting component
ID and de-duplicates before reporting. Without this, the example's single defect
would produce six identical findings.

`dependency-cycle` is a `SET_CHECK`: it is not decidable from one file, which
is the same reason `glossary-unused` needed the `SET_CHECKS` registry in M1.

### D7 — The worked example is asserted free of `error` findings, not free of findings

The tamagotchi example gets a regression test asserting **no `error`-severity
findings**, not zero findings.

Asserting clean would be wrong on two counts. The tool always exits 0, so
"clean" is not a state it is built to guarantee; and STO-219 explicitly wants
the example's remaining deviations to be *chosen* rather than absent — "an
example whose critic found nothing teaches nothing."

Since no rule in this ticket emits `error` severity (D2), that assertion passes
trivially today. It is written anyway, as the pin that catches a future rule
promoted to `error` silently invalidating the shipped example — the same class
of silently-unchecked-data failure STO-102 fixed in `artifact_core.py` and
STO-216 fixed for the structural gate over this same example.

The `dependency-cycle` finding on `CMP-003`/`CMP-004` is recorded in
`docs/requirements/examples/tamagotchi/README.md` as a named, explained
deviation, joining the `IF-003` segregation note and the operation-count
uniformity note already there. It is **not** fixed here: breaking the cycle
means re-deciding how the stat and lifecycle managers talk to each other, which
is a design change to a worked example, and worked-example regeneration is
STO-219. Recording it is what makes it STO-219's input rather than a
rediscovery.

## Files changed

**New**

- `lib/lint_core.py` — shared linter core (D3).
- `skills/design/scripts/lint_design_content.py` — the linter.
- `skills/design/scripts/tests/test_lint_design_content.py` — its suite.
- `skills/design/scripts/tests/fixtures/lint/` — dirty fixtures, one per rule.

**Modified**

- `skills/requirements/scripts/lint_requirements_content.py` — imports from
  `lint_core`; keeps only its own registries, rules, and vocabularies.
- `skills/requirements/scripts/tests/test_lint_content.py` — `artifact_id`
  rename (D4).
- `skills/requirements/scripts/README.md` — `artifact_id` rename in the
  documented `--json` shape.
- `skills/design/scripts/README.md` — new rule table for the linter.
- `skills/design/SKILL.md` — Step 4 gains the linter invocation and its routing
  rule, mirroring the M1 skill's wording.
- `agents/design-critic.md` — the existing STO-208 deferral gains a pointer to
  the real script; the deferral itself is unchanged.
- `docs/requirements/examples/tamagotchi/README.md` — the cycle recorded as a
  named deviation (D7).

## Testing

- **Per-rule fixtures.** Each of the eight rules gets a fixture that fires it and
  a near-miss fixture that must stay clean. The near-misses are the point:
  `god-component` against "durably and atomically", `adr-consequences-one-sided`
  against a `proposed` ADR carrying the placeholder, `orphan-interface` against
  an interface consumed by exactly one component.
- **Cycle de-duplication.** A fixture with one two-component cycle asserts
  exactly one finding, and a fixture with two independent cycles asserts two.
  This is the assertion that would have caught the six-fold duplication.
- **M1 regression.** The existing 240-line suite must stay green through the
  `lint_core` extraction, with only the `artifact_id` rename touched. Any other
  M1 test needing an edit means the extraction was not behavior-preserving.
- **Exit codes.** Exit 0 with findings present; exit 0 under `--strict` with no
  error-severity findings; exit 2 on a missing directory.
- **Worked example.** No `error`-severity findings over
  `docs/requirements/examples/tamagotchi/design` (D7), and the
  `dependency-cycle` finding is asserted present — the example is the only real
  input this rule has.
- **Fallback path.** The linter runs without `pyyaml` installed, via
  `artifact_core`'s stdlib parser. Findings may differ in fidelity; the tool
  must not crash.

## Out of scope

- **Orphan design artifacts** (`traces_from: []`) — STO-226 owns this, in
  `validate_traceability.py`. That ticket explicitly assigns orphan *interface*
  detection, a design-internal `CMP.depends_on → IF.provider` edge, to this one.
  The boundary is already written down on both sides.
- **Structural validation** — STO-197 / `validate_design.py`.
- **Cross-artifact design ↔ requirements checks** — STO-102 /
  `validate_traceability.py`.
- **Regenerating the worked examples** — STO-219. This ticket records a finding
  in the example README; it changes no example artifact.
- **Collapsing `decision_drivers_section` into `body_section`** — a follow-up
  touching a hard-gate validator (D5).
- **Promoting any rule to a hard gate.** The tier is advisory by definition. A
  rule that should block belongs in `validate_design.py`.

## Sequencing note

STO-208 blocks STO-219 and STO-227. It does not block STO-101 (C4 diagrams),
and the two do not touch: diagrams live under `.sdlc/design/diagrams/`, which
`validate_design.py`'s `SKIP_DIRNAMES` already prunes and which this linter
inherits by walking the same discovery function.

The `dependency-cycle` finding recorded in D7 becomes a direct input to
STO-219: a regenerated tamagotchi set should either break the CMP-003/CMP-004
cycle or state why it keeps it.
