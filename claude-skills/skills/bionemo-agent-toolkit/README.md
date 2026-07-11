# qfoldit-bionemo-agent-toolkit

A compatible client for five NVIDIA BioNeMo NIM microservices — AlphaFold2,
DiffDock, MolMIM, Evo 2, Boltz-2 — plus documented, correct guidance on
AlphaFold3 (handled by the separate `alphafold3_mcp` MCP server, not
reimplemented here). Not an official NVIDIA or Google DeepMind integration.

See `SKILL.md` for the full usage guide, `references/api_reference.md` for
verified endpoint documentation, and `references/alphafold3_mcp.md` for
the AlphaFold3 integration note.

## Quick usage

```python
from bionemo_client import (
    predict_protein_structure_af2,
    dock_ligand,
    generate_molecules,
    generate_dna_sequence_evo2,
    predict_structure_boltz2,
)

# All five expect a self-hosted NIM container reachable at base_url
# (default http://localhost:8000). See SKILL.md for docker run commands.

structure = predict_protein_structure_af2("MNVIDIAIAMAI")
pdb_text = structure["pdbs"][0]

docking_result = dock_ligand(pdb_text, "CC(=O)OC1=CC=CC=C1C(=O)O")

molecules = generate_molecules("CC(=O)OC1=CC=CC=C1C(=O)O", n_samples=10)

dna = generate_dna_sequence_evo2("ACTGACTGACTG", num_tokens=50)

boltz_result = predict_structure_boltz2(
    polymers=[{"id": "A", "molecule_type": "protein", "sequence": "MALWMRLLPLLALLALWGPD"}],
    ligands=[{"id": "L1", "smiles": "CC(=O)OC1=CC=CC=C1C(=O)O"}],
)
```

## Testing

```bash
cd scripts
python3 smoke_test.py
```

Runs offline (payload/validation) tests with no GPU or API key needed. Set
`NIM_BASE_URL=http://localhost:8000` (or wherever your container is
listening) to additionally run a live health check.
