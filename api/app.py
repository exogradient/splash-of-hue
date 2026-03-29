"""splash-of-hue: color memory game backend. Stateless API for Vercel serverless."""

import json
import math
import os
import random
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Local dev: serve from public/. Vercel: public/ is CDN-served via vercel.json rewrite.
_PUBLIC_DIR = Path(__file__).resolve().parent.parent / "public"

# --- Database (lazy-init, append-only) ---

DB_PATH = Path("/tmp/games.db") if os.environ.get("VERCEL") else Path("data/games.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS games (
    id TEXT PRIMARY KEY,
    created_at TEXT,
    mode TEXT,
    picker_type TEXT,
    target_colors TEXT,
    guesses TEXT,
    scores TEXT,
    total_score REAL
);
"""

_db_initialized = False


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    global _db_initialized
    if _db_initialized:
        return
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_db() as conn:
        conn.executescript(SCHEMA)
    _db_initialized = True


# --- Color Math (dead code — generation moved client-side; kept for Phase 3 server-side scoring) ---


def hsb_to_rgb(h: float, s: float, b: float) -> tuple[float, float, float]:
    """HSB (h: 0-360, s: 0-100, b: 0-100) -> RGB (0-1)."""
    s_norm = s / 100
    b_norm = b / 100
    c = b_norm * s_norm
    h_prime = h / 60
    x = c * (1 - abs(h_prime % 2 - 1))
    m = b_norm - c

    if h_prime < 1:
        r, g, bl = c, x, 0
    elif h_prime < 2:
        r, g, bl = x, c, 0
    elif h_prime < 3:
        r, g, bl = 0, c, x
    elif h_prime < 4:
        r, g, bl = 0, x, c
    elif h_prime < 5:
        r, g, bl = x, 0, c
    else:
        r, g, bl = c, 0, x

    return r + m, g + m, bl + m


def srgb_to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def rgb_to_xyz(r: float, g: float, b: float) -> tuple[float, float, float]:
    r, g, b = srgb_to_linear(r), srgb_to_linear(g), srgb_to_linear(b)
    x = 0.4124564 * r + 0.3575761 * g + 0.1804375 * b
    y = 0.2126729 * r + 0.7151522 * g + 0.0721750 * b
    z = 0.0193339 * r + 0.1191920 * g + 0.9503041 * b
    return x, y, z


def xyz_to_lab(x: float, y: float, z: float) -> tuple[float, float, float]:
    xn, yn, zn = 0.95047, 1.0, 1.08883

    def f(t: float) -> float:
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116

    fx, fy, fz = f(x / xn), f(y / yn), f(z / zn)
    L = 116 * fy - 16
    a = 500 * (fx - fy)
    b = 200 * (fy - fz)
    return L, a, b


def hsb_to_lab(h: float, s: float, b: float) -> tuple[float, float, float]:
    r, g, bl = hsb_to_rgb(h, s, b)
    x, y, z = rgb_to_xyz(r, g, bl)
    return xyz_to_lab(x, y, z)


def delta_e_76(lab1: tuple[float, float, float], lab2: tuple[float, float, float]) -> float:
    """CIE76 Delta E -- fast Euclidean distance for distinctness checks."""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(lab1, lab2)))


# --- Color Generation ---


def generate_colors(n: int = 5) -> list[dict]:
    """Generate n perceptually distinct colors. Avoid very dark/desaturated."""
    colors = []
    max_attempts = 200

    for _ in range(max_attempts):
        if len(colors) >= n:
            break

        h = random.uniform(0, 360)
        s = random.uniform(35, 100)
        b = random.uniform(35, 100)

        lab = hsb_to_lab(h, s, b)
        too_close = any(delta_e_76(lab, hsb_to_lab(c["h"], c["s"], c["b"])) < 20 for c in colors)

        if not too_close:
            colors.append({"h": round(h, 1), "s": round(s, 1), "b": round(b, 1)})

    while len(colors) < n:
        h = random.uniform(0, 360)
        s = random.uniform(35, 100)
        b = random.uniform(35, 100)
        colors.append({"h": round(h, 1), "s": round(s, 1), "b": round(b, 1)})

    return colors


def generate_distractors(target: dict, n: int = 3) -> list[dict]:
    """Generate n distractor colors for multiple choice (picture mode)."""
    distractors: list[dict] = []
    target_lab = hsb_to_lab(target["h"], target["s"], target["b"])

    for _ in range(200):
        if len(distractors) >= n:
            break
        h = random.uniform(0, 360)
        s = random.uniform(35, 100)
        b = random.uniform(35, 100)
        lab = hsb_to_lab(h, s, b)
        de = delta_e_76(target_lab, lab)
        if de < 15 or de > 50:
            continue
        if any(delta_e_76(lab, hsb_to_lab(d["h"], d["s"], d["b"])) < 15 for d in distractors):
            continue
        distractors.append({"h": round(h, 1), "s": round(s, 1), "b": round(b, 1)})

    while len(distractors) < n:
        h = random.uniform(0, 360)
        s = random.uniform(35, 100)
        b = random.uniform(35, 100)
        distractors.append({"h": round(h, 1), "s": round(s, 1), "b": round(b, 1)})

    return distractors


# --- API Models ---


class SubmitRequest(BaseModel):
    mode: str
    picker_type: str
    target_colors: list[dict]
    guesses: list[dict]
    scores: list[float]
    total_score: float


# --- App ---

app = FastAPI(title="splash-of-hue")


@app.post("/api/game/submit")
async def submit_game(req: SubmitRequest):
    try:
        init_db()
        game_id = str(uuid.uuid4())[:8]
        with get_db() as conn:
            conn.execute(
                "INSERT INTO games (id, created_at, mode, picker_type, target_colors, guesses, scores, total_score) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (game_id, datetime.now(timezone.utc).isoformat(), req.mode, req.picker_type,
                 json.dumps(req.target_colors), json.dumps(req.guesses),
                 json.dumps(req.scores), req.total_score),
            )
    except Exception as e:
        import logging
        logging.warning("Game persist failed: %s", e)
    return {"ok": True}


# Local dev: serve static files from public/. On Vercel, public/ is CDN-served.
if not os.environ.get("VERCEL") and _PUBLIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(_PUBLIC_DIR), html=True), name="static")
