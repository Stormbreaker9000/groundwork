# QA Strategy

This document is projected from the emitted `TS-` item set, the
`qa_context_artifact`, and `qa_context` — it is never hand-authored. See
`qa-formatter.md`, "Render the strategy document", for the exact rule that
fills each section below.

## Test Levels and Rationale
One subsection per `test_level` present in the emitted set, in the schema's
enum order (`unit`, `integration`, `contract`, `e2e`, `performance`,
`security`), each listing the items at that level by ID and title.

## Scope by Component
One subsection per component or interface ID named in some item's
`traces_from`, listing the items whose `traces_from` cites it.

## Risk-Based Prioritisation
Every item, ordered `high` before `medium` before `low`, each with its
`risk_rationale` as the stated reason.

## Tooling
The `qa_context.test_tooling` and `qa_context.ci_enforcement` answers from
the interview, read directly from `qa_context` — raw interview answers that
`qa_context_artifact` carries no copy of.

## Coverage Targets
The `qa_context.coverage_targets` answer from the interview, read directly
from `qa_context` — the same source as Tooling, above.

## Accepted Risks
The `qa_context_artifact.accepted_risks` register — every requirement or
design ID the team declined to test or the critic found uncovered with a
justification. Not one of the validator's five required headings, so it can
be visibly empty (`None identified`) rather than silently missing.

## Assumptions
The `qa_context_artifact.assumptions` list — one bullet per `A-#` entry. Not
gated, for the same reason Accepted Risks is not: it must be visibly, honestly
empty (`None identified`) rather than silently missing.

## Dependencies
The `qa_context_artifact.dependencies` list — one bullet per `D-#` entry.
Same non-gated, visibly-empty rule as Assumptions.

## Open Questions
The `qa_context_artifact.open_questions` list — one bullet per `Q-#` entry.
Same non-gated, visibly-empty rule as Assumptions.
