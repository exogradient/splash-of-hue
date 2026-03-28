---
title: Doc System
description: How the doc system works — principles, layers, schema, pipeline
stability: stable
responsibility: How the doc system works — principles, layers, schema
---

# Doc System

## Problem

AI agents degrade doc quality with each touch — duplication, inconsistent phrasing, content in wrong docs, verbose cross-references that themselves become maintenance burden. The human spends attention on cleanup instead of judgment.

Structure quality determines maintenance cost, not structure quantity. The question for any piece of structure is "can this go stale independently?" — not "is this one more thing?"

## Principles

Every piece of structure must satisfy all three:

1. **Non-duplicative** — captures something not expressed elsewhere
2. **Colocated** — lives where you already are when reading or writing
3. **Can't go stale independently** — changes to the thing it describes naturally prompt updating it

## Views

Evaluate structure from three perspectives:

| View | When | Need |
|------|------|------|
| **Human orientation** | Forming judgment, making decisions | Fast lookup, clear boundaries |
| **AI write** | Agent modifying docs | Colocation, non-duplication, can't go stale |
| **AI onboarding** | Fresh conversation, consuming docs | Understand structure, boundaries, what goes where |

## Layers

Encoded as filename prefix — maximally colocated, zero metadata overhead, self-sorting in directory listings.

| Layer | Docs | What belongs here |
|-------|------|-------------------|
| **identity** | identity-context.md, identity-model.md | Why and what. Context is external — vision, philosophy, competitive landscape. Model is internal — skill decomposition, modes, game structure |
| **design** | design-log.md | How the design evolves through use — decisions and dogfooding |
| **specs** | specs-roadmap.md, specs-features.md, specs-journey.md | What to build, what exists today |
| **meta** | meta-doc-system.md | About the doc system itself |

`layer` captures the doc's role. `stability` captures current rate of change. These are independent — identity is *meant* to be stable but may not be yet (rate of change is contextual to project stage).

## Pipeline

Specs layer follows a pipeline:

**roadmap** (prioritized direction) → **features** (committed specs) → **journey** (shipped flow)

Items move forward through the pipeline as they mature. Roadmap captures what we might build. Features captures committed specs with enough detail to implement. Journey captures what the user actually experiences in the shipped product.

## Frontmatter Schema

Four required fields, enforced by `make check-docs`:

| Field | Purpose |
|-------|---------|
| `title` | Human-readable name |
| `description` | One-line summary — shown by `make docs` |
| `stability` | Current rate of change: stable, evolving, volatile |
| `responsibility` | What this doc owns — used to detect boundary violations |

Each passes the three principles test. `layer` was explicitly dropped from frontmatter since the filename prefix carries it.

## PIT (Point-in-Time) Docs

`docs/pit/` contains frozen research snapshots — timestamped analysis that informed a decision. They are not managed docs: no stability, no responsibility, no maintenance. Their contract is "this was the analysis on this date."

PIT docs feed into the layer system (e.g., a decision in `design-log.md` references a PIT doc as rationale) but are not part of it. Do not apply layer rules to them.

Naming: `YYYY-MM-DD-topic.md`. Frontmatter: `title` and `date` only.

## Trust

Content quality varies by review level. Stability is contextual to project stage — "stable" means the doc's *role* is settled, not that it will never change.

When reading docs, consider review quality: hand-tuned content (e.g. product model, design log) has higher trust than AI-generated content (e.g. early roadmap items). The `stability` field signals rate of change, not quality.
