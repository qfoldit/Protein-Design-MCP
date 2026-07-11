# qFoldIT Oil & Gas Skill — CO2 (Sweet) Pipeline Corrosion

Claude Desktop Skill for internal CO2 corrosion rate prediction and
remaining-wall-life estimation for carbon steel oil & gas pipelines.

## What's inside

```
qfoldit-oilgas/
├── SKILL.md                          — triggers & instructions for Claude
├── README.md                         — this file
├── scripts/
│   └── corrosion_kinetics.py         — de Waard-Milliams model + scale/flow/pitting/inhibitor
├── references/
│   └── model_documentation.md        — full equations, sources, test results
└── evals/
    └── eval_set.json                 — 8 test prompts
```

## Scientific basis

The core model is the **de Waard-Milliams correlation** (de Waard, Lotz &
Milliams, 1991; de Waard & Lotz, 1993) — a widely-published, widely-used
empirical model for internal CO2 corrosion of carbon steel, still a
standard reference point alongside NORSOK M-506 in pipeline integrity
engineering. On top of the base correlation, this module adds:

- **Protective scale suppression**: FeCO3 scale becomes protective above
  a calculable "scaling temperature," producing a genuine non-monotonic
  rate-vs-temperature curve (rises, peaks, then falls) — this is real,
  documented chemistry, not a modeling quirk.
- **Flow/mass-transfer and erosion-corrosion**: a *simplified proxy* (not
  the full de Waard 1995 Sherwood-type equation, which needs inputs this
  skill doesn't collect) capturing the same two qualitative effects:
  mass-transfer-limited corrosion at low velocity, erosion-corrosion
  above a threshold velocity.
- **Pitting risk**: a separate, qualitative 0–1 salinity-driven indicator
  — deliberately never combined into the uniform corrosion rate number,
  since pitting and uniform metal loss are different failure modes.
- **Inhibitor effect**: standard linear efficiency reduction.

## Calibration status — read before trusting a forecast

The base de Waard-Milliams equation itself is an established published
correlation, not something invented for this skill. However, the
**scale, flow, and pitting proxies are simplified engineering
approximations calibrated to generic literature shapes**, not fitted to
any specific qFoldIT pipeline. Use `fit_dewaard_offset_from_data` as soon
as real coupon/ER-probe/field corrosion data exists — verified in testing
to exactly recover a known site-specific offset (1.8x case, R²=1.0 in
log-space) from synthetic data.

**No pH-shift correction** (the full de Waard 1991/1993 model's FpH
factor, which needs water-chemistry inputs like bicarbonate alkalinity)
is included — disclosed explicitly rather than silently implemented, since
it means this module's output runs somewhat more conservative (higher)
than the full published model at higher dissolved-Fe conditions.

## Using this Skill in Claude Desktop

1. Copy the `qfoldit-oilgas/` folder into your Claude Desktop skills
   directory.
2. Ask Claude things like: *"Estimate the corrosion rate for a pipeline
   at 60°C, pCO2 2 bar, flow velocity 2 m/s, salinity 25 ppt, 85%
   inhibitor"* or *"How many years will a 12.7 mm wall pipe last with a
   minimum allowable thickness of 6 mm and a corrosion rate of
   1.08 mm/year?"*
3. Claude will run the model and — per the skill instructions — will
   always report the uniform corrosion rate and pitting risk as separate
   numbers, flag extrapolation outside the correlation's valid range
   (~5-150°C, ~0.1-10 bar), and state whether a generic or site-fitted
   offset was used.

## Testing performed so far

All qualitative behavior below was verified with test scripts before
packaging (see `references/model_documentation.md` for full detail,
including a table of every value):

- Reference-point sanity check (T=20°C, pCO2=1 bar → 0.926 mm/yr) matches
  a hand-calculation and commonly-cited figures for this correlation.
- Non-monotonic temperature response confirmed: rate rises to a peak near
  the calculated scaling temperature (~85°C at pCO2=1 bar), then falls at
  higher T (9.08 mm/yr at 80°C → 7.16 mm/yr at 120°C).
- Flow response confirmed to saturate smoothly with velocity, and the
  erosion-corrosion penalty confirmed to activate only above the
  erosional velocity threshold.
- Pitting risk score confirmed monotonic in salinity.
- Inhibitor effect confirmed exactly proportional (85% efficiency →
  exactly 0.15x remaining rate).
- `fit_dewaard_offset_from_data` confirmed to exactly recover a known
  planted site-specific offset (1.8x, R²=1.0) from synthetic calibration
  data.

**Not yet tested:** anything against real qFoldIT pipeline, coupon, or
ER-probe data — because none has been provided yet. That is the natural
next step before this skill is used to make claims to external parties.
