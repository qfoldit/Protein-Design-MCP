# Plastic Characterization — Skill for Claude

Estimates the pyrolysis behavior of a mixed plastic waste feedstock: expected oil/gas/solid residue yield, chlorine contamination risk from PVC, reactor coking/fouling risk, and process parameter recommendations.

Part of the qFoldIT project — a digital layer on top of existing pyrolysis technologies (Quantafuel, Plastic Energy, etc.), the `plastic-characterization` module.

---

## What this is and isn't

**This is:** an estimated-range calculator based on averaged data widely reproduced in the open literature for pyrolysis of individual ("pure") polymers. A tool for quick first-pass estimation of a feedstock batch, and for presentation/educational purposes.

**This is NOT:** an ML model trained on real industrial data; it does not replace laboratory analysis; it does not give precise numbers for reactor engineering design. It does not include a real-time reactor-parameter optimizer (the `autoresearch` / `quantum-adapter` piece of the broader qFoldIT architecture) — that piece requires calibration against a specific installation's data and is a separate, much harder task.

Every result comes with a range rather than a precise number, and an explicit statement of the source of assumptions — a deliberate choice to avoid creating a false impression of precision where none exists.

---

## Structure

```
plastic-characterization/
├── README.md                       — this file (for humans)
├── SKILL.md                        — instructions for Claude (when and how to use)
├── references/
│   └── pyrolysis_yields.md         — table of literature ranges by polymer + methodology
└── scripts/
    └── estimate_yield.py           — executable calculator (Python 3, no external dependencies)
```

- **SKILL.md** — read by Claude when the skill activates. Contains triggers (when to apply it), step-by-step instructions, and the mandatory caveats Claude must state to the user.
- **README.md** (this file) — for humans: how to install, how to use manually, how to extend.
- **references/pyrolysis_yields.md** — reference data, explanation of where the numbers come from, and methodology caveats.
- **scripts/estimate_yield.py** — can be run directly from the command line, without Claude.

---

## Installation

### In Claude.ai / Claude Desktop / Cowork
Upload the `plastic-characterization.skill.zip` file through the skills management interface (a **Save skill** button appears when opening the file, if your organization allows skill creation). Once installed, Claude will automatically suggest this skill for questions about plastic pyrolysis, feedstock composition, oil yield, etc.

### Manually / for development
```bash
unzip plastic-characterization.skill.zip -d ~/.claude/skills/   # path depends on environment
```
Or simply keep the folder locally and mount it as a skill directory in the relevant environment (Claude Code, Cowork).

---

## Using the script directly (without Claude)

Requirements: Python 3.7+, no external dependencies (standard library only).

```bash
python3 scripts/estimate_yield.py --pe 40 --pp 20 --ps 10 --pet 15 --pvc 5 --other 10
```

Parameters — mixture component fractions in % by mass (don't need to sum to exactly 100; the script normalizes the total):

| Flag | Polymer |
|---|---|
| `--pe` | polyethylene |
| `--pp` | polypropylene |
| `--ps` | polystyrene |
| `--pet` | polyethylene terephthalate |
| `--pvc` | polyvinyl chloride |
| `--other` | other/mixed polymers |

**Output (JSON):**

```json
{
  "assumptions": "...",
  "input_composition_normalized_pct": {...},
  "oil_yield_pct_range": [56.5, 72.2],
  "gas_yield_pct_range": [12.2, 25.5],
  "char_residue_pct_range": [7.3, 14.8],
  "chlorine_in_oil_pct_of_original_range": [2.5, 3.5],
  "fouling_risk_score_0_100": 26.5,
  "recommendations": ["..."]
}
```

| Field | Meaning |
|---|---|
| `oil_yield_pct_range` | Expected oil yield range, % of feedstock mass |
| `gas_yield_pct_range` | Gas fraction yield range |
| `char_residue_pct_range` | Solid residue/char range |
| `chlorine_in_oil_pct_of_original_range` | Fraction of original chlorine (from PVC) that, by rough estimate, will end up in the oil without a dechlorination step |
| `fouling_risk_score_0_100` | Heuristic risk scale for coking/catalyst poisoning (higher = worse) |
| `recommendations` | Text recommendations for feedstock preparation/process parameters |

---

## How to check accuracy and validate before industrial use

This skill **should not** be used as the sole basis for engineering decisions. Recommended validation path:

1. Take 5-10 batches of real feedstock with known composition.
2. Run them through the real pyrolysis process, record the actual oil/gas/residue yield and chlorine content.
3. Compare against the ranges from `estimate_yield.py` — if actual values consistently fall outside the range, adjust the constants in `POLYMER_RANGES` inside the script for your specific equipment (the literature ranges are averaged across different reactor types and may not match your installation).
4. Only after several confirmed runs does it make sense to describe a "calibrated" version of the tool in partner-facing materials.

---

## Known limitations

- The ranges are computed for **pure** polymers individually and simply weighted by their fraction in the mix — the model does not account for possible synergistic/antagonistic effects from co-pyrolyzing different polymers together.
- The chlorine estimate is rough (a linear heuristic), not a substitute for laboratory oil analysis (titration/chromatography).
- Does not account for catalyst effects, heating rate, or the specific reactor design — only feedstock composition and the general 450-550°C temperature range.
- `fouling_risk_score` is a heuristic scale not calibrated against real data; treat it as a rough indicator, not a precise downtime forecast.

---

## How to extend

- To refine the ranges for your installation — edit the `POLYMER_RANGES` dictionary in `scripts/estimate_yield.py`.
- To add a new polymer type (e.g. PU, ABS) — add an entry to `POLYMER_RANGES` and update the table in `references/pyrolysis_yields.md` with the source of the values.
- Once real calibration data exists — it would make sense to replace the fixed ranges with a simple regression (e.g. a linear model on composition) trained on that data, and explicitly label the version as "calibrated on N real runs, date".

---

## Project status

Draft version (v0.1), not validated against real industrial data. Part of the broader qFoldIT project. Fine to use in presentations and at trade shows with an explicit "estimation tool" label, but not as a finished engineering solution until it passes the validation steps above.
