# M2 Cross-Artifact Traceability Validation — Design

**Ticket:** STO-102
**Date:** 2026-08-07
**Status:** approved, ready for implementation planning

## Problem

Every trace between the requirements stage and the design stage is currently
unchecked. Both validators know this and both say so in their own source:

- `validate_design.py` matches `traces_from` against `REQUIREMENT_ID_RE` and
  states that whether those IDs exist "is the cross-artifact validator's job
  (STO-102), not this one." A component may cite `FR-042` in a project that
  has no `FR-042` and pass the structural gate.
- `validate_requirements.py`'s `_collect_trace_targets` deliberately excludes
  every `traces_to` sub-list, on the grounds that "Design<->requirement
  resolution is M2's job." A requirement may point at a design artifact that
  does not exist and pass its gate.
- `agents/design-critic.md` reserves two checks for this ticket in its *Scope
  boundaries* section — `traces_from` resolution, and full FR coverage — and
  instructs the critic not to make them, so that the tool which owns the
  determination is the only one that makes it.

The result is that a design set can be internally valid, individually valid,
and completely disconnected from the requirements it claims to satisfy. The
`CMP.depends_on → IF.provider` edge is resolved; the `CMP.traces_from →
FR-###` edge is not. Only the edge that stays inside one stage is checked.

Nothing else will close this. The two structural validators each see one
directory by design, and the critic runs before any file exists.

## Evidence

Dry-running the proposed rules against the shipped tamagotchi worked example
(22 requirements, 23 design artifacts) shows the gap is real but the existing
data is mostly sound:

| Rule | Result on tamagotchi |
| --- | --- |
| Design `traces_from` resolves | clean — 0 dangling |
| Every FR covered by a component | clean — all 10 FRs covered |
| Requirement `traces_to.design` resolves | **4 violations, across both examples** |

The third row is a genuine defect that shipped. Four requirement files put
*requirement* IDs into a slot the schema documents as design artifacts:

```
tamagotchi  CON-001  traces_to.design: [NFR-002]
tamagotchi  CON-002  traces_to.design: [NFR-005, FR-001]
tamagotchi  CON-003  traces_to.design: [NFR-006]
gdpr        CON-001  traces_to.design: [FR-002]
```

The source is not the data — it is the instruction that produced it.
`agents/constraint-specialist.md` tells the specialist that a constraint
"bounds the requirements whose design space it limits — list those IDs under
`traces_to.design`." That contradicts `requirement.schema.json`, whose
`traces_to` is described as "downstream traceability mapping to design, tests,
and code artifacts," and it contradicts the bullet immediately below it, which
routes the analogous business-rule edge onto the requirement's own
`traces_from` ("the FRs list the rule in their `traces_from`").

The shipped data confirms which bullet is right, twice. `FR-008` carries
`traces_from: [BR-001]` and validates cleanly. And in the gdpr example the
constraint edge is *already* recorded correctly — `FR-002` carries
`traces_from: [BR-001, BR-002, CON-001]`, making its `traces_to.design:
[FR-002]` a redundant second copy of an edge that already lives in the right
place. The constraint bullet is the outlier.

The bounded requirements record the constraint nowhere else, so this is lost
information rather than duplicated information:

```
NFR-002  traces_from: []          ← bounded by CON-001
NFR-005  traces_from: [FR-001]    ← bounded by CON-002
NFR-006  traces_from: []          ← bounded by CON-003
FR-001   traces_from: []          ← bounded by CON-002
```

## Decisions

### D1 — Three checks; the diagram check waits for STO-101

The ticket names four checks. Three are implementable now. The fourth —
"diagram components must match component spec files" — has nothing to read:
`diagrams/` is in `validate_design.py`'s `SKIP_DIRNAMES`, and STO-101 owns the
format. Implementing it here would mean inventing that format ahead of the
ticket that owns it, and forcing STO-101 to conform to a shape chosen by a
validator rather than the other way round. It is deferred to STO-101.

### D2 — Resolution errors block; coverage warns

A design artifact citing `FR-042` when no `FR-042` exists is a factual error
with exactly one correct fix. It is an error and it exits non-zero.

An FR with no component addressing it is not necessarily wrong. It may be
deliberately deferred, out of the current increment, or covered by something
the architecture chose not to model as a component. It is a warning: reported,
counted, non-blocking. `--strict` promotes warnings to blocking for CI, the
same escape hatch `lint_requirements_content.py` already offers.

This is the first tool in the repo with two severities. That is why it is a
new script rather than a flag on an existing one — see D7.

### D3 — The requirement→design edge lives once, on `design.traces_from`

The design artifact's `traces_from` is the single source of truth for this
edge. This is the rule the repo already applies twice: the component→interface
edge lives once as `CMP.depends_on → IF.provider` (there is no `consumers`
field), and the ADR→artifact edge lives once on `CMP/IF.traces_to.adr`.

Consequences:

- A non-empty `traces_to.design` on a requirement must resolve to a real
  design ID. Garbage in that slot is an error.
- An empty `traces_to.design` is never a finding.
- Asymmetry is never a finding. A requirement whose `traces_to.design` omits a
  component that traces to it is correct, not incomplete.
- Nothing writes the reverse direction. Deriving a full bidirectional matrix
  is STO-105's traceability graph, which reads both directions rather than
  storing both.

The alternative — enforcing symmetry — would fail every existing requirement
set on day one, since no agent writes `traces_to.design` today. The other
alternative — having this tool back-fill it — would make the M2 design stage a
writer into `.sdlc/requirements/`, breaking the one-writer discipline STO-99
and STO-215 established, and turn a validator into a mutator.

### D4 — Coverage means FRs, addressed by components

Every functional requirement must appear in at least one **component's**
`traces_from`. Interfaces and ADRs do not count: an FR is behaviour, and
behaviour is owned by a component. An FR cited only by an interface still
warns.

Requirements with `priority: wont` or `status: obsolete` are excluded from the
sweep entirely — not warned about, not counted. A `wont` requirement having no
component is the correct outcome, and warning about it would train the reader
to ignore the rule.

Scoping coverage to FRs keeps a clean split with `agents/design-critic.md`,
which already sweeps ASR coverage — largely the NFR subset — in its ATAM-lite
Phase 2. Sweeping all requirement types here would duplicate exactly the
determination the critic's *Scope boundaries* section exists to prevent
duplicating.

### D5 — ADR decision drivers: body IDs resolve, and should agree with frontmatter

`agents/adr-generator.md` derives `body.decision_drivers` as "the
`traces_from` IDs", and the formatter renders it under `## Decision Drivers`.
So the body list and the frontmatter list are the same list, written twice.

Two rules follow:

- A requirement ID named under `## Decision Drivers` that does not resolve is
  an **error**.
- One that resolves but is absent from the ADR's frontmatter `traces_from` is
  a **warning** — the two copies have drifted.

The check accepts any requirement type, not NFR only. The ticket says "real
NFR IDs", but `agents/adr-generator.md`'s own worked example emits
`decision_drivers: [NFR-002, CON-001]`. An NFR-only rule would flag a
conforming ADR.

The warning is deliberately one-directional. An ID present in frontmatter but
missing from the body is a rendering gap the formatter owns, not a
traceability defect: the body is the human-editable surface and the
frontmatter is machine-derived. Flagging both directions would double the
warning count for one underlying drift.

### D6 — `agents/constraint-specialist.md` is corrected here, with its data

The Evidence section's defect is upstream of this ticket, and shipping the
validator without fixing it would land a gate that fails the repo's own worked
examples on day one — the same shape STO-215 fixed when it moved an
unreachable gate.

The constraint→requirement edge moves to where the business-rule edge already
lives: the **bounded requirement's** `traces_from`. This needs no schema
change, is already validated by `validate_requirements.py`'s existing dangling
-reference check, and matches D3's edge-lives-once rule.

Tiers do not invert under this move. `CON-003` is `business` and `NFR-006` is
`solution`. The same-tier links (`CON-001` solution → `NFR-002` solution)
match the existing shipped precedent `NFR-005 traces_from: [FR-001]`, both
`solution`. `validate_requirements.py` does not enforce tier ordering.

The sibling business-rule bullet is corrected in the same pass: it currently
routes FR IDs into `traces_to.tests`/`traces_to.code`, which is the same class
of misuse and is not caught by any rule here.

### D7 — A new sibling script, not a flag on `validate_design.py`

`skills/design/scripts/validate_traceability.py` sits alongside
`validate_design.py` and imports it, exactly as
`lint_requirements_content.py` sits alongside and imports
`validate_requirements.py`.

The alternative — a `--requirements DIR` flag on `validate_design.py` — would
give the formatter one command instead of two, but it forces D2's warn/error
severity model through `core.print_report` and the exit-code logic in
`lib/artifact_core.py`, which the M1 validator also depends on. A new severity
model does not belong in shared code two stages rely on.

A stage-agnostic `lib/traceability.py` engine was also considered, betting on
reuse by STO-105. That reuse is speculative — STO-105's shape is unspecified.
If it materialises, extracting the engine is precisely the refactor STO-197
already performed when it pulled `artifact_core.py` out of
`validate_requirements.py`. Extracting later is a proven path in this repo,
not a shortcut.

### D8 — The formatter runs it, after the structural gate passes

`agents/design-formatter.md` already re-runs `validate_design.py` against what
it just wrote, and STO-215 established why: the gate belongs where the files
exist, and the formatter is the only stage that has written them. The same
reasoning puts this check there.

It runs **only after `validate_design.py` exits 0**. Traceability findings
computed over a structurally invalid set are noise — an unparseable component
makes its `traces_from` invisible and manufactures false coverage warnings.

Warnings surface after the write, which is later than the Step 3 sign-off
summary. That is inherent: nothing is on disk before the formatter runs, and
the alternative is asking the critic to compute coverage over drafts, which is
the unreachable-gate mistake again. The skill documents the ordering rather
than hiding it.

## Rules

| Rule | Severity | Check |
| --- | --- | --- |
| `dangling-trace` | error | Every design artifact's `traces_from` ID resolves to a requirement file |
| `uncovered-fr` | warn | Every FR (excluding `priority: wont`, `status: obsolete`) appears in ≥1 component's `traces_from` |
| `adr-driver-unresolved` | error | Requirement IDs under an ADR's `## Decision Drivers` resolve |
| `adr-driver-untraced` | warn | A resolving body driver ID absent from that ADR's frontmatter `traces_from` |
| `dangling-reverse-trace` | error | A non-empty `traces_to.design` on a requirement resolves to a real design ID |

## Tool shape

```
python3 validate_traceability.py [DESIGN_DIR] [--requirements DIR]
                                 [--json] [--strict] [--quiet]
```

Defaults: `DESIGN_DIR` is `.sdlc/design`, `--requirements` is
`.sdlc/requirements`. `--quiet` suppresses the **warning** listing; error
lines and the summary always print, matching the flag's meaning in both
existing validators, whose `--quiet` drops PASS lines and keeps failures. A
gate whose quiet mode hides what failed is a bad default — this clause is
what the implementation followed when the two halves of the original wording
turned out to conflict.

Exit codes, matching the two existing validators:

| Code | Meaning |
| --- | --- |
| 0 | No errors (warnings may be present, unless `--strict`) |
| 1 | One or more errors, or any warning under `--strict` |
| 2 | Usage or environment error — either directory missing |

The script imports `validate_design as vd` and `validate_requirements as vr`
for discovery, skip-sets, and the requirement ID pattern, and
`artifact_core as core` for frontmatter parsing. Both script directories are
resolved relative to `__file__`, so the working directory does not matter —
the same `sys.path` handling both existing validators use.

### Finding shape

```python
@dataclass
class Finding:
    rule: str        # one of the five rule names above
    severity: str    # "error" | "warn"
    artifact_id: str # the artifact the finding is about
    path: str        # path relative to its stage directory
    message: str
```

`--json` emits `{"findings": [...], "counts": {"error": N, "warn": N},
"skipped": [...], "duplicate_ids": [...]}`, mirroring
`lint_requirements_content.py`'s machine-readable contract so an agent can
consume it without parsing prose. `skipped` and `duplicate_ids` carry the same
caveats the human report prints in its header: without them a consumer cannot
tell that coverage was computed over an incomplete or collapsed index, which
is precisely the condition that manufactures false `uncovered-fr` findings.

### Human report

```
Validating traceability: .sdlc/design <-> .sdlc/requirements
Indexed 23 design artifact(s), 22 requirement(s).
------------------------------------------------------------
  ERROR  dangling-trace         CMP-003  traces_from -> 'FR-009' is not a known requirement id
  WARN   uncovered-fr           FR-005   no component traces_from this functional requirement
------------------------------------------------------------
Summary: 1 error(s), 1 warning(s).
```

### Unparseable files

A file whose frontmatter does not parse is skipped and counted, with a note in
the report header stating that results may be incomplete. This matters
specifically for coverage: an unparseable component's `traces_from` is
invisible, which would manufacture false `uncovered-fr` warnings. In the
pipeline path this cannot occur, because `validate_design.py` has already
exited 0 (D8).

### Parsing `## Decision Drivers`

The section runs from the line matching `^## Decision Drivers\s*$` to the next
`^## ` line or EOF. IDs are extracted with a non-anchored variant of
`REQUIREMENT_ID_RE` — the shipped constant is anchored with `^...$` and cannot
scan. The variant is guarded so `NFR-001` does not also match as `FR-001`, and
`ADR-` is not in the alternation, so an ADR cross-reference in the prose is
not mistaken for a requirement.

## Files changed

| File | Change |
| --- | --- |
| `skills/design/scripts/validate_traceability.py` | New. The five rules, the CLI, the report. |
| `skills/design/scripts/tests/test_validate_traceability.py` | New. See Testing. |
| `skills/design/scripts/tests/fixtures/traceability/**` | New. Paired design + requirements trees. |
| `agents/design-formatter.md` | "Validator re-run" gains the second command; `formatter_result` carries both outcomes. |
| `skills/design/SKILL.md` | Step 4 documents both commands; the "What This Stage Does Not Produce" list is corrected. |
| `agents/constraint-specialist.md` | Tracing section: both the constraint and business-rule bullets corrected (D6). |
| `skills/design/scripts/README.md` | New. Documents both design-stage scripts, mirroring the M1 scripts README. |
| `docs/requirements/examples/tamagotchi/requirements/**` | 3 constraints clear `traces_to.design`; 4 bounded requirements gain the ID in `traces_from`. |
| `docs/requirements/examples/gdpr/requirements/**` | 1 constraint clears `traces_to.design`. `FR-002` already carries `CON-001` in `traces_from`, so nothing is added. |

### Documentation correction

`skills/design/SKILL.md`'s closing section currently assigns "dependency-cycle
detection, orphan-interface detection" to this ticket, while
`agents/design-critic.md`'s *Scope boundaries* assigns both to STO-208's
content linter. The two files contradict each other. This ticket settles it in
favour of the critic — those are graph and prose sweeps over design-internal
edges, not cross-artifact resolution — and corrects `SKILL.md`, which also
gains the three checks that do ship here.

## Error handling

- Either directory missing → exit 2 with a message naming which one, matching
  `validate_design.py`'s handling of a missing design dir.
- A requirements directory with zero requirements → not an error. Every design
  `traces_from` will fail to resolve and report as `dangling-trace`, which is
  the honest result.
- A design directory with zero artifacts → not an error. Every non-excluded FR
  reports `uncovered-fr`.
- No ADRs → not a finding. An absent `adr/` is a legal outcome per STO-100.
- Missing `pyyaml`/`jsonschema` → the shared core's stdlib fallback applies, as
  for both existing validators. Frontmatter parsing is all this tool needs; it
  does no schema validation of its own.

## Testing

Fixtures live under `skills/design/scripts/tests/fixtures/traceability/<case>/`,
each case a paired `design/` and `requirements/` tree, so a case can be run
end-to-end through the real CLI.

| Case | Asserts |
| --- | --- |
| `clean` | No findings, exit 0 |
| `dangling_trace` | A component citing a non-existent FR is an error |
| `uncovered_fr` | An FR no component cites is a warning |
| `excluded_fr` | A `priority: wont` FR and a `status: obsolete` FR produce **no** finding |
| `fr_covered_by_interface_only` | An FR cited only by an IF still warns — interfaces are not coverage |
| `adr_driver_unresolved` | An unresolvable ID under `## Decision Drivers` is an error |
| `adr_driver_untraced` | A resolving body driver absent from frontmatter `traces_from` is a warning |
| `dangling_reverse_trace` | A requirement's `traces_to.design` naming an unknown ID is an error |
| `empty_reverse_trace` | `traces_to.design: []` produces no finding, and asymmetry produces none |

Exit-code cases: clean → 0; warnings only → 0; warnings only with `--strict` →
1; any error → 1; missing directory → 2. Plus a `--json` shape test asserting
the `findings`/`counts` contract.

Regression: the tamagotchi worked example must pass with zero errors once D6's
data fix lands. It is the only runnable target — it is the sole example with a
`design/` set, and it already passes `dangling-trace` and `uncovered-fr`, the
two rules that do not depend on D6. This is the real-world check that the
rules are calibrated against a set nobody wrote to satisfy them.

The gdpr example has no `design/` directory, so this tool cannot be run
against it (exit 2, missing design dir). Its `CON-001` fix is preventive: it
deletes a redundant copy of an edge `FR-002` already records correctly, and
would otherwise be caught the moment a design set is generated for it. That
fix is verified by re-running `validate_requirements.py` over the gdpr
requirements, which must still exit 0.

## Out of scope

- **Diagram/component agreement** — STO-101 (D1).
- **Dependency cycles and orphan interfaces** — STO-208, per
  `agents/design-critic.md`'s *Scope boundaries*.
- **Prose quality of design artifacts** — STO-208.
- **Writing or back-filling `traces_to.design`** — nothing writes the reverse
  edge (D3); deriving the bidirectional matrix is STO-105.
- **Schema changes** — neither schema changes. D6 moves data between existing
  fields.
- **Test and code traces** (`traces_to.tests`, `traces_to.code`) — no test or
  code artifacts exist to resolve against until M3.
