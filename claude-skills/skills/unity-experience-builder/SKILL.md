---
name: unity-experience-builder
description: Exports a validated Universal Assembly Graph (UAG, from game-designer/digital-twin-builder) into a live Unity scene, using CoplayDev/unity-mcp -- a community MIT-licensed bridge that is NOT affiliated with Unity Technologies. Use this skill when the user wants a qFoldIT UAG realized in Unity, or asks about Unity GameObjects/materials/scripts/physics/XR in the context of a qFoldIT scene.
---

# unity-experience-builder

**Status: community, NOT official Unity Technologies.** Built on `CoplayDev/unity-mcp`, which explicitly states it is "not affiliated with Unity Technologies." It is the de-facto standard today (MIT, 5800+ stars) but must never be described as an official Unity product in any qFoldIT material. If Unity Technologies ships a first-party MCP integration, prefer it over this one per the plugin's "prefer official" principle.

## Prerequisites

1. Unity 2021.3 LTS -> 6.x, Python 3.10+ (via `uv`).
2. Package install: **Window -> Package Manager -> + -> Add package from git URL**: `https://github.com/CoplayDev/unity-mcp.git?path=/MCPForUnity#main`
3. **Window -> MCP for Unity -> Configure All Detected Clients** to wire up Claude Code/Desktop automatically.
4. Verify: ask for something trivial ("create a cube at the origin with a Rigidbody") and confirm it appears in the scene.

## UAG -> Unity mapping

Baseline from `game-designer/references/uag_schema.md` (mesh -> GameObject+MeshRenderer, light -> GameObject+Light, parent_child -> Transform.SetParent, physics_collision -> Collider+Rigidbody, on_grab -> XR Interaction Toolkit Grabbable).

## Key tools (by domain)

`manage_gameobject` (create/modify GameObjects+components), `manage_material`, `manage_script` (create/edit via `apply_text_edits`), `manage_physics` (collision layers, joints, raycasts, forces), `manage_animation`, `manage_profiler`, `batch_execute` (multiple calls in one round-trip). Activate only the tool groups you need (`vfx`/`animation`/`ui`/`testing`/`probuilder`) rather than all of them at once, for cleaner routing.

## Workflow

1. Confirm the UAG passed `game-designer/scripts/uag_validate.py`.
2. Walk `nodes` in hierarchy order (parents before children where possible), calling `manage_gameobject` per node per the mapping table; unmapped `type`/`trigger` values (validator `warnings`) get flagged to the user, not silently skipped.
3. Apply `constraints`/`interactions` via `manage_physics`/scripted components as appropriate.
4. Prefer `batch_execute` for sets of related calls (e.g. all children of one parent) over many sequential single calls.

## Practices worth following (from the upstream repo's own conventions)

- Don't build premature abstractions -- three similar lines beat a helper used once; abstract at 3+ real use sites.
- When removing functionality, remove it fully -- no `_unused` renames, no "just in case" commented-out code.
- Each tool call should do one thing well; don't grow "convenient" parameters that bloat the API surface.

## qFoldIT-specific notes

- Unreal is the primary engine for "МАС «Снежинка»" today -- this skill is for if/when a Unity module appears (e.g. a lightweight/mobile prototype). Don't assume Unity is already in use without seeing `Assets/`+`ProjectSettings/` markers in the working directory.
- If a repo ever has both Unity and Unreal content, never mix `Assets/` (Unity) and `Content/` (Unreal) assets -- incompatible formats.
