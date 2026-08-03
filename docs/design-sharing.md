---
title: Challenge Sharing Design
description: Storage, trust boundaries, and failure policy for shared challenges
stability: evolving
responsibility: Challenge-sharing rationale, risk boundaries, and evolution path
---

# Challenge Sharing Design

## Product contract

A player can turn a completed game into a challenge. The code preserves the mode and five target colors; other players replay them and join a small leaderboard.

Sharing is casual competition. There are no accounts, durable identities, or anti-cheat guarantees.

## Principles

1. **Gameplay stays local.** Creating or joining a challenge must not change the scoring loop.
2. **A code is an address, not a secret.** It identifies a challenge but grants no protected access.
3. **Names are scoped.** A display name is unique only within one challenge.
4. **Persistence must be explicit.** Production sharing requires shared storage; serverless `/tmp` is not a database.
5. **Trust matches stakes.** Client-submitted scores are acceptable for friendly play, not global competition.

## Flow

### Create

1. Finish a game and press Share.
2. Enter a display name.
3. `POST /api/challenge` stores mode, targets, and creator entry.
4. The server returns a six-character Crockford Base32 code and leaderboard.
5. The player copies the code or challenge link.

### Join

1. Open a challenge link or resolve its code.
2. `GET /api/challenge/{code}` returns mode, targets, and leaderboard.
3. Play the same five colors.
4. Enter a display name.
5. `POST /api/challenge/{code}` adds the entry and returns the updated leaderboard.

## Storage

| Environment | Backend | Contract |
| --- | --- | --- |
| Local | `data/challenges.db` | Durable developer data. |
| Vercel with Turso | Turso HTTP API | Durable shared production data. |
| Vercel without Turso | `/tmp/challenges.db` | Ephemeral fallback; not production-ready. |

Turso fits the current system because it preserves SQLite semantics, works over stateless HTTP, and adds no runtime SDK. Reconsider when accounts, row-level authorization, real-time updates, or large global ranking become committed needs.

## Data

Challenges store:

- code, mode, target colors, timestamps;
- entry id, display name, guesses, scores, total, timestamp.

They do not store accounts, email, auth tokens, device identity, or analytics identifiers.

## Trust and abuse boundaries

- The server trusts client-submitted guesses and scores.
- Anyone with a code can read and submit to its leaderboard.
- Names can be squatted; the same person can use different names.
- Maximum entries: 20.
- Maximum name length: 20 characters.
- Duplicate names within one challenge return `409`.
- Output must remain escaped as text; never interpolate a name as HTML.

Server-side score validation is required before daily or global competition. Authentication and moderation are required before identity has durable value.

## Failure policy

| Failure | Behavior |
| --- | --- |
| Turso missing in production | Treat sharing as misconfigured; `/tmp` cannot satisfy the contract. |
| Unknown code | `404`. |
| Duplicate name or full challenge | `409` with a useful message. |
| Storage unavailable | Keep the completed local game; show that sharing failed. |
| Code collision | Retry generation; primary-key uniqueness is authoritative. |
| Malformed code | Normalize case, dashes, and ambiguous Crockford characters before lookup. |

## Security posture

Current data is low-sensitivity casual game data, but the endpoints are still public write surfaces. Add rate limiting and server-side score validation before broad distribution. Reclassify the system before adding accounts or linkable personal history.

## Evolution triggers

- **Daily challenge:** durable target schedule and server score validation.
- **Global leaderboard:** authenticated identity, moderation, pagination, and anti-abuse controls.
- **Real-time competition:** a stateful update channel instead of polling.
- **Accounts:** explicit privacy, deletion, authorization, and migration design.
