#!/usr/bin/env python3
"""
A qualitative heuristic plant growth model based on nutrition (NPK)
and light spectrum/intensity. NOT trained on real data — built on
general, widely-documented plant physiology principles (Liebig's law
of the minimum, macronutrient deficiency symptoms, DLI, R:FR, the
shade-avoidance syndrome). See references/plant_physiology_basis.md.

Can optionally output parameters for integration with the
"qfoldit-l-systems" skill (modifying step length/preset choice based
on the computed morphology).
"""

import argparse
import json


def clip(v, lo, hi):
    return max(lo, min(hi, v))


def nutrient_index(actual, optimal):
    """0..~1.3: 1.0 = optimum, <1.0 = deficiency, slightly >1.0 = mild excess (no harm)."""
    if optimal <= 0:
        return 1.0
    ratio = actual / optimal
    return clip(ratio, 0.0, 1.3)


def light_factor(dli, dli_optimal=20.0):
    """Saturating growth function of DLI. At DLI >> optimal — photoinhibition (penalty)."""
    if dli <= 0:
        return 0.0
    x = dli / dli_optimal
    if x <= 1.0:
        return x  # linear growth up to the optimum
    # past the optimum — saturation and a mild penalty at strong excess
    excess = x - 1.0
    penalty = clip(1.0 - 0.15 * max(0.0, excess - 0.5), 0.5, 1.0)
    return clip(1.0 * penalty, 0.0, 1.0)


def compute(
    n_ppm, p_ppm, k_ppm,
    n_optimal, p_optimal, k_optimal,
    ppfd, photoperiod_hours,
    red_frac, blue_frac, far_red_frac, uv_frac,
    dli_optimal=20.0,
):
    n_idx = nutrient_index(n_ppm, n_optimal)
    p_idx = nutrient_index(p_ppm, p_optimal)
    k_idx = nutrient_index(k_ppm, k_optimal)

    limiting = min(n_idx, p_idx, k_idx)
    limiting_nutrient = {"N": n_idx, "P": p_idx, "K": k_idx}
    limiting_name = min(limiting_nutrient, key=limiting_nutrient.get)

    dli = ppfd * photoperiod_hours * 3600 / 1_000_000  # mol/m2/day
    lf = light_factor(dli, dli_optimal)

    growth_rate_index = round(100 * limiting * lf, 1)

    # R:FR (avoid division by 0)
    r_fr_ratio = red_frac / far_red_frac if far_red_frac > 0 else 5.0  # 5.0 ~ "pure red, no FR"

    # shade avoidance syndrome: the lower R:FR is relative to ~1.2, the stronger the elongation
    shade_avoidance = clip((1.2 - r_fr_ratio) * 1.5, 0.0, 1.0)  # 0..1
    internode_length_multiplier = round(1.0 + shade_avoidance * 0.8, 2)  # up to +80% internode length
    branching_density_multiplier = round(1.0 - shade_avoidance * 0.5, 2)  # less branching in shade

    # blue fraction -> compactness and leaf thickness/density
    compactness_index = round(clip(blue_frac * 2.0, 0.0, 1.0), 2)  # 0..1, higher = more compact
    internode_length_multiplier = round(internode_length_multiplier * (1.0 - 0.3 * compactness_index), 2)

    # deficiency symptoms (qualitative flags)
    symptoms = []
    if n_idx < 0.7:
        symptoms.append("Nitrogen starvation: expect chlorosis of lower/older leaves, thin stems, slowed growth.")
    if n_idx > 1.15:
        symptoms.append("Nitrogen excess: expect excessive vegetative mass, delayed flowering, weakened tissue.")
    if p_idx < 0.7:
        symptoms.append("Phosphorus starvation: slowed growth, dark green/purple leaf color (anthocyanins), delayed maturity.")
    if k_idx < 0.7:
        symptoms.append("Potassium starvation: risk of necrosis/leaf-edge 'scorch', weak stems, lodging risk.")
    if not symptoms:
        symptoms.append("No clear signs of macronutrient deficiency/excess expected at the given levels.")

    # secondary metabolites (anthocyanins/flavonoids) — qualitative stress index
    nutrient_stress = round((1 - n_idx) * 0.4 + (1 - p_idx) * 0.4, 2)
    nutrient_stress = clip(nutrient_stress, 0.0, 1.0)
    light_stress = clip(uv_frac * 3.0 + max(0.0, dli / dli_optimal - 1.5) * 0.3, 0.0, 1.0)
    secondary_metabolite_stress_index = round(clip(nutrient_stress * 0.6 + light_stress * 0.4, 0.0, 1.0) * 100, 1)

    return {
        "assumptions": (
            "Qualitative heuristic model based on general plant physiology principles "
            "(Liebig's law of the minimum, DLI saturation, R:FR-based shade avoidance syndrome, "
            "blue-light fraction and growth compactness). NOT calibrated on data for a specific "
            "species/installation. See references/plant_physiology_basis.md."
        ),
        "nutrient_indices": {"N": n_idx, "P": p_idx, "K": k_idx},
        "limiting_nutrient": limiting_name,
        "dli_mol_m2_day": round(dli, 2),
        "light_factor_0_1": round(lf, 2),
        "growth_rate_index_0_100": growth_rate_index,
        "r_fr_ratio": round(r_fr_ratio, 2),
        "shade_avoidance_0_1": round(shade_avoidance, 2),
        "morphology": {
            "internode_length_multiplier": internode_length_multiplier,
            "branching_density_multiplier": branching_density_multiplier,
            "compactness_index_0_1": compactness_index,
        },
        "deficiency_symptoms": symptoms,
        "secondary_metabolite_stress_index_0_100": secondary_metabolite_stress_index,
    }


def to_lsystem_params(result, base_preset="plant", base_step=1.0, base_angle=25.0):
    """Converts the model result into parameters for qfoldit-l-systems/scripts/lsystem.py."""
    morph = result["morphology"]
    step = round(base_step * morph["internode_length_multiplier"], 3)
    # less branching -> prefer a more "elongated" preset; more -> bushier
    preset = "bush" if morph["compactness_index_0_1"] >= 0.5 else base_preset
    # slightly reduce the angle under strong shade avoidance (more elongated, less sprawling form)
    angle = round(base_angle * (1.0 - 0.2 * result["shade_avoidance_0_1"]), 1)
    # iterations based on the growth index: weak growth -> less "developed" structure
    growth = result["growth_rate_index_0_100"]
    iterations = 3 if growth < 30 else (4 if growth < 65 else 5)
    color_hint = "#7a4a8f" if result["secondary_metabolite_stress_index_0_100"] >= 50 else "#2f6b3a"

    return {
        "suggested_lsystem_cli": (
            f"python3 ../../qfoldit-l-systems/scripts/lsystem.py --preset {preset} "
            f"--angle {angle} --iterations {iterations} --step {step} --out plant_result.svg"
        ),
        "preset": preset,
        "angle": angle,
        "iterations": iterations,
        "step": step,
        "note_stroke_color": color_hint,
        "note": (
            "Color is just a hint (needs to be passed manually into segments_to_svg, since "
            "lsystem.py doesn't yet accept color via the CLI). A purple tint is suggested at a "
            "high secondary-metabolite stress index (symbolizing anthocyanin accumulation)."
        ),
    }


def main():
    parser = argparse.ArgumentParser(description="Plant growth model based on NPK and light spectrum")
    parser.add_argument("--n", type=float, required=True, help="Nitrogen level, ppm (or relative units)")
    parser.add_argument("--p", type=float, required=True, help="Phosphorus level, ppm")
    parser.add_argument("--k", type=float, required=True, help="Potassium level, ppm")
    parser.add_argument("--n-optimal", type=float, default=150.0, help="Optimal N level (default rough value 150 ppm)")
    parser.add_argument("--p-optimal", type=float, default=50.0, help="Optimal P level (default rough value 50 ppm)")
    parser.add_argument("--k-optimal", type=float, default=200.0, help="Optimal K level (default rough value 200 ppm)")
    parser.add_argument("--ppfd", type=float, required=True, help="PPFD, μmol/m2/s (light intensity)")
    parser.add_argument("--photoperiod", type=float, required=True, help="Photoperiod, hours of light per day")
    parser.add_argument("--red-frac", type=float, default=0.4, help="Red light fraction (400-700nm spectrum), 0-1")
    parser.add_argument("--blue-frac", type=float, default=0.2, help="Blue light fraction, 0-1")
    parser.add_argument("--far-red-frac", type=float, default=0.05, help="Far-red fraction (700-750nm), 0-1")
    parser.add_argument("--uv-frac", type=float, default=0.0, help="UV fraction, 0-1")
    parser.add_argument("--dli-optimal", type=float, default=20.0, help="Optimal DLI for the species, mol/m2/day")
    parser.add_argument("--emit-lsystem-params", action="store_true", help="Additionally output parameters for the qfoldit-l-systems skill")
    args = parser.parse_args()

    result = compute(
        n_ppm=args.n, p_ppm=args.p, k_ppm=args.k,
        n_optimal=args.n_optimal, p_optimal=args.p_optimal, k_optimal=args.k_optimal,
        ppfd=args.ppfd, photoperiod_hours=args.photoperiod,
        red_frac=args.red_frac, blue_frac=args.blue_frac,
        far_red_frac=args.far_red_frac, uv_frac=args.uv_frac,
        dli_optimal=args.dli_optimal,
    )

    if args.emit_lsystem_params:
        result["lsystem_integration"] = to_lsystem_params(result)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
