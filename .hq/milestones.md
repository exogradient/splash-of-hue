---
title: Milestones
description: Shipped capability inflection points — what became possible, what it proved, what it unblocked.
summary: "Alpha complete — three modes, calibrated scoring, resilience, analytics. Beta in progress: homepage redesign, frontend polish, new modes."
---

## Beta release `in-progress`

All five modes playable, polished UX. The game is worth sharing broadly.

**Will prove:** Full skill coverage — each of the five perceptual skills has a dedicated training mode.
**Will unblock:** Public launch, broader feedback, progression/tracking features.
**Will ship:** Call It + Split It modes, scoring curve finalized, design pass, share results.

**Shipped so far:**
- PWA icon suite (light installed-app icon, transparent tab favicon, apple-touch, maskable, manifest.json)
- Mobile viewport hardening (viewport-fit=cover, safe-area insets, svh→dvh, top-aligned flex — iPhone Safari validated)
- Focus-visible accessibility styles
- Scoring calibration pipeline (auto-grader, regression fixtures, parity checks, population profiling)
- Homepage redesign (2-column card grid with spectral-ring hero)
- Touch target expansion (hue bar 44px, SB thumb 26px)

**Remaining:**
- Design pass — results reveal order, picker toggle, adaptive overlay, directional transitions, confirm button layout, low-score empathy, history empty state
- Call It mode (XKCD color naming dataset, CIEDE2000 nearest-match)
- Split It mode (needs feature spec)
- Text-only share (navigator.share / clipboard + toast)
- Social og image

## 2026-03-30 — Alpha release `completed`

Client-driven architecture — color generation + CIEDE2000 scoring fully client-side, games start instantly with no server round-trip. Three modes playable (Play/Match It/Picture It). Per-color reveal with HSB slider visualization, hue-recovery bonus. Resilience shipped: error handling, localStorage hardening, reduced-motion, font fallback, mobile layout fixes. PostHog analytics live with 10-insight Alpha Analytics dashboard. Scoring calibration pipeline shipped — auto-grader, regression fixtures, parity checks, population profiling — and first tuning cycle produced the release-gated `effective_delta_guard` scorer.

**Proved:** The core loop is fun and teaches color perception without jargon.
**Unblocked:** Broader playtesting, feedback collection, remaining mode implementation.

## 2026-03-29 — v1 live on Vercel `completed`

Frontend design upgrade and Vercel deployment. The app is publicly reachable for the first time — anyone with the URL can play the core loop.

**Proved:** Single-file frontend + FastAPI backend deploys cleanly on Vercel's serverless Python runtime.
**Unblocked:** External playtesting, sharing, iteration with real users.

## 2026-03-28 — Project bootstrap `completed`

Repo from zero to working prototype in a single session. Backend (FastAPI/SQLite), frontend, CIEDE2000 scoring, five-skill model with scientific grounding, visual identity, user journey spec, competitive analysis of 6 color games.

**Proved:** Color perception training can be structured as a game with measurable skills — not just "guess the color."
**Unblocked:** All five game modes have a design foundation; frontend implementation can begin against a real backend.
