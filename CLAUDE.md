<!-- Agent instructions. Reviewed: 2026-08-02 -->

# splash of hue

A color-perception training game. HSB is the learning model; CIEDE2000 is the scoring model.

## Architecture

- Python 3.13+, `uv`, FastAPI, Vercel.
- `public/index.html` owns gameplay and scoring.
- `public/home.css` and `public/home.js` own the home deck.
- `public/analytics.js` is the only telemetry surface.
- The client generates colors and scores locally. The server persists completed games and shared challenges.
- Local storage: SQLite. Production challenges: Turso when configured.

## Product rules

- Match It is the primary learning loop.
- The game is the interface: remove chrome before adding explanation.
- Show color first. Reveal HSB only on demand.
- Keep gameplay surfaces achromatic; reserve color for the material being learned.
- Validate mobile layouts on iPhone Safari, including safe areas and short viewports.
- Preserve keyboard, pointer, touch, reduced-motion, and visible-focus behavior.
- `docs/homepage-embed-contract.md` owns the `/?embed=play` integration boundary. Preserve the real Play loop rather than creating a site-specific simulation.

## Engineering rules

- Use `uv`; `pyproject.toml` is authoritative.
- Keep gameplay network-independent.
- Keep scorer copies byte-identical between the app and calibration tools.
- Keep durable principles in identity docs, evolving rationale in design docs, and shipped truth in specs.

## Checks

```sh
make check-docs
make check-scoring
make check-calibration-runner
```
