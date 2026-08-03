---
title: Data Dictionary
description: The explicit telemetry contract and its privacy boundary
stability: evolving
responsibility: Analytics event schema, meanings, and privacy guarantees
---

# Data Dictionary

`public/analytics.js` is the audit surface. No other client file sends telemetry.

## Privacy

Never collect names, email, accounts, IP addresses, exact viewport dimensions, user agents, cookies, persistent analytics identifiers, DOM recordings, or autocaptured interactions.

PostHog identity lives in memory for one page load. Challenge display names are sent only to challenge APIs; they are not analytics properties.

`/?embed=play` emits no analytics events, so one-round homepage encounters do
not contaminate five-round game funnels or session-depth measures.

## Common values

- `mode`: `play | match | picture | call | split`
- `picker_type`: `wheel | split | none`
- `viewport_bucket`: `mobile | tablet | desktop`
- `round_index`: `0..4`
- `score`: `0..10`
- `total_score`: `0..50`

## Events

### `session_started`

Page-load signal with `viewport_bucket`.

### `game_started`

`mode`, `picker_type`, `viewport_bucket`, `session_game_index`.

### `mode_transition`

Emitted when consecutive games use different modes: `from_mode`, `to_mode`.

### `round_completed`

One event per scored color:

- context: `mode`, `picker_type`, `round_index`;
- outcome: `score`, `delta_e`, `delta_l`, `delta_c`, `delta_h`;
- target: `target_hue_region`, `target_h`, `target_s`, `target_b`;
- effort: `memorize_duration_ms`, `pick_duration_ms`, `picker_adjustment_count`;
- choice modes: `picture_choice_index`, `picture_correct_index`;
- Call It: `call_chosen_name`, `call_correct_name`.

Choice and mode-specific properties are `null` when irrelevant.

### `game_completed`

`mode`, `picker_type`, `total_score`, `round_scores`, `total_duration_ms`, `viewport_bucket`.

### `game_abandoned`

Emitted once when an active game returns to Home: `mode`, `picker_type`, `rounds_completed`, `abandoned_at_screen`, `elapsed_ms`.

## Derived questions

The event set should answer:

- Where do players abandon?
- Which modes start, complete, and lead to another mode?
- Which mode and hue regions are hardest?
- Does speed trade off with accuracy?
- Which perceptual channel dominates error?
- Are Picture It choices position-biased?
- Which viewport buckets dominate actual use?
- Does session depth or repeat practice improve scores?

Do not add an event until it answers a product question that cannot be answered from this contract.
