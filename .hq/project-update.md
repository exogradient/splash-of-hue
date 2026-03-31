---
updated: 2026-03-30
summary: "Alpha complete — three modes, calibrated scoring, resilience, analytics. Beta in progress: homepage redesign, frontend polish, new modes."
---

## Direction
Hue accuracy matters more than brightness/saturation drift — the game rewards getting the right color family. Power user detail is visual (HSB sliders with pins), not textual. Scoring: effective-ΔE sigmoid with guard terms, hue recovery 33°/55%, release-gated via `make calibrate-release`.

## Key Decisions
- **Client-driven architecture**: client generates colors + scores locally, server is append-only persistence. No network dependency to start a game. (2026-03-29)
- **Hue-recovery scoring**: CIEDE2000 + 55% point recovery if hue within 33°, effective-ΔE guard model (2026-03-31)
- **HSB slider visualization**: show target vs guess as pins on gradient bars, not numbers (2026-03-29)
- **Alpha = resilience + bugs, beta = modes + design pass**: visual polish defers to beta's comprehensive design review (2026-03-29)
- **PWA icon surface split**: installed app icon keeps a self-contained light plate; browser favicon drops the plate and uses true transparency in raster fallbacks (2026-03-30)
- **Achromatic UI during gameplay**: chromatic neutrality is a perceptual requirement, not style (2026-03-28)
- **CIEDE2000 over CIE76**: per-dimension breakdown, built-in hue weighting (2026-03-28)

## Current State
Three modes playable (Play, Match It, Picture It). Client-side color generation + CIEDE2000 scoring — games start instantly with no server round-trip. Per-color reveal screen. localStorage history with mode tabs. Deployed on Vercel serverless. Single-file frontend, single-file backend (submit endpoint only). Alpha resilience and bugs shipped. PostHog analytics and spectral-ring PWA icon system live. Scoring calibration pipeline shipped — alpha scorer release-gated. 5 frontend blockers remain for alpha.

## Open Threads
- Homepage redesign WIP — paint-chip card stack, mode card content
- Frontend polish blockers (beta scope): touch targets, achromatic gameplay bg, mobile scroll overlap, menu cold start, disabled mode cards
- File splitting — unit tests for scoring would be the forcing function
- Remaining modes (Call It, Split It) — beta scope

## Next Steps
- Continue homepage iteration
- Beta frontend polish pass
- Call It + Split It mode implementation
