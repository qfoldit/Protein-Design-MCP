# L-systems — Skill for Claude

A generator and renderer for L-systems (Lindenmayer systems): fractals and procedural branching structures (plants, bushes, curves) as SVG.

Can be used as a standalone generative-graphics tool or as part of procedural vegetation generation for VR scenes (e.g. for a "virtual lab"/greenhouse module in trade-show demos).

---

## What this is

A classic, well-studied algorithm from algorithmic botany (Aristid Lindenmayer, 1968; popularized by Prusinkiewicz and Lindenmayer's book "The Algorithmic Beauty of Plants"). Unlike other modules in the project, there are no empirical/literature assumptions here — this is pure deterministic mathematics: the result is fully and unambiguously determined by the axiom, rules, angle, and iteration count.

---

## Structure

```
qfoldit-l-systems/
├── README.md              — this file
├── SKILL.md                — instructions for Claude
├── references/
│   └── examples.md         — preset table, grammar explanation, extension ideas
└── scripts/
    └── lsystem.py           — generator + SVG renderer (Python 3, no external dependencies)
```

---

## Quick start

```bash
# Ready-made preset
python3 scripts/lsystem.py --preset plant --out plant.svg

# List of presets: koch, dragon, sierpinski, plant, bush

# Custom grammar
python3 scripts/lsystem.py \
  --axiom "F" \
  --rules '{"F":"F+F-F-F+F"}' \
  --angle 90 \
  --iterations 4 \
  --out koch.svg

# Just view the expanded string (for debugging rules, no rendering)
python3 scripts/lsystem.py --preset dragon --string-only
```

## Parameters

| Flag | Description |
|---|---|
| `--preset` | One of: `koch`, `dragon`, `sierpinski`, `plant`, `bush` |
| `--axiom` | Starting string (if not using a preset) |
| `--rules` | JSON dict of substitution rules, e.g. `{"F":"F+F-F-F+F"}` |
| `--angle` | Turtle turning angle, degrees |
| `--iterations` | Number of expansion iterations |
| `--draw-chars` | Which symbols draw a line (default `F`) |
| `--step` | Length of one step before scaling (default 1.0) |
| `--out` | Path to save the SVG (default `output.svg`) |
| `--string-only` | Don't render, just print the expanded string (for debugging) |

## Turtle graphics symbols

| Symbol | Action |
|---|---|
| `F`, `G` (symbols from `draw_chars`) | Step forward, drawing a line |
| `f` | Step forward without drawing |
| `+` | Turn left by the given angle |
| `-` | Turn right by the given angle |
| `[` | Push current state (position and direction) onto the stack |
| `]` | Pop the last saved state |
| any other symbol | Ignored during rendering (usually only used as a variable in rules, e.g. `X`, `Y`) |

---

## Known limitations

- 2D only. 3D L-systems (rotations around multiple axes) are not implemented.
- Only simple turtle graphics without stochasticity or parameters — plants come out geometrically perfect/symmetric, not "alive" with random variation. See `references/examples.md` for ideas on extending this (stochastic/parametric L-systems).
- Line thickness and color are fixed; for a more natural tree appearance, post-process the SVG manually or extend `segments_to_svg`.
- For a large iteration count with complex grammars (`plant`, `bush`), string length grows exponentially — rendering may slow down at 7+ iterations.

---

## How to extend

- **New preset**: add an entry to the `PRESETS` dict in `scripts/lsystem.py`.
- **3D**: would require rewriting `turtle_segments` with a 3D direction vector (e.g. represented via quaternions or a rotation matrix) and a different output format (not SVG, but e.g. OBJ or direct export to Three.js/Unreal).
- **Stochasticity**: in `PRESETS`/your own rules, instead of a single replacement string per symbol, use a list of weighted variants, chosen via `random.choices` at each substitution.
- **Depth-based coloring**: `turtle_segments` already has a `[`/`]` stack — the stack depth at the moment a segment is drawn can easily be passed through to `segments_to_svg` and used for a color gradient (trunk → branch tips).

---

## Status

Working base version (v0.1), tested on all 5 presets. A deterministic algorithm — validation against "real data" isn't needed, but it's worth visually checking each new preset/grammar before using it in presentations (see `--string-only` for debugging rules before rendering).
