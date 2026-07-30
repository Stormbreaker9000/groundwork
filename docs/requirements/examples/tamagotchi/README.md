# Desktop Tamagotchi — Example Artifact Set

A full requirements set (M1) and the architecture set generated from it (M2), produced
by the Groundwork pipelines for a "desktop tamagotchi" feature. This is the example from
the [eyeofthestorm.dev dev log](https://eyeofthestorm.dev/posts/dev-log-building-groundwork):
the first run exposed a list of gaps, and these sets are the re-runs after the work
closed them.

## Layout

- **[`requirements/`](./requirements/)** — the validatable atomic requirement set: one
  Markdown+YAML file per requirement under `functional/`, `non-functional/`,
  `constraints/`, `business-rules/`, plus the project-level `assumptions.md`,
  `glossary.md`, and a machine `index.yaml` (which carries the low-confidence
  `review_queue`).
- **[`design/`](./design/)** — the architecture set generated from those requirements:
  11 component specs under `components/`, 12 interface specs under `interfaces/`, plus
  `assumptions.md`, `drivers.md`, `index.yaml`, and the `critique-report.yaml` the design
  critic produced against this set.
- **[`CONSOLIDATED.md`](./CONSOLIDATED.md)** — every requirement, the assumptions, and the
  review queue rendered into one readable document.
- **[`dev-log-followup.md`](./dev-log-followup.md)** — the follow-up dev-log post
  (portable draft) narrating the before/after.

## Validating the sets

Run each stage's tooling against its own subdirectory, not against this folder — the
consolidated doc and the dev-log are not atomic artifacts, and neither validator will
accept them.

```bash
# M1 — requirements
python3 skills/requirements/scripts/validate_requirements.py \
  docs/requirements/examples/tamagotchi/requirements
python3 skills/requirements/scripts/lint_requirements_content.py \
  docs/requirements/examples/tamagotchi/requirements

# M2 — design
python3 skills/design/scripts/validate_design.py \
  docs/requirements/examples/tamagotchi/design
```

Expected: requirements validator **22/22 pass**, content linter **clean**, design
validator **23/23 pass**.

Note that the design set deliberately has no `README.md` of its own. Anything under
`design/` that is not a skipped companion is discovered as an artifact and must parse as
one, so a stray Markdown file there fails the gate. That is why this README sits at the
example root — the same reason `requirements/` has none either.

## What the requirements set demonstrates

- Functional requirements in EARS notation with Gherkin acceptance criteria,
  including an `unwanted`-pattern error path (`FR-010`).
- Seven ISO 25010 quality-attribute-scenario NFRs with measurable response measures.
- Constraints and business rules kept distinct from NFRs.
- Externalized `assumptions.md` (Assumptions / Dependencies / Open Questions).
- Per-requirement `confidence` with a low-confidence `review_queue` for human triage —
  including the runtime/footprint decision (`NFR-002`, `CON-001` → open question Q-4).

## What the design set demonstrates

The architecture stage picks up exactly where the requirements stage left off, including
its unfinished business.

- **The inherited questions get answered.** Q-4 — *Electron, Tauri, or native, given the
  footprint constraint* — is the question the requirements stage could not settle, and the
  one the first tamagotchi build got wrong by never treating it as a decision. It is
  answered here (Tauri), along with Q-3 (Windows first) and Q-2 (death is permanent), and
  all three are recorded in `drivers.md` as tradeoffs with their gains, their costs, and
  the requirements that rested on them.
- **The dependency graph closes.** 11 components and 12 interfaces, 26 `CMP → IF → CMP`
  edges. Components declare *capabilities* in prose; interfaces satisfy each exactly once;
  the orchestrator back-fills the edge. Two components are `boundary: external` — the OS
  notification service and the system clock — because a dependency cannot point outside
  the graph.
- **The drivers are written down.** `drivers.md` carries 13 architecturally significant
  requirements with why each shapes structure, 10 tradeoffs, and 6 sensitivity points —
  the reasoning that would otherwise live only in the conversation that produced it.
- **The critique is published, not hidden.** `critique-report.yaml` is the design critic's
  real output against this set. It returned `gate: fail`, and the set is shipped with that
  visible rather than tidied away.

### The open critic findings, and why they are still here

Two findings were correctness faults and were fixed: `CMP-004` and `IF-008` traced from
`BR-001` while asserting the opposite of its statement text. Both now pass.

That one is worth reading in full, because it runs the other way. `BR-001` is *internally
inconsistent*: its statement asserts the pet "is reset to a new pet", while its own
rationale says whether death is permanent "is still open (Q-2), which is why this rule is
held at low confidence". The design stage resolved Q-2 as permanent and the specialists
silently followed it. The critic caught the mismatch. The resolution recorded here is that
`BR-001`'s statement text is stale and needs amending upstream — filed as **Q-5** in
`design/assumptions.md`. Architecture found a latent defect in the requirements it was
built from.

Seven findings remain open and are deliberately preserved as genuine critic output:

- **Three responsibility phrasings** (`CMP-003`, `CMP-006`, `CMP-008`) trip the
  single-responsibility rule. `CMP-006` is arguably a false positive — the rule greps the
  sentence for "and" rather than judging cohesion, and a UI surface that presents and
  accepts input is one duty by most readings.
- **Three interfaces** (`IF-002`, `IF-006`, `IF-012`) carry both a blocking and a
  non-blocking operation, but `interaction` is a single enum. The schema cannot express a
  mixed-mode contract, so no wording of these artifacts would satisfy the check.
- **One `traces_from` plausibility** flag on `CMP-001`.

They are left in place because a worked example showing a critic that found nothing would
teach nothing about whether the critic works.
