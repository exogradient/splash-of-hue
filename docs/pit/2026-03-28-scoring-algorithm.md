---
title: Scoring Algorithm Research
date: 2026-03-28
---

# Scoring Algorithm Research

## Context

Current implementation: CIE76 Delta E with Gaussian curve `10 * exp(-0.5 * (ΔE/25)²)`.
Question from dogfooding: does our simpler curve feel right, or do hue misses need sharper punishment?

## Delta E Formulas

### CIE76 (current)

Euclidean distance in CIELAB: `sqrt((ΔL*)² + (Δa*)² + (Δb*)²)`.

Known failures:
- **Blue region (~260-290°):** Overestimates perceived differences. Two blues at ΔE76=3 may look identical while ΔE76=3 in greens is clearly visible.
- **Saturated colors:** At high chroma, two different hues may report ΔE=10 when perceptual difference is ΔE=2-3.
- **Near-neutrals:** Humans are more sensitive to shifts here than CIE76 accounts for.
- **Equal weighting:** Treats 1 unit ΔL* = 1 unit Δa* = 1 unit Δb*, but CIELAB is not actually perceptually uniform.

Our game generates S∈[35,100], B∈[35,100] — exactly the saturated range where CIE76 fails most.

### CIE94

Adds chroma-dependent weighting: `SC = 1 + 0.045C*`, `SH = 1 + 0.015C*`. Better for saturated colors but no blue correction, crude lightness weighting, asymmetric (argument order matters).

### CIEDE2000

Current CIE standard. Five corrections on top of CIELAB:

1. **Lightness weighting (SL):** More tolerant at extreme L* (dark/light). At L*=50, SL=1.0; at L*=10 or L*=90, SL≈1.6.
2. **Chroma weighting (SC):** `SC = 1 + 0.045C̄`. At C=50, SC=3.25. Vivid colors get larger tolerance.
3. **Hue weighting (SH):** `SH = 1 + 0.015C̄T` (T varies ~0.56-1.78 by hue angle). Since SC > SH at same chroma, **hue errors are weighted ~1.86x more heavily than chroma errors** for saturated colors. Matches perception: humans notice hue shifts before chroma/lightness drift.
4. **Blue rotation (RT):** Cross-term peaking at 275° that corrects CIELAB's known blue-region tilt in tolerance ellipses.
5. **Gray correction (a' adjustment):** Improves accuracy for near-achromatic colors.

Performance from CIE evaluation (normalized): chroma weighting 100, hue weighting 29, rotation 8, lightness 8, gray 6.

Known limitation: ~ΔE=0.27 discontinuity at 180° hue difference. Negligible in practice.

### Verdict

CIEDE2000 is unambiguously superior for perceptual accuracy. ~50 lines of Python, negligible computational cost for 5 colors per round.

## Perceptual Non-Uniformities in CIELAB

Where the underlying space breaks down (independent of which ΔE formula):

- **Blue hues (~260-290°):** Over-reported differences. CIEDE2000's RT term exists for this.
- **Yellow region:** Cube-root transform over-expands yellows.
- **Saturated colors:** Tolerance ellipses grow with chroma. ΔE=5 in vivid red << ΔE=5 in muted gray perceptually.
- **Near-neutrals:** Extreme sensitivity to chromatic contamination.

**Relative importance of dimensions** (dental ceramics research, CIEDE2000 units):
- Lightness acceptability threshold: ΔL'=2.92 (most tolerant)
- Chroma acceptability threshold: ΔC'=2.52
- Hue acceptability threshold: ΔH'=1.90 (least tolerant — noticed first)

Consistent with visual attention literature: hue is the most salient chromatic dimension.

## Score Curve Shape

### Current Gaussian: `10 * exp(-0.5 * (ΔE/25)²)`

| Score | ΔE threshold |
|-------|-------------|
| 9/10 | ~11.5 |
| 7/10 | ~21.1 |
| 5/10 | ~29.4 |
| 3/10 | ~38.8 |
| 1/10 | ~53.6 |

**Problem:** Too flat at the top — ΔE 0 and ΔE 10 both score 9+, no incentive for precision. Steepest discrimination at ΔE 20-30 ("completely different colors"). Drops to zero past ~55, so all bad guesses are uniformly 0 with no signal.

### Dialed.gg sigmoid: `10 / (1 + (ΔE/45)^1.4)`

Very forgiving. Still 4.6/10 at ΔE=50. Never reaches zero. Designed for mass appeal — nobody feels devastated. Combined with hue-recovery bonuses, "roughly right hue" is rewarded generously.

### Recommended sigmoid: `10 / (1 + (ΔE00/20)^2.5)`

| ΔE00 | Score | Perceptual meaning |
|------|-------|--------------------|
| 0 | 10.0 | Perfect |
| 2 | 9.9 | Below JND — indistinguishable |
| 5 | 9.3 | Noticeable if you look closely |
| 10 | 7.6 | Clearly different but close |
| 15 | 5.5 | Same family, different color |
| 20 | 3.8 | Quite different |
| 30 | 1.8 | Wrong color |
| 50 | 0.5 | Wildly wrong |

**Why these parameters:**
- Steepest discrimination at ΔE 10-20 — intermediate player zone where improvement happens.
- Sub-JND differences (ΔE < 2) score near-perfect — correct, you can't beat imperceptible.
- ΔE > 30 below 2 — clear "missed" signal without hard zero.
- Long tail gives beginners directional feedback even when wrong.

### Farnsworth-Munsell reference

FM-100 uses transposition count, not continuous ΔE curves. Not directly transferable, but the insight is: ordering accuracy creates natural non-linearity where small errors matter less than large jumps.

## Dimension-Weighted Scoring

### What CIEDE2000 already handles

At moderate chroma (C≈50): hue errors ~1.86x more impactful than chroma errors (SC=3.25 vs SH=1.75 — higher S = more tolerance = less penalty). At low chroma (near-neutrals), ratio shrinks to ~1.26x — correct because hue is less meaningful without saturation.

### Do we need game-level hue bonuses on top?

**No.** Three reasons:

1. CIEDE2000 already weights hue more heavily, calibrated against decades of human perception data.
2. Dialed.gg's hue bonuses compensate for CIE76's *lack* of dimension weighting. With CIEDE2000 as base, that compensation is built in.
3. Double-weighting hue makes scoring less defensible and harder to reason about.

**One exception worth considering later:** A pedagogical hue bonus to specifically train hue attention — but this should be framed as a game design choice, not a perceptual correction, and should wait for dogfooding data.

### Per-dimension storage

Store ΔL', ΔC', ΔH' from the CIEDE2000 computation alongside total ΔE00. Enables:
- Showing players their weakest dimension
- Validating CIEDE2000's built-in weighting feels right during dogfooding
- Future dimension-specific training modes with data backing

## Recommendation

Switch from CIE76 + Gaussian to **CIEDE2000 + sigmoid `10 / (1 + (ΔE00/20)^2.5)`**.

This resolves dogfooding item #5 by reframing it: the question becomes "does this curve feel right?" rather than "does our curve need hue bonuses?" — because CIEDE2000 handles dimension weighting internally.

## Sources

- CIE Technical Report: The development of the CIE 2000 colour-difference formula (Luo, Cui, Rigg)
- Sharma, Wu, Dalal — CIEDE2000 implementation and verification (Rochester)
- Ghinea et al. — CIEDE2000 acceptability thresholds in dental ceramics
- Theeuwes & Kooi — Role of hue, saturation, lightness in visual attention
- Bjorn Ottosson — Oklab perceptual color space (2020)
- Wikipedia — Color difference
- Zachary Schuessler — Delta E 101
