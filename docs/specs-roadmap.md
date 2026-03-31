---
title: Ideas & Raw Thoughts
description: What we might do — actionable, speculative, or raw. Append-only.
stability: volatile
responsibility: Prioritized direction — what we might build, ordered by readiness
---

## Beta

All five modes playable with full visual identity.

**Frontend:**
- Menu cold start — tagline below brand mark on Play card (e.g. "How well do you really see color?") + one-line descriptor per mode card (~40 chars). Replace descriptors with personal best after 3+ games
- ~~Disabled mode card~~ — all modes now playable, no more "Coming soon" cards
- Achromatic gameplay background — tinted body gradient (gold/blue radials at 10-12% opacity) persists during gameplay, affecting color perception. Scope to home screen only; gameplay uses pure `var(--bg)`
- Touch targets — hue bar hit area 34px, below 44px minimum (Apple HIG). Expand via padding. SB field thumb (22px visual) similarly needs 44px hit area
- Mobile scroll overlap — confirm button (position:fixed) overlaps picker on short viewports (iPhone SE). Add `padding-bottom: calc(80px + env(safe-area-inset-bottom))`
- Text-only share on results screen — `navigator.share()` (mobile), clipboard + toast (desktop). Format: mode, per-color scores, total + tier, URL. No image gen for v1
- Social og image
- Scoring drift monitoring: continue tuning against `auto-grader` verdicts, random audit slice for blind-spot discovery, revisit same-hue large-SB and moderate-hue edge cases if fresh exports show renewed disagreement
- Future data accrual: thumbs-down feedback in power-user mode on reveal/result screens
- Design pass (screen-by-screen polish before new modes ship):
  - Font weight trim: drop 600 → 500, keep 400/500/700 (~20KB)
  - Results reveal order: cards first (staggered), then total with scale pulse (0.95→1.0, 200ms) — total as conclusion, not headline
  - Contextual picker toggle: "Field | Sliders" segmented control in pick screen above picker. Menu toggle stays as shortcut
  - Adaptive memorize overlay: pill darkens on bright targets (B>70, S<40), lightens on dark targets
  - Directional transitions: forward translateY(8px)→0, backward translateY(-4px)→0, quit opacity-only 150ms
  - Tier color desaturation ~15%: gold → #b8a078, teal → #7a9a9e (hierarchy via lightness, not chroma)
  - Confirm button in layout flow relative to picker, not viewport-fixed. Mobile: full-width pill. Desktop: picker panel corner
  - PWA install prompt after 3rd game, one-time dismissible banner. `beforeinstallprompt` (Android), instructional (iOS)
  - Low-score empathy: warm feedback text for sub-15 scores (Early reps) — highest-risk churn moment
  - History empty state: "No games yet. Play one?" with ghost Play button

**Modes** (after frontend pass):
- ~~Call It~~ — shipped. XKCD color survey (949 names), CIEDE2000 nearest-match, lazy LAB cache, partial sort for distractor selection.
- ~~Split It~~ — shipped. Neutral sliders (no color preview, no gradient hints), hue color dots + intensity dots for orientation, value readouts track thumb position, reveal shows HSB comparison bars by default. CIEDE2000 scoring. Future: difficulty levels (coarse→narrow buckets) for all modes or adaptive scaling.

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

### Progression

Personal best tracking per mode (prominent on menu), streak tracking (games per day/week), improvement-over-time visualization. localStorage history already captures game data — confirm schema supports everything needed before adding new modes.

## Worth Exploring

### Feedback messages — tone and personality

Current messages are generic and encouraging ("Perfect!", "Great", "Keep practicing").

**Voice:** Honest, direct, fun. Not brutal/snarky (that's dialed's voice and doesn't match our warm visual identity). Not encouraging/generic (that's boring). A sparring partner — specific about what happened, personality in the delivery.

**Voice varies by mode context:**
- **Play:** Sharper, more personality. You're testing yourself. "You saw teal. You played cyan." Fun to fail at without being mean.
- **Skill modes** (Match It, Call It, Split It, Picture It): Coach. Constructive, specific. "Hue spot-on, saturation 20% high." The feedback teaches.

No user-facing tone toggle — the mode selection is the toggle.

**Scope:** ~150 hand-crafted messages across per-color and per-round banks, multiple variants per score tier.

No design-log decision yet — voice direction above is the working spec.

### Educational (nearly free)
- Basic color naming (hue→name) → builds vocabulary
- Real-world color examples ("this is the same hue as a school bus")

### Onboarding `v2`

3-screen guided first-play: (1) "You'll see a color for 5 seconds," (2) "Recreate it from memory," (3) "Let's try one." Interactive, skippable. Not needed for v1 if mode descriptors solve cold start.

### Desktop differentiation

27" monitors expose the mobile-first void around the 1180px content shell. Ambient treatment for surrounding space: noise texture at 2-3% opacity or slow gradient. Makes desktop feel intentional, not "mobile on a big screen."

## Raw / Unfiltered

### Educational (needs evidence)
- Color theory tips contextual to mistakes

### Deferred
- Multiplayer real-time
- Cultural/historical color context
- Synesthesia associations, cross-domain connections
- Progress charts and trend analysis (need data first)
