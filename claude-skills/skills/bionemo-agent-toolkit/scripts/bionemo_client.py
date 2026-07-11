"""
bionemo_client.py

Thin, honest HTTP clients for NVIDIA BioNeMo NIM microservices that do NOT
already have their own MCP server (unlike AlphaFold3, which is accessed
via the separately-installed `alphafold3_mcp` MCP server -- see
references/alphafold3_mcp.md; this module does not reimplement that).

Every endpoint path and request-field name below was verified directly
against NVIDIA's own official documentation (docs.nvidia.com/nim/bionemo/...)
during this session -- not guessed, and not carried over unchanged from an
older draft. Sources are cited per function. All functions target a
SELF-HOSTED NIM container (default base_url="http://localhost:8000"),
which is what NVIDIA's own quickstart guides document for each of these
models. NVIDIA also offers a shared, multi-tenant hosted endpoint at
https://integrate.api.nvidia.com for some models with a different path
prefix (/v1/biology/<org>/<model>/...); that hosted path was only found in
a third-party OpenAPI aggregation (apis.io), not confirmed against NVIDIA's
own docs pages in this session -- treat `base_url` overrides to the hosted
service as unverified until checked against the live API yourself.

No result is ever fabricated: every function propagates the real HTTP
error (status code + body) on failure rather than returning a plausible-
looking fake structure.
"""

from __future__ import annotations

import requests

DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_TIMEOUT_S = 300  # these models can take minutes, especially AF2/DiffDock


def _post(base_url: str, path: str, payload: dict, timeout: int) -> dict:
    url = f"{base_url.rstrip('/')}{path}"
    response = requests.post(url, json=payload, timeout=timeout)
    if not response.ok:
        # Never fabricate a result on failure -- surface the real error.
        raise RuntimeError(
            f"BioNeMo NIM request failed: POST {url} -> {response.status_code}\n{response.text}"
        )
    return response.json()


def health_check(base_url: str = DEFAULT_BASE_URL, timeout: int = 10) -> dict:
    """GET /v1/health/ready -- confirms a NIM container is up and the model
    is loaded. Documented identically across all BioNeMo NIMs (AF2,
    DiffDock, MolMIM, Evo2, Boltz-2)."""
    url = f"{base_url.rstrip('/')}/v1/health/ready"
    response = requests.get(url, timeout=timeout)
    return {"status_code": response.status_code, "body": response.json() if response.ok else response.text}


# ---------------------------------------------------------------------------
# AlphaFold2 -- docs.nvidia.com/nim/bionemo/alphafold2/latest/endpoints.html
# ---------------------------------------------------------------------------
def predict_protein_structure_af2(
    sequence: str,
    databases: list[str] | None = None,
    algorithm: str = "mmseqs2",
    relax_prediction: bool = True,
    base_url: str = DEFAULT_BASE_URL,
    timeout: int = DEFAULT_TIMEOUT_S,
) -> dict:
    """Predict a single-chain protein structure via AlphaFold2 NIM.

    Endpoint: POST /protein-structure/alphafold2/predict-structure-from-sequence
    Returns: {"pdbs": [<PDB-format structure string>, ...]}

    Args:
        sequence: single-letter amino acid sequence.
        databases: MSA databases to search, any of "uniref90", "mgnify",
            "small_bfd". NVIDIA's own docs recommend passing all three for
            best accuracy; defaults to ["uniref90"] here to keep runtime
            down unless the caller asks for more.
        algorithm: "mmseqs2" (GPU-accelerated, NVIDIA's recommended default
            for speed) or "jackhmmer" (what the original AlphaFold2 model
            was trained/validated with).
        relax_prediction: run structural relaxation to fix clashes
            (NVIDIA default: True).
    """
    if not sequence or not sequence.isalpha():
        raise ValueError(f"sequence must be a non-empty amino-acid string, got: {sequence!r}")
    payload = {
        "sequence": sequence,
        "databases": databases or ["uniref90"],
        "algorithm": algorithm,
        "relax_prediction": relax_prediction,
    }
    return _post(base_url, "/protein-structure/alphafold2/predict-structure-from-sequence", payload, timeout)


# ---------------------------------------------------------------------------
# DiffDock -- docs.nvidia.com/nim/bionemo/diffdock/latest/advanced-usage.html
# ---------------------------------------------------------------------------
def dock_ligand(
    protein_pdb: str,
    ligand: str,
    ligand_file_type: str = "smiles",
    num_poses: int = 10,
    time_divisions: int = 20,
    steps: int = 18,
    save_trajectory: bool = False,
    base_url: str = DEFAULT_BASE_URL,
    timeout: int = DEFAULT_TIMEOUT_S,
) -> dict:
    """Dock a small-molecule ligand against a protein structure via DiffDock NIM.

    Endpoint: POST /molecular-docking/diffdock/generate
    Returns: {"ligand_positions": [...], "position_confidence": [...]}
    (one entry per pose, ranked by confidence).

    Args:
        protein_pdb: PDB-format protein structure text (e.g. from
            predict_protein_structure_af2's "pdbs"[0]).
        ligand: SMILES string, or SDF/Mol2 file contents, depending on
            `ligand_file_type`.
        ligand_file_type: "smiles", "sdf", or "mol2".
        num_poses: number of candidate poses to generate (NVIDIA default 10).
        time_divisions, steps: diffusion process parameters (NVIDIA
            defaults 20 and 18 respectively -- do not change without a
            reason, they are tuned for the published model).
    """
    payload = {
        "protein": protein_pdb,
        "ligand": ligand,
        "ligand_file_type": ligand_file_type,
        "num_poses": num_poses,
        "time_divisions": time_divisions,
        "steps": steps,
        "save_trajectory": save_trajectory,
        "is_staged": False,
    }
    return _post(base_url, "/molecular-docking/diffdock/generate", payload, timeout)


# ---------------------------------------------------------------------------
# MolMIM -- docs.nvidia.com/nim/bionemo/molmim/latest/endpoints.html
# ---------------------------------------------------------------------------
def generate_molecules(
    seed_smiles: str,
    n_samples: int = 10,
    scaled_radius: float = 1.0,
    base_url: str = DEFAULT_BASE_URL,
    timeout: int = 120,
) -> dict:
    """Generate new candidate molecules by sampling MolMIM's latent space
    around a seed molecule (unguided -- no property optimization).

    Endpoint: POST /sampling
    Returns: {"generated": [<SMILES>, ...]} (implementation detail: exact
    response key names should be reconfirmed against a live NIM's /docs
    OpenAPI page, since this session's sourcing for /sampling's response
    schema was thinner than for /decode).

    For CMA-ES-guided optimization against a scoring function instead of
    unguided sampling, use the NIM's /generate endpoint directly (not
    wrapped here -- its scoring-function payload shape was not
    independently verified in this session).
    """
    payload = {"sequences": [seed_smiles], "num_molecules": n_samples, "scaled_radius": scaled_radius}
    return _post(base_url, "/sampling", payload, timeout)


def get_molecule_embedding(smiles: str, base_url: str = DEFAULT_BASE_URL, timeout: int = 60) -> dict:
    """Get MolMIM's fixed-size embedding for a molecule.
    Endpoint: POST /embedding. Returns {"embeddings": [[...]]}."""
    return _post(base_url, "/embedding", {"sequences": [smiles]}, timeout)


# ---------------------------------------------------------------------------
# Evo 2 -- docs.nvidia.com/nim/bionemo/evo2/latest/endpoints.html
# Requires an NVIDIA H100/H200-class GPU to self-host (40B model default).
# ---------------------------------------------------------------------------
def generate_dna_sequence_evo2(
    sequence: str,
    num_tokens: int = 100,
    temperature: float = 0.7,
    top_k: int = 3,
    top_p: float = 0.0,
    enable_sampled_probs: bool = False,
    base_url: str = DEFAULT_BASE_URL,
    timeout: int = DEFAULT_TIMEOUT_S,
) -> dict:
    """Generate DNA nucleotides continuing an input sequence, via the Evo 2
    genomic foundation model NIM (Hyena-based, up to 1M-token context,
    40B-parameter default checkpoint -- requires H100/H200-class GPU(s) to
    self-host).

    Endpoint: POST /biology/arc/evo2/generate
    Returns: {"sequence": "<generated nucleotides: A/T/G/C>", ...}
    """
    if not sequence or not set(sequence.upper()) <= set("ATGC"):
        raise ValueError(f"sequence must be non-empty and contain only A/T/G/C, got: {sequence!r}")
    payload = {
        "sequence": sequence,
        "num_tokens": num_tokens,
        "temperature": temperature,
        "top_k": top_k,
        "top_p": top_p,
        "enable_sampled_probs": enable_sampled_probs,
    }
    return _post(base_url, "/biology/arc/evo2/generate", payload, timeout)


# ---------------------------------------------------------------------------
# Boltz-2 -- docs.nvidia.com/nim/bionemo/boltz2/latest/inference.html
# Requires >=48GB VRAM GPU to self-host.
# ---------------------------------------------------------------------------
def predict_structure_boltz2(
    polymers: list[dict],
    ligands: list[dict] | None = None,
    constraints: list[dict] | None = None,
    recycling_steps: int = 3,
    sampling_steps: int = 50,
    diffusion_samples: int = 1,
    step_scale: float = 1.638,
    output_format: str = "mmcif",
    base_url: str = DEFAULT_BASE_URL,
    timeout: int = DEFAULT_TIMEOUT_S,
) -> dict:
    """Predict a biomolecular structure (protein/DNA/RNA, optionally with
    ligands) and, if requested, binding affinity, via Boltz-2 NIM.

    Endpoint: POST /biology/mit/boltz2/predict
    Returns: {"structures": [{"format": ..., "structure": ...}, ...],
              "confidence_scores": [...]}

    Args:
        polymers: list of {"id": str, "molecule_type": "protein"|"dna"|"rna",
            "sequence": str, "cyclic": bool (optional), "modifications":
            [{"ccd": str, "position": int}] (optional)}. At least one
            required; max 12 total, max 4096 residues per chain.
        ligands: optional list of {"id": str, "smiles": str} or
            {"id": str, "ccd": str}. Max 20.
        constraints: optional list of structural constraints, e.g.
            {"constraint_type": "pocket", "binder": <ligand id>,
             "contacts": [{"id": <chain id>, "residue_index": int}]}.
    """
    if not polymers:
        raise ValueError("polymers must contain at least one entry")
    payload = {
        "polymers": polymers,
        "recycling_steps": recycling_steps,
        "sampling_steps": sampling_steps,
        "diffusion_samples": diffusion_samples,
        "step_scale": step_scale,
        "output_format": output_format,
    }
    if ligands:
        payload["ligands"] = ligands
    if constraints:
        payload["constraints"] = constraints
    return _post(base_url, "/biology/mit/boltz2/predict", payload, timeout)
