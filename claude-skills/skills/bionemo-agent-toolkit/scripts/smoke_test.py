"""
smoke_test.py

Tests bionemo_client.py at two levels:

1. OFFLINE (always runs, no network/GPU needed): input validation and
   payload construction, using unittest.mock to intercept requests.post
   and inspect exactly what would have been sent -- this catches bugs in
   this client's code without needing a live NIM.

2. LIVE (only runs if NIM_BASE_URL is set in the environment, e.g.
   "http://localhost:8000" for a self-hosted AF2/DiffDock/MolMIM/Evo2/
   Boltz-2 container you already started): calls health_check against
   the real, running service.

Run with: python3 smoke_test.py
If NIM_BASE_URL is not set, only the offline checks run -- this is
expected and reported clearly, not silently skipped without explanation.
"""

import os
import sys
from unittest.mock import patch, MagicMock

import bionemo_client as bc


def _fake_response(json_body, ok=True, status_code=200):
    resp = MagicMock()
    resp.ok = ok
    resp.status_code = status_code
    resp.json.return_value = json_body
    resp.text = str(json_body)
    return resp


def test_af2_payload_construction():
    with patch("bionemo_client.requests.post") as mock_post:
        mock_post.return_value = _fake_response({"pdbs": ["FAKE PDB TEXT"]})
        result = bc.predict_protein_structure_af2("MNVIDIAIAMAI", databases=["uniref90", "mgnify"])
        assert result == {"pdbs": ["FAKE PDB TEXT"]}
        called_url, called_kwargs = mock_post.call_args[0][0], mock_post.call_args[1]
        assert called_url.endswith("/protein-structure/alphafold2/predict-structure-from-sequence")
        assert called_kwargs["json"]["sequence"] == "MNVIDIAIAMAI"
        assert called_kwargs["json"]["databases"] == ["uniref90", "mgnify"]


def test_af2_rejects_invalid_sequence():
    try:
        bc.predict_protein_structure_af2("NOT-A-VALID-SEQ-123")
        assert False, "should have raised ValueError"
    except ValueError:
        pass


def test_diffdock_payload_construction():
    with patch("bionemo_client.requests.post") as mock_post:
        mock_post.return_value = _fake_response({"ligand_positions": ["SDF..."], "position_confidence": [0.8]})
        result = bc.dock_ligand("PDB TEXT", "CC(=O)OC1=CC=CC=C1C(=O)O", num_poses=5)
        assert result["position_confidence"] == [0.8]
        called_url, called_kwargs = mock_post.call_args[0][0], mock_post.call_args[1]
        assert called_url.endswith("/molecular-docking/diffdock/generate")
        assert called_kwargs["json"]["num_poses"] == 5
        assert called_kwargs["json"]["ligand_file_type"] == "smiles"


def test_evo2_rejects_invalid_sequence():
    try:
        bc.generate_dna_sequence_evo2("ACTGXYZ")
        assert False, "should have raised ValueError"
    except ValueError:
        pass


def test_evo2_payload_construction():
    with patch("bionemo_client.requests.post") as mock_post:
        mock_post.return_value = _fake_response({"sequence": "ACGT"})
        result = bc.generate_dna_sequence_evo2("ACTGACTG", num_tokens=8, top_k=1)
        assert result == {"sequence": "ACGT"}
        called_url, called_kwargs = mock_post.call_args[0][0], mock_post.call_args[1]
        assert called_url.endswith("/biology/arc/evo2/generate")
        assert called_kwargs["json"]["num_tokens"] == 8
        assert called_kwargs["json"]["top_k"] == 1


def test_boltz2_requires_at_least_one_polymer():
    try:
        bc.predict_structure_boltz2(polymers=[])
        assert False, "should have raised ValueError"
    except ValueError:
        pass


def test_boltz2_payload_construction():
    with patch("bionemo_client.requests.post") as mock_post:
        mock_post.return_value = _fake_response({"structures": [{"format": "mmcif", "structure": "..."}], "confidence_scores": [0.9]})
        polymers = [{"id": "A", "molecule_type": "protein", "sequence": "MALWMRLLPLLALLALWGPD"}]
        ligands = [{"id": "L1", "smiles": "CC(=O)OC1=CC=CC=C1C(=O)O"}]
        result = bc.predict_structure_boltz2(polymers, ligands=ligands)
        assert result["confidence_scores"] == [0.9]
        called_url, called_kwargs = mock_post.call_args[0][0], mock_post.call_args[1]
        assert called_url.endswith("/biology/mit/boltz2/predict")
        assert called_kwargs["json"]["polymers"] == polymers
        assert called_kwargs["json"]["ligands"] == ligands


def test_error_propagation_not_fabricated():
    """On a failed request, the client must raise with the real error body,
    never return a fabricated success-shaped result."""
    with patch("bionemo_client.requests.post") as mock_post:
        mock_post.return_value = _fake_response("Internal Server Error", ok=False, status_code=500)
        try:
            bc.predict_protein_structure_af2("MNVIDIAIAMAI")
            assert False, "should have raised RuntimeError on HTTP failure"
        except RuntimeError as e:
            assert "500" in str(e)


OFFLINE_TESTS = [
    test_af2_payload_construction,
    test_af2_rejects_invalid_sequence,
    test_diffdock_payload_construction,
    test_evo2_rejects_invalid_sequence,
    test_evo2_payload_construction,
    test_boltz2_requires_at_least_one_polymer,
    test_boltz2_payload_construction,
    test_error_propagation_not_fabricated,
]


def run_offline_tests():
    for t in OFFLINE_TESTS:
        t()
        print(f"PASS (offline): {t.__name__}")


def run_live_test_if_configured():
    base_url = os.environ.get("NIM_BASE_URL")
    if not base_url:
        print("\nNIM_BASE_URL not set -- skipping live test against a real NIM container.")
        print("(This is expected without a running NIM; set NIM_BASE_URL=http://localhost:8000")
        print(" after starting one, e.g. `docker run ... -p 8000:8000 nvcr.io/nim/deepmind/alphafold2:...`)")
        return
    print(f"\nNIM_BASE_URL={base_url} -- running live health_check()...")
    result = bc.health_check(base_url=base_url)
    print("Live health_check result:", result)


if __name__ == "__main__":
    run_offline_tests()
    run_live_test_if_configured()
    print("\nAll offline smoke tests passed.")
