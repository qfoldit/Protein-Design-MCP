"""
corrosion_kinetics.py

Internal CO2 ("sweet") corrosion rate prediction for carbon steel oil &
gas pipelines, built on the published de Waard-Milliams correlation.

BASE EQUATION (de Waard, Lotz & Milliams, 1991 -- widely cited/used form):
    log10(Vnomo) = 5.8 - 1710/T + 0.67*log10(pCO2)
    Vnomo in mm/year, T in Kelvin, pCO2 in bar.

Reference: de Waard, C., Lotz, U., Milliams, D.E. "Predictive Model for
CO2 Corrosion Engineering in Wet Natural Gas Pipelines." CORROSION 47,
976 (1991); de Waard, C., Lotz, U. "Prediction of CO2 Corrosion of Carbon
Steel." CORROSION/1993, Paper 69 (NACE).

Sign convention sanity-checked against a commonly-cited worked example:
at T=20C (293K), pCO2=1 bar: log(Vnomo) = 5.8 - 1710/293 + 0 = -0.036,
Vnomo = 0.92 mm/yr -- consistent with commonly-quoted "roughly 1 mm/yr at
20C, 1 bar CO2, uninhibited" figures for this correlation.

SCALE (PROTECTIVE FILM) SUPPRESSION at higher temperature -- a real,
well-documented phenomenon (FeCO3 scale becomes protective above roughly
60-70C under supersaturated conditions), following de Waard's own
"scaling temperature" approach:
    Tscale (K) = 2400 / (6.7 + 0.6*log10(pCO2))
    log10(Fscale) = 2400*(1/T - 1/Tscale)   for T > Tscale
    Fscale = 1                               for T <= Tscale
This produces the characteristic non-monotonic temperature response: rate
rises with T up to Tscale (the "worst case" nomogram peak), then falls as
protective scale becomes effective at higher T.

FLOW / MASS-TRANSFER ENHANCEMENT and EROSION-CORROSION: the full de Waard
1995 model computes a genuine mass-transfer-limited rate from a
Sherwood-type correlation requiring diffusion coefficient, kinematic
viscosity, and hydraulic diameter -- inputs this skill does not collect
(see SKILL.md's stated input list: temperature, pCO2, velocity, salinity,
inhibitor). Rather than fabricate values for those extra parameters, this
module uses a DELIBERATELY SIMPLIFIED, clearly-labeled flow-response
model that captures the two real, well-documented qualitative behaviors:
  (a) at low velocity, corrosion becomes mass-transfer limited (dissolved
      CO2/carbonic acid can't reach the metal surface fast enough) --
      modeled as a smooth saturating function of velocity.
  (b) at very high velocity (especially with solids/sand present),
      erosion-corrosion increases metal loss above the erosional velocity
      guideline (cf. API RP 14E) -- modeled as a penalty factor above a
      configurable erosional velocity.
This is NOT a reproduction of the de Waard 1995 Sherwood mass-transfer
equation -- it is a simpler proxy for the same two qualitative effects,
and is documented as such rather than presented as the full published
model.

PITTING RISK from salinity/chlorides: kept as a SEPARATE, qualitative
0-1 risk indicator, never combined into the uniform corrosion rate
number -- pitting (localized) and uniform corrosion are different
failure modes and conflating them would be misleading (see SKILL.md
point 4).

INHIBITOR EFFECT: straightforward multiplicative reduction,
Vcor_inhibited = Vcor_uninhibited * (1 - efficiency).
"""

import numpy as np
from scipy.optimize import curve_fit


# ---------------------------------------------------------------------------
# 1. Base de Waard-Milliams nomogram rate
# ---------------------------------------------------------------------------
def dewaard_nomogram_rate(T_c, pCO2_bar):
    """
    Base (uninhibited, no scale, no flow limitation) de Waard-Milliams
    corrosion rate.

    T_c      : temperature, degrees Celsius
    pCO2_bar : CO2 partial pressure, bar

    Returns Vnomo in mm/year.
    """
    T_k = T_c + 273.15
    log_v = 5.8 - 1710.0 / T_k + 0.67 * np.log10(pCO2_bar)
    return float(10 ** log_v)


# ---------------------------------------------------------------------------
# 2. Protective scale (high-temperature film) suppression
# ---------------------------------------------------------------------------
def scaling_temperature_c(pCO2_bar):
    """
    Tscale (deg C) -- the temperature above which protective FeCO3 scale
    starts suppressing the corrosion rate, per de Waard's own formula:
        Tscale (K) = 2400 / (6.7 + 0.6*log10(pCO2))
    """
    T_scale_k = 2400.0 / (6.7 + 0.6 * np.log10(pCO2_bar))
    return float(T_scale_k - 273.15)


def scale_factor(T_c, pCO2_bar):
    """
    Fscale <= 1, multiplies the nomogram rate down once T exceeds the
    scaling temperature. Fscale = 1 (no suppression) at or below it.
    """
    T_k = T_c + 273.15
    T_scale_k = scaling_temperature_c(pCO2_bar) + 273.15
    if T_k <= T_scale_k:
        return 1.0
    log_fscale = 2400.0 * (1.0 / T_k - 1.0 / T_scale_k)
    return float(10 ** log_fscale)


# ---------------------------------------------------------------------------
# 3. Simplified flow / mass-transfer and erosion-corrosion factors
# ---------------------------------------------------------------------------
def flow_enhancement_factor(velocity_m_s, v_ref=1.0, floor=0.3):
    """
    Simplified mass-transfer proxy: smoothly saturates toward 1.0 as
    velocity increases past v_ref (m/s), and drops toward `floor` (never
    to zero -- some corrosion still occurs even in near-stagnant
    conditions) at very low velocity.

        Fflow(v) = floor + (1 - floor) * tanh(v / v_ref)

    v_ref=1.0 m/s is a generic, illustrative reference matching the
    qualitative range where flow-enhancement effects are typically
    reported to become significant in de Waard-type models -- NOT fitted
    to any specific pipeline's hydraulics.
    """
    return float(floor + (1 - floor) * np.tanh(velocity_m_s / v_ref))


def erosion_corrosion_factor(velocity_m_s, v_erosion=10.0, k=1.5):
    """
    Penalty factor >= 1, kicking in above an erosional velocity threshold
    (API RP 14E-style guideline value, commonly cited in the rough range
    of 5-15 m/s depending on fluid/solids content -- v_erosion=10 m/s is
    an illustrative mid-range default, NOT a site-specific erosional
    velocity calculation, which properly depends on fluid density and a
    C-factor per API RP 14E).

        Ferosion(v) = 1                                    for v <= v_erosion
        Ferosion(v) = 1 + k*((v - v_erosion)/v_erosion)^2   for v > v_erosion
    """
    if velocity_m_s <= v_erosion:
        return 1.0
    return float(1.0 + k * ((velocity_m_s - v_erosion) / v_erosion) ** 2)


# ---------------------------------------------------------------------------
# 4. Pitting risk (salinity/chloride-driven) -- SEPARATE from uniform rate
# ---------------------------------------------------------------------------
def pitting_risk_score(salinity_ppt):
    """
    Qualitative 0-1 pitting/localized-corrosion risk indicator based on
    chloride/salinity level. This is a HEURISTIC screening indicator, not
    a quantitative pit-growth-rate model -- pitting depends heavily on
    factors not captured here (under-deposit conditions, microstructure,
    weld heat-affected zones, dissolved oxygen ingress). Thresholds below
    are illustrative, loosely anchored to the general observation that
    produced-water salinity above roughly 20-30 g/L (ppt) is commonly
    associated with elevated localized-corrosion concern in the industry,
    not a validated quantitative boundary.

    Returns (score in [0,1], category string).
    """
    score = float(np.clip(salinity_ppt / 60.0, 0.0, 1.0))  # saturates by ~60 ppt
    if score < 0.2:
        category = "low"
    elif score < 0.5:
        category = "moderate"
    else:
        category = "high"
    return score, category


# ---------------------------------------------------------------------------
# 5. Combined prediction
# ---------------------------------------------------------------------------
def predict_corrosion_rate(T_c, pCO2_bar, velocity_m_s, salinity_ppt=0.0,
                            inhibitor_efficiency=0.0, site_offset=1.0):
    """
    Full prediction combining all effects. Returns a dict with the
    uniform corrosion rate breakdown AND a separate pitting risk
    indicator -- these are never combined into one number.

    T_c                   : temperature, deg C
    pCO2_bar              : CO2 partial pressure, bar
    velocity_m_s          : liquid flow velocity, m/s
    salinity_ppt          : salinity/chlorides, parts per thousand (0 if fresh water)
    inhibitor_efficiency  : fraction 0-1 (e.g. 0.85 for 85% effective inhibitor)
    site_offset           : multiplicative site-specific correction factor
                            from fit_dewaard_offset_from_data; 1.0 = generic
                            literature calibration (default, unvalidated
                            for any specific pipeline)

    Returns dict:
      vnomo_mm_yr           : base nomogram rate (no corrections)
      fscale, fflow, ferosion : the individual multiplicative factors
      uninhibited_rate_mm_yr : Vnomo * Fscale * Fflow * Ferosion * site_offset
      inhibited_rate_mm_yr   : uninhibited_rate * (1 - inhibitor_efficiency)
      pitting_risk_score, pitting_risk_category : SEPARATE indicator
      scaling_temperature_c  : for reference/interpretation
    """
    vnomo = dewaard_nomogram_rate(T_c, pCO2_bar)
    fscale = scale_factor(T_c, pCO2_bar)
    fflow = flow_enhancement_factor(velocity_m_s)
    ferosion = erosion_corrosion_factor(velocity_m_s)

    uninhibited = vnomo * fscale * fflow * ferosion * site_offset
    inhibited = uninhibited * (1.0 - inhibitor_efficiency)

    pit_score, pit_category = pitting_risk_score(salinity_ppt)

    return {
        "vnomo_mm_yr": round(vnomo, 4),
        "fscale": round(fscale, 4),
        "fflow": round(fflow, 4),
        "ferosion": round(ferosion, 4),
        "uninhibited_rate_mm_yr": round(uninhibited, 4),
        "inhibited_rate_mm_yr": round(inhibited, 4),
        "pitting_risk_score": round(pit_score, 3),
        "pitting_risk_category": pit_category,
        "scaling_temperature_c": round(scaling_temperature_c(pCO2_bar), 1),
    }


# ---------------------------------------------------------------------------
# 6. Remaining wall life
# ---------------------------------------------------------------------------
def remaining_life_years(current_wall_mm, min_required_wall_mm, corrosion_rate_mm_yr):
    """
    Simple constant-rate remaining-life estimate:
        years = (current_wall - min_required_wall) / corrosion_rate

    CAVEAT (state this whenever reporting a result): this assumes the
    corrosion rate stays constant over the pipeline's remaining life.
    Real conditions (water cut, temperature, inhibitor availability,
    scale integrity) change over time -- this is a first-order screening
    number, not a substitute for an ongoing inspection/monitoring program.
    """
    if corrosion_rate_mm_yr <= 0:
        raise ValueError("corrosion_rate_mm_yr must be > 0")
    available_mm = current_wall_mm - min_required_wall_mm
    if available_mm < 0:
        raise ValueError("current_wall_mm is already below min_required_wall_mm")
    return float(available_mm / corrosion_rate_mm_yr)


# ---------------------------------------------------------------------------
# 7. Fitting a site-specific offset from real field/coupon data
# ---------------------------------------------------------------------------
def fit_dewaard_offset_from_data(T_c_list, pCO2_bar_list, velocity_list, measured_rate_list):
    """
    Given a set of real measured corrosion rates (e.g. from coupons, ER
    probes, or field inspection) under known conditions, fit a single
    multiplicative site_offset that best reconciles the model's
    (scale+flow-corrected, uninhibited) predictions with reality.

    Fits in log-space (i.e. finds the offset minimizing squared error of
    log(predicted*offset) vs log(measured)) since corrosion rates span
    orders of magnitude and multiplicative error is the natural way to
    think about a calibration offset here.

    Returns (site_offset, r_squared_in_log_space).
    """
    T_c_arr = np.asarray(T_c_list, dtype=float)
    pCO2_arr = np.asarray(pCO2_bar_list, dtype=float)
    v_arr = np.asarray(velocity_list, dtype=float)
    measured = np.asarray(measured_rate_list, dtype=float)

    base_predictions = np.array([
        dewaard_nomogram_rate(T_c_arr[i], pCO2_arr[i])
        * scale_factor(T_c_arr[i], pCO2_arr[i])
        * flow_enhancement_factor(v_arr[i])
        * erosion_corrosion_factor(v_arr[i])
        for i in range(len(T_c_arr))
    ])

    log_pred = np.log(base_predictions)
    log_meas = np.log(measured)

    # optimal multiplicative offset in log-space = mean(log_meas - log_pred)
    log_offset = np.mean(log_meas - log_pred)
    site_offset = float(np.exp(log_offset))

    fitted_log = log_pred + log_offset
    ss_res = np.sum((log_meas - fitted_log) ** 2)
    ss_tot = np.sum((log_meas - np.mean(log_meas)) ** 2)
    r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")

    return site_offset, float(r_squared)
