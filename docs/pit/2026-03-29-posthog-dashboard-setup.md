---
title: PostHog Dashboard Setup
date: 2026-03-29
---

# PostHog Dashboard Setup

Setup guide for the Alpha Analytics dashboard. All events are defined in `public/analytics.js`.

## Dashboard: Alpha Analytics

Create a new dashboard in PostHog (Dashboards > New), then add these insights.

### 1. Completion Rate by Mode

- **Type:** Funnel
- **Steps:** `game_started` → `game_completed`
- **Breakdown:** `mode`
- **Reads:** Are people finishing games? Which mode has the most drop-off?

### 2. Hardest Hue Region

- **Type:** Trends
- **Event:** `round_completed`
- **Aggregation:** Average of `score`
- **Breakdown:** `target_hue_region`
- **Reads:** Which color families are hardest? Informs difficulty curve and feedback messages.

### 3. Score by Picker Type

- **Type:** Trends
- **Event:** `game_completed`
- **Aggregation:** Average of `total_score`
- **Breakdown:** `picker_type`
- **Reads:** Field vs sliders performance gap. Informs default picker choice.

### 4. Pick Speed vs Accuracy

- **Type:** Trends (two series)
- **Series A:** `round_completed`, average `pick_duration_ms`
- **Series B:** `round_completed`, average `score`
- **Reads:** Do fast picks score better (instinct) or worse (rushed)? Informs timer design.

### 5. Abandon Points

- **Type:** Trends
- **Event:** `game_abandoned`
- **Breakdown:** `abandoned_at_screen`
- **Reads:** Where do people quit? Memorize (too long/stressful), pick (too hard), reveal (bored)?

### 6. Session Depth

- **Type:** Trends
- **Event:** `game_started`
- **Aggregation:** Max of `session_game_index`
- **Reads:** How many games per visit? Engagement signal.

### 7. Positional Bias (Picture mode)

- **Type:** Trends
- **Event:** `round_completed`
- **Filter:** `mode` = `picture`
- **Breakdown:** `picture_choice_index`
- **Reads:** Do players favor a particular position regardless of correctness? If so, shuffle logic may need adjustment.

### 8. Channel Weakness

- **Type:** Trends (three series)
- **Series A:** `round_completed`, average `delta_l` (lightness error)
- **Series B:** `round_completed`, average `delta_c` (chroma error)
- **Series C:** `round_completed`, average `delta_h` (hue error)
- **Reads:** Which perceptual channel drifts most? Validates whether Match It/Call It/Split It target the right skills.

### 9. Mode Transitions

- **Type:** Trends
- **Event:** `mode_transition`
- **Breakdown:** `to_mode`
- **Reads:** Do players progress from easier modes to harder ones? Reveals natural learning path.

### 10. Viewport Distribution

- **Type:** Trends
- **Event:** `session_started`
- **Breakdown:** `viewport_bucket`
- **Reads:** Mobile vs tablet vs desktop split. Prioritizes which layout to polish first.
