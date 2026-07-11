# qFoldIT Prospecting Skill — Biogeochemical (Microbial Indicator) Mineral Exploration

Claude Desktop Skill for statistical analysis of soil/overburden microbial
community data as an exploration signal for buried mineralization.

## What's inside

```
qfoldit-prospecting/
├── SKILL.md                          — triggers & instructions for Claude
├── README.md                         — this file
├── scripts/
│   └── prospecting_stats.py          — diversity, indicator, anomaly, validity-test functions
├── references/
│   └── model_documentation.md        — full methods, sources, test results, bug disclosure
└── evals/
    └── eval_set.json                 — 6 test prompts
```

## Scientific basis — and its real, stated limits

This skill is built around a genuinely recent finding: **Ronholm et al.
(2023), "DNA sequencing, microbial indicators, and the discovery of
buried kimberlites,"** *Communications Earth & Environment* 4, 128.
Soil microbial community composition measurably shifts above a buried
kimberlite, and a curated set of indicator taxa successfully resolved a
kimberlite's surface expression in a blind field test.

**Read this before using this skill for anything external-facing:** the
published validation covers **one mineral system** (diamondiferous
kimberlite) in **one setting** (Canadian subarctic tundra/till). It has
NOT been demonstrated for gold, copper, lithium, or REE exploration, or
in other soil/climate types. Applying it to qFoldIT's actual target
commodities is an untested extrapolation — the skill is written to say
this explicitly rather than imply otherwise.

**Also important:** in the source study, only **19 of 59** lab-derived
candidate indicators actually replicated (in the correct direction) when
tested in the field — roughly a third. Any indicator list this skill
produces from one dataset should be treated with that same skepticism
until independently validated.

## What this skill does NOT do

It does not process raw sequencing reads. Getting from FASTQ files to an
abundance table (samples x taxa counts) requires a real bioinformatics
pipeline — QIIME2 or Mothur, with quality filtering, OTU/ASV clustering,
and taxonomic classification against a reference database like SILVA.
That is separate, well-established infrastructure this skill does not
reimplement. This skill starts from an abundance table you already have.

## A bug found and fixed during development — disclosed on purpose

The indicator-taxon function originally tried to infer which sample group
was "on-deposit" from label sort order. `np.unique(["on_deposit",
"background"])` sorts alphabetically, putting `"background"` first —
which silently swapped every taxon's increaser/decreaser label. Verified
with a planted-signal test: 5 taxa deliberately suppressed on-deposit
were reported as "increasers" with +1700–2900% response ratios — the
exact opposite of the truth. **Fixed** by making `target_group` a
required, explicit argument; re-verified all directions correct after
the fix. Full details in `references/model_documentation.md`.

## Using this Skill in Claude Desktop

1. Copy the `qfoldit-prospecting/` folder into your Claude Desktop skills
   directory.
2. Ask Claude things like: *"Here's an OTU abundance table from QIIME2
   for 20 soil samples, 10 over the ore body and 10 background — find
   the indicator species"* or *"Check whether biodiversity over the
   deposit differs from background"*.
3. Claude will require you to specify which group is the on-deposit
   target (never inferred), run indicator discovery, and — critically —
   run a permutation validity check before presenting any indicator set
   as meaningful.

## Testing performed so far

- Chao1 and inverse Simpson verified against hand-constructed cases with
  known expected direction (more rare taxa → higher Chao1 correction;
  more even community → higher inverse Simpson at equal richness).
- Indicator taxon analysis: recovered 10/10 planted signal taxa (5
  increasers, 5 decreasers) with correct direction labels, after fixing
  the group-ordering bug above.
- Anomaly scoring correctly ranked a true on-deposit sample above a true
  background sample using the discovered indicators.
- Hierarchical clustering achieved 100% agreement with true labels on
  the (strong-signal) synthetic test set.
- Permutation validity test correctly distinguished the real planted
  indicator set (empirical p=0.008) from a random, non-informative taxon
  set of the same size (empirical p=0.538).

**Not yet tested:** against any real qFoldIT soil/overburden sequencing
data, because none has been provided yet — and not yet demonstrated for
any commodity other than kimberlite in any published source. Both are
prerequisites before this skill's output should inform a real exploration
decision.
