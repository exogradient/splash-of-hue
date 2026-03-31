#!/usr/bin/env python3
"""Verify the shared scoring block matches between the app and calibration tool."""

from __future__ import annotations

from difflib import unified_diff
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
APP_FILE = ROOT / "public" / "index.html"
CALIBRATION_FILE = ROOT / "tools" / "calibration.jsx"
START_MARKER = "// --- Shared scorer block: start ---"
END_MARKER = "// --- Shared scorer block: end ---"


def extract_block(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    start = text.find(START_MARKER)
    end = text.find(END_MARKER)
    if start == -1 or end == -1 or end < start:
        raise ValueError(f"Shared scorer markers not found in {path}")
    start += len(START_MARKER)
    block = text[start:end]
    return block.strip() + "\n"


def main() -> int:
    app_block = extract_block(APP_FILE)
    calibration_block = extract_block(CALIBRATION_FILE)
    if app_block == calibration_block:
        print("Shared scoring block parity OK")
        return 0

    diff = unified_diff(
        app_block.splitlines(),
        calibration_block.splitlines(),
        fromfile=str(APP_FILE),
        tofile=str(CALIBRATION_FILE),
        lineterm="",
    )
    print("Shared scoring block drift detected:", file=sys.stderr)
    for line in diff:
        print(line, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
