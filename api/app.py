"""splash-of-hue: color memory game backend. Stateless API for Vercel serverless."""

import json
import os
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
