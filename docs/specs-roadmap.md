---
title: Ideas & Raw Thoughts
description: What we might do — actionable, speculative, or raw. Append-only.
stability: volatile
responsibility: Prioritized direction — what we might build, ordered by readiness
---

## Critical

### Frontend design overhaul (deferred until user journey finalized)

Current UI is functional but has zero personality — basic dark navy CSS, no animations,
swatches in bordered boxes. The gap vs. dialed.gg is large across every dimension:
background, memorize screen, results, typography, chrome, animation, picker.

**Scope:** Full coverage, top-down. Every screen needs a pass.

**Phasing:**
- Phase 1: Lock design direction in a spec (human/conversation task)
- Phase 2: Implementation per-screen, highly parallelizable

Decision: see `design-log` decisions.

## Planned

### Insights (diagnostic) `advanced`

Hidden power-user feature — no visible UI toggle. Activated via URL param, keyboard shortcut, or similar discovery mechanic.

Lens on Play data. Decomposes where errors come from and routes to the right mode.

### Sharing + Leaderboard

Core social loop that made dialed.gg sticky:

- **Share results** — shareable card/link after each game (score, mode, color swatches)
- **Challenge links** — share a specific color set so friends play the same round
- **Leaderboard** — global or friends-only, filterable by mode
- **Daily challenge** — same colors for everyone, compare scores

## Worth Exploring

### Feedback messages — tone and personality

Current messages are generic and encouraging ("Perfect!", "Great", "Keep practicing").
Dialed.gg has ~102 per-round + ~50 total-game entries with multiple random variants per
threshold. Voice: deadpan, snarky, never encouraging even on perfect scores. Examples:
- Perfect: "You're either cheating or broken. Either way, we're concerned."
- Mid: "Violently average."
- Bad: "Somewhere, a color is pressing charges."

This is what makes the game fun to lose at.

**Plan:** Tone presets as a poweruser config (progressive disclosure).
- Initial release: 2 presets — `brutal` (dialed.gg-style, default) + `friendly` (current)
- Future: `coach` preset (constructive/analytical: "Hue spot-on, saturation 20% high")
- UI: dropdown on menu screen, same pattern as picker type
- Bulk of work: writing ~150 hand-crafted messages across both banks

Decision: see `design-log` decisions.

### Educational (nearly free)
- Basic color naming (hue→name) → builds vocabulary
- Real-world color examples ("this is the same hue as a school bus")

## Raw / Unfiltered

### Educational (needs evidence)
- Color theory tips contextual to mistakes

### Deferred
- Multiplayer real-time
- Cultural/historical color context
- Synesthesia associations, cross-domain connections
- Progress charts and trend analysis (need data first)
