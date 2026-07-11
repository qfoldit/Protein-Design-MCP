"""
biosorption_kinetics.py

Real, literature-grounded equilibrium + kinetic model for metal-ion
biosorption onto biomass (e.g. fungal/algal/bacterial biomass used for
metal recovery from leach liquors -- gold, copper, REE, lithium, etc.
depending on qFoldIT's target system).

References for the mechanisms used here (well-established, not invented):
  - Langmuir, I. (1918) -- monolayer adsorption isotherm
  - Freundlich, H.M.F. (1906) -- empirical multilayer/heterogeneous-surface
    isotherm
  - Lagergren, S. (1898) -- pseudo-first-order kinetics
  - Ho, Y.S. & McKay, G. (1999) "Pseudo-second order model for sorption
    processes" -- pseudo-second-order kinetics, very commonly the best fit
    for biosorption of metal ions onto biological materials
  - pH dependence: metal cation biosorption onto biomass generally
    increases with pH as surface functional groups (carboxyl pKa ~3-5,
    phosphate/hydroxyl higher) deprotonate and expose binding sites, then
    falls off at high pH due to metal hydroxide precipitation/competing
    equilibria -- this is a broadly reported shape across biosorption
    literature (bell/sigmoid depending on system).

This module is generic across metal/biomass pairs -- the numeric
parameters (qmax, b, Kf, n, k1, k2) are system-specific and MUST be
fitted from your own equilibrium/kinetic assay data using the fitting
functions provided. The defaults used in the test script are illustrative
literature-range placeholders, not qFoldIT-validated values.
"""

import numpy as np


# ---------------------------------------------------------------------------
# 1. Equilibrium isotherms
# ---------------------------------------------------------------------------
def langmuir_isotherm(Ce, qmax, b):
    """
    Langmuir monolayer isotherm: qe = qmax * b * Ce / (1 + b * Ce)
    Ce: equilibrium metal concentration in solution (mg/L or mmol/L)
    qmax: maximum monolayer sorption capacity (mg/g or mmol/g)
    b: Langmuir affinity constant (L/mg or L/mmol)
    """
    Ce = np.asarray(Ce, dtype=float)
    return qmax * b * Ce / (1.0 + b * Ce)


def freundlich_isotherm(Ce, Kf, n):
    """
    Freundlich isotherm: qe = Kf * Ce^(1/n)
    n > 1 indicates favorable sorption; n=1 is linear (Henry's law) regime.
    """
    Ce = np.asarray(Ce, dtype=float)
    return Kf * Ce ** (1.0 / n)


def fit_langmuir(Ce_data, qe_data):
    """
    Linearized Langmuir fit: Ce/qe = 1/(qmax*b) + Ce/qmax
    Standard linearization used throughout the biosorption literature.
    Returns (qmax, b, r_squared).
    """
    Ce_data = np.asarray(Ce_data, dtype=float)
    qe_data = np.asarray(qe_data, dtype=float)
    y = Ce_data / qe_data
    slope, intercept = np.polyfit(Ce_data, y, 1)
    qmax = 1.0 / slope
    b = slope / intercept
    y_pred = slope * Ce_data + intercept
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - ss_res / ss_tot
    return qmax, b, r_squared


def fit_freundlich(Ce_data, qe_data):
    """
    Linearized Freundlich fit: ln(qe) = ln(Kf) + (1/n) ln(Ce)
    Returns (Kf, n, r_squared).
    """
    Ce_data = np.asarray(Ce_data, dtype=float)
    qe_data = np.asarray(qe_data, dtype=float)
    x = np.log(Ce_data)
    y = np.log(qe_data)
    slope, intercept = np.polyfit(x, y, 1)
    n = 1.0 / slope
    Kf = np.exp(intercept)
    y_pred = slope * x + intercept
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - ss_res / ss_tot
    return Kf, n, r_squared


# ---------------------------------------------------------------------------
# 2. Kinetics
# ---------------------------------------------------------------------------
def pseudo_first_order(t, qe, k1):
    """Lagergren (1898): q(t) = qe * (1 - exp(-k1 * t))"""
    t = np.asarray(t, dtype=float)
    return qe * (1.0 - np.exp(-k1 * t))


def pseudo_second_order(t, qe, k2):
    """
    Ho & McKay (1999): q(t) = qe^2 * k2 * t / (1 + qe * k2 * t)
    Empirically the more commonly dominant kinetic model for biosorption
    of metal ions onto biological materials (chemisorption-like behavior).
    """
    t = np.asarray(t, dtype=float)
    return (qe ** 2 * k2 * t) / (1.0 + qe * k2 * t)


def fit_pseudo_second_order(t_data, q_data):
    """
    Linearized PSO fit: t/q = 1/(k2*qe^2) + t/qe
    Returns (qe, k2, r_squared).
    """
    t_data = np.asarray(t_data, dtype=float)
    q_data = np.asarray(q_data, dtype=float)
    y = t_data / q_data
    slope, intercept = np.polyfit(t_data, y, 1)
    qe = 1.0 / slope
    k2 = slope ** 2 / intercept
    y_pred = slope * t_data + intercept
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - ss_res / ss_tot
    return qe, k2, r_squared


# ---------------------------------------------------------------------------
# 3. pH dependence (sigmoid rise + optional high-pH falloff)
# ---------------------------------------------------------------------------
def ph_biosorption_factor(pH, pH50=3.5, steepness=2.0, pH_precip_onset=6.0,
                            precip_steepness=3.0, sorbate_type="cationic"):
    """
    Normalized [0,1] pH activity factor.

    sorbate_type="cationic" (e.g. Cu2+, Ni2+, Co2+, REE3+, Li+):
      sigmoid RISE around pH50 (deprotonation of surface carboxyl/phosphate
      groups, pKa range ~3-5 typical for biomass) then sigmoid FALL above
      pH_precip_onset (metal hydroxide precipitation starts competing with
      surface binding). This is the commonly reported bell/plateau shape
      for cationic metal biosorption pH-edge studies.

    sorbate_type="anionic_complex" (e.g. Au(CN)2-, PtCl4^2-, other anionic
      metal-ligand complexes typical of cyanide leach liquors):
      the MECHANISM IS DIFFERENT and roughly inverted: uptake is favored at
      LOW pH, where amine/imine surface groups on the biomass are
      protonated (-NH3+) and act as an anion exchanger for the negatively
      charged metal complex; uptake falls as pH rises and those groups
      deprotonate. This is the well-documented pattern in the gold-cyanide
      / chitosan-type biosorbent literature (Guibal and co-workers, among
      others) -- do NOT use the cationic curve for anionic complexes.

    Exact pH50 / pH_precip_onset values are system (metal + biomass)
    specific and should be fitted from your own pH-edge assay data.
    """
    pH = np.asarray(pH, dtype=float)
    if sorbate_type == "cationic":
        rise = 1.0 / (1.0 + np.exp(-steepness * (pH - pH50)))
        fall = 1.0 / (1.0 + np.exp(precip_steepness * (pH - pH_precip_onset)))
        return rise * fall
    elif sorbate_type == "anionic_complex":
        # Mirrored: high activity at low pH (protonated amine sites),
        # falling off as pH rises past the amine pKa (~pH50 here reused
        # as the amine deprotonation midpoint, typically pH ~5-7 for
        # chitosan-type materials -- pass a higher pH50 for this case).
        fall = 1.0 / (1.0 + np.exp(steepness * (pH - pH50)))
        return fall
    else:
        raise ValueError('sorbate_type must be "cationic" or "anionic_complex"')


# ---------------------------------------------------------------------------
# 3b. Illustrative literature-range presets by target metal/system.
#     THESE ARE ORDER-OF-MAGNITUDE STARTING POINTS, NOT VALIDATED qFoldIT
#     DATA. Replace every field with your own fitted values as soon as you
#     have equilibrium/kinetic assay data for that system (use fit_langmuir,
#     fit_freundlich, fit_pseudo_second_order above).
# ---------------------------------------------------------------------------
METAL_PRESETS = {
    "gold_cyanide": {
        # Au(CN)2- anionic complex, typical target for chitosan-type or
        # amine-functionalized biosorbents in cyanide leach liquors.
        "sorbate_type": "anionic_complex",
        "qmax": 80.0,      # mg/g -- chitosan-type sorbents can reach much
                            # higher (100s of mg/g) with optimized material;
                            # generic biomass is typically lower.
        "b": 0.02,          # L/mg
        "k2": 0.0008,       # g/(mg*min)
        "pH50": 5.5,        # amine deprotonation midpoint -- uptake favored
                            # BELOW this pH
        "steepness": 1.5,
        "notes": "Anionic complex mechanism -- low pH favors uptake, "
                 "opposite of cationic metals. Verify against your own "
                 "biomass/pH-edge data; chitosan-specific literature values "
                 "will not directly transfer to a different biosorbent.",
    },
    "copper_cationic": {
        "sorbate_type": "cationic",
        "qmax": 40.0,       # mg/g
        "b": 0.06,          # L/mg
        "k2": 0.0018,       # g/(mg*min)
        "pH50": 4.0,
        "steepness": 2.0,
        "pH_precip_onset": 5.5,  # Cu(OH)2 precipitation begins ~pH 5.5-6
        "precip_steepness": 3.0,
        "notes": "Typical order-of-magnitude for Cu2+ biosorption onto "
                 "algal/fungal biomass. Precipitation onset is notably "
                 "LOWER than for REE -- narrower usable pH window.",
    },
    "ree_trivalent": {
        # Generic trivalent lanthanide (La3+, Nd3+, etc.) -- REE group
        # behaves similarly to each other to first order; a specific
        # element's affinity constant will differ somewhat within the
        # series (lanthanide contraction effects).
        "sorbate_type": "cationic",
        "qmax": 55.0,       # mg/g
        "b": 0.05,          # L/mg
        "k2": 0.0012,       # g/(mg*min)
        "pH50": 4.2,
        "steepness": 2.0,
        "pH_precip_onset": 6.5,  # REE(OH)3 precipitation typically ~pH 6.5-7.5
        "precip_steepness": 2.5,
        "notes": "Generic trivalent REE placeholder -- La/Nd/Ce/Dy etc. "
                 "differ in affinity within the series (lanthanide "
                 "contraction). Use a per-element preset once you know "
                 "which REE(s) are the commercial target.",
    },
    "lithium_cationic": {
        "sorbate_type": "cationic",
        "qmax": 8.0,        # mg/g -- NOTE: much lower than transition
                            # metals/REE. Li+ is a small, hard, poorly
                            # complexed ion; classical biosorption is
                            # generally WEAK for Li+ compared to
                            # ion-exchange/sorbent (e.g. lithium-manganese
                            # oxide, LDH) processes used industrially.
        "b": 0.01,          # L/mg
        "k2": 0.0025,       # g/(mg*min)
        "pH50": 5.0,
        "steepness": 1.5,
        "pH_precip_onset": 10.0,  # LiOH precipitation is a high-pH, high-
                                   # concentration phenomenon -- rarely the
                                   # limiting factor in practice.
        "precip_steepness": 2.0,
        "notes": "CAUTION: biosorption is generally a weak, low-capacity "
                 "route for Li+ recovery compared to purpose-built "
                 "ion-exchange/adsorbent (LDH, lithium-manganese-oxide) "
                 "technologies used industrially for brine. If Li recovery "
                 "is commercially important, validate early whether "
                 "biosorption gives economically relevant qmax at all "
                 "before investing further modeling effort here.",
    },
}


def get_preset(name):
    """Look up a metal/system preset by name. Raises KeyError with the
    available options listed if the name isn't found."""
    if name not in METAL_PRESETS:
        raise KeyError(f"Unknown preset '{name}'. Available: {list(METAL_PRESETS.keys())}")
    return METAL_PRESETS[name]


# ---------------------------------------------------------------------------
# 4. Combined predictive model: uptake q(t) at given Ce, pH
# ---------------------------------------------------------------------------
def predict_uptake_curve(t, Ce, pH, qmax, b, k2, pH50=3.5, steepness=2.0,
                          pH_precip_onset=6.0, precip_steepness=3.0,
                          sorbate_type="cationic"):
    """
    qe(Ce) from Langmuir equilibrium x pH activity factor gives the
    pH-adjusted equilibrium capacity; PSO kinetics governs approach to
    that equilibrium over time.

    sorbate_type: "cationic" or "anionic_complex" -- see ph_biosorption_factor.
    """
    qe_base = langmuir_isotherm(Ce, qmax, b)
    f_pH = ph_biosorption_factor(pH, pH50, steepness, pH_precip_onset,
                                   precip_steepness, sorbate_type)
    qe_eff = qe_base * f_pH
    q_t = pseudo_second_order(t, qe_eff, k2)
    return q_t, qe_eff


def predict_uptake_from_preset(t, Ce, pH, preset_name):
    """Convenience wrapper: predict_uptake_curve using a METAL_PRESETS entry."""
    p = get_preset(preset_name)
    kwargs = {k: v for k, v in p.items() if k != "notes"}
    return predict_uptake_curve(t, Ce, pH, **kwargs)
