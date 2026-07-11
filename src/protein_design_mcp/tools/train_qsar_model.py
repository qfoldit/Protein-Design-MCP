"""
QSAR model training tool using ZairaChem (real, published Ersilia Open
Source Initiative AutoML QSAR tool -- see pipelines/zairachem_runner.py
for full provenance and citations).

Trains a new binary-classification bioactivity/property model from
labeled data (SMILES + activity). For scoring molecules against an
EXISTING model (yours or a published pretrained one), use
predict_bioactivity instead -- this tool is only for building a new
model from scratch.
"""

from typing import Any

from protein_design_mcp.pipelines.zairachem_runner import ZairaChemRunner, ZairaChemConfig


async def train_qsar_model(
    input_csv: str,
    output_dir: str,
    cutoff: float | None = None,
    direction: str | None = None,
    parameters_file: str | None = None,
) -> dict[str, Any]:
    """
    Train a new ZairaChem binary-classification QSAR model.

    Args:
        input_csv: CSV with a SMILES column and an activity column.
        output_dir: Directory ZairaChem will write the trained model into.
        cutoff: Activity cutoff for binarizing a continuous assay column,
            if the activity column isn't already 0/1. Omit if the input
            is already binarized.
        direction: "high" or "low" -- which side of cutoff counts as
            "active". Required if cutoff is given.
        parameters_file: Optional path to a ZairaChem parameters.json for
            custom descriptor selection (advanced use; see ZairaChem's
            own documentation for the schema, not reproduced here).

    Returns:
        Dict with status, output_dir, and a note on where to find the
        actual trained-model artifacts and performance report.

    Raises:
        ZairaChemError: if the zairachem CLI isn't installed/on PATH, the
            input path doesn't exist, or training fails/times out
            (ZairaChem's descriptor calculation and AutoML stages can be
            slow -- default timeout is 4 hours, see ZairaChemConfig).

    Note: ZairaChem currently supports binary classification tasks only
    (not regression) -- if your data is continuous and you don't want to
    binarize it, ZairaChem is not the right tool for that use case.
    """
    if cutoff is not None and direction is None:
        return {"error": "direction ('high' or 'low') is required when cutoff is given."}

    config = ZairaChemConfig(cutoff=cutoff, direction=direction, parameters_file=parameters_file)
    runner = ZairaChemRunner(config=config)
    return await runner.fit(input_csv=input_csv, output_dir=output_dir)
