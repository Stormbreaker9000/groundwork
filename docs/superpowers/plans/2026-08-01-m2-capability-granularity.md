# M2 Capability & Interface Granularity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the M2 specialists a stated rule for how finely to slice a capability and when two capabilities from one provider become one interface, so the artifact count is a design decision rather than a coin-flip.

**Architecture:** Two instructional edits, one per specialist agent file, each placed inside the section that already governs the decision. The component specialist gets a granularity *band* — name the single component that could satisfy this capability entirely — which sharpens the provider-completeness rule the file already carries. The interface specialist gets the Interface Segregation Principle as a consumer test. Each rule lives in the file positioned to execute it: the component specialist runs first, to break the authoring cycle, and structurally cannot see consumer sets.

**Tech Stack:** Markdown agent definition files with single-key YAML frontmatter. No executable code changes. Python 3 is used only for verification greps and the existing test suite.

**Spec:** `docs/superpowers/specs/2026-08-01-m2-capability-granularity-design.md`

## Global Constraints

- **No critic check.** Do not add a granularity criterion to `agents/design-critic.md`. The fix is instructional, in the specialists themselves.
- **No regeneration of the worked example.** Do not modify any file under `docs/requirements/examples/tamagotchi/design/`. Divergences are recorded in the example README only; regeneration is tracked as STO-219.
- **No operation-count rule.** Do not instruct either specialist about how many operations an interface should carry. The 11-of-12 uniformity is evidence, recorded in the README, not a rule. A rule here invites over-correction into artificial variety.
- **Edits go inside existing sections.** Do not add a new `##` top-level section to either specialist file. A `###` subsection within the governing `##` section is correct.
- **An outcome is bad when it spans providers, not when it needs several operations.** This distinction is load-bearing throughout; do not paraphrase it away.
- No changes to any `.py` file, any schema, or any file under `skills/`.

---

## File Structure

| File | Responsibility | Change |
| --- | --- | --- |
| `agents/component-specialist.md` | Decomposes into components; declares capabilities in prose | Modify — one table row + one `###` subsection inside `## Declaring capabilities` |
| `agents/interface-specialist.md` | Turns capabilities into interface contracts | Modify — one bullet + one worked example inside `## The core rule` |
| `docs/requirements/examples/tamagotchi/README.md` | Explains the worked example and its deliberate deviations | Modify — one `###` subsection appended |

Three tasks, one per file. Each is independently reviewable: a reviewer could accept the component-side band while rejecting the interface-side wording, or accept both while rejecting the README framing.

---

### Task 1: The component-side granularity band

**Files:**
- Modify: `agents/component-specialist.md` — table at lines 138-143, and insert a subsection before the paragraph beginning `**The consequence, stated plainly:**` (line 174)

**Interfaces:**
- Consumes: nothing from earlier tasks
- Produces: `"keep the pet alive while the app is closed"` as the canonical too-broad example, and `"preserve the pet's state across restarts"` as the canonical *genuine tie* — a capability that passes the band (one provider) yet is resolved by the split-when-unsure tiebreaker. Task 3 refers to the tie case; keep the strings identical. The several-operations example is deliberately `"take card payments"` rather than the persistence phrase: using the latter would affirmatively endorse the exact carving Task 3's README calls the defect, deciding the ticket's motivating case both ways in one section.

- [ ] **Step 1: Add the fourth Bad row to the existing table**

Find this table (lines 138-143):

```markdown
| **Bad** | `capability: "persistence"` | Names a *category*, not a need. The interface specialist cannot write operations against it. |
```

Append one row directly after it:

```markdown
| **Bad** | `capability: "keep the pet alive while the app is closed"` | Names an *outcome spanning providers*. Satisfying it takes the clock, the decay engine, and the store — three components, so no single interface can carry it. |
```

- [ ] **Step 2: Verify the table still has five rows and one header**

Run:

```bash
grep -c '^| \*\*' agents/component-specialist.md
```

Expected: `5` (one Good, four Bad).

- [ ] **Step 3: Insert the granularity subsection**

Insert this immediately before the line beginning `**The consequence, stated plainly:**`:

```markdown
### How finely to slice a capability

The rules above say what a capability must *name*. This one says how much it
should *cover*, which is the question that silently decides how many interfaces
the design ends up with.

You already owe every capability a provider — the third rule above. Sharpen that
from "a provider exists" to **exactly one provider suffices**, and it becomes a
test you can apply as you write:

> **Name the single component that could satisfy this capability entirely.**

- **You cannot name one** — the capability spans providers and is too broad.
  Split it along the providers it implies. `"keep the pet alive while the app is
  closed"` needs the clock *and* the decay engine *and* the store.
- **The name you give is a product, a vendor, or an API** — the capability is too
  narrow and has named a mechanism rather than the need. Restate it as the need.
- **Exactly one, and it is a component you have emitted** — correct.

**Needing several operations does not make a capability too broad.**
`"take card payments"` is one capability: one provider offers it as one coherent
service, and the contract it becomes may carry an authorize, a capture, and a
void. Never split a capability because satisfying it takes more than one
operation. The test counts *providers*, never operations.

**When in doubt, split.** The band leaves genuine ties — `"preserve the pet's
state across restarts"` and the pair `"load saved state"` / `"commit state on
change"` each name one provider, so both pass. Break the tie by splitting, because
the pipeline can recover from one error and not the other:

- **Too many capabilities is recoverable.** Two capabilities from one provider
  whose consumers turn out to coincide are merged into a single interface by the
  interface specialist. The design self-corrects.
- **Too few is not.** Every capability you declare becomes exactly one interface,
  and nothing downstream can split one into two. A bundled capability is a merge
  decision you made early, silently, and permanently — on consumer sets you
  cannot see.

So declare the narrower capabilities and leave the merge to the stage that has
the information to judge it.
```

- [ ] **Step 4: Verify the subsection landed inside the right section**

Run:

```bash
awk '/^## Declaring capabilities/,/^## Output/' agents/component-specialist.md | grep -c '^### How finely to slice a capability'
```

Expected: `1` — confirming the new `###` is nested inside `## Declaring capabilities` and not orphaned after `## Output`.

- [ ] **Step 5: Verify no new top-level section was introduced**

Run:

```bash
grep -c '^## ' agents/component-specialist.md
```

Compare against the pre-edit file directly — no stashing:

```bash
diff <(git show HEAD:agents/component-specialist.md | grep '^## ') <(grep '^## ' agents/component-specialist.md)
```

Expected: no output. Any line here means a top-level section was added, removed, or renamed, which the global constraints forbid.

- [ ] **Step 6: Verify frontmatter still parses**

Run:

```bash
python3 -c "
import re, pathlib
t = pathlib.Path('agents/component-specialist.md').read_text()
m = re.match(r'^---\n(.*?)\n---\n', t, re.S)
assert m, 'no frontmatter'
keys = [l.split(':')[0] for l in m.group(1).split('\n') if l and not l.startswith(' ')]
assert keys == ['description'], keys
print('OK', keys)
"
```

Expected: `OK ['description']`

- [ ] **Step 7: Commit**

```bash
git add agents/component-specialist.md
git commit -m "feat(sto-217): give the component specialist a capability granularity band

Name the single component that could satisfy this capability entirely. The
rule sharpens the provider-completeness constraint the file already carries,
from 'a provider exists' to 'exactly one provider suffices'.

An outcome is too broad when it spans providers, not when it needs several
operations — so 'preserve the pet's state across restarts' stays legal while
'keep the pet alive while the app is closed' does not."
```

---

### Task 2: The interface-side Interface Segregation rule

**Files:**
- Modify: `agents/interface-specialist.md` — the corollary list at lines 106-117, inside `## The core rule`

**Interfaces:**
- Consumes: nothing from Task 1 at runtime. The two files are read by different agents and share no literal strings that must match.
- Produces: the consumer-coincidence test that Task 3's README note refers to when explaining why `IF-003` should have been two interfaces.

- [ ] **Step 1: Change the list's introducing line**

Find (line 106):

```markdown
Two corollaries decide when to merge and when to split:
```

Replace with:

```markdown
Three corollaries decide when to merge and when to split:
```

- [ ] **Step 2: Append the third corollary**

Add after the existing second bullet (the one beginning `**The same capability from different providers is two interfaces.**`, ending `...each satisfies its own consumer's capability.`):

```markdown
- **Different capabilities from the same provider are one interface only when
  their consumers coincide.** This is the Interface Segregation Principle: no
  consumer should be made to depend on a contract it does not need. Group two
  capabilities from one provider into a single interface when every component
  consuming either also consumes the other, and emit separate interfaces
  otherwise. "Consumer" means a component that declared the capability in its
  `required_capabilities`; the test is over capabilities, not operations — a
  consumer is never expected to call every operation of a contract it depends on,
  only to genuinely need the capability that contract satisfies.
```

- [ ] **Step 3: Add the worked example**

Add directly after the third corollary, before the next `##` heading (the one that opens the `provider` assignment rules):

```markdown
Worked example — one provider, three interfaces. A pet state manager provides
observation, care-action application, and session seeding:

| Capability it satisfies | Components consuming it |
| --- | --- |
| observe the pet's stat values | lifecycle manager, mood evaluator, pet window, reminder scheduler |
| apply a care action to the pet | pet window |
| seed the session's starting state | session coordinator |

Three interfaces, not one. Three of the four components that observe never apply a
care action, and the one that seeds does neither. Folding these into a single
contract would make the mood evaluator depend on care-action operations it never
calls. Had all three rows listed the same components, one interface would have
been right — that is the merge case in the first corollary, reached from a
different direction.
```

- [ ] **Step 4: Verify the corollary count matches the prose**

Run:

```bash
awk '/^Three corollaries decide/,/^## Assigning/' agents/interface-specialist.md | grep -c '^- \*\*'
```

Expected: `3`

- [ ] **Step 5: Verify the ISP citation is present and the rule sits in the right section**

Run:

```bash
awk '/^## The core rule/,/^## Assigning/' agents/interface-specialist.md | grep -c 'Interface Segregation Principle'
```

Expected: `1`

- [ ] **Step 6: Verify frontmatter still parses**

Run:

```bash
python3 -c "
import re, pathlib
t = pathlib.Path('agents/interface-specialist.md').read_text()
m = re.match(r'^---\n(.*?)\n---\n', t, re.S)
assert m, 'no frontmatter'
keys = [l.split(':')[0] for l in m.group(1).split('\n') if l and not l.startswith(' ')]
assert keys == ['description'], keys
print('OK', keys)
"
```

Expected: `OK ['description']`

- [ ] **Step 7: Verify the capability hand-off vocabulary still agrees across all three agents**

The same cross-file check STO-99's plan used. Run:

```bash
for term in required_capabilities satisfies_capabilities consumed_by; do
  printf '%-24s' "$term"
  for f in agents/component-specialist.md agents/interface-specialist.md agents/design-orchestrator.md; do
    printf '%s=%s ' "$(basename $f .md)" "$(grep -c "$term" $f)"
  done
  echo
done
```

Expected: every term appears at least once in the files that own it — `required_capabilities` in all three, `satisfies_capabilities` and `consumed_by` in the interface specialist and orchestrator. A zero where there was a non-zero before means an edit clobbered a contract reference.

- [ ] **Step 8: Commit**

```bash
git add agents/interface-specialist.md
git commit -m "feat(sto-217): give the interface specialist the Interface Segregation rule

Different capabilities from one provider are one interface only when their
consumers coincide. Stated as ISP so the rule carries the same provenance as
the standards cited elsewhere in these files, rather than reading as taste.

The worked example is CMP-003's real consumer sets from the tamagotchi run,
where the rule reproduces the three-way split the specialist already made."
```

---

### Task 3: Record the example's granularity divergences

**Files:**
- Modify: `docs/requirements/examples/tamagotchi/README.md` — append a `###` subsection at the end of the file, after the section `### The open critic findings, and why they are still here`

**Interfaces:**
- Consumes: the granularity band from Task 1 and the ISP rule from Task 2. Both must be committed first so the README's claim that the pipeline "now teaches" these rules is true.
- Produces: nothing consumed downstream.

- [ ] **Step 1: Confirm the two claims against the example before writing them down**

Do not take these on faith from the plan — verify, then write.

```bash
cd docs/requirements/examples/tamagotchi/design

# Claim 1: IF-003 carries two operations and has two consumers
grep -c '^- name:' interfaces/IF-003-durable-pet-state-persistence.md
grep -l -- '- IF-003' components/*.md

# Claim 2: eleven of twelve interfaces carry exactly two operations
for f in interfaces/*.md; do
  printf '%s ops=%d\n' "$(basename $f | cut -d- -f1-2)" "$(grep -c '^- name:' $f)"
done
cd -
```

Expected: IF-003 reports `2` operations and exactly two consuming components (`CMP-003`, `CMP-007`); the loop reports `ops=2` for every interface except `IF-007`, which reports `ops=1`. If any number differs, stop and reconcile the README text with reality rather than writing the plan's numbers.

- [ ] **Step 2: Append the subsection**

Add at the end of `docs/requirements/examples/tamagotchi/README.md`:

```markdown
### Two granularity artifacts, recorded rather than fixed

This set was generated before the capability and interface granularity heuristics
existed. Two divergences from what the pipeline now teaches are left in place, for
the same reason the critic findings above are.

- **`IF-003` should have been two interfaces.** *Durable Pet State Persistence*
  carries `load` and `commit`, and is consumed by `CMP-007`, which seeds the
  session, and `CMP-003`, which commits on change. Their consumer sets do not
  coincide, which under the Interface Segregation rule is grounds to keep them
  apart. Note where the fault actually sits: one capability can only ever become
  one interface, so the interface specialist had no split available to it. The
  capability was carved too coarsely upstream, and the split-when-unsure
  tiebreaker the component specialist now carries is what would have prevented
  it. This is the unrecoverable direction of that asymmetry, caught in the wild.
- **Operation counts are suspiciously uniform.** Eleven of the twelve interfaces
  carry exactly two operations; only `IF-007` carries one. Twelve independent
  contracts over a clock, a log, a store, a decay calculator, a mood evaluator and
  a notifier do not converge on two operations each by coincidence. This is the
  specialist matching a shape it inferred from the examples in its own
  instructions and then carving granularity to fit — the clearest evidence in this
  set for why the heuristics were needed at all.

Regenerating this set against the corrected pipeline is tracked separately, and
waits on the other in-flight changes so the examples are re-run once rather than
after every fix.
```

- [ ] **Step 3: Verify the example artifacts were not touched**

Run:

```bash
git status --short docs/requirements/examples/tamagotchi/design/
```

Expected: empty output. Any file listed here violates the global constraint against regenerating the example.

- [ ] **Step 4: Verify the design set still validates**

Run:

```bash
python3 skills/design/scripts/validate_design.py docs/requirements/examples/tamagotchi/design
```

Expected: exit 0, `23/23 file(s) passed`. The README lives at the example root, not under `design/`, so it is not discovered as an artifact — this run confirms that is still true.

- [ ] **Step 5: Run the full test suite**

Run:

```bash
python3 -m pytest skills/design/scripts/tests skills/requirements/scripts/tests -q
```

Expected: `95 passed`. No script changed, so a failure here means something unintended was touched.

- [ ] **Step 6: Commit**

```bash
git add docs/requirements/examples/tamagotchi/README.md
git commit -m "docs(sto-217): record the example's two granularity divergences

IF-003 should have been two interfaces under the ISP rule now taught, and eleven
of twelve interfaces carry exactly two operations — the specialist matching a
shape from its own instructions rather than deriving granularity from need.

Recorded rather than fixed, for the same reason the seven open critic findings
are. Regeneration is tracked separately so the examples are re-run once."
```

---

## Verification Checklist

Run after all three tasks:

- [ ] `python3 -m pytest skills/design/scripts/tests skills/requirements/scripts/tests -q` — 95 passed
- [ ] `python3 skills/design/scripts/validate_design.py docs/requirements/examples/tamagotchi/design` — exit 0, 23/23
- [ ] `python3 skills/requirements/scripts/validate_requirements.py docs/requirements/examples/tamagotchi/requirements` — exit 0, 22/22
- [ ] All 13 files in `agents/` parse to single-key `description` frontmatter
- [ ] `git status --short docs/requirements/examples/tamagotchi/design/` — empty
- [ ] `git diff --stat main...HEAD` lists exactly three files besides the spec and this plan
- [ ] `grep -rn "operations" agents/component-specialist.md agents/interface-specialist.md` shows no instruction about how many operations an interface should have
- [ ] `grep -c "granularity" agents/design-critic.md` returns 0 — no critic check was added
- [ ] Both new capability example strings appear identically in the component specialist and, where quoted, the README

Full-set frontmatter check:

```bash
python3 -c "
import re, pathlib, sys
ok = True
for p in sorted(pathlib.Path('agents').glob('*.md')):
    m = re.match(r'^---\n(.*?)\n---\n', p.read_text(), re.S)
    keys = [l.split(':')[0] for l in m.group(1).split('\n') if l and not l.startswith(' ')] if m else None
    if keys != ['description']:
        print('FAIL', p, keys); ok = False
print('all frontmatter OK' if ok else 'FAILURES ABOVE')
sys.exit(0 if ok else 1)
"
```
