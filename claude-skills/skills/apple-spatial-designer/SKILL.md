---
name: apple-spatial-designer
description: Exports a validated Universal Assembly Graph (UAG, from game-designer/digital-twin-builder) toward RealityKit/visionOS/USDZ, using Xcode 26.3's official Claude Agent SDK / MCP integration where available. Use this skill when the user wants a qFoldIT UAG realized as a visionOS/RealityKit spatial experience, or asks about Vision Pro, USDZ export, or Apple spatial-computing workflows for a qFoldIT scene.
---

# apple-spatial-designer

**Status: mixed.** Apple/Anthropic announced official Xcode <-> Claude Agent SDK integration (Xcode 26.3+, via MCP, lets Claude Code capture visual Previews and interact with Xcode from the CLI) -- this part is official. There is, however, no single official "RealityKit skill" the way Unreal has one from Epic; visionOS/RealityKit-specific guidance here draws on the general, well-documented public APIs (RealityKit, ARKit hand tracking, USDZ) plus the existence of a healthy community-skill ecosystem (multiple independent visionOS/RealityKit Claude Code skills) rather than one authoritative source -- treat method-level specifics as needing verification against Apple's current documentation, not memorized as certain.

## Prerequisites

- Xcode 26.3+ for the official Claude Agent SDK / MCP integration (App Store Connect uploads require Xcode 26+ / iOS,visionOS 26 SDKs as of the 2026-04-28 deadline -- relevant if this ever ships).
- A visionOS target in the Xcode project for RealityKit/visionOS work specifically.

## Known hard boundary

**Agents (this skill included) cannot reliably edit `.pbxproj` files.** Adding new targets, frameworks, or files to the Xcode project structure needs a human to do it in Xcode, or a dedicated project-generation tool (e.g. XcodeGen/Tuist) -- don't attempt direct `.pbxproj` surgery and don't imply it "just works."

## UAG -> RealityKit mapping

Baseline from `game-designer/references/uag_schema.md`: `node` -> `Entity`, `type: mesh` -> `Entity` + `ModelComponent`, `type: light` -> `Entity` + `PointLight`/`DirectionalLight` component, `parent_child` -> `Entity.addChild`, `physics_collision` -> `CollisionComponent`, `on_grab` -> gesture recognizer / ARKit hand-tracking input.

## Workflow

1. Confirm the UAG passed `game-designer/scripts/uag_validate.py`.
2. For each node, generate the corresponding RealityKit Swift (Entity creation, component attachment) rather than hand-waving pseudo-code -- if a UAG `type`/`trigger` has no established mapping above, say so and ask rather than inventing a RealityKit API that may not exist.
3. If USDZ export/import is involved (UAG scenes originating from `openusd-architect`), note that RealityKit/visionOS consume USDZ as a packaged, compressed subset of USD -- not every USD feature round-trips; flag anything that looks like it needs manual verification in Reality Composer Pro.
4. For anything touching `.pbxproj` (new targets, capabilities), stop and tell the user this step needs to be done manually in Xcode.

## qFoldIT-specific notes

- Relevant primarily as a possible alternate/companion VR platform to Unreal for future work (e.g. a Vision Pro companion viewer for the "МАС «Снежинка»" demo) -- not in active use as of the last update to this skill.
- If picking a community visionOS skill to supplement this one, check its star count/last-updated date and verify its `SKILL.md` claims the same way this plugin verifies engine claims elsewhere -- don't assume a high install count means Apple-endorsed.
