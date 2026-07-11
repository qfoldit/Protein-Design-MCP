# qFoldIT Oil & Gas Skill — Microbial Enhanced Oil Recovery (MEOR)

Claude Desktop Skill wrapping a validated MEOR model: microbial growth →
biosurfactant production → interfacial tension reduction → incremental
oil recovery.

## What's inside

```
qfoldit-meor/
├── SKILL.md                          — triggers, instructions, documented pitfall
├── README.md                         — this file
├── scripts/
│   └── meor_kinetics.py              — full growth-to-recovery pipeline
├── references/
│   └── model_documentation.md        — equations, sources, bug writeup, validation
└── evals/
    └── eval_set.json                 — test prompts
```

## Scientific basis

Four chained, published mechanisms:
1. **Monod (1949)** substrate-limited microbial growth.
2. **Luedeking & Piret (1959)** growth-associated + non-growth-associated
   biosurfactant production kinetics.
3. **Hill-type saturating IFT reduction** with biosurfactant concentration
   — consistent with general surfactant physical chemistry (sharp drop
   toward a critical micelle concentration, then plateau).
4. **Capillary desaturation curve (CDC)** — the standard petroleum
   engineering relationship (Chatzis & Morrow-type correlations, as
   presented in standard EOR references) linking capillary number
   Nc = velocity·viscosity/IFT to residual oil saturation: raising Nc
   past a critical threshold mobilizes oil that a plain waterflood
   leaves behind.

## A real bug found during development — worth reading

An early version of this model reported **~15-30% incremental oil
recovery already at day 0**, before any biosurfactant had been produced.
That's obviously wrong, and here's exactly why it happened: the model
was comparing predicted residual oil saturation against an idealized
textbook reference point (the saturation at capillary number → 0),
rather than against the specific scenario's **actual pre-treatment**
saturation. Because the test scenario's baseline (pre-MEOR) capillary
number wasn't infinitesimally small, the capillary desaturation curve
already predicted some oil mobilization from ordinary flow conditions
alone — and the model was crediting that to MEOR.

**Fix:** incremental recovery is now always computed relative to the
scenario's own computed baseline at zero biosurfactant (day 0), not a
generic textbook constant. Re-tested: the corrected model now shows
0.00% incremental recovery at day 0, rising smoothly as biosurfactant
accumulates.

This is exactly the kind of error that's easy to miss if you only skim
the final number — a plausible-looking 15-30% "MEOR benefit" is the kind
of figure that could easily end up in a pitch deck. Catching it required
actually checking day-0 behavior against the physically obvious
expectation (zero treatment → zero treatment effect), not just checking
that later-time numbers looked reasonable.

## Calibration status — read this before quoting any number externally

**Not calibrated to any qFoldIT reservoir, core-flood experiment, or
field pilot.** Growth kinetics (μmax, Ks, yield), Luedeking-Piret
coefficients (α, β), and CDC parameters (Nc_critical, Sor bounds) are
generic, literature-order-of-magnitude defaults.

`fit_ift_hill_params` calibrates the IFT-biosurfactant relationship from
real tensiometer assay data — and this function itself went through a
correction: an initial linearized fit was measurably biased under
realistic noise (recovered hill_n off by ~90%); replaced with direct
nonlinear least squares, now accurate to ~5-10% on the same test data.
Growth-kinetics and CDC-parameter calibration functions analogous to
this would need real batch-culture and core-flood data respectively, and
aren't implemented yet.

## Efficiency forecast — modeled scenario, not a guarantee

### Incremental recovery vs. strain/biosurfactant productivity
*(90-day treatment, same reservoir flow conditions, varying only biosurfactant production rate)*

| Scenario | α (growth-assoc.) | β (non-growth-assoc.) | Incremental recovery (fraction of remaining oil, day 90) |
|---|---|---|---|
| Weak-producing strain | 1.0 | 0.02 | 0.21% |
| Moderate strain | 3.0 | 0.08 | 2.34% |
| Optimized/high-producing strain | 6.0 | 0.15 | 6.44% |

**Reading this correctly:** the ~30x spread between weak and optimized
strains illustrates a real, well-documented lever in MEOR — biosurfactant
productivity matters enormously — but these are all **generic-parameter
model outputs**, not measurements from any actual qFoldIT reservoir or
strain. Published MEOR field trials report a wide range of outcomes
(commonly cited as roughly single-digit to low-double-digit percent of
OOIP in various field pilots), and this model's numbers are expressed as
a fraction of *remaining* oil after waterflood, not OOIP directly —
converting between the two requires reservoir-specific waterflood-Sor
data this model doesn't assume generically.

### What would turn this into a defensible efficiency claim

1. Real batch-culture data (growth curves, substrate consumption) for
   the actual candidate strain(s) — to calibrate μmax, Ks, Y_xs.
2. Real tensiometer assay data (biosurfactant concentration vs. measured
   IFT) — already supported via `fit_ift_hill_params`.
3. Real core-flood data (capillary number vs. measured residual oil
   saturation) for the target reservoir rock/fluid system — to calibrate
   Nc_critical, Sor_high_Nc, Sor_low_Nc, lambda_exp instead of using
   generic literature defaults.
4. Comparison of the calibrated model's prediction against a **measured**
   waterflood baseline for that same reservoir — not a generic asymptote
   (see the bug section above for why this specific mistake is easy to
   make).

Only after these steps does an incremental-recovery number represent
something defensible to present to a reservoir engineer, investor, or
partner — rather than a generic-parameter demonstration.

## Using this Skill in Claude Desktop

1. Copy the `qfoldit-meor/` folder into your Claude Desktop skills
   directory (or install via the `.skill` package if provided).
2. Ask Claude things like: *"Model MEOR at a flow velocity of 1e-6
   m/s, oil viscosity 0.01 Pa·s, over 90 days"* or supply real
   tensiometer data for calibration.
3. Claude will run the pipeline and, per the skill instructions, always
   report incremental recovery relative to the scenario's own baseline
   (not an idealized constant), state calibration status, and flag
   unrealistic input parameters.

## Testing performed so far

- Growth, biosurfactant production, IFT reduction, and capillary number
  all confirmed monotonic in the expected directions.
- Capillary desaturation curve confirmed to transition correctly around
  Nc_critical.
- The day-0 baseline bug (above) found, root-caused, and fixed —
  verified corrected behavior (0.00% incremental recovery at t=0).
- Hill-parameter fitting corrected from a biased linearized approach to
  validated nonlinear least squares.

**Not yet tested:** anything against real qFoldIT strain, core-flood, or
field pilot data — because none has been provided yet. That is the
natural next step before this skill is used to make claims to external
parties.
