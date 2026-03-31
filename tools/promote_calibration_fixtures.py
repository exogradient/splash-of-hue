#!/usr/bin/env python3
"""Promote audited calibration rows into regression fixture JSON."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from run_calibration import (
    VALID_VERDICTS,
    load_challenge_samples,
    resolved_verdict,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="Path to calibration export JSON")
    parser.add_argument(
        "--label-source",
        choices=("auto", "human", "hybrid"),
        default="hybrid",
        help="How to resolve promoted verdicts",
    )
    parser.add_argument(
        "--include-unreviewed",
        action="store_true",
        help="Also promote unreviewed rows; default is reviewed rows only",
    )
    parser.add_argument(
        "--score-window",
        type=float,
        default=0.0,
        help="Optional +/- score band for promoted OK fixtures",
    )
    parser.add_argument(
        "--directional-shift",
        type=float,
        default=0.5,
        help="Minimum directional score shift to require for promoted too_low/too_high fixtures",
    )
    parser.add_argument(
        "--append-to",
        type=Path,
        help="Optional existing fixture file to merge into; promoted ids replace matching ids",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional output path; defaults to stdout when --append-to is not used",
    )
    return parser.parse_args()


def sanitize_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_") or "sample"


def fixture_id_for(sample_index: int, batch_seed: int | None, sample_id: str | None, profile: str | None) -> str:
    pieces = [
        "calibration",
        str(batch_seed) if batch_seed is not None else "na",
        sanitize_token(sample_id or str(sample_index)),
        sanitize_token(profile or "sample"),
    ]
    return "_".join(pieces)


def promote_rows(
    export_path: Path,
    *,
    label_source: str,
    include_unreviewed: bool,
    score_window: float,
    directional_shift: float,
) -> list[dict[str, Any]]:
    _batches, samples = load_challenge_samples(export_path)
    fixtures: list[dict[str, Any]] = []
    for index, sample in enumerate(samples, start=1):
        if not include_unreviewed and not sample.reviewed:
            continue
        verdict = resolved_verdict(sample, label_source)
        if verdict not in VALID_VERDICTS:
            continue
        fixture: dict[str, Any] = {
            "id": fixture_id_for(index, sample.batch_seed, sample.sample_id, sample.profile),
            "tag": sample.candidate_bucket,
            "target": sample.target,
            "guess": sample.guess,
        }
        if verdict == "ok" and score_window > 0:
            fixture["expected_verdict"] = "ok"
            fixture["min_score"] = round(max(0.0, sample.baseline_score - score_window), 2)
            fixture["max_score"] = round(min(10.0, sample.baseline_score + score_window), 2)
        elif verdict == "ok":
            fixture["expected_verdict"] = "ok"
        else:
            fixture["baseline_score"] = round(sample.baseline_score, 2)
            fixture["required_shift"] = "up" if verdict == "too_low" else "down"
            fixture["min_shift"] = directional_shift
        fixtures.append(fixture)
    fixtures.sort(key=lambda item: item["id"])
    return fixtures


def merge_with_existing(existing_path: Path, promoted: list[dict[str, Any]]) -> list[dict[str, Any]]:
    existing_data = json.loads(existing_path.read_text(encoding="utf-8"))
    if not isinstance(existing_data, list):
        raise SystemExit(f"Existing fixture file must be a JSON array: {existing_path}")
    by_id: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(existing_data, start=1):
        if not isinstance(raw, dict) or "id" not in raw:
            raise SystemExit(f"Invalid fixture entry #{index} in {existing_path}")
        by_id[str(raw["id"])] = raw
    for fixture in promoted:
        by_id[str(fixture["id"])] = fixture
    return [by_id[key] for key in sorted(by_id)]


def write_payload(fixtures: list[dict[str, Any]], path: Path | None) -> None:
    text = json.dumps(fixtures, indent=2)
    if path is None:
        print(text)
        return
    path.write_text(text + "\n", encoding="utf-8")
    print(f"Wrote {len(fixtures)} regression fixtures to {path}")


def main() -> int:
    args = parse_args()
    promoted = promote_rows(
        args.path,
        label_source=args.label_source,
        include_unreviewed=args.include_unreviewed,
        score_window=args.score_window,
        directional_shift=args.directional_shift,
    )
    if not promoted:
        raise SystemExit("No calibration rows qualified for promotion.")
    fixtures = promoted
    if args.append_to is not None:
        fixtures = merge_with_existing(args.append_to, promoted)
    output_path = args.output if args.output is not None else args.append_to
    write_payload(fixtures, output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
