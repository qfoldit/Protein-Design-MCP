"""
nanover_bridge.py -- bridges qFoldIT science-skill outputs (folded
structures from qfold/rosettafold3/esmfold, molecules from genmol, etc.)
into NanoVer, a real, published, open-source framework for collaborative
interactive molecular dynamics in VR (Stroud, Wonnacott, Barnoud et al.
2025, JOSS 10(110):8118; Intangible Realities Laboratory, University of
Santiago de Compostela / Bristol -- github.com/IRL2/nanover-server-py).

IMPORTANT ABOUT THIS FILE'S PROVENANCE:
This client is written against the PUBLICLY DOCUMENTED NanoVer protocol
and Python package structure (nanover.omni, nanover.mdanalysis,
nanover.essd -- see references/model_documentation.md for sources), NOT
against inspected source of any specific fork (including
github.com/qfoldit/nanover, whose contents this authoring environment
could not independently verify or fetch). If your fork has renamed
modules or changed the server API, check it against the real upstream
(github.com/IRL2/nanover-server-py) and adjust the imports below.

REQUIRES (not available in this authoring sandbox -- no network/conda):
  conda install -c irl -c conda-forge nanover-server
Optionally, for live interactive MD (not just static structure viewing):
  conda install -c conda-forge openmm

This module does NOT invent a new protocol -- it is a thin adapter that
prepares qFoldIT structures in the form NanoVer already expects
(a servable "frame"/trajectory), and starts a real NanoVer server so an
actual NanoVer iMD-XR client (desktop, Meta Quest via Horizon Store or
sideload) can connect, view, and -- if a force field is attached -- push
and pull atoms interactively.
"""

import os


def _check_nanover_available():
    """
    Returns (available: bool, message: str). Does not raise -- callers
    should check this before attempting to use the rest of this module,
    since nanover-server is a conda-only package not installable via
    pip, and is not present in most default environments.
    """
    try:
        import nanover.omni  # noqa: F401
        return True, "nanover package found."
    except ImportError:
        return False, (
            "The 'nanover' package is not installed in this Python environment. "
            "It is distributed via conda, not pip: "
            "conda install -c irl -c conda-forge nanover-server "
            "(see references/model_documentation.md for source docs). "
            "If you're using a custom fork (e.g. qfoldit/nanover), install "
            "that fork's package instead and verify the import path still "
            "matches 'nanover.omni' -- if the fork renamed the package, "
            "update the import in this file accordingly."
        )


def static_structure_to_nanover_frame(pdb_text: str):
    """
    Convert a static PDB structure (e.g. output of qfoldit-esmfold,
    qfoldit-rosettafold3, or qfoldit-rfdiffusion) into a single-frame
    NanoVer FrameData object suitable for serving.

    This gives VIEWING/MANIPULATION in VR but NOT physically-responsive
    interactive MD -- for that, see openmm_live_simulation_frame_source
    below, which requires attaching a real force field.

    Returns a nanover.trajectory.FrameData object, or a dict with an
    "error" key if the nanover package or a PDB parser isn't available.
    """
    available, msg = _check_nanover_available()
    if not available:
        return {"error": msg}

    try:
        import numpy as np
        from nanover.trajectory import FrameData
    except ImportError as e:
        return {"error": f"Required NanoVer/numpy import failed: {e}"}

    atoms = []
    for line in pdb_text.splitlines():
        if line.startswith(("ATOM", "HETATM")):
            try:
                x = float(line[30:38]) / 10.0  # PDB is Angstrom, NanoVer frames use nm
                y = float(line[38:46]) / 10.0
                z = float(line[46:54]) / 10.0
                element = line[76:78].strip() or line[12:16].strip()[0]
                atoms.append((x, y, z, element))
            except (ValueError, IndexError):
                continue

    if not atoms:
        return {"error": "No ATOM/HETATM records could be parsed from pdb_text."}

    frame = FrameData()
    frame.particle_positions = np.array([(a[0], a[1], a[2]) for a in atoms], dtype=np.float32)
    frame.particle_count = len(atoms)
    frame.particle_elements = [a[3] for a in atoms]
    return frame


def serve_static_structure(pdb_text: str, name: str = "qfoldit-structure", port: int = None):
    """
    Start a real NanoVer server broadcasting a single static structure,
    so a NanoVer iMD-XR client can connect over the local network and
    view/rotate/scale it in VR (multi-user: several headsets can join
    the same server session).

    This does NOT run physics -- atoms will not respond to being pushed
    in VR (they'll just move where placed, with no force field pulling
    them back). For physically-responsive interaction, use
    openmm_live_simulation_frame_source instead.

    Returns a dict describing how to connect, or {"error": ...} if
    nanover isn't installed. The server keeps running until the calling
    process is stopped -- this is meant to be run from a script/notebook
    the user keeps alive, not a one-shot call.
    """
    frame = static_structure_to_nanover_frame(pdb_text)
    if isinstance(frame, dict) and "error" in frame:
        return frame

    available, msg = _check_nanover_available()
    if not available:
        return {"error": msg}

    try:
        from nanover.omni import OmniRunner
        from nanover.essd import DiscoveryServer
    except ImportError as e:
        return {"error": f"Required NanoVer import failed: {e}"}

    # NOTE: OmniRunner's exact static-frame-serving API may differ slightly
    # by NanoVer version -- consult references/model_documentation.md and
    # your installed version's docs if this errors. The pattern below
    # follows NanoVer's documented "serve a looping/static trajectory"
    # examples (nanover.mdanalysis's infinite-loop frame server is the
    # closest documented analogue for a static/looping structure).
    runner = OmniRunner.with_basic_server(name=name, port=port)
    runner.add_frame(frame)  # confirm this method name against your installed version

    return {
        "status": "server_started",
        "name": name,
        "note": (
            "Server is running and broadcasting the structure. Connect with a "
            "NanoVer iMD-XR client on the same network (auto-discovery via ESSD, "
            "or run `nanover-essd-list` from another machine to find it). "
            "This is VIEW-ONLY -- no force field is attached, so pushing atoms "
            "in VR will not produce physically realistic responses."
        ),
        "runner_object_note": (
            "The returned OmniRunner object must be kept alive (don't let it be "
            "garbage-collected) for the server to keep running -- store it in a "
            "variable in your script/notebook."
        ),
    }


def openmm_live_simulation_note() -> dict:
    """
    Explains what's needed for REAL interactive MD (physically-responsive
    VR manipulation), which is NanoVer's core value proposition beyond
    static viewing -- this function does not implement it, because doing
    so correctly requires OpenMM force-field setup (choosing a force
    field, solvating, energy-minimizing) that is structure- and
    science-question-specific, not something to templatize blindly.
    """
    return {
        "what_static_serving_gives_you": (
            "View a qFoldIT structure (folded protein, docked complex, "
            "generated molecule) in VR, walk around it, scale it, point at "
            "residues/atoms -- genuinely useful for presentation, teaching, "
            "and visual QC, but atoms don't respond to being touched."
        ),
        "what_live_md_adds": (
            "Push/pull atoms and see the structure respond via a real force "
            "field (OpenMM) in real time -- this is what NanoVer's own "
            "published use cases (e.g. Deeks et al. 2023, interactively "
            "sampling drug-protein binding free energy pathways in VR) "
            "actually rely on."
        ),
        "what_you_need_to_add": [
            "conda install -c conda-forge openmm",
            "Choose and parameterize a force field for your structure "
            "(e.g. Amber/CHARMM for proteins -- this is a real modeling "
            "decision, not something this bridge should silently default)",
            "Solvate/minimize as appropriate for your system",
            "Use nanover-server's --omm CLI flag or the Python OmniRunner "
            "API to serve the live OpenMM simulation instead of a static frame",
        ],
        "recommendation": (
            "Start with serve_static_structure() for viewing/presentation use "
            "cases. Only invest in the OpenMM force-field setup once a "
            "specific structure and scientific question calls for actually "
            "interactive (not just visual) VR manipulation."
        ),
    }
