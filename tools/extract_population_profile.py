#!/usr/bin/env python3
"""Flatten local gameplay rounds into a reusable population profile artifact."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from run_calibration import (
    DEFAULT_POPULATION_DB,
    LIVE_BASELINE_PARAMS,
    ScoringParams,
    extract_baseline_params,
    load_batches,
    load_population_samples,
    profile_summary_population,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_POPULATION_DB,
        help="Path to the local gameplay SQLite DB",
    )
    parser.add_argument(
        "--params-from",
        type=Path,
        help="Optional calibration export used to derive baseline scoring params",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path to write the extracted population profile JSON",
    )
    return parser.parse_args()


def resolve_baseline(path: Path | None) -> ScoringParams:
    if path is None:
        return LIVE_BASELINE_PARAMS
    return extract_baseline_params(load_batches(path))


def sample_to_dict(sample: object) -> dict[str, object]:
    # Keep the artifact future-compatible with strata weights even though v1 uses 1.0.
    from run_calibration import Sample

    if not isinstance(sample, Sample):
        raise TypeError(f"Expected Sample, got {type(sample).__name__}")
    return {
        "sample_id": sample.sample_id,
        "source_profile": sample.source_profile,
        "mode": sample.mode,
        "picker_type": sample.picker_type,
        "score_band": sample.score_band,
        "hue_band": sample.hue_band,
        "delta_e_band": sample.delta_e_band,
        "candidate_bucket": sample.candidate_bucket,
        "weight": 1.0,
        "baseline_score": sample.baseline_score,
        "auto_grader": {
            "verdict": sample.auto_verdict,
            "rules": list(sample.rules),
        },
        "target": sample.target,
        "guess": sample.guess,
    }


def main() -> int:
    args = parse_args()
    baseline = resolve_baseline(args.params_from)
    samples, skipped = load_population_samples(args.db, baseline)
    summary = profile_summary_population(samples)
    payload = {
        "mode": "population-profile",
        "db_path": str(args.db),
        "baseline_params": baseline.__dict__,
        "summary": summary,
        "skipped_rows": dict(sorted(skipped.items())),
        "rows": [sample_to_dict(sample) for sample in samples],
    }
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(
        f"Wrote {len(samples)} population rows to {args.output} "
        f"(skipped={dict(sorted(skipped.items()))})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
