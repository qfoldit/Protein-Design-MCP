# qFoldIT Scene Export — Skill for Claude

Converts a universal, engine-agnostic scene description into real files:
OBJ, glTF 2.0, a standalone interactive Three.js HTML page, or Godot 4.x
GDScript. The honest fallback/interchange layer beneath
`qfoldit-engine-bridge`'s live-control integrations.

## Structure

```
qfoldit-scene-export/
├── README.md                              — this file
├── SKILL.md                               — instructions for Claude
├── scripts/
│   ├── scene_plan.py                      — universal data model + validation
│   ├── export_obj.py                      — Wavefront OBJ + MTL
│   ├── export_gltf.py                     — glTF 2.0 (self-contained)
│   ├── export_threejs.py                  — standalone interactive HTML
│   └── export_godot_gdscript.py           — Godot 4.x GDScript (untested against live Godot)
├── references/
│   ├── scene_plan_reference.md            — full field reference, worked examples
│   └── engine_notes.md                    — honest limitations, per-exporter verification depth
└── evals/
    ├── eval_set.json
    └── run_tests.py                       — 22 automated checks, all passing
```

## Verification depth — different per exporter, stated honestly

| Exporter | How it was actually verified |
|---|---|
| OBJ | Structural validity + real geometric correctness (decoded vertex positions checked against known atom coordinates) |
| glTF | Full manual glTF 2.0 spec-conformance check (no `pygltflib` available to validate against, so this was hand-verified against the spec) |
| Three.js | JS syntax check AND a genuine live-browser visual render (a real methane molecule, confirmed showing correct tetrahedral geometry) |
| Godot GDScript | **Weakest of the four** — brace-balance and known-class-name checks only. No live Godot instance was reachable from this environment. Say this plainly whenever this exporter is used. |

## Quick start

```python
from scripts.scene_plan import build_molecule_scene
from scripts.export_obj import export_obj
from scripts.export_gltf import export_gltf
from scripts.export_threejs import export_threejs_html

plan = build_molecule_scene("methane", atoms=[
    ("C", 0.0, 0.0, 0.0),
    ("H", 0.629, 0.629, 0.629),
    ("H", -0.629, -0.629, 0.629),
    ("H", -0.629, 0.629, -0.629),
    ("H", 0.629, -0.629, -0.629),
], bonds=[(0,1), (0,2), (0,3), (0,4)])

export_obj(plan, "methane.obj", "methane.mtl")
export_gltf(plan, "methane.gltf")
export_threejs_html(plan, "methane.html")   # open directly in a browser
```

## Testing

```bash
python3 evals/run_tests.py
```

22/22 checks passing as of this skill's build. Re-run after any change
to the exporters.

## Relationship to qfoldit-engine-bridge

`qfoldit-engine-bridge` documents LIVE engine connections (Unreal
official, Unity de-facto-standard) and knowledge-search-only tools
(Unigine, Omniverse official). This skill is the fallback: when no live
connection exists, or the target engine (Unigine, Omniverse) doesn't
have live scene-editing tooling at all, export a real file instead.

## Status

Core data model + OBJ + glTF exporters: strongly verified (structural
and geometric correctness, hand-checked against specs since no offline
validator libraries were available). Three.js exporter: visually
confirmed via a real browser render. Godot exporter: syntax-only,
explicitly NOT run against a live Godot instance — disclosed in
SKILL.md, this README, and the module's own docstring, not just once.
