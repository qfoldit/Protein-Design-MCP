# Model Reference: qfoldit-oilgas (corrosion)

## Equations

| Component | Equation | Basis |
|---|---|---|
| Base nomogram rate | log10(Vnomo) = 5.8 - 1710/T + 0.67·log10(pCO2), T in Kelvin, Vnomo in mm/yr | de Waard, Lotz & Milliams (1991); de Waard & Lotz (1993) |
| Scaling temperature | Tscale (K) = 2400/(6.7 + 0.6·log10(pCO2)) | de Waard's own scaling-temperature formula |
| Scale (protective film) factor | log10(Fscale) = 2400·(1/T - 1/Tscale) for T>Tscale, else 1 | same source |
| Flow enhancement (simplified proxy) | Fflow(v) = floor + (1-floor)·tanh(v/v_ref) | this skill's own simplified stand-in for de Waard 1995's Sherwood-type mass-transfer term -- see caveat below |
| Erosion-corrosion (simplified proxy) | Ferosion(v) = 1 + k·((v-v_erosion)/v_erosion)² for v>v_erosion | illustrative penalty above an API RP 14E-style erosional velocity guideline |
| Pitting risk (salinity-driven) | score = clip(salinity/60, 0, 1) | heuristic screening indicator, not a quantitative pit-growth model |
| Inhibitor effect | rate_inhibited = rate_uninhibited × (1 - efficiency) | standard linear reduction convention |

## Reference-point sanity check

At T=20°C, pCO2=1 bar: hand-calculated log10(Vnomo) = 5.8 - 1710/293.15 + 0 = -0.037, Vnomo ≈ 0.92 mm/yr. **Verified in code: 0.926 mm/yr.** This matches the commonly-cited "roughly 1 mm/yr, uninhibited, at 20°C and 1 bar CO2" figure quoted in multiple secondary engineering references for this correlation.

## Non-monotonic temperature behavior (verified)

At pCO2=1 bar, corrected rate (Vnomo × Fscale) as a function of temperature:

| T (°C) | Vnomo (mm/yr) | Fscale | Corrected rate (mm/yr) |
|---|---|---|---|
| 20 | 0.93 | 1.000 | 0.93 |
| 40 | 2.19 | 1.000 | 2.19 |
| 60 | 4.65 | 1.000 | 4.65 |
| 80 | 9.08 | 1.000 | 9.08 |
| 100 | 16.50 | 0.539 | 8.90 |
| 120 | 28.22 | 0.254 | 7.16 |
| 150 | 57.40 | 0.094 | 5.38 |

Scaling temperature at pCO2=1 bar: **85.1°C** -- the rate peaks near there (between the 80°C and 100°C rows above) and falls at higher temperature as protective scale takes over, exactly the qualitative behavior SKILL.md describes as expected ("do not 'correct' this as if it were an error"). This is a genuine, well-documented phenomenon (FeCO3 scale formation), not a modeling artifact.

## Flow response and erosion regime (verified)

| Velocity (m/s) | Fflow | Ferosion |
|---|---|---|
| 0.01 | 0.307 | 1.000 |
| 0.1 | 0.370 | 1.000 |
| 0.5 | 0.623 | 1.000 |
| 1.0 | 0.833 | 1.000 |
| 3.0 | 0.997 | 1.000 |
| 10.0 | 1.000 | 1.000 |
| 15.0 | 1.000 | 1.375 |
| 20.0 | 1.000 | 2.500 |

Confirms both qualitative regimes: mass-transfer suppression at low velocity (Fflow well below 1 at v<1 m/s), full saturation by v≈3-10 m/s, and an erosion-corrosion penalty kicking in above the 10 m/s default erosional threshold (Ferosion=1.375 at 15 m/s, 2.5 at 20 m/s).

**Caveat, stated plainly**: `flow_enhancement_factor` and `erosion_corrosion_factor` are simplified proxies for the same qualitative behavior the full de Waard 1995 model captures via a genuine Sherwood-type mass-transfer correlation (`1/Vcor = 1/Vr + 1/Vm`, requiring diffusion coefficient, kinematic viscosity, hydraulic diameter). Those extra inputs are outside this skill's stated scope (T, pCO2, velocity, salinity, inhibitor only), so rather than fabricate values for them, this module uses a smooth, physically-reasonable-but-illustrative proxy. Do not present `Fflow`/`Ferosion` numbers as numerically equivalent to a full de Waard 1995 or NORSOK M-506 calculation -- if the user needs that level of fidelity, say so explicitly and recommend the full model with its complete input set.

## Pitting risk vs. salinity (verified monotonic)

| Salinity (ppt) | Score | Category |
|---|---|---|
| 0 | 0.000 | low |
| 5 | 0.083 | low |
| 15 | 0.250 | moderate |
| 25 | 0.417 | moderate |
| 35 | 0.583 | high |
| 50 | 0.833 | high |
| 70 | 1.000 | high |

This is a **screening heuristic**, explicitly not a quantitative pit-growth-rate model -- real pitting susceptibility depends heavily on factors not captured here (under-deposit conditions, weld heat-affected zones, dissolved oxygen ingress, microstructure). Always reported separately from the uniform corrosion rate, never combined into one number (per SKILL.md point 4).

## Inhibitor proportionality (verified)

At T=60°C, pCO2=2 bar, v=2 m/s, salinity=20 ppt: uninhibited rate 7.208 mm/yr; with 85% inhibitor efficiency, inhibited rate 1.081 mm/yr -- ratio 0.150, exactly (1-0.85)=0.15 as expected from the linear reduction model.

## Fitting round-trip (verified)

Simulated a "pipeline" that corrodes 1.8x faster than the generic model predicts (a plausible real-world scenario -- e.g. from unmodeled local turbulence, weld seams, or slightly off-spec metallurgy) across 4 synthetic (T, pCO2, velocity, measured-rate) points. `fit_dewaard_offset_from_data` recovered the exact offset (1.8000, R²=1.0 in log-space). This is the function to use as soon as real coupon/ER-probe/field corrosion data exists for a specific qFoldIT pipeline.

## Calibration status

The base de Waard-Milliams equation is a widely-published, well-established correlation (1991/1993) -- not something qFoldIT invented, and not something requiring "calibration" in the way the scale/flow/pitting proxies do. However:
- The **scale, flow, and erosion factors** in this module are simplified engineering proxies for real, well-documented phenomena, calibrated to generic illustrative shapes (a reference velocity, an erosional threshold, a scaling-temperature formula from the literature) -- not fitted to any specific qFoldIT pipeline.
- The **pitting risk score** is a heuristic screening indicator with illustrative thresholds, not a validated quantitative model.
- Use `fit_dewaard_offset_from_data` as soon as real field/coupon/ER-probe data exists to calibrate a site-specific multiplicative correction -- this is the single most valuable calibration step available, since it captures whatever this simplified model's proxies are missing for a specific pipeline, in one number.

## Scope limits

- Valid range roughly T=5-150°C, pCO2=0.1-10 bar (per de Waard's own stated empirical basis and NORSOK M-506's flow-loop range of 5-160°C) -- flag extrapolation outside this.
- Models sweet (CO2) corrosion only -- not sour (H2S) corrosion, not microbiologically-influenced corrosion (MIC), not oxygen-ingress corrosion. These are different mechanisms requiring different models.
- No explicit pH-shift-from-dissolved-Fe correction (the full de Waard 1991/1993 model's FpH factor) -- omitted because it requires water chemistry inputs (bicarbonate alkalinity, in-situ pH) outside this skill's stated scope. This means predictions here are somewhat more conservative (higher) than the full de Waard model's FpH-corrected output would be, especially at higher Fe++ concentrations. Disclosed rather than silently included as if implemented.
