"""
ADMET-style property profiling for a single small molecule, built on top
of the existing ZairaChemRunner (see pipelines/zairachem_runner.py for
full ZairaChem provenance/citations -- Turon, Hlozek, Woodland et al.,
Nat Commun 14:5736, 2023).

IMPORTANT SCOPE NOTE: ZairaChem is a binary-classification QSAR AutoML
tool that scores molecules against a model YOU (or someone) has already
trained/published for a *specific* endpoint (e.g. "active/inactive
against Mtb H37Rv"). It has no single built-in "solubility + toxicity +
bioactivity" multi-endpoint output -- that profile only exists if you
point this tool at several separately-trained/published endpoint model
directories (e.g. the H3D Centre's malaria/tuberculosis screening
cascade models, github.com/ersilia-os/h3d-screening-cascade-models,
alongside any solubility/toxicity endpoint models you have separately).
This tool is therefore a thin orchestration layer: it runs ZairaChem's
real `predict` command once per configured endpoint directory and
assembles the results into one profile dict -- it does NOT invent
scores for endpoints that have no corresponding trained model available.
"""

from __future__ import annotations

import csv
import logging
import tempfile
from pathlib import Path
from typing import Any

from protein_design_mcp.exceptions import ZairaChemError
from protein_design_mcp.pipelines.zairachem_runner import ZairaChemConfig, ZairaChemRunner

logger = logging.getLogger(__name__)

# Endpoint name -> environment variable holding the path to a trained/
# pretrained ZairaChem model directory for that endpoint. Unset/missing
# entries are skipped (reported as "not_configured"), never silently
# faked. Override or extend via environment variables at deploy time.
_ENDPOINT_ENV_VARS = {
    "solubility": "ZAIRACHEM_MODEL_SOLUBILITY",
    "toxicity": "ZAIRACHEM_MODEL_TOXICITY",
    "bioactivity_malaria": "ZAIRACHEM_MODEL_MALARIA",
    "bioactivity_tuberculosis": "ZAIRACHEM_MODEL_TUBERCULOSIS",
}


async def predict_admet_profile(smiles: str) -> dict[str, Any]:
    """
    Run ZairaChem prediction for a single SMILES string across all
    configured endpoint models and return a combined ADMET-style profile.

    Args:
        smiles: A single SMILES string for the candidate molecule.

    Returns:
        Dict with ``status``, ``smiles``, and ``endpoints`` -- a dict
        keyed by endpoint name, each either:
          - ``{"status": "ok", "score": <float or None>, "output_dir": ...}``
            (score is best-effort parsed from ZairaChem's own output CSV;
            if the column layout can't be confidently identified, score
            is None and ``output_dir`` is returned so you can inspect
            ZairaChem's raw output yourself), or
          - ``{"status": "not_configured"}`` if no model directory is set
            for that endpoint via its environment variable, or
          - ``{"status": "error", "error": ...}`` if the ZairaChem CLI
            isn't installed or the run failed for that endpoint.
    """
    import os

    if not smiles or not smiles.strip():
        return {"status": "error", "error": "smiles is required and must be non-empty"}

    endpoints: dict[str, Any] = {}

    with tempfile.TemporaryDirectory(prefix="admet_profile_") as tmp_dir:
        input_csv = Path(tmp_dir) / "molecule.csv"
        with open(input_csv, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["smiles"])
            writer.writerow([smiles])

        runner = ZairaChemRunner(config=ZairaChemConfig())

        for endpoint_name, env_var in _ENDPOINT_ENV_VARS.items():
            model_dir = os.environ.get(env_var)
            if not model_dir:
                endpoints[endpoint_name] = {
                    "status": "not_configured",
                    "hint": f"Set {env_var} to a ZairaChem model directory to enable this endpoint.",
                }
                continue

            endpoint_output_dir = str(Path(tmp_dir) / endpoint_name)
            try:
                await runner.predict(
                    input_csv=str(input_csv),
                    model_dir=model_dir,
                    output_dir=endpoint_output_dir,
                )
                score = _best_effort_parse_score(endpoint_output_dir)
                endpoints[endpoint_name] = {
                    "status": "ok",
                    "score": score,
                    "output_dir": endpoint_output_dir if score is None else None,
                }
            except ZairaChemError as exc:
                logger.warning("ZairaChem endpoint %s failed: %s", endpoint_name, exc)
                endpoints[endpoint_name] = {"status": "error", "error": str(exc)}
            except Exception as exc:  # noqa: BLE001 - never crash the MCP loop
                logger.exception("Unexpected error scoring endpoint %s", endpoint_name)
                endpoints[endpoint_name] = {"status": "error", "error": f"Unexpected failure: {exc}"}

    any_ok = any(v.get("status") == "ok" for v in endpoints.values())
    return {
        "status": "ok" if any_ok else "no_endpoints_configured",
        "smiles": smiles,
        "endpoints": endpoints,
    }


def _best_effort_parse_score(output_dir: str) -> float | None:
    """
    Try to pull a single numeric prediction score out of ZairaChem's own
    output directory. ZairaChem's exact output file/column naming was
    NOT independently re-verified in this authoring session (see
    zairachem_runner.py's module docstring for the same caveat on the
    CLI's v1/v2 split) -- this scans for the most plausible candidates
    and returns None rather than guessing if nothing matches, so callers
    always know when they need to look at output_dir themselves.
    """
    candidates = ["predictions.csv", "output.csv", "results.csv"]
    out_path = Path(output_dir)
    if not out_path.exists():
        return None

    for name in candidates:
        csv_path = out_path / name
        if not csv_path.exists():
            continue
        try:
            with open(csv_path, newline="") as f:
                reader = csv.DictReader(f)
                row = next(reader, None)
                if row is None:
                    continue
                for key in ("score", "pred", "prediction", "probability", "y_pred"):
                    if key in row:
                        return float(row[key])
        except (ValueError, StopIteration, OSError):
            continue

    return None
