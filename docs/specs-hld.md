---
title: High-Level Design
description: Technical architecture — deployment, API contracts, data model, key behaviors
stability: evolving
responsibility: Backend architecture and infrastructure decisions
---

# High-Level Design

## Deployment

Vercel serverless. Python function at `api/app.py`, static files from `public/` served by Vercel CDN. Framework detection disabled (`"framework": null` in `vercel.json`) so rewrites take full control.

`vercel.json` rewrites:
- `/` → `/index.html` (CDN-served, no function invocation)
- `/api/*` → `api/app.py` (serverless function, FastAPI catch-all)

## Game Flow (client-driven)

```mermaid
sequenceDiagram
    participant C as Client
    participant S as Server
    participant DB as Database

    C->>C: generate 5 colors (+choices for picture)

    loop 5 rounds
        C->>C: memorize → pick → reveal (target vs guess + score)
    end

    C->>S: POST /api/game/submit {targets, guesses, scores, ...}
    S->>DB: INSERT completed game
    S-->>C: {ok: true}
```

Client generates colors and scores locally — no server round-trip to start a game. Server is append-only persistence for analytics.

## API Contracts

**POST /api/game/submit**
- Request: `{ target_colors: [{h,s,b} x5], guesses: [{h,s,b} x5], scores: [float x5], total_score: float, mode, picker_type }`
- Response: `{ ok: true }`
- Persists pre-scored results. No server-side scoring — client owns CIEDE2000 computation.
- Server-side scoring returns in Phase 3 (challenges) for competitive truth.

**GET /api/history** — removed. Personal history lives in localStorage. Endpoint returns in Phase 2 as a leaderboard.

## Database

**Now:** `/tmp/games.db` (SQLite) — ephemeral, works within warm serverless instances. History may be lost on cold starts. Acceptable because history is not a core feature yet.

**Next:** Turso (LibSQL) — persistent, SQLite-compatible, edge-distributed. Drop-in replacement when persistence matters.

**Schema (current):**

```sql
CREATE TABLE games (
    id TEXT PRIMARY KEY,
    created_at TEXT,
    mode TEXT,
    picker_type TEXT,
    target_colors TEXT,  -- JSON [{h,s,b}]
    guesses TEXT,        -- JSON [{h,s,b}]
    scores TEXT,         -- JSON [float]
    total_score REAL
);
```

**Schema evolution** (see `design-log` for rationale):

```mermaid
graph LR
    A["Phase 1: games"] --> B["Phase 2: + display_name column"]
    B --> C["Phase 3: + challenges table\ngames.challenge_id FK"]
```

- **Phase 1 (now):** Anonymous solo games
- **Phase 2 (leaderboards):** Display name (pseudonym) submitted with score. No accounts — name stored in localStorage, freely changeable. Server stores name as a plain field on the game row, not a FK.
- **Phase 3 (multiplayer):** Shared challenges store target colors server-side, linking multiple game attempts. Display name prompted at join time. Restores server-side truth for competitive scoring while solo play stays stateless.

## Telemetry

Client-side only, via PostHog JS SDK. No server-side analytics.

**Audit surface:** `public/analytics.js` — single file defines every event. Nothing else sends data.

**Privacy config:** `autocapture: false`, `ip: false`, `persistence: 'memory'` (no cookies/localStorage for PostHog), `disable_session_recording: true`. Each page load gets an ephemeral anonymous ID — no cross-session linking.

**Events:** `session_started`, `game_started`, `mode_transition`, `round_completed`, `game_completed`, `game_abandoned`, `picker_switched`. Full schema in `docs/specs-data-dictionary.md`.

**Failure mode:** If PostHog SDK is blocked (ad blocker, network), all calls are silent no-ops. Game functionality is unaffected.

## Key Behaviors

- **No lifespan hooks.** Vercel doesn't fire ASGI lifespan events. DB initialization is lazy (on first write).
- **Refresh resets.** In-progress games exist only in client JS memory. Refresh returns to menu. No orphan state in DB.
- **Graceful DB failure.** If DB write fails on submit, the game already worked — client scored locally. Only history persistence is lost.
