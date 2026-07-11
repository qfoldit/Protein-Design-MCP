# qFoldIT Mining Skill — Bio-oxidation, Biosorption & Cyanide Degradation

Claude Desktop Skill wrapping validated kinetic models for three processes:
**bio-oxidation** of refractory sulfide gold ore, **biosorption** recovery
of dissolved metal (gold-cyanide, copper, REE, lithium) onto biomass, and
**biological cyanide degradation** in tailings/mill effluent.

## What's inside

```
qfoldit-mining/
├── SKILL.md                          — triggers & instructions for Claude
├── README.md                         — this file
├── scripts/
│   ├── bioox_kinetics.py             — bio-oxidation model
│   ├── biosorption_kinetics.py       — biosorption model + metal presets
│   └── cyanide_kinetics.py           — cyanide biodegradation model (Aiba)
├── references/
│   └── model_documentation.md        — full equations, sources, test results
└── evals/
    └── eval_set.json                 — 14 test prompts (bioox, biosorption, cyanide)
```

## Scientific basis (not proprietary black-box — every equation is named)

**Bio-oxidation:** Shrinking Core Model (Levenspiel) for particle conversion,
Arrhenius kinetics, Cardinal Temperature Model with Inflection (Rosso et
al. 1993) for the realistic bell-shaped microbial temperature response,
and an empirical pH activity curve consistent with published bioleaching
pH-optimum studies.

**Biosorption:** Langmuir/Freundlich equilibrium isotherms, pseudo-second-
order kinetics (Ho & McKay 1999), and a pH model that correctly
distinguishes **cationic metals** (favored at higher pH) from **anionic
metal complexes** like gold-cyanide (favored at lower pH — an opposite
mechanism, since it depends on amine protonation rather than carboxyl
deprotonation).

**Cyanide biodegradation:** Aiba substrate-inhibition kinetics (Aiba,
Shoda & Nagatani 1968) — the key property this captures that a plain
Monod model cannot: cyanide is both the growth substrate AND a toxin for
the bacteria that degrade it, so degradation rate is **non-monotonic** in
concentration (rises, peaks near S*=√(Ks·Ki), then collapses at high
concentration due to toxicity). Default parameters from a published batch
kinetic study of cyanide-degrading *Serratia marcescens*.

## Calibration status — read this before quoting any number externally

Every rate/capacity constant currently in the code (`A`, `Ea`, `qmax`,
`b`, `k2`, pH midpoints) is set to an **illustrative, literature-range
placeholder** — calibrated only against generic industry benchmarks (e.g.
commercial BIOX trains reaching ~90% conversion in ~5 days), not against
any qFoldIT ore sample, pilot run, or assay. This is by design at this
stage: the goal was to validate that the *model structure* behaves
correctly (right qualitative shapes, right asymptotes, fitting functions
that actually recover known parameters) before spending effort chasing
precision on numbers that will change anyway once real data comes in.

Every module includes a `fit_*` function (`fit_A_from_data`,
`fit_langmuir`, `fit_freundlich`, `fit_pseudo_second_order`, `fit_aiba`)
that recalibrates the model from real time-series/equilibrium/rate data
as soon as it exists. Recovery accuracy for these fitting functions was
verified at R² > 0.998 against synthetic noisy test data (R²=1.0 on clean
data for `fit_aiba`; noted separately that `fit_aiba` becomes less stable
under noise than the isotherm/Arrhenius fits — see model_documentation.md).

**Cyanide degradation has an additional, distinct calibration gap beyond
the rate constants**: `simulate_batch_treatment`/`time_to_target_residual`
need a starting biomass `X0` that this skill cannot supply — verified
that a 400x range of X0 swings a 300-hour outcome from "barely moved" to
"nearly halved." Absolute treatment-time forecasts for cyanide should
never be given without either real biomass data or an explicit,
clearly-labeled illustrative assumption — see SKILL.md point 7.

## Efficiency forecast — modeled scenario, not a guarantee

You asked for a projection of what these algorithms could mean for a
mining operation's recovery efficiency. Here is what the **current,
placeholder-calibrated model** predicts, shown as a sensitivity table
rather than a single headline number — because the honest answer depends
heavily on how tightly a real operation controls temperature and pH, and
on ore-specific rate constants that aren't fitted yet.

### Bio-oxidation: conversion vs. process control precision
*(continuous/mature-culture reactor, reaction-controlled regime)*

| Process control | T | pH | Conversion at day 5 | Conversion at day 10 |
|---|---|---|---|---|
| Tight optimum | 33°C | 1.8 | 90.0% | 100.0% |
| Your example params | 35°C | 1.8 | 93.8% | 100.0% |
| Moderate drift | 28°C | 2.3 | 58.9% | 88.5% |
| Poor control | 22°C | 3.0 | 8.7% | 16.9% |

**Reading this correctly:** the gap between "moderate drift" and "tight
optimum" (58.9% vs 90.0% at day 5) is *larger* than the gap the
architecture doc cites between traditional (60–65%) and BIOX-class
processes (95–98%). That's a meaningful signal, but it says more about
**how much process control discipline matters** than about a validated
qFoldIT-vs-industry delta — because the "traditional" comparator here is
a generic literature figure, not a measured baseline from a specific mine
your algorithms would replace.

### Biosorption: relative capacity by target metal
*(Ce = 50 mg/L, each system's modeled optimal pH, 180 min contact time)*

| System | Mechanism | Modeled equilibrium capacity (qe_eff) | Modeled uptake at 180 min |
|---|---|---|---|
| Gold-cyanide | anionic complex | ~40 mg/g | ~34 mg/g |
| Copper | cationic | ~15 mg/g | ~12 mg/g |
| REE (generic trivalent) | cationic | ~20 mg/g | ~16 mg/g |
| Lithium | cationic | ~1.3 mg/g | ~0.5 mg/g |

**Reading this correctly:** the ~30x gap between gold and lithium capacity
is not a modeling error — it reflects a real, well-documented chemistry
fact (Li+ is a poorly-complexed, hard ion that binds weakly to typical
biosorbent functional groups). If lithium recovery is commercially
important to qFoldIT, this table is a signal to validate biosorption
economics for Li+ specifically and early, rather than assuming the same
qmax/recovery story as gold or REE will transfer.

### Cyanide degradation: rate vs. feed concentration regime
*(Serratia marcescens AQ07 preset, degradation kinetics)*

| Feed concentration | Regime | Specific degradation rate |
|---|---|---|
| 10 mg/L | Substrate-limited | 0.00034 /h |
| 300 mg/L | Near-optimal (S*≈468 mg/L) | 0.00319 /h |
| 3,000 mg/L | Inhibition-limited (toxic) | 0.00001 /h |
| 10,000 mg/L | Severely inhibited | ~0.00000 /h |

**Reading this correctly:** this is not a smooth diminishing-returns curve
— it is genuinely non-monotonic, and the operational lever is *different*
on each side of the peak. Below S*, add more degrading capacity or reduce
dilution; above S*, dilute or equalize the feed, because more concentrated
cyanide is actively poisoning the culture, not just giving it "more work."
A plain Monod model would (wrongly) suggest 10,000 mg/L degrades almost as
fast as the model's ceiling — see model_documentation.md for the specific
divergence.

### What would turn this into a defensible efficiency claim

1. Real conversion-vs-time or equilibrium/kinetic assay data from an
   actual ore sample or pilot run.
2. Refit `A`/`Ea` (bio-oxidation) or `qmax`/`b`/`k2` (biosorption) to that
   data using the provided `fit_*` functions.
3. Compare the refit model's prediction against a **measured** traditional
   baseline for that same ore/site — not a generic literature number.

Only at that point does a "+X percentage points" or "$Y/tonne" figure
represent something you could put in front of investors, a mining
company, or a government body without it being a placeholder dressed up
as a result.

## Using this Skill in Claude Desktop

1. Copy the `qfoldit-mining/` folder into your Claude Desktop skills
   directory (or install via the `.skill` package if provided).
2. Ask Claude things like: *"Optimize bio-oxidation for gold ore,
   pH 1.8, temperature 35°C, particle size 20 μm"*, *"Forecast gold
   uptake from a cyanide solution at pH 2, concentration 50 mg/L"*, or
   *"We have 300 mg/L free cyanide in tailings — how fast will it
   biodegrade?"*
3. Claude will run the model, and — per the skill instructions — will
   always state whether the constants used are literature defaults or
   fitted to data you've supplied, and for cyanide specifically, will
   flag the separate starting-biomass (X0) caveat before giving any
   absolute treatment timeline.

## Testing performed so far

All qualitative behavior below was verified with test scripts before
packaging (see `references/model_documentation.md` for full detail):

- Bio-oxidation: temperature response peaks at T_opt and is zero outside
  the viable range (not naive-Arrhenius monotonic); pH response peaks at
  pH_opt; finer particles convert faster; continuous vs. batch reactor
  modes produce correctly different timescales.
- Biosorption: parameter-fitting functions recover known values with
  R² > 0.998; pH direction is confirmed opposite for anionic (gold-
  cyanide) vs. cationic (copper, REE, lithium) systems; Langmuir isotherm
  asymptotes correctly to qmax.
- Cyanide degradation: rate confirmed non-monotonic in concentration,
  peaking near S*=√(Ks·Ki); plain Monod confirmed to diverge sharply
  (wrongly) from the Aiba model at high concentration; `fit_aiba` exactly
  recovers known parameters on clean data, degrades gracefully-but-visibly
  under noise (disclosed, not hidden); absolute-timeline sensitivity to
  starting biomass (X0) explicitly quantified (400x X0 range → outcome
  swings from "barely moved" to "nearly halved" at fixed rate constants).

**Not yet tested:** anything against real qFoldIT ore, pilot, or plant
data — because none has been provided yet. That is the natural next step
before this skill is used to make claims to external parties.
