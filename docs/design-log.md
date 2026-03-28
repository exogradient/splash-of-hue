---
title: Design Log
description: Decisions and dogfooding — how the design evolves through use
stability: evolving
responsibility: Design decisions and dogfooding observations
---

# Design Log

## Decisions

- **2026-03-28** — Results: clean by default (swatches + scores). HSB values, ΔE, feedback text behind hidden activation (URL param / shortcut). Mirrors dialed.gg's minimal results, but insights available for power users.
- **2026-03-28** — Frontend: evolve own visual identity, not a dialed.gg clone. Use dialed.gg as quality gate — if it doesn't hold up side-by-side, it's not ready.
- **2026-03-28** — Feedback messages: server-side message bank. Returned with submit response. Enables sharing/leaderboards showing the roast text.

## Dogfooding

### Active
- [ ] Play vs Match score gap — does it reveal recall as the bottleneck?
- [ ] Field picker vs sliders — which feels more natural?
- [ ] 5s memorize time — too short? too long? does it vary by color?
- [ ] Initial picker at H180° S50° B50° — neutral enough or does it anchor guesses?
- [ ] Scoring curve — switched to CIEDE2000 sigmoid `10 / (1 + (ΔE00/20)^2.5)` (see `pit/2026-03-28-scoring-algorithm`). Does the curve feel right across score ranges? Do per-dimension deltas (ΔL', ΔC', ΔH') help players understand mistakes?
- [ ] Learning curve — do scores improve over sessions? Is there a plateau?
- [ ] Systematic biases — does everyone undersaturate? Overshoot hue in the same direction?

### Observations
