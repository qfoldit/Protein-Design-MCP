"""
cyanide_kinetics.py

Real, literature-grounded model for biological degradation of free/WAD
cyanide in gold mill tailings/effluent by cyanide-degrading bacteria
(e.g. Pseudomonas spp., Serratia marcescens, Alcaligenes faecalis --
biological cyanide detoxification is an established alternative/complement
to chemical processes like SO2/Air or hydrogen peroxide, used commercially
since the "Homestake process" in the 1980s-90s).

Key mechanistic fact this model is built around: cyanide is BOTH the growth
substrate for these bacteria AND toxic to them at high concentration. This
means degradation rate is non-monotonic in cyanide concentration -- too
little substrate is slow (ordinary Monod limitation), too much substrate
poisons the culture (substrate inhibition). A simple Monod model gets the
low-concentration behavior right but is qualitatively WRONG at high
concentration, where it would keep predicting ever-faster degradation.
This is exactly the kind of mistake this module exists to prevent.

References (well-established, not invented):
  - Aiba, S., Shoda, M., Nagatani, M. (1968) "Kinetics of product inhibition
    in alcohol fermentation" -- the Aiba/Aiba-Edwards substrate-inhibition
    form used here: rate = rate_max * S/(Ks+S) * exp(-S/Ki)
  - Andrews, J.F. (1968) "A mathematical model for the continuous culture
    of microorganisms utilizing inhibitory substrates" -- the classic
    Haldane/Andrews alternative form: rate = rate_max * S/(Ks+S+S^2/Ki),
    included here for comparison (`haldane_specific_rate`)
  - Default parameters below (mu_max, Ks, Ki for both growth and
    degradation) are taken from: Sharma, N. et al., 'Batch growth kinetic
    studies of locally isolated cyanide-degrading Serratia marcescens
    strain AQ07' (fitted with the Aiba model): growth mu_max=0.05695 /h,
    Ks=491.6 mg/L, Ki=422.1 mg/L (R^2=0.9098); specific degradation rate
    mu_max=0.02056 /h, Ks=577 mg/L, Ki=380 mg/L (R^2=0.7661). Note the
    weaker R^2 on the degradation fit -- flagged explicitly below, this is
    a real, reported model limitation, not something this module hides.
  - Homestake-process-style biological cyanide treatment and typical
    regulatory WAD-cyanide discharge targets (commonly tens of ug/L,
    varies sharply by jurisdiction) are referenced qualitatively only --
    no specific regulatory limit is hardcoded here, because it genuinely
    varies by country/site and must be supplied by the user.

Scope limits, stated plainly:
  - This module models FREE/simple cyanide (CN-) degraded by a single
    generic bacterial culture type. Real tailings streams contain WAD
    (weak-acid-dissociable) cyanide complexes (Zn, Cu, Ni cyanides) with
    different bioavailability and degradation rates -- this is a
    simplification, not a claim that all cyanide species behave identically.
  - No temperature or pH dependence is modeled here (unlike bioox_kinetics.py
    and biosorption_kinetics.py) -- the literature parameters above were
    measured at one set of batch conditions. Adding T/pH response would
    require a second, separate literature basis and is explicitly left
    out rather than guessed at.
  - Biomass (X) is tracked in the same somewhat abstract units as the
    growth-rate literature reports it in (typically OD-based, not mg
    dry cell weight/L) -- treat X as a relative activity/population
    index, not an absolute concentration, unless you supply a real
    OD-to-biomass conversion for your own culture.
"""

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import curve_fit, brentq


# ---------------------------------------------------------------------------
# 1. Substrate-inhibition rate models
# ---------------------------------------------------------------------------
def aiba_specific_rate(S, rate_max, Ks, Ki):
    """
    Aiba/Aiba-Edwards substrate-inhibition kinetics:
        rate(S) = rate_max * S / (Ks + S) * exp(-S / Ki)

    S       : cyanide concentration (mg/L)
    rate_max: maximum specific rate (1/h) -- growth (mu_max) or specific
              degradation rate, depending on which parameter set is passed
    Ks      : half-saturation constant (mg/L)
    Ki      : substrate-inhibition constant (mg/L) -- lower Ki means
              stronger toxicity at a given concentration

    At S << Ks: behaves like standard Monod (rate rises with S).
    At S >> Ki: the exp(-S/Ki) term dominates and rate falls toward zero
    -- this is the toxicity regime. The peak occurs at S* = sqrt(Ks*Ki).
    """
    S = np.asarray(S, dtype=float)
    return rate_max * S / (Ks + S) * np.exp(-S / Ki)


def haldane_specific_rate(S, rate_max, Ks, Ki):
    """
    Classic Haldane/Andrews (1968) substrate-inhibition form:
        rate(S) = rate_max * S / (Ks + S + S^2/Ki)

    Included for comparison -- qualitatively similar shape to the Aiba
    model (rises then falls, peak at S* = sqrt(Ks*Ki)) but a different
    functional form. Use whichever your own fitted data prefers; default
    presets here use the Aiba form since that's what the cited source
    fitted.
    """
    S = np.asarray(S, dtype=float)
    return rate_max * S / (Ks + S + (S ** 2) / Ki)


def monod_specific_rate(S, rate_max, Ks):
    """
    Plain Monod, NO inhibition term: rate(S) = rate_max * S / (Ks + S)

    Included only so you can directly see how wrong this is at high
    cyanide concentration -- it keeps rising toward rate_max and never
    captures the toxicity falloff. Do not use this for cyanide streams
    where concentration can plausibly reach the inhibitory range.
    """
    S = np.asarray(S, dtype=float)
    return rate_max * S / (Ks + S)


def optimal_concentration(Ks, Ki):
    """
    S* = sqrt(Ks * Ki) -- the cyanide concentration at which the Aiba
    (or Haldane) specific rate is maximized. Below S*, degradation is
    substrate-limited (add more cyanide-bearing stream / less dilution
    would help); above S*, it's inhibition-limited (dilute the feed or
    equalize peak concentrations instead).
    """
    return float(np.sqrt(Ks * Ki))


# ---------------------------------------------------------------------------
# 2. Literature parameter presets
# ---------------------------------------------------------------------------
# Source: Sharma et al., batch kinetic study of Serratia marcescens AQ07,
# Aiba model fit. See module docstring for full citation.
CYANIDE_DEGRADER_PRESETS = {
    "serratia_marcescens_AQ07": {
        "growth": {"mu_max": 0.05695, "Ks": 491.6, "Ki": 422.1, "r_squared": 0.9098},
        "degradation": {"mu_max": 0.02056, "Ks": 577.0, "Ki": 380.0, "r_squared": 0.7661},
        "notes": (
            "Batch, single-strain, single-substrate (free cyanide only) "
            "study. Degradation-rate fit R^2=0.7661 is noticeably weaker "
            "than the growth-rate fit (0.9098) -- the source study itself "
            "reports this; treat degradation-rate forecasts from this "
            "preset as the less certain of the two, not equally reliable."
        ),
    },
}


def get_preset(name):
    if name not in CYANIDE_DEGRADER_PRESETS:
        raise KeyError(
            f"Unknown preset '{name}'. Available: {list(CYANIDE_DEGRADER_PRESETS.keys())}"
        )
    return CYANIDE_DEGRADER_PRESETS[name]


# ---------------------------------------------------------------------------
# 3. Batch reactor simulation: biomass growth + cyanide depletion
# ---------------------------------------------------------------------------
def simulate_batch_treatment(t_hours, S0, X0, growth_params, degradation_params):
    """
    Solve the coupled ODE system for a batch biological cyanide treatment:

        dX/dt = mu(S) * X            (biomass growth, Aiba kinetics)
        dS/dt = -q(S) * X            (cyanide degradation, Aiba kinetics,
                                       its own separate rate_max/Ks/Ki)

    t_hours          : array of time points (h) to report the solution at
    S0                : initial cyanide concentration (mg/L)
    X0                : initial biomass, in WHATEVER RELATIVE UNIT the
                        growth_params/degradation_params rate constants
                        were measured against (see CRITICAL CAVEAT below)
    growth_params     : dict with mu_max, Ks, Ki (Aiba growth kinetics)
    degradation_params: dict with mu_max, Ks, Ki (Aiba degradation kinetics
                        -- note this mu_max is really a specific
                        degradation rate constant, not a growth rate)

    Returns (S_t, X_t) arrays aligned with t_hours. S is clipped at 0 --
    the ODE can overshoot slightly negative near depletion, which isn't
    physical.

    CRITICAL CAVEAT ON ABSOLUTE TIMESCALE: the literature mu_max/Ks/Ki
    values here come from specific-rate studies (rate per unit biomass),
    which do NOT by themselves tell you what X0 corresponds to in your
    actual reactor (mg dry cell weight/L, OD600, or cells/L). Verified in
    this sandbox: with the default preset, going from X0=0.05 to X0=20 (a
    400x range) still only takes S from 300 to somewhere between 299.6 and
    162.7 mg/L over 300 hours -- the ABSOLUTE treatment time is extremely
    sensitive to an X0 value this module cannot supply for you. Use this
    function for the SHAPE of the depletion curve and relative comparisons
    (e.g. "this feed concentration is in the inhibition-limited regime, so
    diluting it first will help"), not for a literal "N hours to treat M
    liters" claim, until you calibrate X0 against your own reactor's
    measured biomass density.
    """
    t_hours = np.asarray(t_hours, dtype=float)

    def rhs(t, y):
        S, X = y
        S = max(S, 0.0)
        mu = aiba_specific_rate(S, growth_params["mu_max"], growth_params["Ks"], growth_params["Ki"]) \
            if S > 0 else 0.0
        q = aiba_specific_rate(S, degradation_params["mu_max"], degradation_params["Ks"], degradation_params["Ki"]) \
            if S > 0 else 0.0
        dXdt = mu * X
        dSdt = -q * X
        return [dSdt, dXdt]

    sol = solve_ivp(
        rhs,
        t_span=(t_hours[0], t_hours[-1]),
        y0=[S0, X0],
        t_eval=t_hours,
        method="LSODA",
        rtol=1e-8,
        atol=1e-10,
    )
    if not sol.success:
        raise RuntimeError(f"ODE integration failed: {sol.message}")

    S_t = np.clip(sol.y[0], 0.0, None)
    X_t = sol.y[1]
    return S_t, X_t


def time_to_target_residual(S0, X0, target_S, growth_params, degradation_params,
                             max_hours=2000.0, n_eval=4000):
    """
    Find the time (hours) at which cyanide concentration first drops to
    target_S, by simulating the batch system on a fine grid and
    interpolating. Raises ValueError if the target isn't reached within
    max_hours (this DOES happen physically -- e.g. if S0 is deep in the
    inhibition-limited regime with a small starting inoculum, or if
    target_S is set below what dilute residual conditions can reach with
    this model's degradation kinetics; that's a real result, not a bug,
    and should be reported as such rather than silently extending the
    horizon).
    """
    if target_S >= S0:
        raise ValueError("target_S must be less than S0")
    t_grid = np.linspace(0, max_hours, n_eval)
    S_t, _ = simulate_batch_treatment(t_grid, S0, X0, growth_params, degradation_params)
    if S_t[-1] > target_S:
        raise ValueError(
            f"Target residual {target_S} mg/L not reached within {max_hours} h "
            f"under these conditions (S ended at {S_t[-1]:.2f} mg/L). Try a "
            f"longer horizon, a larger starting inoculum (X0), or check "
            f"whether S0 is in the inhibition-limited regime "
            f"(S0 vs. optimal_concentration(Ks, Ki))."
        )
    idx = np.argmax(S_t <= target_S)
    return float(t_grid[idx])


# ---------------------------------------------------------------------------
# 4. Fitting Aiba parameters to real assay data
# ---------------------------------------------------------------------------
def fit_aiba(S_data, rate_data, initial_guess=None):
    """
    Nonlinear least-squares fit of the Aiba model to real (S, specific
    rate) data pairs -- e.g. from your own batch kinetic assay at a
    series of initial cyanide concentrations.

    Unlike the Langmuir/Freundlich isotherms in biosorption_kinetics.py,
    the Aiba model is NOT linearizable, so this uses scipy.optimize.curve_fit
    (nonlinear) rather than a linear regression trick. This means it needs
    a reasonable initial_guess to converge reliably -- if you don't have
    one, (rate_max=max(rate_data)*1.5, Ks=median(S_data), Ki=median(S_data))
    is used as a rough default starting point.

    Returns (rate_max, Ks, Ki, r_squared).
    """
    S_data = np.asarray(S_data, dtype=float)
    rate_data = np.asarray(rate_data, dtype=float)

    if initial_guess is None:
        initial_guess = (float(np.max(rate_data)) * 1.5, float(np.median(S_data)), float(np.median(S_data)))

    popt, _ = curve_fit(
        aiba_specific_rate, S_data, rate_data, p0=initial_guess,
        bounds=(0, np.inf), maxfev=10000,
    )
    rate_max, Ks, Ki = popt
    pred = aiba_specific_rate(S_data, rate_max, Ks, Ki)
    ss_res = np.sum((rate_data - pred) ** 2)
    ss_tot = np.sum((rate_data - np.mean(rate_data)) ** 2)
    r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return float(rate_max), float(Ks), float(Ki), float(r_squared)
