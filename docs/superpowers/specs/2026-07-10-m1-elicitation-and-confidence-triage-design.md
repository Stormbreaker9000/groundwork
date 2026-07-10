# Design: M1 Elicitation Quality + Confidence Triage

**Date:** 2026-07-10
**Tickets:** STO-137 (elicitation quality — 5-Whys, numbered options, omitted-category coverage), STO-138 (per-requirement confidence scoring + human-in-the-loop triage)
**Milestone:** M1 — Foundation & Requirements Stage
**Closes:** Gaps 3, 8, 9 (STO-137) and the behavior side of the confidence mechanism (STO-138), from `docs/requirements/requirements_research_gap_analysis.md`

## Context

The requirements skill runs a hypothesis-led interview (`skills/requirements/SKILL.md`
Phases 1–4.5) that produces a `clarification_context`, then a multi-agent pipeline
(orchestrator → fr/nfr/constraint specialists → critic → formatter) that emits atomic
requirement files. Two M1 gaps remain, both **prompt-level**:

- **STO-137** — the interview does not yet apply 5-Whys (reach the business *why*),
  numbered-option questions (Santos et al. 2025: +22.7% quality), or explicit
  coverage prompts for categories LLMs systematically skip.
- **STO-138** — requirements carry a `confidence` field (already in the STO-97 schema,
  already forced to `low` for open-question-affected items by the orchestrator), but
  there is no deliberate assignment rubric and no durable triage surface for
  low-confidence items beyond a one-line note in the conversational summary.

This spec covers both as one coherent change. No new Python scripts; edits land in
`SKILL.md` and the agent definitions. Verification is re-running the existing
validator + content linter on the example set (must stay green) plus a coherence read.

## Part A — STO-137: stronger elicitation (SKILL.md Phases 3–4)

### Phase 3 (Hypothesize) — 5-Whys to the business *why*

After presenting the 3–5 hypotheses, add a step ensuring the underlying business/user
*why* is understood before generating. This is applied judgment, **not** a mechanical
five-times "why?": if the root motivation is already clear from the request, do not
belabor it; if it is murky, ask for it as (or folded into) the Phase 3 question. The
purpose is to prevent generating requirements that satisfy the stated *what* while
missing the actual goal.

### Phase 4 (Converse) — numbered options + omitted-category coverage

**Numbered-option questions.** When a targeted question's answer space is enumerable,
present 2–4 numbered candidate answers so the user can reply with a number (optionally
adding their own). Keep questions open-ended only when the space genuinely is not
enumerable. This layers onto the existing "state what's confirmed → surface working
assumption → one targeted question" per-exchange shape; it does not add extra
questions.

**Commonly-omitted-category coverage.** Add a checklist Claude walks silently across
the interview to catch what LLMs skip:

- error / exception paths
- compliance / regulatory constraints
- data retention / migration / deletion
- internationalization & accessibility
- operational concerns (deployment, backup, monitoring, on-call)
- legal / licensing
- stakeholder roles beyond "the user" (admin, operator, support, auditor, regulator, third-party)

Governing rule, consistent with the skill's existing restraint: **infer from context
where obvious; only ask when the category is high-stakes and non-obvious for this
domain.** The checklist surfaces gaps without ballooning a well-described request's
2–4 exchange budget. It attaches to the existing Phase 4 coverage areas (stakeholders,
NFRs, constraints) rather than becoming a separate interrogation phase.

## Part B — STO-138: confidence scoring + triage

### Specialist confidence rubric

Give the fr/nfr/constraint specialists an explicit rubric for the `confidence` field
they already emit:

- **high** — directly stated or confirmed by the user.
- **medium** — reasonably inferred from the provided context.
- **low** — rests on an open question or an unconfirmed assumption, or is speculative
  / filling a gap the user did not address.

The orchestrator already forces `low` for any requirement affected by
`clarification_context.open_questions`; this rubric makes the remaining assignments
deliberate rather than defaulted.

### Persisted review queue (durable triage surface)

The formatter emits a `review_queue` in `.sdlc/requirements/index.yaml` — the list of
every `confidence: low` requirement ID with a one-line reason — so the triage survives
past the conversation:

```yaml
review_queue:
  - id: FR-007
    confidence: low
    reason: "depends on open question Q-2 (retention window)"
```

This reuses the index the formatter already optionally writes; it is derived (the
per-file `confidence` frontmatter remains authoritative) and regenerated wholesale.
No schema or validator change is required — `index.yaml` is already skipped by the
structural validator.

### Conversational triage block

Upgrade Phase 5's one-line "Flagged for review" into an explicit triage block in the
in-conversation summary that groups the low-confidence FRs/NFRs together with the open
questions and directs the user to review **those specifically** before sign-off — the
efficient human gate the research's Stage 5 calls for (review the uncertain items, not
the whole list).

### Critic / orchestrator

The critic already flags low-confidence items for human triage rather than auto-failing
them (`requirements-critic.md` "Gotchas"). Add a short note that the low-confidence set
is what feeds the formatter's `review_queue` and the Phase 5 triage block, so the three
surfaces stay consistent.

## Files touched

- `skills/requirements/SKILL.md` — Phase 3 (5-Whys), Phase 4 (numbered options +
  omitted-category checklist), Phase 5 (triage block; note the `review_queue` output).
- `agents/fr-specialist.md`, `agents/nfr-specialist.md`, `agents/constraint-specialist.md`
  — confidence rubric.
- `agents/requirements-formatter.md` — emit `review_queue` in `index.yaml`.
- `agents/requirements-orchestrator.md` — note the low-confidence set feeds the review
  queue + triage (keep the existing open-question → `low` rule).
- `agents/requirements-critic.md` — one-line note tying low-confidence to the triage surfaces.

## Build order

1. SKILL.md interview edits (Phase 3 + Phase 4) — STO-137.
2. Specialist confidence rubric — STO-138.
3. Formatter `review_queue` + orchestrator/critic triage notes — STO-138.
4. SKILL.md Phase 5 triage block + `review_queue` mention — STO-138.

## Verification

- `python3 skills/requirements/scripts/validate_requirements.py docs/requirements/examples` → exit 0.
- `python3 skills/requirements/scripts/lint_requirements_content.py docs/requirements/examples` → exit 0.
- Coherence read: the interview flow (Phases 3→4→4.5) reads naturally and does not
  contradict the "infer where obvious, 2–4 exchanges" guidance; the three triage
  surfaces (specialist `confidence`, `index.yaml review_queue`, Phase 5 block) agree.

## Out of scope

- The `confidence` schema field itself (already defined in STO-97).
- Any change to the structural validator or a new script.
- Automated enforcement that `review_queue` matches the low-confidence set (YAGNI —
  the formatter derives both from the same source).
