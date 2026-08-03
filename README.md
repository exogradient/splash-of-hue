# splash of hue

Learn to see color—not just name it.

**splash of hue** is a focused set of games for building intuition for hue,
saturation, and brightness. The interface stays quiet so color can do the
teaching; detail appears only when it helps you learn.

## The games

| Mode | Skill |
| --- | --- |
| **Match It** | Tune a color beside the target. The main learning loop. |
| **Play** | Memorize a color, then recreate it without a reference. |
| **Picture It** | Read HSB values and choose the color they describe. |
| **Call It** | Connect a color to its closest everyday name. |
| **Split It** | Estimate hue, saturation, and brightness independently. |

Match It uses a full-spectrum picker: angle controls hue, distance from the
center controls saturation, and the outer ring controls brightness. The target
and guess remain visual by default; press the comparison swatch when you want
to inspect the HSB values.

Scoring uses CIEDE2000 for perceptual color difference while keeping HSB as the
player-facing mental model.

## Run locally

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```sh
uv sync
make dev
```

Open [http://localhost:8000](http://localhost:8000).

## Check changes

```sh
make check-docs
make check-scoring
make check-calibration-runner
```

## Read deeper

- [Product model](docs/identity-model.md) — the perceptual skills behind each mode
- [Visual identity](docs/identity-visual.md) — the design principles and quality bar
- [Player journey](docs/specs-journey.md) — the shipped game flows
- [Homepage embed](docs/homepage-embed-contract.md) — the one-round integration boundary
- [Roadmap](docs/specs-roadmap.md) — prioritized product direction
- [System architecture](docs/specs-hld.md) — runtime, persistence, and analytics
