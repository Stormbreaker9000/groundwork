# M1 Elicitation Quality + Confidence Triage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Strengthen the requirements interview (5-Whys, numbered-option questions, omitted-category coverage — STO-137) and make per-requirement confidence deliberate with a durable triage surface (STO-138).

**Architecture:** All prompt-level edits to `skills/requirements/SKILL.md` and the agent definitions under `agents/`. No new scripts, no code, no tests. The `confidence` frontmatter field already exists (STO-97); the `review_queue` lives in the formatter's already-optional `index.yaml`, which the structural validator already skips.

**Tech Stack:** Markdown (skill + agent prompt definitions). Verification via the existing `validate_requirements.py` and `lint_requirements_content.py` against `docs/requirements/examples`.

## Global Constraints

- No new scripts, no schema change, no validator change. `index.yaml` is derived and already skipped by the validator.
- The interview must keep its existing restraint: **infer from context where obvious; only ask when high-stakes and non-obvious.** A well-described request still needs ~2–4 exchanges — the new coverage sweep is a gap check, not an interrogation.
- The three triage surfaces must agree: specialist `confidence: low` ⇒ formatter `review_queue` entry ⇒ Phase 5 triage block.
- The confidence rubric text is repeated verbatim in each of the three specialist files (they are standalone prompts with no shared include — this repetition is intentional, not a DRY violation).
- After every task, the example set must stay green: `validate_requirements.py docs/requirements/examples` exits 0 and `lint_requirements_content.py docs/requirements/examples` exits 0. (These edits don't touch example files, so this is a regression sanity check; the real gate is a coherence read.)

---

## Task 1: STO-137 — 5-Whys + numbered options + omitted-category coverage (SKILL.md)

**Files:**
- Modify: `skills/requirements/SKILL.md` (Phase 3 ~line 57; Phase 4 ~lines 82 and 87)

**Interfaces:**
- Produces: an updated interview flow. Later tasks (Phase 5 triage) rely only on the existing Phase 5 structure, not on these edits.

- [ ] **Step 1: Add the 5-Whys step to Phase 3**

In `skills/requirements/SKILL.md`, find this line (end of Phase 3's instruction, before the examples):

```
This is ONE question. Do not ask multiple questions here.
```

Insert immediately AFTER it (new blank line + paragraph):

```
**Reach the business *why* (5-Whys).** Before moving to Phase 4, make sure you understand the underlying business or user goal driving the request — not just the surface *what*. Apply 5-Whys as judgment, not ritual: if the root motivation is already clear from the request, don't belabor it; if it's murky, fold a *why* into this same Phase 3 message (e.g. "…and what problem does this solve for [the user]?"). Requirements generated against a misunderstood goal satisfy the letter and miss the point.
```

- [ ] **Step 2: Add the omitted-category coverage sweep to Phase 4**

In Phase 4, find the end of the numbered "Coverage areas" list:

```
6. **Out of scope** — what's explicitly not being built in this iteration
```

Insert immediately AFTER it (blank line + block):

```
**Also sweep the commonly-omitted categories.** These are the areas requirements processes routinely skip — walk them silently and surface only those that matter for this domain. Governing rule (same restraint as above): **infer where obvious; only ask when the category is high-stakes and non-obvious.**

- Error / exception paths
- Compliance / regulatory constraints
- Data retention / migration / deletion
- Internationalization & accessibility
- Operational concerns — deployment, backup, monitoring, on-call
- Legal / licensing
- Stakeholder roles beyond "the user" — admin, operator, support, auditor, regulator, third-party

This is a gap check, not a script. A well-scoped request may need none of these raised explicitly; do not manufacture questions to cover the list.
```

- [ ] **Step 3: Add numbered-option guidance to the per-exchange shape**

In Phase 4, find the "Per-exchange shape" block:

```
**Per-exchange shape:**
- Briefly state what you've confirmed so far
- Surface your working assumption on the next uncovered area
- Ask one targeted question to validate or correct it
```

Insert immediately AFTER that block (blank line + paragraph):

```
**Prefer numbered options.** When a question's answer space is enumerable, present 2–4 numbered candidate answers and invite the user to reply with a number (or add their own) instead of asking open-ended — this measurably improves answer quality. Reserve open-ended questions for genuinely open spaces. For example: *"For an unauthenticated user hitting a protected route, should the system (1) redirect to login, (2) return 401 with a JSON error, or (3) serve a public preview? Pick one, or describe another."*
```

- [ ] **Step 4: Verify coherence and regression**

Read Phases 3–4.5 top to bottom and confirm the additions read naturally, the "six coverage areas" / "When all six areas are confirmed" wording is not contradicted (the sweep augments the areas; it is not a seventh area), and the restraint guidance is intact.

Run:
```bash
python3 skills/requirements/scripts/validate_requirements.py docs/requirements/examples
python3 skills/requirements/scripts/lint_requirements_content.py docs/requirements/examples
```
Expected: both exit 0 (no example files changed).

- [ ] **Step 5: Commit**

```bash
git add skills/requirements/SKILL.md
git commit -m "feat(sto-137): add 5-Whys, numbered options, and omitted-category coverage to the interview

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: STO-138 — confidence rubric in the three specialists

**Files:**
- Modify: `agents/fr-specialist.md` (after the "Authoring rules" list, ~line 61)
- Modify: `agents/nfr-specialist.md` (in the authoring guidance after the QAS mapping, ~line 67)
- Modify: `agents/constraint-specialist.md` (after the authoring bullets, ~line 69)

**Interfaces:**
- Produces: a consistent confidence rubric in each specialist. Task 3's `review_queue` and Task 4's triage block consume the `confidence: low` set this rubric governs.

- [ ] **Step 1: Add the rubric to the FR specialist**

In `agents/fr-specialist.md`, find the last bullet of the "## Authoring rules (per requirement)" list:

```
- **verification_method** is usually `test` for FRs (occasionally
  `demonstration` or `inspection`).
```

Insert immediately AFTER it (blank line + block):

```
### Confidence rubric

Set `confidence` deliberately, not by default:

- **high** — directly stated or confirmed by the user.
- **medium** — reasonably inferred from the provided context.
- **low** — rests on an open question or an unconfirmed assumption, or fills a gap the user did not address.

The orchestrator additionally forces `low` for any requirement affected by an open question. Low-confidence items are the human triage queue: they are surfaced in the formatter's `index.yaml` `review_queue` and the skill's Phase 5 triage block — so assigning `confidence` honestly is what makes the human gate efficient.
```

- [ ] **Step 2: Add the same rubric to the NFR specialist**

In `agents/nfr-specialist.md`, find this line (end of the fit_criterion/verification guidance):

```
Set `fit_criterion` to the response measure (or a direct restatement of it) and
`verification_method` to how it is proven (`test`/`analysis`/`demonstration`/
`inspection`). Map the characteristic to the `tier` — quality targets are almost
```

That sentence continues on the next lines; locate the end of that paragraph (the blank line before the next `##` heading) and insert this block on its own, after that paragraph ends:

```
### Confidence rubric

Set `confidence` deliberately, not by default:

- **high** — directly stated or confirmed by the user.
- **medium** — reasonably inferred from the provided context.
- **low** — rests on an open question or an unconfirmed assumption, or fills a gap the user did not address.

The orchestrator additionally forces `low` for any requirement affected by an open question. Low-confidence items are the human triage queue: they are surfaced in the formatter's `index.yaml` `review_queue` and the skill's Phase 5 triage block — so assigning `confidence` honestly is what makes the human gate efficient.
```

If the NFR specialist already contains a `### Confidence rubric` heading, stop and report — do not add a duplicate.

- [ ] **Step 3: Add the same rubric to the constraint specialist**

In `agents/constraint-specialist.md`, find this bullet:

```
- `priority` (MoSCoW) and `confidence` as usual; lower `confidence` when the
  boundary stems from an open question.
```

Replace those two lines with:

```
- `priority` (MoSCoW) and `confidence` per the rubric below.
```

Then, immediately after the authoring bullet list that this line belongs to (before the next `##` heading), insert:

```
### Confidence rubric

Set `confidence` deliberately, not by default:

- **high** — directly stated or confirmed by the user.
- **medium** — reasonably inferred from the provided context.
- **low** — rests on an open question or an unconfirmed assumption, or fills a gap the user did not address.

The orchestrator additionally forces `low` for any requirement affected by an open question. Low-confidence items are the human triage queue: they are surfaced in the formatter's `index.yaml` `review_queue` and the skill's Phase 5 triage block — so assigning `confidence` honestly is what makes the human gate efficient.
```

- [ ] **Step 4: Verify consistency and regression**

Confirm all three files now contain the identical `### Confidence rubric` block (same three bullets, same trailing paragraph). Run:
```bash
grep -rl "### Confidence rubric" agents/
python3 skills/requirements/scripts/validate_requirements.py docs/requirements/examples
python3 skills/requirements/scripts/lint_requirements_content.py docs/requirements/examples
```
Expected: the grep lists all three specialist files; both scripts exit 0.

- [ ] **Step 5: Commit**

```bash
git add agents/fr-specialist.md agents/nfr-specialist.md agents/constraint-specialist.md
git commit -m "feat(sto-138): add explicit confidence rubric to the specialists

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: STO-138 — formatter review_queue + orchestrator/critic triage notes

**Files:**
- Modify: `agents/requirements-formatter.md` (Optional machine index section, ~line 107)
- Modify: `agents/requirements-orchestrator.md` (Gotchas, ~line 248)
- Modify: `agents/requirements-critic.md` (Gotchas, ~line 135)

**Interfaces:**
- Consumes: the `confidence: low` set governed by Task 2's rubric.
- Produces: the persisted `review_queue` contract in `index.yaml`, referenced by Task 4's Phase 5 triage block.

- [ ] **Step 1: Add the review_queue to the formatter's index section**

In `agents/requirements-formatter.md`, find the end of the index YAML example and the sentence after it:

```
    path: functional/FR-002-cancel-pending-order.md
```
```

The index is derived, not authoritative — the per-file frontmatter is the source
of truth. Regenerate it wholesale rather than patching it.
```

Insert BETWEEN the closing ``` of the example and the "The index is derived…" sentence (i.e. right after the code fence closes):

```
The index MAY also carry a `review_queue` — every `confidence: low` requirement with a one-line reason — so low-confidence items are triageable without opening each file:

```yaml
review_queue:
  - id: FR-007
    confidence: low
    reason: "depends on open question Q-2 (retention window)"
```

Derive `review_queue` from the same approved set: list every requirement whose `confidence` is `low`. Omit the key (or use an empty list) when none are low-confidence. It is derived, like the rest of the index — the per-file `confidence` frontmatter stays authoritative.
```

- [ ] **Step 2: Add the formatter_result note (same file)**

In `agents/requirements-formatter.md`, the `formatter_result` example lists `index: ".sdlc/requirements/index.yaml"`. Find that line:

```
  index: ".sdlc/requirements/index.yaml"
```

Insert immediately AFTER it:

```
  review_queue_count: 0            # number of confidence:low items in index.yaml's review_queue
```

- [ ] **Step 3: Tie the low-confidence set to triage in the orchestrator**

In `agents/requirements-orchestrator.md`, find this Gotcha:

```
- If `open_questions` is non-empty, ensure affected requirements are marked
  `confidence: low` so the human-in-the-loop can triage them.
```

Insert immediately AFTER it (new bullet):

```
- The full set of `confidence: low` requirements is the triage queue: the
  formatter persists it as `review_queue` in `index.yaml`, and the skill
  foregrounds it in the Phase 5 summary. Keep these consistent — a requirement is
  either low-confidence in all three places or none.
```

- [ ] **Step 4: Tie the low-confidence set to triage in the critic**

In `agents/requirements-critic.md`, find this Gotcha:

```
- Lower-confidence requirements (touching open questions) should be flagged for
  human triage, not auto-failed.
```

Replace it with:

```
- Lower-confidence requirements (touching open questions or unconfirmed
  assumptions) should be flagged for human triage, not auto-failed. This
  low-confidence set is what the formatter persists as `index.yaml`'s
  `review_queue` and the skill surfaces in its Phase 5 triage block — keep your
  verdicts consistent with it.
```

- [ ] **Step 5: Verify and regression**

Confirm the `review_queue` shape in the formatter matches how the orchestrator/critic/Task 4 refer to it (`review_queue`, `id`/`confidence`/`reason`). Run:
```bash
grep -rn "review_queue" agents/
python3 skills/requirements/scripts/validate_requirements.py docs/requirements/examples
python3 skills/requirements/scripts/lint_requirements_content.py docs/requirements/examples
```
Expected: grep shows `review_queue` in formatter (definition), orchestrator, and critic; both scripts exit 0.

- [ ] **Step 6: Commit**

```bash
git add agents/requirements-formatter.md agents/requirements-orchestrator.md agents/requirements-critic.md
git commit -m "feat(sto-138): persist low-confidence review_queue and wire triage across agents

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: STO-138 — Phase 5 triage block in the skill

**Files:**
- Modify: `skills/requirements/SKILL.md` (Phase 5 Step 1 formatter bullet ~line 143; Step 2 summary ~line 172)

**Interfaces:**
- Consumes: the formatter `review_queue` (Task 3) and specialist `confidence` (Task 2).
- Produces: the human-facing triage surface — the terminal consumer; nothing depends on it.

- [ ] **Step 1: Note the review_queue on the formatter pipeline bullet**

In `skills/requirements/SKILL.md` Phase 5 Step 1, find the formatter bullet:

```
6. **requirements-formatter** — writes the atomic files plus the project-level
   `assumptions.md` (Assumptions / Dependencies / Open Questions), running only
   after the critic returns `gate: pass`.
```

Replace it with:

```
6. **requirements-formatter** — writes the atomic files plus the project-level
   `assumptions.md` (Assumptions / Dependencies / Open Questions) and an
   `index.yaml` carrying a `review_queue` of every `confidence: low` requirement,
   running only after the critic returns `gate: pass`.
```

- [ ] **Step 2: Replace the one-line "Flagged for review" with a triage block**

In Phase 5 Step 2's summary template, find:

```
**Flagged for review:** [low-confidence items + open questions — or "None"]
```

Replace it with:

```
**⚠️ Triage before sign-off — review these specifically:**
- **Low-confidence requirements:** [each `confidence: low` FR/NFR/CON/BR ID with its one-line reason — or "None"]
- **Open questions:** [Q-# items still needing a human answer — or "None"]

  These are the uncertain items; confirm or correct *these* rather than re-scanning the whole set. The same low-confidence list is persisted as `review_queue` in `index.yaml`.
```

- [ ] **Step 3: Verify coherence and regression**

Read Phase 5 end to end: the summary now foregrounds the triage block, the formatter bullet mentions `review_queue`, and the wording agrees with the formatter's `review_queue` shape from Task 3. Run:
```bash
python3 skills/requirements/scripts/validate_requirements.py docs/requirements/examples
python3 skills/requirements/scripts/lint_requirements_content.py docs/requirements/examples
```
Expected: both exit 0.

- [ ] **Step 4: Commit**

```bash
git add skills/requirements/SKILL.md
git commit -m "feat(sto-138): foreground low-confidence triage block in the Phase 5 summary

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Final verification

- [ ] **Cross-surface consistency check**

Run:
```bash
grep -rn "review_queue" agents/ skills/requirements/SKILL.md
grep -rl "### Confidence rubric" agents/
```
Expected: `review_queue` appears in the formatter (definition + formatter_result), orchestrator, critic, and SKILL.md; the confidence rubric appears in all three specialists. The three triage surfaces (specialist `confidence`, `index.yaml review_queue`, Phase 5 block) refer to the same low-confidence set with consistent naming.

- [ ] **Example set still green**

Run:
```bash
python3 skills/requirements/scripts/validate_requirements.py docs/requirements/examples
python3 skills/requirements/scripts/lint_requirements_content.py docs/requirements/examples
```
Expected: validator exit 0; linter exit 0.

- [ ] **Interview coherence read**

Read `skills/requirements/SKILL.md` Phases 3–5 once more end to end and confirm the interview reads as one coherent flow that preserves the "infer where obvious, 2–4 exchanges" restraint while adding the 5-Whys, numbered options, omitted-category sweep, and confidence triage.
