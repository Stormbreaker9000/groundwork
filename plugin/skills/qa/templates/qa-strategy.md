# QA Strategy

This document is projected from the emitted `TS-` item set and the
`qa_context_artifact` — it is never hand-authored. See `qa-formatter.md`,
"Render the strategy document", for the exact rule that fills each section
below.

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
The `qa_context.test_tooling` and `qa_context.ci_enforcement` answers from the
interview, carried by the `qa_context_artifact`.

## Coverage Targets
The `qa_context.coverage_targets` answer from the interview, carried by the
`qa_context_artifact`.

## Accepted Risks
The `qa_context_artifact.accepted_risks` register — every requirement or
design ID the team declined to test or the critic found uncovered with a
justification. Not one of the validator's five required headings, so it can
be visibly empty (`None identified`) rather than silently missing.
