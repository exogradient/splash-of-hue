---
title: User Journey
description: Screen-by-screen UI spec — what the user sees and does
stability: volatile
responsibility: The user flow — screen by screen, what the user experiences
---

# User Journey

```
Menu → Countdown → Memorize → Pick → Results
         (play only)  (play only)  (×5)
```

## Menu

- **Play** / **Match** / **Picture It** buttons (active modes)
- **Name It** / **Read It** buttons (disabled placeholders)
- **History** button → recent games list (mode, timestamp, score, picker type)
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
- **Picture It:** target shown as HSB text (e.g. "H210° S80% B60%") — pick matching color from 4 choices (no picker)
- **Play/Match:** Picker (field or sliders, per Menu setting)
- Confirm button → advances to next color, or Results after color 5
- Pick screen fills full viewport width; picker controls constrained to 480px

## Results

- Total score /50 (large, tappable to toggle details)
- 5 result cards: target swatch vs guess swatch, per-color score
- **Menu** / **Play Again** buttons

**Default (clean):** swatches + scores only.

**Advanced** (tap score or `?advanced` URL param): adds color name, feedback text, HSB values, ΔE with per-dimension breakdown (ΔL', ΔC', ΔH').

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

Per-color 0–10 based on CIEDE2000 ΔE with sigmoid curve `10 / (1 + (ΔE00/20)^2.5)`. Total /50. Per-dimension deltas (ΔL', ΔC', ΔH') stored and shown in advanced view.
