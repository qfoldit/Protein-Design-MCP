"""
qfoldit-qfold: hybrid quantum-classical protein folding on the 2D HP
lattice model (Dill, 1985), executed on Amazon Braket.

IMPORTANT NAMING NOTE -- read this before trusting the name alone:
This module is named after the "QFold" project (Casares, Campos &
Martin-Delgado, arXiv:2101.10279; github.com/roberCO/QFold), which is a
real, published, much more sophisticated algorithm: it represents a
protein by its torsion angles (not a 2D lattice), computes energies with
Psi4 (real ab-initio quantum chemistry), initializes with a Minifold
deep-learning model, and performs a Szegedy quantum-walk-based quantized
Metropolis sampler. NONE of that is implemented here.

What IS implemented here is a much smaller, self-contained toy that
borrows only the general "quantum-biased sampling + classical scoring"
spirit of the idea and applies it to the well-known HP-lattice folding
model (Dill, 1985) -- a standard, honest teaching/prototyping
simplification used widely in the lattice-protein literature, decades
before and independently of the QFold paper. Concretely:

  1. A protein sequence is reduced to an H/P string (Hydrophobic/Polar),
     the standard simplification used for lattice-model folding demos.
  2. Each of the (n-2) internal bond directions (Left/Right/Up/Down
     relative to the previous step, i.e. a self-avoiding walk on a 2D
     lattice) is encoded with 2 qubits.
  3. A parameterized quantum circuit (RY rotations + a CNOT entangling
     ladder -- a QAOA-style ansatz) is run on Amazon Braket's
     LocalSimulator (free, runs on this machine -- no AWS account or
     cost) to produce a biased distribution over direction-bitstrings.
  4. We sample many shots, classically decode each bitstring into a
     lattice walk, DISCARD self-intersecting (physically invalid)
     walks, score the valid ones by H-H contact count (more non-bonded
     H-H adjacencies = lower/better energy in the HP model), and return
     the best.

This is genuinely hybrid quantum-classical, and can run on a real QPU by
swapping LocalSimulator for a Braket QPU device ARN -- but real-QPU
shots are billed by AWS and are NOT free; only the LocalSimulator path
is free.

Scope limits (be upfront about these):
  - Only supports short sequences (recommend <= 12-15 residues) --
    2 qubits per internal bond means qubit count grows linearly, but
    the *useful* walk space still grows exponentially, and shot budgets
    needed for good coverage grow with it.
  - 2D lattice only, not 3D.
  - The HP model is a well-known TEACHING/toy abstraction of folding
    energetics (hydrophobic collapse drives folding), not a physically
    accurate all-atom force field -- do not present its output as a
    real 3D structure prediction. For that, use the rosettafold3 tool.
  - The quantum circuit here does not encode the self-avoidance
    constraint (that would need a much larger auxiliary-qubit
    formulation); it only biases the sampled distribution away from
    uniform random, and self-avoidance is enforced classically after
    the fact by discarding invalid bitstrings. This is a materially
    weaker use of "quantum" than the real QFold's quantum-walk
    Metropolis sampler, which is why this module is documented so
    explicitly as a distinct, smaller thing.

See references/model_documentation.md for the classical-code validation
(brute-force cross-check) and a full side-by-side comparison against
the real published QFold algorithm.
"""

import itertools

try:
    from braket.circuits import Circuit
    from braket.devices import LocalSimulator
    _BRAKET_AVAILABLE = True
except ImportError:
    _BRAKET_AVAILABLE = False


_DIRECTIONS = ["L", "R", "U", "D"]
_DELTA = {"L": (-1, 0), "R": (1, 0), "U": (0, 1), "D": (0, -1)}
_OPPOSITE = {"L": "R", "R": "L", "U": "D", "D": "U"}


def _bits_to_direction(b0: int, b1: int) -> str:
    return _DIRECTIONS[b0 * 2 + b1]


def decode_walk(bitstring: str, n_residues: int):
    """Turn a bitstring of 2*(n_residues-2) bits into lattice coordinates.
    Returns None if the walk self-intersects (invalid) or backtracks
    directly onto itself."""
    coords = [(0, 0), (1, 0)]  # first two residues fixed to break lattice symmetry
    prev_dir = "R"
    occupied = set(coords)
    for i in range(n_residues - 2):
        b0 = int(bitstring[2 * i])
        b1 = int(bitstring[2 * i + 1])
        d = _bits_to_direction(b0, b1)
        if d == _OPPOSITE[prev_dir]:
            return None  # immediate backtrack -- physically invalid
        dx, dy = _DELTA[d]
        nxt = (coords[-1][0] + dx, coords[-1][1] + dy)
        if nxt in occupied:
            return None  # self-intersection -- physically invalid
        coords.append(nxt)
        occupied.add(nxt)
        prev_dir = d
    return coords


def hp_energy(coords, hp_string: str) -> int:
    """Number of non-sequential H-H lattice-adjacent contacts (higher = more
    favorable in the HP model; folding "energy" is conventionally -1 per
    contact, we return the raw contact count here for readability)."""
    contacts = 0
    n = len(coords)
    for i in range(n):
        if hp_string[i] != "H":
            continue
        for j in range(i + 2, n):  # skip sequence-adjacent neighbors
            if hp_string[j] != "H":
                continue
            dx = abs(coords[i][0] - coords[j][0])
            dy = abs(coords[i][1] - coords[j][1])
            if dx + dy == 1:
                contacts += 1
    return contacts


def brute_force_best_fold(hp_sequence: str) -> dict:
    """Exhaustive (non-quantum) ground truth: enumerate every one of the
    4**(n-2) direction-bitstrings, keep the valid self-avoiding walks, and
    return the true best-contact fold. Only tractable for short sequences
    (used here purely as a correctness check for fold_hp_sequence, not as
    a production tool -- 4**(n-2) becomes impractical well before the
    n<=15 limit that fold_hp_sequence enforces for other reasons).

    This is the reference implementation used to validate that the
    quantum-sampling path in fold_hp_sequence() is scoring and decoding
    correctly, the same role the H2/STO-3G published benchmark plays for
    the qfoldit-quantum skill: an external, independently-computable
    ground truth rather than a self-consistency check.
    """
    hp_sequence = hp_sequence.upper()
    n_residues = len(hp_sequence)
    n_bonds = n_residues - 2
    n_qubits = 2 * n_bonds

    best = None
    n_valid = 0
    for bits in itertools.product("01", repeat=n_qubits):
        bitstring = "".join(bits)
        coords = decode_walk(bitstring, n_residues)
        if coords is None:
            continue
        n_valid += 1
        energy = hp_energy(coords, hp_sequence)
        if best is None or energy > best["contacts"]:
            best = {"bitstring": bitstring, "contacts": energy, "coordinates": coords}

    return {
        "hp_sequence": hp_sequence,
        "n_qubits": n_qubits,
        "total_bitstrings": 2 ** n_qubits,
        "valid_self_avoiding_walks": n_valid,
        "best_fold": best,
    }


def _build_qaoa_style_circuit(n_qubits: int, betas, gammas) -> "Circuit":
    """A lightweight QAOA-style ansatz: alternating entangling CNOT ladder
    and RY-rotation layers. Not tied to a specific cost Hamiltonian
    compilation (that would require a much larger auxiliary-qubit
    encoding for self-avoidance constraints); instead this biases the
    sampled distribution away from uniform random, and validity/energy
    scoring happens classically in decode_walk / hp_energy."""
    circ = Circuit()
    for q in range(n_qubits):
        circ.h(q)
    for beta, gamma in zip(betas, gammas):
        for q in range(n_qubits - 1):
            circ.cnot(q, q + 1)
            circ.rz(q + 1, gamma)
            circ.cnot(q, q + 1)
        for q in range(n_qubits):
            circ.ry(q, beta)
    return circ


def fold_hp_sequence(hp_sequence: str, shots: int = 500, qaoa_layers: int = 2, seed: int = 0) -> dict:
    """
    Fold an H/P sequence (e.g. "HPHPPHHPHPPH") on the 2D lattice using a
    QAOA-style circuit on Amazon Braket's free LocalSimulator, then
    classically pick the best valid self-avoiding walk found among the
    sampled bitstrings.

    hp_sequence: string over {"H","P"} only. Use classify_hp() first if
    you have a real amino-acid sequence.
    """
    if not _BRAKET_AVAILABLE:
        return {
            "error": (
                "amazon-braket-sdk is not installed in this environment. "
                "Add it to requirements.txt and rebuild the image -- "
                "`pip install amazon-braket-sdk`. The LocalSimulator device "
                "used here is free and requires no AWS account."
            )
        }

    hp_sequence = hp_sequence.upper()
    if any(c not in "HP" for c in hp_sequence):
        return {"error": "hp_sequence must contain only 'H' and 'P' characters."}
    n_residues = len(hp_sequence)
    if n_residues < 3:
        return {"error": "Need at least 3 residues to have any internal bonds."}
    if n_residues > 15:
        return {
            "error": (
                f"n_residues={n_residues} exceeds this tool's practical limit (~15). "
                f"Qubit count and required shot budget both grow with sequence "
                f"length; longer sequences need a proper constrained QUBO "
                f"encoding, which is out of scope here."
            )
        }

    n_bonds = n_residues - 2
    n_qubits = 2 * n_bonds

    import numpy as np
    rng = np.random.default_rng(seed)
    betas = rng.uniform(0, np.pi, size=qaoa_layers)
    gammas = rng.uniform(0, 2 * np.pi, size=qaoa_layers)

    circ = _build_qaoa_style_circuit(n_qubits, betas, gammas)
    circ.probability()

    device = LocalSimulator()
    task = device.run(circ, shots=shots)
    result = task.result()
    counts = result.measurement_counts  # dict: bitstring -> count

    best = None
    n_valid = 0
    for bitstring, count in counts.items():
        coords = decode_walk(bitstring, n_residues)
        if coords is None:
            continue
        n_valid += 1
        energy = hp_energy(coords, hp_sequence)
        if best is None or energy > best["contacts"]:
            best = {
                "bitstring": bitstring,
                "shots_observed": count,
                "contacts": energy,
                "coordinates": coords,
            }

    if best is None:
        return {
            "error": (
                "No self-avoiding walk was found among the sampled shots -- "
                "try increasing `shots`. This is a known limitation of "
                "unconstrained sampling for longer sequences."
            ),
            "n_qubits": n_qubits,
            "shots": shots,
        }

    return {
        "hp_sequence": hp_sequence,
        "n_residues": n_residues,
        "n_qubits": n_qubits,
        "shots": shots,
        "valid_self_avoiding_walks_found": n_valid,
        "best_fold": {
            "direction_bitstring": best["bitstring"],
            "lattice_coordinates": best["coordinates"],
            "h_h_contacts": best["contacts"],
            "hp_model_energy": -best["contacts"],
        },
        "device": "braket.LocalSimulator (free, local, classical simulation of the circuit)",
        "note": (
            "2D HP-lattice toy model, not an all-atom structure prediction. "
            "Quantum circuit proposes candidate walks; classical code filters "
            "for validity (self-avoidance) and scores them. For real 3D "
            "structure prediction use the rosettafold3 tool instead."
        ),
    }


def classify_hp(amino_acid_sequence: str) -> dict:
    """
    Convert a one-letter amino-acid sequence into the H(ydrophobic)/
    P(olar) alphabet used by fold_hp_sequence(), via the standard
    Kyte-Doolittle-derived H/P split used in HP-model literature
    (hydrophobic: A,V,L,I,M,F,W,C; polar/charged: everything else).
    """
    hydrophobic = set("AVLIMFWC")
    seq = amino_acid_sequence.upper().strip()
    invalid = [c for c in seq if c not in "ACDEFGHIKLMNPQRSTVWY"]
    if invalid:
        return {"error": f"Unrecognized amino-acid letters: {sorted(set(invalid))}"}
    hp = "".join("H" if c in hydrophobic else "P" for c in seq)
    return {"amino_acid_sequence": seq, "hp_sequence": hp}
