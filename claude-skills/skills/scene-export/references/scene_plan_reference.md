# Scene plan reference

## Node fields

| Field | Type | Meaning |
|---|---|---|
| `id` | str | Unique identifier within the scene |
| `primitive` | str | One of: `sphere`, `box`, `cylinder`, `capsule`, `cone` |
| `position` | (x,y,z) | World-space position, meters |
| `rotation_euler_deg` | (x,y,z) | Euler rotation, degrees, XYZ order |
| `scale` | (x,y,z) | Per-axis scale (sphere/capsule use the average of the three as radius in some exporters — see each exporter's docstring) |
| `material` | Material | See below |
| `label` | str or None | Optional human-readable label (e.g. an element symbol) |
| `parent_id` | str or None | Optional parent node id, for hierarchy — validated for cycles |

## Edge fields (bonds/connections)

| Field | Type | Meaning |
|---|---|---|
| `from_id`, `to_id` | str | Must reference existing node ids |
| `radius` | float | Cylinder radius, meters |
| `material` | Material | See below |

## Material fields

| Field | Type | Meaning |
|---|---|---|
| `color_rgba` | (r,g,b,a), each 0-1 | Base color |
| `metallic` | float 0-1 | PBR metallic factor |
| `roughness` | float 0-1 | PBR roughness factor |
| `emissive_rgb` | (r,g,b), each 0-1 | Emissive color (glow), default black/off |

## Light fields

| Field | Type | Meaning |
|---|---|---|
| `kind` | str | `point`, `directional`, or `spot` |
| `position` | (x,y,z) | Meaningful for point/spot |
| `direction_euler_deg` | (x,y,z) | Meaningful for directional/spot |
| `color_rgb` | (r,g,b), each 0-1 | |
| `intensity` | float >= 0 | |

## Camera fields

| Field | Type | Meaning |
|---|---|---|
| `position` | (x,y,z) | |
| `look_at` | (x,y,z) | Point the camera is aimed at |
| `fov_deg` | float, 1-179 | Vertical field of view |

## Worked example: building a scene by hand (not via build_molecule_scene)

```python
from scene_plan import ScenePlan, Node, Edge, Material, Light, Camera

plan = ScenePlan(
    name="corrosion_demo",
    nodes=[
        Node(id="pipe", primitive="cylinder",
             position=(0, 0, 0), scale=(1.0, 3.0, 1.0),
             material=Material(color_rgba=(0.6, 0.3, 0.1, 1.0), metallic=0.8, roughness=0.4),
             label="pipe segment"),
        Node(id="corrosion_patch", primitive="box",
             position=(0.9, 0.5, 0), scale=(0.1, 0.3, 0.3),
             material=Material(color_rgba=(0.8, 0.2, 0.1, 1.0), roughness=0.9),
             label="corroded region", parent_id="pipe"),
    ],
    lights=[Light(kind="directional", intensity=1.0)],
    camera=Camera(position=(4, 2, 6), look_at=(0, 0, 0)),
)
plan.validate()  # raises ValueError with a specific message if anything is wrong
```

## Worked example: molecule from atom list (the common case)

```python
from scene_plan import build_molecule_scene

plan = build_molecule_scene(
    "caffeine",
    atoms=[("C", 0.0, 0.0, 0.0), ("N", 1.2, 0.3, 0.0), ...],  # (element, x, y, z) in angstroms
    bonds=[(0, 1), (1, 2), ...],  # atom index pairs
)
```

`build_molecule_scene` handles CPK element coloring (`ELEMENT_COLORS`),
element-scaled sphere radii (`ELEMENT_RADII`), a fixed angstrom-to-scene-
unit conversion (0.3, purely a visualization choice), thin bond
cylinders, and two default lights — then calls `.validate()` for you
before returning.

## Units and coordinate convention

Meters, Y-up, right-handed — matching Unity/Unreal's common default and
glTF's spec default. This means:
- `export_obj.py` and `export_gltf.py` need no axis conversion.
- A hypothetical USD/Omniverse exporter (not implemented) WOULD need a
  Y-up → Z-up conversion, since USD defaults to Z-up — this is exactly
  the kind of detail `qfoldit-engine-bridge`'s `engine_comparison.md`
  flags as a real gotcha, not a minor detail to gloss over.
