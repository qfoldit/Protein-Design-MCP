---
name: digital-twin-builder
description: Enriches a Universal Assembly Graph (UAG, produced by the game-designer skill) with simulation-grade semantics -- physical units, material/mass properties, and physics/logic constraints -- so it is ready for a physically meaningful digital twin, not just a visual scene. Use this skill whenever the user wants a UAG to actually behave correctly in a physics/simulation context (e.g. "make sure this greenhouse UAG has correct mass and collision for Unigine physics validation"), as an intermediate step between game-designer and an engine-adapter skill, or when they explicitly ask about "digital twin" fidelity/accuracy.
---

# digital-twin-builder

## Purpose

A raw UAG from `game-designer` describes WHAT is in a scene and WHERE. It does not necessarily carry the physical semantics needed for a scene to behave correctly as a **digital twin** (a simulation that should mirror real physical/biological behavior, not just look plausible). This skill fills that gap: it adds units, material/mass/physical properties, and validates that constraints are physically coherent, before the graph goes to an engine adapter.

## What "digital-twin-ready" means concretely

1. **Units are explicit.** Every numeric property that has physical meaning (position, mass, temperature, concentration) must carry an explicit unit in `properties` (e.g. `"mass_kg": 2.4`, not a bare `"mass": 2.4`). If the incoming UAG has bare numbers, ask the user for the intended unit rather than guessing -- guessing units is a common, costly source of simulation bugs (see Mars Climate Orbiter-class failures from unit mismatches -- a cautionary example, not a joke).
2. **Material/physical properties are attached where relevant.** Nodes of `type: mesh` intended to participate in physics need at minimum: mass, friction/restitution (if colliding), and for anything meant to model a real process (e.g. a plant from `plant-growth`, an ore sample from `mining`) -- a `source_context` back-reference to the science skill and inputs that produced its properties, so the twin can be re-run/audited later.
3. **Constraints are physically coherent.** E.g. a `physics_collision` constraint on two overlapping-at-rest nodes with no exception configured will produce simulation blow-up in most physics engines -- flag this instead of passing it through silently.
4. **No fabricated precision.** If the incoming science-skill data was a qualitative index (e.g. `plant-growth`'s `growth_rate_index_0_100`) rather than a calibrated physical quantity, do NOT silently convert it into a fake-precise physical unit (e.g. don't invent "this plant has calculated mass 340.2g" from a 0-100 index). Carry the qualitative index through as-is and let the engine adapter/visual layer decide how to represent it (e.g. scale, color) -- see each science skill's own "known limitations" section before assuming its output is more precise than it is.

## Workflow

1. Take the UAG from `game-designer` (must already pass `game-designer/scripts/uag_validate.py` -- re-validate if unsure).
2. For each node needing physical semantics, add/confirm units and material properties per above.
3. For constraints, check physical coherence (see point 3 above) -- flag issues rather than silently accepting.
4. Re-run `uag_validate.py` (structure should not have changed, only `properties` content) to confirm nothing was broken while enriching.
5. Hand the enriched UAG to the appropriate engine-adapter skill (`unreal-world-builder`, `unity-experience-builder`, `unigine-simulation-engineer`, `openusd-architect`, `apple-spatial-designer`, or `threejs-web-designer`).

## Relationship to other qFoldIT skills

- Upstream: `game-designer` (produces the raw UAG).
- Downstream: any engine-adapter skill (consumes the enriched UAG).
- Cross-reference: qFoldIT science skills (`mining`, `plant-growth`, `oilgas`, etc.) are the correct source for any physically-grounded numbers -- this skill organizes/validates those numbers into UAG form, it does not generate new scientific claims itself.
