# Plant Growth Model — Skill for Claude

A qualitative model of how nutrition (NPK) and light (intensity, spectrum) affect plant growth, morphology, and secondary metabolites. Optionally integrates with the **qfoldit-l-systems** skill to visualize the result as a procedural plant.

---

## What this is and isn't

**This is:** a transparent, explainable calculator based on well-known plant physiology principles — Liebig's law of the minimum, DLI light-saturation of growth, the shade-avoidance syndrome (R:FR), qualitative macronutrient deficiency symptoms, and the direction of the effect on secondary metabolites. All the formula code is readable in `scripts/plant_model.py` — no "black box."

**This is NOT:** an ML model calibrated on real agronomic/greenhouse data. It does not replace real measurements, laboratory plant tissue analysis, or consulting an agronomist. The default "optimal" NPK/DLI levels are general reference points, not values for a specific plant species.

Full explanation of the physiological logic is in `references/plant_physiology_basis.md`.

---

## Structure

```
plant-growth-model/
├── README.md                          — this file
├── SKILL.md                           — instructions for Claude
├── references/
│   └── plant_physiology_basis.md      — explanation of each relationship + general literature source
└── scripts/
    └── plant_model.py                 — calculation script (Python 3, no external dependencies)
```

---

## Quick start

```bash
python3 scripts/plant_model.py \
  --n 150 --p 50 --k 200 \
  --ppfd 400 --photoperiod 16 \
  --red-frac 0.45 --blue-frac 0.25 --far-red-frac 0.03
```

### Parameters

| Flag | Description | Default |
|---|---|---|
| `--n`, `--p`, `--k` | Current N/P/K levels, ppm (required) | — |
| `--n-optimal`, `--p-optimal`, `--k-optimal` | "Optimal" levels for comparison | 150 / 50 / 200 (rough reference points) |
| `--ppfd` | Light intensity, μmol/m²/s (required) | — |
| `--photoperiod` | Hours of light per day (required) | — |
| `--red-frac`, `--blue-frac`, `--far-red-frac`, `--uv-frac` | Spectrum fractions (0-1) | 0.4 / 0.2 / 0.05 / 0.0 |
| `--dli-optimal` | Optimal DLI for the species, mol/m²/day | 20.0 |
| `--emit-lsystem-params` | Additionally output parameters for integration with qfoldit-l-systems | off |

### Example output (abbreviated)

```json
{
  "nutrient_indices": {"N": 1.0, "P": 1.0, "K": 0.3},
  "limiting_nutrient": "K",
  "dli_mol_m2_day": 6.48,
  "growth_rate_index_0_100": 9.7,
  "morphology": {
    "internode_length_multiplier": 0.94,
    "branching_density_multiplier": 1.0,
    "compactness_index_0_1": 0.2
  },
  "deficiency_symptoms": [
    "Potassium starvation: risk of necrosis/leaf-edge 'scorch', weak stems, lodging risk."
  ],
  "secondary_metabolite_stress_index_0_100": 0.0
}
```

---

## Integration with qfoldit-l-systems

With the `--emit-lsystem-params` flag, the script additionally outputs an `lsystem_integration` block — ready-to-use parameters (`preset`, `angle`, `iterations`, `step`) for `qfoldit-l-systems/scripts/lsystem.py`, to visualize the computed morphology as a procedural plant:

```bash
# 1. Compute the growth model
python3 plant-growth-model/scripts/plant_model.py --n 150 --p 50 --k 60 \
  --ppfd 150 --photoperiod 12 --red-frac 0.3 --blue-frac 0.1 --far-red-frac 0.25 \
  --emit-lsystem-params > result.json

# 2. Take suggested_lsystem_cli from result.json and run it (example):
python3 qfoldit-l-systems/scripts/lsystem.py --preset plant --angle 25.0 --iterations 3 --step 0.94 --out plant_result.svg
```

Mapping logic (simplified):
- **Step length (`step`)** ← `internode_length_multiplier` (shade/light deficiency → longer internodes).
- **Preset** (`plant`, elongated, vs. `bush`, compact) ← compactness index (blue-light fraction).
- **Iteration count** ← growth-rate index (weak growth → less developed structure).
- **Color (hint only, not automated)** — a purple tint at a high stress-metabolite index (symbolizing anthocyanins), needs to be passed manually into `segments_to_svg` in `lsystem.py`, since the CLI doesn't yet accept color as a parameter.

---

## Known limitations

- Does not account for micronutrients, pH, temperature, humidity, or CO2 — only NPK and light.
- The default "optimal" values are rough and not tied to a specific species — be sure to set `--*-optimal` for the real crop, if known.
- The secondary-metabolite index is qualitative (0-100), not tied to concentration units of a specific compound.
- Integration with qfoldit-l-systems produces only approximate, illustrative shape parameters — it does not replace a real botanical reference model for a specific species.

---

## How to validate before serious use

1. Take a known plant species with optimal NPK/DLI values documented in the agronomic literature — set them via `--*-optimal`/`--dli-optimal`.
2. Compare the model's qualitative output (symptoms, growth index) against real observations/literature data for that species under similar conditions.
3. If real growth data is accumulated for your installation (e.g. the MAS "Snezhinka" greenhouse) at various NPK/spectrum conditions — it would make sense to replace the heuristic formulas with a regression trained on that data, and explicitly label the version as calibrated.

---

## Status

Working base version (v0.1), tested on two contrasting scenarios (optimal conditions / potassium deficiency + insufficient light with low R:FR) — the model correctly identifies the limiting factor and logically changes the growth index and morphology. Not validated against real agronomic data.
