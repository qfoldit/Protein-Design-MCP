"""
MCP tool: predict_structure_quantum_walk.

Thin re-export around pipelines/quantum_runner.py's classical,
quantum-walk-inspired torsion-angle Metropolis simulation -- kept as
its own tools/ module to match this repo's existing one-tool-per-file
convention.
"""

from typing import Any

from protein_design_mcp.pipelines.quantum_runner import (
    simulate_quantum_walk_fold as _simulate_quantum_walk_fold,
)


async def predict_structure_quantum_walk(
    sequence: str,
    steps: int = 500,
    continuous_space: bool = True,
) -> dict[str, Any]:
    """
    Simulate a continuous off-lattice, quantum-walk-inspired Metropolis
    fold for the given sequence and return a 3D backbone coordinate
    tensor (N/CA/C atoms per residue, built via NeRF from the resulting
    phi/psi torsion angles).

    See pipelines/quantum_runner.py's module docstring for an honest
    account of what is and isn't a faithful classical stand-in for the
    real QFold quantum-walk algorithm (Casares, Campos, Martin-Delgado,
    2022, Quantum Sci. Technol. 7, 025013).
    """
    return await _simulate_quantum_walk_fold(
        sequence=sequence,
        steps=steps,
        continuous_space=continuous_space,
    )
