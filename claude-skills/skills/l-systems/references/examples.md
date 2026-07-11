# L-system examples and presets

All presets are available via `--preset <name>` in `scripts/lsystem.py`.

| Preset | Axiom | Rules | Angle | Iterations (default) | Result |
|---|---|---|---|---|---|
| `koch` | `F` | `F → F+F-F-F+F` | 90° | 4 | Koch curve/snowflake |
| `dragon` | `FX` | `X → X+YF+`, `Y → -FX-Y` | 90° | 10 | Dragon curve |
| `sierpinski` | `F-G-G` | `F → F-G+F+G-F`, `G → GG` | 120° | 5 | Sierpinski triangle (arrowhead) |
| `plant` | `X` | `X → F+[[X]-X]-F[-FX]+X`, `F → FF` | 25° | 5 | Classic branching "plant" (Prusinkiewicz) |
| `bush` | `F` | `F → FF-[-F+F+F]+[+F-F-F]` | 22.5° | 4 | Symmetric "bush" |

## How to read an L-system grammar

- **Axiom** — the starting string the expansion begins from.
- **Rules** — a "symbol → replacement" dictionary. At each iteration, every symbol in the current string is replaced according to the rule (if there's no rule for a symbol, it stays as-is).
- **Angle** — how many degrees the "turtle" turns on `+`/`-` symbols.
- **draw_chars** — which symbols draw a line when rendering (usually `F`, sometimes `F` and `G`). Symbols like `X`/`Y` are often used only as "variables" in the rules and aren't drawn directly.

## Custom grammar — example

Want a five-pointed snowflake — experiment with a 72° angle (360/5):

```bash
python3 scripts/lsystem.py --axiom "F" --rules '{"F":"F+F++F-F"}' --angle 72 --iterations 3 --out custom.svg
```

If the result looks "off" — start with a small iteration count (1-2) and check whether the string expands as expected via `--string-only`, before rendering with a larger iteration count.

## Ideas for further extension (not implemented in the base version)

- Stochastic L-systems (multiple rule variants for one symbol, chosen randomly with weights) — for more "alive", not perfectly symmetric plants.
- Parametric L-systems (symbols with numeric parameters, e.g. segment length decreasing with each iteration) — for realistic trees with tapering branches.
- 3D rendering (export to OBJ/three.js) instead of flat SVG — relevant for VR scenes.
- Coloring by recursion depth (trunk darker, branch tips lighter/greener) for a more natural look.
