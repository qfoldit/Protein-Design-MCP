"""
export_obj.py

Exports a ScenePlan to Wavefront OBJ -- the simplest universal 3D format,
readable by essentially every 3D tool/engine in existence (Unity, Unreal,
Blender, Godot, Omniverse, etc. all import OBJ natively).

OBJ has no native material-per-face color in the base spec (that needs a
companion .mtl file, which this module also generates) and no built-in
hierarchy/scene-graph concept -- every primitive is baked into world-
space vertices, which is exactly why this format is a good universal
"lowest common denominator" fallback when live engine control isn't
available.

Primitives are tessellated as real geometry (icosphere-style for
spheres, standard box/cylinder meshes) -- not just point markers -- so
the output is genuinely viewable/usable in any OBJ-capable tool.
"""

import math
from scene_plan import ScenePlan, Node


def _rotate_point(p, euler_deg):
    """Applies XYZ Euler rotation (degrees) to a point, in that order."""
    x, y, z = p
    rx, ry, rz = (math.radians(a) for a in euler_deg)

    # rotate around X
    y, z = y * math.cos(rx) - z * math.sin(rx), y * math.sin(rx) + z * math.cos(rx)
    # rotate around Y
    x, z = x * math.cos(ry) + z * math.sin(ry), -x * math.sin(ry) + z * math.cos(ry)
    # rotate around Z
    x, y = x * math.cos(rz) - y * math.sin(rz), x * math.sin(rz) + y * math.cos(rz)
    return (x, y, z)


def _transform(local_pt, node: Node):
    x, y, z = local_pt
    sx, sy, sz = node.scale
    scaled = (x * sx, y * sy, z * sz)
    rotated = _rotate_point(scaled, node.rotation_euler_deg)
    px, py, pz = node.position
    return (rotated[0] + px, rotated[1] + py, rotated[2] + pz)


def _icosphere(subdivisions=1):
    """Returns (vertices, faces) for a unit icosphere centered at origin."""
    t = (1.0 + math.sqrt(5.0)) / 2.0
    verts = [
        (-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0),
        (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t),
        (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1),
    ]
    norm = lambda v: (lambda l: (v[0]/l, v[1]/l, v[2]/l))(math.sqrt(sum(c*c for c in v)))
    verts = [norm(v) for v in verts]
    faces = [
        (0,11,5),(0,5,1),(0,1,7),(0,7,10),(0,10,11),
        (1,5,9),(5,11,4),(11,10,2),(10,7,6),(7,1,8),
        (3,9,4),(3,4,2),(3,2,6),(3,6,8),(3,8,9),
        (4,9,5),(2,4,11),(6,2,10),(8,6,7),(9,8,1),
    ]
    for _ in range(subdivisions):
        mid_cache = {}
        def midpoint(i1, i2):
            key = tuple(sorted((i1, i2)))
            if key in mid_cache:
                return mid_cache[key]
            v1, v2 = verts[i1], verts[i2]
            mid = norm(((v1[0]+v2[0])/2, (v1[1]+v2[1])/2, (v1[2]+v2[2])/2))
            verts.append(mid)
            idx = len(verts) - 1
            mid_cache[key] = idx
            return idx
        new_faces = []
        for (a, b, c) in faces:
            ab, bc, ca = midpoint(a,b), midpoint(b,c), midpoint(c,a)
            new_faces += [(a,ab,ca),(b,bc,ab),(c,ca,bc),(ab,bc,ca)]
        faces = new_faces
    return verts, faces


def _box():
    verts = [
        (-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
        (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1),
    ]
    faces = [
        (0,1,2),(0,2,3), (4,6,5),(4,7,6),
        (0,4,5),(0,5,1), (1,5,6),(1,6,2),
        (2,6,7),(2,7,3), (3,7,4),(3,4,0),
    ]
    return verts, faces


def _cylinder(segments=12):
    verts = []
    for i in range(segments):
        a = 2 * math.pi * i / segments
        verts.append((math.cos(a), -1, math.sin(a)))
    for i in range(segments):
        a = 2 * math.pi * i / segments
        verts.append((math.cos(a), 1, math.sin(a)))
    verts.append((0, -1, 0))  # bottom center
    verts.append((0, 1, 0))   # top center
    bottom_c, top_c = len(verts) - 2, len(verts) - 1
    faces = []
    for i in range(segments):
        j = (i + 1) % segments
        faces.append((i, j, segments + j))
        faces.append((i, segments + j, segments + i))
        faces.append((bottom_c, j, i))
        faces.append((top_c, segments + i, segments + j))
    return verts, faces


_PRIMITIVE_MESH = {
    "sphere": lambda: _icosphere(1),
    "capsule": lambda: _icosphere(1),  # simplified: a capsule is approximated as a sphere in this exporter
    "box": _box,
    "cylinder": _cylinder,
    "cone": _cylinder,  # simplified: a cone is approximated as a cylinder in this exporter (see references)
}


def export_obj(plan: ScenePlan, obj_path: str, mtl_path: str = None):
    """
    Writes plan to a .obj file (plus a companion .mtl if mtl_path is
    given). Each node's material becomes one 'usemtl' group.

    Bonds/edges are rendered as thin cylinders oriented from one node's
    position to the other's.

    Returns (num_vertices, num_faces, num_materials) for verification.
    """
    if mtl_path is None:
        mtl_path = obj_path.rsplit(".", 1)[0] + ".mtl"
    mtl_name = mtl_path.split("/")[-1]

    all_verts = []
    all_faces = []  # (material_name, [(v1,v2,v3), ...] using 1-based global indices)
    materials = {}  # name -> Material

    def add_material(mat, prefix):
        key = f"{prefix}_{round(mat.color_rgba[0],3)}_{round(mat.color_rgba[1],3)}_{round(mat.color_rgba[2],3)}_{round(mat.metallic,2)}_{round(mat.roughness,2)}"
        materials[key] = mat
        return key

    for node in plan.nodes:
        mesh_fn = _PRIMITIVE_MESH.get(node.primitive)
        if mesh_fn is None:
            raise ValueError(f"No OBJ mesh generator for primitive '{node.primitive}'")
        local_verts, faces = mesh_fn()
        base_index = len(all_verts)
        for lv in local_verts:
            all_verts.append(_transform(lv, node))
        mat_key = add_material(node.material, node.id)
        all_faces.append((mat_key, [(f[0]+base_index+1, f[1]+base_index+1, f[2]+base_index+1) for f in faces]))

    for edge in plan.edges:
        node_a = next(n for n in plan.nodes if n.id == edge.from_id)
        node_b = next(n for n in plan.nodes if n.id == edge.to_id)
        pa, pb = node_a.position, node_b.position
        dx, dy, dz = pb[0]-pa[0], pb[1]-pa[1], pb[2]-pa[2]
        length = math.sqrt(dx*dx+dy*dy+dz*dz)
        if length < 1e-9:
            continue
        # build a unit cylinder then orient it from pa to pb
        local_verts, faces = _cylinder(segments=8)
        # cylinder is along Y by construction; compute rotation to align Y with (dx,dy,dz)
        target = (dx/length, dy/length, dz/length)
        # simple rotation via axis-angle from (0,1,0) to target
        axis = (target[2], 0.0, -target[0])  # cross((0,1,0), target)
        axis_len = math.sqrt(sum(c*c for c in axis))
        angle = math.acos(max(-1.0, min(1.0, target[1])))
        mid = ((pa[0]+pb[0])/2, (pa[1]+pb[1])/2, (pa[2]+pb[2])/2)

        base_index = len(all_verts)
        for lv in local_verts:
            x, y, z = lv[0]*edge.radius, lv[1]*(length/2), lv[2]*edge.radius
            if axis_len > 1e-9:
                ax = (axis[0]/axis_len, axis[1]/axis_len, axis[2]/axis_len)
                # Rodrigues' rotation formula
                cos_a, sin_a = math.cos(angle), math.sin(angle)
                dotv = x*ax[0] + y*ax[1] + z*ax[2]
                crossv = (ax[1]*z - ax[2]*y, ax[2]*x - ax[0]*z, ax[0]*y - ax[1]*x)
                x2 = x*cos_a + crossv[0]*sin_a + ax[0]*dotv*(1-cos_a)
                y2 = y*cos_a + crossv[1]*sin_a + ax[1]*dotv*(1-cos_a)
                z2 = z*cos_a + crossv[2]*sin_a + ax[2]*dotv*(1-cos_a)
                x, y, z = x2, y2, z2
            all_verts.append((x+mid[0], y+mid[1], z+mid[2]))
        mat_key = add_material(edge.material, f"edge_{edge.from_id}_{edge.to_id}")
        all_faces.append((mat_key, [(f[0]+base_index+1, f[1]+base_index+1, f[2]+base_index+1) for f in faces]))

    with open(obj_path, "w") as f:
        f.write(f"# qFoldIT scene export: {plan.name}\n")
        f.write(f"mtllib {mtl_name}\n")
        for v in all_verts:
            f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
        for mat_key, faces in all_faces:
            f.write(f"usemtl {mat_key}\n")
            for face in faces:
                f.write(f"f {face[0]} {face[1]} {face[2]}\n")

    with open(mtl_path, "w") as f:
        for key, mat in materials.items():
            f.write(f"newmtl {key}\n")
            f.write(f"Kd {mat.color_rgba[0]:.4f} {mat.color_rgba[1]:.4f} {mat.color_rgba[2]:.4f}\n")
            f.write(f"d {mat.color_rgba[3]:.4f}\n")
            f.write(f"Pm {mat.metallic:.4f}\n" if False else "")  # Pm/Pr are PBR extension, not core MTL; omitted for compatibility
            f.write("\n")

    return len(all_verts), sum(len(f) for _, f in all_faces), len(materials)
