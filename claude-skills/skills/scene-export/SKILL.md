---
name: qfoldit-scene-export
description: Converts a universal, engine-agnostic scene description (spheres/boxes/cylinders with position/material, connected by bonds/edges -- e.g. a ball-and-stick molecule, or an L-system's turtle-graphics segments) into real files usable across engines -- Wavefront OBJ, glTF 2.0, a standalone interactive Three.js HTML page, or Godot 4.x GDScript. Use whenever the user wants to export a qFoldIT visualization (a molecule, a procedural plant, a generic 3D scene) to a universal format, needs a file importable into Unity/Unreal/Blender/Godot/Omniverse, or wants an interactive browser-viewable 3D scene with no engine installed. This is a fallback/interchange layer for when qfoldit-engine-bridge's live-control tools aren't available or aren't the right fit.
---

# qFoldIT Scene Export

Converts a universal `ScenePlan` (nodes = primitives with position/
rotation/scale/material, edges = bonds/connections, optional lights and
camera) into real output files. Built specifically so it needs **no live
engine** — the honest fallback tier below `qfoldit-engine-bridge`'s
live-control integrations (Unreal/Unity), for when those aren't
connected, or for engines where only knowledge-search tools exist
(Unigine, Omniverse) and a human needs an actual file to import.

## What's implemented, and how thoroughly each was verified

| Exporter | Format | Verification depth |
|---|---|---|
| `export_obj.py` | Wavefront OBJ + MTL | **Strong**: structural validity (indices in range, materials cross-referenced) AND real geometric correctness (decoded vertex positions checked against known atom coordinates) |
| `export_gltf.py` | glTF 2.0 (self-contained, base64-embedded) | **Strong**: full manual spec-conformance check (buffer/bufferView/accessor cross-referencing, decoded binary geometry) — no `pygltflib` available in this sandbox, so this was written by hand against the spec, not rubber-stamped by an existing validator |
| `export_threejs.py` | Standalone interactive HTML | **Strong but different kind**: JS syntax verified (`node --check`), AND the actual rendering logic was visually confirmed correct by rendering a real methane molecule in a live browser widget during this skill's development — genuine visual proof, not just a syntax check |
| `export_godot_gdscript.py` | Godot 4.x GDScript | **Weak, disclosed as such**: only brace-balance/known-class-name checks. No live Godot instance was available to actually run this. Treat as "written to the documented API," not "tested." |

## When to use which exporter

1. **OBJ**: broadest compatibility (every engine and DCC tool imports
   it). No animation, no native hierarchy — geometry is baked to world
   space. Good default when you don't know the target tool yet.
2. **glTF**: the modern standard for web/AR/most game engines; better
   material fidelity (PBR metallic/roughness) than OBJ; self-contained
   single file (no separate texture/bin files to lose track of).
3. **Three.js HTML**: when the user wants something viewable RIGHT NOW
   with zero installs — just open the file in a browser. Needs internet
   access to load Three.js from a CDN (not offline-capable, unlike the
   OBJ/glTF output files).
4. **Godot GDScript**: only if the user is specifically targeting Godot
   AND understands this hasn't been run against a real Godot instance —
   say this explicitly every time this exporter is used.

## How to build a scene plan

Use `scene_plan.build_molecule_scene(name, atoms, bonds)` for the common
"ball-and-stick molecule from an atom list" case (handles CPK element
coloring, element-scaled radii, and bond cylinders automatically). For
anything else (an L-system's turtle segments as cylinders, a generic
qFoldIT process visualization), construct `Node`/`Edge`/`Light`/`Camera`
objects directly — see `references/scene_plan_reference.md` for the full
field reference and worked examples.

**Always call `.validate()` before exporting** — it catches invalid
primitives, duplicate IDs, dangling edge references, and parent-child
cycles with a specific, actionable error message, rather than letting a
malformed plan produce a broken or silently-wrong export file.

## Relationship to qfoldit-engine-bridge

This skill is the fallback/interchange layer; `qfoldit-engine-bridge` is
the live-control layer (where Unreal/Unity actually exist). If a live
Unreal or Unity MCP connection is available, that's usually more capable
(hierarchy, prefabs/blueprints, live iteration) than an OBJ/glTF import.
Use this skill when no live connection exists, when targeting an engine
that only has knowledge-search tools (Unigine, Omniverse), or when a
portable, engine-independent file is what's actually wanted.

## What NOT to claim

- Do not claim the Godot output has been tested in Godot — it hasn't.
- Do not claim these exporters implement animation, textures/UVs,
  skeletal rigs, or physics — none of that exists here; this is static
  geometry + basic PBR material only.
- Do not claim the Three.js HTML file works fully offline — it loads
  Three.js from a CDN and needs internet access in the browser that
  opens it.
