---
title: Design Log
description: Decisions and dogfooding — how the design evolves through use
stability: evolving
responsibility: Design decisions and dogfooding observations
---

# Design Log

## Decisions

- **2026-03-29** — HSB slider visualization for power users. Three gradient bars (H/S/B) with dual pins (target = solid white, guess = translucent) showing where each value landed. Used on both the Reveal screen (tap score to toggle) and Results cards (advanced view). Replaces raw ΔL'/ΔC'/ΔH' delta bars — same information but in the HSB mental model the player actually thinks in.
- **2026-03-29** — Picture It mode: click-to-submit. Selecting a choice immediately confirms — no separate confirm button. Reduces tap count and removes wasted button real estate.
- **2026-03-29** — Picture It target is HSB text, not a swatch. The text IS the game mechanic — Decoding skill means reading "H210 S80 B60" and mentally constructing the color. Showing a swatch would reduce it to a trivial color-matching exercise. See `identity-model` Decoding skill.
- **2026-03-29** — Scoring curve tightened: k=20 → k=12 in sigmoid `10 / (1 + (ΔE/k)^2.5)`. Original curve was too generous — ΔE 7.5 (clearly visible purple/magenta difference) scored 9.2. With k=12, same case scores 7.6. Tier thresholds adjusted: 42/35/25/15 (was 47/40/32/22).
- **2026-03-29** — Hue-recovery bonus added. CIEDE2000 weights hue ~1.86x over chroma for saturated colors but treats lightness equally. Research in `pit/2026-03-28-scoring-algorithm` specified hue-weighted scoring. Fix: if hue within 25°, recover up to 40% of lost points. Same-hue-family guesses with brightness/saturation drift get partial credit. Example: ΔE 20 with hue 5° off → 2.2 → 4.7.
- **2026-03-29** — Reveal screen design: side-by-side color panels (not diagonal split), score colored to match target, verdict text only — no ΔE or HSB numbers. Rationale: ΔE is jargon, HSB values are redundant when you can see the colors. The visual comparison + score + verdict communicate everything.
- **2026-03-29** — Results screen: stripped decorative boxes from total score and individual per-color scores. Bare numbers directly on background. Raw HSB text dump removed from advanced detail view — kept just ΔE number + visual delta bars (L/C/H).
- **2026-03-29** — ~~Vercel SPA rewrite doesn't work with framework detection enabled.~~ Superseded: disabled framework detection (`"framework": null`), added explicit `/` → `/index.html` rewrite. Root now served directly from CDN — no function invocation, no 307 redirect hop. The `@app.get("/")` handler was removed; local dev uses `StaticFiles(html=True)` instead.
- **2026-03-29** — History: localStorage, not server. Sorted by highest score, 20 per mode, tabs per mode. Full game data stored (targets, guesses, scores) so tapping a row shows the complete result view. `/api/history` removed — returns in Phase 2 as a leaderboard endpoint.
- **2026-03-29** — Identity: no accounts, no auth. Privacy-first. Users provide a display name (pseudonym) only when needed (multiplayer/leaderboards), freely changeable each time. Stored in localStorage to prepopulate, not enforced. No server-side user identity until Phase 3 challenges require linking attempts.
- **2026-03-29** — Per-color reveal: after each pick, show target vs guess side-by-side with score. Client computes CIEDE2000 locally for instant feedback (no round-trip latency). Server re-scores on final submit for persistence. Flow per round: memorize → pick → reveal. Final results screen still shows all 5 + total.
- **2026-03-29** — Backend architecture: client-driven game flow. Client generates colors and scores locally — no server round-trip to start a game. `submit` accepts targets + guesses + client-computed scores, then appends completed game to DB. Server is append-only persistence for analytics. Rationale: serverless (Vercel) means ephemeral `/tmp`, no shared state across instances, cold starts add latency. Client-side generation eliminates network dependency for gameplay — games start instantly. DB is never in the critical path. Tradeoff: scoring is technically cheatable (client sends scores), but this is a training tool — cheating only hurts yourself.
- **2026-03-29** — Database strategy: Turso (LibSQL) for persistent storage, with `/tmp` SQLite as a zero-dependency fallback. Turso is SQLite-compatible (minimal migration from current schema), edge-distributed, free tier. The append-only write pattern (one INSERT per completed game) is ideal for either backend.
- **2026-03-29** — Refresh resets. No session persistence for in-progress games. A browser refresh returns to the menu — the partially-played round is silently discarded. This is intentional: rounds are short (< 2min), there's no penalty for abandoning, and persisting partial state adds complexity with no training value.
- **2026-03-29** — Schema evolution path for multiplayer: solo games (now) → leaderboards (add `display_name` column on `games`, no users table) → shared challenges (add `challenges` table storing target colors server-side, `challenge_id` FK on `games`). Shared challenges restore server-side truth for competitive scoring while solo play stays stateless.
- **2026-03-28** — Results: clean by default (swatches + scores). HSB values, ΔE, feedback text behind hidden activation (URL param / shortcut). Mirrors dialed.gg's minimal results, but insights available for power users.
- **2026-03-28** — Frontend: evolve own visual identity, not a dialed.gg clone. Use dialed.gg as quality gate — if it doesn't hold up side-by-side, it's not ready.
- **2026-03-28** — ~~Feedback messages: server-side message bank.~~ Superseded: feedback messages are client-side (`colorFeedbackText`, `totalFeedbackText` in index.html). Original plan was server-side for shareability; pivoted to client-side with the stateless architecture.

## Dogfooding

### Active
- [ ] Play vs Match score gap — does it reveal recall as the bottleneck?
- [ ] Field picker vs sliders — which feels more natural?
- [ ] 5s memorize time — too short? too long? does it vary by color?
- [ ] Initial picker at H180° S50° B50° — neutral enough or does it anchor guesses?
- [ ] Scoring curve — CIEDE2000 sigmoid `10 / (1 + (ΔE00/12)^2.5)` + hue-recovery bonus (see `pit/2026-03-28-scoring-algorithm`). Tightened from k=20 → k=12. Does the curve feel right now? Is hue recovery (40% at hue ≤25°) well-calibrated?
- [ ] Learning curve — do scores improve over sessions? Is there a plateau?
- [ ] Systematic biases — does everyone undersaturate? Overshoot hue in the same direction?

### Observations
