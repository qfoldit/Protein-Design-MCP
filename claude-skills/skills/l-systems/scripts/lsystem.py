#!/usr/bin/env python3
"""
L-system (Lindenmayer system) generator with SVG rendering via turtle interpretation.

Supported turtle graphics symbols:
  F, G, ... (any uppercase letter in the alphabet) — step forward, drawing a line
  f                                              — step forward WITHOUT drawing
  +                                               — turn left by the angle
  -                                               — turn right by the angle
  [                                               — push state (position, angle) onto the stack
  ]                                               — pop the last state from the stack

All other symbols in the alphabet (e.g. X, Y — often used only as
"variables" for rules, with no geometric action) are skipped during
rendering unless explicitly included in draw_chars.

Examples of ready-made presets — see references/examples.md and PRESETS below.
"""

import argparse
import json
import math


PRESETS = {
    "koch": {
        "axiom": "F",
        "rules": {"F": "F+F-F-F+F"},
        "angle": 90,
        "iterations": 4,
        "draw_chars": "F",
    },
    "dragon": {
        "axiom": "FX",
        "rules": {"X": "X+YF+", "Y": "-FX-Y"},
        "angle": 90,
        "iterations": 10,
        "draw_chars": "F",
    },
    "sierpinski": {
        "axiom": "F-G-G",
        "rules": {"F": "F-G+F+G-F", "G": "GG"},
        "angle": 120,
        "iterations": 5,
        "draw_chars": "FG",
    },
    "plant": {
        "axiom": "X",
        "rules": {"X": "F+[[X]-X]-F[-FX]+X", "F": "FF"},
        "angle": 25,
        "iterations": 5,
        "draw_chars": "F",
    },
    "bush": {
        "axiom": "F",
        "rules": {"F": "FF-[-F+F+F]+[+F-F-F]"},
        "angle": 22.5,
        "iterations": 4,
        "draw_chars": "F",
    },
}


def expand(axiom: str, rules: dict, iterations: int) -> str:
    s = axiom
    for _ in range(iterations):
        s = "".join(rules.get(ch, ch) for ch in s)
    return s


def turtle_segments(s: str, angle_deg: float, draw_chars: str, step: float = 1.0):
    """Returns a list of segments [(x1,y1,x2,y2), ...] from the L-system string."""
    x, y = 0.0, 0.0
    heading = 90.0  # face "up" at the start, convenient for plants
    stack = []
    segments = []
    for ch in s:
        if ch in draw_chars:
            rad = math.radians(heading)
            nx = x + step * math.cos(rad)
            ny = y + step * math.sin(rad)
            segments.append((x, y, nx, ny))
            x, y = nx, ny
        elif ch == "f":
            rad = math.radians(heading)
            x = x + step * math.cos(rad)
            y = y + step * math.sin(rad)
        elif ch == "+":
            heading += angle_deg
        elif ch == "-":
            heading -= angle_deg
        elif ch == "[":
            stack.append((x, y, heading))
        elif ch == "]":
            if stack:
                x, y, heading = stack.pop()
        # other symbols (variables like X, Y with no geometry) are ignored
    return segments


def segments_to_svg(segments, stroke="#2f6b3a", stroke_width=1.0, padding=10, max_dim=800):
    if not segments:
        return "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'></svg>"

    xs = [p for seg in segments for p in (seg[0], seg[2])]
    ys = [p for seg in segments for p in (seg[1], seg[3])]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    width = max(max_x - min_x, 1e-6)
    height = max(max_y - min_y, 1e-6)

    scale = max_dim / max(width, height)
    svg_w = width * scale + 2 * padding
    svg_h = height * scale + 2 * padding

    lines = []
    for (x1, y1, x2, y2) in segments:
        # SVG y increases downward, so we invert
        sx1 = (x1 - min_x) * scale + padding
        sy1 = svg_h - ((y1 - min_y) * scale + padding)
        sx2 = (x2 - min_x) * scale + padding
        sy2 = svg_h - ((y2 - min_y) * scale + padding)
        lines.append(
            f'<line x1="{sx1:.2f}" y1="{sy1:.2f}" x2="{sx2:.2f}" y2="{sy2:.2f}" '
            f'stroke="{stroke}" stroke-width="{stroke_width}" stroke-linecap="round"/>'
        )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w:.2f} {svg_h:.2f}" '
        f'width="{svg_w:.0f}" height="{svg_h:.0f}">\n'
        f'<rect width="100%" height="100%" fill="white"/>\n'
        + "\n".join(lines) +
        "\n</svg>"
    )
    return svg


def main():
    parser = argparse.ArgumentParser(description="L-system generator and renderer")
    parser.add_argument("--preset", choices=list(PRESETS.keys()), help="Ready-made preset")
    parser.add_argument("--axiom", type=str, help="Starting string (axiom), if not using a preset")
    parser.add_argument("--rules", type=str, help='Rules in JSON format, e.g. \'{"F":"F+F-F-F+F"}\'')
    parser.add_argument("--angle", type=float, help="Turning angle in degrees")
    parser.add_argument("--iterations", type=int, help="Number of expansion iterations")
    parser.add_argument("--draw-chars", type=str, help="Symbols that draw a line (default 'F')")
    parser.add_argument("--step", type=float, default=1.0, help="Length of one step (before scaling)")
    parser.add_argument("--out", type=str, default="output.svg", help="Path to save the SVG")
    parser.add_argument("--string-only", action="store_true", help="Only print the expanded string, no SVG")
    args = parser.parse_args()

    if args.preset:
        cfg = dict(PRESETS[args.preset])
    else:
        if not (args.axiom and args.rules and args.angle is not None and args.iterations is not None):
            raise SystemExit(
                "Without --preset you must specify --axiom, --rules (JSON), --angle and --iterations"
            )
        cfg = {
            "axiom": args.axiom,
            "rules": json.loads(args.rules),
            "angle": args.angle,
            "iterations": args.iterations,
            "draw_chars": args.draw_chars or "F",
        }

    result_string = expand(cfg["axiom"], cfg["rules"], cfg["iterations"])

    if args.string_only:
        print(json.dumps({
            "config": cfg,
            "expanded_length": len(result_string),
            "expanded_string_preview": result_string[:500] + ("..." if len(result_string) > 500 else ""),
        }, ensure_ascii=False, indent=2))
        return

    segments = turtle_segments(result_string, cfg["angle"], cfg["draw_chars"], step=args.step)
    svg = segments_to_svg(segments)

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(svg)

    print(json.dumps({
        "config": cfg,
        "expanded_length": len(result_string),
        "num_segments": len(segments),
        "output_file": args.out,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
