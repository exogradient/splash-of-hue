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
| **Perception** | Chromatic discrimination | Detecting small color differences across hue, saturation, and lightness. Non-uniform across color space — threshold varies by region. Training is hue-specific: improving discrimination in blue-green does not transfer to red-orange |
| **Encoding** | Color appearance scaling | Consciously decomposing a perceived color into HSB parameters. Research shows untrained observers perceive color holistically — dimensional decomposition is a genuinely difficult learned skill |
| **Decoding** | Color visualization | HSB parameters → predicting the color. Encoding's inverse — mentally simulating what a parametric description looks like |
| **Retention** | Delayed reproduction | Holding a perceived color in working memory across a delay. The full pipeline is encode → maintain → retrieve; the maintenance phase is the bottleneck. During the delay, color memories drift toward category prototypes ("blue", "green") — parametric encoding counteracts this drift |
| **Context** | Simultaneous contrast awareness | Recognizing when surrounding colors shift perceived appearance. Core of Albers' *Interaction of Color* curriculum |

### Adjacent skills

Not targeted by the game but relevant to the landscape:

| Skill | Scientific basis | Relation |
|-------|-----------------|----------|
| **Categorization** | Categorical color perception | Parallel to Encoding — coarser (discrete labels vs continuous parameters) but faster. Vocabulary expansion literally shifts discrimination at category boundaries (Sapir-Whorf). Name It mode trains this. Labels also anchor Retention — they resist decay where metric details fade |
| **Color mixing** | Subtractive/additive synthesis | Predicting results of combining colors. Requires Encoding + Decoding + material knowledge. Different domain — empirical, not parametric |
| **Color harmony** | Color combination aesthetics | Evaluative, not perceptual. Empirical evidence for traditional rules (complementary, triadic) is weaker than assumed. Engagement feature, not a training target |

## Modes

Each mode **emphasizes** a skill — not pure isolation (that gets clinical), but the design minimizes confounds for the skill you're training.

| Mode | Status | Primary skill | What's minimized | How |
|------|--------|--------------|-----------------|-----|
| **Play** | Shipped | Integrated (all) | Nothing — full chain | Memorize 5s → hidden → recreate. Retention is the differentiating constraint vs Match, not the primary skill |
| **Match** | Shipped | Perception | Retention, encoding (both visible) | Target and guess shown side-by-side, converge by eye |
| **Name It** | Idea | Encoding (vocabulary) | Picker, visual feedback (commit before seeing answer) | See color → pick its name from choices (cerulean, burnt sienna, etc.) → reveal correct name + HSB values. Builds color vocabulary |
| **Read It** | Idea | Encoding (parametric) | Picker, visual feedback (commit before seeing answer) | See color → classify into HSB range buckets (e.g. warm/cool, high/low sat) → reveal answer + color name. Difficulty scales from coarse buckets to narrow ranges |
| **Picture It** | Shipped | Decoding | Perception, picker (multiple choice) | Given HSB values → pick the matching color from choices → reveal answer. Encoding's inverse |
| **Judge It** | Idea | Context | Perception (confound is surround, not delta-E) | Target on neutral background → pick the match from 4 swatches on a colored surround → reveal strips backgrounds to show true colors. Difficulty scales from strong surrounds + spread choices to subtle surrounds + close choices to no neutral reference |
| **Explore** | Idea | None (engagement) | Everything (not scored) | Color + topic → image search |
