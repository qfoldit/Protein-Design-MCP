"""
export_threejs.py

Generates a self-contained, standalone HTML file with an embedded
Three.js scene built from a ScenePlan -- viewable in any browser, no
build step, no server. Uses OrbitControls for interactive inspection
(rotate/pan/zoom with the mouse).

Three.js is loaded from a CDN (cdnjs.cloudflare.com), matching the
convention used elsewhere in this environment for HTML artifacts -- the
generated file therefore needs internet access to actually load Three.js
in a browser (it is NOT fully offline-capable, unlike the OBJ/glTF
exporters' output files, which have zero runtime dependencies).
"""

import json
from scene_plan import ScenePlan


_THREEJS_GEOMETRY = {
    "sphere": "new THREE.SphereGeometry(1, 24, 16)",
    "box": "new THREE.BoxGeometry(2, 2, 2)",
    "cylinder": "new THREE.CylinderGeometry(1, 1, 2, 16)",
    "capsule": "new THREE.CapsuleGeometry(0.7, 1.2, 4, 12)",
    "cone": "new THREE.ConeGeometry(1, 2, 16)",
}


def export_threejs_html(plan: ScenePlan, path: str, title: str = None):
    """
    Writes plan to a standalone HTML file with an embedded, interactive
    Three.js scene. Returns the path written (for convenience/chaining).
    """
    title = title or plan.name

    node_js = []
    for n in plan.nodes:
        geo = _THREEJS_GEOMETRY.get(n.primitive)
        if geo is None:
            raise ValueError(f"No Three.js geometry mapping for primitive '{n.primitive}'")
        c = n.material.color_rgba
        rx, ry, rz = (__import__("math").radians(a) for a in n.rotation_euler_deg)
        node_js.append(f"""
{{
  const geo = {geo};
  const mat = new THREE.MeshStandardMaterial({{
    color: new THREE.Color({c[0]}, {c[1]}, {c[2]}),
    transparent: {str(c[3] < 1.0).lower()},
    opacity: {c[3]},
    metalness: {n.material.metallic},
    roughness: {n.material.roughness},
  }});
  const mesh = new THREE.Mesh(geo, mat);
  mesh.position.set({n.position[0]}, {n.position[1]}, {n.position[2]});
  mesh.rotation.set({rx}, {ry}, {rz});
  mesh.scale.set({n.scale[0]}, {n.scale[1]}, {n.scale[2]});
  mesh.userData.id = {json.dumps(n.id)};
  if ({json.dumps(n.label)}) mesh.userData.label = {json.dumps(n.label)};
  scene.add(mesh);
}}""")

    edge_js = []
    for e in plan.edges:
        node_a = next(x for x in plan.nodes if x.id == e.from_id)
        node_b = next(x for x in plan.nodes if x.id == e.to_id)
        c = e.material.color_rgba
        edge_js.append(f"""
{{
  const a = new THREE.Vector3({node_a.position[0]}, {node_a.position[1]}, {node_a.position[2]});
  const b = new THREE.Vector3({node_b.position[0]}, {node_b.position[1]}, {node_b.position[2]});
  const dir = new THREE.Vector3().subVectors(b, a);
  const len = dir.length();
  const geo = new THREE.CylinderGeometry({e.radius}, {e.radius}, len, 8);
  const mat = new THREE.MeshStandardMaterial({{ color: new THREE.Color({c[0]}, {c[1]}, {c[2]}) }});
  const mesh = new THREE.Mesh(geo, mat);
  mesh.position.copy(a).addScaledVector(dir, 0.5);
  mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0), dir.clone().normalize());
  scene.add(mesh);
}}""")

    light_js = []
    for l in plan.lights:
        if l.kind == "directional":
            light_js.append(f"""
{{
  const light = new THREE.DirectionalLight(new THREE.Color({l.color_rgb[0]}, {l.color_rgb[1]}, {l.color_rgb[2]}), {l.intensity});
  light.position.set(3, 5, 2);
  scene.add(light);
}}""")
        elif l.kind == "point":
            light_js.append(f"""
{{
  const light = new THREE.PointLight(new THREE.Color({l.color_rgb[0]}, {l.color_rgb[1]}, {l.color_rgb[2]}), {l.intensity}, 0, 2);
  light.position.set({l.position[0]}, {l.position[1]}, {l.position[2]});
  scene.add(light);
}}""")
        elif l.kind == "spot":
            light_js.append(f"""
{{
  const light = new THREE.SpotLight(new THREE.Color({l.color_rgb[0]}, {l.color_rgb[1]}, {l.color_rgb[2]}), {l.intensity});
  light.position.set({l.position[0]}, {l.position[1]}, {l.position[2]});
  scene.add(light);
}}""")
    if not plan.lights:
        light_js.append("scene.add(new THREE.AmbientLight(0xffffff, 0.6));")

    cam = plan.camera
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{title} — qFoldIT scene export</title>
<style>
  body {{ margin:0; overflow:hidden; background:#111318; font-family: sans-serif; }}
  #info {{ position:absolute; top:10px; left:10px; color:#aaa; font-size:12px; }}
</style>
</head>
<body>
<div id="info">{title} — drag to rotate, scroll to zoom</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/examples/js/controls/OrbitControls.js"></script>
<script>
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x111318);

const camera = new THREE.PerspectiveCamera({cam.fov_deg}, window.innerWidth/window.innerHeight, 0.01, 1000);
camera.position.set({cam.position[0]}, {cam.position[1]}, {cam.position[2]});
camera.lookAt({cam.look_at[0]}, {cam.look_at[1]}, {cam.look_at[2]});

const renderer = new THREE.WebGLRenderer({{ antialias: true }});
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

const controls = new THREE.OrbitControls(camera, renderer.domElement);
controls.target.set({cam.look_at[0]}, {cam.look_at[1]}, {cam.look_at[2]});

{"".join(light_js)}
{"".join(node_js)}
{"".join(edge_js)}

function animate() {{
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
}}
animate();

window.addEventListener('resize', () => {{
  camera.aspect = window.innerWidth/window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
}});
</script>
</body>
</html>
"""
    with open(path, "w") as f:
        f.write(html)
    return path
