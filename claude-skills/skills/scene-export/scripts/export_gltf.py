"""
export_gltf.py

Exports a ScenePlan to glTF 2.0 (the .gltf JSON variant, with geometry
embedded as a base64 data URI buffer -- a single self-contained file,
no separate .bin needed). glTF is Y-up, right-handed, meters by default
-- exactly matching this project's ScenePlan convention, so no axis
conversion is needed here (unlike a hypothetical USD exporter, which
would need one -- see references/engine_notes.md).

Reuses the same primitive tessellation as export_obj.py (icosphere, box,
cylinder) to avoid maintaining two separate mesh-generation
implementations.
"""

import base64
import json
import struct

from scene_plan import ScenePlan
from export_obj import _PRIMITIVE_MESH, _transform, _rotate_point


def _mesh_to_gltf_accessors(local_verts, faces, node, buffer_bytes, accessors, buffer_views):
    """
    Appends this primitive's vertex+index data to the shared binary
    buffer, and returns the accessor indices needed for a glTF
    primitive entry (POSITION accessor idx, indices accessor idx).
    """
    world_verts = [_transform(v, node) for v in local_verts]

    vert_bytes = b"".join(struct.pack("<3f", *v) for v in world_verts)
    vert_offset = len(buffer_bytes)
    buffer_bytes.extend(vert_bytes)
    while len(buffer_bytes) % 4 != 0:
        buffer_bytes.append(0)

    flat_indices = [idx for face in faces for idx in face]
    use_uint32 = len(world_verts) > 65535
    fmt = "<I" if use_uint32 else "<H"
    idx_bytes = b"".join(struct.pack(fmt, i) for i in flat_indices)
    idx_offset = len(buffer_bytes)
    buffer_bytes.extend(idx_bytes)
    while len(buffer_bytes) % 4 != 0:
        buffer_bytes.append(0)

    pos_bv_idx = len(buffer_views)
    buffer_views.append({
        "buffer": 0, "byteOffset": vert_offset, "byteLength": len(vert_bytes), "target": 34962,
    })
    idx_bv_idx = len(buffer_views)
    buffer_views.append({
        "buffer": 0, "byteOffset": idx_offset, "byteLength": len(idx_bytes), "target": 34963,
    })

    xs = [v[0] for v in world_verts]; ys = [v[1] for v in world_verts]; zs = [v[2] for v in world_verts]
    pos_acc_idx = len(accessors)
    accessors.append({
        "bufferView": pos_bv_idx, "componentType": 5126, "count": len(world_verts), "type": "VEC3",
        "min": [min(xs), min(ys), min(zs)], "max": [max(xs), max(ys), max(zs)],
    })
    idx_acc_idx = len(accessors)
    accessors.append({
        "bufferView": idx_bv_idx,
        "componentType": 5125 if use_uint32 else 5123,
        "count": len(flat_indices), "type": "SCALAR",
    })

    return pos_acc_idx, idx_acc_idx


def export_gltf(plan: ScenePlan, path: str) -> dict:
    """
    Writes plan to a self-contained .gltf JSON file (geometry embedded
    as a base64 data URI). Returns the parsed glTF dict for
    verification (so a caller/test doesn't have to re-read+re-parse the
    file).
    """
    buffer_bytes = bytearray()
    accessors = []
    buffer_views = []
    materials = []
    material_index = {}
    meshes = []
    gltf_nodes = []
    node_index = {}

    def get_material_index(mat):
        key = (round(mat.color_rgba[0], 3), round(mat.color_rgba[1], 3),
               round(mat.color_rgba[2], 3), round(mat.color_rgba[3], 3),
               round(mat.metallic, 2), round(mat.roughness, 2))
        if key in material_index:
            return material_index[key]
        idx = len(materials)
        materials.append({
            "pbrMetallicRoughness": {
                "baseColorFactor": list(mat.color_rgba),
                "metallicFactor": mat.metallic,
                "roughnessFactor": mat.roughness,
            },
            "emissiveFactor": list(mat.emissive_rgb),
        })
        material_index[key] = idx
        return idx

    for node in plan.nodes:
        mesh_fn = _PRIMITIVE_MESH.get(node.primitive)
        if mesh_fn is None:
            raise ValueError(f"No mesh generator for primitive '{node.primitive}'")
        local_verts, faces = mesh_fn()
        # export_gltf bakes transforms into vertex positions (matching export_obj's
        # approach) rather than using glTF's native node TRS -- simpler and keeps
        # this exporter consistent with export_obj.py's baked-world-space output.
        pos_acc, idx_acc = _mesh_to_gltf_accessors(local_verts, faces, node, buffer_bytes, accessors, buffer_views)
        mat_idx = get_material_index(node.material)
        mesh_idx = len(meshes)
        meshes.append({
            "primitives": [{
                "attributes": {"POSITION": pos_acc},
                "indices": idx_acc,
                "material": mat_idx,
            }]
        })
        gltf_node_idx = len(gltf_nodes)
        gltf_nodes.append({"mesh": mesh_idx, "name": node.id})
        node_index[node.id] = gltf_node_idx

    # bonds/edges as cylinders, same approach as export_obj's edge handling
    import math
    for i, edge in enumerate(plan.edges):
        node_a = next(n for n in plan.nodes if n.id == edge.from_id)
        node_b = next(n for n in plan.nodes if n.id == edge.to_id)
        pa, pb = node_a.position, node_b.position
        dx, dy, dz = pb[0]-pa[0], pb[1]-pa[1], pb[2]-pa[2]
        length = math.sqrt(dx*dx+dy*dy+dz*dz)
        if length < 1e-9:
            continue
        local_verts, faces = _PRIMITIVE_MESH["cylinder"]()
        target = (dx/length, dy/length, dz/length)
        axis = (target[2], 0.0, -target[0])
        axis_len = math.sqrt(sum(c*c for c in axis))
        angle = math.acos(max(-1.0, min(1.0, target[1])))
        mid = ((pa[0]+pb[0])/2, (pa[1]+pb[1])/2, (pa[2]+pb[2])/2)

        transformed = []
        for lv in local_verts:
            x, y, z = lv[0]*edge.radius, lv[1]*(length/2), lv[2]*edge.radius
            if axis_len > 1e-9:
                ax = (axis[0]/axis_len, axis[1]/axis_len, axis[2]/axis_len)
                cos_a, sin_a = math.cos(angle), math.sin(angle)
                dotv = x*ax[0]+y*ax[1]+z*ax[2]
                crossv = (ax[1]*z-ax[2]*y, ax[2]*x-ax[0]*z, ax[0]*y-ax[1]*x)
                x2 = x*cos_a + crossv[0]*sin_a + ax[0]*dotv*(1-cos_a)
                y2 = y*cos_a + crossv[1]*sin_a + ax[1]*dotv*(1-cos_a)
                z2 = z*cos_a + crossv[2]*sin_a + ax[2]*dotv*(1-cos_a)
                x, y, z = x2, y2, z2
            transformed.append((x+mid[0], y+mid[1], z+mid[2]))

        class _FakeNode:
            position = (0, 0, 0)
            rotation_euler_deg = (0, 0, 0)
            scale = (1, 1, 1)
        pos_acc, idx_acc = _mesh_to_gltf_accessors(transformed, faces, _FakeNode(), buffer_bytes, accessors, buffer_views)
        mat_idx = get_material_index(edge.material)
        mesh_idx = len(meshes)
        meshes.append({"primitives": [{"attributes": {"POSITION": pos_acc}, "indices": idx_acc, "material": mat_idx}]})
        gltf_node_idx = len(gltf_nodes)
        gltf_nodes.append({"mesh": mesh_idx, "name": f"bond_{i}"})

    while len(buffer_bytes) % 4 != 0:
        buffer_bytes.append(0)
    b64 = base64.b64encode(bytes(buffer_bytes)).decode("ascii")

    gltf = {
        "asset": {"version": "2.0", "generator": "qfoldit-scene-export"},
        "scene": 0,
        "scenes": [{"nodes": list(range(len(gltf_nodes)))}],
        "nodes": gltf_nodes,
        "meshes": meshes,
        "materials": materials,
        "accessors": accessors,
        "bufferViews": buffer_views,
        "buffers": [{"byteLength": len(buffer_bytes), "uri": f"data:application/octet-stream;base64,{b64}"}],
    }

    with open(path, "w") as f:
        json.dump(gltf, f)

    return gltf
