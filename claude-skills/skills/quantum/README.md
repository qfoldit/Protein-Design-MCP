# qFoldIT Quantum Skill — VQE Simulator (classical, numpy-based)

Claude Desktop Skill wrapping a from-scratch classical statevector
Variational Quantum Eigensolver (VQE) simulator, validated against a
real published molecular chemistry benchmark.

## What's inside

```
qfoldit-quantum/
├── SKILL.md                          — triggers, instructions, scope limits
├── README.md                         — this file
├── scripts/
│   └── vqe_simulator.py              — statevector sim + VQE optimizer
├── references/
│   └── model_documentation.md        — full validation results, sources
└── evals/
    └── eval_set.json                 — test prompts
```

## A note before the technical detail: about the "efficiency gain" framing

Every other qFoldIT skill README so far has included a forecast of what
the algorithm means for mining-operation efficiency (recovery %,
remaining asset life, etc.), because those skills (bio-oxidation,
biosorption, corrosion) map directly onto an extraction or asset-integrity
metric. **VQE does not.** It's a general quantum-chemistry ground-state
solver — useful for computing molecular energies, which could
*eventually* feed into something mining-relevant (e.g. evaluating a
candidate leaching catalyst or corrosion-inhibitor molecule's stability),
but it does not itself produce a recovery-rate or asset-life number.
Forcing an "efficiency gain" figure onto this skill just to match the
pattern of the others would mean presenting an invented number as if it
were a real projection, which is exactly the kind of thing this whole
project has been careful to avoid. If/when this is chained together with
`qfoldit-design` (molecule generation, currently on hold pending your ML
model access) for a specific mining application — e.g. "does this
candidate catalyst molecule improve leaching kinetics" — that combined
pipeline would be the place to make a mining-efficiency claim, once both
halves are real and connected to your process data.

## Scientific basis

**Algorithm:** Variational Quantum Eigensolver (Peruzzo et al. 2014).
Prepare a parameterized quantum state via an ansatz circuit, measure the
Hamiltonian's expectation value, classically optimize the parameters to
minimize it — by the variational principle, this upper-bounds (and, with
enough ansatz expressivity and optimizer convergence, reaches) the true
ground-state energy.

**Ansatz:** hardware-efficient (Kandala et al. 2017) — RY+RZ rotations
on every qubit per layer, CNOT entangling ring between layers.

**Optimizer:** COBYLA (gradient-free, standard practice for VQE since
real quantum hardware doesn't expose analytic gradients), with multiple
random restarts.

**Implementation:** genuine statevector simulation — qubits as a 2^n
complex vector, gates as explicit unitary matrices via Kronecker
products, Hamiltonians as explicit Pauli-string matrices. Nothing here
is a shortcut or approximation for the qubit counts tested (2 qubits);
it's exact linear algebra.

## Validation — this is the part worth reading closely

Rather than only checking the code against itself, it's validated
against a **real, published, external chemistry benchmark**:

1. **Gate mechanics**: CNOT and rotation gates checked against
   hand-computable expected outputs. Passed.
2. **Toy Hamiltonians**: VQE matches exact diagonalization to ~1e-9 on
   both an analytically-solvable case (H=Z0+Z1, ground energy exactly
   -2.0) and a random 16-term Hermitian 2-qubit Hamiltonian.
3. **Real H2 molecule (STO-3G basis)**: using qubit Hamiltonian
   coefficients *published in* Li, Wang, Wu & Zuo (2022), "Stabilizer
   Approximation" (arXiv:2209.09564) — not derived or guessed by this
   project — the simulator's VQE result, after adding nuclear repulsion,
   gives:
   - **-1.137284 Hartree** at equilibrium bond length (0.74 Å)
   - The widely-cited literature value for H2/STO-3G at equilibrium is
     **-1.1373 Hartree** — one of the most commonly quoted reference
     numbers in the VQE/quantum-computing literature. The match to 4
     decimal places is a genuine external validation, not a
     self-consistency check.
   - At extended bond length (2.8 Å): **-0.934151 Hartree**, matching
     the source paper's cited "~-0.93" value in that region.

This is meaningfully stronger validation than most from-scratch
simulator implementations get, precisely because it was checked against
someone else's independently published numbers rather than only against
its own internal logic.

## Scope limits — important, not optional reading

- **Classical simulator only.** No real quantum hardware, no quantum
  computational advantage. Statevector simulation is exponential in
  qubit count (2^n) — practical here for the small systems tested (2-6
  qubits); tens of qubits would already be infeasible.
- **Cannot generate Hamiltonians for arbitrary molecules.** Building a
  qubit Hamiltonian for a molecule you name (beyond H2, whose
  coefficients came from the cited paper) needs an actual quantum
  chemistry pipeline (PySCF + Jordan-Wigner/parity mapping via
  OpenFermion or Qiskit Nature) that isn't implemented here. If you want
  this for other molecules, either supply the Hamiltonian coefficients
  directly, or this becomes a follow-on piece of work once such a
  pipeline is available.
- **Diatomic nuclear repulsion only** in `nuclear_repulsion_energy` —
  polyatomic molecules need summing over all nuclear pairs.
- **No quantum annealing** — the qFoldIT architecture describes
  quantum-adapter as unifying VQE and annealing backends; this skill
  covers VQE only.

## Using this Skill in Claude Desktop

1. Copy the `qfoldit-quantum/` folder into your Claude Desktop skills
   directory (or install via the `.skill` package if provided).
2. Ask Claude things like: *"Fold H2 using VQE at the equilibrium
   bond length"* or supply a custom Pauli-string Hamiltonian directly.
3. Claude will run VQE, report it alongside the exact-diagonalization
   check, and — per the skill instructions — will be upfront if you ask
   about an arbitrary molecule this skill can't yet handle, or about
   real quantum hardware, rather than overstating what it can do.
