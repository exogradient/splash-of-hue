<!-- What: Agent instructions for splash of hue (repo: true-to-hue). Where else: docs/ for vision, user journey. Stability: evolves with stack. Reviewed: 2026-03-28 -->

# splash of hue

Color memory game that teaches color perception.

## Tech Stack
- Python 3.13+, uv, FastAPI, uvicorn
- SQLite (auto-created at `data/games.db`)
- Single-file backend (`api/index.py`), single-file frontend (`public/index.html`)

## Conventions
- Inline everything until forced to split
- Dark theme, mobile-first
- HSB for user-facing color, CIELAB for scoring
- Minimal pleasing defaults, advanced config via progressive disclosure
- Doc structure principles and schema enforced by `make check-docs` — see `docs/meta-doc-system.md`
- Cross-doc references: use compact, grepable labels (e.g. `` `dogfooding` ``) not verbose prose. One label, one canonical location.

## CLI
- `make dev` — start dev server with hot reload
- `make docs` — list managed docs
- `make pit` — list point-in-time research docs
