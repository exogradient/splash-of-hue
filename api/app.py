"""true-to-hue: color memory game backend. Single file until forced to split."""

import json
import math
import os
import random
import sqlite3
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel

# Local dev: serve index.html directly. Vercel: public/ is CDN-served, not in function bundle.
_INDEX_HTML_PATH = Path(__file__).resolve().parent.parent / "public" / "index.html"

# --- Database ---

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


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_db() as conn:
        conn.executescript(SCHEMA)


# --- Color Math ---


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
    # D65 reference white
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
    """CIE76 Delta E — fast Euclidean distance for distinctness checks."""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(lab1, lab2)))


def delta_e_2000(lab1: tuple[float, float, float], lab2: tuple[float, float, float]) -> tuple[float, float, float, float]:
    """CIEDE2000 ΔE. Returns (ΔE00, ΔL', ΔC', ΔH')."""
    L1, a1, b1 = lab1
    L2, a2, b2 = lab2

    # Step 1: Calculate C'ab, h'ab
    C1 = math.sqrt(a1**2 + b1**2)
    C2 = math.sqrt(a2**2 + b2**2)
    C_avg = (C1 + C2) / 2
    C_avg7 = C_avg**7
    G = 0.5 * (1 - math.sqrt(C_avg7 / (C_avg7 + 25**7)))
    a1p = a1 * (1 + G)
    a2p = a2 * (1 + G)
    C1p = math.sqrt(a1p**2 + b1**2)
    C2p = math.sqrt(a2p**2 + b2**2)
    h1p = math.degrees(math.atan2(b1, a1p)) % 360
    h2p = math.degrees(math.atan2(b2, a2p)) % 360

    # Step 2: Calculate ΔL', ΔC', ΔH'
    dLp = L2 - L1
    dCp = C2p - C1p
    if C1p * C2p == 0:
        dhp = 0.0
    elif abs(h2p - h1p) <= 180:
        dhp = h2p - h1p
    elif h2p - h1p > 180:
        dhp = h2p - h1p - 360
    else:
        dhp = h2p - h1p + 360
    dHp = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dhp / 2))

    # Step 3: Weighting functions
    Lp_avg = (L1 + L2) / 2
    Cp_avg = (C1p + C2p) / 2
    if C1p * C2p == 0:
        hp_avg = h1p + h2p
    elif abs(h1p - h2p) <= 180:
        hp_avg = (h1p + h2p) / 2
    elif h1p + h2p < 360:
        hp_avg = (h1p + h2p + 360) / 2
    else:
        hp_avg = (h1p + h2p - 360) / 2

    T = (1
         - 0.17 * math.cos(math.radians(hp_avg - 30))
         + 0.24 * math.cos(math.radians(2 * hp_avg))
         + 0.32 * math.cos(math.radians(3 * hp_avg + 6))
         - 0.20 * math.cos(math.radians(4 * hp_avg - 63)))

    SL = 1 + 0.015 * (Lp_avg - 50)**2 / math.sqrt(20 + (Lp_avg - 50)**2)
    SC = 1 + 0.045 * Cp_avg
    SH = 1 + 0.015 * Cp_avg * T

    Cp_avg7 = Cp_avg**7
    RT = (-math.sin(math.radians(60 * math.exp(-((hp_avg - 275) / 25)**2)))
          * 2 * math.sqrt(Cp_avg7 / (Cp_avg7 + 25**7)))

    dE = math.sqrt(
        (dLp / SL)**2 + (dCp / SC)**2 + (dHp / SH)**2
        + RT * (dCp / SC) * (dHp / SH)
    )
    return dE, dLp, dCp, dHp


def score_from_delta_e(de: float) -> float:
    """Sigmoid curve: ΔE00 0→10, 5→9.3, 10→7.6, 15→5.5, 20→3.8, 30→1.8."""
    return round(10 / (1 + (de / 20) ** 2.5), 2)


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

    # Fallback if we couldn't get enough distinct colors
    while len(colors) < n:
        h = random.uniform(0, 360)
        s = random.uniform(35, 100)
        b = random.uniform(35, 100)
        colors.append({"h": round(h, 1), "s": round(s, 1), "b": round(b, 1)})

    return colors


def generate_distractors(target: dict, n: int = 3) -> list[dict]:
    """Generate n distractor colors for multiple choice (picture mode).

    Distractors are ΔE76 15–50 from target (plausible but distinguishable)
    and ΔE76 ≥15 from each other.
    """
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


# --- Color Naming ---

HUE_NAMES = [
    (15, "Red"),
    (40, "Orange"),
    (65, "Yellow"),
    (150, "Green"),
    (195, "Cyan"),
    (250, "Blue"),
    (295, "Purple"),
    (330, "Pink"),
    (360, "Red"),
]


def hue_name(h: float) -> str:
    for boundary, name in HUE_NAMES:
        if h < boundary:
            return name
    return "Red"


# --- API Models ---


class StartRequest(BaseModel):
    mode: str = "play"  # 'play', 'match', or 'picture'
    picker_type: str = "field"  # 'sliders' or 'field'


class ColorGuess(BaseModel):
    h: float
    s: float
    b: float


class SubmitRequest(BaseModel):
    game_id: str
    guesses: list[ColorGuess]


# --- App ---


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="true-to-hue", lifespan=lifespan)


@app.get("/")
async def index():
    if _INDEX_HTML_PATH.exists():
        return FileResponse(_INDEX_HTML_PATH)
    return RedirectResponse("/index.html", status_code=307)


@app.post("/api/game/start")
async def start_game(req: StartRequest):
    game_id = str(uuid.uuid4())[:8]
    colors = generate_colors(5)

    with get_db() as conn:
        conn.execute(
            "INSERT INTO games (id, created_at, mode, picker_type, target_colors) VALUES (?, ?, ?, ?, ?)",
            (game_id, datetime.now(timezone.utc).isoformat(), req.mode, req.picker_type, json.dumps(colors)),
        )

    result = {"game_id": game_id, "target_colors": colors}

    if req.mode == "picture":
        choices = []
        for color in colors:
            options = [color] + generate_distractors(color, 3)
            random.shuffle(options)
            choices.append(options)
        result["choices"] = choices

    return result


@app.post("/api/game/submit")
async def submit_game(req: SubmitRequest):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM games WHERE id = ?", (req.game_id,)).fetchone()

    if not row:
        return {"error": "Game not found"}

    targets = json.loads(row["target_colors"])

    if len(req.guesses) != len(targets):
        raise HTTPException(
            status_code=422,
            detail=f"Expected {len(targets)} guesses, got {len(req.guesses)}.",
        )

    results = []

    for target, guess in zip(targets, req.guesses):
        lab_t = hsb_to_lab(target["h"], target["s"], target["b"])
        lab_g = hsb_to_lab(guess.h, guess.s, guess.b)
        de, dLp, dCp, dHp = delta_e_2000(lab_t, lab_g)
        score = score_from_delta_e(de)
        results.append({
            "target": target,
            "guess": {"h": round(guess.h, 1), "s": round(guess.s, 1), "b": round(guess.b, 1)},
            "target_name": hue_name(target["h"]),
            "guess_name": hue_name(guess.h),
            "delta_e": round(de, 1),
            "delta_l": round(dLp, 1),
            "delta_c": round(dCp, 1),
            "delta_h": round(dHp, 1),
            "score": score,
        })

    total = round(sum(r["score"] for r in results), 2)
    scores_list = [r["score"] for r in results]
    guesses_list = [{"h": g.h, "s": g.s, "b": g.b} for g in req.guesses]

    with get_db() as conn:
        conn.execute(
            "UPDATE games SET guesses = ?, scores = ?, total_score = ? WHERE id = ?",
            (json.dumps(guesses_list), json.dumps(scores_list), total, req.game_id),
        )

    return {"results": results, "total_score": total}


@app.get("/api/history")
async def history(limit: int = 20):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM games WHERE total_score IS NOT NULL ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()

    return [
        {
            "id": r["id"],
            "created_at": r["created_at"],
            "mode": r["mode"],
            "picker_type": r["picker_type"],
            "total_score": r["total_score"],
            "scores": json.loads(r["scores"]) if r["scores"] else None,
        }
        for r in rows
    ]
