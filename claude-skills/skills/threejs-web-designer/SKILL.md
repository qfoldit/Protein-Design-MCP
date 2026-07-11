---
name: threejs-web-designer
description: Exports a validated Universal Assembly Graph (UAG, from game-designer/digital-twin-builder) to a browser-based Three.js/React Three Fiber (R3F) WebXR experience. Use this skill when the user wants a qFoldIT UAG realized as a web/browser 3D experience, multiplayer visualization, or rapid prototype, or asks about Three.js/R3F/WebXR in the context of a qFoldIT scene.
---

# threejs-web-designer

**Status: community ecosystem, no single official skill.** Neither Three.js's maintainers nor Vercel/Poimandres (React Three Fiber) publish one authoritative "the" Claude skill for this stack -- there is instead a crowded, actively-maintained community ecosystem (multiple independent skill repos covering R3F fundamentals, drei, physics via Rapier, shaders, performance). The core APIs referenced below (Canvas, useFrame, drei) are stable, well-documented public APIs, not claims about any specific skill's authority.

## Stack

```bash
npm install three @react-three/fiber @react-three/drei
npm install -D @types/three
npm install @react-three/postprocessing   # optional
npm install @react-three/xr               # needed specifically for WebXR interactions
```

## UAG -> R3F mapping

Baseline from `game-designer/references/uag_schema.md`: `node type=mesh` -> `<mesh>` + geometry/material JSX, `type=light` -> `<pointLight>`/`<directionalLight>`, `parent_child` -> React component nesting (children), `physics_collision` -> Rapier (`@react-three/rapier`) rigidbody/collider, `on_grab`/interactions -> `@react-three/xr` interaction hooks.

## Core patterns (stable, standard R3F -- verify against current docs for anything beyond this)

```jsx
import { Canvas, useFrame } from '@react-three/fiber'

function Node({ position, rotation }) {
  const ref = useRef()
  useFrame((state, delta) => {
    // per-frame updates here; NEVER call setState inside useFrame -- causes
    // unnecessary re-renders and defeats the point of the render loop
  })
  return (
    <mesh ref={ref} position={position} rotation={rotation}>
      <boxGeometry args={[1, 1, 1]} />
      <meshStandardMaterial color="#6366f1" />
    </mesh>
  )
}

export default function Scene({ uag }) {
  return (
    <Canvas camera={{ position: [0, 0, 5], fov: 75 }} dpr={[1, 2]}>
      {uag.nodes.filter(n => !n.parent_id).map(n => <Node key={n.id} {...n} />)}
    </Canvas>
  )
}
```

## Workflow

1. Confirm the UAG passed `game-designer/scripts/uag_validate.py`.
2. Walk `nodes` respecting `parent_id` hierarchy as React component nesting (root nodes first).
3. Map `constraints`/`interactions` to Rapier/`@react-three/xr` per the table above; unmapped types get flagged, not silently dropped.
4. Performance: cap device pixel ratio (`dpr={[1,2]}`), use `drei`'s `<Instances>` for repeated geometry (e.g. many identical procedural plants from `l-systems`), and dispose of geometries/materials on unmount -- GPU resources leak silently otherwise.

## qFoldIT-specific notes

- Best fit for rapid browser prototypes and multiplayer visualization of a UAG (e.g. sharing a `mining`/`plant-growth` digital twin as a link, no VR headset or engine install required) rather than the primary "МАС «Снежинка»" VR experience (Unreal).
- If a UAG scene includes procedurally generated geometry from `l-systems`, prefer generating the SVG/point data once (Python) and importing it as static geometry, rather than re-implementing L-system expansion in JS.
