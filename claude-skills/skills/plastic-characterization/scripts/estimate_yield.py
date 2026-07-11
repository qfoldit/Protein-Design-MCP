#!/usr/bin/env python3
"""
Estimates pyrolysis product yield for a plastic mixture, based on
averaged literature ranges for pure polymers.

IMPORTANT: this is an estimation calculator based on reference ranges,
not a model trained on real data. The result is a range, not a precise
number. See references/pyrolysis_yields.md.
"""

import argparse
import json

# (oil_min, oil_max, gas_min, gas_max, char_min, char_max) in wt.%
POLYMER_RANGES = {
    "pe":    (70, 85, 10, 25, 1, 5),
    "pp":    (70, 80, 15, 25, 1, 5),
    "ps":    (60, 80, 5, 15, 5, 15),
    "pet":   (20, 40, 15, 30, 30, 40),
    "pvc":   (30, 45, 20, 30, 15, 25),
    "other": (40, 60, 15, 30, 10, 30),
}

CHLORINE_TRANSFER_MIN = 0.5  # fraction of original PVC chlorine transferring to oil (min.)
CHLORINE_TRANSFER_MAX = 0.7  # (max., without upstream dechlorination)


def weighted_range(composition: dict) -> dict:
    total = sum(composition.values())
    if total <= 0:
        raise ValueError("Sum of composition fractions must be greater than zero")
    # normalize in case percentages don't add up to exactly 100
    norm = {k: v / total for k, v in composition.items()}

    oil_min = oil_max = gas_min = gas_max = char_min = char_max = 0.0
    for polymer, frac in norm.items():
        if frac <= 0:
            continue
        ranges = POLYMER_RANGES.get(polymer, POLYMER_RANGES["other"])
        oil_min += frac * ranges[0]
        oil_max += frac * ranges[1]
        gas_min += frac * ranges[2]
        gas_max += frac * ranges[3]
        char_min += frac * ranges[4]
        char_max += frac * ranges[5]

    pvc_frac = norm.get("pvc", 0.0) * 100  # in %
    chlorine_min = pvc_frac * CHLORINE_TRANSFER_MIN
    chlorine_max = pvc_frac * CHLORINE_TRANSFER_MAX

    # simple heuristic for coking/catalyst-poisoning risk:
    # higher PET/PVC/other fraction -> higher risk (arbitrary 0-100 scale)
    fouling_risk_score = round(
        100 * (norm.get("pet", 0) * 0.9 + norm.get("pvc", 0) * 1.0 + norm.get("other", 0) * 0.5
               + norm.get("ps", 0) * 0.3), 1
    )

    recommendations = []
    if pvc_frac >= 3:
        recommendations.append(
            f"PVC fraction {pvc_frac:.1f}% — an upstream dechlorination step is recommended "
            f"(low-temperature heating at 300-350°C) before the main pyrolysis step, otherwise the "
            f"expected chlorine content in the oil ({chlorine_min:.1f}-{chlorine_max:.1f}% of original chlorine) "
            f"may render the oil unsuitable for many applications without further refining."
        )
    if norm.get("pet", 0) * 100 >= 15:
        recommendations.append(
            "High PET fraction — expect elevated solid/acidic product yield; "
            "consider pre-sorting or a separate stream for PET."
        )
    if fouling_risk_score >= 40:
        recommendations.append(
            "Estimated coking/catalyst-deactivation risk is elevated — "
            "more frequent reactor cleaning is recommended, or reduce the PET/PVC/other fraction in the batch."
        )
    if not recommendations:
        recommendations.append(
            "Mixture composition is favorable (PE/PP-dominant) — standard pyrolysis parameters "
            "of 450-500°C should give stable oil yield without special preparation."
        )

    return {
        "assumptions": (
            "Estimate based on averaged literature ranges for pyrolysis product yield of "
            "PURE polymers at 450-550°C without a catalyst. Does not account for possible "
            "synergistic effects during co-pyrolysis of the mixture. Requires calibration "
            "against real laboratory runs before use in industrial planning."
        ),
        "input_composition_normalized_pct": {k: round(v * 100, 1) for k, v in norm.items() if v > 0},
        "oil_yield_pct_range": [round(oil_min, 1), round(oil_max, 1)],
        "gas_yield_pct_range": [round(gas_min, 1), round(gas_max, 1)],
        "char_residue_pct_range": [round(char_min, 1), round(char_max, 1)],
        "chlorine_in_oil_pct_of_original_range": [round(chlorine_min, 2), round(chlorine_max, 2)],
        "fouling_risk_score_0_100": fouling_risk_score,
        "recommendations": recommendations,
    }


def main():
    parser = argparse.ArgumentParser(description="Estimate pyrolysis product yield for a plastic mixture")
    parser.add_argument("--pe", type=float, default=0, help="PE fraction, wt.%")
    parser.add_argument("--pp", type=float, default=0, help="PP fraction, wt.%")
    parser.add_argument("--ps", type=float, default=0, help="PS fraction, wt.%")
    parser.add_argument("--pet", type=float, default=0, help="PET fraction, wt.%")
    parser.add_argument("--pvc", type=float, default=0, help="PVC fraction, wt.%")
    parser.add_argument("--other", type=float, default=0, help="Other polymers fraction, wt.%")
    args = parser.parse_args()

    composition = {
        "pe": args.pe, "pp": args.pp, "ps": args.ps,
        "pet": args.pet, "pvc": args.pvc, "other": args.other,
    }
    result = weighted_range(composition)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
