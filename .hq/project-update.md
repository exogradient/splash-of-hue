---
updated: 2026-03-29
summary: "Three modes playable end-to-end on Vercel, working toward alpha release polish."
---

## Direction
Hue accuracy matters more than brightness/saturation drift — the game rewards getting the right color family. Power user detail is visual (HSB sliders with pins), not textual. UI is stripped to bare essentials — no decorative containers. Scoring curve (k=12 + hue recovery) is actively being calibrated through playtesting.

## Key Decisions
- **Stateless serverless**: client owns scoring, server is append-only persistence (2026-03-29)
- **Hue-recovery scoring**: CIEDE2000 + 40% point recovery if hue within 25° (2026-03-29)
- **HSB slider visualization**: show target vs guess as pins on gradient bars, not numbers (2026-03-29)
- **Alpha = resilience + bugs, beta = modes + design pass**: visual polish defers to beta's comprehensive design review (2026-03-29)
- **Frontend overhaul is staged, not monolithic**: decomposed across alpha and beta (2026-03-29)
- **Achromatic UI during gameplay**: chromatic neutrality is a perceptual requirement, not style (2026-03-28)
- **CIEDE2000 over CIE76**: per-dimension breakdown, built-in hue weighting (2026-03-28)

## Current State
Three modes playable (Play, Match, Picture It). Per-color reveal screen with instant client-side scoring. localStorage history with mode tabs. Deployed on Vercel serverless. Single-file frontend (2500 lines), single-file backend (236 lines). Alpha release in progress, beta planned.

## Open Threads
- Scoring calibration — more playtesting needed
- File splitting — unit tests for scoring would be the forcing function
- Remaining modes (Name It, Read It) — beta scope
- Project rename: true-to-hue → splash-of-hue for alpha

## Next Steps
- Alpha resilience: start-game error feedback/retry, loading indicator, font load fallback, slow mode load
- Alpha bugs: Picture mode HSB leak, match mode mobile layout, reduced-motion
- Scoring curve calibration across all three modes
