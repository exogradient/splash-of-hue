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

- **Play** / **Match** / **Picture It** buttons (active modes)
- **Name It** / **Read It** — planned modes, not yet in UI
- **History** button → History screen
- **Settings** — picker type dropdown: Field (default) or Sliders

## Countdown (Play only)

- "Get ready to memorize!" prompt
- 3, 2, 1 countdown (large centered number)

## Memorize (Play only)

- Single color fills entire viewport (edge-to-edge)
- "Color N of 5 — memorize!" label + timer bar overlaid at bottom
- 5s countdown, auto-advances to Pick when timer expires

## Pick

- "Color N of 5" progress label
- HSB values of current guess shown below swatch in all modes
- **Play:** preview swatch fills available space — no target visible, recreate from memory
- **Match:** target and guess swatches side-by-side (equal size, labeled "Target" / "Your guess"), converge by eye
- **Picture It:** target shown as HSB text (e.g. "H210 S80 B60") — tap matching color from 4 choices to instantly submit (no confirm button, no picker)
- **Judge It:** target swatch on neutral gray background at top. 4 choice swatches on a colored surround below. Pick the match — surround shifts how all choices look. Reveal dissolves backgrounds to neutral, showing true colors.
- **Play/Match:** Picker (field or sliders, per Menu setting)
- Confirm button → advances to Reveal

## Reveal

- Target and guess as two side-by-side color panels (no diagonal split)
- Score large, colored to match the target color
- Verdict text (Perfect/Excellent/Great/Good/Okay/Keep practicing)
- No ΔE or HSB numbers by default — score + verdict + visual comparison tell the story
- Tap score to toggle HSB slider detail: three gradient bars (H/S/B) with pins for target vs guess
- Back button (quit to menu) + Continue button
- Continue → next color's Memorize (play) or Pick (match/picture), or Results after color 5

## Results

- Total score /50 (bare number, no box — tappable to toggle details)
- 5 result cards: target vs guess swatch (diagonal split), per-color score (bare number, no pill)
- **Menu** / **Play Again** buttons

**Default (clean):** swatches + scores only.

**Advanced** (tap card or `?advanced` URL param): adds HSB slider visualization — three gradient bars (H/S/B) with pins showing target vs guess positions at a glance. Same visualization used on the Reveal screen (tap score to toggle).

## History

localStorage-backed. No server dependency.

- Tabs per mode (Play / Match / Picture It)
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

**Base curve:** Per-color 0–10 via CIEDE2000 sigmoid `10 / (1 + (ΔE00/12)^2.5)`. Tighter than original k=20 — ΔE 7.5 scores ~7.6 (was 9.2), ΔE 10 scores ~5.3 (was 7.6).

**Hue-recovery bonus:** If hue distance ≤ 25°, recover up to 40% of lost points: `score += (10 - score) * 0.4 * (1 - hueDist/25)`. Rewards getting the right color family even when brightness/saturation drifts. Example: ΔE 20 with hue 5° off → base 2.2, final 4.7.

Total /50. Per-dimension deltas (ΔL', ΔC', ΔH') stored and shown in advanced view.

| Total Score | Tier |
|-------------|------|
| ≥ 42 | Near perfect |
| ≥ 35 | Very strong eye |
| ≥ 25 | Solid eye |
| ≥ 15 | Learning curve |
| < 15 | Early reps |
