# qFoldIT Protein Design MCP

**This repository has two parts under two different licenses — see `NOTICE` for full attribution.**

1. **The MCP server** (this directory, outside `claude-skills/`) — Apache-2.0, based on [jasonkim8652/protein-design-mcp](https://github.com/jasonkim8652/protein-design-mcp). Currently unmodified from upstream; installation below correctly points to the upstream project's own PyPI/Docker/GitHub since qFoldIT has not yet published an independent build.
2. **`claude-skills/`** — MIT, originally authored by qFoldIT: 21 Claude Skills covering scientific simulation (VQE, protein folding, bio-mining, corrosion, plant growth...) and digital-twin engine adapters (Unreal, Unity, Unigine, Omniverse, Apple, Three.js). See `claude-skills/README.md`.

Actual current directory layout (server portion; run `tree claude-skills/` separately for the skills side):

```
Protein-Design-MCP/
├── README.md
├── NOTICE                    ← licensing/attribution for both parts of this repo
├── LICENSE                   ← Apache-2.0 (governs everything EXCEPT claude-skills/)
├── pyproject.toml
├── docker-compose.yml
├── Dockerfile*
├── src/protein_design_mcp/
│   ├── server.py
│   ├── pipelines/            (alphafold2, boltz_runner, esmfold, openmm_runner,
│   │                          proteinmpnn, pyrosetta_runner, rfdiffusion)
│   ├── tools/                (19 MCP tools -- design, predict, score, analyze)
│   ├── resources/
│   └── utils/
├── tests/
└── claude-skills/            ← MIT license (own LICENSE file), see claude-skills/README.md
```

[![PyPI](https://img.shields.io/pypi/v/protein-design-mcp)](https://pypi.org/project/protein-design-mcp/)
[![Docker Hub](https://img.shields.io/docker/v/jeonghyeonkim8652/protein-design-mcp?label=docker%20hub&logo=docker)](https://hub.docker.com/r/jeonghyeonkim8652/protein-design-mcp)
[![GHCR](https://img.shields.io/badge/ghcr.io-protein--design--mcp-blue?logo=github)](https://github.com/jasonkim8652/protein-design-mcp/pkgs/container/protein-design-mcp)
[![Smithery](https://smithery.ai/badge/protein-design-mcp)](https://smithery.ai/server/protein-design-mcp)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)

An [MCP](https://modelcontextprotocol.io) server that gives LLM agents access to computational protein design tools. Ask your LLM to design binders, generate de novo folds, predict structures, score interfaces, or relax with Rosetta — it calls the right tool automatically.

**25 tools total**, spanning generative design, structure prediction, physics-based scoring, analysis, bioactivity/QSAR prediction, and quantum-computing-assisted peptide folding. Built on RFdiffusion, ProteinMPNN, ESMFold, AlphaFold2, **Boltz-2**, **PyRosetta**, ESM2, OpenMM, **ZairaChem**, **QuPepFold** (CVaR-VQE), and a classical simulation inspired by **QFold**'s quantum-walk Metropolis algorithm. 3D output from any of these -- or from external MCPs like BindCraft's `bindcraft_mcp` -- can be exported to OpenUSD (`uag_exporter.py`) for NVIDIA Omniverse / NanoVer VR / Unreal / Unity.

| Distribution | Tools out-of-the-box | Extras |
|---|---|---|
| `pip install "protein-design-mcp[gpu]"` | 13 core tools | `[rosetta]` (license required), `[boltz]` (isolated venv) |
| `docker pull jeonghyeonkim8652/protein-design-mcp` | 13 core tools (GPU), 10 (CPU) | PyRosetta / Boltz not bundled (license + torch conflict) |

The 6 non-bundled tools (`rosetta_*` x4, `predict_*_boltz` x2) install cleanly via pip extras — see [Optional Tools](#optional-tools-pyrosetta--boltz-2).

## claude-skills/ (qFoldIT's own work, MIT-licensed)

The `claude-skills/` subdirectory is a self-contained Claude Code plugin — 20 skills spanning scientific simulation (VQE quantum chemistry, HP-lattice protein folding, bio-mining kinetics, pipeline corrosion, plant growth/NPK modeling, L-systems, plastic pyrolysis) and a Universal Assembly Graph (UAG) based digital-twin pipeline with adapters for Unreal, Unity, Unigine, OpenUSD/Omniverse, Apple RealityKit, and Three.js. It has its own `LICENSE` (MIT), `README.md`, `CITATION.cff`, and governance docs (`CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`). To install just this plugin in Claude Code, point a marketplace add at the `claude-skills/` directory rather than the repo root. Full details: [`claude-skills/README.md`](claude-skills/README.md).

---

## MCP Server (upstream: jasonkim8652/protein-design-mcp, Apache-2.0)

### Installation



Choose the method that fits your situation. Listed from simplest to most customizable.

---

### 1. Auto-Setup (Recommended)

One command. Detects your environment, pulls Docker if available, writes MCP client config.

```bash
pip install protein-design-mcp
protein-design-mcp-setup
```

What it does:
- Checks for Docker and NVIDIA GPU
- Pulls the Docker image (or falls back to local Python mode)
- Writes config for Claude Desktop or Claude Code automatically
- Model weights download lazily on first tool call

Options:
```bash
protein-design-mcp-setup --docker    # Force Docker mode
protein-design-mcp-setup --local     # Force local Python mode
protein-design-mcp-setup --modal URL # Use Modal cloud GPU
protein-design-mcp-setup -y          # Skip confirmation prompt
```

---

### 2. Smithery

If you use [Smithery](https://smithery.ai):

```bash
npx -y @smithery/cli install protein-design-mcp --client claude
```

---

### 3. pip + Manual Config

```bash
pip install protein-design-mcp                      # Core CPU (12 tools -- includes predict_structure_quantum_walk and export_structure_to_spatial_twin, no extra deps)
pip install "protein-design-mcp[gpu]"               # + PyTorch + ESM (15 tools)
pip install "protein-design-mcp[gpu,rosetta]"       # + PyRosetta (19 tools) *
pip install "protein-design-mcp[gpu,rosetta,boltz]" # + Boltz-2 (21 of 25 tools -- ZairaChem's 3 tools and predict_peptide_quantum_vqe need separate envs, see below) **
```

\* PyRosetta requires a [free academic license](https://www.pyrosetta.org/downloads). The `[rosetta]` extra installs `pyrosetta-installer` which fetches the wheel after you accept the license.

\** Boltz needs `torch>=2.2` which conflicts with RFdiffusion's `torch==2.0.1`. Install in an isolated venv, not alongside `[gpu]`.

Add to your MCP client config:

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):
```json
{
  "mcpServers": {
    "protein-design": {
      "command": "protein-design-mcp"
    }
  }
}
```

**Claude Code** (`.mcp.json` in your project root):
```json
{
  "mcpServers": {
    "protein-design": {
      "command": "protein-design-mcp"
    }
  }
}
```

Restart your client after editing config.

---

### 4. Docker

Isolated, reproducible environments with all computational backends pre-installed. **Primary registry: [Docker Hub](https://hub.docker.com/r/jeonghyeonkim8652/protein-design-mcp).**

#### Pull

```bash
# Latest release (GPU image, ~12GB, bundles RFdiffusion + ProteinMPNN + ESMFold + ColabFold + ESM2 + OpenMM)
docker pull jeonghyeonkim8652/protein-design-mcp:latest
docker pull jeonghyeonkim8652/protein-design-mcp:1.0.0   # pin a specific version
```

GHCR mirror (equivalent):
```bash
docker pull ghcr.io/jasonkim8652/protein-design-mcp:latest
```

Tools included in the image: **13 of 19**. The 6 license/conflict-gated tools (`rosetta_*`, `predict_*_boltz`) are not bundled — install via pip extras instead. See [Optional Tools](#optional-tools-pyrosetta--boltz-2).

#### Run (GPU)

Model weights download lazily on first use and persist in a named volume so subsequent runs are instant:

```bash
docker volume create protein-design-models

docker run --rm -i \
  --gpus all \
  -v protein-design-models:/models \
  -v $(pwd):/data \
  jeonghyeonkim8652/protein-design-mcp:latest
```

GPU mode requires [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html). The image stdin/stdout is the MCP protocol — you normally don't run it directly, your MCP client does (see below).

#### Run (CPU)

No GPU — works with the same image:

```bash
docker run --rm -i \
  -e DEVICE=cpu \
  -v protein-design-models:/models \
  -v $(pwd):/data \
  jeonghyeonkim8652/protein-design-mcp:latest
```

CPU mode disables `design_binder`, `design_fold`, `generate_backbone` (RFdiffusion is GPU-only) → 12 tools available.

#### MCP client config

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS, or `%APPDATA%/Claude/claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "protein-design": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm", "--gpus", "all",
        "-e", "SKIP_MODEL_DOWNLOAD=true",
        "-v", "protein-design-models:/models",
        "-v", "/absolute/path/to/your/pdbs:/data",
        "jeonghyeonkim8652/protein-design-mcp:latest"
      ]
    }
  }
}
```

**Claude Code** (`.mcp.json` in your project root):

```json
{
  "mcpServers": {
    "protein-design": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm", "--gpus", "all",
        "-v", "protein-design-models:/models",
        "-v", "${workspaceFolder}:/data",
        "jeonghyeonkim8652/protein-design-mcp:latest"
      ]
    }
  }
}
```

For **CPU-only hosts**, drop `"--gpus", "all"` and add `"-e", "DEVICE=cpu"`.

Restart your MCP client after editing config.

#### Tags available on Docker Hub

| Tag | Purpose |
|---|---|
| `latest` | Tracks the most recent release on `main` |
| `1.0.0`, `1.0`, `1` | Semver-pinned (recommended for production) |
| `<sha>` | Exact commit SHA (immutable) |

Check the full tag list at [hub.docker.com/r/jeonghyeonkim8652/protein-design-mcp/tags](https://hub.docker.com/r/jeonghyeonkim8652/protein-design-mcp/tags).

#### Build locally

```bash
git clone https://github.com/jasonkim8652/protein-design-mcp.git
cd protein-design-mcp
docker build -t protein-design-mcp:dev .                  # GPU image
docker build -f Dockerfile.lite -t protein-design-mcp:lite .  # CPU-only, ~3-5GB
```

The GPU build needs ~30 GB free disk and ~20 minutes.

---

### 5. Modal (Cloud GPU)

No local GPU? Deploy to your own [Modal](https://modal.com) account. Serverless GPU on demand, billed per-second (~$1.10/hr A10G). Containers auto-stop after 5 min idle.

```bash
pip install modal
modal setup                          # One-time: link your Modal account

git clone https://github.com/jasonkim8652/protein-design-mcp.git
cd protein-design-mcp
pip install -e .
modal deploy deploy/modal_app.py     # Deploy GPU endpoint
```

After deploying, Modal prints your endpoint URL. Connect via the local proxy:

```json
{
  "mcpServers": {
    "protein-design": {
      "command": "python",
      "args": ["-m", "protein_design_mcp.modal_proxy"],
      "env": {
        "MODAL_URL": "https://<your-workspace>--protein-design-tools.modal.run"
      }
    }
  }
}
```

21 of 25 tools available (ZairaChem's 3 tools and `predict_peptide_quantum_vqe` need their own separate environments, see below -- not part of this Modal image). Local PDB files are automatically sent to Modal.

---

### 6. From Source (Development)

```bash
git clone https://github.com/jasonkim8652/protein-design-mcp.git
cd protein-design-mcp
pip install -e ".[gpu,dev]"
python -m protein_design_mcp.server
```

For full GPU pipeline, install [RFdiffusion](https://github.com/RosettaCommons/RFdiffusion) and [ProteinMPNN](https://github.com/dauparas/ProteinMPNN) separately and set `RFDIFFUSION_PATH` / `PROTEINMPNN_PATH`.

---

## CPU vs GPU

| | GPU | CPU |
|---|---|---|
| **Tools available** | All 19 | 14 (no `design_binder`, `design_fold`, `generate_backbone`, `predict_structure_boltz`, `predict_affinity_boltz`) |
| **RFdiffusion** | ~30s/design | Disabled |
| **Boltz-2** | ~10-30s | Disabled |
| **ESMFold** | ~10s | ~2-5min |
| **ESM2** | ~5s | ~30s |
| **ProteinMPNN** | ~30s | ~5-10min |
| **PyRosetta** | Fast | Comparable |
| **OpenMM** | Fast | Comparable |
| **AlphaFold2 (API)** | Works | Works |

GPU is auto-detected. To force CPU mode, set `DEVICE=cpu`.

## Available Tools

Tools marked **(optional)** are not bundled in the Docker image. See [Optional Tools](#optional-tools-pyrosetta--boltz-2) for install.

### Design & Generation

#### `design_binder` (GPU only)

End-to-end binder design: RFdiffusion (backbone) -> ProteinMPNN (sequence) -> ESMFold (validation).

```json
{
  "target_pdb": "path/to/target.pdb",
  "hotspot_residues": ["A45", "A46", "A49"],
  "num_designs": 10,
  "binder_length": 80
}
```

Returns ranked designs with sequences, PDB structures, pLDDT, pTM, and mpnn_score.

#### `generate_backbone` (GPU only)

De novo backbone generation using unconditional RFdiffusion. No target protein required.

```json
{"length": 100, "num_designs": 5}
```

#### `design_fold` (GPU only)

End-to-end de novo fold design: RFdiffusion (unconditional backbone) → ProteinMPNN (sequence) → AlphaFold2 (validation, falls back to ESMFold). Returns ranked designs filtered by pLDDT/pTM.

```json
{"length": 120, "num_designs": 10, "num_sequences_per_backbone": 4}
```

#### `design_sequence`

Design sequences for a given backbone using ProteinMPNN. Unlike `optimize_sequence` (which refines an existing sequence), this designs from scratch given only a backbone PDB — the correct tool after `generate_backbone`. Optionally validates each design with ESMFold.

```json
{
  "backbone_pdb": "path/to/backbone.pdb",
  "num_sequences": 8,
  "sampling_temp": 0.1,
  "fixed_positions": [1, 5, 10],
  "validate": true
}
```

#### `optimize_sequence`

Redesign a protein sequence for improved stability and/or binding affinity using ProteinMPNN.

```json
{
  "current_sequence": "MTKLYV...",
  "target_pdb": "path/to/target.pdb",
  "optimization_target": "both",
  "fixed_positions": [1, 5, 10]
}
```

### Structure Prediction

#### `predict_structure`

Single-chain structure prediction via ESMFold (fast) or AlphaFold2 (accurate).

```json
{"sequence": "MTKLYV...", "predictor": "esmfold"}
```

Returns PDB file, mean pLDDT, pTM, per-residue confidence.

#### `predict_complex`

Multi-chain complex structure prediction using AlphaFold2-Multimer.

```json
{
  "sequences": ["BINDER_SEQ...", "TARGET_SEQ..."],
  "chain_names": ["binder", "target"]
}
```

Returns predicted complex PDB with pLDDT, pTM/ipTM, and PAE matrix.

#### `predict_structure_boltz` (GPU only, **optional**)

Single-chain structure prediction with [Boltz-2](https://github.com/jwohlwend/boltz) — a fast, high-accuracy open model competitive with AF2.

```json
{"sequence": "MTKLYV...", "model": "boltz2", "num_samples": 1}
```

Returns predicted PDB, mean pLDDT, pTM.

#### `predict_affinity_boltz` (GPU only, **optional**)

Multi-chain complex + binding affinity prediction with Boltz-2. Returns affinity score alongside the predicted complex structure and confidence metrics.

```json
{"sequences": ["BINDER_SEQ...", "TARGET_SEQ..."], "model": "boltz2"}
```

#### `validate_design`

Predict structure of a designed sequence and optionally compute RMSD against a reference.

```json
{
  "sequence": "MTKLYV...",
  "expected_structure": "path/to/reference.pdb",
  "predictor": "esmfold"
}
```

### Analysis & Scoring

#### `analyze_interface`

Analyze protein-protein interface: contacts, buried surface area, hydrogen bonds, salt bridges.

```json
{"complex_pdb": "path/to/complex.pdb", "chain_a": "A", "chain_b": "B"}
```

#### `suggest_hotspots`

Predict binding hotspots from multiple sources. Accepts protein names, UniProt IDs, PDB IDs, or file paths.

```json
{"target": "EGFR", "criteria": "druggable", "include_literature": true}
```

Criteria: `"exposed"` (SASA), `"druggable"` (pocket geometry), `"conserved"` (evolution).

#### `score_stability`

Protein stability scoring via ESM2 pseudo-log-likelihood. Optionally score individual mutations.

```json
{
  "sequence": "MTKLYV...",
  "mutations": ["A42G", "L55V"]
}
```

Returns overall stability score and per-mutation delta log-likelihood (stabilizing/destabilizing).

#### `energy_minimize`

All-atom energy minimization with OpenMM (AMBER14 + implicit solvent).

```json
{"pdb_path": "path/to/structure.pdb", "num_steps": 500, "solvent": "implicit"}
```

Returns minimized PDB, energy change, and RMSD from input.

### Rosetta (Physics-Based Design & Scoring) — **optional**

PyRosetta-backed tools for physics-based scoring, relaxation, and fixed-backbone design. All use `ref2015` by default. **Not bundled in Docker** — install via `pip install "protein-design-mcp[rosetta]"` after accepting the PyRosetta license.

#### `rosetta_score`

Score a structure with a Rosetta energy function. Returns total score, per-residue energies, and component breakdown.

```json
{"pdb_path": "path/to/structure.pdb", "score_function": "ref2015"}
```

#### `rosetta_relax`

FastRelax protocol to find a low-energy conformation. Returns relaxed PDB, energy before/after, and CA-RMSD from input.

```json
{"pdb_path": "path/to/structure.pdb", "nstruct": 1}
```

#### `rosetta_interface_score`

Interface analysis via `InterfaceAnalyzerMover`: binding energy (dG_separated), buried surface area (dSASA), interface hydrogen bonds, packstat.

```json
{"pdb_path": "path/to/complex.pdb", "chains": "A_B"}
```

#### `rosetta_design`

Fixed-backbone redesign pipeline: score → PackRotamers → MinMover → score. Returns designed PDB, mutation list, and energy delta. Composite tool — in benchmark mode, call `rosetta_score` / `rosetta_relax` individually instead.

```json
{"pdb_path": "path/to/input.pdb", "chains": "A_B", "fixed_positions": [12, 14, 18]}
```

### Bioactivity / QSAR (**optional**, see [Optional Tools: ZairaChem](#optional-tools-zairachem-bioactivityqsar-prediction))

#### `predict_bioactivity` (**optional**)

Score candidate molecules against a trained ZairaChem model (yours, or a published pretrained one e.g. from the H3D Centre screening cascade). Classification only.

```json
{"input_csv": "path/to/candidates.csv", "model_dir": "path/to/model", "output_dir": "path/to/output"}
```

#### `train_qsar_model` (**optional**)

Train a new binary-classification QSAR model from labeled SMILES + activity data.

```json
{"input_csv": "path/to/training_data.csv", "output_dir": "path/to/model_output", "cutoff": 6.5, "direction": "high"}
```

#### `predict_admet_profile` (**optional**)

Run ZairaChem's `predict` across every endpoint you've configured (solubility, toxicity, malaria/tuberculosis bioactivity via `ZAIRACHEM_MODEL_<ENDPOINT>` env vars, e.g. from the H3D Centre screening cascade) for a single SMILES, and return one combined profile. Endpoints with no configured model report `"status": "not_configured"` rather than a fabricated score.

```json
{"smiles": "CCO"}
```

### Quantum Peptide Folding & Spatial Digital Twin (**optional**, see [Optional Tools: QuPepFold](#optional-tools-qupepfold-quantum-peptide-folding))

#### `predict_peptide_quantum_vqe` (**optional**)

Estimate a low-energy peptide conformation with QuPepFold's CVaR-optimized Variational Quantum Eigensolver (Qiskit Aer / Amazon Braket / IonQ Aria-1). Best suited to short peptides (≲10 residues). If `qupepfold` isn't installed in the active environment, returns a structured `"status": "unavailable"` result instead of failing.

```json
{"sequence": "ACDEFGHIK", "alpha": 0.1, "shots": 1024}
```

#### `predict_structure_quantum_walk`

Classical, quantum-walk-inspired torsion-angle (φ,ψ) Metropolis simulation, loosely modeled on QFold's continuous off-lattice algorithm, followed by NeRF backbone reconstruction. Returns a 3D N/CA/C coordinate tensor. Pure Python — no extra dependency, available in every install including core CPU.

```json
{"sequence": "ACDEFGHIK", "steps": 500, "continuous_space": true}
```

Feed the resulting `coordinates` (or Boltz-2's output, reshaped similarly) into `uag_exporter.export_to_openusd()` to get a `.usda` file for NVIDIA Omniverse, NanoVer VR, Unreal Engine 5, or Unity. Uses real `pxr`/`UsdGeom` if `usd-core` is installed (`pip install "protein-design-mcp[usd]"`); otherwise falls back to a hand-written, schema-valid ASCII `.usda` writer with no extra dependency.

### Utility

#### `get_design_status`

Check progress of long-running design jobs.

```json
{"job_id": "abc123"}
```

#### `export_structure_to_spatial_twin`

Export any existing PDB file to OpenUSD (.usda), for NVIDIA Omniverse / NanoVer VR / Unreal Engine 5 / Unity. Source-agnostic -- works on this server's own PDB output as well as PDB output from external MCPs (see [Optional Tools: MacromNex/BindCraft](#optional-tools-macromnexbindcraft-binder-design)).

```json
{"pdb_path": "path/to/structure.pdb", "output_path": "path/to/output.usda"}
```

## Optional Tools: PyRosetta + Boltz-2

These 6 tools (`rosetta_score`, `rosetta_relax`, `rosetta_interface_score`, `rosetta_design`, `predict_structure_boltz`, `predict_affinity_boltz`) are **not included in the Docker image** because:

- **PyRosetta** requires a Rosetta license (free for academics, paid for commercial) and cannot be legally redistributed in a container.
- **Boltz-2** needs `torch>=2.2`, while RFdiffusion's dependency chain (e3nn, dgl) pins `torch==2.0.1`. Both cannot coexist in one venv.

### Installing PyRosetta tools

1. Register at [pyrosetta.org/downloads](https://www.pyrosetta.org/downloads) and accept the license.
2. Install alongside the MCP server:
   ```bash
   pip install "protein-design-mcp[gpu,rosetta]"
   python -c "import pyrosetta_installer; pyrosetta_installer.install_pyrosetta()"
   ```
3. Verify: `python -c "import pyrosetta; print(pyrosetta.__version__)"`

The 4 `rosetta_*` tools become available immediately.

### Installing Boltz-2 tools

Create a separate virtualenv (isolated from the RFdiffusion torch stack):

```bash
python -m venv ~/.venvs/protein-design-boltz
source ~/.venvs/protein-design-boltz/bin/activate
pip install "protein-design-mcp[boltz]"
```

Then point your MCP client at this venv's `protein-design-mcp` binary (or run two MCP servers — one for RFdiffusion/Docker tools, one for Boltz).

### Configuring two MCP servers side-by-side

```json
{
  "mcpServers": {
    "protein-design": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "--gpus", "all",
               "-v", "protein-design-models:/models",
               "jeonghyeonkim8652/protein-design-mcp:latest"]
    },
    "protein-design-boltz": {
      "command": "/home/you/.venvs/protein-design-boltz/bin/protein-design-mcp"
    }
  }
}
```

Your LLM will see all 20 of those tools through the two servers (includes `predict_structure_quantum_walk`, which needs no extra dependency) and call whichever is appropriate (add a third server entry pointing at a zairachem conda env's Python for the 3 ZairaChem tools, and a fourth pointing at a quantum venv for `predict_peptide_quantum_vqe`, following the same pattern -- see `claude_desktop_config.json` in the repo root for a complete 4-server example).

## Optional Tools: ZairaChem (bioactivity/QSAR prediction)

`predict_bioactivity`, `train_qsar_model`, and `predict_admet_profile` wrap [ZairaChem](https://github.com/ersilia-os/zaira-chem), a published open-source AutoML QSAR/QSPR pipeline from the Ersilia Open Source Initiative (Turon, Hlozek, Woodland et al., "First fully-automated AI/ML virtual screening cascade implemented at a drug discovery centre in Africa," *Nature Communications* 14, 5736, 2023). ZairaChem was co-developed with and validated at the [H3D Centre](https://h3d.uct.ac.za/) (University of Cape Town) -- pretrained models from that malaria/tuberculosis screening cascade are published separately at [ersilia-os/h3d-screening-cascade-models](https://github.com/ersilia-os/h3d-screening-cascade-models) and can be used directly with `predict_bioactivity`/`predict_admet_profile` with no retraining needed.

**Not included in the Docker image** for the same class of reason as PyRosetta/Boltz-2: ZairaChem is a heavy, conda-orchestrated, multi-environment AutoML stack (it also depends on the separately-installed Ersilia Model Hub CLI for descriptor calculation, which itself needs Docker or Singularity for most descriptor models) -- not something that fits cleanly into a single pip extra or a shared container alongside RFdiffusion's pinned torch stack.

### Installing ZairaChem

```bash
git clone https://github.com/ersilia-os/zaira-chem.git
cd zaira-chem
bash install_script.sh
conda activate zairachem
```

Verify: `zairachem --help` should print the CLI's subcommands (`fit`, `predict`, `distill`).

Then point a separate MCP server instance at this conda environment's Python (same "configure two/three MCP servers side-by-side" pattern shown above for Boltz-2).

### Usage notes

- **Classification only** (not regression) -- binarize continuous assay data yourself, or pass `cutoff`/`direction` to `train_qsar_model` and let ZairaChem do it.
- **`predict_bioactivity` needs an existing model** -- either one you trained with `train_qsar_model`, or a pretrained one (e.g. download an H3D screening-cascade model for a malaria/TB-relevant endpoint and point `model_dir` at it directly).
- Natural pipeline position: score candidate molecules from `design_binder`/`design_fold`/an external molecule-generation step (e.g. qFoldIT's `genmol` skill) for predicted bioactivity *before* committing to expensive downstream validation (docking, synthesis).
- Descriptor calculation (especially GROVER embeddings) can be slow on first run or CPU-only setups -- both new tools default to a generous 4-hour subprocess timeout, configurable via `ZairaChemConfig.timeout_seconds` in `pipelines/zairachem_runner.py`.

## Optional Tools: QuPepFold (quantum peptide folding)

`predict_peptide_quantum_vqe` wraps **QuPepFold**, a published Python package for CVaR-tuned Variational Quantum Eigensolver peptide conformational sampling (Uttarkar, Niranjan, Saxena, Kumar, "QuPepFold: A python package for hybrid quantum-classical protein folding simulations with CVaR-optimized VQE," *PLOS ONE*, 2026, [doi:10.1371/journal.pone.0342012](https://doi.org/10.1371/journal.pone.0342012)), runnable on Qiskit Aer, Amazon Braket's tensor-network simulator, or IonQ Aria-1 hardware. No official package repository URL was independently verified for this addition -- install from PyPI (`pip install qupepfold`) if available, or from the paper's own supplementary materials/links, and confirm the source before pinning a version in production.

**Not included in any bundled image** for the same class of reason as PyRosetta/Boltz-2: Qiskit + Amazon Braket SDK + `qupepfold` is a large, independent dependency stack best kept in its own venv.

### Installing the quantum stack

```bash
python -m venv ~/.venvs/protein-design-quantum
source ~/.venvs/protein-design-quantum/bin/activate
pip install "protein-design-mcp[quantum]"
```

Then point a separate MCP server instance at this venv's Python -- see `claude_desktop_config.json` in the repo root for a worked 5-environment example (core / boltz / zairachem / quantum / macromnex-bindcraft), or the "Configuring two MCP servers side-by-side" pattern above.

### Usage notes

- **Best suited to short peptides** (≲10 residues) -- matches the published benchmark range where CVaR-VQE reliably reaches the ground state.
- **Never crashes the server if unavailable**: if `qupepfold` isn't importable, `predict_peptide_quantum_vqe` returns `{"status": "unavailable", "install_hint": ...}` instead of raising.
- `predict_structure_quantum_walk` (the classical, quantum-walk-*inspired* Metropolis simulation + NeRF backbone builder) needs **no** extra dependency and is available in every install, including the base `pip install protein-design-mcp`. See `pipelines/quantum_runner.py`'s module docstring for exactly what it does and doesn't reproduce from the real QFold quantum-walk algorithm.
- QuPepFold's exact importable Python API (class/function names) was not independently re-verified against an installed copy of the package when this wrapper was written -- see `_run_qupepfold_job` in `pipelines/quantum_runner.py` before relying on it in production.

## Spatial Digital Twin Export (OpenUSD)

`uag_exporter.export_to_openusd(atom_coordinates, output_path)` converts any 3D atom-coordinate list produced by this server (Boltz-2, `predict_structure_quantum_walk`, RFdiffusion, etc. -- anything shaped as a list of `{atom, element, x, y, z, residue_index}` dicts) into a `.usda` OpenUSD scene, for live sync with NVIDIA Omniverse, NanoVer VR, Unreal Engine 5, or Unity.

```bash
pip install "protein-design-mcp[usd]"   # optional -- enables the real pxr/UsdGeom path
```

Without `usd-core` installed, the same function still works via a hand-written, schema-valid ASCII `.usda` fallback (no extra dependency) -- you lose time-sampling/composition-arc support, but get a working file either way.

#### `export_structure_to_spatial_twin` -- exporting *any* PDB file, including from external MCPs

For anything that only produces a PDB file rather than this repo's own coordinate-dict shape, use the `export_structure_to_spatial_twin` MCP tool (or `uag_exporter.export_pdb_to_openusd(pdb_path, output_path)` directly): it parses the PDB with this repo's own `utils/pdb.py`, flattens it to the coordinate-dict shape above, and hands it straight to `export_to_openusd`. It has no dependency on whatever tool produced the PDB -- it only reads a file path off disk.

```json
{"pdb_path": "path/to/binder_design.pdb", "output_path": "path/to/output.usda"}
```

This is the integration point for **BindCraft** (via ProteinMCP's `bindcraft_mcp`, see [Optional Tools: MacromNex/BindCraft](#optional-tools-macromnexbindcraft-binder-design) below) -- point this tool at whatever `.pdb` file BindCraft's `quick_design` writes to disk and get back a live OpenUSD 3D model, no manual conversion step required.

## Optional Tools: MacromNex/BindCraft (binder design)

`claude_desktop_config.json`'s 5th server entry, `qfoldit-mcp-macromnex-bindcraft`, launches an **external, independently-maintained** MCP: `bindcraft_mcp`, a wrapper around [BindCraft](https://github.com/martinpacesa/BindCraft) (Pacesa, Nickel, Schellhaas et al., "One-shot design of functional protein binders with BindCraft," developed at EPFL's Correia Lab with MIT's Ovchinnikov Lab). `bindcraft_mcp` itself is published as part of [ProteinMCP](https://github.com/charlesxu90/ProteinMCP) (Xu et al., *Protein Science*, 2026, doi:10.1002/pro.70547), forked at [MacromNex/ProteinMCP](https://github.com/MacromNex/ProteinMCP) -- [MacromNex](https://github.com/MacromNex) is a real, independently-confirmed GitHub organization ("Macromolecular Nexus") focused on macromolecular design tooling.

**Naming note:** "macromnex-bindcraft" is this config entry's own label, not a published package or command name -- no repository by that exact name was found. What actually gets launched is `bindcraft_mcp`'s own `src/server.py`, run with its own dedicated conda/mamba environment's Python (its documented invocation is `<env>/bin/python src/server.py`, using `fastmcp`) -- **not** this repo's `protein_design_mcp.server` module. See the config entry's own inline comment for the full correction.

**Not vendored in this repo** -- it's a separate project with its own install script, its own JAX/CUDA setup, and its own PyRosetta license requirement (same license terms as this repo's own `rosetta_*` tools). To use it:

1. Clone `MacromNex/ProteinMCP` (or `charlesxu90/ProteinMCP`) and follow `tool-mcps/bindcraft_mcp`'s own README for environment setup (creates its own `./env`, installs BindCraft itself).
2. Point `claude_desktop_config.json`'s `qfoldit-mcp-macromnex-bindcraft` entry's paths at wherever that ends up on your machine.
3. Once it's running, its `quick_design` (or async equivalent) tool writes a `.pdb` file -- feed that path directly to this repo's own `export_structure_to_spatial_twin` tool to get a live OpenUSD 3D model in Omniverse/NanoVer/Unreal/Unity.

**One framing note:** MacromNex's own stated mission (per its GitHub organization page) is "Geometric Deep Learning, Molecular Physics, and Synthetic Biology" research -- it does not describe itself as a gamification or gaming initiative anywhere in its own materials. Any "gamification"/game-related framing applied to this integration is qFoldIT's own product positioning, not a claim made by or about MacromNex, BindCraft, or ProteinMCP.

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DEVICE` | `"auto"`, `"cuda"`, or `"cpu"` | `auto` |
| `RFDIFFUSION_PATH` | Path to RFdiffusion installation | `/opt/RFdiffusion` |
| `PROTEINMPNN_PATH` | Path to ProteinMPNN installation | `/opt/ProteinMPNN` |
| `COLABFOLD_BACKEND` | `"api"` (remote MSA) or `"local"` (local DB) | `api` |
| `CACHE_DIR` | Cache directory | `~/.cache/protein-design-mcp` |
| `TORCH_HOME` | ESM model weights directory | (PyTorch default) |
| `SKIP_MODEL_DOWNLOAD` | Skip eager weight download in Docker | `true` |

## Architecture

```
MCP Server (stdio)
 |
 +-- Design tools
 |    +-- design_binder         RFdiffusion -> ProteinMPNN -> ESMFold
 |    +-- design_fold           RFdiffusion -> ProteinMPNN -> AlphaFold2
 |    +-- generate_backbone     RFdiffusion (unconditional)
 |    +-- design_sequence       ProteinMPNN (+ optional ESMFold validation)
 |    +-- optimize_sequence     ProteinMPNN + ESMFold
 |
 +-- Structure prediction
 |    +-- predict_structure       ESMFold or AlphaFold2
 |    +-- predict_complex         AlphaFold2-Multimer (ColabFold)
 |    +-- predict_structure_boltz Boltz-2 (monomer)
 |    +-- predict_affinity_boltz  Boltz-2 (complex + affinity)
 |    +-- validate_design         Structure prediction + RMSD
 |
 +-- Rosetta (PyRosetta)
 |    +-- rosetta_score           ref2015 energy scoring
 |    +-- rosetta_relax           FastRelax
 |    +-- rosetta_interface_score InterfaceAnalyzerMover
 |    +-- rosetta_design          PackRotamers + MinMover
 |
 +-- Bioactivity / QSAR (ZairaChem)
 |    +-- predict_bioactivity     Score molecules against a trained/pretrained model
 |    +-- train_qsar_model        Train a new binary-classification QSAR model
 |    +-- predict_admet_profile   Multi-endpoint ZairaChem orchestration (solubility/toxicity/bioactivity)
 |
 +-- Quantum peptide folding
 |    +-- predict_peptide_quantum_vqe     QuPepFold CVaR-VQE (Qiskit/Braket)
 |    +-- predict_structure_quantum_walk  Classical quantum-walk-inspired Metropolis + NeRF
 |
 +-- Spatial digital twin export
 |    +-- uag_exporter.export_to_openusd      Atom coordinates -> OpenUSD (.usda)
 |    +-- export_structure_to_spatial_twin    Any PDB file -> OpenUSD (source-agnostic, incl. external MCPs)
 |
 +-- Analysis tools
 |    +-- analyze_interface   PDB geometry analysis
 |    +-- suggest_hotspots    SASA + pockets + UniProt + PubMed
 |    +-- score_stability     ESM2 pseudo-log-likelihood
 |    +-- energy_minimize     OpenMM (AMBER14)
 |
 +-- Utilities
      +-- get_design_status  Job queue polling
      +-- Structure fetching (RCSB, AlphaFold DB, UniProt)
      +-- Conservation scoring, caching
```

## Development

```bash
git clone https://github.com/jasonkim8652/protein-design-mcp.git
cd protein-design-mcp
pip install -e ".[gpu,dev]"

pytest tests/           # Run tests
ruff check .            # Lint
black .                 # Format
mypy src/               # Type check
```

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

## References

- [MCP Specification](https://modelcontextprotocol.io/docs)
- [RFdiffusion](https://github.com/RosettaCommons/RFdiffusion) - Protein backbone generation
- [ProteinMPNN](https://github.com/dauparas/ProteinMPNN) - Sequence design
- [ESMFold / ESM2](https://github.com/facebookresearch/esm) - Structure prediction and stability scoring
- [ColabFold](https://github.com/sokrypton/ColabFold) - Fast AlphaFold2 with MMseqs2
- [Boltz](https://github.com/jwohlwend/boltz) - Open structure and affinity prediction
- [PyRosetta](https://www.pyrosetta.org/) - Physics-based protein modeling
- [OpenMM](https://github.com/openmm/openmm) - Molecular dynamics and energy minimization
- [ZairaChem](https://github.com/ersilia-os/zaira-chem) - AutoML QSAR/bioactivity prediction (Turon, Hlozek, Woodland et al., "First fully-automated AI/ML virtual screening cascade implemented at a drug discovery centre in Africa," *Nature Communications* 14, 5736, 2023, https://doi.org/10.1038/s41467-023-41512-2)
- [H3D Centre screening cascade models](https://github.com/ersilia-os/h3d-screening-cascade-models) - Pretrained ZairaChem models usable directly with `predict_bioactivity` / `predict_admet_profile`
- QuPepFold - CVaR-optimized VQE peptide folding (Uttarkar, Niranjan, Saxena, Kumar, *PLOS ONE*, 2026, https://doi.org/10.1371/journal.pone.0342012)
- QFold - Quantum-walk Metropolis protein folding (Casares, Campos, Martin-Delgado, "QFold: quantum walks and deep learning to solve protein folding," *Quantum Science and Technology* 7, 025013, 2022, https://doi.org/10.1088/2058-9565/ac4f2f, arXiv:2101.10279) -- classical inspiration only for `predict_structure_quantum_walk`, see that tool's own scope note
- [OpenUSD](https://openusd.org/) - Scene description format used by `uag_exporter.py` for spatial digital-twin export (NVIDIA Omniverse, NanoVer VR, Unreal Engine 5, Unity)
- [BindCraft](https://github.com/martinpacesa/BindCraft) - De novo protein binder design (Pacesa, Nickel, Schellhaas et al., EPFL Correia Lab / MIT Ovchinnikov Lab). Not vendored -- integrated externally via `bindcraft_mcp`, see [Optional Tools: MacromNex/BindCraft](#optional-tools-macromnexbindcraft-binder-design)
- [ProteinMCP](https://github.com/charlesxu90/ProteinMCP) - Agentic MCP framework packaging BindCraft as `bindcraft_mcp` (Xu et al., *Protein Science*, 2026, https://doi.org/10.1002/pro.70547), forked at [MacromNex/ProteinMCP](https://github.com/MacromNex/ProteinMCP)
- Full citation metadata, including software/consortium references: see [CITATION.cff](CITATION.cff)
