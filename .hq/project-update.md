---
updated: 2026-03-29
summary: "Alpha nearly complete — three modes playable, client-driven architecture, resilience shipped. Scoring calibration remains."
---

## Direction
Hue accuracy matters more than brightness/saturation drift — the game rewards getting the right color family. Power user detail is visual (HSB sliders with pins), not textual. UI is stripped to bare essentials — no decorative containers. Scoring curve (k=12 + hue recovery) is actively being calibrated through playtesting.

## Key Decisions
- **Client-driven architecture**: client generates colors + scores locally, server is append-only persistence. No network dependency to start a game. (2026-03-29)
- **Hue-recovery scoring**: CIEDE2000 + 40% point recovery if hue within 25° (2026-03-29)
- **HSB slider visualization**: show target vs guess as pins on gradient bars, not numbers (2026-03-29)
- **Alpha = resilience + bugs, beta = modes + design pass**: visual polish defers to beta's comprehensive design review (2026-03-29)
- **Achromatic UI during gameplay**: chromatic neutrality is a perceptual requirement, not style (2026-03-28)
- **CIEDE2000 over CIE76**: per-dimension breakdown, built-in hue weighting (2026-03-28)

## Current State
Three modes playable (Play, Match, Picture It). Client-side color generation + CIEDE2000 scoring — games start instantly with no server round-trip. Per-color reveal screen. localStorage history with mode tabs. Deployed on Vercel serverless. Single-file frontend, single-file backend (submit endpoint only). Alpha resilience and bugs shipped; scoring calibration and analytics remain.

## Open Threads
- Scoring calibration — more playtesting needed
- PostHog telemetry — alpha scope per roadmap
- File splitting — unit tests for scoring would be the forcing function
- Remaining modes (Name It, Read It) — beta scope

## Next Steps
- Scoring curve calibration across all three modes
- PostHog analytics integration
- Beta planning: design pass, Name It, Read It
