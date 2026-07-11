# [qFoldIT](https://qfoldit.github.io/claude/) Agent Skills Plugin

[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-standard-green)](https://agentskills.io)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

![](https://qfoldit.github.io/claude/claude_science.png)

# Included Agent Skills

qFoldIT Skills are modular AI capabilities. Each Skill contains: domain knowledge, workflows, validation rules, examples, and MCP integration points where relevant. Folder names below match exactly what's in `skills/` -- use them to install/reference a specific skill.

Repository: https://github.com/qfoldit/skills/

---

# Scientific AI Skills

## `skills/qfold` -- Quantum Molecular Folding
2D HP-lattice protein folding (Dill, 1985) with a QAOA-style circuit on Amazon Braket LocalSimulator, plus optional delegation to a full qFold MCP server when available.

## `skills/bionemo-agent-toolkit` -- Structure Prediction
Protein/complex structure prediction via AlphaFold2 (NVIDIA BioNeMo NIM) and AlphaFold3 (local Docker), plus DiffDock docking and MolMIM molecule generation. **A compatible client, not an official NVIDIA or Google DeepMind integration.**

## `skills/quantum` -- VQE Simulator
Classical statevector VQE simulator (numpy-only), validated against exact diagonalization and a real published H2/STO-3G benchmark (arXiv:2209.09564, matches -1.1373 Hartree to 4 decimal places).

---

# Bioindustrial & Environmental Skills

## `skills/mining` -- Bioprocesses in Mining
Bio-oxidation, biosorption (gold-cyanide/copper/REE/lithium), and cyanide biodegradation kinetics for metal recovery.

## `skills/prospecting` -- Microbial Ore Prospecting
Indicator-taxa statistics on microbial abundance data for biogeochemical mineral exploration.

## `skills/meor` -- Microbial Enhanced Oil Recovery
Bacterial growth, biosurfactant production, IFT reduction, and incremental oil recovery modeling.

## `skills/oilgas` -- CO2 Corrosion in Pipelines
Pipeline corrosion rate and remaining-wall-life estimation (de Waard-Milliams correlation).

---

# Biological Simulation Skills

## `skills/l-systems` -- L-System Fractals & Plants
Procedural plant/fractal generation (Koch, dragon, Sierpinski, branching plants) rendered as SVG.

## `skills/plant-growth` -- Plant Nutrition & Light Model
Growth rate, morphology, and secondary-metabolite indices from NPK nutrition and light spectrum -- qualitative/illustrative, not species-calibrated. Can feed `skills/l-systems` to visualize the resulting shape.

---

# Materials & Industrial Skills

## `skills/plastic-characterization` -- Plastic Pyrolysis Estimator
Pyrolysis oil/gas/char yield ranges and chlorine-contamination risk for mixed plastic feedstock.

---

# VR / Interactive Molecular Dynamics

## `skills/nanover` -- NanoVer VR Bridge
Bridges qFoldIT structures (from `qfold`/`bionemo-agent-toolkit`) into **NanoVer**, a real, independently published and maintained open-source framework (IRL2, Univ. of Santiago de Compostela; JOSS 2025, DOI 10.21105/joss.08118) for collaborative interactive molecular dynamics in VR. qFoldIT's role is a thin adapter only -- **NanoVer is not a qFoldIT invention; citing the source publications is required** whenever this skill's output is used. Requires a local conda install of `nanover-server`.

---

# Digital Twin & Engine Skills

These share one engine-neutral format -- the **Universal Assembly Graph (UAG)**, schema in `skills/game-designer/references/uag_schema.md`. `game-designer` produces a UAG; `digital-twin-builder` adds simulation-grade physical semantics; each engine skill below exports the (enriched) UAG to one target platform. Every engine skill validates against `skills/game-designer/scripts/uag_validate.py` before exporting -- and every skill states plainly whether its target integration is official or community-maintained.

| Skill folder | Target | Status |
|---|---|---|
| `skills/game-designer` | produces the UAG (engine-neutral) | qFoldIT-authored |
| `skills/digital-twin-builder` | enriches UAG with physical/simulation semantics | qFoldIT-authored |
| `skills/unreal-world-builder` | Unreal Engine | ✅ Official (Epic Games MCP plugin) |
| `skills/unity-experience-builder` | Unity | ⚠️ Community (CoplayDev/unity-mcp -- **not affiliated with Unity Technologies**) |
| `skills/unigine-simulation-engineer` | UNIGINE 2 / UNIGINE 2 Sim | ✅ Official pattern (unigine-engine/ai-docs), docs-grounded to avoid hallucinated API calls |
| `skills/openusd-architect` | OpenUSD / NVIDIA Omniverse | ✅ Official (NVIDIA-Omniverse/kit-usd-agents) |
| `skills/apple-spatial-designer` | RealityKit / visionOS / USDZ | ✅ Official Xcode<->Claude Agent SDK integration; RealityKit specifics from public docs + community skills, not one single authoritative source |
| `skills/threejs-web-designer` | Three.js / React Three Fiber / WebXR | Community ecosystem; no single official skill exists for this stack |

---

## Links

- [qFoldIT](https://qfoldit.github.io/claude/)
- [Agent Skills specification](https://agentskills.io)
- [Claude Code documentation](https://docs.claude.com/en/docs/claude-code)

---

*Built with curiosity by the qFoldIT community.*
