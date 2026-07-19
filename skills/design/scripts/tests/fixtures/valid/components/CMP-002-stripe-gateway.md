---
id: CMP-002
type: component
title: stripe-gateway
description: The external payment provider, modelled as a component outside the system boundary.
traces_from: []
traces_to:
  adr: []
  diagrams:
    - c4-container
  code: []
  tests: []
status: reviewed
confidence: medium
created_at: 2026-07-18
responsibility: Charge cards and report payment outcomes; owned and operated by a third party.
boundary: external
depends_on: []
---

# stripe-gateway

An external system. It is a component with `boundary: external` because the
graph must stay total — every provider of an interface has to be a component,
even one we do not build.
