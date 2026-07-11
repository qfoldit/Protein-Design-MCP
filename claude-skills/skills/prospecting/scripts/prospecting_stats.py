"""
prospecting_stats.py

Statistical analysis layer for microbial-community-based mineral
exploration ("biogeochemical prospecting" / "indicator microbial
species" method).

WHAT THIS IS: the analysis half of a two-part pipeline. Given an OTU/ASV
abundance table (samples x taxa counts) with group labels (e.g.
"on-deposit" vs "background"), this module computes diversity indices,
identifies candidate indicator taxa, computes anomaly scores, and includes
an honest validity check (permutation test) for whether an indicator set's
apparent spatial signal could plausibly be due to chance.

WHAT THIS IS NOT: this does not process raw sequencing reads. Getting from
raw FASTQ files to an OTU/ASV abundance table requires a real
bioinformatics pipeline (QIIME2 or Mothur: demultiplexing, quality
filtering, denoising/OTU clustering, taxonomic classification against a
reference database like SILVA). That is a heavy, well-established but
separate piece of software infrastructure -- it is not reimplemented here,
and this module cannot be used until you already have an abundance table
from your own such pipeline. Treat the boundary between "raw reads" and
"abundance table" as the boundary between "not this module's job" and
"this module's job."

SCIENTIFIC BASIS AND HOW MATURE IT ACTUALLY IS -- read this before using
this in any external-facing claim:

The core idea (soil/overburden microbial community composition shifts
measurably above a buried ore body, and specific indicator taxa can be
identified and used prospectively) is REAL, RECENT, PEER-REVIEWED research
-- not an invented premise:

  Ronholm, J. et al. "DNA sequencing, microbial indicators, and the
  discovery of buried kimberlites." Communications Earth & Environment
  4, 128 (2023). https://doi.org/10.1038/s43247-023-01020-z

Key facts from that paper, since they set realistic expectations for what
this method can and can't do:
  - It was demonstrated for ONE mineral system: diamondiferous kimberlites
    in Canadian subarctic tundra/till overburden. It has NOT been
    demonstrated in that paper for gold, copper, lithium, or REE
    exploration, or in other climates/soil types. Do not assume it
    transfers.
  - Laboratory kimberlite-amendment incubations showed a ~48% drop in
    observed OTU richness (990+/-10 -> 520+/-10) and identified 375
    candidate indicator taxa (LEfSe, LDA threshold >2): 65 enriched
    (17%), 310 depleted (83%) in the presence of kimberlite material.
  - At a real field site (DO-18), species richness above kimberlite
    averaged ~29% lower than background (Chao1 1840+/-80 vs 2600+/-100).
    59 of the lab-derived indicators overlapped with field-observed
    indicators; only 19 of those matched the predicted direction of
    change -- i.e. most lab-derived indicators did NOT replicate cleanly
    in the field. This is reported by the source study itself and is
    the central reason this module includes a permutation/validity check
    as a first-class function rather than an optional afterthought.
  - A combined set of 78 indicators, applied blind at a different deposit
    (Kelvin), successfully resolved the kimberlite's surface expression.
    The authors validated significance with a randomization test: when
    they repeated the analysis with 10 random (non-indicator) taxon sets
    of the same size, 7 of 10 showed no meaningful spatial correlation --
    i.e. the real indicator set's signal was distinguishable from what
    chance alone would produce, but not by an overwhelming margin.

Given this, the honest framing for qFoldIT's use of this method is:
"a real, promising, actively-developing exploration technique with one
published success story for one mineral system" -- not "an established,
generalizable prospecting tool ready to point at any qFoldIT ore body."
Every function below that produces a number should be reported alongside
this context, not as a validated production forecast.
"""

import numpy as np
from scipy import stats
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import pdist


# ---------------------------------------------------------------------------
# 1. Diversity indices
# ---------------------------------------------------------------------------
def chao1_richness(counts):
    """
    Chao1 richness estimator (bias-corrected form):
        S_chao1 = S_obs + F1*(F1-1) / (2*(F2+1))

    counts : 1D array of per-taxon read counts for ONE sample (zeros for
             absent taxa are fine and expected).

    S_obs = number of taxa with count > 0
    F1    = number of singletons (count == 1)
    F2    = number of doubletons (count == 2)

    This estimates TOTAL richness including taxa likely present but not
    sampled, correcting for the fact that rare taxa are undersampled.
    Reference: Chao, A. (1984) "Non-parametric estimation of the number
    of classes in a population." Scand. J. Statist. 11, 265-270.
    """
    counts = np.asarray(counts, dtype=float)
    counts = counts[counts > 0]
    s_obs = len(counts)
    f1 = np.sum(counts == 1)
    f2 = np.sum(counts == 2)
    return float(s_obs + (f1 * (f1 - 1)) / (2 * (f2 + 1)))


def inverse_simpson(counts):
    """
    Inverse Simpson diversity index: 1 / sum(p_i^2), where p_i is the
    relative abundance of taxon i. Higher = more even/diverse community.
    Unlike Chao1 (richness only), this is sensitive to evenness too --
    a community with the same number of taxa but more skewed dominance
    will have a LOWER inverse Simpson value.
    """
    counts = np.asarray(counts, dtype=float)
    total = counts.sum()
    if total == 0:
        return 0.0
    p = counts[counts > 0] / total
    return float(1.0 / np.sum(p ** 2))


# ---------------------------------------------------------------------------
# 2. Response ratio (on-deposit vs background enrichment/depletion)
# ---------------------------------------------------------------------------
def response_ratio(abundance_on_deposit, abundance_background, pseudocount=1e-6):
    """
    Response ratio, following the source paper's convention:
        RR = (mean(on_deposit) / mean(background) - 1) * 100

    Positive RR = enriched on-deposit (candidate "increaser").
    Negative RR = depleted on-deposit (candidate "decreaser"; the source
    study found decreasers were the majority class, 83% of its 375
    lab-derived indicators).

    A small pseudocount avoids divide-by-zero when background abundance
    is exactly 0 for a given taxon -- this is a standard compositional-
    data convention, not a way of hiding a real zero.
    """
    on = np.asarray(abundance_on_deposit, dtype=float)
    bg = np.asarray(abundance_background, dtype=float)
    mean_on = on.mean() + pseudocount
    mean_bg = bg.mean() + pseudocount
    return float((mean_on / mean_bg - 1.0) * 100.0)


# ---------------------------------------------------------------------------
# 3. Indicator taxon analysis
# ---------------------------------------------------------------------------
def indicator_taxa_analysis(otu_table, group_labels, target_group, taxon_names=None, alpha=0.05):
    """
    Identify candidate indicator taxa that differ between two groups
    (e.g. "on_deposit" vs "background").

    otu_table    : 2D array, shape (n_samples, n_taxa), raw or relative
                   abundance counts.
    group_labels : 1D array/list of length n_samples, exactly two unique
                   values (e.g. ["on_deposit", "background", ...]).
    target_group : REQUIRED. The exact value in group_labels that
                   represents the condition of interest (e.g.
                   "on_deposit"). "increaser"/"decreaser" and the sign of
                   response_ratio_pct are defined relative to THIS group.
                   This is required (not inferred) on purpose: relying on
                   e.g. alphabetical or first-seen ordering of group
                   labels is a real bug this module hit during its own
                   testing -- "background" sorts before "on_deposit"
                   alphabetically, which silently swapped increaser and
                   decreaser labels for every taxon when direction was
                   inferred instead of specified. Always pass this
                   explicitly.
    taxon_names  : optional list of length n_taxa for readable output.
    alpha        : significance threshold for the per-taxon Mann-Whitney
                   U test (uncorrected -- see caveat below).

    Returns a list of dicts, one per taxon that passed the threshold,
    each with: taxon, p_value, response_ratio_pct (positive = enriched
    IN target_group), direction ("increaser" or "decreaser", relative to
    target_group), sorted by ascending p-value.

    METHODOLOGY CAVEAT, stated plainly: this is a deliberately SIMPLER
    substitute for the published LEfSe algorithm (Segata et al. 2011,
    Kruskal-Wallis + linear discriminant analysis effect size), which is
    what the cited kimberlite study actually used. This module uses a
    per-taxon Mann-Whitney U test (non-parametric, broadly analogous in
    spirit) plus a response-ratio effect size, NOT the LDA-based effect
    size LEfSe reports. If you need results directly comparable to
    published LEfSe output, use the actual LEfSe tool. This function is
    for a first-pass, dependency-light candidate screen.

    MULTIPLE-TESTING CAVEAT: with many taxa tested at alpha=0.05
    uncorrected, false positives are expected by chance alone (roughly
    5% of truly non-differing taxa will appear "significant"). For a
    real dataset with hundreds of taxa, apply a false-discovery-rate
    correction (e.g. Benjamini-Hochberg) before treating the output as
    a final indicator list -- this function does NOT do that correction
    automatically, so it is not done silently on your behalf.
    """
    otu_table = np.asarray(otu_table, dtype=float)
    group_labels = np.asarray(group_labels)
    unique_groups = np.unique(group_labels)
    if len(unique_groups) != 2:
        raise ValueError(f"Expected exactly 2 groups, got {len(unique_groups)}: {unique_groups}")
    if target_group not in unique_groups:
        raise ValueError(
            f"target_group={target_group!r} not found in group_labels "
            f"(available: {list(unique_groups)}). This is intentionally "
            f"a hard error rather than a silent fallback."
        )
    other_group = [g for g in unique_groups if g != target_group][0]
    mask_target = group_labels == target_group
    mask_other = group_labels == other_group

    n_taxa = otu_table.shape[1]
    if taxon_names is None:
        taxon_names = [f"taxon_{i}" for i in range(n_taxa)]

    results = []
    for j in range(n_taxa):
        col = otu_table[:, j]
        vals_target, vals_other = col[mask_target], col[mask_other]
        if np.all(vals_target == vals_target[0]) and np.all(vals_other == vals_other[0]) and vals_target[0] == vals_other[0]:
            continue  # constant across both groups, nothing to test
        try:
            stat, p = stats.mannwhitneyu(vals_target, vals_other, alternative="two-sided")
        except ValueError:
            continue  # e.g. all-zero in both groups
        if p <= alpha:
            rr = response_ratio(vals_target, vals_other)  # positive = enriched in target_group
            results.append({
                "taxon": taxon_names[j],
                "p_value": float(p),
                "response_ratio_pct": rr,
                "direction": "increaser" if rr > 0 else "decreaser",
            })
    results.sort(key=lambda r: r["p_value"])
    return results


# ---------------------------------------------------------------------------
# 4. Anomaly score for new/unlabeled samples
# ---------------------------------------------------------------------------
def anomaly_score(sample_abundance, indicator_taxa_idx, indicator_directions, taxon_totals=None):
    """
    Compute a simple anomaly score for one sample given a pre-identified
    set of indicator taxa and their expected direction ("increaser" or
    "decreaser"). Score = sum over indicators of (signed, normalized
    relative abundance), where "increaser" taxa contribute positively and
    "decreaser" taxa contribute negatively when abundant -- so a sample
    that looks like the on-deposit signature scores higher.

    sample_abundance     : 1D array, this sample's raw counts across all
                           taxa (same taxon order as used for indicator
                           discovery).
    indicator_taxa_idx   : list of column indices into sample_abundance
                           corresponding to the chosen indicator taxa.
    indicator_directions : list of "increaser"/"decreaser", same length
                           and order as indicator_taxa_idx.
    taxon_totals         : optional per-taxon normalization denominator
                           (e.g. max abundance across a reference survey)
                           -- if omitted, uses this sample's own total
                           read count (i.e. reports relative abundance).

    This is a simple, transparent scoring rule chosen for interpretability,
    NOT a reproduction of the source paper's exact anomaly-mapping
    statistics (which used relative-abundance heatmaps across a spatial
    grid, not a single scalar score per sample). Treat this as a
    reasonable first-pass ranking metric, not a validated ore-probability
    score.
    """
    sample_abundance = np.asarray(sample_abundance, dtype=float)
    total = taxon_totals if taxon_totals is not None else sample_abundance.sum()
    if total == 0:
        return 0.0
    rel = sample_abundance / total
    score = 0.0
    for idx, direction in zip(indicator_taxa_idx, indicator_directions):
        sign = 1.0 if direction == "increaser" else -1.0
        score += sign * rel[idx]
    return float(score)


# ---------------------------------------------------------------------------
# 5. Hierarchical clustering (community similarity)
# ---------------------------------------------------------------------------
def hierarchical_cluster(otu_table, method="average", metric="euclidean", n_clusters=2):
    """
    UPGMA-style hierarchical clustering of samples by community
    composition (matches the general approach used in the source study
    for visualizing community structure differences).

    Returns (linkage_matrix, cluster_assignments) where
    cluster_assignments is a 1D array of length n_samples assigning each
    sample to one of n_clusters groups.

    method="average" is UPGMA. Uses raw Euclidean distance on the
    provided table by default -- if your abundances span very different
    scales, consider normalizing (e.g. relative abundance, or a
    Bray-Curtis distance via scipy's pdist(metric="braycurtis")) before
    calling this, since Euclidean distance on raw counts can be dominated
    by a few highly abundant taxa.
    """
    otu_table = np.asarray(otu_table, dtype=float)
    dist = pdist(otu_table, metric=metric)
    Z = linkage(dist, method=method)
    clusters = fcluster(Z, t=n_clusters, criterion="maxclust")
    return Z, clusters


# ---------------------------------------------------------------------------
# 6. Permutation validity test -- is the indicator signal distinguishable
#    from chance? (Directly modeled on the source study's own randomization
#    check -- included here because the source study found this mattered:
#    only 19 of 59 candidate indicators actually replicated in the field.)
# ---------------------------------------------------------------------------
def permutation_validity_test(otu_table, group_labels, indicator_taxa_idx,
                               n_permutations=1000, random_state=None):
    """
    Tests whether the chosen indicator taxa separate the two groups
    better than randomly-selected taxon sets of the same size would.

    Procedure: compute a separation score for the real indicator set
    (difference in mean anomaly-style score between the two groups),
    then repeat with `n_permutations` random taxon sets of the same size
    and see what fraction of random sets achieve an equal-or-greater
    separation. This empirical p-value is the honest way to answer
    "could this apparent signal be a coincidence?" -- exactly the
    question the source study asked with its 10-random-set check (they
    found 7/10 random sets showed no correlation; this function
    generalizes that into a proper empirical p-value at arbitrary
    permutation count).

    Returns dict: {"real_separation": float, "empirical_p_value": float,
                   "n_permutations": int}

    A high empirical p-value (e.g. > 0.05) means the chosen indicators
    are NOT clearly distinguishable from a random taxon set of the same
    size for THIS dataset -- that is an important negative result to
    report, not something to suppress or re-run until it looks better.
    """
    rng = np.random.default_rng(random_state)
    otu_table = np.asarray(otu_table, dtype=float)
    group_labels = np.asarray(group_labels)
    unique_groups = np.unique(group_labels)
    if len(unique_groups) != 2:
        raise ValueError("Expected exactly 2 groups")
    g1, g2 = unique_groups
    mask1 = group_labels == g1
    mask2 = group_labels == g2
    n_taxa = otu_table.shape[1]
    k = len(indicator_taxa_idx)

    def separation_score(taxa_idx):
        rel = otu_table / (otu_table.sum(axis=1, keepdims=True) + 1e-12)
        subset = rel[:, taxa_idx].sum(axis=1)
        return abs(subset[mask1].mean() - subset[mask2].mean())

    real_sep = separation_score(indicator_taxa_idx)

    random_seps = np.empty(n_permutations)
    all_idx = np.arange(n_taxa)
    for i in range(n_permutations):
        random_idx = rng.choice(all_idx, size=k, replace=False)
        random_seps[i] = separation_score(random_idx)

    empirical_p = float(np.mean(random_seps >= real_sep))
    return {
        "real_separation": float(real_sep),
        "empirical_p_value": empirical_p,
        "n_permutations": n_permutations,
    }
