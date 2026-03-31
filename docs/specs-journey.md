---
title: User Journey
description: Screen-by-screen UI spec — what the user sees and does
stability: volatile
responsibility: The user flow — screen by screen, what the user experiences
---

# User Journey

```
Menu → Countdown → [ Memorize → Pick → Reveal ] ×5 → Results
         (play only)  (play only)
```

## Menu

- **Play** / **Match It** / **Picture It** / **Call It** buttons (active modes)
- **Split It** — planned mode, not yet active
- **History** button → History screen
- **Settings** — picker type dropdown: Field (default) or Sliders

## Countdown (Play only)

- 3, 2, 1 countdown (large centered number, no text prompt)

## Memorize (Play only)

- Single color fills entire viewport (edge-to-edge)
- Timer bar overlaid at bottom — 5s countdown, auto-advances to Pick when timer expires
- Color label and memorize pill hidden in current alpha

## Pick

- "Color N of 5" progress label
- Mode eyebrow visible (e.g. "MEMORY", "MATCH") — identifies the active mode at a glance
- HSB readout of current guess hidden in current alpha (picker meta hidden)
- **Play:** preview swatch fills available space — no target visible, recreate from memory
- **Match It:** target and guess swatches side-by-side (equal size), with visible "TARGET" / "YOUR GUESS" labels above each swatch
- **Picture It:** target shown as HSB text (e.g. "H210 S80 B60") — tap matching color from 4 choices to instantly submit (no confirm button, no picker)
- **Call It:** target color shown as full swatch — tap matching name from 8 choices (XKCD color survey) to instantly submit (no confirm button, no picker). Correct name = 10/10. Wrong picks scored by CIEDE2000 distance between chosen name's canonical color and the target — nearby names score higher than distant ones.
- **Judge It** (idea — not yet implemented): target swatch on neutral gray background at top. 4 choice swatches on a colored surround below. Pick the match — surround shifts how all choices look. Reveal dissolves backgrounds to neutral, showing true colors.
- **Play/Match It:** Picker (field or sliders, per Menu setting)
  - **Field picker:** SB plane + hue bar. Thumb handles ≥26px with glow ring (`box-shadow: 0 0 0 3px rgba(255,255,255,0.25)`). Hue bar 44px tall (Apple HIG touch target).
  - **Sliders picker:** Three gradient-filled tracks (H/S/B) wrapped in `.slider-track-wrap` containers with inset shadow and rounded corners. 6px white pill thumb, full-track height, glow ring matching field picker. Label column (H/S/B) left-aligned.
- Confirm button: glass-morphism overlay pill (44×44px) positioned top-right of the guess swatch area inside `.play-stage-row`. `backdrop-filter: blur(12px) saturate(1.4)`, dark semi-transparent background, white border. Hidden in Picture It and Call It (CSS `[hidden] { display: none }` override). Advances to Reveal.

## Reveal

- Round progress visible ("1 / 5") — vertically centered layout
- Target and guess as two side-by-side color panels (no diagonal split)
- Score large, colored to match the target color
- Verdict text (Perfect/Excellent/Great/Good/Okay/Keep practicing)
- No ΔE or HSB numbers by default — score + verdict + visual comparison tell the story
- Tap score/verdict area to toggle HSB slider detail: three gradient bars (H/S/B) with pins for target vs guess
- Navigation: two glass-morphism overlay pills (44×44px) inside `.reveal-card` — home icon (top-left, ghost variant) quits to menu, forward arrow (top-right) continues. Same `backdrop-filter` pattern as confirm button.
- **Call It only:** correct name and chosen name displayed between swatches and HSB detail
- Continue → next color's Memorize (play) or Pick (match it/picture it/call it), or Results after color 5

## Results

- Top-aligned layout, not vertically centered
- Hero panel: total score with inline "/50" on the same baseline, score tier label (e.g. "SOLID EYE"), mode + picker eyebrow (e.g. "PLAY · FIELD PICKER") — contained in a surface panel with border and elevation. Tappable to toggle advanced details.
- 5 result cards (fixed 3-column grid via `repeat(3, 1fr)`, top-aligned): target vs guess swatch (diagonal split), per-color score (bare number). Per-card verdict text hidden — progressive disclosure only.
- **Call It result cards:** no per-card score. Correct name shown as link to xkcd color survey entry. Wrong picks show "you said *name*" below. Names link to `xkcd.com/color/rgb/#:~:text=<name>`.
- **Menu** / **Play Again** buttons

**Default (clean):** swatches + scores + hero metadata. Verdict text reserved for advanced view.

**Advanced** (tap hero or `?advanced` URL param): adds HSB slider visualization — three gradient bars (H/S/B) with pins showing target vs guess positions at a glance. Same visualization used on the Reveal screen (tap score to toggle).

## History

localStorage-backed. No server dependency. Top-aligned layout, not vertically centered.

- Tabs per mode (Play / Match It / Picture It / Call It)
- Top 20 per mode, sorted by highest score
- Each row: date, total score /50, mini color strip (5 target swatches)
- Tap row → full Results view for that game (reuses Results layout)
- ~500 bytes per game, capped at 20 per mode

---

## Defaults

| Setting | Default | Configurable? |
|---------|---------|---------------|
| Colors per round | 5 | Not yet |
| Memorize time | 5s | Not yet |
| Picker type | Field (hue bar + SB plane) | Yes (Menu dropdown) |
| Countdown | 3s | Not yet |
| Initial picker position | H180° S50% B50% | No (resets each color) |

## Scoring

**Base curve:** Per-color 0–10 via effective-ΔE sigmoid `10 / (1 + (ΔEeff/10)^2.25)`.

**Effective-ΔE guard:** `ΔEeff` starts from `ΔE00`, then adds structured penalty before scoring for overgenerous same-hue saturation / brightness misses and moderate-hue generous cases. Current alpha params: same-hue SB guard `0.25`, mid-hue guard `0.30`.

**Hue-recovery bonus:** If hue distance ≤ 33°, recover up to 55% of lost points: `score += (10 - score) * 0.55 * (1 - hueDist/33)`. Rewards getting the right color family even when brightness/saturation drifts.

**Same-hue rescue:** Disabled in the current alpha scorer.

Total /50. Per-dimension deltas (ΔL', ΔC', ΔH') stored and shown in advanced view.

| Total Score | Tier |
|-------------|------|
| ≥ 42 | Near perfect |
| ≥ 35 | Very strong eye |
| ≥ 25 | Solid eye |
| ≥ 15 | Learning curve |
| < 15 | Early reps |
