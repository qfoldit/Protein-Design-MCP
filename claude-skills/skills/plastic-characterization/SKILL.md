---
name: qfoldit-plastic-characterization
description: Estimates pyrolysis behavior (oil/gas/char yield ranges, chlorine risk, catalyst-fouling risk) for a given mixed-plastic feedstock composition (PE, PP, PS, PET, PVC, other), and suggests reactor parameter adjustments (temperature, residence time, catalyst use). Use this skill whenever the user asks about plastic pyrolysis feedstock, plastic-to-fuel conversion, mixed plastic waste characterization, expected pyrolysis oil yield/quality, or wants to know how a specific plastic mix will behave in a pyrolysis reactor. Also trigger for questions about chlorine contamination risk from PVC in feedstock, or how to adjust pyrolysis parameters for a given waste stream.
---

# Plastic Characterization (pyrolysis feedstock estimator)

## What this skill does

Gives an **estimated** (not a precise prediction from a trained model) range of pyrolysis products for a plastic mixture, based on published literature yield ranges for the main polymer types. This is a reference-data-based calculator, not a proprietary ML model — the result should be presented to the user that way.

**Important:** this skill does NOT implement the `autoresearch` / `quantum-adapter` piece (a real-time reactor-parameter optimizer trained on real runs) — that is a separate, much harder task requiring real data from a specific reactor for calibration. Do not present heuristic estimates as the output of such an optimizer.

## When to use

- The user describes a batch of plastic waste composition (in % of PE, PP, PS, PET, PVC, other) and asks about expected oil/gas/char yield.
- The user asks about chlorine contamination risk in the oil (from PVC) or reactor coking/fouling risk.
- The user asks for a recommended temperature/residence time for a specific feedstock batch.

## How to work

1. Gather the batch composition (mass fractions of PE / PP / PS / PET / PVC / other). If the user gives incomplete data, explicitly state what assumptions you're making (e.g. "other = mixed polymers, using averaged literature values").
2. Run `scripts/estimate_yield.py` with the composition as input (see example below).
3. Read `references/pyrolysis_yields.md` if you need to explain to the user where the ranges come from and what literature they're based on.
4. Always present the result as a **range**, not a precise number, and explicitly state: "this is an estimate based on averaged literature data for pure-polymer pyrolysis at 450-550°C, not the result of training on data from a specific reactor. Industrial deployment requires calibration against real runs."
5. If the user asks for "the exact percentage oil yield" — don't fabricate precision that doesn't exist; offer a range and explain that only a test run on the real feedstock can narrow it.

## Example call

```bash
python3 scripts/estimate_yield.py --pe 40 --pp 20 --ps 10 --pet 15 --pvc 5 --other 10
```

Output — JSON with oil/gas/char yield ranges, an estimate of chlorine content in the oil, and process-parameter recommendations (see the code for field details).

## Limitations (must be communicated to the user)

- The ranges in `references/pyrolysis_yields.md` are averaged from widely-cited laboratory experiments on pyrolysis of *pure* polymers. Real mixture behavior can differ due to interactions between polymers (synergistic/antagonistic effects during co-pyrolysis) that this simple model does not account for.
- The chlorine estimate is a rough one (PVC fraction × typical HCl/organic-chlorine yield), not a substitute for laboratory oil analysis.
- This is a tool for first-pass estimates and presentations, not for reactor engineering design without subsequent empirical verification.
