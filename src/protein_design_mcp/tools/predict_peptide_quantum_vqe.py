"""
MCP tool: predict_peptide_quantum_vqe.

Thin re-export around pipelines/quantum_runner.py's implementation --
kept as its own tools/ module to match this repo's existing
one-tool-per-file convention (see tools/predict_bioactivity.py,
tools/train_qsar_model.py).
"""

from typing import Any

from protein_design_mcp.pipelines.quantum_runner import (
    predict_peptide_quantum_vqe as _predict_peptide_quantum_vqe,
)


async def predict_peptide_quantum_vqe(
    sequence: str,
    alpha: float = 0.1,
    shots: int = 1024,
) -> dict[str, Any]:
    """
    Estimate a peptide's low-energy conformation using QuPepFold's
    CVaR-optimized Variational Quantum Eigensolver.

    See pipelines/quantum_runner.py for full implementation notes,
    citations, and the ImportError-safe fallback behavior when the
    `qupepfold` package (and its Qiskit/Braket dependencies) isn't
    installed in the current environment.
    """
    return await _predict_peptide_quantum_vqe(sequence=sequence, alpha=alpha, shots=shots)
