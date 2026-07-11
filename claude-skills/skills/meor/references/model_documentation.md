# Model Reference: qfoldit-meor (Microbial Enhanced Oil Recovery)

## 1. Pipeline and equations

| Stage | Equation | Basis |
|---|---|---|
| Microbial growth | Monod: mu(S) = mu_max*S/(Ks+S); batch dX/dt=mu*X, dS/dt=-mu*X/Y_xs | Monod (1949) |
| Biosurfactant production | Luedeking-Piret: dP/dt = alpha*dX/dt + beta*X | Luedeking & Piret (1959) |
| IFT reduction | Hill-type: sigma(P) = sigma_min + (sigma0-sigma_min)/(1+(P/P50)^n) | Standard surfactant saturation-curve shape |
| Capillary number | Nc = v*mu_oil/sigma | Standard EOR definition |
| Residual oil saturation | Capillary desaturation curve (CDC), sigmoid in log10(Nc) | Chatzis & Morrow-type correlations, standard EOR literature (e.g. Lake, "Enhanced Oil Recovery") |
| Incremental recovery | (Sor_baseline(t=0) - Sor(t)) / Sor_baseline(t=0) | -- |

### Key functions
- `batch_growth_curve`, `luedeking_piret_product`, `ift_from_biosurfactant`,
  `capillary_number`, `residual_oil_saturation`, `predict_meor_recovery`
  (full pipeline), `fit_ift_hill_params` (nonlinear least-squares
  calibration of the IFT-biosurfactant relationship from real assay data).

## 2. A real bug found and fixed during development

**Symptom**: an early version reported significant incremental oil
recovery (~15-30% of remaining oil) already at day 0, before any
biosurfactant had been produced.

**Root cause**: "incremental recovery" was computed relative to
`Sor_low_Nc`, an idealized textbook parameter representing the residual
saturation at Nc -> 0. But the scenario's actual pre-treatment (P=0)
capillary number was not infinitesimally small -- it was already close
enough to `Nc_critical` that the capillary desaturation curve predicted
some mobilization even without any biosurfactant. Comparing against the
idealized asymptote instead of the scenario's own actual baseline
overstated the MEOR-attributable effect.

**Fix**: `predict_meor_recovery` now computes the baseline Sor by
evaluating the model at P=0 (using the scenario's own velocity,
viscosity, and sigma0) and uses THAT as the reference point for
incremental recovery, unless the user explicitly supplies a different
baseline. After the fix, a re-run of the same test scenario correctly
showed 0.00% incremental recovery at day 0, rising smoothly as
biosurfactant accumulated (0.05% at day 20, 1.30% at day 60 in the
default test scenario).

**Why this matters for how you use this skill**: any specific reservoir
scenario has its own actual pre-treatment capillary number, which may
already sit closer to or farther from the critical mobilization
threshold than a generic textbook value assumes. Always let the model
compute its own P=0 baseline rather than hardcoding a reference Sor,
unless you have an independently measured pre-treatment Sor for that
specific reservoir (in which case, use that real measured value).

## 3. Validation performed

- Growth curve: biomass increases monotonically to a plateau, substrate
  depletes monotonically to near-zero -- confirmed.
- Biosurfactant: accumulates monotonically (Luedeking-Piret is
  non-negative by construction with realistic alpha/beta) -- confirmed.
- IFT: decreases monotonically from sigma0 toward sigma_min as
  biosurfactant increases, following the expected Hill saturation shape
  -- confirmed (e.g. sigma0=30 -> 15.25 at P=P50=50 -> 0.79 at P=500).
- Capillary number: increases monotonically as IFT decreases (inverse
  relationship, confirmed at fixed velocity/viscosity).
- Capillary desaturation curve: Sor falls from near Sor_low_Nc at low Nc
  toward Sor_high_Nc at high Nc, transitioning around Nc_critical --
  confirmed.
- **Hill-parameter fitting accuracy**: initial linearized-logit fit was
  found to be biased under realistic noise (recovered P50=59.4 vs true
  50.0, hill_n=3.77 vs true 2.0 -- roughly 20% and 90% error
  respectively). Replaced with nonlinear least squares (scipy
  `curve_fit`) directly on the Hill equation, which recovered P50=47.5
  and hill_n=2.08 from the same noisy synthetic data -- both within
  ~5-10% of the true values. **Use the current `fit_ift_hill_params`
  function; do not revert to a linearized approach.**

## 4. Calibration status

All growth kinetics (mu_max, Ks, Y_xs), Luedeking-Piret coefficients
(alpha, beta), and CDC parameters (Nc_critical, Sor_high_Nc, Sor_low_Nc,
lambda_exp) currently use **generic, literature-order-of-magnitude
defaults**. None are fitted to any specific qFoldIT reservoir, core-flood
experiment, or field pilot. `fit_ift_hill_params` is available and
validated for calibrating the IFT-biosurfactant relationship once real
tensiometer assay data exists; analogous fitting for the growth and CDC
parameters would need real batch-culture and core-flood data
respectively, and is not yet implemented as separate calibration
functions.
