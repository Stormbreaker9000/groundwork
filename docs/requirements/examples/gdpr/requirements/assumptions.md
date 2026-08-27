# Assumptions, Dependencies & Open Questions

## Assumptions
- A-1: The existing identity provider's step-up re-authentication flow returns a discrete, system-observable "confirmed" event that can be correlated to a specific pending deletion request within the 24-hour confirmation window.
- A-2: "Personal data held for the account" is fully and accurately described by the already-catalogued data map; data outside that map is out of scope for export and erasure.
- A-3: The 30-day windows for both export generation and deletion completion are measured as elapsed calendar time from the triggering event (request or confirmation timestamp), not business days.
- A-4: Only one deletion request can be pending confirmation for a given account at a time; behavior for a second deletion request submitted while one is already pending is undefined by this set.
- A-5: A p95 export-turnaround target of 72 hours (NFR-003) is an assumed interim engineering target, not a confirmed figure, pending Q-1.
- A-6: WCAG 2.2 Level AA (NFR-007) is assumed as the applicable accessibility standard for the export/deletion self-service flows; no accessibility law or target was stated in the elicited context.
- A-7: A monthly availability target of >= 99.9% (NFR-008) is assumed for the request-submission endpoints; no SLA was stated in the elicited context.
- A-8: AES-256 (or an equivalent industry-standard algorithm) is assumed for export-archive encryption at rest, and a 72-hour download-link expiry window is assumed (NFR-010); the elicited context specifies the encryption and time-limited-link mechanism but not the algorithm or exact duration.
- A-9: A 5-day margin before the 30-day statutory ceiling is assumed as the alerting threshold for at-risk requests (NFR-015); no specific early-warning window was stated.
- A-10: Financial and tax records are assumed not necessarily to be the complete list of statutory-retention categories (NFR-014, CON-001, BR-002); the set may need to grow pending Q-2's answer from legal.
- A-11: Pseudonymisation of statutorily-retained financial/tax records (CON-001) is assumed to meet the bar GDPR Article 17(3)(b) sets for putting data beyond ordinary processing use, without requiring a separate legal sign-off step in-system.
- A-12: BR-002's retention exemption is assumed to apply per-record (or per-record-category) — only the specific statutory-retention records are held back from FR-002's erasure, not the account as a whole.

## Dependencies
- D-1: A durable object store must be available to hold generated export archives before FR-001 and NFR-010 can be implemented and verified.
- D-2: The existing identity provider must expose a step-up re-authentication flow before FR-003 and NFR-011 can be implemented and verified; no new authentication mechanism is to be built.
- D-3: The already-catalogued data map must be complete and accurate — NFR-001's and NFR-002's completeness measures are bounded by, and only as good as, that catalogue.
- D-4: Legal's finalized enumeration of statutory-retention record types beyond financial and tax (open question Q-2) is needed to fully verify FR-002's fit criterion, to finalize NFR-014's and NFR-017's compliance scope, and may require broadening BR-002 and CON-001 beyond financial/tax records.
- D-5: Product's answer to the maximum acceptable export turnaround (open question Q-1) is needed to replace NFR-003's assumed 72-hour target with a confirmed figure.

## Open Questions
- Q-1: What is the maximum acceptable turnaround for an export request? (The 30-day statutory ceiling in FR-001 is fixed and not in question; this asks for the practical operational target within that ceiling — currently assumed as a 72-hour p95 in NFR-003 — pending this answer.) (owner: product)
- Q-2: Which regulated record types override erasure, beyond financial? (owner: legal)
