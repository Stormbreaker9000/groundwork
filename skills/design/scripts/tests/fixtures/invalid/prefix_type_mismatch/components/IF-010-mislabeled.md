---
id: IF-010
type: component
title: mislabeled
description: An IF- prefixed id declaring itself a component.
traces_from: []
traces_to:
  adr: []
  diagrams: []
  code: []
  tests: []
status: draft
confidence: low
created_at: 2026-07-18
responsibility: Schema-valid as a component, but its IF- prefix implies an interface.
boundary: internal
depends_on: []
---

# mislabeled

The `IF-` prefix implies `type: interface`, but this file declares
`type: component`. Schema-valid (it satisfies the component branch); the
prefix/type disagreement is a cross-file check.
