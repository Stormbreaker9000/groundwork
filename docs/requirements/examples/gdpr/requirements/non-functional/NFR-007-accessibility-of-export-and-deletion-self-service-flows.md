---
id: NFR-007
type: non_functional
tier: solution
title: Accessibility of export and deletion self-service flows
description: The export and deletion self-service flows, including the re-authentication and irreversibility-acknowledgment steps, shall conform to WCAG 2.2 Level AA with 0 critical violations.
rationale: Export and deletion are the only two capabilities this set gives the data subject, and both are exercised through self-service UI with no operator fallback (no admin/support role is described anywhere in the brief). A data subject who cannot perceive or operate the flow — including the re-authentication step-up (FR-003) and the irreversibility acknowledgment (BR-001) — is functionally denied a statutory right with no alternate path, so accessibility conformance is load-bearing rather than cosmetic.
fit_criterion: 0 critical (WCAG 2.2 Level A/AA blocking) violations across the export flow, the deletion flow, the re-authentication step-up, and the irreversibility-acknowledgment step, verified by automated scan (e.g. axe-core) plus a manual screen-reader and keyboard-only walkthrough.
priority: should
confidence: low
verification_method: test
status: draft
created_at: '2026-08-26'
traces_from:
- FR-001
- FR-002
- FR-003
traces_to:
  design: []
  tests: []
  code: []
scope: project
parent_scope: null
---

# NFR-007 — Accessibility of export and deletion self-service flows

## ISO 25010 Characteristic
Interaction Capability → Accessibility / Inclusivity

## Quality Attribute Scenario
- **Source of stimulus:** Authenticated data subject using assistive
  technology (e.g. screen reader, keyboard-only navigation).
- **Stimulus:** Navigates the export or deletion self-service flow,
  including the re-authentication step-up and the
  irreversibility-acknowledgment step.
- **Environment:** Normal operation, any supported assistive
  technology.
- **Artifact:** Export and deletion self-service UI flow.
- **Response:** All flow steps, including re-authentication and the
  irreversibility acknowledgment, are operable and perceivable via
  assistive technology per WCAG 2.2 AA success criteria.
- **Response measure:** 0 critical violations, verified by automated
  scan plus manual screen-reader and keyboard-only walkthrough.

## Rationale
Export and deletion are the only two capabilities this set gives the
data subject, and both are exercised through self-service UI with no
operator fallback (no admin/support role is described anywhere in
the brief). A data subject who cannot perceive or operate the flow —
including the re-authentication step-up (FR-003) and the
irreversibility acknowledgment (BR-001) — is functionally denied a
statutory right with no alternate path, so accessibility conformance
is load-bearing rather than cosmetic.
