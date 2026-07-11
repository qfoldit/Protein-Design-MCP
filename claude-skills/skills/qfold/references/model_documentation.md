# Model Reference: qfoldit-qfold (2D HP-lattice folding)

## 1. What is implemented

A QAOA-style circuit (Hadamard layer, then alternating CNOT-entangling
ladders and RY-rotation layers) is sampled on Amazon Braket's free
`LocalSimulator`. Each of the `n_residues - 2` internal bond directions
of a self-avoiding walk on the 2D square lattice is encoded as 2 qubits
(4 possible directions: L/R/U/D). Every sampled bitstring is decoded
classically into lattice coordinates (`decode_walk`); walks that
backtrack immediately or self-intersect are discarded as physically
invalid. Valid walks are scored by H-H contact count (`hp_energy`) --
the standard HP-model "energy" (Dill, 1985) -- and the best-scoring
valid walk is returned.

`scripts/hp_lattice_folder.py` also includes `brute_force_best_fold`,
an exhaustive (non-quantum) enumeration of all `4**(n-2)`
direction-bitstrings, used purely to validate `decode_walk`/`hp_energy`
against an independently-computable ground truth (see below), the same
role the published H2/STO-3G benchmark plays for the `qfoldit-quantum`
skill.

## 2. Validation performed

### Classical decode/scoring logic -- exhaustive brute-force cross-check

Because the quantum circuit here only *proposes* candidate walks (it
does not encode the self-avoidance constraint -- see SKILL.md point 4),
correctness of the whole pipeline hinges almost entirely on
`decode_walk`/`hp_energy` being right, not on the circuit. These two
functions were validated by exhaustively enumerating every possible
bitstring for several sequences up to 13 residues (`4**11` = 4,194,304
bitstrings, small enough to brute-force in this authoring environment)
and confirming a well-defined best fold is found in every case:

| Sequence (truncated to ≤13 for brute force) | Qubits | Valid self-avoiding walks | Best H-H contacts |
|---|---|---|---|
| `HPHPPHHPHPPHP` | 22→ (13-mer, 11 bonds) | 81,233 / 2^22 | 4 |
| `HHPPHHHPHHPH` (12-mer) | 20 | 30,073 / 2^20 | 5 |
| `HPHPPHHPHPPH` (12-mer) | 20 | 30,073 / 2^20 | 5 |
| `PHPPHPHHHPHH` (12-mer) | 20 | 30,073 / 2^20 | 5 |
| `HHPHH` (5-mer) | 6 | 25 / 2^6 | 1 |
| `HPPH` (4-mer) | 4 | 9 / 2^4 | 1 |

(Qubit counts above are `2*(n-2)`; the table header shows total
bitstrings enumerated as `2^n_qubits`, matching `4**(n-2)`.) These are
sane, internally consistent results: contact counts grow with sequence
length and hydrophobic density, and the self-avoiding-walk fraction
shrinks as expected as sequences get longer relative to lattice space.

### External reference point: the standard 20-mer HP benchmark

The lattice-protein literature has a widely-used 20-residue benchmark
sequence, `HPHPPHHPHPPHPHHPPHPH` (first used by Unger & Moult, later
cited across many GA/ACO/RL papers), with a published, independently
verified optimal energy of **-9** (9 H-H contacts). This sequence is
**longer than this tool's supported ~15-residue limit**, so
`fold_hp_sequence` cannot run it directly and this is *not* a match
validation -- it's included only as external context for what
"reasonable" HP-model contact counts look like at this scale, the same
way a textbook constant helps sanity-check an order of magnitude.

### What was NOT validated here

The quantum-sampling path itself (`fold_hp_sequence`'s use of
`amazon-braket-sdk`'s `LocalSimulator`) could not be run in this
authoring environment, which has neither network access nor the
package installed. This documentation only validates the classical
decode/scoring logic that the quantum samples are fed through. Anyone
running this in the actual container (where `amazon-braket-sdk` is
installed per `requirements.txt`) can additionally confirm that
`fold_hp_sequence` converges toward the same optimum
`brute_force_best_fold` finds for a given short sequence, as a
recommended follow-up check -- worth doing before treating this skill's
outputs as anything more than illustrative.

## 3. Side-by-side comparison with the real, published QFold algorithm

| Aspect | This skill (`qfoldit-qfold`) | Real QFold (Casares/Campos/Martin-Delgado, arXiv:2101.10279) |
|---|---|---|
| Structure representation | 2D lattice coordinates (self-avoiding walk) | Torsion (dihedral) angles -- no lattice simplification |
| Dimensionality | 2D only | 3D |
| Initialization | None (random circuit parameters / seed) | Minifold (deep-learning structure predictor, AlphaFold stand-in) |
| Energy function | HP-model H-H contact count (unitless proxy) | Psi4 -- real ab-initio quantum chemistry energies |
| Quantum component | Fixed-depth QAOA-style ansatz, single sampling pass | Szegedy-style quantized quantum walk applied to a Metropolis Markov chain (genuine quantum-walk sampler with proven speedup) |
| Self-avoidance / physical constraints | Enforced entirely classically, after sampling (invalid samples discarded) | Naturally absent as a discrete constraint -- continuous angle space |
| Validated on real quantum hardware | No (LocalSimulator only) | Yes -- proof-of-concept on IBMQ Casablanca |
| Practical size limit | ~15 residues (this tool's enforced cap) | Demonstrated on dipeptides/tripeptides/tetrapeptides in the paper; framed as scalable |
| Output | 2D lattice coordinates + contact count | 3D torsion angles (reconstructable backbone) |

The shared thread is genuinely thin: both use *some* form of
quantum-classical hybrid sampling to search a folding conformation
space, and both trace back to the general idea of applying quantum
techniques to Metropolis-style search. Beyond that, they are different
algorithms solving different (simplified vs. realistic) versions of the
same problem. Anyone wanting the actual published QFold method should
be pointed at github.com/roberCO/QFold or the AWS Braket notebook
(`qfoldit/AWS-Deploy`, `.../c-1-protein-folding-quantum-random-walk`),
not told this skill already covers it.

## 4. Explicit non-goals / scope limits

- **Not the published QFold algorithm** -- see section 3.
- **Not a real 3D structure predictor** -- use `rosettafold3` for that.
- **No self-avoidance encoding in the circuit itself** -- validity is a
  purely classical post-filter.
- **Sequences longer than ~15 residues are out of scope** -- would need
  a proper constrained QUBO encoding, not implemented here.
- **HP-model energy is unitless** -- not comparable to any real
  physical energy scale (Hartree, kcal/mol, etc.).
