---
title: Ideas & Raw Thoughts
description: What we might do — actionable, speculative, or raw. Append-only.
stability: volatile
responsibility: Prioritized direction — what we might build, ordered by readiness
---

## Alpha

Polish and resilience for the three existing modes (Play/Match/Picture).

**Project:**
- Rename repo/project from true-to-hue to splash-of-hue

**Performance:**
- Slow initial load for each of the 3 modes
- Font load: body starts `opacity: 0`, no fallback timeout if Google Fonts is slow/blocked

**Error handling:**
- Start-game failure: no error feedback, silently returns to menu. Add retry + user-visible message.
- No loading indicator while fetching from `/api/game/start`
- localStorage errors silently swallowed — no feedback if storage full/disabled
- Submit endpoint: `except Exception: pass` — data loss is invisible

**Bugs:**
- Picture mode leaks HSB numbers as target label (`formatHSBCompact`) — contradicts visual-over-textual
- Match mode mobile layout needs tuning
- `prefers-reduced-motion` only respected on score counters, not screen transitions

**Scoring:**
- Curve calibration across all three modes

## Beta

All five modes playable with full visual identity.

**Frontend:**
- Design pass on existing mode screens — the v1 foundation (tokens, typography, dark theme, panels) is in place but each screen needs a polish pass before new modes ship on top of it
- Custom icon for app
- Custom icons for home menu mode rows — distinct SVGs per mode matching visual identity
- Animation refinement

**Modes** (after frontend pass):
- Name It — spec'd in `specs-journey`, disabled placeholder in menu
- Read It — spec'd in `specs-journey`, disabled placeholder in menu

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

**Voice:** Honest, direct, fun. Not brutal/snarky (that's dialed's voice and doesn't match our warm visual identity). Not encouraging/generic (that's boring). A sparring partner — specific about what happened, personality in the delivery.

**Voice varies by mode context:**
- **Play:** Sharper, more personality. You're testing yourself. "You saw teal. You played cyan." Fun to fail at without being mean.
- **Skill modes** (Match, Name It, Read It, Picture It): Coach. Constructive, specific. "Hue spot-on, saturation 20% high." The feedback teaches.

No user-facing tone toggle — the mode selection is the toggle.

**Scope:** ~150 hand-crafted messages across per-color and per-round banks, multiple variants per score tier.

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
