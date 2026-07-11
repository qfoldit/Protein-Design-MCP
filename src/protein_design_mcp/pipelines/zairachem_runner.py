"""
ZairaChem wrapper for automated QSAR/QSPR bioactivity and property
prediction on small molecules.

ZairaChem is a real, published, open-source AutoML tool from the
Ersilia Open Source Initiative (Turon, Hlozek, Woodland et al., "First
fully-automated AI/ML virtual screening cascade implemented at a drug
discovery centre in Africa," Nature Communications 14, 5736, 2023).
It combines multiple molecular descriptors (Mordred physicochemical
parameters, ECFP fingerprints, Chemical Checker bioactivity signatures,
GROVER graph embeddings, chemical-language-model embeddings) with an
AutoML ensemble (FLAML, AutoGluon, Keras Tuner, TabPFN, MolMapNet) to
build binary-classification QSAR models -- currently ZairaChem targets
classification tasks (active/inactive), not regression.

Notably, ZairaChem was co-developed with and validated at the H3D
Centre (University of Cape Town, Africa's leading integrated drug
discovery unit, directed by Prof. Kelly Chibale) -- pretrained models
from that collaboration's malaria/tuberculosis screening cascade are
published separately at github.com/ersilia-os/h3d-screening-cascade-models
and can be used directly with `predict()` below without retraining.

Two real, independently confirmed CLI generations exist:
  v1 (conda/pip installable): `zairachem fit`, `zairachem predict`,
    `zairachem distill` -- github.com/ersilia-os/zaira-chem
  v2 (Docker-only, newer): `run_fit.sh`, presumably an analogous
    `run_predict.sh` -- github.com/ersilia-os/zairachem-docker

THIS RUNNER TARGETS v1's CLI (`zairachem fit` / `zairachem predict`),
since it has a simpler, directly-documented command-line surface than
the Docker-orchestrated v2. If your environment only has v2 installed,
the command construction below will need adjusting -- see
references/model_documentation.md in the corresponding skill for the
v2 shell-script invocation pattern, which was NOT independently
re-verified for its exact predict-side flags in this authoring session
(only the general `run_fit.sh` flag set was documented in the source
consulted).

Like PyRosettaRunner in this codebase, this class does NOT assume
ZairaChem is installed -- it's a large, conda-heavy AutoML stack (not a
lightweight pip package), so availability is checked explicitly with a
clear, actionable error rather than an opaque subprocess failure.
"""

import asyncio
import logging
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from protein_design_mcp.exceptions import ZairaChemError

logger = logging.getLogger(__name__)


def _ensure_zairachem_available() -> None:
    """Raise a clear, actionable error if the zairachem CLI isn't on PATH."""
    if shutil.which("zairachem") is None:
        raise ZairaChemError(
            "The 'zairachem' CLI is not on PATH. ZairaChem (v1) is "
            "conda-distributed, not a plain pip package: create and activate "
            "its own conda environment per the official install instructions "
            "at https://github.com/ersilia-os/zaira-chem, then re-run. It also "
            "depends on the Ersilia Model Hub for descriptor calculation "
            "(ersilia CLI), which itself needs Docker or Singularity for most "
            "models -- this is a heavy, multi-tool stack, not a single pip "
            "extra; budget real setup time before relying on this tool."
        )


@dataclass
class ZairaChemConfig:
    """Configuration for ZairaChem fit/predict operations."""

    cutoff: float | None = None       # activity cutoff for binarizing a continuous assay column
    direction: str | None = None      # "high" or "low" -- which side of cutoff counts as "active"
    parameters_file: str | None = None  # optional parameters.json (custom descriptor selection etc.)
    timeout_seconds: int = 3600 * 4   # ZairaChem's descriptor calculation (esp. GROVER) can be slow


class ZairaChemRunner:
    """Subprocess wrapper for the ZairaChem (v1) CLI."""

    def __init__(self, config: ZairaChemConfig | None = None):
        self.config = config or ZairaChemConfig()

    async def fit(self, input_csv: str, output_dir: str) -> dict[str, Any]:
        """
        Train a new binary-classification QSAR model.

        input_csv: CSV with a SMILES column and an activity column. If
          the activity column isn't already binarized (0/1), supply
          self.config.cutoff and self.config.direction so ZairaChem
          binarizes it internally -- confirm the exact expected column
          names/order against ZairaChem's own documentation/examples,
          which were not exhaustively re-verified in this authoring
          session beyond the CLI flag names themselves.
        output_dir: directory ZairaChem will write the trained model
          artifacts into.

        Returns dict with status, output_dir, and raw stdout/stderr for
        diagnosing failures (ZairaChem's AutoML stage can fail for many
        data-dependent reasons -- surfacing raw output beats swallowing it).
        """
        _ensure_zairachem_available()

        input_path = Path(input_csv)
        if not input_path.exists():
            raise ZairaChemError(f"input_csv not found: {input_csv}")

        cmd = ["zairachem", "fit", "-i", str(input_path), "-m", output_dir]
        if self.config.cutoff is not None:
            cmd += ["-c", str(self.config.cutoff)]
        if self.config.direction is not None:
            cmd += ["-d", self.config.direction]
        if self.config.parameters_file:
            cmd += ["-p", self.config.parameters_file]

        return await self._run(cmd, output_dir)

    async def predict(self, input_csv: str, model_dir: str, output_dir: str) -> dict[str, Any]:
        """
        Score new molecules against an existing (trained or pretrained)
        ZairaChem model -- e.g. one of the published H3D screening-cascade
        models (github.com/ersilia-os/h3d-screening-cascade-models) for
        malaria/tuberculosis-relevant endpoints, used as-is with no
        retraining needed.

        input_csv: CSV with (at minimum) a SMILES column -- exact
          expected column name/order not independently re-verified here,
          check ZairaChem's own example inputs.
        model_dir: path to a trained ZairaChem model directory (either
          your own from fit(), or a downloaded pretrained one).
        output_dir: directory ZairaChem will write predictions into.
        """
        _ensure_zairachem_available()

        input_path = Path(input_csv)
        if not input_path.exists():
            raise ZairaChemError(f"input_csv not found: {input_csv}")
        if not Path(model_dir).exists():
            raise ZairaChemError(f"model_dir not found: {model_dir}")

        cmd = ["zairachem", "predict", "-i", str(input_path), "-m", model_dir, "-o", output_dir]
        return await self._run(cmd, output_dir)

    async def _run(self, cmd: list[str], output_dir: str) -> dict[str, Any]:
        logger.info(f"Running ZairaChem: {' '.join(cmd)}")
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=self.config.timeout_seconds
            )
        except asyncio.TimeoutError:
            raise ZairaChemError(
                f"ZairaChem did not finish within {self.config.timeout_seconds}s. "
                "Descriptor calculation (especially GROVER embeddings) can be slow "
                "on CPU-only or first-run (model-download) invocations -- consider "
                "raising ZairaChemConfig.timeout_seconds for large input sets."
            )

        if proc.returncode != 0:
            raise ZairaChemError(
                f"ZairaChem exited with code {proc.returncode}.\n"
                f"stdout:\n{stdout.decode(errors='replace')[-4000:]}\n"
                f"stderr:\n{stderr.decode(errors='replace')[-4000:]}"
            )

        return {
            "status": "completed",
            "output_dir": output_dir,
            "stdout_tail": stdout.decode(errors="replace")[-2000:],
            "note": (
                "ZairaChem writes its own report/output files into output_dir "
                "(predictions CSV, performance report for fit runs) -- parse "
                "those directly rather than relying only on stdout, whose exact "
                "format was not exhaustively documented in this authoring session."
            ),
        }
