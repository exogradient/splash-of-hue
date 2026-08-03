---
title: Exogradient homepage embed contract
description: Product-owned boundary for embedding one real Splash of Hue round
stability: evolving
responsibility: Homepage embed behavior and integration constraints
updated: 2026-08-03
---

# Exogradient homepage embed contract

Splash of Hue owns the playable surface used by the Exogradient homepage. The
site may frame and link around it, but it must not clone, crop, or reinterpret
the game mechanics.

## Entry point

`/?embed=play` renders a compact Play encounter based on the shipped memorize,
reconstruct, and reveal loop.

Normal routes and the default `/?` experience remain unchanged. Embed mode is
an explicit product surface, not responsive CSS accidentally hiding the menu.

## Included

- one complete color-memory round;
- the full-spectrum HSB wheel used by Play;
- target presentation, reconstruction, and visual reveal;
- the minimum state feedback needed to understand the loop;
- keyboard and touch operation; and
- reduced-motion behavior.

## Excluded

- the mode menu and its paint-chip stack;
- global product navigation;
- results history, advanced analysis, or multi-round totals;
- a redundant one-round counter or optional HSB disclosure on reveal;
- persistence or submission as a completed full game;
- homepage title, outbound arrow, and editorial framing; and
- shallow replacement interactions or decorative color cycling.

## Layout contract

- Fill the iframe viewport without internal page scrolling.
- Adapt within the viewport rather than exposing a nested scrollbar.
- Preserve usable control sizes at the homepage desktop footprint and at a
  390-pixel mobile width.
- Keep the surrounding UI perceptually neutral so it does not bias the task.
- Do not reserve space for controls or copy excluded from embed mode.
- Focus changes inside the game must not move the host page.

## Completion behavior

After reveal, the visitor may replay within the miniature. Navigation to the
full game remains a host-owned affordance outside the iframe, so gameplay and
page navigation do not compete for space.

Embed sessions do not write a completed game or enter normal history. Existing
privacy-safe analytics may distinguish the embed surface, but analytics must
not enter the interaction's critical path.

## Quality gate

The embed advances only when it remains recognizably the shipped Play loop and
feels complete at miniature scale. The current full game is the comparison
control. Simplification alone is not an improvement.
