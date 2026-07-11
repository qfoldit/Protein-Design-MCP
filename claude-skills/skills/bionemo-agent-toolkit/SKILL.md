---
name: qfoldit-bionemo-agent-toolkit
description: >
  Provides protein/nucleic-acid structure prediction, molecular docking, and
  molecule/DNA-sequence generation via five NVIDIA BioNeMo NIM models:
  AlphaFold2 (structure), DiffDock (docking), MolMIM (small-molecule
  generation), Evo 2 (genomic sequence generation), and Boltz-2
  (structure + binding affinity, multi-entity). AlphaFold3 is handled by a
  separate, already-existing MCP server (alphafold3_mcp) rather than
  reimplemented here. Use whenever the user asks to predict a protein/
  complex structure, dock a small molecule, generate new molecules, or
  generate/continue a DNA sequence. This skill is a compatible client, not
  an official NVIDIA or Google DeepMind integration.
---

# qFoldIT BioNeMo Agent Toolkit

A client for five NVIDIA BioNeMo NIM microservices that do not already have
their own MCP server, plus documented guidance on the one that does
(AlphaFold3, via `alphafold3_mcp`).

**Read `references/api_reference.md` before answering** — exact endpoint
paths and request/response shapes, each individually verified against
NVIDIA's own documentation. **Read `references/alphafold3_mcp.md`** before
saying anything about AlphaFold3 specifically — the integration approach
there was corrected this session (see below).

## What is implemented

| Component | Function | Requirement |
|---|---|---|
| AlphaFold2 | `predict_protein_structure_af2(sequence, ...)` | Self-hosted NIM container, NGC API key |
| DiffDock | `dock_ligand(protein_pdb, ligand, ...)` | Self-hosted NIM container, NGC API key |
| MolMIM | `generate_molecules(seed_smiles, ...)`, `get_molecule_embedding(smiles)` | Self-hosted NIM container, NGC API key |
| Evo 2 | `generate_dna_sequence_evo2(sequence, ...)` | Self-hosted NIM container, **H100/H200-class GPU** |
| Boltz-2 | `predict_structure_boltz2(polymers, ligands=..., ...)` | Self-hosted NIM container, **>=48GB VRAM GPU** |

All five are implemented in `scripts/bionemo_client.py` as thin, honest
`requests`-based HTTP clients against a self-hosted NIM container
(default `base_url="http://localhost:8000"`). Every endpoint/payload shape
was checked against NVIDIA's own docs during this session — see
`references/api_reference.md` for citations per model. On any HTTP
failure, the real error (status + body) is raised; no result is ever
fabricated.

## AlphaFold3 — different pattern, not reimplemented here

AlphaFold3 is **not** wrapped by this skill's own code. It already has a
separate, real MCP server — [MacromNex/alphafold3_mcp](https://github.com/MacromNex/alphafold3_mcp)
— which should be installed and connected in the same Claude session, the
same way qFoldIT treats unity-mcp, UnrealClaude, or kit-usd-agents
elsewhere: **when an existing bridge already covers a tool, use it
directly instead of duplicating it.** See `references/alphafold3_mcp.md`
for what was (and was not) verified about it this session — in
particular, its exact exposed tool names were not confirmed; introspect
the connected server's tool list rather than assuming names.

If `alphafold3_mcp` is connected, a common workflow is: predict a
multi-chain/ligand complex with its tools → take the resulting structure
→ feed it to this skill's `dock_ligand(...)` for downstream docking
against a new ligand.

## What is still NOT implemented

**OpenFold3, ESMFold, RFdiffusion, ProteinMPNN**, and other BioNeMo NIMs
are not wrapped — their schemas were not independently verified this
session. See `references/api_reference.md`'s closing section for how to
extend `bionemo_client.py` safely (verify the real endpoint/payload
against NVIDIA's docs or the container's own `/docs` page first — do not
guess a plausible-looking schema).

## Requirements common to all five implemented NIMs

- **Docker** with NVIDIA GPU runtime (`--gpus all` or `nvidia-docker`).
- **An NGC API key** (`NGC_API_KEY` env var) — get one at
  [build.nvidia.com](https://build.nvidia.com) or [ngc.nvidia.com](https://ngc.nvidia.com).
- Start the relevant container(s), e.g.:
  ```
  docker run --rm --name alphafold2 --runtime=nvidia -e NGC_API_KEY \
    -v $LOCAL_NIM_CACHE:/opt/nim/.cache -p 8000:8000 \
    nvcr.io/nim/deepmind/alphafold2:<version>
  ```
  (image names differ per model — see `references/api_reference.md`).
- First-run model downloads can take hours on a typical connection —
  set this expectation explicitly, don't let the person think it hung.
- Evo 2 and Boltz-2 have materially heavier GPU requirements than AF2/
  DiffDock/MolMIM (see the table above) — check this before promising a
  quick turnaround.

## How to handle a request

1. **Structure prediction**: single chain, speed matters → AlphaFold2.
   Multi-chain/ligand/DNA/RNA complex → check whether `alphafold3_mcp` is
   connected in this session (use it directly if so) or use Boltz-2
   (implemented here, also multi-entity, also predicts binding affinity).
2. **Docking**: `dock_ligand(...)` against a PDB structure from any of the
   above.
3. **Molecule generation**: `generate_molecules(...)` (MolMIM, unguided
   sampling around a seed SMILES).
4. **DNA sequence generation/continuation**: `generate_dna_sequence_evo2(...)`
   — remember the H100/H200 GPU requirement before promising this works
   on arbitrary hardware.
5. **Check prerequisites before attempting any call** — missing API key,
   missing GPU class, container not running. Explain exactly what's
   missing; never fabricate a result.
6. **Set runtime expectations**: AF2/DiffDock/MolMIM — seconds to minutes
   once the container is warm; Evo 2/Boltz-2 — minutes, GPU-class
   dependent; any of them — hours for the *first* container start while
   weights download.

## Testing status

- `scripts/smoke_test.py` — offline tests (payload construction, input
  validation, error propagation) for all five implemented clients, using
  `unittest.mock` to intercept HTTP calls — run these with no GPU/API key
  needed. Also runs a live `health_check()` if `NIM_BASE_URL` is set in
  the environment, against a container you've already started.
- No AF3-specific smoke test exists here by design — see
  `references/alphafold3_mcp.md` for why, and what a real one would need.

## References

- `references/api_reference.md` — verified endpoint/payload documentation
  for AlphaFold2, DiffDock, MolMIM, Evo 2, Boltz-2, with citations.
- `references/alphafold3_mcp.md` — corrected integration note for
  AlphaFold3 (separate MCP server, not reimplemented here).
