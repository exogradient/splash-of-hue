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
Standalone rounds also expose one familiar Home icon. Browser Back and Escape
return to Home through the same cleanup path, and focus returns to the mode card
that started the round. The homepage embed omits this game-owned return control
because its host owns collapse and return.

### Homepage embed

`/?embed=play` runs one Play round without the home screen, a round counter,
reveal-time HSB disclosure, results history, or persistence. Continue starts a
new one-round encounter. The host page owns the title and full-game link; see
`homepage-embed-contract.md` for the integration boundary.

## Modes

### Match It

- Target remains continuously visible while Guess owns the working surface.
  Wider layouts place the Target reference beside a larger Guess field; phone
  layouts reflow the same hierarchy into a shallow Target strip above Guess.
- The full-spectrum wheel controls the guess: hue on the outer ring, saturation
  horizontally in the inner field, and brightness vertically in the same
  field. It is superimposed directly on the Guess field rather than separated
  into a black control panel. A continuous square-to-disc mapping keeps every
  HSB extreme reachable.
- Pressing the `Guess` label reveals live Guess HSB values. The stable role
  label remains visible; Target values remain hidden until the round is locked.
- The visibly named `Compare` action commits the guess and opens the reveal.

### Play

- A three-second countdown starts the game.
- The color labeled `Target` fills the viewport for five seconds. The first
  round adds the single verb `Remember`.
- The target disappears; a stable `Guess` game case responds to the same wheel
  used by Match It and keeps its exact outer geometry through Reveal. The wheel
  is superimposed without splitting the color field into a separate control
  region.
- The first reconstruction adds `Match from memory`; that cue disappears after
  the first meaningful adjustment while stable role and action labels remain.
- The wheel is fully active on arrival, then becomes visually quiet after a
  completed input while keeping its full geometry.
  The next pointer, touch, or keyboard adjustment both reactivates and changes
  the value; no activation-only action is required.
- The visibly named `Compare` action commits the guess and names what appears
  next rather than describing storage mechanics.
- No reference or live HSB readout is shown.

### Picture It

- The screen names the immediate task once: `Choose the color`.
- The target is an HSB expression, not a swatch.
- Four color choices appear in a 2×2 grid.
- Choosing a color submits immediately.

### Call It

- The target occupies the dominant upper field and is explicitly labeled.
- A compact `Choose a name` tray offers eight XKCD color names as distinct
  typographic choices rather than an undifferentiated cell grid.
- Choosing a name submits immediately.
- The reveal identifies the canonical name and the player's choice.

### Split It

- The screen names the immediate task once: `Estimate HSB`.
- The target appears as a labeled swatch.
- Neutral sliders ask for H, S, and B independently.
- No composite preview or gradient answer cue is shown.
- The visibly named `Compare` action commits the estimate and opens the reveal.

## Picker

Play and Match It use one wheel. Initial value is `H180 S50 B50` for every color.

| Input | Pointer/touch | Keyboard |
| --- | --- | --- |
| Hue | Position around the outer ring | Left/right arrows on the hue ring |
| Saturation | Horizontal position in the inner field | Left/right arrows in the field |
| Brightness | Vertical position in the inner field | Up/down arrows in the field |

Shift increases the keyboard step. Hue and the combined saturation/brightness
field remain independent controls.

## Reveal

- Target and guess appear side by side.
- Score is shown out of 10 with a short verdict.
- Play, Match It, Picture It, Call It, Split It, and Reveal use the same
  `--game-stage-width` and `--game-stage-height` at a given viewport: up to
  980×720px on wider layouts and 980×760px on phone/narrow layouts, always
  constrained by available viewport space. The shared `--game-stage-inset`
  keeps the exact bounding box and center position stable. Pick → Reveal
  changes the content inside the stage, never the stage's outer geometry. The
  Play memory exposure remains immersive; reconstruction and Reveal occupy the
  same stable game case. The homepage embed remains edge-to-edge within its
  host-owned frame.
- Every mode uses the same reveal swatch split, outcome-band height, label
  positions, and navigation placement at a given viewport.
- Round progress is grouped with the score in the outcome band rather than
  competing with the Target and Guess labels on the color split.
- Continue advances to the next color; the Home control stays clear of both
  swatch labels and abandons the game.
- In full Play, the entire outcome band toggles the Target and Guess HSB
  comparison; the breakdown is hidden by default. The homepage embed omits
  this secondary detail.
- Split It reveals HSB comparison by default.
- Match It reveals Target and Guess HSB when the player opted into live values during the pick.

## Results

- Total score appears out of 50 with a tier.
- Five result cards summarize the round.
- A visible `Show breakdown` disclosure toggles advanced HSB comparison detail;
  result cards do not hide additional click-only behavior.
- Actions are visibly named: Menu, Again, Share.

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

`make check-stage-browser` starts the real application and verifies the rendered
Pick → Reveal geometry, screen focus ownership, inert inactive screens, return
paths, concise per-mode guidance, minimum return/disclosure targets, and Results
disclosure at desktop, narrow, and phone viewports.
