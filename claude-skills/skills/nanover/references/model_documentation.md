# Model Reference: qfoldit-nanover

## What NanoVer is (real, independently published)

NanoVer is a client-server framework for real-time, multi-user
interactive molecular dynamics in VR/XR, developed by the Intangible
Realities Laboratory (Bristol/Santiago de Compostela). It consists of:
- **Python server** (`nanover-server-py`): connects to a physics engine
  (typically OpenMM) and broadcasts frames over a gRPC-based network
  protocol.
- **VR/XR client** (`nanover-imd-xr`, Unity3D-based): connects to a
  server, renders the structure, and lets a user in VR push/pull atoms,
  which (if a force field is attached server-side) produces physically
  responsive motion.
- **ESSD** (Extremely Simple Service Discovery): local-network discovery
  so clients can auto-find servers (`nanover-essd-list` CLI).

Primary citation: Stroud, H.J., Wonnacott, M.D., Barnoud, J., Roebuck
Williams, R., Dhouioui, M., McSloy, A., Aisa, L., Toledo, L.E., Bates,
P., Mulholland, A.J., & Glowacki, D.R. (2025). "NanoVer Server: A Python
Package for Serving Real-Time Multi-User Interactive Molecular Dynamics
in Virtual Reality." *Journal of Open Source Software*, 10(110), 8118.
https://doi.org/10.21105/joss.08118

Flagship science use case: Deeks, H.M., Zinovjev, K., Barnoud, J.,
Mulholland, A.J., van der Kamp, M.W., & Glowacki, D.R. (2023). "Free
energy along drug-protein binding pathways interactively sampled in
virtual reality." *Scientific Reports*, 13, 16665.

## Confirmed real installation/usage facts

- Install via conda only: `conda install -c irl -c conda-forge nanover-server`
  (not on PyPI).
- CLI usage for serving a precomputed OpenMM simulation:
  `nanover-server --omm my-openmm-sim.xml`
- CLI usage for serving a recorded trajectory (playback, no live
  physics): `nanover-server --playback my-recording.state my-recording.traj`
- `nanover.mdanalysis` provides an example server pattern that loops
  over the frames of a trajectory indefinitely — the closest documented
  analogue to "serve a static/looping structure" that this skill's
  `serve_static_structure()` follows.
- Client: NanoVer iMD-XR, available via Meta Horizon Store, or as a
  standalone Windows build / sideloadable Meta Quest APK.
- Units: the NanoVer frame protocol uses nanometers for particle
  positions; PDB files use Angstroms — `static_structure_to_nanover_frame`
  converts accordingly (divides by 10).

## What was NOT independently confirmed during authoring

- The exact Python API for constructing and serving a **single static
  frame** (as opposed to a full OpenMM-driven live simulation or a
  pre-recorded trajectory file) was not found as a explicit standalone
  documented example during authoring — `serve_static_structure()`'s use
  of `OmniRunner.with_basic_server(...)` and `runner.add_frame(...)` is
  written by analogy with the documented `OmniRunner` / looping-frame-
  server patterns (e.g. `nanover.mdanalysis`), but the exact method name
  `add_frame` should be confirmed against your installed NanoVer
  version's actual `OmniRunner` API before relying on it — this is
  exactly the kind of detail that's easy to get slightly wrong from
  documentation alone versus reading the actual installed package's
  source/docstrings.
- Whether `github.com/qfoldit/nanover` (if it exists) is an unmodified
  fork of `IRL2/nanover-server-py` or a customized version was not and
  could not be independently verified in this authoring environment.

## Recommended verification steps before production use

1. `conda install -c irl -c conda-forge nanover-server` in a real
   environment.
2. `python -c "import nanover.omni; help(nanover.omni.OmniRunner)"` to
   confirm the actual available methods for serving a static frame,
   and correct `nanover_bridge.py` if `add_frame` isn't the right call.
3. Test with a small structure (e.g. a short peptide) and a local
   NanoVer client before using this for anything presentation-critical.
