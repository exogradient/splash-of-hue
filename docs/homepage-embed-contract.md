---
title: Exogradient homepage embed contract
description: Product-owned boundary for embedding one real Splash of Hue round
stability: evolving
responsibility: Homepage embed behavior and integration constraints
updated: 2026-08-08
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
- the full-spectrum HSB wheel used by Play, with hue on the outer ring and a
  saturation/brightness inner field;
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
- Every Play state fills the same iframe bounds; Target, Guess, and Reveal may
  not expose a transparent remainder or change the outer panel geometry.
- Countdown supplies its own neutral, high-contrast surface; it cannot inherit
  a host canvas that makes the transition unreadable.
- Adapt within the viewport rather than exposing a nested scrollbar.
- Preserve usable control sizes at the homepage desktop footprint and at a
  390-pixel mobile width.
- Keep the surrounding UI perceptually neutral so it does not bias the task.
- Do not reserve space for controls or copy excluded from embed mode.
- Focus changes inside the game must not move the host page.
- Target and Reveal role labels share one header alignment with their return
  control at phone, split-pane, and desktop widths.

## Completion behavior

After the embed initializes its real Play round, it emits a versioned `ready`
phase with the bounded kind `play`. The host uses this product-owned signal—not
an iframe load event—to replace loading treatment or disclose an unavailable
state when readiness never arrives.

Because the iframe can finish loading before the host installs its message
listener, readiness is a two-way handshake rather than a one-shot event. The
host sends a privacy-minimal `exogradient:splash-host` version 1
`probe`/`ready` message immediately after installing its listener and again on
iframe `load`. The embed accepts the probe only from `window.parent`, validates
the parent origin against `document.referrer` when available, and replies with
the product-owned `ready`/`play` signal above. The host must never treat iframe
`load` alone as product readiness.

After reveal, the visitor may replay within the miniature. Navigation to the
full game remains a host-owned affordance outside the iframe, so gameplay and
page navigation do not compete for space.

Comprehension is owned by Splash and built into the game surfaces. Memorize
names the presented color `Target`; reconstruction names the live swatch
`Guess` and visibly names the outcome action `Compare`; reveal preserves
`Target` / `Guess` and visibly names the next action. These are stable game
semantics, not an instruction panel or first-use coach. A host-authored overlay
over the round is prohibited, and labels never intercept input.

The first round adds one short verb to each state: `Remember` under Target and
`Match from memory` under Guess. The Guess cue disappears after the first
meaningful instrument adjustment; stable role and action labels remain.
Reconstruction keeps one uninterrupted Guess field with the instrument
superimposed. The instrument is fully active and discoverable on arrival. Only
after a completed adjustment may it become visually quiet; it must retain its
full geometry and resume on the same gesture that changes the value. Reveal
presents equal Target and Guess fields immediately.

After a completed pointer or keyboard adjustment of the color controls, the
embed posts a versioned `exogradient:splash-engagement` message to its parent.
Iframe focus alone does not establish comprehension.
Locked guesses retain their own richer interaction kind but are not considered
an invitation to enlarge the experience. The message contains no color, score,
identity, or session data. Hosts may use it to acknowledge attention, but must
not move the embed during an active gesture.

When Escape is not consumed by an embed-owned disclosure or sheet, the same
message uses the `dismiss` phase so the host can restore its collection view
even while keyboard focus remains inside the cross-origin frame.

A deliberate wheel gesture also emits `dismiss` with a clamped vertical delta,
allowing the host to restore the collection and preserve the visitor's scroll
direction without exposing gameplay state.

Embed sessions do not write a completed game or enter normal history. Existing
privacy-safe analytics may distinguish the embed surface, but analytics must
not enter the interaction's critical path.

## Quality gate

The embed advances only when it remains recognizably the shipped Play loop and
feels complete at miniature scale. The current full game is the comparison
control. Simplification alone is not an improvement.
