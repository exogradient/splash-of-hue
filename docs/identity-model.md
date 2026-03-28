---
title: Product Model
description: Internal structure — skill decomposition, modes, and game mechanics
stability: stable
responsibility: What the product is structurally — skills, modes, and why each exists
---

# Product Model

## Skills

Color matching decomposes into separable skills:

| Skill | Scientific basis | What it is |
|-------|-----------------|-----------|
| **Perception** | Chromatic discrimination | Detecting small color differences across hue, saturation, and lightness. Non-uniform across color space — threshold varies by region |
| **Encoding** | Color appearance scaling | Consciously decomposing a perceived color into HSB parameters. Research shows untrained observers perceive color holistically — dimensional decomposition is a genuinely difficult learned skill |
| **Decoding** | Color visualization | HSB parameters → predicting the color. Encoding's inverse — mentally simulating what a parametric description looks like |
| **Retention** | Delayed reproduction | Holding a perceived color in working memory across a delay. The full pipeline is encode → maintain → retrieve; the maintenance phase is the bottleneck |

## Modes

Each mode **emphasizes** a skill — not pure isolation (that gets clinical), but the design minimizes confounds for the skill you're training.

| Mode | Status | Primary skill | What's minimized | How |
|------|--------|--------------|-----------------|-----|
| **Play** | Shipped | Integrated (all) | Nothing — full chain | Memorize 5s → hidden → recreate. Retention is the differentiating constraint vs Match, not the primary skill |
| **Match** | Shipped | Perception | Retention, encoding (both visible) | Target and guess shown side-by-side, converge by eye |
| **Name It** | Idea | Encoding (vocabulary) | Picker, visual feedback (commit before seeing answer) | See color → pick its name from choices (cerulean, burnt sienna, etc.) → reveal correct name + HSB values. Builds color vocabulary |
| **Read It** | Idea | Encoding (parametric) | Picker, visual feedback (commit before seeing answer) | See color → classify into HSB range buckets (e.g. warm/cool, high/low sat) → reveal answer + color name. Difficulty scales from coarse buckets to narrow ranges |
| **Dial It In** | Idea | Decoding | Perception, picker (multiple choice) | Given HSB values → pick the matching color from choices → reveal answer. Encoding's inverse |
| **Explore** | Idea | None (engagement) | Everything (not scored) | Color + topic → image search |
