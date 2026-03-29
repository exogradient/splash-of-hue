<!-- Agent instructions. Reviewed: 2026-03-29 -->

# splash of hue

Color memory game that teaches color perception.

## Stack & Architecture
- Runtime: Python 3.13+, uv, FastAPI, uvicorn
- Storage: SQLite — local: `data/games.db`, Vercel: `/tmp/games.db` (ephemeral)
- Layout: Single-file backend (`api/app.py`), single-file frontend (`public/index.html`)
- Deploy: Vercel — serverless Python, `public/` CDN-served, rewrites in `vercel.json`
- Scoring: CIEDE2000, client-side — HSB user-facing, CIELAB internal
- Docs: 4-layer frontmatter schema, PIT snapshots, `make check-docs` validation

## Conventions
- Code: Inline everything until forced to split
- Server is stateless — no in-memory game state between requests
- Dark theme, mobile-first
- Visual: Minimal pleasing defaults, advanced config via progressive disclosure
- Cross-doc references: use compact, grepable labels (e.g. `` `dogfooding` ``) not verbose prose. One label, one canonical location.

## CLI
- `make dev` — start dev server with hot reload
- `make docs` — list managed docs
- `make pit` — list point-in-time research docs
