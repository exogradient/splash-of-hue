---
title: Project Context
description: External context — why this project exists, philosophy, competitive landscape
stability: stable
responsibility: Why the product exists and what shaped it — vision, philosophy, competitive positioning
---

# splash of hue — Project Context

## Vision

A color memory game that **teaches** color perception, not just tests it. The goal is to help players build real understanding of color — hue, saturation, brightness — so they improve through insight, not grinding.

## Early Development Philosophy

- **Dogfood first.** Build fast, play it, learn from what actually happens.
- **Evidence over design.** Don't pre-architect features. Let data and experience drive decisions.
- **Iterate fast.** Everything is disposable. Shortcuts are encouraged if they accelerate learning.

## Dialed.gg Product Study

**What it does:** Show one color full-screen for 5s (2s hard) — countdown styled as "**5**00" — then recreate from memory using HSB sliders. Repeat 5 times. Scored via sigmoid on CIELAB Delta E with hue accuracy bonuses and saturation weighting, 0-10 per color, 50 max.

**Design identity:** Minimal digital brutalism. Black chrome, white type (Suisse Intl S Alt), full-bleed color immersion during memorization — zero visual noise competing with the target color. Sparse layout with generous negative space. Motion is restrained but intentional: ripple effects on buttons, chromatic-aberration shake on transitions, kinetic number slides on the countdown. Mobile-first full-screen overlays; desktop adds a centered 476px card with shadow.

**Design insights:**
- **Full-bleed memorization** — removing all chrome during the memorize phase forces pure perceptual encoding. No swatches, no grid, no reference points. Just you and the color filling your entire viewport.
- **Typographic countdown as tension device** — "**5**00" uses weight contrast within a single numeral. It's kinetic typography doing double duty: communicating time *and* building pressure through visual rhythm.
- **Scoring copy as personality** — brutal, sarcastic feedback ("Did you even look at the screen?", "The participation ribbon of color memory") reframes failure as entertainment. Makes repeated play feel low-stakes and addictive rather than punishing.
- **Vertical strip sliders** — HSB channels as separate linear strips, not a 2D field. Decomposes the color-matching task into three independent decisions. Lower cognitive load per interaction but requires the player to mentally compose the result.
- **Hue-weighted scoring** — the sigmoid isn't pure Delta E. Hue accuracy within ~25° recovers up to 40% of lost points; missing hue by >40° incurs penalties scaled by saturation. This matches human perception: we notice hue shifts more than saturation/brightness drift, especially in chromatic colors.

**What we're keeping from dialed.gg:**
- Core mechanic: memorize one color, recreate from memory, repeat
- CIELAB Delta E scoring (perceptually accurate)
- 5 colors per round
- Full-screen color immersion during memorization
- Sparse, focused UI that stays out of the way
