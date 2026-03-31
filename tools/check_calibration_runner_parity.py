#!/usr/bin/env python3
"""Verify the Python calibration runner matches the shared JS scorer."""

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys

from check_scoring_parity import APP_FILE, extract_block
from run_calibration import ScoringParams, score_guess

FIXTURES = [
    {"target": {"h": 12.0, "s": 80.0, "b": 76.0}, "guess": {"h": 18.0, "s": 72.0, "b": 68.0}},
    {"target": {"h": 210.0, "s": 82.0, "b": 60.0}, "guess": {"h": 205.0, "s": 58.0, "b": 31.0}},
    {"target": {"h": 285.0, "s": 72.0, "b": 63.0}, "guess": {"h": 338.0, "s": 74.0, "b": 62.0}},
    {"target": {"h": 140.0, "s": 44.0, "b": 54.0}, "guess": {"h": 246.0, "s": 58.0, "b": 61.0}},
]

PARAMS = [
    ScoringParams(10.0, 2.25, 33.0, 0.55, 0.25, 0.30, 0.0, 0.0),
    ScoringParams(11.0, 2.5, 31.0, 0.45, 0.15, 0.20, 0.8, 0.6),
]


def js_results() -> list[list[dict[str, object]]]:
    block = extract_block(APP_FILE)
    block = re.sub(r"const SCORING_PARAMS =", "let SCORING_PARAMS =", block, count=1)
    node_source = f"""
{block}
const fixtures = {json.dumps(FIXTURES)};
const paramSets = {json.dumps([params.__dict__ for params in PARAMS])};
const results = paramSets.map((params) => {{
  SCORING_PARAMS = {{
    curve: {{ divisor: params.curve_divisor, exponent: params.curve_exponent }},
    hueRecovery: {{ thresholdDegrees: params.hue_threshold_degrees, lostPointRate: params.hue_lost_point_rate }},
    guardPenalty: {{
      sameHueSbPenaltyRate: params.same_hue_sb_penalty_rate,
      midHuePenaltyRate: params.mid_hue_penalty_rate,
    }},
    sameHueRescue: {{
      lowScoreBoost: params.same_hue_rescue_low_score_boost,
      midScoreBoost: params.same_hue_rescue_mid_score_boost,
    }},
    tiers: {{ elite: 8.5, strong: 5.5, learning: 2.5 }},
  }};
  return fixtures.map((fixture) => scoreGuess(fixture.target, fixture.guess));
}});
console.log(JSON.stringify(results));
"""
    completed = subprocess.run(
        ["node", "-e", node_source],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def py_results() -> list[list[dict[str, object]]]:
    results: list[list[dict[str, object]]] = []
    for params in PARAMS:
        param_results: list[dict[str, object]] = []
        for fixture in FIXTURES:
            result = score_guess(fixture["target"], fixture["guess"], params)
            param_results.append(
                {
                    "score": result["score"],
                    "delta_e": result["delta_e"],
                    "delta_l": result["delta_l"],
                    "delta_c": result["delta_c"],
                    "delta_h": result["delta_h"],
                    "hueDist": result["hue_dist"],
                    "target_name": "unused",
                    "guess_name": "unused",
                }
            )
        results.append(param_results)
    return results


def main() -> int:
    js = js_results()
    py = py_results()
    for param_index, (js_group, py_group) in enumerate(zip(js, py, strict=True)):
        for fixture_index, (js_result, py_result) in enumerate(zip(js_group, py_group, strict=True)):
            for key in ("score", "delta_e", "delta_l", "delta_c", "delta_h", "hueDist"):
                if abs(float(js_result[key]) - float(py_result[key])) > 1e-9:
                    print(
                        f"Mismatch for param set {param_index + 1}, fixture {fixture_index + 1}, key {key}: "
                        f"js={js_result[key]} py={py_result[key]}",
                        file=sys.stderr,
                    )
                    return 1
    print("Calibration runner parity OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
