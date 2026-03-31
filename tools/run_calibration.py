#!/usr/bin/env python3
"""Search scoring parameters against multi-profile auto-grader calibration data."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import argparse
import itertools
import json
import math
from pathlib import Path
import sqlite3
from typing import Any


VALID_VERDICTS = {"ok", "too_high", "too_low", "abstain"}
SCORER_FAMILIES = (
    "baseline",
    "same_hue_guard",
    "balanced_guard",
    "effective_delta_guard",
    "effective_delta_rebalance",
    "same_hue_rescue",
    "recovery_gate",
)
BUCKET_WEIGHTS = {
    "suspected_negative": 3.0,
    "abstain_probe": 2.5,
    "boundary_probe": 2.0,
    "positive_sanity": 1.0,
    "coverage_probe": 1.0,
}
DEFAULT_POPULATION_DB = Path("data/games.db")
DEFAULT_REGRESSION_FIXTURES = Path("tools/calibration-regression.json")
DEFAULT_POPULATION_PRESERVE_DROP_BUDGET = 0.02
DEFAULT_POPULATION_DIRECTIONAL_WORSEN_BUDGET = 0.05
DEFAULT_CHALLENGE_WORSEN_CEILING = 0.05
EPSILON = 1e-9


@dataclass(frozen=True)
class ScoringParams:
    curve_divisor: float
    curve_exponent: float
    hue_threshold_degrees: float
    hue_lost_point_rate: float
    same_hue_sb_penalty_rate: float = 0.0
    mid_hue_penalty_rate: float = 0.0
    same_hue_rescue_low_score_boost: float = 0.0
    same_hue_rescue_mid_score_boost: float = 0.0


LIVE_BASELINE_PARAMS = ScoringParams(10.0, 2.25, 33.0, 0.55, 0.25, 0.30, 0.0, 0.0)


@dataclass(frozen=True)
class CandidateSpec:
    family: str
    params: ScoringParams
    same_hue_sb_penalty_rate: float = 0.0
    mid_hue_penalty_rate: float = 0.0


@dataclass(frozen=True)
class Sample:
    source_profile: str
    batch_seed: int | None
    sample_id: str | None
    profile: str | None
    mode: str | None
    picker_type: str | None
    score_band: str | None
    hue_band: str | None
    delta_e_band: str | None
    target: dict[str, float]
    guess: dict[str, float]
    baseline_score: float
    auto_verdict: str
    human_final_verdict: str | None
    reviewed: bool
    human_agrees_with_auto: bool | None
    candidate_bucket: str
    rules: tuple[str, ...]


@dataclass(frozen=True)
class RegressionFixture:
    fixture_id: str
    target: dict[str, float]
    guess: dict[str, float]
    expected_verdict: str | None
    baseline_score: float | None
    required_shift: str | None
    min_shift: float | None
    min_score: float | None
    max_score: float | None
    tag: str | None


@dataclass(frozen=True)
class PopulationMetrics:
    ok_total: int
    directional_total: int
    preserve_ok_rate: float
    directional_worsen_rate: float
    mean_abs_drift_ok: float


@dataclass(frozen=True)
class ChallengeMetrics:
    directional_total_weight: float
    fix_wrong_rate: float
    help_wrong_rate: float
    worsen_wrong_rate: float
    soft_objective: float


@dataclass(frozen=True)
class RegressionMetrics:
    total: int
    pass_rate: float
    failed_ids: tuple[str, ...]


@dataclass(frozen=True)
class CandidateResult:
    candidate: CandidateSpec
    population: PopulationMetrics
    challenge: ChallengeMetrics
    regression: RegressionMetrics
    gate_failures: tuple[str, ...]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="Path to challenge calibration JSON export")
    parser.add_argument("--top", type=int, default=8, help="How many top valid parameter sets to print")
    parser.add_argument(
        "--analysis-limit",
        type=int,
        default=8,
        help="How many sample-level analysis rows to print per section",
    )
    parser.add_argument(
        "--families",
        default=",".join(SCORER_FAMILIES),
        help="Comma-separated scorer families to evaluate "
        f"({', '.join(SCORER_FAMILIES)})",
    )
    parser.add_argument(
        "--label-source",
        choices=("auto", "human", "hybrid"),
        default="hybrid",
        help="How to resolve challenge labels: auto-grader, reviewed human labels, or hybrid human-overrides-auto",
    )
    parser.add_argument(
        "--population-db",
        type=Path,
        default=DEFAULT_POPULATION_DB,
        help="Path to local gameplay SQLite DB used for the population profile",
    )
    parser.add_argument(
        "--regression-fixtures",
        type=Path,
        default=DEFAULT_REGRESSION_FIXTURES,
        help="Path to checked-in regression fixtures JSON",
    )
    parser.add_argument(
        "--fix-margin",
        type=float,
        default=0.5,
        help="Minimum score shift needed to count a directional row as fixed",
    )
    parser.add_argument(
        "--preserve-tolerance",
        type=float,
        default=0.5,
        help="Maximum score drift allowed for an OK row to count as preserved",
    )
    parser.add_argument(
        "--population-preserve-drop-budget",
        type=float,
        default=DEFAULT_POPULATION_PRESERVE_DROP_BUDGET,
        help="Maximum allowed drop in population preserve_ok_rate relative to baseline",
    )
    parser.add_argument(
        "--population-directional-worsen-budget",
        type=float,
        default=DEFAULT_POPULATION_DIRECTIONAL_WORSEN_BUDGET,
        help="Maximum allowed increase in population directional_worsen_rate relative to baseline",
    )
    parser.add_argument(
        "--challenge-worsen-ceiling",
        type=float,
        default=DEFAULT_CHALLENGE_WORSEN_CEILING,
        help="Maximum allowed challenge directional_worsen_rate before rejection",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write ranked candidate results as JSON",
    )
    return parser.parse_args()


def parse_families(raw: str) -> tuple[str, ...]:
    families = tuple(part.strip() for part in raw.split(",") if part.strip())
    if not families:
        raise SystemExit("At least one scorer family must be provided.")
    unknown = [family for family in families if family not in SCORER_FAMILIES]
    if unknown:
        raise SystemExit(f"Unknown scorer families: {', '.join(sorted(unknown))}")
    return families


def load_batches(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    raise ValueError(f"Unsupported calibration payload in {path}")


def extract_baseline_params(batches: list[dict[str, Any]]) -> ScoringParams:
    for batch in batches:
        params = batch.get("scoring_params")
        if not params:
            continue
        guard_penalty = params.get("guardPenalty", {})
        same_hue_rescue = params.get("sameHueRescue", {})
        return ScoringParams(
            curve_divisor=float(params["curve"]["divisor"]),
            curve_exponent=float(params["curve"]["exponent"]),
            hue_threshold_degrees=float(params["hueRecovery"]["thresholdDegrees"]),
            hue_lost_point_rate=float(params["hueRecovery"]["lostPointRate"]),
            same_hue_sb_penalty_rate=float(guard_penalty.get("sameHueSbPenaltyRate", 0.0)),
            mid_hue_penalty_rate=float(guard_penalty.get("midHuePenaltyRate", 0.0)),
            same_hue_rescue_low_score_boost=float(same_hue_rescue.get("lowScoreBoost", 0.0)),
            same_hue_rescue_mid_score_boost=float(same_hue_rescue.get("midScoreBoost", 0.0)),
        )
    return LIVE_BASELINE_PARAMS


def verdict_from_rules(rules: tuple[str, ...]) -> str:
    too_low = any(rule.startswith("too_low_") or rule in {"hue-close-scored-low", "low-dE-low-score"} for rule in rules)
    too_high = any(rule.startswith("too_high_") or rule in {"hue-far-scored-high", "high-dE-high-score"} for rule in rules)
    if too_low and too_high:
        return "abstain"
    if too_low:
        return "too_low"
    if too_high:
        return "too_high"
    return "ok"


def auto_grade_rules_from_components(
    *,
    score: float,
    delta_e: float,
    hue_dist: float,
    abs_delta_l: float,
    abs_delta_c: float,
) -> tuple[str, ...]:
    rules: list[str] = []
    close_hue_too_low_threshold = 3.75 if hue_dist <= 5 else 4.0
    same_hue_rescue = (
        hue_dist <= 1
        and delta_e <= 16
        and score < 6.5
        and max(abs_delta_l, abs_delta_c) >= 20
    )
    same_hue_large_sb = (
        hue_dist <= 4
        and score >= 7.0
        and delta_e <= 12
        and max(abs_delta_l, abs_delta_c) >= 18
        and not same_hue_rescue
    )

    if hue_dist <= 15 and score < close_hue_too_low_threshold:
        rules.append("too_low_close_hue_low_score")
    if 18 <= hue_dist <= 24 and delta_e <= 20 and score < 3.5:
        rules.append("too_low_mid_hue_low_score")
    if same_hue_rescue:
        rules.append("too_low_same_hue_moderate_de")
    if delta_e < 10 and score < 6:
        rules.append("too_low_low_delta_e_low_score")
    if hue_dist > 40 and score > 6:
        rules.append("too_high_far_hue_high_score")
    if hue_dist > 10 and delta_e > 30 and score > 3:
        rules.append("too_high_high_delta_e_high_score")
    if same_hue_large_sb:
        rules.append("too_high_same_hue_large_sb")
    if 12 <= hue_dist <= 22 and delta_e <= 10 and score >= 7:
        rules.append("too_high_mid_hue_too_generous")
    return tuple(rules)


def inferred_review_verdict(metrics: dict[str, Any]) -> str:
    score = float(metrics["score"])
    delta_e = float(metrics["delta_e"])
    hue_dist = float(metrics["hue_dist"])
    abs_delta_l = abs(float(metrics["delta_l"]))
    abs_delta_c = abs(float(metrics["delta_c"]))
    verdict = verdict_from_rules(
        auto_grade_rules_from_components(
            score=score,
            delta_e=delta_e,
            hue_dist=hue_dist,
            abs_delta_l=abs_delta_l,
            abs_delta_c=abs_delta_c,
        )
    )
    return verdict if verdict != "ok" else "abstain"


def current_auto_grade(metrics: dict[str, Any]) -> tuple[str, tuple[str, ...], str]:
    score = float(metrics["score"])
    delta_e = float(metrics["delta_e"])
    hue_dist = float(metrics["hue_dist"])
    abs_delta_l = abs(float(metrics["delta_l"]))
    abs_delta_c = abs(float(metrics["delta_c"]))
    rules = auto_grade_rules_from_components(
        score=score,
        delta_e=delta_e,
        hue_dist=hue_dist,
        abs_delta_l=abs_delta_l,
        abs_delta_c=abs_delta_c,
    )
    verdict = verdict_from_rules(rules)
    if verdict == "abstain":
        confidence = "low"
    elif len(rules) >= 2:
        confidence = "high"
    elif len(rules) == 1:
        confidence = "medium"
    else:
        confidence = "low"
    return verdict, rules, confidence


def score_band(score: float) -> str:
    if score < 2.5:
        return "0-2.5"
    if score < 5:
        return "2.5-5"
    if score < 7.5:
        return "5-7.5"
    return "7.5-10"


def hue_band(hue_dist: float) -> str:
    if hue_dist <= 5:
        return "0-5"
    if hue_dist <= 15:
        return "5-15"
    if hue_dist <= 25:
        return "15-25"
    return "25+"


def delta_e_band(delta_e: float) -> str:
    if delta_e <= 5:
        return "0-5"
    if delta_e <= 10:
        return "5-10"
    if delta_e <= 20:
        return "10-20"
    return "20+"


def normalize_color(raw: Any) -> dict[str, float]:
    if not isinstance(raw, dict):
        raise ValueError(f"Expected color dict, got {type(raw).__name__}")
    return {
        "h": float(raw["h"]),
        "s": float(raw["s"]),
        "b": float(raw["b"]),
    }


def make_sample(
    *,
    source_profile: str,
    batch_seed: int | None,
    sample_id: str | None,
    profile: str | None,
    mode: str | None,
    picker_type: str | None,
    target: dict[str, float],
    guess: dict[str, float],
    metrics: dict[str, float],
    auto_verdict: str,
    human_final_verdict: str | None,
    reviewed: bool,
    human_agrees_with_auto: bool | None,
    candidate_bucket: str,
    rules: tuple[str, ...],
) -> Sample:
    return Sample(
        source_profile=source_profile,
        batch_seed=batch_seed,
        sample_id=sample_id,
        profile=profile,
        mode=mode,
        picker_type=picker_type,
        score_band=score_band(float(metrics["score"])),
        hue_band=hue_band(float(metrics["hue_dist"])),
        delta_e_band=delta_e_band(float(metrics["delta_e"])),
        target=target,
        guess=guess,
        baseline_score=float(metrics["score"]),
        auto_verdict=auto_verdict,
        human_final_verdict=human_final_verdict,
        reviewed=reviewed,
        human_agrees_with_auto=human_agrees_with_auto,
        candidate_bucket=candidate_bucket,
        rules=rules,
    )


def normalize_challenge_sample(batch: dict[str, Any], raw: dict[str, Any]) -> Sample:
    metrics = raw.get("metrics", raw)
    metrics = {
        "score": float(metrics["score"]),
        "delta_e": float(metrics["delta_e"]),
        "hue_dist": float(metrics.get("hue_dist", metrics.get("hueDist"))),
        "delta_l": float(metrics["delta_l"]),
        "delta_c": float(metrics["delta_c"]),
        "delta_h": float(metrics["delta_h"]),
    }
    auto_grader = raw.get("auto_grader", {})
    human_review = raw.get("human_review", {})
    auto_assess = raw.get("auto_assess", {})
    stored_rules = tuple(auto_grader.get("rules", auto_assess.get("issues", [])))
    stored_verdict = str(auto_grader.get("verdict") or raw.get("default_verdict") or "") or None
    if auto_grader:
        rules = stored_rules
        auto_verdict = stored_verdict if stored_verdict in VALID_VERDICTS else verdict_from_rules(rules)
    else:
        auto_verdict, rules, _confidence = current_auto_grade(metrics)
    reviewed = bool(raw.get("reviewed", raw.get("overridden", False)))
    human_final_verdict = human_review.get("final_verdict") or raw.get("final_verdict")
    if human_final_verdict is None and reviewed:
        final_ok = bool(raw.get("final_ok", raw.get("human_ok", True)))
        default_ok = bool(raw.get("default_ok", auto_verdict == "ok"))
        if final_ok:
            human_final_verdict = "ok"
        elif not default_ok and auto_verdict in VALID_VERDICTS:
            human_final_verdict = auto_verdict
        else:
            human_final_verdict = inferred_review_verdict(metrics)
    if human_final_verdict is not None and human_final_verdict not in VALID_VERDICTS:
        human_final_verdict = None
    human_agrees = human_review.get("agrees_with_auto")
    if human_agrees is None and reviewed and human_final_verdict is not None:
        human_agrees = human_final_verdict == auto_verdict
    return make_sample(
        source_profile="challenge",
        batch_seed=batch.get("seed"),
        sample_id=str(raw.get("id")) if raw.get("id") is not None else None,
        profile=raw.get("profile"),
        mode=None,
        picker_type=None,
        target=normalize_color(raw["target"]),
        guess=normalize_color(raw["guess"]),
        metrics=metrics,
        auto_verdict=auto_verdict,
        human_final_verdict=human_final_verdict,
        reviewed=reviewed,
        human_agrees_with_auto=bool(human_agrees) if human_agrees is not None else None,
        candidate_bucket=str(raw.get("candidate_bucket", "coverage_probe")),
        rules=rules,
    )


def load_challenge_samples(path: Path) -> tuple[list[dict[str, Any]], list[Sample]]:
    batches = load_batches(path)
    samples = [normalize_challenge_sample(batch, raw) for batch in batches for raw in batch.get("samples", [])]
    return batches, samples


def load_population_samples(db_path: Path, baseline: ScoringParams) -> tuple[list[Sample], Counter[str]]:
    if not db_path.exists():
        raise SystemExit(f"Population DB not found: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    samples: list[Sample] = []
    skipped: Counter[str] = Counter()
    try:
        rows = conn.execute("SELECT id, mode, picker_type, target_colors, guesses, scores FROM games").fetchall()
    finally:
        conn.close()
    for row in rows:
        if not row["target_colors"] or not row["guesses"] or not row["scores"]:
            skipped["missing_payload"] += 1
            continue
        try:
            targets = json.loads(row["target_colors"])
            guesses = json.loads(row["guesses"])
            scores = json.loads(row["scores"])
        except (json.JSONDecodeError, TypeError, ValueError):
            skipped["invalid_json"] += 1
            continue
        if not isinstance(targets, list) or not isinstance(guesses, list) or not isinstance(scores, list):
            skipped["non_list_payload"] += 1
            continue
        round_count = min(len(targets), len(guesses), len(scores))
        if round_count == 0:
            skipped["empty_rounds"] += 1
            continue
        for index in range(round_count):
            try:
                target = normalize_color(targets[index])
                guess = normalize_color(guesses[index])
            except (KeyError, TypeError, ValueError):
                skipped["invalid_round_color"] += 1
                continue
            metrics = score_guess(target, guess, baseline)
            auto_verdict, rules, _confidence = current_auto_grade(metrics)
            samples.append(
                make_sample(
                    source_profile="population",
                    batch_seed=None,
                    sample_id=f"{row['id']}:{index}",
                    profile=None,
                    mode=str(row["mode"]) if row["mode"] is not None else None,
                    picker_type=str(row["picker_type"]) if row["picker_type"] is not None else None,
                    target=target,
                    guess=guess,
                    metrics=metrics,
                    auto_verdict=auto_verdict,
                    human_final_verdict=None,
                    reviewed=False,
                    human_agrees_with_auto=None,
                    candidate_bucket="population",
                    rules=rules,
                )
            )
    if not samples:
        raise SystemExit(f"No usable population rounds found in {db_path}")
    return samples, skipped


def load_regression_fixtures(path: Path) -> list[RegressionFixture]:
    if not path.exists():
        raise SystemExit(f"Regression fixtures not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit(f"Regression fixtures must be a JSON array: {path}")
    fixtures: list[RegressionFixture] = []
    for index, raw in enumerate(data, start=1):
        if not isinstance(raw, dict):
            raise SystemExit(f"Invalid regression fixture entry #{index} in {path}: expected object")
        try:
            fixture_id = str(raw["id"])
            target = normalize_color(raw["target"])
            guess = normalize_color(raw["guess"])
        except KeyError as exc:
            raise SystemExit(f"Regression fixture entry #{index} in {path} missing field: {exc.args[0]}") from exc
        except (TypeError, ValueError) as exc:
            raise SystemExit(f"Regression fixture entry #{index} in {path} has invalid color payload: {exc}") from exc
        expected_verdict_raw = raw.get("expected_verdict")
        expected_verdict = str(expected_verdict_raw) if expected_verdict_raw is not None else None
        if expected_verdict is not None and expected_verdict not in VALID_VERDICTS:
            raise SystemExit(f"Invalid expected_verdict in {path} entry #{index}: {expected_verdict}")
        required_shift_raw = raw.get("required_shift")
        required_shift = str(required_shift_raw) if required_shift_raw is not None else None
        if required_shift is not None and required_shift not in {"up", "down"}:
            raise SystemExit(f"Invalid required_shift in {path} entry #{index}: {required_shift}")
        baseline_score = float(raw["baseline_score"]) if raw.get("baseline_score") is not None else None
        min_shift = float(raw["min_shift"]) if raw.get("min_shift") is not None else None
        if required_shift is not None and (baseline_score is None or min_shift is None):
            raise SystemExit(
                f"Regression fixture entry #{index} in {path} must provide baseline_score and min_shift with required_shift"
            )
        if expected_verdict is None and required_shift is None:
            raise SystemExit(
                f"Regression fixture entry #{index} in {path} must provide expected_verdict or required_shift"
            )
        fixtures.append(
            RegressionFixture(
                fixture_id=fixture_id,
                target=target,
                guess=guess,
                expected_verdict=expected_verdict,
                baseline_score=baseline_score,
                required_shift=required_shift,
                min_shift=min_shift,
                min_score=float(raw["min_score"]) if raw.get("min_score") is not None else None,
                max_score=float(raw["max_score"]) if raw.get("max_score") is not None else None,
                tag=str(raw["tag"]) if raw.get("tag") is not None else None,
            )
        )
    if not fixtures:
        raise SystemExit(f"No regression fixtures found in {path}")
    return fixtures


def resolved_verdict(sample: Sample, label_source: str) -> str | None:
    if label_source == "auto":
        return sample.auto_verdict
    if label_source == "human":
        return sample.human_final_verdict
    if label_source != "hybrid":
        raise ValueError(f"Unknown label_source: {label_source!r}")
    if sample.reviewed and sample.human_final_verdict is not None:
        return sample.human_final_verdict
    return sample.auto_verdict


def challenge_weight(sample: Sample) -> float:
    return BUCKET_WEIGHTS.get(sample.candidate_bucket, 1.0)


def direction_for_verdict(verdict: str | None) -> str | None:
    if verdict == "too_low":
        return "up"
    if verdict == "too_high":
        return "down"
    return None


def hsb_to_rgb(h: float, s: float, b: float) -> tuple[float, float, float]:
    s_n = s / 100
    b_n = b / 100
    c = b_n * s_n
    hp = h / 60
    x = c * (1 - abs(hp % 2 - 1))
    m = b_n - c
    if hp < 1:
        r, g, bl = c, x, 0
    elif hp < 2:
        r, g, bl = x, c, 0
    elif hp < 3:
        r, g, bl = 0, c, x
    elif hp < 4:
        r, g, bl = 0, x, c
    elif hp < 5:
        r, g, bl = x, 0, c
    else:
        r, g, bl = c, 0, x
    return r + m, g + m, bl + m


def srgb_to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def rgb_to_xyz(r: float, g: float, b: float) -> tuple[float, float, float]:
    r = srgb_to_linear(r)
    g = srgb_to_linear(g)
    b = srgb_to_linear(b)
    return (
        0.4124564 * r + 0.3575761 * g + 0.1804375 * b,
        0.2126729 * r + 0.7151522 * g + 0.0721750 * b,
        0.0193339 * r + 0.1191920 * g + 0.9503041 * b,
    )


def xyz_to_lab(x: float, y: float, z: float) -> tuple[float, float, float]:
    xn, yn, zn = 0.95047, 1.0, 1.08883

    def f(t: float) -> float:
        return math.cbrt(t) if t > 0.008856 else 7.787 * t + 16 / 116

    fx = f(x / xn)
    fy = f(y / yn)
    fz = f(z / zn)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def hsb_to_lab(h: float, s: float, b: float) -> tuple[float, float, float]:
    return xyz_to_lab(*rgb_to_xyz(*hsb_to_rgb(h, s, b)))


def delta_e2000(lab1: tuple[float, float, float], lab2: tuple[float, float, float]) -> tuple[float, float, float, float]:
    l1, a1, b1 = lab1
    l2, a2, b2 = lab2
    c1 = math.sqrt(a1 * a1 + b1 * b1)
    c2 = math.sqrt(a2 * a2 + b2 * b2)
    cavg = (c1 + c2) / 2
    cavg7 = cavg**7
    g = 0.5 * (1 - math.sqrt(cavg7 / (cavg7 + 25**7)))
    a1p = a1 * (1 + g)
    a2p = a2 * (1 + g)
    c1p = math.sqrt(a1p * a1p + b1 * b1)
    c2p = math.sqrt(a2p * a2p + b2 * b2)
    h1p = (math.degrees(math.atan2(b1, a1p)) + 360) % 360
    h2p = (math.degrees(math.atan2(b2, a2p)) + 360) % 360
    dlp = l2 - l1
    dcp = c2p - c1p
    if c1p * c2p == 0:
        dhp = 0.0
    elif abs(h2p - h1p) <= 180:
        dhp = h2p - h1p
    elif h2p - h1p > 180:
        dhp = h2p - h1p - 360
    else:
        dhp = h2p - h1p + 360
    dhp_radians = math.radians(dhp / 2)
    dhp_term = 2 * math.sqrt(c1p * c2p) * math.sin(dhp_radians)
    lpavg = (l1 + l2) / 2
    cpavg = (c1p + c2p) / 2
    if c1p * c2p == 0:
        hpavg = h1p + h2p
    elif abs(h1p - h2p) <= 180:
        hpavg = (h1p + h2p) / 2
    elif h1p + h2p < 360:
        hpavg = (h1p + h2p + 360) / 2
    else:
        hpavg = (h1p + h2p - 360) / 2
    t = (
        1
        - 0.17 * math.cos(math.radians(hpavg - 30))
        + 0.24 * math.cos(math.radians(2 * hpavg))
        + 0.32 * math.cos(math.radians(3 * hpavg + 6))
        - 0.20 * math.cos(math.radians(4 * hpavg - 63))
    )
    sl = 1 + 0.015 * (lpavg - 50) ** 2 / math.sqrt(20 + (lpavg - 50) ** 2)
    sc = 1 + 0.045 * cpavg
    sh = 1 + 0.015 * cpavg * t
    cpavg7 = cpavg**7
    rt = -math.sin(math.radians(60 * math.exp(-((hpavg - 275) / 25) ** 2))) * 2 * math.sqrt(
        cpavg7 / (cpavg7 + 25**7)
    )
    de = math.sqrt(
        (dlp / sl) ** 2
        + (dcp / sc) ** 2
        + (dhp_term / sh) ** 2
        + rt * (dcp / sc) * (dhp_term / sh)
    )
    return de, dlp, dcp, dhp_term


def hue_distance(h1: float, h2: float) -> float:
    distance = abs(h1 - h2)
    return 360 - distance if distance > 180 else distance


def score_from_delta_e(de: float, params: ScoringParams) -> float:
    return round(10 / (1 + (de / params.curve_divisor) ** params.curve_exponent), 2)


def score_components(target: dict[str, float], guess: dict[str, float]) -> tuple[float, float, float, float, float]:
    de, dlp, dcp, dhp = delta_e2000(
        hsb_to_lab(target["h"], target["s"], target["b"]),
        hsb_to_lab(guess["h"], guess["s"], guess["b"]),
    )
    hue_dist = hue_distance(target["h"], guess["h"])
    return de, dlp, dcp, dhp, hue_dist


def apply_hue_recovery(score: float, hue_dist: float, params: ScoringParams, recovery_scale: float = 1.0) -> float:
    if hue_dist > params.hue_threshold_degrees:
        return score
    lost = 10 - score
    recovery = params.hue_lost_point_rate * (1 - hue_dist / params.hue_threshold_degrees) * max(0.0, recovery_scale)
    return round(score + lost * recovery, 2)


def build_metrics(score: float, de: float, dlp: float, dcp: float, dhp: float, hue_dist: float) -> dict[str, float]:
    return {
        "score": round(max(0.0, min(10.0, score)), 2),
        "delta_e": round(de, 1),
        "delta_l": round(dlp, 1),
        "delta_c": round(dcp, 1),
        "delta_h": round(dhp, 1),
        "hue_dist": round(hue_dist, 1),
    }


def score_guess_core(target: dict[str, float], guess: dict[str, float], params: ScoringParams) -> dict[str, float]:
    de, dlp, dcp, dhp, hue_dist = score_components(target, guess)
    score = apply_hue_recovery(score_from_delta_e(de, params), hue_dist, params)
    return build_metrics(score, de, dlp, dcp, dhp, hue_dist)


def apply_guard_penalties(metrics: dict[str, float], params: ScoringParams) -> dict[str, float]:
    score = float(metrics["score"])
    hue_dist = float(metrics["hue_dist"])
    delta_e = float(metrics["delta_e"])
    abs_delta_l = abs(float(metrics["delta_l"]))
    abs_delta_c = abs(float(metrics["delta_c"]))

    if params.same_hue_sb_penalty_rate > 0:
        sb_excess = max(0.0, max(abs_delta_l, abs_delta_c) - 14.0)
        hue_weight = max(0.0, 1 - hue_dist / max(1.0, params.hue_threshold_degrees))
        score -= params.same_hue_sb_penalty_rate * sb_excess * hue_weight

    if params.mid_hue_penalty_rate > 0 and 10.0 <= hue_dist <= 28.0 and delta_e <= 14.0:
        hue_window = max(0.0, 1 - abs(hue_dist - 19.0) / 9.0)
        delta_window = max(0.0, 1 - delta_e / 14.0)
        score -= params.mid_hue_penalty_rate * 10.0 * hue_window * delta_window

    updated = dict(metrics)
    updated["score"] = round(max(0.0, min(10.0, score)), 2)
    return updated


def apply_same_hue_rescue(metrics: dict[str, float], params: ScoringParams) -> dict[str, float]:
    score = float(metrics["score"])
    delta_e = float(metrics["delta_e"])
    hue_dist = float(metrics["hue_dist"])
    abs_delta_l = abs(float(metrics["delta_l"]))
    abs_delta_c = abs(float(metrics["delta_c"]))
    sb_extent = max(abs_delta_l, abs_delta_c)

    if params.same_hue_rescue_low_score_boost > 0 and delta_e >= 12.0 and score <= 5.75 and sb_extent >= 16.0:
        close_hue_weight = max(0.0, 1 - hue_dist / 12.0)
        sb_window = min(1.0, max(0.0, sb_extent - 16.0) / 20.0)
        low_score_window = min(1.0, max(0.0, 5.75 - score) / 2.75)
        score += params.same_hue_rescue_low_score_boost * close_hue_weight * max(0.35, sb_window) * low_score_window

    if params.same_hue_rescue_mid_score_boost > 0 and delta_e <= 18.0 and score <= 6.9 and sb_extent >= 14.0:
        very_close_hue_weight = max(0.0, 1 - hue_dist / 5.0)
        sb_window = min(1.0, max(0.0, sb_extent - 14.0) / 12.0)
        mid_score_window = min(1.0, max(0.0, 6.9 - score) / 1.9)
        score += params.same_hue_rescue_mid_score_boost * very_close_hue_weight * sb_window * mid_score_window

    updated = dict(metrics)
    updated["score"] = round(max(0.0, min(10.0, score)), 2)
    return updated


def score_guess_score_penalty(target: dict[str, float], guess: dict[str, float], params: ScoringParams) -> dict[str, float]:
    metrics = score_guess_core(target, guess, params)
    metrics = apply_guard_penalties(metrics, params)
    return apply_same_hue_rescue(metrics, params)


def effective_delta_value(
    de: float,
    dlp: float,
    dcp: float,
    hue_dist: float,
    same_hue_sb_penalty_rate: float,
    mid_hue_penalty_rate: float,
    hue_threshold_degrees: float,
) -> float:
    abs_delta_l = abs(dlp)
    abs_delta_c = abs(dcp)
    sb_excess = max(0.0, max(abs_delta_l, abs_delta_c) - 14.0)
    hue_weight = max(0.0, 1 - hue_dist / max(1.0, hue_threshold_degrees))
    hue_window = max(0.0, 1 - abs(hue_dist - 19.0) / 9.0)
    delta_window = max(0.0, 1 - de / 14.0)

    effective_de = de
    effective_de += same_hue_sb_penalty_rate * sb_excess * hue_weight
    effective_de += mid_hue_penalty_rate * 6.0 * hue_window * delta_window
    return effective_de


def score_guess(target: dict[str, float], guess: dict[str, float], params: ScoringParams) -> dict[str, float]:
    de, dlp, dcp, dhp, hue_dist = score_components(target, guess)
    effective_de = effective_delta_value(
        de,
        dlp,
        dcp,
        hue_dist,
        params.same_hue_sb_penalty_rate,
        params.mid_hue_penalty_rate,
        params.hue_threshold_degrees,
    )
    score = apply_hue_recovery(score_from_delta_e(effective_de, params), hue_dist, params)
    metrics = build_metrics(score, de, dlp, dcp, dhp, hue_dist)
    return apply_same_hue_rescue(metrics, params)


def score_guess_effective_delta(target: dict[str, float], guess: dict[str, float], candidate: CandidateSpec) -> dict[str, float]:
    de, dlp, dcp, dhp, hue_dist = score_components(target, guess)
    effective_de = effective_delta_value(
        de,
        dlp,
        dcp,
        hue_dist,
        candidate.same_hue_sb_penalty_rate,
        candidate.mid_hue_penalty_rate,
        candidate.params.hue_threshold_degrees,
    )
    score = apply_hue_recovery(score_from_delta_e(effective_de, candidate.params), hue_dist, candidate.params)
    return build_metrics(score, de, dlp, dcp, dhp, hue_dist)


def score_guess_recovery_gate(target: dict[str, float], guess: dict[str, float], candidate: CandidateSpec) -> dict[str, float]:
    de, dlp, dcp, dhp, hue_dist = score_components(target, guess)
    abs_delta_l = abs(dlp)
    abs_delta_c = abs(dcp)
    sb_excess = max(0.0, max(abs_delta_l, abs_delta_c) - 14.0)
    hue_weight = max(0.0, 1 - hue_dist / max(1.0, candidate.params.hue_threshold_degrees))
    hue_window = max(0.0, 1 - abs(hue_dist - 19.0) / 9.0)
    delta_window = max(0.0, 1 - de / 14.0)

    attenuation = candidate.same_hue_sb_penalty_rate * min(1.0, sb_excess / 18.0) * hue_weight
    attenuation += candidate.mid_hue_penalty_rate * hue_window * delta_window
    recovery_scale = max(0.0, 1.0 - attenuation)

    score = apply_hue_recovery(score_from_delta_e(de, candidate.params), hue_dist, candidate.params, recovery_scale)
    return build_metrics(score, de, dlp, dcp, dhp, hue_dist)


def score_guess_same_hue_rescue(target: dict[str, float], guess: dict[str, float], candidate: CandidateSpec) -> dict[str, float]:
    de, dlp, dcp, dhp, hue_dist = score_components(target, guess)
    score = apply_hue_recovery(score_from_delta_e(de, candidate.params), hue_dist, candidate.params)
    abs_delta_l = abs(dlp)
    abs_delta_c = abs(dcp)
    sb_extent = max(abs_delta_l, abs_delta_c)

    if de >= 12.0 and score <= 5.75 and sb_extent >= 16.0:
        close_hue_weight = max(0.0, 1 - hue_dist / 12.0)
        sb_window = min(1.0, max(0.0, sb_extent - 16.0) / 20.0)
        low_score_window = min(1.0, max(0.0, 5.75 - score) / 2.75)
        score += candidate.same_hue_sb_penalty_rate * close_hue_weight * max(0.35, sb_window) * low_score_window

    if de <= 18.0 and score <= 6.9 and sb_extent >= 14.0:
        very_close_hue_weight = max(0.0, 1 - hue_dist / 5.0)
        sb_window = min(1.0, max(0.0, sb_extent - 14.0) / 12.0)
        mid_score_window = min(1.0, max(0.0, 6.9 - score) / 1.9)
        score += candidate.mid_hue_penalty_rate * very_close_hue_weight * sb_window * mid_score_window

    return build_metrics(round(max(0.0, min(10.0, score)), 2), de, dlp, dcp, dhp, hue_dist)


def score_guess_with_candidate(target: dict[str, float], guess: dict[str, float], candidate: CandidateSpec) -> dict[str, float]:
    if candidate.family in {"effective_delta_guard", "effective_delta_rebalance"}:
        return score_guess_effective_delta(target, guess, candidate)
    if candidate.family == "same_hue_rescue":
        return score_guess_same_hue_rescue(target, guess, candidate)
    if candidate.family == "recovery_gate":
        return score_guess_recovery_gate(target, guess, candidate)
    family_params = ScoringParams(
        curve_divisor=candidate.params.curve_divisor,
        curve_exponent=candidate.params.curve_exponent,
        hue_threshold_degrees=candidate.params.hue_threshold_degrees,
        hue_lost_point_rate=candidate.params.hue_lost_point_rate,
        same_hue_sb_penalty_rate=(
            candidate.params.same_hue_sb_penalty_rate
            if candidate.family == "baseline"
            else candidate.same_hue_sb_penalty_rate if candidate.family in {"same_hue_guard", "balanced_guard"} else 0.0
        ),
        mid_hue_penalty_rate=(
            candidate.params.mid_hue_penalty_rate
            if candidate.family == "baseline"
            else candidate.mid_hue_penalty_rate if candidate.family == "balanced_guard" else 0.0
        ),
        same_hue_rescue_low_score_boost=candidate.params.same_hue_rescue_low_score_boost if candidate.family == "baseline" else 0.0,
        same_hue_rescue_mid_score_boost=candidate.params.same_hue_rescue_mid_score_boost if candidate.family == "baseline" else 0.0,
    )
    if candidate.family in {"same_hue_guard", "balanced_guard"}:
        return score_guess_score_penalty(target, guess, family_params)
    return score_guess(target, guess, family_params)


def frange(start: float, stop: float, step: float) -> list[float]:
    values: list[float] = []
    current = start
    while current <= stop + step / 2:
        values.append(round(current, 4))
        current += step
    return values


def baseline_param_grid(base: ScoringParams) -> list[ScoringParams]:
    divisors = frange(max(6.0, base.curve_divisor - 4.0), base.curve_divisor + 4.0, 0.5)
    exponents = frange(max(1.25, base.curve_exponent - 0.75), base.curve_exponent + 0.75, 0.25)
    thresholds = frange(max(10.0, base.hue_threshold_degrees - 10.0), base.hue_threshold_degrees + 10.0, 2.0)
    rates = frange(max(0.0, base.hue_lost_point_rate - 0.2), min(0.8, base.hue_lost_point_rate + 0.2), 0.05)
    return [
        ScoringParams(
            divisor,
            exponent,
            threshold,
            rate,
            base.same_hue_sb_penalty_rate,
            base.mid_hue_penalty_rate,
            base.same_hue_rescue_low_score_boost,
            base.same_hue_rescue_mid_score_boost,
        )
        for divisor, exponent, threshold, rate in itertools.product(divisors, exponents, thresholds, rates)
    ]


def guard_param_grid(base: ScoringParams) -> list[ScoringParams]:
    divisors = frange(max(8.0, base.curve_divisor - 2.0), base.curve_divisor + 2.0, 0.5)
    exponents = frange(max(1.5, base.curve_exponent - 0.5), base.curve_exponent + 0.5, 0.25)
    thresholds = frange(max(12.0, base.hue_threshold_degrees - 8.0), base.hue_threshold_degrees + 10.0, 2.0)
    rates = frange(max(0.0, base.hue_lost_point_rate - 0.15), min(0.8, base.hue_lost_point_rate + 0.05), 0.05)
    return [
        ScoringParams(divisor, exponent, threshold, rate)
        for divisor, exponent, threshold, rate in itertools.product(divisors, exponents, thresholds, rates)
    ]


def experimental_param_grid(base: ScoringParams) -> list[ScoringParams]:
    divisors = frange(max(9.0, base.curve_divisor - 1.5), base.curve_divisor + 1.0, 0.5)
    exponents = frange(max(1.75, base.curve_exponent - 0.5), base.curve_exponent + 0.25, 0.25)
    thresholds = frange(max(18.0, base.hue_threshold_degrees - 6.0), base.hue_threshold_degrees + 6.0, 2.0)
    rates = frange(max(0.2, base.hue_lost_point_rate - 0.1), min(0.6, base.hue_lost_point_rate + 0.05), 0.05)
    return [
        ScoringParams(divisor, exponent, threshold, rate)
        for divisor, exponent, threshold, rate in itertools.product(divisors, exponents, thresholds, rates)
    ]


def candidate_grid(base: ScoringParams, families: tuple[str, ...]) -> list[CandidateSpec]:
    candidates: list[CandidateSpec] = []
    for family in families:
        if family == "baseline":
            candidates.extend(CandidateSpec(family="baseline", params=params) for params in baseline_param_grid(base))
            continue

        family_params = guard_param_grid(base)
        if family == "same_hue_guard":
            penalty_rates = (0.03, 0.05, 0.07)
            candidates.extend(
                CandidateSpec(
                    family="same_hue_guard",
                    params=params,
                    same_hue_sb_penalty_rate=penalty_rate,
                )
                for params, penalty_rate in itertools.product(family_params, penalty_rates)
            )
            continue

        if family == "balanced_guard":
            same_hue_rates = (0.03, 0.05)
            mid_hue_rates = (0.1, 0.2, 0.3)
            candidates.extend(
                CandidateSpec(
                    family="balanced_guard",
                    params=params,
                    same_hue_sb_penalty_rate=same_hue_rate,
                    mid_hue_penalty_rate=mid_hue_rate,
                )
                for params, same_hue_rate, mid_hue_rate in itertools.product(family_params, same_hue_rates, mid_hue_rates)
            )
            continue

        if family == "effective_delta_guard":
            family_params = experimental_param_grid(base)
            same_hue_rates = (0.15, 0.25, 0.35)
            mid_hue_rates = (0.3, 0.5, 0.7)
            candidates.extend(
                CandidateSpec(
                    family="effective_delta_guard",
                    params=params,
                    same_hue_sb_penalty_rate=same_hue_rate,
                    mid_hue_penalty_rate=mid_hue_rate,
                )
                for params, same_hue_rate, mid_hue_rate in itertools.product(family_params, same_hue_rates, mid_hue_rates)
            )
            continue

        if family == "effective_delta_rebalance":
            family_params = experimental_param_grid(base)
            same_hue_rates = (-0.25, -0.15, -0.05, 0.05)
            mid_hue_rates = (0.3, 0.5, 0.7)
            candidates.extend(
                CandidateSpec(
                    family="effective_delta_rebalance",
                    params=params,
                    same_hue_sb_penalty_rate=same_hue_rate,
                    mid_hue_penalty_rate=mid_hue_rate,
                )
                for params, same_hue_rate, mid_hue_rate in itertools.product(family_params, same_hue_rates, mid_hue_rates)
            )
            continue

        if family == "recovery_gate":
            family_params = experimental_param_grid(base)
            same_hue_rates = (0.4, 0.6, 0.8)
            mid_hue_rates = (0.1, 0.2, 0.3)
            candidates.extend(
                CandidateSpec(
                    family="recovery_gate",
                    params=params,
                    same_hue_sb_penalty_rate=same_hue_rate,
                    mid_hue_penalty_rate=mid_hue_rate,
                )
                for params, same_hue_rate, mid_hue_rate in itertools.product(family_params, same_hue_rates, mid_hue_rates)
            )
            continue

        if family == "same_hue_rescue":
            family_params = experimental_param_grid(base)
            low_score_boosts = (1.0, 1.4, 1.8)
            mid_score_boosts = (0.4, 0.8, 1.2)
            candidates.extend(
                CandidateSpec(
                    family="same_hue_rescue",
                    params=params,
                    same_hue_sb_penalty_rate=low_score_boost,
                    mid_hue_penalty_rate=mid_score_boost,
                )
                for params, low_score_boost, mid_score_boost in itertools.product(
                    family_params,
                    low_score_boosts,
                    mid_score_boosts,
                )
            )
            continue

        raise SystemExit(f"Unhandled scorer family: {family}")
    return candidates


def evaluate_population(
    candidate: CandidateSpec,
    samples: list[Sample],
    *,
    fix_margin: float,
    preserve_tolerance: float,
) -> PopulationMetrics:
    ok_total = 0
    directional_total = 0
    ok_preserved = 0
    directional_worsen = 0
    drift_sum = 0.0
    for sample in samples:
        candidate_score = score_guess_with_candidate(sample.target, sample.guess, candidate)["score"]
        drift = candidate_score - sample.baseline_score
        verdict = sample.auto_verdict
        if verdict == "ok":
            ok_total += 1
            drift_sum += abs(drift)
            if abs(drift) <= preserve_tolerance + EPSILON:
                ok_preserved += 1
            continue
        direction = direction_for_verdict(verdict)
        if direction is None:
            continue
        directional_total += 1
        if (direction == "up" and drift <= -fix_margin - EPSILON) or (
            direction == "down" and drift >= fix_margin + EPSILON
        ):
            directional_worsen += 1
    return PopulationMetrics(
        ok_total=ok_total,
        directional_total=directional_total,
        preserve_ok_rate=ok_preserved / ok_total if ok_total else 1.0,
        directional_worsen_rate=directional_worsen / directional_total if directional_total else 0.0,
        mean_abs_drift_ok=drift_sum / ok_total if ok_total else 0.0,
    )


def evaluate_challenge(
    candidate: CandidateSpec,
    samples: list[Sample],
    *,
    label_source: str,
    fix_margin: float,
    preserve_tolerance: float,
) -> ChallengeMetrics:
    directional_total_weight = 0.0
    fixed_weight = 0.0
    helped_weight = 0.0
    worsened_weight = 0.0
    soft_objective = 0.0
    for sample in samples:
        weight = challenge_weight(sample)
        candidate_score = score_guess_with_candidate(sample.target, sample.guess, candidate)["score"]
        drift = candidate_score - sample.baseline_score
        verdict = resolved_verdict(sample, label_source)
        if verdict == "ok":
            soft_objective += weight * max(-1.0, 1 - abs(drift) / preserve_tolerance)
            continue
        direction = direction_for_verdict(verdict)
        if direction is None:
            continue
        directional_total_weight += weight
        signed_shift = drift if direction == "up" else -drift
        soft_objective += weight * max(-1.0, min(1.0, signed_shift / fix_margin))
        if direction == "up":
            if drift >= fix_margin + EPSILON:
                fixed_weight += weight
            elif drift > 0:
                helped_weight += weight
            elif drift <= -fix_margin - EPSILON:
                worsened_weight += weight
        else:
            if drift <= -fix_margin - EPSILON:
                fixed_weight += weight
            elif drift < 0:
                helped_weight += weight
            elif drift >= fix_margin + EPSILON:
                worsened_weight += weight
    return ChallengeMetrics(
        directional_total_weight=directional_total_weight,
        fix_wrong_rate=fixed_weight / directional_total_weight if directional_total_weight else 0.0,
        help_wrong_rate=helped_weight / directional_total_weight if directional_total_weight else 0.0,
        worsen_wrong_rate=worsened_weight / directional_total_weight if directional_total_weight else 0.0,
        soft_objective=soft_objective,
    )


def evaluate_regression(candidate: CandidateSpec, fixtures: list[RegressionFixture]) -> RegressionMetrics:
    failed_ids: list[str] = []
    for fixture in fixtures:
        metrics = score_guess_with_candidate(fixture.target, fixture.guess, candidate)
        verdict, _rules, _confidence = current_auto_grade(metrics)
        score = metrics["score"]
        failed = False
        if fixture.required_shift is not None:
            assert fixture.baseline_score is not None
            assert fixture.min_shift is not None
            shift = score - fixture.baseline_score
            if fixture.required_shift == "up" and shift < fixture.min_shift - EPSILON:
                failed = True
            if fixture.required_shift == "down" and shift > -fixture.min_shift + EPSILON:
                failed = True
        elif fixture.expected_verdict is not None:
            failed = verdict != fixture.expected_verdict
        if fixture.min_score is not None and score < fixture.min_score - EPSILON:
            failed = True
        if fixture.max_score is not None and score > fixture.max_score + EPSILON:
            failed = True
        if failed:
            failed_ids.append(fixture.fixture_id)
    total = len(fixtures)
    return RegressionMetrics(
        total=total,
        pass_rate=(total - len(failed_ids)) / total if total else 1.0,
        failed_ids=tuple(failed_ids),
    )


def evaluate_candidate_result(
    candidate: CandidateSpec,
    *,
    population_samples: list[Sample],
    challenge_samples: list[Sample],
    regression_fixtures: list[RegressionFixture],
    label_source: str,
    fix_margin: float,
    preserve_tolerance: float,
    baseline_population: PopulationMetrics,
    population_preserve_drop_budget: float,
    population_directional_worsen_budget: float,
    challenge_worsen_ceiling: float,
) -> CandidateResult:
    population = evaluate_population(
        candidate,
        population_samples,
        fix_margin=fix_margin,
        preserve_tolerance=preserve_tolerance,
    )
    challenge = evaluate_challenge(
        candidate,
        challenge_samples,
        label_source=label_source,
        fix_margin=fix_margin,
        preserve_tolerance=preserve_tolerance,
    )
    regression = evaluate_regression(candidate, regression_fixtures)
    gate_failures: list[str] = []
    if regression.failed_ids:
        gate_failures.append(f"regression_failed:{len(regression.failed_ids)}")
    preserve_floor = baseline_population.preserve_ok_rate - population_preserve_drop_budget
    if population.preserve_ok_rate < preserve_floor - EPSILON:
        gate_failures.append("population_preserve_budget")
    worsen_ceiling = baseline_population.directional_worsen_rate + population_directional_worsen_budget
    if population.directional_worsen_rate > worsen_ceiling + EPSILON:
        gate_failures.append("population_worsen_budget")
    if challenge.worsen_wrong_rate > challenge_worsen_ceiling + EPSILON:
        gate_failures.append("challenge_worsen_ceiling")
    return CandidateResult(
        candidate=candidate,
        population=population,
        challenge=challenge,
        regression=regression,
        gate_failures=tuple(gate_failures),
    )


def result_rank_key(result: CandidateResult) -> tuple[bool, float, float, float, float, float, float]:
    return (
        not result.gate_failures,
        result.challenge.fix_wrong_rate,
        result.challenge.help_wrong_rate,
        -result.challenge.worsen_wrong_rate,
        result.population.preserve_ok_rate,
        -result.population.mean_abs_drift_ok,
        result.challenge.soft_objective,
    )


def summarize_result(label: str, result: CandidateResult) -> str:
    gates = "pass" if not result.gate_failures else ",".join(result.gate_failures)
    family_bits = [result.candidate.family]
    if result.candidate.same_hue_sb_penalty_rate > 0:
        family_bits.append(f"sb={result.candidate.same_hue_sb_penalty_rate:.2f}")
    if result.candidate.mid_hue_penalty_rate > 0:
        family_bits.append(f"mid={result.candidate.mid_hue_penalty_rate:.2f}")
    family_text = "/".join(family_bits)
    params_bits = [
        f"k={result.candidate.params.curve_divisor:g}",
        f"exp={result.candidate.params.curve_exponent:g}",
        f"hue≤{result.candidate.params.hue_threshold_degrees:g}",
        f"recover={result.candidate.params.hue_lost_point_rate:.2f}",
    ]
    if result.candidate.params.same_hue_rescue_low_score_boost > 0:
        params_bits.append(f"rescue_low={result.candidate.params.same_hue_rescue_low_score_boost:.2f}")
    if result.candidate.params.same_hue_rescue_mid_score_boost > 0:
        params_bits.append(f"rescue_mid={result.candidate.params.same_hue_rescue_mid_score_boost:.2f}")
    return (
        f"{label}: {family_text} | "
        f"{', '.join(params_bits)} | "
        f"population preserve={result.population.preserve_ok_rate:.1%} "
        f"worsen={result.population.directional_worsen_rate:.1%} drift={result.population.mean_abs_drift_ok:.2f} | "
        f"challenge fix={result.challenge.fix_wrong_rate:.1%} "
        f"help={result.challenge.help_wrong_rate:.1%} "
        f"worsen={result.challenge.worsen_wrong_rate:.1%} soft={result.challenge.soft_objective:.2f} | "
        f"regression={result.regression.pass_rate:.1%} | gates={gates}"
    )


def candidate_name(candidate: CandidateSpec) -> str:
    parts = [candidate.family]
    if candidate.same_hue_sb_penalty_rate > 0:
        parts.append(f"sb={candidate.same_hue_sb_penalty_rate:.2f}")
    if candidate.mid_hue_penalty_rate > 0:
        parts.append(f"mid={candidate.mid_hue_penalty_rate:.2f}")
    return "/".join(parts)


def challenge_status_for_sample(sample: Sample, candidate: CandidateSpec, *, label_source: str, fix_margin: float) -> dict[str, Any] | None:
    verdict = resolved_verdict(sample, label_source)
    if verdict is None:
        return None
    candidate_metrics = score_guess_with_candidate(sample.target, sample.guess, candidate)
    candidate_score = float(candidate_metrics["score"])
    drift = round(candidate_score - sample.baseline_score, 2)
    direction = direction_for_verdict(verdict)
    record: dict[str, Any] = {
        "sample_id": sample.sample_id,
        "profile": sample.profile,
        "candidate_bucket": sample.candidate_bucket,
        "review_state": "reviewed" if sample.reviewed else "inherited",
        "verdict": verdict,
        "baseline_score": sample.baseline_score,
        "candidate_score": candidate_score,
        "drift": drift,
        "weight": challenge_weight(sample),
        "delta_e": float(candidate_metrics["delta_e"]),
        "hue_dist": float(candidate_metrics["hue_dist"]),
        "target": sample.target,
        "guess": sample.guess,
    }
    if direction is None:
        record["status"] = "abstain"
        return record
    if direction == "up":
        if drift >= fix_margin + EPSILON:
            status = "fixed"
        elif drift > 0:
            status = "helped"
        elif drift <= -fix_margin - EPSILON:
            status = "worsened"
        else:
            status = "unchanged"
    else:
        if drift <= -fix_margin - EPSILON:
            status = "fixed"
        elif drift < 0:
            status = "helped"
        elif drift >= fix_margin + EPSILON:
            status = "worsened"
        else:
            status = "unchanged"
    record["status"] = status
    return record


def population_status_for_sample(
    sample: Sample,
    candidate: CandidateSpec,
    *,
    fix_margin: float,
    preserve_tolerance: float,
) -> dict[str, Any]:
    candidate_metrics = score_guess_with_candidate(sample.target, sample.guess, candidate)
    candidate_score = float(candidate_metrics["score"])
    drift = round(candidate_score - sample.baseline_score, 2)
    direction = direction_for_verdict(sample.auto_verdict)
    record: dict[str, Any] = {
        "sample_id": sample.sample_id,
        "mode": sample.mode or "unknown",
        "mode_picker": f"{sample.mode or 'unknown'}/{sample.picker_type or 'unknown'}",
        "picker_type": sample.picker_type or "unknown",
        "score_band": sample.score_band,
        "hue_band": sample.hue_band,
        "delta_e_band": sample.delta_e_band,
        "verdict": sample.auto_verdict,
        "baseline_score": sample.baseline_score,
        "candidate_score": candidate_score,
        "drift": drift,
        "delta_e": float(candidate_metrics["delta_e"]),
        "hue_dist": float(candidate_metrics["hue_dist"]),
        "target": sample.target,
        "guess": sample.guess,
    }
    if sample.auto_verdict == "ok":
        record["status"] = "preserved" if abs(drift) <= preserve_tolerance + EPSILON else "drifted"
        return record
    if direction is None:
        record["status"] = "abstain"
        return record
    if (direction == "up" and drift <= -fix_margin - EPSILON) or (direction == "down" and drift >= fix_margin + EPSILON):
        record["status"] = "worsened"
    else:
        record["status"] = "safe"
    return record


def aggregate_status_rows(rows: list[dict[str, Any]], key_name: str) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "count": 0,
            "weight": 0.0,
            "fixed": 0.0,
            "helped": 0.0,
            "worsened": 0.0,
            "unchanged": 0.0,
            "preserved": 0,
            "drifted": 0,
        }
    )
    for row in rows:
        key = str(row.get(key_name) or "<none>")
        bucket = grouped[key]
        bucket["count"] += 1
        weight = float(row.get("weight", 1.0))
        bucket["weight"] += weight
        status = str(row["status"])
        if status in {"fixed", "helped", "worsened", "unchanged"}:
            bucket[status] += weight
        elif status in {"preserved", "drifted"}:
            bucket[status] += 1
    summaries: list[dict[str, Any]] = []
    for key, bucket in grouped.items():
        directional_weight = bucket["fixed"] + bucket["helped"] + bucket["worsened"] + bucket["unchanged"]
        summaries.append(
            {
                key_name: key,
                "count": bucket["count"],
                "weight": round(bucket["weight"], 2),
                "fix_rate": round(bucket["fixed"] / directional_weight, 4) if directional_weight else None,
                "help_rate": round(bucket["helped"] / directional_weight, 4) if directional_weight else None,
                "worsen_rate": round(bucket["worsened"] / directional_weight, 4) if directional_weight else None,
                "unchanged_rate": round(bucket["unchanged"] / directional_weight, 4) if directional_weight else None,
                "preserve_rate": round(bucket["preserved"] / (bucket["preserved"] + bucket["drifted"]), 4)
                if bucket["preserved"] + bucket["drifted"]
                else None,
                "drifted": bucket["drifted"],
            }
        )
    summaries.sort(key=lambda item: (-item["count"], str(item[key_name])))
    return summaries


def top_rows(rows: list[dict[str, Any]], *, status_order: dict[str, int], limit: int) -> list[dict[str, Any]]:
    def sort_key(row: dict[str, Any]) -> tuple[int, float, float, str]:
        return (
            status_order.get(str(row["status"]), 99),
            -abs(float(row["drift"])),
            -float(row.get("weight", 1.0)),
            str(row.get("sample_id") or ""),
        )

    return sorted(rows, key=sort_key)[:limit]


def analyze_challenge_candidate(
    candidate: CandidateSpec,
    samples: list[Sample],
    *,
    label_source: str,
    fix_margin: float,
    preserve_tolerance: float,
    limit: int,
) -> dict[str, Any]:
    rows = [
        row
        for sample in samples
        if (row := challenge_status_for_sample(sample, candidate, label_source=label_source, fix_margin=fix_margin)) is not None
    ]
    directional_rows = [row for row in rows if row["status"] in {"fixed", "helped", "worsened", "unchanged"}]
    ok_rows = [row for row in rows if row["verdict"] == "ok"]
    return {
        "by_profile": aggregate_status_rows(directional_rows, "profile"),
        "by_bucket": aggregate_status_rows(directional_rows, "candidate_bucket"),
        "by_review_state": aggregate_status_rows(directional_rows, "review_state"),
        "top_residuals": top_rows(
            [row for row in directional_rows if row["status"] in {"worsened", "unchanged"}],
            status_order={"worsened": 0, "unchanged": 1},
            limit=limit,
        ),
        "top_fixes": top_rows(
            [row for row in directional_rows if row["status"] in {"fixed", "helped"}],
            status_order={"fixed": 0, "helped": 1},
            limit=limit,
        ),
        "ok_drift_outliers": top_rows(
            [
                {
                    **row,
                    "status": "drifted" if abs(float(row["drift"])) > preserve_tolerance + EPSILON else "preserved",
                }
                for row in ok_rows
                if abs(float(row["drift"])) > preserve_tolerance + EPSILON
            ],
            status_order={"drifted": 0},
            limit=limit,
        ),
    }


def analyze_population_candidate(
    candidate: CandidateSpec,
    samples: list[Sample],
    *,
    fix_margin: float,
    preserve_tolerance: float,
    limit: int,
) -> dict[str, Any]:
    rows = [
        population_status_for_sample(
            sample,
            candidate,
            fix_margin=fix_margin,
            preserve_tolerance=preserve_tolerance,
        )
        for sample in samples
    ]
    ok_rows = [row for row in rows if row["verdict"] == "ok"]
    directional_rows = [row for row in rows if row["verdict"] in {"too_high", "too_low"}]
    return {
        "ok_by_mode_picker": aggregate_status_rows(ok_rows, "mode_picker"),
        "ok_by_score_band": aggregate_status_rows(ok_rows, "score_band"),
        "directional_by_mode_picker": aggregate_status_rows(directional_rows, "mode_picker"),
        "top_ok_drifts": top_rows(
            [row for row in ok_rows if row["status"] == "drifted"],
            status_order={"drifted": 0},
            limit=limit,
        ),
        "top_directional_worsen": top_rows(
            [row for row in directional_rows if row["status"] == "worsened"],
            status_order={"worsened": 0},
            limit=limit,
        ),
    }


def candidate_analysis(
    candidate: CandidateSpec,
    *,
    challenge_samples: list[Sample],
    population_samples: list[Sample],
    label_source: str,
    fix_margin: float,
    preserve_tolerance: float,
    limit: int,
) -> dict[str, Any]:
    return {
        "candidate": candidate_name(candidate),
        "challenge": analyze_challenge_candidate(
            candidate,
            challenge_samples,
            label_source=label_source,
            fix_margin=fix_margin,
            preserve_tolerance=preserve_tolerance,
            limit=limit,
        ),
        "population": analyze_population_candidate(
            candidate,
            population_samples,
            fix_margin=fix_margin,
            preserve_tolerance=preserve_tolerance,
            limit=limit,
        ),
    }


def format_sample_row(row: dict[str, Any], label: str) -> str:
    return (
        f"{label}={row.get(label)} | id={row.get('sample_id')} | verdict={row.get('verdict')} "
        f"| status={row.get('status')} | {row.get('baseline_score'):.2f}->{row.get('candidate_score'):.2f} "
        f"(Δ{row.get('drift'):+.2f}) | dE={row.get('delta_e'):.1f} | hue={row.get('hue_dist'):.1f}"
    )


def print_candidate_analysis(label: str, analysis: dict[str, Any]) -> None:
    print(f"{label}: {analysis['candidate']}")
    print("  challenge by profile:")
    for row in analysis["challenge"]["by_profile"][:6]:
        print(
            f"    {row['profile']}: n={row['count']} "
            f"fix={row['fix_rate']:.1%} help={row['help_rate']:.1%} "
            f"worsen={row['worsen_rate']:.1%} unchanged={row['unchanged_rate']:.1%}"
        )
    print("  challenge by bucket:")
    for row in analysis["challenge"]["by_bucket"]:
        print(
            f"    {row['candidate_bucket']}: n={row['count']} "
            f"fix={row['fix_rate']:.1%} help={row['help_rate']:.1%} worsen={row['worsen_rate']:.1%}"
        )
    print("  challenge residuals:")
    for row in analysis["challenge"]["top_residuals"]:
        print(f"    {format_sample_row(row, 'profile')}")
    print("  challenge strongest fixes:")
    for row in analysis["challenge"]["top_fixes"]:
        print(f"    {format_sample_row(row, 'profile')}")
    print("  population ok drift hotspots:")
    for row in analysis["population"]["ok_by_mode_picker"]:
        if row["preserve_rate"] is None:
            continue
        print(
            f"    mode/picker={row['mode_picker']}: n={row['count']} "
            f"preserve={row['preserve_rate']:.1%} drifted={row['drifted']}"
        )
    print("  population ok drift outliers:")
    for row in analysis["population"]["top_ok_drifts"]:
        print(f"    {format_sample_row(row, 'mode_picker')}")

def profile_summary_population(samples: list[Sample]) -> dict[str, Any]:
    verdicts = Counter(sample.auto_verdict for sample in samples)
    mode_picker = Counter((sample.mode or "unknown", sample.picker_type or "unknown") for sample in samples)
    score_bands = Counter(sample.score_band for sample in samples if sample.score_band is not None)
    hue_bands = Counter(sample.hue_band for sample in samples if sample.hue_band is not None)
    delta_bands = Counter(sample.delta_e_band for sample in samples if sample.delta_e_band is not None)
    return {
        "count": len(samples),
        "verdicts": dict(verdicts),
        "mode_picker": {f"{mode}/{picker}": count for (mode, picker), count in sorted(mode_picker.items())},
        "score_bands": dict(sorted(score_bands.items())),
        "hue_bands": dict(sorted(hue_bands.items())),
        "delta_e_bands": dict(sorted(delta_bands.items())),
    }


def profile_summary_challenge(samples: list[Sample], label_source: str) -> dict[str, Any]:
    resolved = Counter(resolved_verdict(sample, label_source) for sample in samples)
    buckets = Counter(sample.candidate_bucket for sample in samples)
    profiles = Counter(sample.profile or "<none>" for sample in samples)
    review = Counter("reviewed" if sample.reviewed else "inherited" for sample in samples)
    return {
        "count": len(samples),
        "resolved_verdicts": dict(resolved),
        "candidate_buckets": dict(sorted(buckets.items())),
        "profiles": dict(sorted(profiles.items())),
        "review_state": dict(sorted(review.items())),
    }


def profile_summary_regression(fixtures: list[RegressionFixture]) -> dict[str, Any]:
    tags = Counter(fixture.tag or "<untagged>" for fixture in fixtures)
    requirements = Counter(
        f"shift:{fixture.required_shift}" if fixture.required_shift is not None else f"verdict:{fixture.expected_verdict}"
        for fixture in fixtures
    )
    return {
        "count": len(fixtures),
        "tags": dict(sorted(tags.items())),
        "requirements": dict(sorted(requirements.items())),
    }


def print_population_summary(summary: dict[str, Any], skipped: Counter[str]) -> None:
    print(
        f"Population: {summary['count']} rounds | verdicts={summary['verdicts']} "
        f"| mode/picker={summary['mode_picker']}"
    )
    print(
        f"  score_bands={summary['score_bands']} | hue_bands={summary['hue_bands']} | "
        f"deltaE_bands={summary['delta_e_bands']}"
    )
    if skipped:
        print(f"  skipped_rows={dict(sorted(skipped.items()))}")


def print_challenge_summary(summary: dict[str, Any]) -> None:
    print(
        f"Challenge: {summary['count']} rows | resolved={summary['resolved_verdicts']} "
        f"| review={summary['review_state']}"
    )
    print(f"  buckets={summary['candidate_buckets']}")
    print(f"  profiles={summary['profiles']}")


def print_regression_summary(summary: dict[str, Any]) -> None:
    print(
        f"Regression: {summary['count']} fixtures | requirements={summary['requirements']} "
        f"| tags={summary['tags']}"
    )


def print_human_audit_summary(samples: list[Sample]) -> None:
    reviewed = [sample for sample in samples if sample.reviewed and sample.human_final_verdict is not None]
    if not reviewed:
        return
    comparable = [sample for sample in reviewed if sample.human_final_verdict in VALID_VERDICTS]
    if not comparable:
        return
    agreements = sum(1 for sample in comparable if sample.human_final_verdict == sample.auto_verdict)
    auto_abstain = sum(1 for sample in comparable if sample.auto_verdict == "abstain")
    human_directional = sum(1 for sample in comparable if sample.human_final_verdict in {"too_high", "too_low"})
    print(
        f"Human audit: {len(comparable)} reviewed | auto-human agreement={agreements / len(comparable):.1%} "
        f"| auto abstain={auto_abstain} | human directional={human_directional}"
    )


def candidate_to_dict(result: CandidateResult) -> dict[str, Any]:
    return {
        "candidate": {
            "family": result.candidate.family,
            "params": result.candidate.params.__dict__,
            "same_hue_sb_penalty_rate": result.candidate.same_hue_sb_penalty_rate,
            "mid_hue_penalty_rate": result.candidate.mid_hue_penalty_rate,
        },
        "gate_failures": list(result.gate_failures),
        "population": {
            "ok_total": result.population.ok_total,
            "directional_total": result.population.directional_total,
            "preserve_ok_rate": round(result.population.preserve_ok_rate, 6),
            "directional_worsen_rate": round(result.population.directional_worsen_rate, 6),
            "mean_abs_drift_ok": round(result.population.mean_abs_drift_ok, 6),
        },
        "challenge": {
            "directional_total_weight": round(result.challenge.directional_total_weight, 6),
            "fix_wrong_rate": round(result.challenge.fix_wrong_rate, 6),
            "help_wrong_rate": round(result.challenge.help_wrong_rate, 6),
            "worsen_wrong_rate": round(result.challenge.worsen_wrong_rate, 6),
            "soft_objective": round(result.challenge.soft_objective, 6),
        },
        "regression": {
            "total": result.regression.total,
            "pass_rate": round(result.regression.pass_rate, 6),
            "failed_ids": list(result.regression.failed_ids),
        },
    }


def gate_failure_summary(results: list[CandidateResult]) -> dict[str, int]:
    counts = Counter[str]()
    for result in results:
        for failure in result.gate_failures:
            counts[failure] += 1
    return dict(sorted(counts.items()))


def best_result_by_family(results: list[CandidateResult]) -> dict[str, CandidateResult]:
    winners: dict[str, CandidateResult] = {}
    for result in results:
        family = result.candidate.family
        if family not in winners:
            winners[family] = result
    return winners


def write_output(
    path: Path,
    *,
    families: tuple[str, ...],
    baseline: ScoringParams,
    baseline_result: CandidateResult,
    winner: CandidateResult,
    all_results: list[CandidateResult],
    valid_results: list[CandidateResult],
    results: list[CandidateResult],
    profile_inputs: dict[str, Any],
    label_source: str,
    fix_margin: float,
    preserve_tolerance: float,
    population_preserve_drop_budget: float,
    population_directional_worsen_budget: float,
    challenge_worsen_ceiling: float,
    analyses: dict[str, Any],
) -> None:
    gate_failures = gate_failure_summary(all_results)
    family_winners = {family: candidate_to_dict(result) for family, result in best_result_by_family(valid_results).items()}
    payload = {
        "mode": "multi-profile",
        "families": list(families),
        "label_source": label_source,
        "baseline": baseline.__dict__,
        "gate_config": {
            "population_preserve_drop_budget": population_preserve_drop_budget,
            "population_directional_worsen_budget": population_directional_worsen_budget,
            "challenge_worsen_ceiling": challenge_worsen_ceiling,
            "fix_margin": fix_margin,
            "preserve_tolerance": preserve_tolerance,
        },
        "profile_inputs": profile_inputs,
        "baseline_result": candidate_to_dict(baseline_result),
        "winner": candidate_to_dict(winner),
        "family_winners": family_winners,
        "gate_failures": gate_failures,
        "analysis": analyses,
        "results": [candidate_to_dict(result) for result in results],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    args = parse_args()
    families = parse_families(args.families)
    batches, challenge_samples = load_challenge_samples(args.path)
    if not challenge_samples:
        raise SystemExit(f"No usable challenge samples found in {args.path}")
    baseline = extract_baseline_params(batches)
    population_samples, population_skipped = load_population_samples(args.population_db, baseline)
    regression_fixtures = load_regression_fixtures(args.regression_fixtures)

    challenge_directional = sum(
        1 for sample in challenge_samples if direction_for_verdict(resolved_verdict(sample, args.label_source)) is not None
    )
    if challenge_directional == 0:
        raise SystemExit("No directional challenge rows found after label resolution.")

    population_summary = profile_summary_population(population_samples)
    challenge_summary = profile_summary_challenge(challenge_samples, args.label_source)
    regression_summary = profile_summary_regression(regression_fixtures)

    print(f"Loaded challenge export {args.path}")
    print_population_summary(population_summary, population_skipped)
    print_challenge_summary(challenge_summary)
    print_regression_summary(regression_summary)
    print_human_audit_summary(challenge_samples)
    baseline_bits = [
        f"k={baseline.curve_divisor:g}",
        f"exp={baseline.curve_exponent:g}",
        f"hue≤{baseline.hue_threshold_degrees:g}",
        f"recover={baseline.hue_lost_point_rate:.2f}",
    ]
    if baseline.same_hue_sb_penalty_rate > 0:
        baseline_bits.append(f"sb={baseline.same_hue_sb_penalty_rate:.2f}")
    if baseline.mid_hue_penalty_rate > 0:
        baseline_bits.append(f"mid={baseline.mid_hue_penalty_rate:.2f}")
    if baseline.same_hue_rescue_low_score_boost > 0:
        baseline_bits.append(f"rescue_low={baseline.same_hue_rescue_low_score_boost:.2f}")
    if baseline.same_hue_rescue_mid_score_boost > 0:
        baseline_bits.append(f"rescue_mid={baseline.same_hue_rescue_mid_score_boost:.2f}")
    print(f"Baseline params: {', '.join(baseline_bits)}")
    print(
        "Gate config: "
        f"preserve_drop≤{args.population_preserve_drop_budget:.1%}, "
        f"directional_worsen+≤{args.population_directional_worsen_budget:.1%}, "
        f"challenge_worsen≤{args.challenge_worsen_ceiling:.1%}, "
        f"fix_margin={args.fix_margin:g}, preserve_tolerance={args.preserve_tolerance:g}"
    )
    print(f"Scorer families: {', '.join(families)}")

    baseline_candidate = CandidateSpec(family="baseline", params=baseline)

    baseline_population = evaluate_population(
        baseline_candidate,
        population_samples,
        fix_margin=args.fix_margin,
        preserve_tolerance=args.preserve_tolerance,
    )
    baseline_result = evaluate_candidate_result(
        baseline_candidate,
        population_samples=population_samples,
        challenge_samples=challenge_samples,
        regression_fixtures=regression_fixtures,
        label_source=args.label_source,
        fix_margin=args.fix_margin,
        preserve_tolerance=args.preserve_tolerance,
        baseline_population=baseline_population,
        population_preserve_drop_budget=args.population_preserve_drop_budget,
        population_directional_worsen_budget=args.population_directional_worsen_budget,
        challenge_worsen_ceiling=args.challenge_worsen_ceiling,
    )

    candidates = candidate_grid(baseline, families)
    print(f"Evaluating {len(candidates)} parameter sets...")
    results = sorted(
        (
            evaluate_candidate_result(
                candidate,
                population_samples=population_samples,
                challenge_samples=challenge_samples,
                regression_fixtures=regression_fixtures,
                label_source=args.label_source,
                fix_margin=args.fix_margin,
                preserve_tolerance=args.preserve_tolerance,
                baseline_population=baseline_population,
                population_preserve_drop_budget=args.population_preserve_drop_budget,
                population_directional_worsen_budget=args.population_directional_worsen_budget,
                challenge_worsen_ceiling=args.challenge_worsen_ceiling,
            )
            for candidate in candidates
        ),
        key=result_rank_key,
        reverse=True,
    )

    valid_results = [result for result in results if not result.gate_failures]
    if not valid_results:
        raise SystemExit("No candidates passed regression and population gates.")
    winner = valid_results[0]

    print()
    print(summarize_result("Baseline", baseline_result))
    print(summarize_result("Winner", winner))
    print(f"Rejected by gates: {len(results) - len(valid_results)} / {len(results)}")
    rejected_summary = gate_failure_summary([result for result in results if result.gate_failures])
    if rejected_summary:
        print(f"Gate failure counts: {rejected_summary}")
    print()
    print("Best valid candidate by family:")
    for family, result in best_result_by_family(valid_results).items():
        print(f"  {family}: {summarize_result('Candidate', result)[11:]}")
    print()
    print("Top valid candidates:")
    for index, result in enumerate(valid_results[: args.top], start=1):
        print(f"  {index}. {summarize_result('Candidate', result)[11:]}")

    family_winners = best_result_by_family(valid_results)
    winner_analysis = candidate_analysis(
        winner.candidate,
        challenge_samples=challenge_samples,
        population_samples=population_samples,
        label_source=args.label_source,
        fix_margin=args.fix_margin,
        preserve_tolerance=args.preserve_tolerance,
        limit=args.analysis_limit,
    )
    baseline_family_analysis = None
    if "baseline" in family_winners:
        baseline_family_analysis = candidate_analysis(
            family_winners["baseline"].candidate,
            challenge_samples=challenge_samples,
            population_samples=population_samples,
            label_source=args.label_source,
            fix_margin=args.fix_margin,
            preserve_tolerance=args.preserve_tolerance,
            limit=args.analysis_limit,
        )
    print()
    print_candidate_analysis("Winner analysis", winner_analysis)
    if baseline_family_analysis is not None and family_winners["baseline"].candidate != winner.candidate:
        print()
        print_candidate_analysis("Best baseline analysis", baseline_family_analysis)

    analyses = {
        "winner": winner_analysis,
        "family_winners": {
            family: candidate_analysis(
                result.candidate,
                challenge_samples=challenge_samples,
                population_samples=population_samples,
                label_source=args.label_source,
                fix_margin=args.fix_margin,
                preserve_tolerance=args.preserve_tolerance,
                limit=args.analysis_limit,
            )
            for family, result in family_winners.items()
        },
    }

    if args.output:
        write_output(
            args.output,
            families=families,
            baseline=baseline,
            baseline_result=baseline_result,
            winner=winner,
            all_results=results,
            valid_results=valid_results,
            results=valid_results[: args.top],
            profile_inputs={
                "population": population_summary,
                "challenge": challenge_summary,
                "regression": regression_summary,
            },
            label_source=args.label_source,
            fix_margin=args.fix_margin,
            preserve_tolerance=args.preserve_tolerance,
            population_preserve_drop_budget=args.population_preserve_drop_budget,
            population_directional_worsen_budget=args.population_directional_worsen_budget,
            challenge_worsen_ceiling=args.challenge_worsen_ceiling,
            analyses=analyses,
        )
        print()
        print(f"Wrote ranked candidates to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
