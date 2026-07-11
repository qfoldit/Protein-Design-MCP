---
name: unreal-world-builder
description: Exports a validated Universal Assembly Graph (UAG, from game-designer/digital-twin-builder) into a live Unreal Engine scene, using the OFFICIAL Epic Games MCP plugin (EpicGames/unreal-engine-skills-for-claude-code-plugin). Use this skill when the user wants a qFoldIT UAG realized in Unreal Engine, or asks about Unreal actors/blueprints/materials/Niagara/Sequencer/UMG in the context of a qFoldIT scene (e.g. the "МАС Снежинка" VR demo).
---

# unreal-world-builder

**Status: official.** Built on `EpicGames/unreal-engine-skills-for-claude-code-plugin`, published by Epic Games directly.

## Prerequisites (do not skip)

1. Unreal Editor with BOTH plugins enabled: **ModelContextProtocol** AND **AllToolsets** (AllToolsets provides the tools -- without it the MCP server exposes none).
2. MCP server running: console command `ModelContextProtocol.StartServer` (or `bAutoStartServer`).
3. `bash` on PATH (macOS/Linux native; Windows needs Git Bash or WSL).
4. Generate client config from the editor console: `ModelContextProtocol.GenerateClientConfig ClaudeCode` (default `localhost:8000`, path `/mcp`).

## UAG -> Unreal mapping

Use `game-designer/references/uag_schema.md` mapping table as the baseline (mesh -> StaticMeshActor, light -> Point/DirectionalLight actor, parent_child -> Attach, physics_collision -> collision component/preset, on_grab -> Enhanced Input + Interaction Component). Before calling any tool, use the meta-tools `list_toolsets` -> `describe_toolset` -> `call_tool` (tool search is on by default) rather than guessing tool names from memory.

## Workflow

1. Confirm the UAG passed `game-designer/scripts/uag_validate.py` (re-run it if unsure -- do not export an unvalidated graph).
2. `list_toolsets` to see available domains (Actors/Scene, Blueprints, Materials, Niagara, UMG, Gameplay Ability System, Sequencer, etc.).
3. For each UAG node, map to the corresponding Unreal tool call per the table above; for `type`/`trigger` values with no established mapping (flagged as `warnings` by the validator), stop and ask the user how they want it represented rather than guessing.
4. For interactions (`on_grab`, `on_proximity`, etc.) needing custom logic beyond a direct tool call, prefer Blueprint tools over `execute_tool_script` unless Python is specifically required -- see security note below.

## Security (read before a live session)

- **localhost is not a trust boundary** -- any local process from the same user can connect. Don't run the MCP server on shared/untrusted machines or expose the port beyond loopback.
- **`ProgrammaticToolset.execute_tool_script` runs arbitrary Python inside the editor process** with full project/asset access -- treat every call as privileged, and prefer it only when no dedicated tool covers the need.
- **Don't run with `--dangerously-skip-permissions`** against a real project -- it removes per-tool confirmation. Use a disposable sandbox project instead if this mode is truly needed.
- **Commit or shelve in version control before a long MCP session** -- tools mutate live `UObject`s and can move/delete tracked assets in one call.

## qFoldIT-specific notes

- The current primary use case is the "МАС «Снежинка»" VR demo (virtual lab, greenhouse). For UAG scenes tagged with `source_context` from `plant-growth` or `mining`, expect mostly `Actors and Scene` / `Blueprints` / `UI` (UMG) / `VFX` (Niagara, for aurora/snow effects) toolsets.
- Any qFoldIT science-skill computation (e.g. re-running `plant-growth` for updated morphology) happens OUTSIDE Unreal, in Python, before re-exporting an updated UAG -- do not attempt to call qFoldIT Python skills from inside `execute_tool_script`; these are separate processes.
- `Content/` is binary -- confirm Git LFS is configured before bulk asset operations; if it's not set up, say so rather than proceeding silently.
