# qFoldIT Engine Integrations (index page)

qFoldIT uses an engine-neutral Digital Twin → Scene Plan architecture: it
provides scientific molecular data and scene plans, and lets specialized,
already-existing engine bridges perform the actual scene creation — it
does not duplicate engine functionality itself.

**This page is a short index, not the authoritative documentation.** Each
row below links to the maintained `skills/*/SKILL.md`, which has the real,
hedged details (what's verified, what's official vs. community, what's
NOT implemented) — read that file before making any specific claim.

| Platform | Bridge | Status | Authoritative doc |
|---|---|---|---|
| NVIDIA Omniverse | NVIDIA-Omniverse/kit-usd-agents | Official NVIDIA, API/doc-assistant pattern (not live scene control) | [`skills/openusd-architect/SKILL.md`](../skills/openusd-architect/SKILL.md) |
| Unreal Engine | EpicGames/unreal-engine-skills-for-claude-code-plugin, or community UnrealClaude | Official Epic Games plugin (live control) or community alternative | [`skills/unreal-world-builder/SKILL.md`](../skills/unreal-world-builder/SKILL.md) |
| Unity | CoplayDev/unity-mcp | Community MIT MCP bridge, NOT affiliated with Unity Technologies, but de-facto standard | [`skills/unity-experience-builder/SKILL.md`](../skills/unity-experience-builder/SKILL.md) |
| UNIGINE | Built-in MCPBridge Editor Plugin (official, live control) + unigine-engine/ai-docs (official, docs-grounding, not live control) | Two distinct official integrations, different patterns | [`skills/unigine-simulation-engineer/SKILL.md`](../skills/unigine-simulation-engineer/SKILL.md) |
| Apple (RealityKit/visionOS) | Xcode's Claude Agent SDK / MCP integration | See linked skill for current verified status | [`skills/apple-spatial-designer/SKILL.md`](../skills/apple-spatial-designer/SKILL.md) |
| Web (Three.js/WebXR) | No official bridge — community ecosystem | Browser-native, no install required | [`skills/threejs-web-designer/SKILL.md`](../skills/threejs-web-designer/SKILL.md) |
| NanoVer (interactive MD in VR) | qfoldit/nanover (mirror of IRL2/nanover-server-py) | Data-source direction (NanoVer → qFoldIT twin), not a scene-output target — see note below | [`skills/nanover/SKILL.md`](../skills/nanover/SKILL.md) |

## Why NanoVer isn't in the Digital Twin → Scene Plan table above

Every other row is a place qFoldIT sends a scene plan *to*. NanoVer is
the opposite: a source of real interactive-MD data that qFoldIT can pull
*from* and convert into its own digital-twin format — which then flows
into any of the rows above. qFoldIT does not push twins into a live
NanoVer simulation (that needs a real OpenMM topology/force-field qFoldIT
doesn't have) — see `skills/nanover/SKILL.md` for the honest scope.

## Design principle

qFoldIT's own code stays a thin, engine-independent scientific data layer.
When an official or de-facto-standard bridge already exists for a target
(unity-mcp, UnrealClaude/Epic's plugin, UNIGINE's MCPBridge,
kit-usd-agents, alphafold3_mcp), qFoldIT documents how to use it rather
than reimplementing it — see `CONTRIBUTING.md`.
