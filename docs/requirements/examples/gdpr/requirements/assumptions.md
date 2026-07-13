# Assumptions, Dependencies & Open Questions

## Assumptions
- A-1: Every data subject has exactly one authenticated account identity.
- A-2: "Personal data" is limited to records already catalogued in the data map.
- A-3: Re-authentication uses the existing identity provider; no new auth is built.

## Dependencies
- D-1: A durable object store is available for generated export archives.
- D-2: The identity provider exposes a step-up (re-authentication) flow.
- D-3: Statutory retention rules for financial records are supplied by legal.

## Open Questions
- Q-1: What is the maximum acceptable turnaround for an export request? (owner: product)
- Q-2: Which regulated record types override erasure, beyond financial? (owner: legal)
