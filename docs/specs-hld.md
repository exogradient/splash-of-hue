---
title: High-Level Design
description: Runtime architecture, persistence, APIs, and failure boundaries
stability: evolving
responsibility: Backend architecture and hardened infrastructure contracts
---

# High-Level Design

## Shape

```text
Browser
├── static game UI and local scoring
├── localStorage history
├── PostHog telemetry
└── FastAPI
    ├── append completed games
    ├── create and join challenges
    └── local-only calibration support
```

The browser owns the game loop. It generates targets, records guesses, computes scores, renders feedback, and stores local history. A network failure must not prevent play.

## Runtime

- Static product files: `public/`.
- API: `api/app.py` with FastAPI.
- Local development: `make dev`; FastAPI also serves `public/`.
- Production: Vercel serves static files and routes API/deep-link requests to FastAPI.
- Python: 3.13+, managed with `uv`.

## Persistence

### Completed games

One append-only row per completed game: mode, picker type, targets, guesses, round scores, and total score.

- Local: `data/games.db`.
- Vercel: `/tmp/games.db`, intentionally ephemeral.
- Failure is non-blocking; the client already completed the game.

### Challenges

Challenges store a mode, five targets, and up to 20 named entries.

- Local: `data/challenges.db`.
- Production: Turso when `TURSO_DATABASE_URL` and `TURSO_AUTH_TOKEN` are configured.
- Serverless SQLite fallback is ephemeral and unsuitable for production sharing.

Display names are challenge-scoped pseudonyms, not identities. Scores are client-submitted and therefore not competitive truth.

## Public API

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/game/submit` | Append a completed solo game. |
| `POST` | `/api/challenge` | Create a challenge and creator entry. |
| `GET` | `/api/challenge/{code}` | Fetch targets and leaderboard. |
| `POST` | `/api/challenge/{code}` | Submit a challenge entry. |
| `GET` | `/c/{code}` | Serve challenge-aware social metadata and hand off to the app. |

Challenge codes use six-character Crockford Base32. Input is uppercased, dashes removed, and ambiguous `I/L/O` characters normalized. Names are 1–20 characters and unique within a challenge.

## Trust boundaries

- Gameplay and scoring are client-controlled.
- The game persistence endpoint is best-effort.
- Challenge storage trusts submitted guesses, scores, and totals.
- Production challenges require Turso for shared persistence.
- PostHog is optional and must fail silently.
- Local calibration endpoints reject non-local requests.

## Telemetry

`public/analytics.js` is the only telemetry surface. PostHog uses explicit events, memory-only identity, no autocapture, no session recording, and no IP processing. See `specs-data-dictionary.md`.

## Release invariants

- The game starts and scores without the server.
- Refresh discards an unfinished round.
- Homepage embed sessions are one-round, self-contained, and non-persistent.
- Scorer copies remain byte-identical across runtime and calibration tools.
- Database initialization is lazy; no ASGI lifespan dependency.
- Challenge storage errors are visible; solo persistence errors are not gameplay errors.
