---
name: unigine-simulation-engineer
description: Exports a validated Universal Assembly Graph (UAG, from game-designer/digital-twin-builder) toward UNIGINE 2 / UNIGINE 2 Sim, using docs-grounded verification (against unigine-engine/ai-docs) to avoid hallucinated API calls, plus the experimental official MCPBridge/DataBridge plugins where available. Use this skill when the user wants a qFoldIT UAG realized in UNIGINE, or asks about UNIGINE simulation/digital-twin/synthetic-environment workflows.
---

# unigine-simulation-engineer

**Status: official pattern, partially unverified in this session.** Based on the official `unigine-engine/ai-docs` GitHub organization (confirmed to exist) and official UNIGINE SDK 2.21 release notes (confirmed: AI-ready workflow, experimental MCPBridge Editor Plugin for text-prompt scene editing, DataBridge Plugin for external data/Python/ML connections). The exact current text of `unigine-engine/ai-docs/CLAUDE.md` was not re-verified line-by-line when this skill was last edited -- check the live repo before relying on specifics not stated here.

## Core principle: verify against docs, don't guess

UNIGINE is far less represented in general LLM training data than Unreal/Unity, so a plausible-sounding but nonexistent class/method name is a real risk here specifically. Before writing any UNIGINE API call:
1. If the project vendors `ai_docs/` (from `unigine-engine/ai-docs`), search it for the class/method first.
2. If not found, or `ai_docs/` isn't present, say so explicitly and suggest cloning `unigine-engine/ai-docs` or checking `https://developer.unigine.com/en/docs/latest` -- do not invent a signature that "should" exist.

## UAG -> UNIGINE mapping

Baseline from `game-designer/references/uag_schema.md` (mesh -> ObjectMeshStatic, light -> LightWorld/LightPoint, parent_child -> Node.setParent, physics_collision -> BodyRigid).

## Two paths to realize a UAG in UNIGINE

- **Live scene editing (experimental):** if the project has UNIGINE SDK 2.21+ with the **MCPBridge Editor Plugin** enabled, this is the closest UNIGINE equivalent to Unreal/Unity's live MCP control -- warn the user it's marked experimental by UNIGINE itself before using it in an important session.
- **Data-driven / digital-twin (DataBridge):** the **DataBridge Plugin** connects a UNIGINE scene to external systems (sensors, robotics, Python, ML pipelines) -- this is the more natural fit for qFoldIT's science-skill outputs (e.g. streaming `plant-growth` indices into scene parameters live) rather than one-shot scene construction. Untested hypothesis in this codebase -- validate on one simple case (e.g. `plant-growth` output) before relying on it architecturally.

## qFoldIT-specific notes

- Not the primary engine for any active qFoldIT module as of the last update to this skill (Unreal is primary for "МАС «Снежинка»"). This skill exists for industrial/simulation scenarios where UNIGINE's enterprise digital-twin templates are a better fit than a game engine (e.g. a `mining`/`oilgas` industrial digital twin).
- If the project adopts UNIGINE, clone the current `unigine-engine/ai-docs` into the repo rather than relying solely on this file, and re-verify the docs-grounding pattern above is still current practice.
