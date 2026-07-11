---
name: qfoldit-mining
description: Prediction and optimization of bio-oxidation (biooxidation) of refractory sulfide gold ore, biosorption-based metal recovery (gold-cyanide, copper, REE, lithium), and biological cyanide degradation in tailings/effluent, using validated kinetic models (Shrinking Core Model, Arrhenius, cardinal-temperature response, Langmuir/Freundlich isotherms, pseudo-second-order kinetics, Aiba substrate-inhibition kinetics). Use whenever the user asks about biooxidation, bioleaching, biosorption, cyanide biodegradation/detoxification, mining-bioox, mining-biosorption, mining-cyanide, gold/copper/lithium/REE recovery from ore or leach liquor, pH/temperature optimization for a bioreactor, tailings cyanide discharge compliance, or wants a recovery/uptake/degradation forecast for a mining process. Trigger even if the user just gives ore or effluent parameters (pH, temperature, particle size, concentration) without naming "biooxidation", "biosorption", or "cyanide degradation".
---

# qfoldit-mining

Kinetic modeling skill for three related processes in refractory ore
processing and effluent treatment:

1. **Bio-oxidation** (`bioox_kinetics.py`) -- microbial oxidation of
   sulfide minerals (arsenopyrite/pyrite) that locks up gold, freeing it
   for downstream leaching. Model: Shrinking Core Model (reaction-controlled)
   x Arrhenius x microbial cardinal-temperature response x pH response.
2. **Biosorption** (`biosorption_kinetics.py`) -- recovery of dissolved
   metal (gold-cyanide complex, copper, REE, lithium) onto biomass. Model:
   Langmuir/Freundlich equilibrium x pseudo-second-order kinetics x
   pH-dependent activity (mechanism differs for cationic metals vs
   anionic complexes like Au(CN)2-).
3. **Cyanide biodegradation** (`cyanide_kinetics.py`) -- biological
   detoxification of free/WAD cyanide in tailings or mill effluent by
   cyanide-degrading bacteria. Model: Aiba substrate-inhibition kinetics
   (cyanide is BOTH the growth substrate and, at high concentration, toxic
   to the degrading culture -- rate is non-monotonic in concentration, not
   simple Monod).

**Read `references/model_documentation.md` before answering** -- it
contains the literature basis, all equations, calibration status, and
critical caveats (especially: default rate/capacity constants are
generic literature-range placeholders, NOT validated for any specific
qFoldIT ore or site, until fitted against real assay data).

## How to handle a request

1. **Identify which process** the user is asking about (bio-oxidation of
   ore, biosorption of dissolved metal, or cyanide degradation in
   effluent/tailings) and which metal/system, if biosorption
   (`gold_cyanide`, `copper_cationic`, `ree_trivalent`, `lithium_cationic`,
   or a custom parameter set).
2. **Validate inputs**: pH should be a plausible acidic bioleaching range
   (typically 0.5-6); temperature in a plausible mesophilic range
   (typically 10-50 C) -- flag values outside this as unusual and ask for
   confirmation rather than silently extrapolating. Particle size,
   concentration (Ce) must be positive. For cyanide degradation, flag
   concentrations above roughly 1000-1500 mg/L as entering a regime where
   the source study's fit is less certain (sparse literature data that
   high) -- see references.
3. **Run the model** via `scripts/bioox_kinetics.py`,
   `scripts/biosorption_kinetics.py`, or `scripts/cyanide_kinetics.py`
   (see references for function signatures and examples).
4. **Always report calibration status** alongside any numeric forecast:
   state plainly whether the constants used are the generic literature
   defaults or have been fitted to real data the user supplied. Never
   present a placeholder-calibrated forecast as a validated production
   guarantee.
5. **If the user has real assay/pilot data** (time-series conversion
   data, equilibrium isotherm data, kinetic uptake data, or rate-vs-
   concentration data for cyanide degradation), use `fit_A_from_data`,
   `fit_langmuir`, `fit_freundlich`, `fit_pseudo_second_order`, or
   `fit_aiba` to recalibrate before forecasting -- this is always
   preferable to the defaults.
6. **Reactor mode matters for bio-oxidation**: ask (or confirm) whether
   the reactor is continuous/mature-culture (e.g. BIOX-style CSTR train)
   or batch/fresh-inoculation (e.g. heap start-up) -- these give
   drastically different time-to-target-conversion.
7. **For cyanide degradation, never give an absolute treatment time
   (hours/days to reach a target residual concentration) without first
   flagging the X0 (starting biomass) caveat** -- the literature rate
   constants describe specific (per-unit-biomass) rates, and the
   translation to an absolute timeline is extremely sensitive to a
   biomass loading value this skill cannot supply on its own (verified:
   a 400x range of X0 changes a 300-hour outcome from "barely moved" to
   "cut by nearly half" using the same rate constants). Absolute
   `simulate_batch_treatment`/`time_to_target_residual` results should be
   presented as illustrating the SHAPE of the response, not a commissioning
   timeline, unless the user has supplied a real measured biomass density.

## Interpreting results

- Conversion/uptake values are fractions (0-1) or percentages; always
  present with the day/time axis explicit.
- A forecast is a **modeled scenario under stated assumptions**, not a
  guaranteed recovery rate. Sensitivity to T and pH is often very large
  (see references/model_documentation.md, Section "Sensitivity example")
  -- small deviations from optimum can more than halve conversion at a
  given time, so operational control precision matters as much as the
  algorithm itself.
- For biosorption, always name the sorbate mechanism
  (cationic vs anionic_complex) in the explanation -- getting this wrong
  for gold-cyanide (an anionic complex) inverts the pH recommendation.
- For cyanide degradation, always report where the feed concentration
  sits relative to the optimal concentration S* = sqrt(Ks*Ki)
  (`optimal_concentration`) -- below S*, the lever is adding more
  cyanide-degrading capacity or less dilution; above S*, the lever is
  diluting/equalizing the feed, since more concentrated cyanide is
  actively poisoning the culture, not just "more work for it to do."
  Never present the plain Monod curve (`monod_specific_rate`) as
  applicable here -- it is included only to show how badly it diverges
  from the (toxicity-aware) Aiba model at high concentration.

## Testing

See `evals/eval_set.json` for representative test prompts and
`references/model_documentation.md` for validated qualitative behavior
checks (temperature/pH sensitivity shapes, isotherm asymptotes, fitting
recovery accuracy, cyanide non-monotonicity and Monod-vs-Aiba divergence)
that were run against this code before packaging.
