# Model Reference: qfoldit-prospecting

## Scientific basis, and precisely how far it generalizes

Ronholm, J. et al. "DNA sequencing, microbial indicators, and the
discovery of buried kimberlites." *Communications Earth & Environment*
4, 128 (2023). https://doi.org/10.1038/s43247-023-01020-z

This is real, peer-reviewed, 2023 research -- not an invented premise.
Read the numbers below carefully, because they set the honest boundary of
what this method has actually demonstrated:

| Finding | Number | What it means for expectations |
|---|---|---|
| Lab incubation OTU richness drop (kimberlite-amended vs control) | 990±10 → 520±10 (~48% drop) | Kimberlite material measurably suppresses richness under controlled lab conditions |
| Candidate indicator taxa from lab incubation (LEfSe, LDA>2) | 375 total: 65 increasers (17%), 310 decreasers (83%) | Most real indicators are DEPLETED on-deposit, not enriched -- don't assume "indicator" means "grows more" |
| Field site (DO-18) richness, on-deposit vs background | Chao1 1840±80 vs 2600±100 (~29% lower) | Confirms the richness-drop signal replicates in a real field setting, at smaller magnitude than the lab incubation |
| Lab-to-field indicator overlap | 59 of 375 lab indicators observed in field data; only 19 of those matched predicted direction | **Roughly 1/3 replication rate** from lab to field -- most candidate indicators from a lab study will NOT hold up in the field. This is the single most important number for calibrating trust in any indicator list. |
| Blind validation at an independent deposit (Kelvin) | 78 combined indicators successfully resolved the kimberlite's surface expression | The method worked prospectively in this one case |
| Randomization/chance check | 7 of 10 random (non-indicator) taxon sets showed no spatial correlation | The real indicator signal is distinguishable from chance, but not overwhelmingly -- 3/10 random sets still showed some correlation |

**Scope of demonstrated validity: ONE mineral system (diamondiferous
kimberlite), ONE broad setting (Canadian subarctic tundra/till
overburden).** There is no published evidence in this source that the
method transfers to gold, copper, lithium, or REE exploration, or to
different soil/climate types. Treat any application to those systems as
an untested extrapolation, not a validated use case, until qFoldIT (or
someone) runs and publishes an equivalent study for those systems.

---

## Statistical methods implemented (`scripts/prospecting_stats.py`)

| Function | Method | Basis |
|---|---|---|
| `chao1_richness` | S_obs + F1(F1-1)/(2(F2+1)) | Chao (1984) |
| `inverse_simpson` | 1/Σp_i² | standard ecology diversity index |
| `response_ratio` | (mean_target/mean_other - 1)×100 | matches source paper's convention |
| `indicator_taxa_analysis` | per-taxon Mann-Whitney U + response ratio | simplified analog to LEfSe (Segata et al. 2011) -- NOT a reimplementation of LEfSe's actual LDA effect size |
| `anomaly_score` | signed sum of normalized indicator abundances | original, simple, transparent scoring rule -- not the source paper's spatial-heatmap statistic |
| `hierarchical_cluster` | UPGMA (average-linkage) on Euclidean distance | matches general approach in source study |
| `permutation_validity_test` | empirical p-value vs. random taxon sets of equal size | generalizes the source study's 10-random-set randomization check into a proper permutation test |

### A bug found and fixed during this skill's own development (disclosed, not hidden)

`indicator_taxa_analysis` originally inferred which group was "on-deposit"
from `np.unique(group_labels)` ordering. **`np.unique` sorts
alphabetically** -- for labels `["on_deposit", "background"]`,
`"background"` sorts first. This silently swapped every taxon's
increaser/decreaser label. Verified with a planted-signal synthetic test:
5 taxa deliberately suppressed in the on-deposit group were reported as
"increasers" with response ratios of +1700% to +2900% -- the exact
opposite of the truth. **Fixed** by making `target_group` a required,
explicit parameter (no inference from ordering). Re-verified after the
fix: all 10 planted taxa (5 increasers, 5 decreasers) were correctly
labeled; swapping `target_group` correctly flips the sign; an invalid
`target_group` value raises a hard error rather than silently doing
something.

### Validated qualitative behavior (tests run during development)

- **Chao1**: a sample with more singletons/doubletons produces a higher
  estimate above observed richness than one with fewer (verified:
  S_obs=7 with 2 singletons → Chao1=8.0; S_obs=11 with more rare taxa →
  Chao1=13.0), consistent with the estimator's purpose (correcting for
  undersampled rare taxa).
- **Inverse Simpson**: an even community (5 taxa at equal abundance)
  scores higher (5.0, the theoretical maximum for 5 equally-abundant
  taxa) than a skewed community with the same richness (one dominant
  taxon + 4 rare ones scores 1.18) -- confirms sensitivity to evenness,
  not just richness.
- **Indicator taxa analysis**: recovered all 10 of 10 deliberately
  planted signal taxa (5 increasers, 5 decreasers) from synthetic data
  with correct direction labels, after the bug above was fixed.
- **Anomaly scoring**: correctly ranked a true on-deposit sample (0.335)
  higher than a true background sample (0.009) using the discovered
  indicator set.
- **Hierarchical clustering**: achieved 100% agreement with true group
  labels on the synthetic planted-signal dataset (a strong, clean signal
  case -- real field data with a weaker signal, per the lab-to-field
  replication numbers above, should be expected to cluster far less
  cleanly).
- **Permutation validity test**: correctly assigned a low empirical
  p-value (0.008) to the real planted indicator set, and a high,
  non-significant empirical p-value (0.538) to a random, non-informative
  taxon set of the same size -- confirming the test discriminates real
  signal from noise as intended.

### Scope limits

- No raw-read processing (see SKILL.md's two-part pipeline note) --
  needs an abundance table as input, not FASTQ files.
- `indicator_taxa_analysis` does not apply multiple-testing correction
  automatically -- disclosed in the function docstring and in SKILL.md
  instructions; apply FDR correction yourself for datasets with many taxa.
- The Mann-Whitney + response-ratio approach is a simpler substitute for
  the published LEfSe method, not a reimplementation of it -- results are
  not numerically comparable to a published LEfSe LDA score.
- `anomaly_score` is an original, simple scoring rule for this skill, not
  a reproduction of the source paper's spatial anomaly-mapping statistics.
