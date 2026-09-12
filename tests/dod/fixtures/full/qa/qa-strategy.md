# QA Strategy

## Test Levels and Rationale
- Unit (TS-001) — the cancellation state machine is exercised in isolation,
  without the order store.
- Performance (TS-002) — the Order API's latency budget is a fitness function,
  not a one-off check.
- Security (TS-003) — audit log tamper-evidence is inspected manually; it is
  not something a unit test can observe from inside the system.
- Integration (TS-004) — the fulfilment cut-off is reviewed at the boundary
  between cancellation and fulfilment.

## Scope by Component
- Order Service — TS-001, TS-004.
- Order API service — TS-002.
- Audit logging subsystem — TS-003.

## Risk-Based Prioritisation
- High: TS-002 (order-api-latency-fitness), TS-003 (audit-log-inspection).
- Medium: TS-001 (cancellation-state-machine).
- Low: TS-004 (fulfilment-cutoff-review).

## Tooling
- CI-enforced: TS-001, TS-002.
- Manual: TS-003.
- Declared unenforced: TS-004.

## Coverage Targets
- FR-001, NFR-001 and NFR-002 are each covered by at least one test-strategy
  item. CON-001 is not: it is a build-time constraint, not a runtime
  behaviour a test strategy exercises.
