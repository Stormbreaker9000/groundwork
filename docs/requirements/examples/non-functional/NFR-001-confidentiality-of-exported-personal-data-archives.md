---
id: NFR-001
type: non_functional
tier: solution
title: Confidentiality of exported personal-data archives
description: Exported personal-data archives shall be encrypted at rest and retrievable only over an authenticated, time-limited download link scoped to the requesting user.
rationale: A data-export archive concentrates all of a user's personal data into a single object, so its exposure is a high-impact breach; encryption plus short-lived authenticated links keep the portability feature from becoming an exfiltration channel.
fit_criterion: Archives are encrypted with AES-256 at rest; download links require the requesting user's authenticated session and expire within 24 hours; a penetration test finds 0 archives retrievable without authentication.
priority: must
confidence: high
verification_method: test
status: draft
created_at: 2026-06-26
traces_from: [FR-001]
traces_to:
  design: []
  tests: []
  code: []
scope: project
parent_scope: null
---

# NFR-001 — Confidentiality of exported personal-data archives

## ISO 25010 Characteristic
Security → Confidentiality

## Quality Attribute Scenario
- **Source of stimulus:** An authenticated user, or an attacker attempting to intercept the download.
- **Stimulus:** A completed data-export archive is made available for download.
- **Environment:** Normal production operation, with the archive stored pending retrieval.
- **Artifact:** The export-archive storage and its download endpoint.
- **Response:** The archive is encrypted at rest and served only over an authenticated, time-limited download link scoped to the requesting user.
- **Response measure:** Archives are encrypted with AES-256 at rest; download links require the requesting user's authenticated session and expire within 24 hours; a penetration test finds 0 archives retrievable without authentication.

## Rationale
A data-export archive concentrates all of a user's personal data into a single
object, so its exposure is a high-impact breach. Encrypting it and gating
retrieval behind short-lived authenticated links keeps the portability feature
from becoming an exfiltration channel.
