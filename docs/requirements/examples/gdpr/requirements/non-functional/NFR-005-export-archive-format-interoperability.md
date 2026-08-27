---
id: NFR-005
type: non_functional
tier: solution
title: Export archive format interoperability
description: Exported personal-data archives shall be delivered in a documented, standard machine-readable format that is parseable by common third-party tools without proprietary software.
rationale: Article 20 requires a "structured, commonly used, machine-readable format"; the brief's core_functionality echoes this ("machine-readable archive"). Interoperability is what makes the export actually portable rather than merely file-shaped.
fit_criterion: 100% of generated export archives validate against the published archive/schema specification via automated schema validation, and open successfully in standard tooling (e.g., archive utility + JSON/CSV parser) in verification testing.
priority: should
confidence: medium
verification_method: test
status: draft
created_at: '2026-08-26'
traces_from: []
traces_to:
  design: []
  tests: []
  code: []
scope: project
parent_scope: null
---

# NFR-005 — Export archive format interoperability

## ISO 25010 Characteristic
Compatibility → Interoperability

## Quality Attribute Scenario
- **Source of stimulus:** Authenticated data subject (or a downstream
  tool acting on their behalf).
- **Stimulus:** Downloads and opens the export archive.
- **Environment:** Normal operation, using common third-party tooling
  (archive utilities, JSON/CSV parsers).
- **Artifact:** Export archive format and its published specification.
- **Response:** The archive opens and parses correctly without
  proprietary software.
- **Response measure:** 100% of archives validate against the published
  schema via automated validation and open successfully in standard
  tooling during verification testing.

## Rationale
Portability under Article 20 is only meaningful if the receiving party
(the data subject or another controller) can actually consume the data;
an undocumented or proprietary format would satisfy the letter of
"machine-readable" while failing its intent.
