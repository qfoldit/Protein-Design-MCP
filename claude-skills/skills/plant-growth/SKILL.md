---
name: qfoldit-plant-growth
description: Estimates plant growth rate, morphology (internode length, branching density, compactness), deficiency symptoms, and secondary-metabolite stress indices from nutrient levels (NPK) and light conditions (intensity/PPFD, photoperiod, spectral composition — red/blue/far-red/UV fractions). Use this skill whenever the user asks about plant nutrition, NPK deficiency/excess effects, light spectrum effects on plant growth, DLI (daily light integral), shade avoidance / R:FR ratio effects, grow-light setup for plants, or wants to model/visualize how growing conditions affect plant shape and secondary metabolites. Can output parameters to feed into the qfoldit-l-systems skill to visualize the resulting morphology as a procedurally generated plant.
---

# Plant Growth Model (NPK + light spectrum → morphology & metabolites)

## What this skill does

A qualitative heuristic model that, from nitrogen/phosphorus/potassium (NPK) levels and lighting parameters (intensity, photoperiod, spectral composition), computes:
- a growth-rate index (Liebig's law of the minimum — limited by the scarcest resource),
- morphological effects (internode length, branching density, compactness — based on the shade-avoidance syndrome via the R:FR ratio and blue-light fraction),
- qualitative deficiency/excess symptoms for macronutrients,
- a stress-related secondary-metabolite index (anthocyanins/flavonoids).

**This is NOT an ML model calibrated on real data.** These are transparent, explainable formulas based on well-known plant physiology principles — see `references/plant_physiology_basis.md` for a full explanation of each relationship. Always present the result as a qualitative/illustrative estimate, not a precise agronomic forecast.

## When to use

- Questions about NPK plant nutrition, fertilizer deficiency/excess.
- Questions about the effect of light spectrum/intensity on growth (grow lights, LED spectrum, DLI, R:FR, shade-avoidance syndrome).
- A request to model/visualize how growing conditions will affect plant shape.
- Context — a "virtual lab"/greenhouse in a game/VR demo, where you need to show the effect of environmental parameters on a plant.

## How to work

1. Gather the input parameters: N/P/K (in ppm or relative units — if the user doesn't know exact figures, help translate a description like "low nitrogen" into approximate relative levels, explicitly flagging this as an assumption), PPFD and photoperiod (or total DLI directly), and the red/blue/far-red/UV fractions of the spectrum.
2. If the user doesn't know some parameters — use the script's sensible defaults (see `--help`) and explicitly state which defaults were applied.
3. Run `scripts/plant_model.py`, read the result.
4. Explain the result to the user in plain language: what the limiting factor is, what symptoms to expect, what the secondary-metabolite index means — using the wording from `references/plant_physiology_basis.md`.
5. If the user is also using the **"qfoldit-l-systems" skill** (or asks for a visualization) — add the `--emit-lsystem-params` flag and pass the resulting `preset`/`angle`/`iterations`/`step` into `qfoldit-l-systems/scripts/lsystem.py` to generate an SVG reflecting the computed morphology. Mention that the suggested color (`note_stroke_color`) needs to be passed manually — lsystem.py doesn't yet support color directly via the CLI.
6. Always end with a reminder: this is an illustrative model; real-world application (a specific greenhouse, specific plant species) requires calibration against real data from that specific installation and species.

## Example call

```bash
python3 scripts/plant_model.py \
  --n 150 --p 50 --k 60 \
  --ppfd 150 --photoperiod 12 \
  --red-frac 0.3 --blue-frac 0.1 --far-red-frac 0.25 \
  --emit-lsystem-params
```

## Limitations

- The default "optimal" NPK and DLI levels are general rough reference points, not for a specific species. For a real plant they should be set via `--n-optimal`/`--p-optimal`/`--k-optimal`/`--dli-optimal`.
- The model does not account for micronutrients (Fe, Mg, Ca, Zn, etc.), substrate/solution pH, temperature, humidity, or CO2 — all factors that strongly affect real-world growth.
- The secondary-metabolite index is qualitative (0-100), not tied to a specific compound or concentration unit.
