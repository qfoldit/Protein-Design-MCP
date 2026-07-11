# qFoldIT NanoVer Skill — VR Bridge to a Real Published Framework

Bridges qFoldIT structures into **NanoVer**, a real, independently
published, open-source framework for collaborative interactive
molecular dynamics in VR — not a qFoldIT invention.

- Paper: Stroud, H.J., Wonnacott, M.D., Barnoud, J. et al. (2025).
  "NanoVer Server: A Python Package for Serving Real-Time Multi-User
  Interactive Molecular Dynamics in Virtual Reality." *JOSS*, 10(110), 8118.
- Also see: Deeks et al. (2023), *Scientific Reports*, 13, 16665 — VR
  interactive sampling of drug-protein binding free energy pathways,
  NanoVer's flagship published science use case.
- Maintainer: Intangible Realities Laboratory, University of Bristol /
  Santiago de Compostela.
- Upstream: https://github.com/IRL2/nanover-server-py
- Client available on Meta Horizon Store, or as a standalone
  Windows/APK build.

## A note on provenance

This client was written against NanoVer's **publicly documented**
protocol and Python package structure — not against inspected source of
any specific fork. If you're using a fork under `github.com/qfoldit/nanover`
or similar, this authoring environment could not independently verify or
fetch its contents (no network access, and the URL hadn't surfaced in
any prior search result). If your fork renamed modules or changed the
server API, check `scripts/nanover_bridge.py`'s imports against your
actual installed package.

## Setup

```bash
conda install -c irl -c conda-forge nanover-server
# optionally, for live interactive MD:
conda install -c conda-forge openmm
```

**Not pip-installable.** Not present in this authoring sandbox — every
function in `nanover_bridge.py` checks for the package and returns a
clear error if it's missing, rather than pretending to work.

## What it does

- `static_structure_to_nanover_frame(pdb_text)` — parse a PDB structure
  into a NanoVer `FrameData` object.
- `serve_static_structure(pdb_text, name, port)` — start a real,
  natively multi-user NanoVer server so any NanoVer iMD-XR client can
  connect and view/rotate/scale the structure in VR.
- `openmm_live_simulation_note()` — explains (does not implement) what's
  needed for real physically-responsive interactive MD.

## Static viewing vs. live interactive MD — know the difference

| | Static serving (implemented) | Live interactive MD (not implemented here) |
|---|---|---|
| What you get | View, rotate, scale in VR, multi-user | Push/pull atoms, physically-responsive |
| Requirement | `nanover-server` only | + OpenMM + a real force-field setup decision |
| This skill | ✅ `serve_static_structure()` | ⚠️ `openmm_live_simulation_note()` explains the gap only |

Force-field selection, solvation, and minimization are genuine
per-structure modeling decisions — this skill deliberately does not
auto-decide them.

## Pipeline position

Any qFoldIT structure-producing skill (`qfoldit-esmfold`,
`qfoldit-rosettafold3`, `qfoldit-rfdiffusion`, `qfoldit-diffdock` poses)
→ **qfoldit-nanover** (serve for VR viewing) → a real NanoVer iMD-XR
client on the same network.

## Status

Written against NanoVer's public documentation, not tested end-to-end
(no network/conda access in the authoring sandbox, and no independent
verification of any `qfoldit/nanover` fork's actual contents). Verify
against your real installed NanoVer version before relying on this in
production — the `add_frame` method name in particular is noted in-code
as needing confirmation against your installed version.
