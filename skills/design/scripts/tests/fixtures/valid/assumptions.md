# Design Assumptions

Architecture-stage assumptions, dependencies, and open questions. These are
distinct from requirements assumptions: they are decisions the design leans on
that never rose to a full ADR.

## Assumptions
- The system runs against a single-writer relational database.
- The payment provider is reachable synchronously within the request budget.

## Dependencies
- The requirements glossary (../requirements/glossary.md) is authoritative for
  shared vocabulary; the design stage does not redefine terms.

## Open Questions
- None identified.
