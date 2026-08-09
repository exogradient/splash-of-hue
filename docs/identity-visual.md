---
title: Visual Identity
description: Design principles and interaction standards for splash of hue
stability: stable
responsibility: Visual language, interaction principles, and quality bar
---

# Visual Identity

## North star

**The game is the interface.** Color should feel immediate, physical, and worth studying. Everything around it should become quiet.

The quality bar comes from the restraint of Rauno Freiberg, the interaction precision of Emil Kowalski, and the editorial clarity of Paco Coursey. Their work is a standard, not a style kit.

The shipped game is the comparison control. A proposed change must name a demonstrated problem and outperform the current interaction directly.

## Principles

### 1. Color is content

Gameplay chrome is achromatic. Saturated color belongs to targets, guesses, choices, and the home deck—not generic controls or decoration.

### 2. Teach through interaction

The picker should explain HSB through movement. Feedback should begin with a visual comparison. Labels and values appear only when they improve learning.

### 3. Progressive disclosure must feel native

Advanced detail lives on the surface it explains. In Match It, pressing the comparison swatch reveals live HSB values; it does not add a permanent pill, panel, or settings row.

### 4. Restraint is a feature

Every visible element must help the player choose, compare, commit, or continue. Remove numbering, helper copy, labels, and containers that do not change an action.

### 5. Precision compounds

Alignment, hit targets, focus, contrast, motion timing, and color truth are product behavior. A picker handle must show the same color as the guess. A ring must complete its full circumference.

### 6. One system across sizes

Mobile and desktop use the same hierarchy, reflowed—not separate designs. Mobile is the stricter contract: safe areas, short viewports, touch targets, and no horizontal overflow.

## Home

The home screen is a paint-chip deck:

- **Play** is the large parchment cover and brand surface.
- **Match It**, **Picture It**, **Call It**, and **Split It** are chromatic tabs.
- Mobile stacks tabs below the cover; desktop fans them to the right.
- Mode icons are cues, not illustrations. Labels align to one optical system.
- Sequence numbers and explanatory subtitles are omitted.

The deck should feel like one object. Avoid disconnected cards, dashboards, grids, and ornamental backgrounds.

## Picker

The current owner-selected implementation candidate is under final product
review; it is shipped truth for this branch, not yet a promoted durable identity
rule. Play and Match It use one full-spectrum HSB control:

- The outer 360° ring controls **hue**.
- The inner circular field controls **saturation** horizontally and
  **brightness** vertically.
- A reversible square-to-disc mapping keeps every saturation/brightness pair
  reachable without introducing a second picker shape.
- Both handles use the exact current guess color.
- Hue and the saturation/brightness field remain independent for pointer,
  touch, and keyboard input.
- The ring and inner field meet without a permanent separator contour. Handles
  explain the geometry; a field outline appears only for keyboard focus.
- In Play, the control is superimposed on the Guess field and becomes visually
  quiet after input without moving, shrinking, or requiring an activation-only
  gesture.
- In Match It, Guess is likewise the instrument's working surface. Target stays
  visible as the fixed reference beside it on wider layouts and as a shallow
  reference strip on phone; a separate dark picker panel is prohibited.

The prior angle/radius hue-saturation disc with a brightness ring remains the
comparison control and reversal candidate until the owner completes this final
review.

The wheel is a learning object, not a decorative color wheel. Never combine unrelated square and circular models, truncate the value ring, or display a handle color that disagrees with the guess.

Split It deliberately uses neutral channel sliders because seeing the composite color would answer the exercise.

## Type and copy

- Plus Jakarta Sans carries product UI and scores.
- Instrument Serif italic is reserved for the `splash of hue` wordmark.
- Labels are short, literal, and sentence-free where possible.
- Use `Target` and `Guess`; avoid possessive or instructional variants.
- Render those role labels in one title-case typographic system across Play,
  Match It, and Reveal; do not fall back to tiny tracked uppercase metadata.
- Name outcome-specific actions (`Compare`, `Next`, `Results`) in text. Reserve
  standalone icons for familiar persistent navigation such as Home.
- Numerical detail uses tabular alignment and appears only when earned.

## Surfaces and spacing

- Near-black background; neutral gray hierarchy.
- One primary card radius and one compact control radius.
- Hairline borders and restrained elevation separate layers.
- Controls attach to the surface they act on.
- Prefer negative space to extra panels.
- Use optical centering for icons and vertical labels; do not rely on mathematical centering alone.

## Motion

Motion communicates state change:

- Fast control response: about 150ms.
- Screen and card transitions: 200–300ms.
- Prefer opacity and transform; avoid layout animation.
- No ambient motion during color judgment.
- Reduced motion preserves state clarity without travel or spring effects.

## Accessibility

- Pointer, touch, and keyboard paths are first-class.
- Visible focus uses a deliberate high-contrast ring.
- Interactive targets are at least 44px where layout permits.
- `--control-hit`, `--focus-ring`, and `--focus-ring-offset` are the shared
  control contracts; local screen styling must not silently shrink or replace
  them.
- Color is never the only indicator of role or state.
- Only the active screen remains in the focus order. Screen transitions move
  focus to the new task or outcome; returning restores the initiating mode.
- Custom controls expose truthful names, values, and independent semantics.
- Light swatches switch label ink for readable contrast.

## Anti-patterns

- Explanatory text that compensates for unclear interaction.
- Permanent controls for optional information.
- Decorative gradients outside color-learning surfaces.
- Floating actions detached from their card.
- Multiple picker models or picker-choice settings.
- Hardware-like knobs, incomplete rings, and loading-spinner symbolism.
- Desktop layouts that merely center a mobile card in empty space.
- Styling that changes native button geometry without restoring focus and hit behavior.
