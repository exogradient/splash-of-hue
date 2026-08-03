---
title: Auto-Grader Design
description: How local calibration supervises and release-gates the scorer
stability: evolving
responsibility: Auto-grader principles, architecture, audit model, and evolution path
---

# Auto-Grader Design

## Goal

Tune the perceptual scorer without turning human review into an endless labeling job.

The scorer produces measurements and a score. The auto-grader judges whether that score is directionally reasonable. Humans audit the grader. Release tooling tunes and gates the scorer against reviewed evidence.

## Principles

1. **Interpretability first.** Every verdict names the rules and signals behind it.
2. **Abstain on conflict.** Uncertain evidence is a routing decision, not a forced label.
3. **Audit the grader.** Human review measures supervision quality before tuning the scorer.
4. **Keep random audits.** Targeted queues find known failures; random samples find blind spots.
5. **Promote evidence.** Reviewed cases become regression fixtures.
6. **Gate before optimizing.** A candidate must protect known behavior before improving aggregate fit.

## System

```text
scorer → auto-grader → export → audit sampler → human review
   └──────────────→ tuner / release gate ←──────────────┘
                                      └→ regression fixtures
```

### Scorer

Produces score, CIEDE2000 distance, hue distance, and lightness/chroma/hue components.

### Auto-grader

Emits:

- `too_high`
- `too_low`
- `ok`
- `abstain`

Every result carries fired rules, supporting signals, and confidence. Opposing directional rules produce `abstain`.

### Human review

Records whether the grader was right, the corrected verdict when wrong, and an optional reason. A human override is first evidence against the grading rule—not automatic evidence against the scorer.

### Audit sampling

Each review cycle mixes:

- suspected scoring failures;
- abstentions and contradictions;
- threshold-adjacent probes;
- obvious positive controls;
- a mandatory random slice.

Report agreement by sampling bucket. A targeted queue is not a population estimate.

## Current calibration focus

The difficult regions are:

- near-same-hue guesses with large saturation or brightness drift;
- moderate hue drift that still feels too generous;
- close matches that guard terms make too harsh;
- contradictory signals near thresholds.

The current release scorer is the shared `effective_delta_guard` implementation. App and calibration copies must remain byte-identical.

## Release flow

1. Collect a dogfooding export.
2. Review a mixed audit sample.
3. Promote stable examples into fixtures.
4. Run `make calibrate-release FILE=...`.
5. Reject candidates that worsen fixtures or protected challenge behavior.
6. Adopt a candidate only when the remaining aggregate evidence improves.

## Evolution

Keep the top-level concepts stable—grader, verdict, rules, signals, confidence, abstain, review, sampling bucket, fixture—even if deterministic rules later become probabilistic aggregation.

Do not introduce stronger evaluators or automatic rule generation until the local audit loop has measured failure modes that justify them.
