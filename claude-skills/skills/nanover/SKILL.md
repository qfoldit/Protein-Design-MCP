---
name: qfoldit-nanover
description: Bridge qFoldIT structures (folded proteins from qfold/rosettafold3/esmfold, docked complexes from diffdock, designed backbones from rfdiffusion, generated molecules from genmol) into NanoVer, a real published open-source framework for collaborative interactive molecular dynamics in VR. Use this skill whenever the user asks to view/manipulate a qFoldIT structure in VR, wants collaborative/multiplayer molecular visualization, or mentions NanoVer, iMD-VR, or interactive molecular dynamics in virtual reality. Requires a local conda install of nanover-server (not pip-installable, not available in most default environments) -- say this plainly before promising anything will work out of the box.
---

# qfoldit-nanover (VR bridge to a real published framework)

**NanoVer is real, published, and independently maintained** by the
Intangible Realities Laboratory (University of Bristol / Santiago de
Compostela) -- Stroud, Wonnacott, Barnoud et al. 2025, JOSS 10(110):8118.
This is NOT a qFoldIT invention; qFoldIT's role here is a thin adapter
that hands NanoVer a structure to serve, nothing more.

## Read this before promising anything works

1. **`nanover-server` is conda-only, not pip-installable**, and is NOT
   present in this authoring environment or most default Python setups.
   `scripts/nanover_bridge.py` checks for it and returns a clear
   `{"error": ...}` if missing -- surface that error, don't imply the
   bridge "just works" without setup.
2. **This client was written against the publicly documented NanoVer
   protocol/package structure**, not against inspected source of any
   specific fork (including a `qfoldit/nanover` fork, if one exists --
   this authoring environment could not independently verify or fetch
   its contents). If the user's fork renamed modules or changed the
   server API, the import paths in `nanover_bridge.py` may need
   adjusting -- say this rather than assuming the code is guaranteed
   correct against an unverified fork.
3. **Static structure serving vs. live interactive MD are very
   different things.** `serve_static_structure()` gives VR
   viewing/rotation/scaling of a structure with NO physics -- atoms
   don't respond to being touched. Real interactive MD (NanoVer's actual
   headline capability, e.g. pushing atoms and feeling the structure
   respond) requires attaching a real OpenMM force field, which is a
   genuine per-structure modeling decision (choice of force field,
   solvation, minimization) that this skill does NOT templatize or
   auto-decide. Call `openmm_live_simulation_note()` to explain the gap
   rather than silently only offering the static (less impressive, but
   honestly deliverable) version.

## What this skill actually does

1. `static_structure_to_nanover_frame(pdb_text)` -- parses a PDB
   structure (from any qFoldIT structure-producing skill) into a
   NanoVer `FrameData` object.
2. `serve_static_structure(pdb_text, name, port)` -- starts a real
   NanoVer server broadcasting that structure for VR viewing (multi-user
   -- several headsets can join the same session, since NanoVer is
   natively collaborative).
3. `openmm_live_simulation_note()` -- explains what's needed to go from
   static viewing to physically-responsive interactive MD; does not
   implement it (see point 3 above for why).

## How to handle a request

1. Confirm `nanover-server` (conda) is installed in the user's actual
   environment -- not this authoring sandbox. If unsure, say so and let
   `_check_nanover_available()` surface the real answer.
2. Get a PDB structure from wherever the user's actual goal produces one
   (`qfoldit-esmfold`, `qfoldit-rosettafold3`, `qfoldit-rfdiffusion`,
   docked poses from `qfoldit-diffdock`, etc.) -- this skill doesn't
   generate structures itself.
3. For "show me this in VR" / presentation / teaching use cases: use
   `serve_static_structure()`, and set expectations that atoms won't
   respond to touch.
4. For "let me interactively explore binding/folding" use cases (closer
   to NanoVer's actual published science use, e.g. Deeks et al. 2023's
   VR-sampled binding free energy pathways): explain via
   `openmm_live_simulation_note()` that a force-field setup step is
   needed first, and don't skip straight to claiming interactivity that
   isn't there.
5. **Always cite NanoVer properly** when discussing it (Stroud et al.
   2025, JOSS; Deeks et al. 2023, Scientific Reports) -- it's someone
   else's real, published research infrastructure that qFoldIT is
   building on top of, not qFoldIT's own invention.

## Multi-user / collaborative VR

NanoVer is natively multi-user -- multiple NanoVer iMD-XR clients (on
different headsets, e.g. via Meta Horizon Store, or desktop) can connect
to the same server session simultaneously. This is the real,
already-existing answer to the "collaborative VR" goal described
elsewhere in qFoldIT's vision documents -- it does not need to be built
from scratch, only connected to.
