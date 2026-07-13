---
id: NFR-005
type: non_functional
tier: solution
title: Local-only data handling
description: The application shall keep all pet data on the local device, performing no network transmission unless the owner grants explicit opt-in consent.
rationale: A private desktop companion should not phone home; users expect their pet and any usage data to stay on their machine, and shipping telemetry by default would breach that expectation and invite privacy and regulatory scrutiny.
fit_criterion: During a full exercise of all features with default settings, a network monitor records 0 outbound connections from the app process; telemetry endpoints are contacted only after an explicit opt-in flag is set, verified by inspection of captured traffic.
priority: must
confidence: high
verification_method: test
status: draft
created_at: 2026-07-10
traces_from: [FR-001]
traces_to:
  design: []
  tests: []
  code: []
scope: project
parent_scope: null
---

# NFR-005 — Local-only data handling

## ISO 25010 Characteristic
Security → Confidentiality

## Quality Attribute Scenario
- **Source of stimulus:** The application itself during normal use (and any embedded third-party component).
- **Stimulus:** The user exercises every feature with default privacy settings.
- **Environment:** Normal operation with a network monitor observing the process.
- **Artifact:** The application process and its data-handling paths.
- **Response:** All pet data is read from and written to local storage only; no data leaves the device.
- **Response measure:** 0 outbound network connections are observed under default settings; telemetry endpoints are contacted only after an explicit opt-in flag is set.

## Rationale
A private desktop companion should not phone home; users expect their pet and any
usage data to stay on their machine, and shipping telemetry by default would breach
that expectation and invite privacy and regulatory scrutiny.
