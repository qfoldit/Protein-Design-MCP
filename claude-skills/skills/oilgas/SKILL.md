---
name: qfoldit-oilgas
description: Prediction of internal CO2 (sweet) corrosion rate for oil & gas pipelines and estimation of remaining wall-life, using the published de Waard-Milliams correlation combined with protective-scale suppression, flow/mass-transfer enhancement, pitting risk from salinity, and corrosion-inhibitor effects. Use this skill whenever the user asks about pipeline corrosion, corrosion rate, remaining life / wall thickness / integrity of a pipeline, CO2 corrosion, sweet corrosion, inhibitor dosing effectiveness, or oilgas-corrosion. Trigger even if the user just gives conditions (temperature, CO2 pressure, flow velocity, salinity) without naming "corrosion" explicitly.
---

# qfoldit-oilgas (corrosion)

Kinetic/empirical model for internal CO2 corrosion of carbon steel oil &
gas pipelines, built on the published de Waard-Milliams correlation plus
three well-documented secondary effects: protective FeCO3 scale
suppression at higher temperature, flow-driven mass-transfer enhancement
(with an erosion-corrosion regime at high velocity), and a chloride/
salinity-driven pitting risk indicator.

**Read `references/model_documentation.md` before answering** -- it has
the full equations, the model's valid range, calibration status, and
critical caveats (the base correlation and secondary-effect parameters
are generic literature values, not fitted to any specific qFoldIT
pipeline/field until real coupon/ER-probe/field data is supplied).

## How to handle a request

1. **Gather inputs**: temperature (C), CO2 partial pressure (bar) --
   estimate from total pressure x CO2 mole fraction if not given directly
   -- flow velocity (m/s), salinity (ppt, default seawater ~35 if
   offshore/produced-water context implies it), and whether a corrosion
   inhibitor is in use (and its claimed efficiency, typically 80-95% if
   properly maintained -- ask rather than assume if not stated).
2. **Validate ranges**: the de Waard-Milliams correlation's empirical
   basis is roughly T=5-150C, pCO2=0.1-10 bar. Flag extrapolation outside
   this rather than presenting it with the same confidence.
3. **Run `scripts/corrosion_kinetics.py`**: `predict_corrosion_rate(...)`
   for the uniform corrosion rate + pitting risk factor;
   `remaining_life_years(...)` if wall thickness is known or asked about.
4. **Always separate uniform corrosion rate from pitting risk** -- they
   are different corrosion modes (general metal loss vs. localized
   perforation risk) and should never be combined into one number or
   implied to be interchangeable.
5. **State calibration status** with any numeric forecast: the base
   correlation is a widely-used published one, but the scale-suppression
   and flow-enhancement terms are simplified approximations calibrated to
   generic literature shapes, not to any specific pipeline. If the user
   has field/coupon corrosion data, use `fit_dewaard_offset_from_data` to
   calibrate a site-specific correction factor before forecasting.
6. **Remaining-life estimates assume a constant rate** -- flag this
   explicitly; real field conditions (water cut, temperature, inhibitor
   availability) change over time, so this is a first-order screening
   number, not a substitute for an inspection program.
7. **The flow/mass-transfer factor here is a deliberately simplified
   proxy**, not a reproduction of the full de Waard 1995 Sherwood-type
   mass-transfer equation (which needs diffusion coefficient, viscosity,
   and hydraulic diameter -- inputs this skill doesn't collect). It
   captures the same two qualitative behaviors (mass-transfer-limited at
   low velocity, erosion-corrosion above an erosional threshold) but
   should not be presented as numerically equivalent to the full
   published model. Say so if asked how this compares to NORSOK M-506 or
   the full de Waard 1995 equation.

## Interpreting results

- Corrosion rate in mm/year; remaining life in years given wall thickness
  and corrosion allowance.
- Non-monotonic temperature behavior is expected and correct: rate
  typically rises with T, peaks somewhere in the ~70-90C region in this
  model, then falls as protective scale becomes more effective -- do not
  "correct" this as if it were an error.
- Large sensitivity to inhibitor efficiency and flow control is expected
  and should be highlighted -- it's often the actionable lever, more than
  the base chemistry.

## Testing

See `evals/eval_set.json` and `references/model_documentation.md` for the
validated qualitative behavior checks performed before packaging (known
reference-point sanity check, non-monotonic temperature peak, flow
saturation + erosion regime, pitting factor monotonicity, inhibitor
proportionality, calibration-fit accuracy).
