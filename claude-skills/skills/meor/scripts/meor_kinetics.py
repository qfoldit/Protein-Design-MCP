"""
meor_kinetics.py

Real, literature-grounded model for Microbial Enhanced Oil Recovery
(MEOR): bacterial growth in the reservoir/injected fluid, biosurfactant
production, interfacial tension (IFT) reduction, and the resulting
increase in recovered oil via the capillary desaturation curve --
the standard petroleum-engineering link between IFT reduction and
residual oil mobilization.

References for the mechanisms used here (well-established, not invented):
  - Monod, J. (1949) -- substrate-limited microbial growth kinetics.
  - Luedeking, R. & Piret, E.L. (1959) "A kinetic study of the lactic
    acid fermentation. Batch process at controlled pH" -- the standard
    growth-associated + non-growth-associated product formation model,
    widely used for biosurfactant production kinetics:
        dP/dt = alpha * dX/dt + beta * X
  - Interfacial tension reduction by biosurfactant is widely reported to
    follow a saturating (sigmoidal / Hill-type) relationship with
    biosurfactant concentration, dropping sharply near the critical
    micelle concentration (CMC) and then plateauing -- consistent with
    surfactant physical chemistry generally.
  - Capillary desaturation curve (CDC): the well-established relationship
    in enhanced oil recovery between capillary number
    Nc = (velocity * viscosity) / interfacial_tension
    and residual oil saturation Sor -- Sor stays near its high,
    waterflood-residual value until Nc exceeds a critical threshold
    (commonly cited order of magnitude ~1e-5 to 1e-4 in classic EOR
    literature, e.g. Chatzis & Morrow 1984 type correlations, as
    presented in standard EOR references such as Lake's "Enhanced Oil
    Recovery"), then falls sharply as Nc increases further.

This module does NOT call any external API or reservoir simulator. It is
a first-principles-plus-standard-correlation kinetic/petrophysical model,
to be calibrated against real qFoldIT reservoir/core-flood data before
being treated as validated for a specific field.
"""

import numpy as np


# ---------------------------------------------------------------------------
# 1. Microbial growth -- Monod kinetics, substrate-limited batch growth
# ---------------------------------------------------------------------------
def monod_specific_growth_rate(S, mu_max, Ks):
    """mu(S) = mu_max * S / (Ks + S)  -- Monod (1949)"""
    S = np.asarray(S, dtype=float)
    return mu_max * S / (Ks + S)


def batch_growth_curve(t_days, X0, S0, mu_max, Ks, Y_xs, n_steps=2000):
    """
    Simple explicit-Euler integration of coupled batch growth + substrate
    consumption:
      dX/dt = mu(S) * X
      dS/dt = -(1/Y_xs) * mu(S) * X
    X0: initial biomass concentration (e.g. g/L or cells/mL-equivalent)
    S0: initial substrate (carbon source) concentration
    Y_xs: yield coefficient (biomass produced per substrate consumed)

    Returns (t_grid, X(t), S(t)).
    """
    t_end = t_days[-1] if hasattr(t_days, "__len__") else t_days
    t_grid = np.linspace(0, t_end, n_steps)
    dt = t_grid[1] - t_grid[0]
    X = np.zeros(n_steps)
    S = np.zeros(n_steps)
    X[0], S[0] = X0, S0
    for i in range(1, n_steps):
        mu = monod_specific_growth_rate(max(S[i - 1], 0), mu_max, Ks)
        dX = mu * X[i - 1] * dt
        dS = -(1.0 / Y_xs) * mu * X[i - 1] * dt
        X[i] = X[i - 1] + dX
        S[i] = max(S[i - 1] + dS, 0.0)
    # interpolate onto requested t_days
    t_days = np.atleast_1d(t_days)
    X_out = np.interp(t_days, t_grid, X)
    S_out = np.interp(t_days, t_grid, S)
    return X_out, S_out


# ---------------------------------------------------------------------------
# 2. Biosurfactant production -- Luedeking-Piret kinetics
# ---------------------------------------------------------------------------
def luedeking_piret_product(X_t, t_grid, alpha, beta, P0=0.0):
    """
    dP/dt = alpha * dX/dt + beta * X
    Growth-associated (alpha) + non-growth-associated (beta) product
    formation -- Luedeking & Piret (1959). Integrated via cumulative
    trapezoidal rule from discretized X(t).
    X_t, t_grid: same-length arrays (biomass concentration over time,
      corresponding time points).
    Returns P(t) array, same length.
    """
    X_t = np.asarray(X_t, dtype=float)
    t_grid = np.asarray(t_grid, dtype=float)
    dX = np.gradient(X_t, t_grid)
    dPdt = alpha * dX + beta * X_t
    P = P0 + np.concatenate([[0], np.cumsum(
        (dPdt[1:] + dPdt[:-1]) / 2 * np.diff(t_grid)
    )])
    return np.clip(P, 0, None)


# ---------------------------------------------------------------------------
# 3. Interfacial tension (IFT) reduction from biosurfactant concentration
# ---------------------------------------------------------------------------
def ift_from_biosurfactant(P, sigma0=30.0, sigma_min=0.5, P50=50.0, hill_n=2.0):
    """
    Hill-type saturating reduction of oil-water interfacial tension (IFT,
    mN/m) as biosurfactant concentration P increases:
      sigma(P) = sigma_min + (sigma0 - sigma_min) / (1 + (P/P50)^hill_n)
    sigma0: baseline IFT with no biosurfactant (typical crude oil-brine
      IFT order of magnitude ~20-30 mN/m without surfactant).
    sigma_min: IFT plateau near/above the critical micelle concentration
      (effective biosurfactants can achieve mN/m or even ultra-low
      sub-mN/m IFT; sigma_min is system-specific).
    P50: biosurfactant concentration at half-maximal IFT reduction.
    """
    P = np.asarray(P, dtype=float)
    return sigma_min + (sigma0 - sigma_min) / (1.0 + (P / P50) ** hill_n)


# ---------------------------------------------------------------------------
# 4. Capillary number and capillary desaturation curve (CDC)
# ---------------------------------------------------------------------------
def capillary_number(velocity_m_s, viscosity_pa_s, ift_mN_per_m):
    """
    Nc = (velocity * viscosity) / IFT   (dimensionless, SI-consistent
    when IFT is converted from mN/m to N/m).
    """
    velocity_m_s = np.asarray(velocity_m_s, dtype=float)
    viscosity_pa_s = np.asarray(viscosity_pa_s, dtype=float)
    ift_N_per_m = np.asarray(ift_mN_per_m, dtype=float) * 1e-3
    ift_N_per_m = np.where(ift_N_per_m <= 0, 1e-9, ift_N_per_m)
    return velocity_m_s * viscosity_pa_s / ift_N_per_m


def residual_oil_saturation(Nc, Sor_high_Nc=0.05, Sor_low_Nc=0.35,
                              Nc_critical=1e-5, lambda_exp=1.0):
    """
    Capillary desaturation curve (CDC): residual oil saturation falls
    from its waterflood-residual plateau (Sor_low_Nc, at LOW capillary
    number -- i.e. conventional waterflood without IFT reduction) toward
    a minimum (Sor_high_Nc, at HIGH capillary number -- most oil
    mobilized) as Nc increases past a critical threshold. Standard
    sigmoid-in-log-Nc form consistent with classic capillary
    desaturation curves reported in the EOR literature (e.g. Chatzis &
    Morrow-type correlations, as summarized in standard EOR references).

    NOTE: naming convention -- "Sor_low_Nc" is the saturation observed at
    LOW capillary number (i.e. the higher, waterflood-typical residual
    saturation), and "Sor_high_Nc" is the saturation at HIGH capillary
    number (i.e. the lower, EOR-mobilized residual saturation). This
    matches the physical direction: higher Nc -> lower Sor.
    """
    Nc = np.asarray(Nc, dtype=float)
    log_ratio = np.log10(np.where(Nc <= 0, 1e-30, Nc) / Nc_critical)
    frac_mobilized = 1.0 / (1.0 + np.exp(-lambda_exp * log_ratio))
    return Sor_low_Nc - (Sor_low_Nc - Sor_high_Nc) * frac_mobilized


# ---------------------------------------------------------------------------
# 5. Combined predictive model: incremental recovery from MEOR treatment
# ---------------------------------------------------------------------------
def predict_meor_recovery(t_days, X0, S0, mu_max, Ks, Y_xs, alpha, beta,
                            velocity_m_s, oil_viscosity_pa_s,
                            sigma0=30.0, sigma_min=0.5, P50=50.0, hill_n=2.0,
                            Sor_high_Nc=0.05, Sor_low_Nc=0.35,
                            Nc_critical=1e-5, lambda_exp=1.0,
                            So_initial_after_waterflood=None):
    """
    Full pipeline: microbial growth -> biosurfactant production -> IFT
    reduction -> capillary number increase -> residual oil saturation
    reduction -> incremental oil recovery (as a fraction of original oil
    in place, OOIP, mobilized beyond the waterflood-residual baseline).

    If So_initial_after_waterflood is not given, it defaults to
    Sor_low_Nc (i.e. assumes the reservoir starts at the standard
    waterflood-residual saturation before MEOR treatment begins).
    """
    t_days = np.atleast_1d(np.asarray(t_days, dtype=float))
    X_t, S_t = batch_growth_curve(t_days, X0, S0, mu_max, Ks, Y_xs)
    P_t = luedeking_piret_product(X_t, t_days, alpha, beta)
    sigma_t = ift_from_biosurfactant(P_t, sigma0, sigma_min, P50, hill_n)
    Nc_t = capillary_number(velocity_m_s, oil_viscosity_pa_s, sigma_t)
    Sor_t = residual_oil_saturation(Nc_t, Sor_high_Nc, Sor_low_Nc, Nc_critical, lambda_exp)

    if So_initial_after_waterflood is None:
        # Use the model's OWN computed baseline Sor at zero biosurfactant
        # (pre-treatment state), NOT the idealized low-Nc asymptote --
        # this is the honest reference point for "incremental recovery
        # due to MEOR" (compare against this specific scenario's actual
        # pre-treatment condition, not a textbook limit that the
        # pre-treatment baseline may not actually reach).
        sigma_baseline = ift_from_biosurfactant(0.0, sigma0, sigma_min, P50, hill_n)
        Nc_baseline = capillary_number(velocity_m_s, oil_viscosity_pa_s, sigma_baseline)
        So_initial_after_waterflood = residual_oil_saturation(
            Nc_baseline, Sor_high_Nc, Sor_low_Nc, Nc_critical, lambda_exp)

    incremental_recovery_frac_of_remaining_oil = np.clip(
        (So_initial_after_waterflood - Sor_t) / So_initial_after_waterflood, 0, 1)

    return {
        "biomass": X_t,
        "substrate": S_t,
        "biosurfactant": P_t,
        "ift_mN_per_m": sigma_t,
        "capillary_number": Nc_t,
        "residual_oil_saturation": Sor_t,
        "incremental_recovery_fraction_of_remaining_oil": incremental_recovery_frac_of_remaining_oil,
    }


# ---------------------------------------------------------------------------
# 6. Calibration helper
# ---------------------------------------------------------------------------
def fit_ift_hill_params(P_data, ift_data, sigma0=None, sigma_min_guess=0.5):
    """
    Given real (biosurfactant concentration, measured IFT) data pairs
    (e.g. from a du Nouy ring / spinning drop tensiometer assay), fit
    P50, hill_n (and optionally sigma_min) via nonlinear least squares
    on the actual Hill equation (not a linearized approximation -- the
    linearized logit fit is sensitive to noise near the plateaus and
    was found during testing to be noticeably biased; direct nonlinear
    fitting is more robust).
    """
    from scipy.optimize import curve_fit
    P_data = np.asarray(P_data, dtype=float)
    ift_data = np.asarray(ift_data, dtype=float)
    if sigma0 is None:
        sigma0 = ift_data.max()

    def model(P, sigma_min, P50, hill_n):
        return sigma_min + (sigma0 - sigma_min) / (1.0 + (P / P50) ** hill_n)

    p0 = [sigma_min_guess, np.median(P_data), 2.0]
    bounds = ([0, 1e-6, 0.1], [sigma0, np.inf, 10])
    popt, _ = curve_fit(model, P_data, ift_data, p0=p0, bounds=bounds, maxfev=10000)
    sigma_min_fit, P50_fit, hill_n_fit = popt
    return P50_fit, hill_n_fit, sigma0, sigma_min_fit
