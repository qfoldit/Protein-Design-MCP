---
name: openusd-architect
description: Exports a validated Universal Assembly Graph (UAG, from game-designer/digital-twin-builder) to OpenUSD/NVIDIA Omniverse, using the official NVIDIA-Omniverse/kit-usd-agents MCP servers (USD Code, Kit, OmniUI) and/or NVIDIA Skills. Use this skill when the user wants a qFoldIT UAG realized as a USD stage/Omniverse scene, or asks about USD prims, Kit extensions, or Omniverse digital-twin/industrial-visualization workflows.
---

# openusd-architect

**Status: official.** Built on `NVIDIA-Omniverse/kit-usd-agents`, published directly by the NVIDIA-Omniverse GitHub organization.

## Available official tooling

- **USD Code MCP** -- 7 specialized tools for USD/OpenUSD API help: `list_usd_modules`, `list_usd_classes`, `get_usd_module_detail`, `get_usd_class_detail`, `get_usd_method_detail`, `search_usd_code_examples` (a 7th tool exists per the docs but wasn't confirmed by name -- check `source/mcp/usd_code_mcp/README.md`). Same principle as `unigine-simulation-engineer`: use these to verify USD API signatures rather than guessing, the API surface is large and easy to misremember.
- **Kit MCP** / **OmniUI MCP** -- extension and UI-framework work.
- **Chat USD** -- runs inside Omniverse Kit itself for natural-language scene interaction (not a standalone MCP server).
- **NVIDIA Skills** (alternative to running the full MCP Docker stack): Omniverse RTX SDK, USD physics simulation, Kit development assistant, USD/OpenUSD development assistant, OmniUI development assistant -- also distributed via the Claude Code marketplace and Vercel Skill Marketplace (Physical AI section). Simpler to install than the full server stack if only reference info (not live execution) is needed.

## UAG -> USD mapping

Baseline from `game-designer/references/uag_schema.md`: `node` -> USD prim under an `Xform`, `type: mesh` -> geometry prim (e.g. `UsdGeomMesh`), `type: light` -> `UsdLuxLight` subtype, `parent_child` -> SdfPath hierarchy, `physics_collision` -> UsdPhysics schema.

## Local setup (if live MCP execution is needed, not just reference)

```bash
export NVIDIA_API_KEY=...   # required
export NGC_API_KEY=...      # only if pulling NIM containers for fully local models
cd source/mcp && ./build-wheels.sh all
docker compose -f docker-compose.local.yaml up --build   # cloud embed/rerank endpoints, faster start
# or: docker-compose.ngc.yaml for fully local NIM models (needs 1-2 NVIDIA GPUs)
```
Health checks: `curl localhost:8001/v1/health` (embedder), `:8002/v1/health` (reranker), `:9903/health` (USD Code MCP itself).

## qFoldIT-specific notes

- Natural fit for the molecular/quantum track (VQE, RosettaFold3/BioNeMo outputs) as well as industrial digital twins (`mining`, `oilgas`) -- not only game-style scenes.
- The NIM (fully local) path needs an NVIDIA GPU; if the team doesn't have GPU infrastructure, start with the cloud-endpoint compose file, not NIM.
- Using this official open repository is not, by itself, a partnership with NVIDIA -- don't describe it as one in external materials (same rule applied to other engine integrations in this plugin).
- For robotics/physical simulation specifically, NVIDIA also has Isaac Sim tooling referenced on their developer forums -- status as a first-class `NVIDIA-Omniverse` org repo (vs. a community wrapper around an official announcement) was not verified in this session; check the org's repo list before depending on it.
