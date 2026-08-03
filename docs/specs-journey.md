---
title: User Journey
description: The shipped player experience, screen by screen
stability: evolving
responsibility: Shipped user flow and gameplay defaults
---

# User Journey

## Home

A paint-chip deck presents five modes:

- **Play** is the large parchment cover.
- **Match It**, **Picture It**, **Call It**, and **Split It** form the chromatic tabs.
- The deck stacks vertically on mobile and fans horizontally on desktop.
- History is the only persistent utility control.

Selecting a card starts immediately. There is no picker setting or onboarding copy.

## Round structure

All games contain five colors.

```text
Play:       Countdown → [Memorize → Pick → Reveal] ×5 → Results
Other modes:             [Pick → Reveal] ×5 → Results
```

Refresh abandons the in-progress game and returns to Home.

### Homepage embed

`/?embed=play` runs one Play round without the home screen, a round counter,
reveal-time HSB disclosure, results history, or persistence. Continue starts a
new one-round encounter. The host page owns the title and full-game link; see
`homepage-embed-contract.md` for the integration boundary.

## Modes

### Match It

- Target and Guess appear side by side.
- The full-spectrum wheel controls the guess: hue by angle, saturation by radius, brightness on the outer ring.
- Pressing the comparison surface reveals live Guess HSB values. Target values remain hidden until the round is locked.
- The forward action locks the guess.

### Play

- A three-second countdown starts the game.
- The target fills the viewport for five seconds.
- The target disappears; the player recreates it with the same wheel used by Match It.
- No reference or live HSB readout is shown.

### Picture It

- The target is an HSB expression, not a swatch.
- Four color choices appear in a 2×2 grid.
- Choosing a color submits immediately.

### Call It

- The target appears as a swatch.
- Eight XKCD color names are offered.
- Choosing a name submits immediately.
- The reveal identifies the canonical name and the player's choice.

### Split It

- The target appears as a swatch.
- Neutral sliders ask for H, S, and B independently.
- No composite preview or gradient answer cue is shown.
- The forward action locks the estimate.

## Picker

Play and Match It use one wheel. Initial value is `H180 S50 B50` for every color.

| Input | Pointer/touch | Keyboard |
| --- | --- | --- |
| Hue | Angle in the disc | Left/right arrows |
| Saturation | Radius in the disc | Up/down arrows |
| Brightness | Position around the outer ring | Arrow keys |

Shift increases the keyboard step. Hue/saturation and brightness are independent controls.

## Reveal

- Target and guess appear side by side.
- Score is shown out of 10 with a short verdict.
- Continue advances to the next color; Home abandons the game.
- HSB comparison detail is hidden by default.
- Split It reveals HSB comparison by default.
- Match It reveals Target and Guess HSB when the player opted into live values during the pick.

## Results

- Total score appears out of 50 with a tier.
- Five result cards summarize the round.
- The hero surface toggles advanced HSB comparison detail.
- Actions: Home, Play Again, Share.

## History

History is localStorage-backed and available for all five modes.

- Tabs filter by mode.
- Solo games keep the best 20 per mode.
- Challenge games are retained with their code.
- Selecting a row reopens its results.

## Sharing

Share asks for a display name, creates a six-character challenge code, and shows a leaderboard. A challenge replays the same mode and target colors. Joining is supported through challenge links/codes; each challenge accepts at most 20 unique display names.

See `docs/design-sharing.md` for storage and trust boundaries.

## Scoring

Each color scores 0–10; totals score 0–50. The client computes CIEDE2000-based perceptual distance, applies the shipped guard and hue-recovery terms, and gives immediate feedback without a server round trip.

The shared scorer block in `public/index.html` is the release source. Parity checks protect its calibration copies.
