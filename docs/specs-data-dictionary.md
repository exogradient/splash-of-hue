---
title: Data Dictionary
description: Every analytics event and property — what, why, and privacy classification
stability: evolving
responsibility: Analytics telemetry schema and privacy guarantees
---

# Data Dictionary

Audit surface: `public/analytics.js`. Every event that leaves the client is defined there.

## Privacy Guarantees

**Never collected:**
- IP addresses (`ip: false` in PostHog config)
- Cookies or persistent identifiers (`persistence: 'memory'`)
- User agent, exact screen dimensions, language, timezone
- Email, name, account data (no accounts exist)
- Session recordings, heatmaps, DOM snapshots (`disable_session_recording: true`)
- Autocaptured clicks, pageviews, or page leaves (`autocapture: false`)

**Ephemeral identity:** Each page load gets a random PostHog `distinct_id` that is never persisted. No cross-session linking.

## Events

### `session_started`

Fires once on page load.

| Property | Type | Example | Purpose |
|---|---|---|---|
| `viewport_bucket` | string | `mobile` | Device class distribution |

### `game_started`

Fires when a new game begins (colors generated, round state reset).

| Property | Type | Example | Purpose |
|---|---|---|---|
| `mode` | string | `play` | Which game mode |
| `picker_type` | string | `field` | Which picker (or `none` for picture) |
| `viewport_bucket` | string | `tablet` | Device class at game start |
| `session_game_index` | int | `2` | How many games this page load (engagement depth) |

### `mode_transition`

Fires when a player starts a game in a different mode than their previous game.

| Property | Type | Example | Purpose |
|---|---|---|---|
| `from_mode` | string | `match` | Previous mode |
| `to_mode` | string | `play` | New mode — reveals learning progression patterns |

### `round_completed`

Fires after each of 5 color rounds is scored.

| Property | Type | Example | Purpose |
|---|---|---|---|
| `mode` | string | `play` | Game mode |
| `picker_type` | string | `sliders` | Picker used |
| `round_index` | int | `3` | Which round (0-4) |
| `score` | float | `7.42` | Round score (0-10) |
| `delta_e` | float | `8.3` | CIEDE2000 total distance |
| `delta_l` | float | `3.1` | Lightness error component |
| `delta_c` | float | `4.2` | Chroma error component |
| `delta_h` | float | `2.8` | Hue error component |
| `target_hue_region` | string | `Blue` | Hue family of target — reveals which colors are hardest |
| `target_h` | float | `220` | Target hue (0-360) |
| `target_s` | float | `75` | Target saturation (0-100) |
| `target_b` | float | `60` | Target brightness (0-100) |
| `memorize_duration_ms` | int/null | `5000` | Time in memorize phase (play mode only) |
| `pick_duration_ms` | int/null | `3200` | Time from pick screen to confirm |
| `picker_adjustment_count` | int | `14` | Pointer interactions before confirming |
| `picture_choice_index` | int/null | `2` | Which option tapped (picture mode only) |
| `picture_correct_index` | int/null | `0` | Position of correct answer — detects positional bias |

### `game_completed`

Fires when all 5 rounds finish.

| Property | Type | Example | Purpose |
|---|---|---|---|
| `mode` | string | `match` | Game mode |
| `picker_type` | string | `field` | Picker used |
| `total_score` | float | `38.5` | Sum of 5 round scores (0-50) |
| `round_scores` | float[] | `[7.4, 8.1, ...]` | Individual round scores |
| `total_duration_ms` | int | `45000` | Wall-clock game duration |
| `viewport_bucket` | string | `desktop` | Device class at completion |

### `game_abandoned`

Fires when a player leaves mid-game (back to menu).

| Property | Type | Example | Purpose |
|---|---|---|---|
| `mode` | string | `play` | Game mode |
| `picker_type` | string | `field` | Picker used |
| `rounds_completed` | int | `2` | How many rounds finished (0-4) |
| `abandoned_at_screen` | string | `memorize` | Which phase they left |
| `elapsed_ms` | int | `12000` | Time since game started |

### `picker_switched`

Fires when picker type changes.

| Property | Type | Example | Purpose |
|---|---|---|---|
| `from_picker` | string | `field` | Previous picker |
| `to_picker` | string | `sliders` | New picker |
| `during_game` | bool | `true` | Whether switch happened mid-game |

## Derived Metrics

These are computed in PostHog from the raw events above:

| Metric | Formula |
|---|---|
| Completion rate | `game_completed` / `game_started`, grouped by mode |
| Hardest hue region | Average `score` grouped by `target_hue_region` |
| Picker preference | `game_started` count by `picker_type` |
| Score by picker | Average `total_score` grouped by `picker_type` |
| Session depth | Max `session_game_index` per session |
| Abandon point | `abandoned_at_screen` distribution |
| Pick speed vs accuracy | Scatter of `pick_duration_ms` vs `score` |
| Channel weakness | Which of `delta_l/c/h` contributes most to low scores |
| Positional bias | `picture_choice_index` distribution vs `picture_correct_index` |
