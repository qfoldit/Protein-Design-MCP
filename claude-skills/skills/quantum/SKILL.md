---
name: qfoldit-quantum
description: Classical statevector simulation of the Variational Quantum Eigensolver (VQE) algorithm for small molecular/spin Hamiltonians (2-4 qubits), validated against exact diagonalization and against a real published H2 molecular benchmark (STO-3G, -1.1373 Hartree at equilibrium bond length). Use this skill whenever the user asks about VQE, quantum simulation of molecules, ground state energy calculation via quantum algorithms, ansatz circuits, or qfoldit quantum-adapter requests involving VQE. Trigger even if the user just gives a molecule name and bond distance without saying "VQE" explicitly. Do NOT use this for quantum annealing requests -- that backend is not implemented here.
---

# qfoldit-quantum (VQE simulator)

A from-scratch classical statevector VQE simulator (numpy only -- no
Qiskit, no real quantum hardware, no network access to quantum cloud
backends). Implements: Pauli-string Hamiltonian construction, a
hardware-efficient ansatz (Kandala et al. 2017 style: RY+RZ rotations per
qubit per layer, CNOT entanglers between layers), and a gradient-free
classical optimization loop (COBYLA with multi-restart) that minimizes
the ansatz's energy expectation value.

**Read `references/model_documentation.md` before answering** -- it has
the full validation results (toy Hamiltonians, and a real H2 molecular
benchmark matching the well-known -1.1373 Hartree literature value) and,
critically, the scope limits below.

## Critical scope limits -- read before promising anything

1. **This is a classical simulator, not a real quantum backend.**
   Statevector simulation scales as 2^n in memory/compute -- practical
   here only for small systems (2-6 qubits demonstrated; tens of qubits
   would already be infeasible on this classical hardware). It cannot
   provide any quantum computational advantage; it is useful for
   algorithm development/testing/education, matching what a "simulator"
   backend option would offer, not a "real quantum hardware" backend.
2. **No arbitrary-molecule Hamiltonian generation.** Building a qubit
   Hamiltonian for a molecule the user names (beyond H2, whose
   coefficients were sourced from a published paper for validation)
   requires an actual quantum chemistry integral/mapping pipeline
   (PySCF + Jordan-Wigner/parity mapping, e.g. via OpenFermion or
   Qiskit Nature) that is NOT implemented in this skill. If the user
   asks to fold/simulate an arbitrary molecule, this skill can only
   proceed if they supply the qubit Hamiltonian coefficients directly
   (as a Pauli-string dict) -- it cannot derive them from a SMILES
   string or molecule name on its own.
3. **VQE energies are electronic-structure energies only.** For a real
   molecule's total energy, nuclear repulsion must be added separately
   (see `nuclear_repulsion_energy` -- point-charge model, correct for
   diatomics; polyatomic systems need a sum over all nuclear pairs, not
   implemented here beyond the 2-body case).
4. **Quantum annealing is a separate backend** mentioned in the qFoldIT
   architecture (quantum-adapter unifies VQE and annealing) -- this
   skill covers VQE only. Do not answer annealing questions as if this
   skill's code applies.

## How to handle a request

1. If the user gives a Pauli-string Hamiltonian directly (or a known
   small system like H2 at a given bond distance, where this skill has
   validated published coefficients), run `run_vqe(...)` from
   `scripts/vqe_simulator.py`.
2. If the user asks to simulate an arbitrary/named molecule without
   supplying Hamiltonian coefficients, explain the gap in point 2 above
   plainly rather than fabricating plausible-looking coefficients.
3. Always report the VQE energy **alongside** the exact diagonalization
   result for the same Hamiltonian (the code computes both) -- this is
   the built-in correctness check and should be surfaced, not hidden.
4. For molecular total energy, add `nuclear_repulsion_energy(r_angstrom)`
   to the electronic VQE result and say so explicitly.
5. State plainly that this is a classical simulator when asked about
   "quantum backends," "real quantum hardware," or performance/speed
   claims -- do not imply quantum hardware execution occurred.

## Testing

See `evals/eval_set.json` and `references/model_documentation.md` for
full validation details: gate-mechanics unit checks, a toy Hamiltonian
with an analytically known ground state, a random Hermitian 2-qubit
Hamiltonian, and the H2/STO-3G real molecular benchmark (matched to
-1.1373 Hartree at equilibrium, and to the paper's ~-0.93 Hartree value
at extended bond length, after adding nuclear repulsion).
