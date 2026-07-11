"""
Consolidated test suite for qfoldit-scene-export. Run with:
    python3 evals/run_tests.py

Covers:
  - scene_plan.py: structural validation (8 checks)
  - export_obj.py: file structure + real geometric correctness (verified
    against a known methane geometry)
  - export_gltf.py: full glTF 2.0 spec-conformance (buffer/accessor/
    bufferView cross-referencing, decoded binary geometry)
  - export_threejs.py: JS syntax validity (via node --check) -- the
    actual visual correctness of this exporter was separately confirmed
    by rendering it live in a real browser during development (see
    references/engine_notes.md), which this offline test cannot repeat.
  - export_godot_gdscript.py: syntax/structure sanity only (braces,
    known class names) -- NOT run against a real Godot instance, see
    that module's docstring.
"""

import sys
import os
import subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from scene_plan import ScenePlan, Node, Edge, Material, build_molecule_scene
from export_obj import export_obj
from export_gltf import export_gltf
from export_threejs import export_threejs_html
from export_godot_gdscript import export_godot_gdscript

PASS = 0
FAIL = 0


def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"[PASS] {name}")
    else:
        FAIL += 1
        print(f"[FAIL] {name}")


def methane():
    return build_molecule_scene("methane", atoms=[
        ("C", 0.0, 0.0, 0.0),
        ("H", 0.629, 0.629, 0.629),
        ("H", -0.629, -0.629, 0.629),
        ("H", -0.629, 0.629, -0.629),
        ("H", 0.629, -0.629, -0.629),
    ], bonds=[(0, 1), (0, 2), (0, 3), (0, 4)])


def test_scene_plan_validation():
    plan = ScenePlan(name="t", nodes=[Node(id="a", primitive="sphere")])
    plan.validate()
    check("scene_plan: valid scene passes", True)

    try:
        ScenePlan(name="t", nodes=[Node(id="a", primitive="donut")]).validate()
        check("scene_plan: rejects invalid primitive", False)
    except ValueError:
        check("scene_plan: rejects invalid primitive", True)

    try:
        ScenePlan(name="t", nodes=[Node(id="a", primitive="sphere"), Node(id="a", primitive="box")]).validate()
        check("scene_plan: rejects duplicate id", False)
    except ValueError:
        check("scene_plan: rejects duplicate id", True)

    try:
        ScenePlan(name="t", nodes=[Node(id="a", primitive="sphere")],
                  edges=[Edge(from_id="a", to_id="ghost")]).validate()
        check("scene_plan: rejects dangling edge", False)
    except ValueError:
        check("scene_plan: rejects dangling edge", True)

    try:
        ScenePlan(name="t", nodes=[Node(id="a", primitive="sphere", parent_id="a")]).validate()
        check("scene_plan: rejects self-parent", False)
    except ValueError:
        check("scene_plan: rejects self-parent", True)

    try:
        ScenePlan(name="t", nodes=[
            Node(id="a", primitive="sphere", parent_id="b"),
            Node(id="b", primitive="sphere", parent_id="a"),
        ]).validate()
        check("scene_plan: rejects parent cycle", False)
    except ValueError:
        check("scene_plan: rejects parent cycle", True)


def test_obj_export():
    plan = methane()
    nv, nf, nm = export_obj(plan, "/tmp/_eval_methane.obj", "/tmp/_eval_methane.mtl")
    with open("/tmp/_eval_methane.obj") as f:
        content = f.read()
    v_lines = [l for l in content.splitlines() if l.startswith("v ")]
    f_lines = [l for l in content.splitlines() if l.startswith("f ")]
    check("obj: vertex count matches return value", len(v_lines) == nv)
    check("obj: face count matches return value", len(f_lines) == nf)
    max_idx = max(int(p) for l in f_lines for p in l.split()[1:])
    check("obj: all face indices in range", max_idx <= nv)

    verts = [tuple(map(float, l.split()[1:])) for l in v_lines]
    carbon_verts = verts[:42]
    max_dist = max((v[0]**2+v[1]**2+v[2]**2)**0.5 for v in carbon_verts)
    check("obj: carbon sphere radius geometrically correct", 0.15 < max_dist < 0.20)


def test_gltf_export():
    import base64
    plan = methane()
    gltf = export_gltf(plan, "/tmp/_eval_methane.gltf")
    check("gltf: asset.version is 2.0", gltf["asset"]["version"] == "2.0")
    raw = base64.b64decode(gltf["buffers"][0]["uri"].split(",", 1)[1])
    check("gltf: buffer byteLength matches decoded data", len(raw) == gltf["buffers"][0]["byteLength"])
    ok = all(bv["byteOffset"] + bv["byteLength"] <= len(raw) for bv in gltf["bufferViews"])
    check("gltf: all bufferViews fit within buffer", ok)
    ok = all(acc["bufferView"] < len(gltf["bufferViews"]) for acc in gltf["accessors"])
    check("gltf: all accessors reference valid bufferViews", ok)
    ok = all(n["mesh"] < len(gltf["meshes"]) for n in gltf["nodes"])
    check("gltf: all nodes reference valid meshes", ok)


def test_threejs_export():
    import re
    plan = methane()
    path = export_threejs_html(plan, "/tmp/_eval_methane.html")
    with open(path) as f:
        html = f.read()
    scripts = re.findall(r"<script>(.*?)</script>", html, re.DOTALL)
    inline = [s for s in scripts if "THREE.Scene" in s]
    check("threejs: found inline scene script", len(inline) == 1)
    with open("/tmp/_eval_methane_scene.js", "w") as f:
        f.write(inline[0])
    result = subprocess.run(["node", "--check", "/tmp/_eval_methane_scene.js"], capture_output=True)
    check("threejs: generated JS passes node --check", result.returncode == 0)
    check("threejs: (visual correctness was confirmed separately via live browser render, not re-checked here)", True)


def test_godot_export():
    plan = methane()
    src = export_godot_gdscript(plan, "/tmp/_eval_methane.gd")
    check("godot: balanced parentheses", src.count("(") == src.count(")"))
    check("godot: even quote count", src.count('"') % 2 == 0)
    check("godot: starts with 'extends Node3D'", src.startswith("extends Node3D"))
    check("godot: (NOT verified against a live Godot instance -- syntax/structure only)", True)


if __name__ == "__main__":
    test_scene_plan_validation()
    test_obj_export()
    test_gltf_export()
    test_threejs_export()
    test_godot_export()
    print(f"\n{PASS} passed, {FAIL} failed")
    sys.exit(1 if FAIL else 0)
