"""
bioox_kinetics.py

Real, literature-grounded kinetic model for bio-oxidation of refractory
sulfide gold ore (e.g. arsenopyrite FeAsS, pyrite FeS2) by mesophilic
iron/sulfur-oxidizing bacteria (Acidithiobacillus ferrooxidans and
consortia).

References for the mechanisms used here (well-established, not invented):
  - Levenspiel, O. "Chemical Reaction Engineering" (Shrinking Core Model)
  - Rosso, L., Lobry, J.R., Flandrois, J.P. (1993) "An unexpected correlation
    between cardinal temperatures of microbial growth highlighted by a new
    model" -- cardinal temperature model with inflection (CTMI)
  - Numerous bioleaching/biooxidation studies report activation energies
    in the ~40-75 kJ/mol range for chemical-reaction-controlled regimes,
    and optimum pH ~1.5-2.0 / optimum T ~30-35 C for mesophilic
    A. ferrooxidans consortia -- these are the literature ranges the
    defaults below are drawn from.

This module does NOT call any external API or dataset. It is a
first-principles kinetic model intended to be validated against real
qFoldIT assay/pilot data once available, and is the "real algorithm"
layer that a Skill would eventually wrap.
"""

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq


# ---------------------------------------------------------------------------
# 1. Temperature response: Cardinal Temperature Model with Inflection (CTMI)
# ---------------------------------------------------------------------------
def ctmi_temperature_factor(T_c, T_min=10.0, T_opt=33.0, T_max=45.0):
    """
    Rosso et al. (1993) CTMI model, normalized so factor(T_opt) = 1.0.
    Returns 0 outside [T_min, T_max]. This is the standard way to express
    a microbial rate's non-monotonic (bell-shaped) temperature dependence,
    as opposed to naive Arrhenius which is monotonically increasing and
    wrong for living organisms above their thermal optimum.

    T_min, T_opt, T_max in degrees C. Defaults are typical literature
    values for mesophilic A. ferrooxidans-dominated bioleaching consortia.
    """
    T = np.asarray(T_c, dtype=float)
    out = np.zeros_like(T)
    mask = (T > T_min) & (T < T_max)
    Tm = T[mask]

    num = (Tm - T_max) * (Tm - T_min) ** 2
    den = (
        (T_opt - T_min)
        * ((T_opt - T_min) * (Tm - T_opt) - (T_opt - T_max) * (T_opt + T_min - 2 * Tm))
    )
    out[mask] = num / den
    return out if out.shape else float(out)


# ---------------------------------------------------------------------------
# 2. pH response: skewed Gaussian around an optimum
# ---------------------------------------------------------------------------
def ph_factor(pH, pH_opt=1.8, sigma_low=0.5, sigma_high=0.7):
    """
    Bell-shaped pH activity factor, normalized to 1.0 at pH_opt.
    Asymmetric sigma because A. ferrooxidans consortia tolerate the
    acidic side less steeply than typical -- this reflects commonly
    reported bioleaching pH-activity curves (sharper falloff below ~1.0,
    gentler falloff up to ~2.5-3.0).
    """
    pH = np.asarray(pH, dtype=float)
    sigma = np.where(pH < pH_opt, sigma_low, sigma_high)
    return np.exp(-((pH - pH_opt) ** 2) / (2 * sigma ** 2))


# ---------------------------------------------------------------------------
# 3. Arrhenius baseline rate constant (chemical/enzymatic step)
# ---------------------------------------------------------------------------
R_GAS = 8.314  # J/(mol K)


def arrhenius_k(T_c, A, Ea_kJ_per_mol):
    """k = A * exp(-Ea / (R T)), T in Kelvin."""
    T_k = np.asarray(T_c, dtype=float) + 273.15
    Ea = Ea_kJ_per_mol * 1000.0
    return A * np.exp(-Ea / (R_GAS * T_k))


# ---------------------------------------------------------------------------
# 4. Effective rate constant combining Arrhenius x microbial T-response x pH
# ---------------------------------------------------------------------------
def effective_rate_constant(
    T_c,
    pH,
    A=2.6e8,          # pre-exponential factor, 1/day -- calibrated so that at
                      # T_opt=33C, pH_opt=1.8 the model reaches X=90% in ~5
                      # days, matching commercial BIOX reactor retention times
                      # (industry benchmark, ~4-6 days at optimum conditions).
                      # THIS IS STILL A CALIBRATION AGAINST A GENERIC BENCHMARK,
                      # NOT YOUR ORE. Replace with a fit to your own assay data
                      # as soon as you have it (see fit_A_from_data below).
    Ea_kJ_per_mol=55.0,  # mid-range literature value for reaction-controlled biooxidation
    T_min=10.0, T_opt=33.0, T_max=45.0,
    pH_opt=1.8, sigma_low=0.5, sigma_high=0.7,
):
    """
    k_eff(T, pH) = k_Arrhenius(T) * f_T_microbial(T) * f_pH(pH)

    Arrhenius gives the underlying chemical/enzymatic temperature
    sensitivity; the CTMI factor imposes the realistic microbial ceiling
    (bacteria die off above T_max, unlike a bare Arrhenius law which
    would predict ever-increasing rate); pH factor imposes the microbial
    pH tolerance window.
    """
    k_arr = arrhenius_k(T_c, A, Ea_kJ_per_mol)
    f_T = ctmi_temperature_factor(T_c, T_min, T_opt, T_max)
    f_pH = ph_factor(pH, pH_opt, sigma_low, sigma_high)
    return k_arr * f_T * f_pH


# ---------------------------------------------------------------------------
# 5. Shrinking Core Model -- reaction-controlled regime (typical for fine
#    ground flotation concentrate, which is the usual biooxidation feed)
# ---------------------------------------------------------------------------
def scm_conversion_reaction_controlled(t_days, k_eff, particle_radius_um=20.0, r0_ref_um=20.0):
    """
    Reaction-controlled SCM: 1 - (1-X)^(1/3) = k * t / r0

    Rate scales inversely with initial particle radius (surface-area
    argument); r0_ref_um is the radius the k_eff calibration assumes, so
    other particle sizes are scaled relative to it.
    """
    k_scaled = k_eff * (r0_ref_um / particle_radius_um)
    tau = k_scaled * t_days
    tau = np.clip(tau, 0, None)
    one_minus_X_cbrt = 1.0 - tau
    one_minus_X_cbrt = np.clip(one_minus_X_cbrt, 0.0, None)
    X = 1.0 - one_minus_X_cbrt ** 3
    return np.clip(X, 0.0, 1.0)


def time_to_reach_conversion(X_target, k_eff, particle_radius_um=20.0, r0_ref_um=20.0):
    """Invert the SCM equation to find days needed for a target conversion."""
    if not (0 < X_target < 1):
        raise ValueError("X_target must be strictly between 0 and 1")
    k_scaled = k_eff * (r0_ref_um / particle_radius_um)
    tau_needed = 1.0 - (1.0 - X_target) ** (1.0 / 3.0)
    return tau_needed / k_scaled


# ---------------------------------------------------------------------------
# 6. Bacterial population growth (Monod-limited logistic), feeding back
#    into an effective active-biomass multiplier during startup
# ---------------------------------------------------------------------------
def fit_A_from_data(t_days_data, X_data, T_c, pH, particle_radius_um=20.0,
                     Ea_kJ_per_mol=55.0, **kwargs):
    """
    Given real (t, X) assay/pilot data points at known T and pH, back out
    the pre-exponential factor A that best fits them (least squares on the
    linearized reaction-controlled SCM: 1-(1-X)^(1/3) = k*t/r0).

    THIS is how the placeholder A above should eventually be replaced --
    feed it your lab bottle-roll or pilot column test data.
    """
    t_days_data = np.asarray(t_days_data, dtype=float)
    X_data = np.asarray(X_data, dtype=float)
    y = 1.0 - (1.0 - X_data) ** (1.0 / 3.0)
    # y = k * t  =>  k = slope of y vs t through origin (least squares)
    k_fit = np.sum(y * t_days_data) / np.sum(t_days_data ** 2)
    k_fit_scaled = k_fit  # already at the given particle_radius_um / r0_ref match
    f_T = ctmi_temperature_factor(T_c, kwargs.get("T_min", 10.0),
                                   kwargs.get("T_opt", 33.0), kwargs.get("T_max", 45.0))
    f_pH = ph_factor(pH, kwargs.get("pH_opt", 1.8),
                      kwargs.get("sigma_low", 0.5), kwargs.get("sigma_high", 0.7))
    k_arr_no_A = arrhenius_k(T_c, 1.0, Ea_kJ_per_mol)  # Arrhenius term without A
    A_fit = k_fit_scaled / (k_arr_no_A * f_T * f_pH)
    return A_fit, k_fit_scaled


def bacterial_growth_curve(t_days, mu_max=0.15, X0_frac=0.02, carrying_capacity=1.0):
    """
    Simple logistic growth for active bacterial population fraction
    (0=inoculum, 1=fully established consortium). mu_max ~0.1-0.2 /day
    is a realistic mesophilic A. ferrooxidans specific growth rate range.
    Returns fraction of full microbial activity available at time t.
    """
    t = np.asarray(t_days, dtype=float)
    K = carrying_capacity
    X0 = X0_frac * K
    return K / (1 + ((K - X0) / X0) * np.exp(-mu_max * t))


# ---------------------------------------------------------------------------
# 7. Full process model: recovery(t) accounting for biomass ramp-up
# ---------------------------------------------------------------------------
def predict_recovery_curve(
    t_days,
    T_c=35.0,
    pH=1.8,
    particle_radius_um=20.0,
    reactor_mode="continuous",   # "continuous" (mature, always-active culture,
                                  # e.g. BIOX-style CSTR train) or "batch"
                                  # (fresh inoculation each cycle, e.g. heap/
                                  # bottle-roll start-up)
    mu_max=0.15,
    X0_frac=0.02,
    **kwargs
):
    """
    Combines microbial state (mature vs ramping) with SCM reaction-controlled
    kinetics, using an effective time that accounts for the population not
    being fully active from day 0 in batch mode.

    reactor_mode="continuous": biomass_frac == 1 for all t (culture already
      established and continuously maintained -- appropriate for commercial
      CSTR bio-oxidation trains like BIOX, where retention time is what's
      being sized, not population growth).
    reactor_mode="batch": biomass_frac follows the logistic ramp-up curve
      (appropriate for heap inoculation or fresh bottle-roll/column tests).
    """
    if reactor_mode not in ("continuous", "batch"):
        raise ValueError('reactor_mode must be "continuous" or "batch"')

    t = np.asarray(t_days, dtype=float)
    k_eff = effective_rate_constant(T_c, pH, **kwargs)

    if reactor_mode == "continuous":
        biomass_frac = np.ones_like(t)
        active_time = t
    else:
        biomass_frac = bacterial_growth_curve(t, mu_max, X0_frac)
        active_time = np.concatenate([[0], np.cumsum(
            (biomass_frac[1:] + biomass_frac[:-1]) / 2 * np.diff(t)
        )]) if t.size > 1 else np.array([0.0])

    X = scm_conversion_reaction_controlled(active_time, k_eff, particle_radius_um)
    return X, k_eff, biomass_frac
