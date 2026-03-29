---
title: Milestones
description: Shipped capability inflection points — what became possible, what it proved, what it unblocked.
summary: "Alpha nearly complete — client-driven architecture, resilience shipped. Scoring calibration and analytics remain before beta."
---

## Beta release `planned`

All five modes playable, polished UX, custom icons. The game is worth sharing broadly.

**Will prove:** Full skill coverage — each of the five perceptual skills has a dedicated training mode.
**Will unblock:** Public launch, broader feedback, progression/tracking features.
**Scope:** Name It + Read It modes, custom icons, scoring curve finalized.

## Alpha release `in-progress`

Client-driven architecture — color generation + CIEDE2000 scoring fully client-side, games start instantly with no server round-trip. Three modes playable (Play/Match/Picture). Per-color reveal with HSB slider visualization, hue-recovery bonus. Resilience shipped: error handling, localStorage hardening, reduced-motion, font fallback, mobile layout fixes.

**Proving:** The core loop is fun and teaches color perception without jargon.
**Will unblock:** Broader playtesting, feedback collection, remaining mode implementation.
**Remaining:** Scoring curve calibration (playtesting), PostHog analytics.

## 2026-03-29 — v1 live on Vercel `completed`

Frontend design upgrade and Vercel deployment. The app is publicly reachable for the first time — anyone with the URL can play the core loop.

**Proved:** Single-file frontend + FastAPI backend deploys cleanly on Vercel's serverless Python runtime.
**Unblocked:** External playtesting, sharing, iteration with real users.

## 2026-03-28 — Project bootstrap `completed`

Repo from zero to working prototype in a single session. Backend (FastAPI/SQLite), frontend, CIEDE2000 scoring, five-skill model with scientific grounding, visual identity, user journey spec, competitive analysis of 6 color games.

**Proved:** Color perception training can be structured as a game with measurable skills — not just "guess the color."
**Unblocked:** All five game modes have a design foundation; frontend implementation can begin against a real backend.
