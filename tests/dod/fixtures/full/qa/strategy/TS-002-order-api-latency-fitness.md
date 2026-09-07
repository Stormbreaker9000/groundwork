---
id: TS-002
type: test_strategy
title: Order API latency fitness function
description: Exercises the Order API's latency budget under normal load.
test_level: performance
risk_level: high
risk_rationale: A latency regression is invisible until checkout conversion drops.
enforcement: ci
traces_from: [NFR-001]
traces_to:
  tests: []
  code: []
status: draft
confidence: high
created_at: '2026-09-07'
---

# TS-002 — Order API latency fitness function

Body prose.
