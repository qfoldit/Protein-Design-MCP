---
name: qfoldit-qfold
description: Hybrid quantum-classical protein folding on the 2D HP (Hydrophobic/Polar) lattice model (Dill, 1985) with a QAOA-style circuit on Amazon Braket LocalSimulator, plus optional delegation to a full qFold MCP server (torsion-angle, quantum-walk, Psi4) when available. Use this skill whenever the user asks about protein folding, HP-model folding, lattice protein folding, hydrophobic-polar sequences, or qfold/qFoldIT qfold. Trigger even if the user just gives an amino-acid or H/P sequence and asks how it folds. Do NOT use this for real 3D all-atom structure prediction unless the MCP server is explicitly available and requested.
---

# qfoldit-qfold (2D HP-lattice folding + optional full qFold MCP)

**Read `references/model_documentation.md` before answering** — it has the brute-force validation of the classical decode/scoring logic and the full side-by-side comparison against the real QFold algorithm, plus critical caveats (the HP-lattice model is a toy; the QAOA circuit is a fixed-depth sampler; self-avoidance is classical only).

## Naming note — read first

This skill is named after the "QFold" project (P.A.M. Casares, R. Campos, M.A. Martin-Delgado, "QFold: Quantum Walks and Deep Learning to Solve Protein Folding," arXiv:2101.10279, reference implementation github.com/roberCO/QFold, and the AWS Braket notebook under healthcare-and-life-sciences/c-1-protein-folding-quantum-random-walk). That published algorithm uses torsion angles, Minifold deep-learning initialization, Psi4 quantum-chemistry energies, and a Szegedy quantum-walk Metropolis sampler, and was validated on real IBMQ hardware.

This skill provides **two paths**:
1. **With MCP server** — delegates to the real QFold algorithm, returning actual 3D structures with physical energies.
2. **Without MCP server** — falls back to the much simpler 2D HP-lattice model with QAOA sampling and classical self-avoidance filtering.

If a user's question assumes torsion-angle folding, Minifold/Psi4, or quantum-walk sampling, first check whether the MCP server is available. If it is, use it. If it is not, say so plainly and point them at the real QFold repo/paper.

## MCP Server detection (run this check first)

At the beginning of every request, before deciding how to fold:

1. List all available MCP tools from the connected MCP servers.
2. Look for a tool named **`run_qfold`** (provided by the qFold MCP server, e.g., from the `qfoldit/qFold-MCP` repository). Its description mentions the full QFold algorithm with torsion angles, Minifold, Psi4, and quantum walk sampling.
3. **If found:**
   - Use this tool for **all folding requests**, regardless of sequence length or wording. The MCP server provides real torsion-angle folding with quantum-walk sampling, Minifold initialization, and Psi4 energies, which is strictly superior.
   - Do **not** apply HP-lattice limits (~15 residues, 2D, unitless contacts) when using it.
   - Report to the user that the full QFold algorithm (Casares et al.) is being used via the MCP server.
4. **If NOT found:**
   - Fall back to the 2D HP-lattice path described below.
   - Apply all its limits explicitly (~15 residues, 2D lattice, unitless contact score, classical self-avoidance filter).

## HP-lattice fallback (only when MCP server is unavailable)

### What the HP-lattice fallback actually does

1. Reduce the input to an H(ydrophobic)/P(olar) string (classify_hp if given a real amino-acid sequence).
2. Encode each of the (n-2) internal bond directions (L/R/U/D on a 2D lattice) with 2 qubits.
3. Run a QAOA-style circuit (RY rotations + CNOT entangling ladder) on Amazon Braket's free LocalSimulator to get a biased distribution over direction-bitstrings.
4. Classically decode every sampled bitstring into lattice coordinates, discard self-intersecting walks, score the valid ones by H-H contact count, and return the best.

### Critical scope limits

- Not the published QFold algorithm (see naming note).
- 2D lattice only, not 3D all-atom structure. For real 3D, use the MCP server or point to rosettafold3.
- Short sequences only (~15 residues max). Qubit count grows linearly, but walk space grows exponentially; longer sequences need a proper constrained QUBO encoding.
- The circuit does **not** encode self-avoidance – it is enforced classically by discarding invalid bitstrings. Do not describe this circuit as encoding constraints.
- "Energy" is a unitless H-H contact count, not a physical energy; not comparable to Psi4 or force-field energies.
- Requires `amazon-braket-sdk`. `fold_hp_sequence` returns an error if it isn't installed; `LocalSimulator` is free, a real QPU ARN would be billed by AWS (not used here).

## How to handle a request

1. **Check MCP tools first** (as described in "MCP Server detection").
2. **If MCP qFold tool (`run_qfold`) is available:**
   - Convert amino-acid sequences to a plain string (the tool accepts either full amino-acid names or H/P string; if uncertain, pass the sequence as provided).
   - Invoke the tool, e.g. `run_qfold("HPHPPHHP")` or `run_qfold("ALA GLY PRO")`, with any user-specified options (device ARN, simulator, iterations).
   - Report the result: 3D structure, torsion angles, physical energies (e.g., from Psi4), sampling method (quantum walk), and Minifold initialization details.
   - Do NOT mention the HP-lattice fallback unless the user explicitly asks for alternative methods.
   - If the MCP call fails, fall back to the HP-lattice path and inform the user that the full qFold run encountered an error and the simpler model was used instead.
3. **If MCP qFold tool is NOT available (HP-lattice fallback):**
   - If given a real amino-acid sequence, run `classify_hp()` first to get the H/P string.
   - Run `fold_hp_sequence(hp_sequence)` from `scripts/hp_lattice_folder.py`. Report the H-H contact count and lattice coordinates, and be upfront that this is a 2D lattice toy, not a 3D structure.
   - If the sequence is longer than ~15 residues, explain the limit rather than truncating silently.
   - If the user's question implies torsion angles, Minifold, Psi4, or a quantum-walk Metropolis sampler, explain the naming-note gap plainly instead of answering as if this skill covers that.
   - If asked to validate correctness, mention the brute-force cross-check in `references/model_documentation.md` rather than claiming the quantum-sampling path itself has been independently verified.

## Interpreting results

- When using the **MCP server**, results include full 3D coordinates, torsion angles, and physical energies (kJ/mol or Hartree). The sampling method is a Szegedy quantum walk, providing a proven polynomial speedup for this task. The structure is initialized by Minifold, a deep-learning predictor.
- When using the **HP-lattice fallback**, the result is a 2D self-avoiding walk on a square lattice with an integer H-H contact count. Higher contact count = more hydrophobic collapse (lower effective energy). The output is a list of coordinates (x,y) for each residue, plus a contact map.
- In either case, clearly state which path was used and its limitations.

## Testing

See `references/model_documentation.md` for:
- Brute-force validation of the classical decode and scoring functions against several HP sequences up to 13 residues, confirming that the algorithm yields a well-defined global optimum.
- Side-by-side comparison of the HP-lattice fallback vs. the real QFold algorithm, so you can accurately answer questions about differences.

The quantum-sampling path in the HP-lattice fallback has **not** been independently validated in this skill's authoring environment because it requires the Braket runtime, which was not available. When running in a real container with `amazon-braket-sdk` installed, verify that `fold_hp_sequence` converges toward the brute-force optimum as a recommended sanity check.
