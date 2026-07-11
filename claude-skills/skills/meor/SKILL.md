---
name: qfoldit-meor
description: Prediction of Microbial Enhanced Oil Recovery (MEOR) outcomes -- bacterial growth, biosurfactant production, interfacial tension (IFT) reduction, and resulting incremental oil recovery via the capillary desaturation curve. Use this skill whenever the user asks about MEOR, microbial enhanced oil recovery, biosurfactant, interfacial tension reduction, capillary number/desaturation, incremental oil recovery from microbial treatment, or oilgas-meor. Trigger even if the user just gives reservoir/injection parameters (flow velocity, oil viscosity, nutrient/substrate concentration) without naming "MEOR" explicitly.
---

# qfoldit-meor (Microbial Enhanced Oil Recovery)

Kinetic + petrophysical model chaining four well-established mechanisms:
microbial growth (Monod) -> biosurfactant production (Luedeking-Piret)
-> interfacial tension reduction (Hill-type saturation) -> incremental
oil recovery via the capillary desaturation curve (CDC), the standard
petroleum-engineering relationship between capillary number and residual
oil saturation.

**Read `references/model_documentation.md` before answering** -- it has
the full equations, sources, a documented modeling pitfall found and
fixed during development (see below), and calibration status.

## Important: a documented pitfall (so you don't repeat it in reasoning)

During development, an early version of this model showed a large
**nonzero incremental recovery already at day 0**, before any
biosurfactant had been produced -- caused by comparing the model's Sor
against an idealized textbook asymptote (Sor at Nc->0) rather than
against the **actual pre-treatment Sor** implied by the scenario's own
baseline capillary number. This was a real bug, not just a caveat, and
was fixed: `predict_meor_recovery` now always computes "incremental
recovery" relative to the scenario's own P=0 (pre-treatment) baseline
Sor. If you build any independent recovery calculation on top of this
skill's outputs, use the same self-consistent baseline principle, not an
idealized reference constant.

## How to handle a request

1. **Gather inputs**: microbial growth parameters (mu_max, Ks, yield
   coefficient) if known, or use provided defaults with a clear caveat;
   injection/reservoir flow velocity, oil viscosity, baseline IFT
   (sigma0, typically ~20-30 mN/m without surfactant for crude
   oil-brine systems).
2. **Run the pipeline**: `predict_meor_recovery(...)` in
   `scripts/meor_kinetics.py` -- returns biomass, substrate, biosurfactant,
   IFT, capillary number, Sor, and incremental recovery fraction over time.
3. **Always report incremental recovery as a fraction of REMAINING oil
   after waterflood, not of OOIP directly** -- converting to a %OOIP
   figure requires knowing the waterflood-residual oil saturation as a
   fraction of OOIP for the specific reservoir, which this model doesn't
   assume generically.
4. **State calibration status**: growth kinetics, Luedeking-Piret
   coefficients, and CDC parameters (Nc_critical, Sor_high/low_Nc) are
   generic literature-consistent defaults, not fitted to any specific
   qFoldIT reservoir/core-flood data. If real core-flood or field pilot
   data exists, use `fit_ift_hill_params` (nonlinear least squares,
   validated to recover known parameters accurately) to calibrate the
   IFT-biosurfactant relationship; growth and CDC parameters would need
   analogous fitting once such data exists (not yet implemented as
   separate functions).
5. **Sanity-check self-consistency**: if a computed scenario shows
   substantial "incremental recovery" at t=0 or before meaningful
   biosurfactant has accumulated, that indicates a baseline/parameter
   inconsistency (see pitfall above) -- flag it rather than reporting it.

## Interpreting results

- IFT in mN/m; capillary number is dimensionless; Sor and incremental
  recovery are fractions (0-1).
- The capillary desaturation curve's critical capillary number
  (Nc_critical, default 1e-5) and the transition steepness (lambda_exp)
  are literature-order-of-magnitude defaults -- real reservoir rock/fluid
  systems vary, and this should be calibrated against core-flood data
  when available.
- Incremental recovery growing slowly then accelerating as biosurfactant
  accumulates past the IFT Hill-curve's P50 threshold is expected
  behavior, not an anomaly.

## Testing

See `evals/eval_set.json` and `references/model_documentation.md` for
validated qualitative behavior (monotonic growth/substrate depletion,
monotonic IFT reduction with saturation, monotonic Sor reduction with
Nc, the baseline-consistency fix, and Hill-parameter fit accuracy).
