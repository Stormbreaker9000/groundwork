# Desktop Tamagotchi — Example Requirements Set

A full requirements artifact set produced by the Groundwork pipeline (M1) for a
"desktop tamagotchi" feature. This is the example from the
[eyeofthestorm.dev dev log](https://eyeofthestorm.dev/posts/dev-log-building-groundwork):
the first run exposed a list of gaps, and this set is the re-run after the M1 work
closed them.

## Layout

- **[`requirements/`](./requirements/)** — the validatable atomic set: one Markdown+YAML
  file per requirement under `functional/`, `non-functional/`, `constraints/`,
  `business-rules/`, plus the project-level `assumptions.md` and a machine `index.yaml`
  (which carries the low-confidence `review_queue`).
- **[`CONSOLIDATED.md`](./CONSOLIDATED.md)** — every requirement, the assumptions, and the
  review queue rendered into one readable document.
- **[`dev-log-followup.md`](./dev-log-followup.md)** — the follow-up dev-log post
  (portable draft) narrating the before/after.

## Validating the set

Run the M1 tooling against the `requirements/` subdirectory (not this folder — the
consolidated doc and dev-log are not atomic requirements):

```bash
python3 skills/requirements/scripts/validate_requirements.py \
  docs/requirements/examples/tamagotchi/requirements
python3 skills/requirements/scripts/lint_requirements_content.py \
  docs/requirements/examples/tamagotchi/requirements
```

Expected: validator **22/22 pass**, content linter **clean**. (Requires the M1
requirements pipeline — `assumptions.md` support lands with the STO-134 change.)

## What it demonstrates

- Functional requirements in EARS notation with Gherkin acceptance criteria,
  including an `unwanted`-pattern error path (`FR-010`).
- Seven ISO 25010 quality-attribute-scenario NFRs with measurable response measures.
- Constraints and business rules kept distinct from NFRs.
- Externalized `assumptions.md` (Assumptions / Dependencies / Open Questions).
- Per-requirement `confidence` with a low-confidence `review_queue` for human triage —
  including the runtime/footprint decision (`NFR-002`, `CON-001` → open question Q-4).
