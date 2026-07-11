---
name: qfoldit-prospecting
description: Statistical analysis of soil/overburden microbial community data (16S rRNA amplicon or shotgun metagenomic sequencing) for biogeochemical mineral exploration -- diversity indices (Chao1, inverse Simpson), indicator taxon identification, response-ratio effect sizes, anomaly scoring, hierarchical clustering, and a permutation-based validity check for whether an indicator signal could be due to chance. Use whenever the user asks about microbial indicator species for mineral exploration, biogeochemical prospecting, soil/overburden microbiome analysis over an ore body, mining-prospecting, or wants to know whether candidate indicator taxa actually separate on-deposit from background samples. Trigger even if the user just provides an OTU/ASV abundance table with group labels and asks what it means for exploration, without saying "biogeochemical" or "indicator species". Does NOT process raw sequencing reads (FASTQ) -- starts from an already-generated abundance table (e.g. QIIME2/Mothur output).
---

# qfoldit-prospecting

Statistical analysis layer for microbial-community-based mineral
exploration ("biogeochemical prospecting"). Given an abundance table
(samples x taxa) with group labels, this skill computes diversity
indices, screens for candidate indicator taxa, scores new samples, and
critically, checks whether the indicator signal is actually
distinguishable from chance -- because the source literature this is
based on found that it often isn't, for a meaningful fraction of
candidates.

**Read `references/model_documentation.md` before answering** -- it
covers the real scientific basis (a 2023 peer-reviewed kimberlite study),
exactly how far that evidence generalizes (one mineral system, one
climate/soil setting), and the specific numbers from that study that
should calibrate expectations (e.g. only 19 of 59 candidate indicators
replicated from lab to field).

## Two-part pipeline -- know which part you're in

1. **Raw reads -> abundance table**: demultiplexing, quality filtering,
   OTU clustering or ASV denoising (DADA2), taxonomic classification
   against a reference database (e.g. SILVA). This requires QIIME2 or
   Mothur and real FASTQ files. **This skill does not do this step.** If
   the user only has raw sequencing files and no abundance table yet,
   say so plainly and explain this is a separate bioinformatics
   pipeline they need to run first (or ask if they have QIIME2/Mothur
   output already).
2. **Abundance table -> exploration signal** (`scripts/prospecting_stats.py`):
   everything this skill actually does. Needs a samples x taxa count
   matrix and group labels (e.g. "on_deposit" vs "background") as input.

## How to handle a request

1. **Check what data the user actually has.** If they describe raw
   sequencing/FASTQ files only, this skill can't proceed until there's
   an abundance table -- don't pretend otherwise.
2. **Always require an explicit `target_group`** when calling
   `indicator_taxa_analysis` -- never infer which group is "on-deposit"
   from label ordering. This is not a minor style point: this exact
   ambiguity produced a real, verified bug during this skill's own
   development (alphabetical sort silently swapped increaser/decreaser
   labels for every taxon). Always ask the user to confirm which group
   label means "on deposit" / "target" if it isn't obvious from the data.
3. **Run indicator discovery**, then **always run
   `permutation_validity_test`** on the resulting indicator set before
   presenting it as meaningful -- do not skip this step even if the
   p-values from `indicator_taxa_analysis` look individually convincing.
   Report the empirical p-value plainly. If it's not significant
   (typically > 0.05), say so directly: this specific indicator set does
   not clearly separate the groups better than chance, for this dataset.
4. **Apply multiple-testing correction context**: `indicator_taxa_analysis`
   does NOT auto-correct for multiple comparisons. If dozens or hundreds
   of taxa were tested, mention that some fraction of "significant" hits
   are expected by chance alone, and suggest FDR correction (e.g.
   Benjamini-Hochberg) before finalizing a list for field use.
5. **Never claim generalization beyond kimberlites without saying so.**
   The published validation is for one mineral system (diamondiferous
   kimberlite) in one setting (Canadian subarctic till/tundra). If the
   user is exploring for gold, copper, lithium, or REE, or in a different
   climate/soil type, say explicitly that this is an extrapolation of the
   method to an untested system, not a validated application.
6. **Report diversity/anomaly numbers with their caveats attached**, not
   as bare figures -- e.g. Chao1 estimates have their own uncertainty
   from rare-taxon undersampling; anomaly scores here are a simple,
   transparent scoring rule chosen for interpretability, not the source
   paper's exact spatial-heatmap statistic.

## Interpreting results

- A statistically "significant" indicator taxon (low p-value) is a
  CANDIDATE, not a confirmed indicator, until it passes the permutation
  validity check and, ideally, replicates in an independent sample set --
  the source study found only about a third of lab-derived candidates
  replicated cleanly in the field.
- Report both DIRECTIONS of change: the source kimberlite study found the
  majority of real indicators were DECREASERS (taxa depleted on-deposit),
  not increasers -- don't let a request implicitly assume "indicator"
  means "something that grows more."
- When comparing multiple candidate deposits/sites, note that anomaly
  scores are only meaningfully comparable if computed with the same
  indicator set and the same normalization convention across sites.

## Testing

See `evals/eval_set.json` for representative test prompts and
`references/model_documentation.md` for validated qualitative behavior
(recovery of a planted signal from synthetic data, direction-labeling
correctness, permutation test discriminating real vs. random taxon sets)
that were run against this code before packaging -- including the
group-labeling bug found and fixed during that testing.
