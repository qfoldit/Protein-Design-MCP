"""
scene_plan.py

A universal, engine-agnostic scene representation for qFoldIT's
cross-engine visualization work. This is pure data + validation logic --
no dependency on any specific 3D engine, so it's fully testable without
a live Unreal/Unity/Unigine/Omniverse/Godot instance.

Design: a scene is a graph of NODES (primitives: sphere, box, cylinder,
capsule, line/cylinder-as-bond) with position/rotation/scale/material,
optionally connected by EDGES (for molecule-like ball-and-stick
structures, or generic parent-child hierarchy). This maps cleanly onto:
- qFoldIT's own outputs (e.g. a folded-protein PDB reduced to
  atom-spheres + bond-cylinders, or an L-system's turtle segments as
  cylinders)
- Both engine-native formats (Unreal actors, Unity GameObjects, Godot
  Spatial nodes) and universal export formats (OBJ, glTF)

Units convention: all positions/scales are in METERS, Y-UP, right-handed
-- matching Unity/Unreal's common default. Exporters are responsible for
converting to their target format's convention (e.g. glTF is also Y-up
right-handed by spec, so no conversion needed there; USD is Z-up by
default, so a USD exporter would need to rotate -- NOT implemented here,
see references/engine_notes.md for why).
"""

import json
import math
from dataclasses import dataclass, field, asdict
from typing import Optional


VALID_PRIMITIVES = {"sphere", "box", "cylinder", "capsule", "cone"}


@dataclass
class Material:
    color_rgba: tuple = (0.8, 0.8, 0.8, 1.0)  # 0-1 floats
    metallic: float = 0.0
    roughness: float = 0.5
    emissive_rgb: tuple = (0.0, 0.0, 0.0)

    def validate(self):
        for name, val in [("color_rgba", self.color_rgba), ("emissive_rgb", self.emissive_rgb)]:
            if not all(0.0 <= c <= 1.0 for c in val):
                raise ValueError(f"{name} components must be in [0,1], got {val}")
        if not (0.0 <= self.metallic <= 1.0):
            raise ValueError(f"metallic must be in [0,1], got {self.metallic}")
        if not (0.0 <= self.roughness <= 1.0):
            raise ValueError(f"roughness must be in [0,1], got {self.roughness}")


@dataclass
class Node:
    id: str
    primitive: str  # one of VALID_PRIMITIVES
    position: tuple = (0.0, 0.0, 0.0)
    rotation_euler_deg: tuple = (0.0, 0.0, 0.0)
    scale: tuple = (1.0, 1.0, 1.0)
    material: Material = field(default_factory=Material)
    label: Optional[str] = None
    parent_id: Optional[str] = None

    def validate(self):
        if self.primitive not in VALID_PRIMITIVES:
            raise ValueError(f"Unknown primitive '{self.primitive}', must be one of {VALID_PRIMITIVES}")
        for name, val in [("position", self.position), ("rotation_euler_deg", self.rotation_euler_deg), ("scale", self.scale)]:
            if len(val) != 3:
                raise ValueError(f"{name} must have exactly 3 components, got {val}")
        if any(s <= 0 for s in self.scale):
            raise ValueError(f"scale components must be > 0, got {self.scale}")
        self.material.validate()


@dataclass
class Edge:
    """A connection between two nodes -- e.g. a chemical bond, or a generic link."""
    from_id: str
    to_id: str
    radius: float = 0.05
    material: Material = field(default_factory=Material)

    def validate(self, known_ids: set):
        if self.from_id not in known_ids:
            raise ValueError(f"Edge references unknown node id '{self.from_id}'")
        if self.to_id not in known_ids:
            raise ValueError(f"Edge references unknown node id '{self.to_id}'")
        if self.radius <= 0:
            raise ValueError(f"Edge radius must be > 0, got {self.radius}")
        self.material.validate()


@dataclass
class Light:
    kind: str  # "point", "directional", "spot"
    position: tuple = (0.0, 5.0, 0.0)
    direction_euler_deg: tuple = (-45.0, 0.0, 0.0)
    color_rgb: tuple = (1.0, 1.0, 1.0)
    intensity: float = 1.0

    def validate(self):
        if self.kind not in ("point", "directional", "spot"):
            raise ValueError(f"Unknown light kind '{self.kind}'")
        if self.intensity < 0:
            raise ValueError("intensity must be >= 0")


@dataclass
class Camera:
    position: tuple = (0.0, 2.0, 8.0)
    look_at: tuple = (0.0, 0.0, 0.0)
    fov_deg: float = 50.0

    def validate(self):
        if not (1.0 <= self.fov_deg <= 179.0):
            raise ValueError(f"fov_deg must be in [1,179], got {self.fov_deg}")


@dataclass
class ScenePlan:
    name: str
    nodes: list = field(default_factory=list)
    edges: list = field(default_factory=list)
    lights: list = field(default_factory=list)
    camera: Camera = field(default_factory=Camera)
    units: str = "meters"

    def validate(self):
        """
        Full structural validation. Raises ValueError on the first problem
        found, with a message specific enough to fix it (not a generic
        'invalid scene plan').
        """
        if not self.name:
            raise ValueError("ScenePlan.name is required and cannot be empty")
        if not self.nodes:
            raise ValueError("ScenePlan must have at least one node")

        seen_ids = set()
        for node in self.nodes:
            if node.id in seen_ids:
                raise ValueError(f"Duplicate node id '{node.id}'")
            seen_ids.add(node.id)
            node.validate()
            if node.parent_id is not None and node.parent_id not in seen_ids and node.parent_id != node.id:
                # allow forward references resolved after the full first pass
                pass

        all_ids = {n.id for n in self.nodes}
        for node in self.nodes:
            if node.parent_id is not None and node.parent_id not in all_ids:
                raise ValueError(f"Node '{node.id}' has parent_id '{node.parent_id}' which does not exist")
            if node.parent_id == node.id:
                raise ValueError(f"Node '{node.id}' cannot be its own parent")

        for edge in self.edges:
            edge.validate(all_ids)

        for light in self.lights:
            light.validate()

        self.camera.validate()

        self._check_no_cycles()

    def _check_no_cycles(self):
        parent_of = {n.id: n.parent_id for n in self.nodes}
        for start in parent_of:
            seen = set()
            cur = start
            while cur is not None:
                if cur in seen:
                    raise ValueError(f"Parent-child cycle detected involving node '{start}'")
                seen.add(cur)
                cur = parent_of.get(cur)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "units": self.units,
            "nodes": [
                {**asdict(n)} for n in self.nodes
            ],
            "edges": [asdict(e) for e in self.edges],
            "lights": [asdict(l) for l in self.lights],
            "camera": asdict(self.camera),
        }

    def to_json(self, indent=2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @staticmethod
    def from_dict(d: dict) -> "ScenePlan":
        nodes = [
            Node(
                id=n["id"], primitive=n["primitive"],
                position=tuple(n.get("position", (0, 0, 0))),
                rotation_euler_deg=tuple(n.get("rotation_euler_deg", (0, 0, 0))),
                scale=tuple(n.get("scale", (1, 1, 1))),
                material=Material(**n.get("material", {})) if isinstance(n.get("material"), dict) else Material(),
                label=n.get("label"),
                parent_id=n.get("parent_id"),
            )
            for n in d.get("nodes", [])
        ]
        edges = [
            Edge(
                from_id=e["from_id"], to_id=e["to_id"],
                radius=e.get("radius", 0.05),
                material=Material(**e.get("material", {})) if isinstance(e.get("material"), dict) else Material(),
            )
            for e in d.get("edges", [])
        ]
        lights = [
            Light(
                kind=l["kind"], position=tuple(l.get("position", (0, 5, 0))),
                direction_euler_deg=tuple(l.get("direction_euler_deg", (-45, 0, 0))),
                color_rgb=tuple(l.get("color_rgb", (1, 1, 1))),
                intensity=l.get("intensity", 1.0),
            )
            for l in d.get("lights", [])
        ]
        camera_d = d.get("camera", {})
        camera = Camera(
            position=tuple(camera_d.get("position", (0, 2, 8))),
            look_at=tuple(camera_d.get("look_at", (0, 0, 0))),
            fov_deg=camera_d.get("fov_deg", 50.0),
        )
        return ScenePlan(
            name=d["name"], nodes=nodes, edges=edges, lights=lights,
            camera=camera, units=d.get("units", "meters"),
        )


# ---------------------------------------------------------------------------
# Convenience builder: molecule (ball-and-stick) from a simple atom list
# ---------------------------------------------------------------------------
ELEMENT_COLORS = {
    # standard CPK-ish coloring, RGBA 0-1
    "C": (0.2, 0.2, 0.2, 1.0),
    "N": (0.13, 0.35, 0.85, 1.0),
    "O": (0.85, 0.15, 0.15, 1.0),
    "H": (0.95, 0.95, 0.95, 1.0),
    "S": (0.9, 0.8, 0.2, 1.0),
    "P": (0.9, 0.5, 0.1, 1.0),
}
ELEMENT_RADII = {  # illustrative relative van-der-Waals-ish radii, not exact
    "C": 0.17, "N": 0.155, "O": 0.15, "H": 0.11, "S": 0.18, "P": 0.18,
}


def build_molecule_scene(name: str, atoms: list, bonds: list) -> ScenePlan:
    """
    atoms: list of (element_symbol, x, y, z) tuples, positions in
           angstroms (converted to a visually reasonable meter scale by
           a fixed factor below -- angstroms are far too small to be a
           usable "meters" scene directly).
    bonds: list of (atom_index_a, atom_index_b) tuples

    Returns a validated ScenePlan with one sphere per atom (CPK-colored,
    element-scaled) and one thin cylinder per bond.
    """
    ANGSTROM_TO_SCENE_UNIT = 0.3  # purely a visualization scale choice, not physically meaningful

    nodes = []
    for i, (elem, x, y, z) in enumerate(atoms):
        color = ELEMENT_COLORS.get(elem, (0.6, 0.6, 0.6, 1.0))
        radius = ELEMENT_RADII.get(elem, 0.15)
        nodes.append(Node(
            id=f"atom_{i}",
            primitive="sphere",
            position=(x * ANGSTROM_TO_SCENE_UNIT, y * ANGSTROM_TO_SCENE_UNIT, z * ANGSTROM_TO_SCENE_UNIT),
            scale=(radius, radius, radius),
            material=Material(color_rgba=color, roughness=0.4),
            label=elem,
        ))

    edges = []
    for (a, b) in bonds:
        edges.append(Edge(from_id=f"atom_{a}", to_id=f"atom_{b}", radius=0.03,
                           material=Material(color_rgba=(0.7, 0.7, 0.7, 1.0))))

    plan = ScenePlan(name=name, nodes=nodes, edges=edges,
                      lights=[Light(kind="directional", intensity=1.2),
                              Light(kind="point", position=(3, 4, 3), intensity=0.6)])
    plan.validate()
    return plan
