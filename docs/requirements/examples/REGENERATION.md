# Regenerating the worked examples

**Ticket: STO-219. Covers all three shipped artifact sets.**

The three example sets in this directory were originally produced by
earlier, incomplete versions of the Groundwork pipelines. Each carried
deviations that were not chosen — they were inherited from tooling that
did not yet do the thing the deviation apologised for. ADRs did not exist
yet, so there were no ADRs. Diagrams did not exist yet, so the diagrams
were bolted on afterwards and the index that should have listed them
could not. One set shipped on a failing critique gate because the
alternative was to keep grinding a critic that was raising real findings.

All three sets have now been re-run from the top against the corrected
pipeline. The point of that exercise was not to make the examples look
clean. It was to make every remaining deviation a **chosen** one, so that
a reader can tell the difference between "the tooling cannot do this yet"
and "the tooling did this and we agree with it".

This file is the record of what changed and why. Where a finding survived
the regeneration, it says so and says why surviving was the better
answer.

## What was regenerated

| Set | Path | Before | After |
|---|---|---|---|
| Tamagotchi requirements (M1) | `tamagotchi/requirements/` | 22 requirements | **26** |
| Tamagotchi design (M2) | `tamagotchi/design/` | 11 CMP, 12 IF, 0 ADR, 3 diagrams | **19 CMP, 31 IF, 7 ADR, 4 diagrams** |
| GDPR requirements (M1) | `gdpr/requirements/` | 8 requirements | **21** |

Each set was replayed from a reconstructed `clarification-context.yaml`
(M1) or `design-context.yaml` (M2), committed alongside the set it
produced. The reconstruction rule was strict: every field had to trace to
something the *published set itself* asserts. Nothing that only a later
stage knew was allowed back into the input — see *The replay inputs were
deliberately impoverished*, below, which is where the most interesting
result in this document comes from.

Nothing in any set was hand-edited. Where a fix was needed, the
responsible pipeline agent was re-dispatched and its output copied in
whole. Two attempts to shortcut that rule are recorded in *Hazards this
regeneration exposed* — both were caught, and both are worth publishing
because neither looked like a hand edit from the outside.

---

## 1. The tamagotchi requirements set

### 1.1 BR-001 was self-contradicting, and the pipeline found it unaided

This is the single most load-bearing result in this document, so it is
worth stating precisely what was and was not told to the pipeline.

The published `BR-001` contradicted itself inside one file. Its statement
asserted an outcome — the pet "is reset to a new pet according to the
death-handling policy" — while its own rationale said that whether death
is permanent "is still open (Q-2), which is why this rule is held at low
confidence". One half of the file answered a question the other half
called open. Nothing in the toolchain caught this: it is not a structural
defect, not a lint pattern, and the design critic that later noticed it
only did so because the design stage had by then resolved Q-2 and the
mismatch became visible from outside.

When the clarification context was reconstructed, that contradiction was
found again and written into the `open_questions` field as an editorial
note. It was then **deliberately stripped out** before the pipeline ran.
The reasoning: a note describing what is wrong with the artifact being
replaced is knowledge the original interview never had, sitting in the
exact field the orchestrator consumes. Leaving it in would have steered
the regenerated `BR-001` toward an answer already known, and a clean
result would then have been evidence of nothing. Q-2 went into the replay
reading exactly as `assumptions.md` records it — the plain question, its
owner, and which requirements are held low pending it.

The regenerated set fixed it anyway, and did more than fix it:

- `BR-001` now asserts **no outcome**. Its statement and body both end
  with "This rule asserts nothing about what happens to a pet after it
  reaches the terminal status. That question is open question Q-2."
- The old rule's two entangled concerns were split into two independently
  verifiable rules: `BR-001` (causation — the terminal status is reached
  only through sustained per-stat neglect, never by elapsed time alone or
  an application fault, verified by test) and a new `BR-002` (interim
  preservation — no terminal pet's state may be discarded and no
  disposition implemented while Q-2 is open, verified by inspection).
- `BR-002`'s rationale names the old answer as what it was: *"A previous
  draft invented 'reset to a new pet' as the answer; that was a
  fabrication."*
- The glossary went further and renamed the term. "Death" became
  "terminal end-of-life status", specifically because the old word
  presupposes Q-2's answer in its own name.

The pipeline was told what to watch for. It was never told the answer.

### 1.2 The energy stat was dropped rather than justified

The old glossary defined four stats — hunger, happiness, cleanliness,
energy — but "energy" was grounded in exactly one requirement, the old
`FR-006` (sleep), and nothing else in the set consumed it. The
`fr-specialist` explicitly declined to invent an energy-restoration
requirement to justify the vocabulary, and recommended removing the term
instead. It is now gone from the glossary, and `FR-006` is a bare
Awake↔Sleeping state transition with a new counterpart, `FR-011` (wake) —
the old sleep requirement had no defined exit at all.

This is recorded as assumption `A-12`. It is a divergence in the
direction of less content, and it is the right one: vestigial vocabulary
in a requirement set is a standing invitation for a later stage to build
something to satisfy it.

Related cosmetic divergence: "cleanliness" is now "hygiene". The
reconstructed context never fixed stat names, so this was a free naming
choice, not a contradiction of the input.

### 1.3 Two splits, two new NFRs, and one policy deliberately not carried

- **`FR-011` (wake)** split out of the old `FR-006`, which specified an
  entry into sleep with no exit from it.
- **`FR-012` (quarantine a save file that fails integrity validation)**
  split out of the old combined "recover from corrupted or missing save
  file". The missing-file case is now `FR-010` alone.
- **`NFR-008` and `NFR-009`** are new, from an ISO 25010 Time-behaviour
  gap the critic surfaced unprompted: decay computation cost must not
  scale with absence length (`NFR-008`), and must complete within a bound
  on the launch path (`NFR-009`).
- The old `BR-002` capped decay "at the configured maximum offline
  interval". That cap is **not carried forward**, and its absence is a
  decision rather than an oversight — the first regeneration pass dropped
  it silently, which was caught in review and re-decided by dispatching
  the `constraint-specialist` with both of the old rule's policies laid
  out. It declined to reinstate the cap and recorded `A-24` explaining
  why: decay magnitude is already scale-bounded by `A-2`'s per-stat
  min/max, progression to terminal is driven by neglect *duration*
  (`FR-008`) not decay *magnitude*, so a magnitude cap changes neither
  whether nor when terminal is reached; and a long unremedied absence is
  precisely the sustained neglect `BR-001` treats as legitimate
  causation, so capping to blunt it would cut against `BR-001`'s own
  rationale. The computation-blowup half of the old rationale is covered
  by `NFR-008`.

### 1.4 The set now says what it does not know

Open questions went from 4 to 10; the low-confidence review queue from 5
to 8. Both increases are the pipeline refusing to treat an unstated
premise as settled:

- `Q-5` — **there is no reference machine.** The old set stated absolute
  CPU, memory and latency budgets (`NFR-002`, `CON-001`, and now
  `NFR-009`) with no machine to measure them on. Those figures are not
  executable until Q-5 closes, and the new set says so instead of
  presenting them as testable.
- `Q-6` (release/update/rollback), `Q-7` (maintainability targets),
  `Q-8` (is the Sleeping state even visible to the owner), `Q-9`
  (two-generation save retention), `Q-10` (evaluation cadence) each came
  from a specialist or the critic finding a genuine unstated dependency.

The glossary grew from 6 terms to 32, several of them deliberately
neutral relabelings of the kind described in §1.1.

### 1.5 Three advisory lint findings, and why they stand

`lint_requirements_content.py` on this set reports **3 findings (0 error,
3 warn, 0 info)** and exits 0. They are explained in full in
`tamagotchi/CONSOLIDATED.md` under *Content-lint notes*, and summarised
here so the explanation is not only in the rendering:

- **`NFR-001` `passive-nameless`** — "each pet stat shall be decayed…".
  The actor is the offline-decay computation, named in the Quality
  Attribute Scenario's Artifact field directly below the description.
  Forcing an artificial grammatical subject would read worse.
- **`NFR-007` `vague-qualifier`** on "sufficient". The word appears only
  in supporting prose; the description and fit criterion both carry a
  concrete measure (0 missing transition entries per 24-hour session),
  so the oracle a test checks is unaffected.
- **`glossary.md` `glossary-unused`** on "Idle steady state". The term is
  used inside `NFR-002`'s scenario body (the Environment field), which
  the linter's scan does not index. Real domain vocabulary, not padding.

The old set's linter was clean. That is a genuine regression in the
metric and a wash in substance: none of the three is a defect, and none
was hand-patched away, because a hand-patched set is not a pipeline
product.

---

## 2. The tamagotchi design set

### 2.1 What the old set could not have had

| | Old | New |
|---|---|---|
| Components | 11 (9 internal, 2 external) | **19** (17 internal, 2 external) |
| Interfaces | 12 | **31** |
| ADRs | **none — no `adr/` directory** | **7** |
| Diagrams | 3, generated after the fact | **4**, inside the formatter's run |
| `index.yaml` | 23 entries, no diagrams | **61** (19 CMP, 31 IF, 7 ADR, 4 DIA) |
| `traces_to.diagrams` | deliberately empty | all **19** components |
| `traces_to.adr` | n/a | the **13** components ADRs affect |
| Containers | 1 | **2** (`pet-core`, `webview-ui`) |
| Gate it shipped on | `gate: fail`, human override | **`gate: pass`**, round 3 |
| Traceability sweep | 0 errors, 0 warnings (26 artifacts, 22 requirements) | 0 errors, 0 warnings (61 artifacts, 26 requirements) |

The last row is parity, not a gain, and is listed so that it is not
mistaken for one: the old published set's traces were clean against the
requirements it was actually written for. The two `uncovered-fr`
warnings that appear in this ticket's working notes belong to a
*transient* state — the regenerated M1 checked against a not-yet-
regenerated M2 — and were never a property of anything published. The
regeneration held that row level while more than doubling the artifact
count on both sides of it, which is the claim worth making.

The ADRs are not decoration. Four record decisions the design stage
actually resolved (`ADR-001` terminal status is permanent, `ADR-002`
Windows first, `ADR-003` Tauri, `ADR-004` one committed save generation);
three are `proposed` records for decisions the stage deliberately
deferred (`ADR-005` where the below-threshold clock lives, `ADR-006` the
evaluation cadence period, `ADR-007` whether `CON-001`'s exclusion screen
was ever run). Eleven further decisions were reported as *skipped* by the
ADR generator rather than inflated into records — nine name no `Q-` ID
and stay in `drivers.md`, two duplicate `ADR-003`/`ADR-004`.

There are 4 diagrams rather than 3 because the C4 generator returned two
containers: `generate_c4.py` reuses a container's `technology` label for
every member component, and one container would have had to mislabel
either the Rust core or the webview. One component view is emitted per
container.

### 2.2 The gate passes, and the critique report moved

The old set shipped on `gate: fail` with the artifacts written anyway.
That was a knowing human override, taken because the alternative was to
re-dispatch until the critic went quiet, and the findings were worth more
than a clean gate. It also made the set unreproducible: no ordinary run
may write on a failing gate, so no ordinary run could produce that set.

The regenerated set reached `gate: pass` on round 3 with no override:
round 1 returned `fail` with ten findings (F-01..F-10), all discharged;
round 2 returned `fail` with four *entirely new* findings (F-11..F-14),
all discharged; round 3 returned `pass` with an empty finding register.
No finding survived a third re-dispatch, so the stop rule against
grinding a critic into silence was never even approached.

`critique-report.yaml` is now the **passing** report, and it sits at
`tamagotchi/critique-report.yaml` — the example root, not inside
`design/`. In the old set it lived inside the validated design directory,
where it was a file no agent is instructed to write and no declared
layout contains. At the root it cannot be mistaken for pipeline layout,
and it sits where the other non-artifact companions already sit. Only the
final passing report is published; the failing rounds are narrated here
rather than shipped as a second file.

**One field in it invites misreading.** `critique_report.validator` is
`null`. That is correct by contract, not an omission: the critic runs
*before* anything is on disk and before `drivers.md` exists, so it has no
structural-validator result to report. The structural gate is the
formatter's own re-run of `validate_design.py`, which the orchestrator
folds back into that field in a live run. The file's own header comment
says this; it is repeated here because a reader who opens the exhibit
without the header will read `null` as "the validator was skipped".

### 2.3 The dependency cycle is broken, and nothing forced it

This and §2.4 are the two outcomes the ticket deliberately refused to
pre-decide, on the grounds that deciding them before seeing what the
corrected pipeline produced would be inventing the result. What was *not*
allowed was inheriting either one silently.

The old set contained a genuine dependency cycle:
`CMP-003 → IF-006 → CMP-004 → IF-005 → CMP-003` — two state-holding
components consulting each other to decide what the other was allowed to
do. Both structural validators passed it (every edge resolves); only the
content linter's `dependency-cycle` rule surfaced it, and it was left in
place because breaking it meant redesigning a worked example.

The regenerated set has no cycle. `lint_design_content.py` reports **no
content anti-patterns found**. This was not forced — no re-dispatch was
made to break a cycle, and no cycle ever appeared at any round. The
orchestrator DFS-checked the `CMP → IF.provider → CMP` graph after each
of its three back-fills and it was acyclic every time.

The cause is a decomposition change, not luck. The new decomposition
draws the live-state holder as a **leaf** (`CMP-003 Pet Session` below
`CMP-012 Pet State Store`), with the evaluator, care handler and
presentation shell layered above it. There is no longer a pair of
mutually-consulting state components that *could* close a loop.

**The cost, stated plainly: the `dependency-cycle` rule has lost its only
real-world input.** Before this regeneration, `test_lint_design_content.py`
pinned the rule's exact rendered path against this example. That test is
rewritten, not deleted — the same exact-path assertion now lives at
`test_dependency_cycle_is_reported_with_its_rendered_path`, against the
synthetic `fixtures/lint/cycle-one`, asserting
`"dependency cycle: CMP-001 -> IF-002 -> CMP-002 -> IF-001 -> CMP-001"`.
The assertion is exact-match rather than substring for the same reason it
was before: a transposed lookup in the path renderer would reverse the
path while every ID-substring assertion still passed.

Coverage of that rule is therefore thinner than it was, and the loss was
**accepted rather than avoided**. Breaking the cycle was the better
design; keeping a worse decomposition alive to preserve one test's
realism would have been the wrong trade. No test was added pinning the
shipped example as acyclic, which would over-constrain a set that is
meant to be regenerable.

### 2.4 Both flagged contracts split — but only one by segregation

The old `IF-003` (durable pet-state persistence) and `IF-006` (pet
lifecycle state) were the two contracts flagged as carrying operations
whose consumer sets diverged. Both concerns are separated in the new set.
Only one of them was separated *by* the segregation heuristics, and the
difference is the finding.

- **Durable persistence — split by segregation.** It is now `IF-012`
  (`retrieve`) and `IF-013` (`commit`). The consumer sets are *disjoint*,
  not merely nested: `CMP-003` commits and never retrieves, `CMP-011`
  retrieves and never commits. They are disjoint in time as well
  (retrieval happens once, before a pet exists; commit repeatedly after)
  and differ in failure kind — a failed quarantine must stop a launch, a
  failed commit must report non-durability to a live session.
- **Lifecycle state — separated before segregation was ever reached.**
  Live-state access (`IF-002`, four consumers) could not have merged with
  any lifecycle-transition capability regardless of the heuristics,
  because those capabilities landed on **different providers**: sleep
  entry and wake resolution on `CMP-006`, health advancement on
  `CMP-005`. The merge rule only ever applies within one provider, so the
  heuristics never saw the question at all.

**The finding worth recording is about the heuristics, not the set.** The
interface-segregation heuristics only apply *within a single provider*.
Once a decomposition change has moved two capabilities onto different
components, the question never reaches them — so "did segregation split
this?" cannot be answered from the output alone. A reader comparing the
two sets would naturally credit the heuristics with a split they did not
make. Nothing here is wrong; the outcome is right either way. But the
mechanism that produced it is not the one the output appears to show.

Where the question genuinely did arise inside one provider, the
heuristics did split it: `CMP-006`'s `IF-005 enter_sleep` (consumer
`CMP-008`) from `IF-006 resolve_wake` (consumer `CMP-009`), disjoint by
requirement, since requirements `A-8` fixes that no owner action wakes
the pet. A third split emerged unprompted and was left standing: adding
`CMP-002` as a read-only consumer gave `IF-019`'s two capabilities
non-identical consumer sets, splitting it into `IF-019` (read) and
`IF-025` (atomic replace).

### 2.5 Interface granularity — the old tell is gone

The old set had **11 of 12** interfaces at exactly two operations — 92%.
Twelve independent contracts over a clock, a log, a store, a decay
calculator, a mood evaluator and a notifier do not converge on two
operations each by coincidence; that was the specialist matching a shape
inferred from the examples in its own instructions and carving
granularity to fit. It was the clearest evidence in the old set for why
the granularity heuristics were needed.

The new set has **7 of 31** at two — 23% — across 49 operations:

```
1 op × 21    2 ops × 7    3 ops × 1    4 ops × 1    7 ops × 1
```

The pattern-match on two did not recur, and the outliers are argued
rather than accidental: `IF-001` (7) serves seven consumers with disjoint
parameter needs, and `IF-008` (4) names `feed`/`play`/`clean`/
`put_to_sleep` separately so `FR-003`/`4`/`5`/`6` each trace to a
distinct operation rather than to one switch.

**Recorded rather than acted on:** counts now cluster at *one* instead —
21 of 31, 68%. The acceptance gate asks that counts not cluster at two,
and they do not. But "operation counts vary with need" is only weakly
demonstrated on the low end, and a single-operation contract is the
cheapest thing for a specialist to emit when unsure. Most of these
capabilities genuinely are one verb, so no change was made; a future pass
comparing single-operation contracts against their consumers would be a
reasonable check that the tiebreaker has not simply moved.

### 2.6 One inherited tension, kept visible

`design-context.yaml` records `Q-4` (Electron vs Tauri vs native) as
resolved, while the requirement set's `D-10` says it cannot be closed
before `Q-5` fixes a reference machine. Rather than pretend the tension
away, the resolution is recorded as explicitly provisional — and the
pipeline surfaced the same tension independently, as `ADR-003`'s `medium`
confidence and as `ADR-007` existing at all (does `CON-001`'s exclusion
screen have a recorded baseline, and where is it?). This is an
inconsistency somebody noticed, not one nobody did.

---

## 3. The GDPR requirements set

This set has no README of its own — it is requirements only, with no
design stage and no consolidated rendering — which is why this record
lives one directory up and covers all three sets rather than living under
`tamagotchi/`. Its divergences would otherwise have had nowhere to go.

### 3.1 It also contradicted itself, in the same shape

`assumptions.md` listed `Q-1` — "What is the maximum acceptable
turnaround for an export request?" — as fully open, while `FR-001`
already fixed a 30-day ceiling and `NFR-002` already fixed a one-hour
target for typical accounts. Two requirements answered a question the
assumptions file called unanswered. This is the same class of defect as
tamagotchi's `BR-001` (§1.1), reached independently in a different
domain, and, like it, nothing in the toolchain has any way to see it.

The editorial note describing it was stripped from the replay input for
exactly the reason given in §1.1, and for one more: treating the two M1
replays differently would have made them incomparable.

**The regenerated set does not resolve `Q-1` — deliberately.** `FR-001`
still carries the 30-day figure (it is a statutory ceiling, not a product
choice, and it is not in question) and `NFR-003` states a 72-hour p95
operational target — but that figure is labelled as an *assumed*
placeholder at `confidence: low`, pending `Q-1`, in its description, its
rationale, and `assumptions.md`'s `A-5` and `D-5`. `Q-1`'s
own text was rewritten to say what it is actually asking: not the legal
ceiling, which is fixed, but the practical target inside it.

That is the more honest outcome. The tension is real — a hard legal
ceiling coexisting with an open question about the operational target —
and the regeneration made it visible and labelled rather than making it
disappear.

### 3.2 The confidence field now does work

The old set held **all 8 requirements at `confidence: high`** while two
open questions stood. That is not a disagreement with the discipline; it
is the discipline not being applied. The tamagotchi set of the same era
was flagging affected requirements at low/medium, so the two published
sets were not even internally consistent with each other.

The regenerated set holds **7 low, 4 medium, 10 high**, with all seven
low items in `index.yaml`'s `review_queue`, each naming which open
question it rests on. Where a requirement is speculative, it now says so
in the field built for saying so.

### 3.3 The set grew from 8 to 21, and two of the new NFRs invent things

NFRs went from 2 to 15, driven by the `nfr-specialist`'s mandatory
walkthrough of all nine ISO/IEC 25010:2023 characteristics plus the four
extensions. Two of them reach past the elicited context:

- **`NFR-007`** names WCAG 2.2 AA — a standard the source set never
  mentions.
- **`NFR-008`** names 99.9% availability — an SLA the source set never
  states.

Both are left standing, and both are `confidence: low` with
`review_queue` entries naming exactly the gap. That is the disciplined
handling of a gap-fill: the specialist is allowed to propose a concrete
target where the domain has an obvious one, provided it flags that it
proposed it. An invented figure that is *disclosed* is a question for a
human; an invented figure that is silent is a defect. This regeneration
produced one of each, and the silent one did not survive — see §4.4.

Two NFRs the specialist drafted were dropped at critique for the opposite
failure: `NFR-004` and `NFR-013` invented a traffic-spike premise and a
data-map-growth premise with no anchor in the elicited context, and the
critic's own suggested resolution was to drop them. Their ID slots are
left as gaps rather than renumbered, since nothing was ever published
under those numbers.

### 3.4 The lint delta is larger and is not a regression

`lint_requirements_content.py` reports **7 findings (0 error, 6 warn, 1
info)**, up from the old set's single warning. Zero errors either way.
The delta tracks set size, not per-item quality: 7 findings across 21
items is 0.33 per item against the old set's 0.13, but the old set had
only 2 NFRs and five of the six warnings are `passive-nameless` on NFRs,
an idiom the quality-attribute-scenario template actively invites
("Exported archives shall be delivered…"). The old set's one warning was
`passive-nameless` on its own NFR-001, and that same content still
carries it at its new ID (`NFR-010`) — the original finding recurred, it
did not get papered over.

Two findings are worth naming individually:

- **`CON-001` `impl-bias` on "rest"** is a false positive: the phrase is
  "encrypted at rest".
- **`glossary.md` `glossary-unused` on "Pseudonymisation"** is
  mechanical collateral. Removing an unsourced clause from `CON-001`'s
  rationale (§4.4) happened to delete the only bare-noun use of the term
  in the set; every other occurrence is "pseudonymised" or
  "pseudonymising", which the linter's word-form match does not count.
  Left as-is: chasing it would mean re-dispatching a specialist to
  reword prose for a linter's morphology, which is the tail wagging the
  dog. Advisory, zero errors.

### 3.5 Companion parity

Both M1 sets now carry an identical set of companion files —
`assumptions.md`, `glossary.md`, `index.yaml`, `definition-of-done.md`
and the four type directories. Before this ticket the GDPR set had no
`index.yaml` and the tamagotchi set had no `definition-of-done.md`; each
was missing the file the other had. `diff` of the two directory listings
is now empty.

---

## 4. Hazards this regeneration exposed

These are findings about the *pipeline*, surfaced by running it over real
sets. They are the most transferable part of this document.

### 4.1 Requirement IDs get re-issued with different meanings

A full M1 regeneration re-allocates IDs from scratch. `FR-001`..`FR-010`
in the new tamagotchi set are not the `FR-001`..`FR-010` the design set
was written against — the old `FR-010` was "recover from a corrupted or
missing save file", the new `FR-010` is "initialize a default pet when no
save file is present", and the corrupted case is now `FR-012`.

`traces_from` and `traces_to` carry **bare IDs**, never slugs. So every
stale trace still *resolves*. Both structural validators pass it. The
traceability sweep passes it. There is no tool in this repository that
can see the difference, because every one of them checks that an ID
exists and none of them checks that its meaning still fits.

Concretely, before the design set was regenerated: `CMP-001` declared
`traces_from: [FR-001, FR-010, ...]` and its rationale read "`FR-010`'s
missing-or-corrupt path and the Quarantine of the unreadable file are the
load side of that same ownership" — a sentence describing a requirement
that no longer said that. Clean gates, wrong document.

The regeneration handled it by re-deriving every design trace from
*meaning* rather than assuming ID stability, and a post-hoc sweep of
roughly fifteen artifacts against the re-issued IDs came back clean —
`CMP-013` traces `FR-012` for integrity/quarantine, `FR-010` goes to the
default-pet components. The sweep also caught a trap nobody had flagged:
`BR-002`'s meaning changed *entirely* between the sets, and all fifteen
prose sites that mention it argue the new meaning.

**The transferable rule: an M1 regeneration silently invalidates every
downstream trace, and no gate in this repository will tell you.** Either
regenerate the downstream stage or re-read every trace by hand.

### 4.2 Assumption and dependency IDs collide across stages

The design set maintains its own `A-1`, `A-2`, … in
`design/assumptions.md`, and the requirements set maintains a completely
separate `A-1`, `A-2`, … in `requirements/assumptions.md`. Design
artifacts cite both. An unqualified "A-8" in a component spec is
therefore ambiguous, and the ambiguity is invisible — both IDs exist,
both resolve to something, and neither namespace knows about the other.

**`D-N` collides in exactly the same shape**, and it is worth naming
because the obvious dismissal of it is wrong. The requirements set runs
`D-1`..`D-16`; the design set runs `D-1`..`D-12`. That the design range
is a strict subset is not a reason there is no collision — it is the
collision, since the overlapping IDs carry unrelated content.
Requirements `D-1` is "a reference decay model must exist as an
executable oracle"; design `D-1` is "Q-1 must settle the decay curve …
before the balance configuration can be authored". Both resolve, neither
is what the other means.

Nothing is currently broken by it: a sweep of every component,
interface, ADR, diagram and `drivers.md` in the shipped design set finds
exactly **one** `D-N` citation, and it already reads "requirements
`D-14`". The hazard is latent rather than realised — which is precisely
why it belongs in a record like this one rather than in a bug report.

`Q-N` is the case that genuinely does *not* collide, and the difference
is instructive. The design stage **continues** the requirements
question namespace rather than restarting it: it inherits `Q-1` and
`Q-5`..`Q-10` unchanged and allocates its own new questions from `Q-11`
upward. One namespace, one meaning per ID. That is the shape `A-N` and
`D-N` should have had.

Sixty-seven citation sites in the regenerated design set needed
qualification as "requirements A-N"; they now read that way. Eight of the
sixty-seven are inside YAML frontmatter (`error_modes` strings and one
`operations[].summary`) rather than in body prose. Those were qualified
too, deliberately: they are free-prose string values, no structural key
changed, and skipping them would have half-fixed the defect in exactly
the fields a reader hits first.

The underlying design issue is not fixed by this ticket — the two stages
still share an ID shape. The examples just no longer demonstrate the
collision.

### 4.3 A specialist returned stale published content

During the GDPR replay, a re-dispatched `fr-specialist` was explicitly
instructed not to read any previously published file for this feature. It
returned an `FR-002` that was **byte-identical to the old published
file**, stale `created_at: 2026-06-26` and all — matching nothing in the
round-1 draft it was supposedly revising. It had read the file on disk
despite the instruction, which defeats the entire premise of a
from-context replay.

The contaminated output was discarded and never reached a commit. A
whole-set prose-overlap scan afterwards (old versus new, every file,
60-character fragments) returned zero matches; at 40 characters the seven
hits were all benign — carried open questions, Definition-of-Done
boilerplate, and phrases traceable to `clarification-context.yaml`.

**The transferable rule: "do not read X" is not an enforceable
constraint on an agent with filesystem access.** It is a request. If a
replay's validity depends on it, the output has to be checked against the
thing it was told not to read.

### 4.4 The transcription hazard — the one worth reading twice

This is the subtlest finding in the ticket, and it is a real weakness in
the pipeline's provenance guarantees.

The rule for these sets is that no artifact is hand-edited: a fix means
re-dispatching the responsible agent and copying its output in whole.
That rule was followed in letter and broken in substance, in a way that
took two review rounds to surface.

What happened: the orchestrator took a specialist's **raw returned YAML**
and pasted it verbatim into the formatter's dispatch as "exact content to
write". The formatter then wrote it. Every box is ticked — a specialist
authored the content, a formatter wrote the file, no human typed into the
artifact — and the resulting file is a *transcription*, not a
serialization. The formatter exercised no judgment because none was left
to exercise; the bytes were already fixed before it was asked.

It was caught by a **house-style tell, and only by that**. The file
carried a double-quoted `created_at` — the only one in the GDPR set,
whose other 20 `created_at` values were all single-quoted — and
flow-style `traces_from: [BR-001, BR-002, CON-001]` where every sibling
file in the set uses block style, including its single-item lists. Those
were the specialist's own serialization habits, passed through. Nothing
about the content was wrong. Nothing about the process report was
literally false. The file was simply not produced the way the claim
implied.

**Note how narrow that detection method is.** There is demonstrably no
tree-wide convention to check a file against. The sharpest evidence is
inside a single directory: in `tamagotchi/design`, the 57
formatter-written artifacts carry a single-quoted `created_at` while the
4 `generate_c4.py` diagrams carry an unquoted one — two writers, one
directory, two styles. The per-set contrast points the same way without
proving as much: `gdpr/requirements` is single-quoted and
`tamagotchi/requirements` is entirely unquoted, which is consistent with
style following the writer, though each of those sets is also a single
formatter run and so cannot separate the two explanations. Either way
the anomaly was legible only against its own siblings, and only because
the rest of that one set happened to be uniform. A transcription into a
set that was itself mixed, or the first file written into an empty one,
would leave no tell at all. The
guarantee this fingerprint provides is much weaker than the fact that it
worked once suggests.

The fix was to re-dispatch the formatter with **field values only**, and
instruct it to read two or three sibling files for their conventions
before serializing. The file now matches its siblings exactly.

**The transferable rule: "an agent wrote this file" and "an agent decided
what is in this file" are different claims, and only the second one is
worth anything.** A pipeline whose provenance guarantee rests on which
process performed the write can be satisfied by transcription, and the
resulting artifact is indistinguishable from genuine pipeline output
except by house-style fingerprints. If you need the stronger claim, hand
downstream stages structured values, never pre-serialized text.

A related incident in the same set: an orchestrator applied a
single-field `confidence` change itself rather than re-dispatching,
reasoning that a one-enum edit endorsed by the critic was not really
authoring. When it was re-dispatched properly, the clean specialist
returned a **third** value — `low`, differing from both the hand-set
`high` and the original `medium`, with a defensible rationale neither
prior value had. The hand-set value was simply wrong. Documenting the
shortcut instead of undoing it would have shipped an incorrect confidence
under a "pipeline product" claim.

### 4.5 Two rounds each introduced a defect while fixing one

Worth recording as a fact about fix loops rather than about these sets:
in the GDPR set, the fix round that removed unsourced regulation detail
introduced an unsourced retention figure ("retained for 7 years from the
event date") that appears nowhere in the source set or in the replay
input; and the round that fixed *that* is the one that produced the
transcription artifact in §4.4. Both were caught by review. The corrected
`NFR-012` now asserts no retention duration at all, flags the gap as a
new open question `Q-3` (owner: legal), and sits at `confidence: low`.

A related process lesson, recorded because it nearly sent a review the
wrong way: the initial claim that "7 years appears nowhere in the
pre-task set" rested on a `git show` that had exited 128 because the
filename was wrong. Empty output from a failed command was read as
evidence of absence. The conclusion happened to survive — the real file
said "e.g. 6-10 years", which was never carried into the replay input, so
the figure was unsupported either way — but the reasoning was invalid.
Check exit status before treating empty output as a negative result.

### 4.6 Two smaller generation-quality observations

Neither is a defect and neither was acted on; both are recorded so a
future pass does not rediscover them from scratch.

- **Body-prose line wrapping degraded.** The regenerated M1 formatter
  output wraps body prose noticeably worse than the set it replaced. No
  file in the old tamagotchi set carried more than 11 lines over 79
  columns. The new set's worst are `definition-of-done.md` at 76,
  `assumptions.md` 53, `FR-011` 40, `glossary.md` 32, `FR-002` 21 and
  `FR-008` 17 — 29 of its files exceed 79 somewhere. This is formatter
  output, and the no-hand-editing rule forbids reflowing it by hand, so
  it stands. The fix belongs in the formatter's prompt, not in the
  artifacts.
- **The Definition of Done carries two generation artifacts.**
  `FR-011`'s gate text drops one clause that is present in `FR-011`'s own
  `fit_criterion`, and §3 of both sets' files carries a "**Flagged as
  currently unmet**" note about `traces_to.tests` being empty on every
  `must` item. The second is correct — no tests exist for these examples
  — but it is a template artifact that will read as an alarm to anyone
  who has not read this paragraph. Both want a `generate_dod.py` re-run in
  a later pass, writing to the root-level `.sdlc/definition-of-done.md`
  (the `dod-generator` agent this note originally named no longer ships —
  STO-104 replaced it with that script).

---

## 5. What is still deviant, and why

Everything in this list is a **choice**. None of it is inherited.

| Deviation | Where | Why it stands |
|---|---|---|
| 3 advisory lint findings on tamagotchi M1 | §1.5 | None is a defect; hand-patching would forfeit the pipeline-product claim |
| 7 advisory lint findings on GDPR M1 | §3.4 | Proportionate to a set 2.6× larger; 0 errors; one is a false positive |
| Operation counts cluster at one | §2.5 | Most capabilities are genuinely one verb; worth a future check, not a change |
| `dependency-cycle` has no real-world input | §2.3 | Breaking the cycle was the better design; the rule is still tested synthetically |
| `validator: null` in the critique exhibit | §2.2 | Correct by contract — the critic runs before anything is on disk |
| `critique-report.yaml` is not pipeline layout | §2.2 | It is an exhibit, published at the root precisely so it cannot be mistaken for one |
| `Q-4` resolved while the requirement set's `D-10` says it cannot be | §2.6 | Recorded as provisional; the pipeline surfaced the same tension itself |
| GDPR `NFR-007`/`NFR-008` name an unsourced standard and SLA | §3.3 | Disclosed gap-fills at `confidence: low` with review-queue entries |
| GDPR `Q-1` still unreconciled against `FR-001` | §3.1 | The tension is real; labelling it beats resolving it by fiat |
| `A-N` and `D-N` namespaces still collide across stages | §4.2 | Qualified wherever the examples cite them; the underlying ID-shape issue is another ticket |
| Body-prose wrapping, DoD generation noise | §4.6 | Formatter/generator prompt fixes, not artifact fixes |
| `tamagotchi/dev-log-followup.md` still cites 22 requirements | — | A dated narrative, banner-flagged rather than rewritten; correcting its counts would destroy the before/after account it exists to give |
