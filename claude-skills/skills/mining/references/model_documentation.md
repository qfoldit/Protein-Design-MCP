# Model Reference: qfoldit-mining

## 1. Bio-oxidation (`scripts/bioox_kinetics.py`)

### Equations
| Component | Equation | Basis |
|---|---|---|
| Arrhenius rate | k = A·exp(-Ea/RT) | standard chemical kinetics |
| Microbial T-response | Cardinal Temperature Model with Inflection (Rosso et al. 1993) | bell-shaped, T_min/T_opt/T_max |
| pH response | asymmetric Gaussian around pH_opt | typical bioleaching pH-activity curves |
| Conversion | Shrinking Core Model, reaction-controlled: 1-(1-X)^(1/3) = k·t/r0 | Levenspiel |
| Biomass ramp-up (batch mode) | logistic growth, μmax | standard microbial growth kinetics |

### Key functions
- `effective_rate_constant(T_c, pH, A, Ea_kJ_per_mol, T_min, T_opt, T_max, pH_opt, sigma_low, sigma_high)`
- `predict_recovery_curve(t_days, T_c, pH, particle_radius_um, reactor_mode, mu_max, X0_frac, **kwargs)` -- `reactor_mode="continuous"` (mature culture) or `"batch"` (fresh inoculation)
- `time_to_reach_conversion(X_target, k_eff, particle_radius_um, r0_ref_um)`
- `fit_A_from_data(t_days_data, X_data, T_c, pH, ...)` -- **use this as soon as you have real assay/pilot conversion-vs-time data**

### Calibration status
`A = 2.6e8` (pre-exponential factor) is calibrated so that **at T_opt=33C, pH_opt=1.8, continuous reactor mode**, the model reaches 90% conversion in ~5 days -- matching commercial BIOX-train retention-time benchmarks reported in industry literature. `Ea = 55 kJ/mol` is a mid-range literature value for reaction-controlled bio-oxidation.

**These are NOT fitted to any qFoldIT ore sample.** Treat every quantitative output as illustrative until `fit_A_from_data` has been run against real bottle-roll, column, or pilot conversion data for the specific ore body.

### Validated qualitative behavior (tests run during development)
- Temperature factor peaks at T_opt=33C, is exactly 0 outside [T_min, T_max] -- confirms the model does not (incorrectly) predict ever-increasing rate with temperature the way naive Arrhenius alone would.
- pH factor peaks at pH_opt=1.8, falls off asymmetrically.
- Finer particles (lower radius) reach a given conversion faster than coarser ones, as expected from surface-area scaling.
- Continuous-mode reaches 95%+ conversion in ~5-6 days; batch-mode with fresh 2% inoculum takes several weeks to reach the same conversion, purely due to population ramp-up -- this is a first-order operational distinction, not a modeling artifact.

### Sensitivity example (illustrates why control precision matters)
Continuous reactor, conversion at day 5 / day 10:

| Scenario | T | pH | X(5d) | X(10d) |
|---|---|---|---|---|
| Optimum | 33C | 1.8 | 90.0% | 100.0% |
| Example from spec | 35C | 1.8 | 93.8% | 100.0% |
| Moderate drift | 28C | 2.3 | 58.9% | 88.5% |
| Poor control | 22C | 3.0 | 8.7% | 16.9% |

This is a **model sensitivity illustration under the current (unvalidated) calibration**, not a site-specific guarantee -- see caveat above.

---

## 2. Biosorption (`scripts/biosorption_kinetics.py`)

### Equations
| Component | Equation | Basis |
|---|---|---|
| Langmuir isotherm | qe = qmax·b·Ce/(1+b·Ce) | Langmuir 1918 |
| Freundlich isotherm | qe = Kf·Ce^(1/n) | Freundlich 1906 |
| Pseudo-1st-order kinetics | q(t) = qe·(1-exp(-k1·t)) | Lagergren 1898 |
| Pseudo-2nd-order kinetics | q(t) = qe²·k2·t/(1+qe·k2·t) | Ho & McKay 1999 |
| pH factor (cationic) | sigmoid rise x sigmoid fall (precipitation) | typical biosorption pH-edge shape |
| pH factor (anionic complex) | inverted sigmoid (favored at LOW pH) | amine-protonation anion-exchange mechanism (chitosan-type literature) |

### Critical distinction: sorbate mechanism
- **Cationic** (Cu2+, Ni2+, REE3+, Li+): uptake favored at **higher** pH (surface carboxyl/phosphate groups deprotonate), falls at high pH once metal hydroxide precipitation competes.
- **Anionic complex** (Au(CN)2-, PtCl4^2-): uptake favored at **lower** pH (amine groups on biomass are protonated, acting as anion exchanger). Using the cationic curve for gold-cyanide gives the **wrong** pH recommendation.

### Presets (`METAL_PRESETS`)
| Preset | Type | qmax (mg/g) | Notes |
|---|---|---|---|
| `gold_cyanide` | anionic_complex | 80 | Chitosan-type materials can reach much higher with optimized sorbent; generic biomass typically lower |
| `copper_cationic` | cationic | 40 | Narrower usable pH window (Cu(OH)2 precipitates ~pH 5.5-6) |
| `ree_trivalent` | cationic | 55 | Generic trivalent lanthanide; specific REE (La/Nd/Ce/Dy) differ within series |
| `lithium_cationic` | cationic | 8 | **Caution:** biosorption is a weak, low-capacity route for Li+ vs. industrial ion-exchange/LDH sorbents -- validate economic viability early |

All preset numeric values are **illustrative literature-range placeholders**, not qFoldIT-validated. Use `fit_langmuir`, `fit_freundlich`, `fit_pseudo_second_order` against real equilibrium/kinetic assay data to replace them.

### Validated qualitative behavior (tests run during development)
- Parameter recovery: fitting functions recovered known Langmuir (qmax, b) and PSO (qe, k2) parameters from noisy synthetic data with R² > 0.998.
- pH direction confirmed opposite for `gold_cyanide` (falls with pH) vs. `copper_cationic`/`ree_trivalent` (bell-shaped, peaks mid-range) vs. `lithium_cationic` (still rising at pH 8 under current parameters -- LiOH precipitation is a high-pH phenomenon).
- Langmuir isotherm correctly asymptotes to qmax as Ce -> infinity.
- Lithium preset shows uptake roughly an order of magnitude below gold/copper/REE at comparable conditions, consistent with the caution noted for that system.

---

## 3. Cyanide biodegradation (`scripts/cyanide_kinetics.py`)

### Equations
| Component | Equation | Basis |
|---|---|---|
| Aiba substrate-inhibition rate | rate = rate_max·S/(Ks+S)·exp(-S/Ki) | Aiba, Shoda & Nagatani (1968) |
| Haldane/Andrews rate (alt. form, included for comparison) | rate = rate_max·S/(Ks+S+S²/Ki) | Andrews (1968) |
| Plain Monod (included ONLY to show it's wrong here) | rate = rate_max·S/(Ks+S) | no inhibition term -- never use for cyanide at concentrations that can reach the inhibitory range |
| Batch treatment | dX/dt=μ(S)·X, dS/dt=-q(S)·X | coupled ODE, solved via `scipy.integrate.solve_ivp` |

### Why substrate inhibition matters here specifically
Cyanide is unusual among biodegradation substrates in that it is simultaneously the food source AND the poison for the organisms that eat it. A plain Monod model only captures the "more substrate = faster, up to a ceiling" behavior; it cannot capture the fact that a sufficiently concentrated cyanide stream will actively suppress or kill the culture. Verified in this sandbox: at S=10,000 mg/L, plain Monod predicts the rate is still climbing toward rate_max (0.0194 vs a max of 0.0206), while the Aiba model correctly predicts the rate has collapsed to essentially zero (0.00000). Using the wrong model here doesn't just give a slightly-off number — it gives the **opposite operational recommendation** (concentrate the feed vs. dilute it).

### Presets (`CYANIDE_DEGRADER_PRESETS`)
| Preset | Growth μmax (1/h) | Growth Ks/Ki (mg/L) | Degradation rate_max (1/h) | Degradation Ks/Ki (mg/L) | Fit quality |
|---|---|---|---|---|---|
| `serratia_marcescens_AQ07` | 0.05695 | 491.6 / 422.1 | 0.02056 | 577.0 / 380.0 | R²=0.910 (growth), R²=0.766 (degradation) |

Source: batch kinetic study of a locally isolated cyanide-degrading *Serratia marcescens* strain, Aiba-model fit. **The weaker R² on the degradation-rate fit (0.766) is reported by the source study itself** — this preset's degradation forecasts should be treated as less certain than its growth forecasts, and this is stated plainly rather than glossed over.

### Validated qualitative behavior (tests run during development)
- Rate is confirmed non-monotonic: degradation rate at S=300 mg/L (0.00319/h) is higher than at both S=10 mg/L (0.00034/h, substrate-limited) and S=3000 mg/L (0.00001/h, inhibition-limited). Peak occurs near S* = sqrt(Ks·Ki) ≈ 468 mg/L for degradation, ≈ 456 mg/L for growth — consistent with the closed-form optimum.
- Monod-vs-Aiba divergence confirmed at high S: at S=10,000 mg/L, Monod predicts 0.0194 (94% of its ceiling), Aiba predicts ~0.0000 (correctly collapsed).
- `fit_aiba` exactly recovers known (rate_max, Ks, Ki) from clean synthetic data (R²=1.0). **With 5% synthetic noise added, the fit becomes noticeably less stable** (rate_max and Ks can shift by 2-3x while still fitting the noisy points reasonably well) — this is a real property of the nonlinear Aiba fit (Ks and rate_max trade off against each other) and is disclosed rather than hidden. Provide a wide concentration range and a good initial guess (literature defaults work well) when fitting real assay data.

### Critical caveat: absolute treatment-time forecasts
`simulate_batch_treatment` and `time_to_target_residual` require a starting biomass `X0` in whatever relative unit the literature `mu_max` was measured in (typically OD-based, not mg dry weight/L or cells/L). **Verified in this sandbox: holding S0=300 mg/L fixed and varying X0 from 0.05 to 20 (a 400x range) changes the 300-hour outcome from "S barely moved, 299.65 mg/L remaining" to "S cut nearly in half, 162.70 mg/L remaining."** The model's absolute timeline is dominated by this uncalibrated X0 choice, not by the (comparatively well-grounded) rate constants. Use these two functions to illustrate the *shape* of a depletion curve or to compare scenarios at a *fixed, consistent* X0 — not to promise a literal commissioning timeline — until X0 is calibrated against a real measured biomass density for the actual culture and reactor in question.

### Scope limits
- Models free/simple cyanide (CN⁻) only. Real tailings streams contain WAD cyanide complexes (Zn, Cu, Ni cyanides) with different bioavailability — not modeled here.
- No temperature or pH dependence (unlike the bio-oxidation and biosorption modules) — the source literature parameters were measured at one set of batch conditions, and extending them to a T/pH-dependent model would need a separate literature basis not yet incorporated.

---

## 4. What "efficiency gain" means here, and what it doesn't

The sensitivity table above shows the model's own internal range (how much conversion changes as T/pH deviate from optimum), **not** a validated comparison against a specific mine's current traditional-process baseline. A defensible "traditional vs. qFoldIT" efficiency-gain claim requires:

1. A traditional-process baseline recovery number **measured at the specific ore body**, not a generic industry figure.
2. Model constants (`A`, `Ea`, `qmax`, `b`, `k2`, etc.) fitted to **that same ore body's** assay/pilot data via the `fit_*` functions.
3. Only then does a "+X percentage points" or "Y days faster" comparison represent a real, defensible efficiency forecast rather than a difference between two literature placeholders.

Until step 2 happens, any efficiency-gain number should be presented as **"the model predicts approximately X% under stated assumptions, pending validation against site-specific data"** -- not as a company-wide or investment-grade performance guarantee.
