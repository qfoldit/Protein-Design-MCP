# qFoldIT qFold Skill — 2D HP-Lattice Folding + Optional Full QFold via MCP (Amazon Braket)

Claude Desktop Skill wrapping a hybrid quantum-classical protein folder.
Now supports **two execution paths**:

1. **Full QFold algorithm (Casares et al.)** — when the companion
   [qFold MCP server](https://github.com/qfoldit/qFold-MCP) is running:
   torsion‑angle parameterization, Minifold deep‑learning initialization,
   Psi4 quantum‑chemistry energies, and a Szegedy‑style quantum‑walk
   Metropolis sampler, dispatched to Amazon Braket (local simulator or
   real QPU).

2. **2D HP‑lattice model (Dill, 1985)** — fallback when no MCP server is
   detected: a QAOA‑style circuit on Braket's free `LocalSimulator`
   proposes candidate lattice walks, and a classical post‑filter enforces
   self‑avoidance and scores H‑H contacts.

The `SKILL.md` has been updated to automatically detect the MCP server
and delegate to it, with a transparent fallback if it is unavailable.

## What's inside

```
qfoldit-qfold/
├── SKILL.md                          — triggers, instructions, MCP detection logic, naming note, scope limits
├── README.md                         — this file
├── scripts/
│   └── hp_lattice_folder.py          — decode/scoring logic + circuit + brute-force validator
└── references/
    └── model_documentation.md        — brute-force validation + full comparison vs. real QFold
```

The full qFold algorithm is provided by the **external MCP server**
([`qfoldit/qFold-MCP`](https://github.com/qfoldit/qFold-MCP)), not by
the files in this skill directory.

## Please read the naming note before anything else

This skill is named after — but does **not** inherently implement — the
published QFold algorithm (Casares, Campos & Martin‑Delgado,
arXiv:2101.10279; github.com/roberCO/QFold; also shipped as an AWS
Braket notebook in `qfoldit/AWS‑Deploy` under
`healthcare‑and‑life‑sciences/c‑1‑protein‑folding‑quantum‑random‑walk`).
That algorithm uses torsion angles, a Minifold deep‑learning
initializer, real Psi4 quantum‑chemistry energies, and a genuine
Szegedy quantum‑walk Metropolis sampler, and was validated on real IBMQ
hardware.

**However**, when the qFold MCP server is connected, Claude **will** use
that exact algorithm — the MCP server provides the real QFold
implementation. The HP‑lattice model (Dill, 1985) with QAOA‑style
sampling is a fallback for situations where the MCP server is not
available. If you want to guarantee access to the full QFold algorithm,
set up and run the [`qFold-MCP`](https://github.com/qfoldit/qFold-MCP)
server alongside this skill.

## Scientific basis

**Full QFold (via MCP):** torsion‑angle protein representation;
Minifold neural‑network initializer; Psi4 ab‑initio energy evaluation;
Szegedy quantum‑walk Metropolis sampler (proven polynomial speed‑up);
validated on IBMQ hardware (see arXiv:2101.10279).

**HP‑lattice fallback:** proteins reduced to an H(ydrophobic)/P(olar)
string, folded as a self‑avoiding walk on a 2D square lattice, scored
by non‑sequential H‑H contact count (Dill, 1985). Quantum component: a
QAOA‑style ansatz (Hadamard layer, alternating CNOT‑entangling ladders
and RY‑rotation layers) on Braket's `LocalSimulator`, biasing the
sampled distribution away from uniform. Classical component: decode
bitstrings, discard self‑intersecting walks, score H‑H contacts, return
the best.

## Validation

### HP‑lattice fallback
- Decode/scoring logic (`decode_walk`, `hp_energy`): validated by
  exhaustive brute‑force enumeration (`brute_force_best_fold`) against
  HP sequences up to 13 residues — every case produces a
  well‑defined, internally‑consistent best fold. See
  `references/model_documentation.md` for the full table.
- External context: the standard 20‑mer HP benchmark
  (`HPHPPHHPHPPHPHHPPHPH`) has a published optimal energy of −9
  (9 contacts) — cited as scale context only; it exceeds this tool's
  ~15‑residue limit and was not run as a match check.
- Quantum‑sampling path: not validated in the authoring environment
  (no `amazon‑braket‑sdk`). When running in a container with the SDK,
  confirm `fold_hp_sequence` converges to the brute‑force optimum.

### Full QFold (MCP)
The MCP server implements the published algorithm; its correctness is
established by the original paper and the reference implementation.
No additional validation is performed by this skill — it simply
delegates to the server.

## Scope limits

### When using the full QFold MCP server
- 3D all‑atom structures (torsion angles) — **no lattice simplification**.
- No hard residue limit; large peptides are feasible given sufficient
  compute and shot budget.
- Physical energies (Psi4) — comparable with force‑field results.
- Quantum‑walk sampling with proven speed‑up.
- Requires `amazon‑braket‑sdk`, `psi4`, Minifold dependencies (handled
  by the MCP server installation).
- Real QPU usage is optional and billed by AWS.

### When falling back to the HP‑lattice model
- **Not the published QFold algorithm** — see naming note.
- **2D lattice only, not 3D** — not an all‑atom structure.
- **~15 residues max** — qubit count grows linearly, but useful walk
  space grows exponentially; longer sequences need a proper constrained
  QUBO encoding, not implemented here.
- **Self‑avoidance is a classical post‑filter**, not encoded in the
  circuit — a materially weaker use of "quantum" than a true
  constrained‑sampling or quantum‑walk approach.
- **HP‑model "energy" is a unitless contact count**, not a physical
  energy comparable to Psi4/force‑field results.
- **Requires `amazon‑braket‑sdk`.** `LocalSimulator` is free and needs
  no AWS account; a real QPU device ARN would be billed by AWS (not
  used by the fallback).

## What's changed (update summary)

- **MCP integration**: `SKILL.md` now instructs Claude to detect an
  MCP tool named `run_qfold` (from the qFold MCP server) and use it
  as the primary folding method.
- **Graceful fallback**: when no MCP server is found, Claude
  automatically switches to the existing HP‑lattice script, applying
  all its documented limits.
- **Unified user experience**: whether the full algorithm or the
  HP‑lattice model is used, Claude reports the method transparently
  and describes the results accordingly.
- **Updated naming note**: clarifies that the skill *can* now access
  the real QFold algorithm through the MCP server, even though the
  standalone skill files only contain the HP‑lattice fallback.

## Using this Skill in Claude Desktop

### Prerequisites
- Claude Desktop with skills support.
- (Optional, for full QFold) [`qFold-MCP`](https://github.com/qfoldit/qFold-MCP)
  server installed and running; configure its path in
  `claude_desktop_config.json` as described in that repository's README.
- (For HP‑lattice fallback) `amazon‑braket‑sdk` installed in Claude's
  execution environment.

### Quick start
1. Copy the `qfoldit-qfold/` folder into your Claude Desktop skills
   directory (or install via the `.skill` package if provided).
2. (Optional) Start the qFold MCP server — see its documentation for
   installation and configuration.
3. Ask Claude things like:
   - *"Fold the sequence HPHPPHHPHPPH on the HP lattice"*
   - *"Fold the protein sequence ALA‑GLY‑VAL‑..."* (full QFold)
4. Claude will determine whether the MCP server is available and choose
   the best available method. It will report the result along with
   which method was used.

### Interpreting the output
- **Full QFold (MCP)**: returns 3D structure (torsion angles),
  Psi4‑computed energy, and sampling statistics.
- **HP‑lattice fallback**: returns 2D lattice coordinates and an
  H‑H contact count. The output is explicitly labelled as a lattice
  model, not a physical 3D structure.

---

*For more details on the HP‑lattice implementation and its validation,
see `references/model_documentation.md` and the original QFold paper
(arXiv:2101.10279).*
