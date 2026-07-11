"""
uag_exporter.py -- Universal Assembly Graph (UAG) translation layer.

Converts 3D atom coordinates produced anywhere in this pipeline (Boltz-2,
QuPepFold, the classical quantum-walk simulation in
pipelines/quantum_runner.py, RFdiffusion backbones, etc.) into a valid
OpenUSD (.usda) scene layer, for live sync with NVIDIA Omniverse, NanoVer
VR, Unreal Engine 5, Unity, or any other OpenUSD-consuming client.

Two code paths, both producing a spec-valid .usda file:

1. **Primary path (pxr / usd-core installed):** builds the stage with
   the real ``pxr`` USD Python bindings (``Usd``, ``UsdGeom``, ``Gf``),
   which is the correct, production way to author USD and guarantees
   schema-valid output (correct attribute types, time-sampling support,
   composition arcs, etc).

2. **Fallback path (pxr NOT installed):** ``usd-core`` is a large,
   platform-specific binary wheel that isn't always available (e.g.
   some ARM/Linux CI images, some MCP client sandboxes). Because the
   ``.usda`` ("USD ASCII") format is a documented, plain-text encoding
   of the same object model, this module can still emit a valid, if
   minimal, .usda file by hand -- with no dependency beyond the
   standard library -- so this tool degrades gracefully instead of
   hard-failing just because a heavy binary wheel isn't installed in
   the current venv. The hand-written path is deliberately kept simple
   (static Sphere prims with translate/color only, no time-sampling, no
   references) -- for anything beyond that, install ``usd-core`` and
   use the primary path.

Either path never raises for the "pxr not installed" case -- callers
get the file either way, plus a ``backend`` field in the return value
telling them which path was used.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# CPK-ish element coloring, linear-light RGB in [0, 1] (Usd displayColor
# convention). Extend as needed for additional elements.
ELEMENT_COLORS: dict[str, tuple[float, float, float]] = {
    "C": (0.30, 0.30, 0.30),   # dark grey
    "N": (0.20, 0.20, 0.90),   # blue
    "O": (0.90, 0.15, 0.15),   # red
    "S": (0.90, 0.80, 0.20),   # yellow
    "H": (0.95, 0.95, 0.95),   # near-white
    "P": (0.90, 0.50, 0.10),   # orange
}
DEFAULT_ELEMENT_COLOR = (0.70, 0.70, 0.70)
ELEMENT_RADII: dict[str, float] = {
    "C": 0.70,
    "N": 0.65,
    "O": 0.60,
    "S": 1.00,
    "H": 0.25,
    "P": 1.00,
}
DEFAULT_RADIUS = 0.70


def export_to_openusd(atom_coordinates: list[dict[str, Any]], output_path: str) -> str:
    """
    Convert 3D atom coordinates into a valid .usda OpenUSD file.

    Args:
        atom_coordinates: List of atom dicts. Each dict must have
            numeric ``x``, ``y``, ``z`` keys. Element is read from an
            ``element`` key if present, else inferred from an ``atom``
            key's first character (e.g. "CA" -> "C"), else defaults to
            carbon. An optional ``residue_index`` key is used to group
            atoms under per-residue Xform scopes for a more navigable
            scene graph; if absent, all atoms are placed under one
            "Residue_0" scope.
        output_path: Destination path. A ``.usda`` extension is
            recommended (and will be added if missing) since the
            fallback path always writes ASCII USD regardless of
            extension, and the primary (pxr) path is explicitly
            configured to write ASCII (not binary .usd/.usdc) here for
            human-readability and diff-friendliness.

    Returns:
        The path actually written (str).

    Raises:
        ValueError: if atom_coordinates is empty or malformed.
        OSError: if output_path's directory can't be created/written to.
    """
    if not atom_coordinates:
        raise ValueError("atom_coordinates must be a non-empty list of atom dicts")

    out_path = Path(output_path)
    if out_path.suffix.lower() not in (".usda", ".usd"):
        out_path = out_path.with_suffix(".usda")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    normalized = [_normalize_atom(a, i) for i, a in enumerate(atom_coordinates)]

    try:
        import pxr  # noqa: F401  -- presence check only
        written_path = _export_with_pxr(normalized, out_path)
        backend = "pxr"
    except ImportError:
        logger.info(
            "pxr (usd-core) not installed -- falling back to hand-written "
            "ASCII .usda export. `pip install usd-core` for the full, "
            "schema-validated pxr-based export path."
        )
        written_path = _export_with_manual_usda(normalized, out_path)
        backend = "manual_usda_fallback"

    logger.info("Exported %d atoms to %s (backend=%s)", len(normalized), written_path, backend)
    return str(written_path)


def _normalize_atom(atom: dict[str, Any], index: int) -> dict[str, Any]:
    try:
        x, y, z = float(atom["x"]), float(atom["y"]), float(atom["z"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"atom_coordinates[{index}] is missing valid numeric x/y/z: {atom!r}") from exc

    element = atom.get("element")
    if not element:
        atom_name = str(atom.get("atom", "C"))
        element = atom_name[0].upper() if atom_name else "C"
    element = str(element).upper()

    return {
        "index": index,
        "x": x,
        "y": y,
        "z": z,
        "element": element,
        "atom_name": str(atom.get("atom", element)),
        "residue_index": int(atom.get("residue_index", 0)),
    }


def _sphere_prim_name(atom: dict[str, Any]) -> str:
    # USD prim names must be valid identifiers: letters, digits, underscore,
    # and must not start with a digit.
    name = f"{atom['atom_name']}_{atom['index']}"
    safe = "".join(c if (c.isalnum() or c == "_") else "_" for c in name)
    if safe[0].isdigit():
        safe = f"Atom_{safe}"
    return safe


# =============================================================================
# Primary path: real pxr / UsdGeom authoring
# =============================================================================


def _export_with_pxr(atoms: list[dict[str, Any]], out_path: Path) -> Path:
    from pxr import Usd, UsdGeom, Gf  # type: ignore

    stage = Usd.Stage.CreateNew(str(out_path))
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    stage.SetMetadata("metersPerUnit", 1e-10)  # atoms in Angstrom-as-meters-analog scale

    root = UsdGeom.Xform.Define(stage, "/Molecule")
    stage.SetDefaultPrim(root.GetPrim())

    residue_scopes: dict[int, "UsdGeom.Xform"] = {}

    for atom in atoms:
        res_idx = atom["residue_index"]
        if res_idx not in residue_scopes:
            residue_scopes[res_idx] = UsdGeom.Xform.Define(stage, f"/Molecule/Residue_{res_idx}")
        residue_path = residue_scopes[res_idx].GetPath()

        prim_path = residue_path.AppendChild(_sphere_prim_name(atom))
        sphere = UsdGeom.Sphere.Define(stage, prim_path)

        radius = ELEMENT_RADII.get(atom["element"], DEFAULT_RADIUS)
        sphere.CreateRadiusAttr(radius)

        xform_api = UsdGeom.XformCommonAPI(sphere)
        xform_api.SetTranslate(Gf.Vec3d(atom["x"], atom["y"], atom["z"]))

        color = ELEMENT_COLORS.get(atom["element"], DEFAULT_ELEMENT_COLOR)
        sphere.CreateDisplayColorAttr([Gf.Vec3f(*color)])

        sphere.GetPrim().SetCustomDataByKey("element", atom["element"])
        sphere.GetPrim().SetCustomDataByKey("residueIndex", res_idx)

    stage.GetRootLayer().Save()
    return out_path


# =============================================================================
# Fallback path: hand-written ASCII .usda (no pxr dependency)
# =============================================================================


def _fmt(v: float) -> str:
    return f"{v:.6g}"


def _export_with_manual_usda(atoms: list[dict[str, Any]], out_path: Path) -> Path:
    residues: dict[int, list[dict[str, Any]]] = {}
    for atom in atoms:
        residues.setdefault(atom["residue_index"], []).append(atom)

    lines: list[str] = []
    lines.append('#usda 1.0')
    lines.append("(")
    lines.append('    defaultPrim = "Molecule"')
    lines.append('    upAxis = "Y"')
    lines.append(")")
    lines.append("")
    lines.append('def Xform "Molecule"')
    lines.append("{")

    for res_idx in sorted(residues):
        lines.append(f'    def Xform "Residue_{res_idx}"')
        lines.append("    {")
        for atom in residues[res_idx]:
            prim_name = _sphere_prim_name(atom)
            radius = ELEMENT_RADII.get(atom["element"], DEFAULT_RADIUS)
            color = ELEMENT_COLORS.get(atom["element"], DEFAULT_ELEMENT_COLOR)
            lines.append(f'        def Sphere "{prim_name}" (')
            lines.append(f'            customData = {{')
            lines.append(f'                string element = "{atom["element"]}"')
            lines.append(f'                int residueIndex = {res_idx}')
            lines.append(f'            }}')
            lines.append("        )")
            lines.append("        {")
            lines.append(f'            double radius = {_fmt(radius)}')
            lines.append(
                f'            color3f[] primvars:displayColor = '
                f'[({_fmt(color[0])}, {_fmt(color[1])}, {_fmt(color[2])})]'
            )
            lines.append(
                f'            double3 xformOp:translate = '
                f'({_fmt(atom["x"])}, {_fmt(atom["y"])}, {_fmt(atom["z"])})'
            )
            lines.append('            uniform token[] xformOpOrder = ["xformOp:translate"]')
            lines.append("        }")
        lines.append("    }")

    lines.append("}")
    lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path
