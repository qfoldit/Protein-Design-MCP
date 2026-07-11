---
name: qfoldit-l-systems
description: Generates and renders L-systems (Lindenmayer systems) — fractal curves and procedural plant/branching structures — as SVG images. Use this skill whenever the user asks about L-systems, Lindenmayer systems, procedural plant generation, fractal curves (Koch curve, dragon curve, Sierpinski), turtle graphics, or wants to generate branching/botanical/fractal patterns for a game, visualization, or generative art. Also trigger for requests to generate procedural plants/vegetation (e.g. for a game or VR scene), or to visualize a custom axiom+rules grammar as an image.
---

# L-systems (Lindenmayer systems)

## What this skill does

Expands an L-system (axiom + substitution rules + iteration count) into a string and renders it as SVG via turtle graphics. Suitable for: classic fractals (Koch curve, dragon curve, Sierpinski triangle), procedural plants/branches, generative graphics for game scenes (e.g. a "virtual lab" / plant generation in a VR demo).

This is a deterministic mathematical algorithm — unlike other qFoldIT modules, there are no empirical assumptions or literature ranges that need to be caveated here. The result is fully predictable given the specified rules.

## When to use

- The user asks to generate a fractal (Koch, dragon, Sierpinski triangle, etc.).
- The user asks to generate a procedural plant/bush/branching structure.
- The user gives their own grammar (axiom and substitution rules) and wants to see what it looks like.
- The context is vegetation/fractal generation for a game scene, VR demo, or visualization.

## How to work

1. If the user wants something standard ("Koch fractal", "tree", "bush", "dragon", "Sierpinski triangle") — use the ready-made preset from `scripts/lsystem.py` (`--preset koch|dragon|sierpinski|plant|bush`), don't reinvent the rules.
2. If the user provides their own grammar — pass it via `--axiom`, `--rules` (a JSON string like `{"F":"F+F-F-F+F"}`), `--angle`, `--iterations`.
3. Run the script; it saves an SVG file and prints metadata (expanded string length, number of segments).
4. If the string comes out very long (>~50,000 characters) at the given iteration count — warn the user that rendering may be slow/heavy, and suggest reducing the iteration count.
5. Open the resulting SVG (via `view`) to confirm it isn't empty or doesn't look like a single point (a typical bug — wrong turtle argument order, or draw_chars not matching the rules' alphabet).
6. Show the result to the user — as an artifact (SVG renders directly in the interface) or as a file, depending on the conversation context.

## Example call

```bash
python3 scripts/lsystem.py --preset plant --out plant.svg
```

Custom grammar:

```bash
python3 scripts/lsystem.py --axiom "F" --rules '{"F":"F+F-F-F+F"}' --angle 90 --iterations 4 --out koch.svg
```

Just view the expanded string without rendering (useful for debugging rules):

```bash
python3 scripts/lsystem.py --preset dragon --string-only
```

## Limitations

- Only a basic set of turtle-graphics symbols is supported (F/G draw, f moves without drawing, +/- turn, []-stack state). 3D L-systems (with rotation on multiple axes, symbols like `&^\|`, etc.) are not implemented — extend `turtle_segments` in the script if needed.
- Line thickness and color are fixed by default; for an "organic" tree/bush look, post-processing the SVG is worthwhile (variable thickness from trunk to branches, color by recursion depth) — this is not implemented in the base version.
- Iteration count for complex grammars grows the string length exponentially — at 7-8 iterations, the "plant"/"bush" presets may render slowly.

See `references/examples.md` for a table of all presets and parameter explanations.
