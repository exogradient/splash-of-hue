<!-- Agent instructions. Reviewed: 2026-03-29 -->

# splash of hue

Color memory game that teaches color perception.

## Stack & Architecture
- Runtime: Python 3.13+, uv, FastAPI, uvicorn
- Storage: SQLite — local: `data/games.db`, Vercel: `/tmp/games.db` (ephemeral)
- Layout: Single-file backend (`api/app.py`), single-file frontend (`public/index.html`), analytics module (`public/analytics.js`)
- Deploy: Vercel — serverless Python, `public/` CDN-served, rewrites in `vercel.json`
- Game flow: Client-driven — colors generated and scored client-side, server is append-only persistence
- Scoring: CIEDE2000, client-side — HSB user-facing, CIELAB internal
- Analytics: PostHog, client-side only — privacy-safe (no PII, no cookies, no IP). Audit surface: `public/analytics.js`
- Docs: 4-layer frontmatter schema, PIT snapshots, `make check-docs` validation

## Conventions
- Code: Inline everything until forced to split. `analytics.js` is the exception — separate for auditability
- Server is stateless — append-only, no game state between requests
- Dark theme, mobile-first
- Visual: Minimal pleasing defaults, advanced config via progressive disclosure
- Cross-doc references: use compact, grepable labels (e.g. `` `dogfooding` ``) not verbose prose. One label, one canonical location.

## CLI
- `make dev` — start dev server with hot reload
- `make docs` — list managed docs
- `make pit` — list point-in-time research docs
