# Physiological basis of the plant growth model

The model in `scripts/plant_model.py` is a **qualitative heuristic index calculator**, built on well-documented general plant physiology principles. It is NOT a species-specific calibrated model and does not replace agronomic expertise or real field/greenhouse trials. Below are the principles the model relies on, and their basis in the general plant physiology literature (not tied to a single paper — these are standard agronomy/botany fundamentals).

---

## 1. Liebig's Law of the Minimum

Plant growth is limited by whichever resource is scarcest relative to need — not by the sum of resources, but by the most deficient one. If nitrogen is sufficient but potassium is critically lacking, an excess of nitrogen does not compensate for the potassium shortfall.

**In the model:** `growth_limiting_factor = min(N_index, P_index, K_index)`.

## 2. Macronutrient deficiency symptoms (well-known, qualitative)

| Element | Typical deficiency symptoms | Typical excess symptoms |
|---|---|---|
| **N (nitrogen)** | Chlorosis of older (lower) leaves, slowed growth, thin stems | Excess vegetative mass, delayed flowering/fruiting, weakened tissue |
| **P (phosphorus)** | Slowed growth, dark green/purple leaves (anthocyanin accumulation), delayed maturity | Rarely presents overtly; can block micronutrient uptake (Zn, Fe) |
| **K (potassium)** | Necrosis/"scorch" of leaf edges, weak stems, lodging, reduced stress tolerance | Can block Mg, Ca uptake |

These are qualitative patterns widely described in the agronomic literature — the specific expression depends heavily on plant species, growth stage, and soil/substrate.

## 3. Effect of light: intensity (DLI)

**DLI (Daily Light Integral)** — the total amount of photosynthetically active radiation (PAR, 400-700 nm) received per day, mol/m²/day. Calculated as:

```
DLI = PPFD × photoperiod_hours × 3600 / 1,000,000
```

where PPFD is the instantaneous intensity (μmol/m²/s).

Growth generally increases with DLI up to a (species-specific) saturation point, beyond which further light gives diminishing returns and can cause photoinhibition (damage to the photosynthetic apparatus from excess light). The model uses a simplified saturating function with a default "optimal" DLI of ~20 mol/m²/day (a typical value for many greenhouse crops; should be adjusted for a specific species).

## 4. Effect of light: spectral composition

- **Red:far-red ratio (R:FR, ~660nm/730nm)** — a key photomorphogenesis signal via phytochromes. Low R:FR (typical of shade/dense plantings — far-red light passes through neighboring plants' leaves more readily than red) triggers the **shade avoidance syndrome**: elongated internodes, a stretched-out stem, reduced branching, a thinner stem. High R:FR produces compact, stocky growth. This is one of the most robustly reproduced patterns in plant photobiology.
- **Blue-light fraction (400-500 nm)** — associated with more compact growth, thicker leaves, and higher chlorophyll content per unit leaf area (overall, plants grown under a high blue-light fraction tend to be stockier and "denser").
- **UV and general light stress** — stimulate accumulation of flavonoid/anthocyanin-group secondary metabolites (protective pigmentation against excess radiation) — a general, repeatedly confirmed effect in plant physiology.

## 5. Secondary metabolites (anthocyanins/flavonoids) — a qualitative index

The model computes a notional "stress secondary-metabolite index" as a function of:
- phosphorus deficiency (a classic trigger for anthocyanin accumulation),
- nitrogen deficiency (also linked to anthocyanin accumulation in many species),
- excess/UV-enriched light.

This is a **qualitative index, not calibrated to any specific species** — intended to demonstrate the direction of the effect ("under these conditions, more pronounced stress pigmentation is expected"), not to precisely forecast the concentration of a specific metabolite.

---

## How this is used in the model

All the principles above are translated into simple, transparent formulas in `plant_model.py` (the code can be opened and read — no "black box"). The resulting indices (0-100, or multipliers) are used for:
1. A text report to the user on growth status/deficiencies.
2. Optional generation of parameters for the `qfoldit-l-systems` skill (step/internode length, "stockiness" via preset choice, green/purple tint by stress index) — to visualize the morphological effect of growing conditions on a procedurally generated plant.

## Mandatory caveat

Any specific numbers the model outputs (percentages, 0-100 indices) are **illustrative, qualitatively-grounded estimates**, not the result of training on real agronomic data. Real greenhouse/industrial application (including for the "virtual lab" module at the MAS "Snezhinka") requires calibration against data for specific plant species and specific equipment (LED panel spectrum, nutrient solution composition).
