# Example artifact sets

Complete artifact sets produced by the Groundwork pipelines. Each project is
an independent ID space — `FR-001` in one has nothing to do with `FR-001` in
the other — so each is validated on its own:

| Set | Path | Size |
| --- | --- | --- |
| GDPR data-subject rights (M1) | `gdpr/requirements/` | 21 requirements |
| Desktop tamagotchi (M1) | `tamagotchi/requirements/` | 26 requirements |
| Desktop tamagotchi (M2) | `tamagotchi/design/` | 19 components, 31 interfaces, 7 ADRs, 4 diagrams |

Validate a set by pointing the tools at that set's own directory:

```bash
python3 skills/requirements/scripts/validate_requirements.py \
  docs/requirements/examples/gdpr/requirements
python3 skills/requirements/scripts/lint_requirements_content.py \
  docs/requirements/examples/gdpr/requirements
```

Do **not** point them at `docs/requirements/examples` — the walk is recursive,
and the two projects' ID spaces collide.

- **[`REGENERATION.md`](./REGENERATION.md)** — what changed when all three sets
  were regenerated against the corrected pipeline under STO-219, why each
  difference exists, and which findings deliberately survived. It also records
  the hazards the exercise exposed in the pipeline itself. Read it before
  comparing any of these sets against an older copy.
- **[`tamagotchi/README.md`](./tamagotchi/README.md)** — a guided tour of the
  tamagotchi sets, the exact expected output of every validator, and the
  findings that are still present by choice. The GDPR set has no README of its
  own; its divergences are in `REGENERATION.md` §3.

The tamagotchi project also ships a single-document rendering
(`tamagotchi/CONSOLIDATED.md`) and the dev-log draft that discusses it.
